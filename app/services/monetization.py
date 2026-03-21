"""
Monetization Service

Revenue streams:
1. Subscriptions (Freemium → Basic $9.99 → Pro $29.99 → Enterprise $99.99/mo)
2. Pay-per-prediction credits ($5 = 25 credits, each premium prediction = 1 credit)
3. API access (Enterprise only)
4. Affiliate revenue (future: refer users to sportsbooks/exchanges)

Stripe integration:
  - Set STRIPE_SECRET_KEY in .env for live payments
  - Webhook handles subscription lifecycle events
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User, SubscriptionTier, TIER_LIMITS
from app.models.prediction import Prediction
from app.models.transaction import Transaction, TransactionType


CREDIT_PACKAGES = {
    "starter": {"credits": 25, "price_usd": 5.00, "label": "Starter Pack"},
    "standard": {"credits": 75, "price_usd": 12.00, "label": "Standard Pack (20% bonus)"},
    "pro": {"credits": 200, "price_usd": 25.00, "label": "Pro Pack (60% bonus)"},
}
CREDIT_COST_PREMIUM = 1.0  # credits per premium prediction
CREDIT_VALUE_USD = 0.20    # $0.20 per credit (buy at $0.20 avg)


class AccessDenied(Exception):
    pass


class InsufficientCredits(Exception):
    pass


class QuotaExceeded(Exception):
    pass


def get_tier_limits(tier: SubscriptionTier) -> dict:
    return TIER_LIMITS[tier]


def reset_monthly_quota_if_needed(user: User, db: Session) -> None:
    """Reset monthly prediction counter at the start of each billing cycle."""
    now = datetime.utcnow()
    if user.month_reset_date is None or (now - user.month_reset_date).days >= 30:
        user.predictions_this_month = 0
        user.api_calls_this_month = 0
        user.month_reset_date = now
        db.commit()


def check_and_consume_prediction(user: User, is_premium: bool, db: Session) -> float:
    """
    Gate prediction access based on subscription + credits.
    Returns credits charged (0.0 if covered by subscription).
    Raises QuotaExceeded or InsufficientCredits if access denied.
    """
    reset_monthly_quota_if_needed(user, db)
    limits = get_tier_limits(user.subscription_tier)

    # Premium signals require Pro+ OR credits
    if is_premium and user.subscription_tier not in (SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE):
        if user.credits < CREDIT_COST_PREMIUM:
            raise InsufficientCredits(
                f"This is a premium signal. You need {CREDIT_COST_PREMIUM} credit(s). "
                f"Current balance: {user.credits:.1f}. Purchase credits or upgrade to Pro."
            )
        # Charge credit
        user.credits -= CREDIT_COST_PREMIUM
        credits_charged = CREDIT_COST_PREMIUM
        _record_transaction(
            db, user, TransactionType.CREDIT_SPEND,
            amount=-CREDIT_COST_PREMIUM * CREDIT_VALUE_USD,
            credits_delta=-CREDIT_COST_PREMIUM,
            description="Premium prediction signal",
        )
    else:
        credits_charged = 0.0

    # Check monthly quota (only for non-enterprise / non-credit-spend paths)
    max_monthly = limits["monthly_predictions"]
    if max_monthly != -1 and user.predictions_this_month >= max_monthly:
        raise QuotaExceeded(
            f"Monthly limit of {max_monthly} predictions reached for {user.subscription_tier} plan. "
            f"Upgrade your plan or purchase credits."
        )

    user.predictions_this_month += 1
    db.commit()
    return credits_charged


def can_access_market(user: User, market: str) -> bool:
    limits = get_tier_limits(user.subscription_tier)
    return market in limits["markets"]


def can_use_api(user: User) -> bool:
    return get_tier_limits(user.subscription_tier)["api_access"]


def purchase_credits(user: User, package_key: str, db: Session, stripe_payment_id: str = "mock") -> dict:
    """Add credits to user account after successful payment."""
    package = CREDIT_PACKAGES.get(package_key)
    if not package:
        raise ValueError(f"Unknown credit package: {package_key}")

    user.credits += package["credits"]
    _record_transaction(
        db, user, TransactionType.CREDIT_PURCHASE,
        amount=package["price_usd"],
        credits_delta=package["credits"],
        description=f"Credit purchase: {package['label']}",
        stripe_payment_id=stripe_payment_id,
    )
    db.commit()
    return {"credits_added": package["credits"], "new_balance": user.credits}


def activate_subscription(
    user: User,
    tier: SubscriptionTier,
    db: Session,
    stripe_payment_id: str = "mock",
    stripe_invoice_id: str = "mock",
) -> None:
    """Activate or upgrade a user subscription."""
    limits = get_tier_limits(tier)
    user.subscription_tier = tier
    user.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
    _record_transaction(
        db, user, TransactionType.SUBSCRIPTION,
        amount=limits["price_monthly"],
        description=f"Subscription: {tier.value} plan",
        stripe_payment_id=stripe_payment_id,
        stripe_invoice_id=stripe_invoice_id,
    )
    db.commit()


def cancel_subscription(user: User, db: Session) -> None:
    """Downgrade to free at end of billing period (don't revoke mid-cycle)."""
    user.subscription_tier = SubscriptionTier.FREE
    user.subscription_expires_at = None
    db.commit()


def get_revenue_summary(db: Session) -> dict:
    """Platform-wide revenue metrics."""
    from sqlalchemy import func
    from app.models.transaction import Transaction, TransactionType

    total_revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.amount > 0
    ).scalar() or 0.0

    subscription_revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.SUBSCRIPTION
    ).scalar() or 0.0

    credit_revenue = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.CREDIT_PURCHASE
    ).scalar() or 0.0

    user_tiers = {}
    for tier in SubscriptionTier:
        from app.models.user import User
        count = db.query(func.count(User.id)).filter(User.subscription_tier == tier).scalar()
        user_tiers[tier.value] = count

    return {
        "total_revenue_usd": round(total_revenue, 2),
        "subscription_revenue_usd": round(subscription_revenue, 2),
        "credit_revenue_usd": round(credit_revenue, 2),
        "users_by_tier": user_tiers,
        "mrr_estimate": round(subscription_revenue, 2),  # simplified
    }


def _record_transaction(
    db: Session,
    user: User,
    tx_type: TransactionType,
    amount: float,
    credits_delta: float = 0.0,
    description: str = "",
    stripe_payment_id: Optional[str] = None,
    stripe_invoice_id: Optional[str] = None,
) -> None:
    tx = Transaction(
        user_id=user.id,
        type=tx_type,
        amount=amount,
        credits_delta=credits_delta,
        description=description,
        stripe_payment_id=stripe_payment_id,
        stripe_invoice_id=stripe_invoice_id,
    )
    db.add(tx)
