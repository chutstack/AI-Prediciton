"""
Billing & Subscription Routes

Revenue model:
  1. Subscriptions via Stripe Checkout (recurring)
  2. Credit purchases (one-time payments)
  3. Webhook handler for Stripe events

To go live:
  - Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in .env
  - Create products/prices in Stripe dashboard
  - Set STRIPE_*_PRICE_ID env vars
  - Point your Stripe webhook to /billing/webhook
"""
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.database import get_db
from app.models.user import User, SubscriptionTier, TIER_LIMITS
from app.models.transaction import Transaction
from app.routes.auth import get_current_user
from app.services.monetization import (
    activate_subscription,
    cancel_subscription,
    purchase_credits,
    get_revenue_summary,
    CREDIT_PACKAGES,
)
from app.services.auth import generate_api_key

router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])

_stripe_key = getattr(settings, "stripe_secret_key", "")
stripe.api_key = _stripe_key

TIER_PRICE_MAP = {
    SubscriptionTier.BASIC: getattr(settings, "stripe_basic_price_id", ""),
    SubscriptionTier.PRO: getattr(settings, "stripe_pro_price_id", ""),
    SubscriptionTier.ENTERPRISE: getattr(settings, "stripe_enterprise_price_id", ""),
}


class SubscribeRequest(BaseModel):
    tier: SubscriptionTier
    success_url: str = "http://localhost:8000/dashboard?success=true"
    cancel_url: str = "http://localhost:8000/pricing"


class CreditPurchaseRequest(BaseModel):
    package: str  # starter | standard | pro


class MockPaymentRequest(BaseModel):
    """For demo/dev — skip real Stripe and directly activate."""
    tier: Optional[SubscriptionTier] = None
    credit_package: Optional[str] = None


@router.get("/plans")
def get_plans():
    """Return all available subscription plans with pricing."""
    return {
        tier.value: {
            "name": tier.value.capitalize(),
            **TIER_LIMITS[tier],
            "credit_packages": CREDIT_PACKAGES,
        }
        for tier in SubscriptionTier
    }


@router.post("/subscribe")
def create_checkout_session(
    req: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session for subscription."""
    if not _stripe_key or _stripe_key.startswith("sk_test_your"):
        raise HTTPException(
            status_code=503,
            detail="Stripe not configured. Use /billing/demo-activate for testing."
        )

    price_id = TIER_PRICE_MAP.get(req.tier)
    if not price_id:
        raise HTTPException(status_code=400, detail="Cannot subscribe to free tier via checkout.")

    # Create or retrieve Stripe customer
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(email=current_user.email)
        current_user.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=req.success_url,
        cancel_url=req.cancel_url,
        metadata={"user_id": current_user.id, "tier": req.tier.value},
    )
    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/buy-credits")
def buy_credits_checkout(
    req: CreditPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session for one-time credit purchase."""
    if req.package not in CREDIT_PACKAGES:
        raise HTTPException(status_code=400, detail=f"Unknown package. Choose: {list(CREDIT_PACKAGES.keys())}")

    if not _stripe_key or _stripe_key.startswith("sk_test_your"):
        raise HTTPException(
            status_code=503,
            detail="Stripe not configured. Use /billing/demo-activate for testing."
        )

    pkg = CREDIT_PACKAGES[req.package]
    # In production: create a Stripe Price for each package or use price_data
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"AI Prediction Credits — {pkg['label']}"},
                "unit_amount": int(pkg["price_usd"] * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="http://localhost:8000/dashboard?credits=true",
        cancel_url="http://localhost:8000/pricing",
        metadata={"user_id": current_user.id, "credit_package": req.package},
    )
    return {"checkout_url": session.url}


@router.post("/demo-activate")
def demo_activate(
    req: MockPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    DEMO ONLY — instantly activate subscription or credits without real payment.
    Remove this endpoint in production.
    """
    result = {}
    if req.tier and req.tier != SubscriptionTier.FREE:
        activate_subscription(current_user, req.tier, db, stripe_payment_id="demo", stripe_invoice_id="demo")
        result["subscription"] = req.tier.value

        # Grant API key for Enterprise
        if req.tier == SubscriptionTier.ENTERPRISE and not current_user.api_key:
            current_user.api_key = generate_api_key()
            db.commit()
            result["api_key"] = current_user.api_key

    if req.credit_package:
        credit_result = purchase_credits(current_user, req.credit_package, db, stripe_payment_id="demo")
        result["credits"] = credit_result

    return {"success": True, **result}


@router.post("/cancel")
def cancel(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel subscription — downgrade to free immediately (for demo)."""
    cancel_subscription(current_user, db)
    return {"message": "Subscription cancelled. Downgraded to Free tier."}


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Stripe webhook endpoint.
    Handles: checkout.session.completed, invoice.paid, customer.subscription.deleted
    """
    if not getattr(settings, "stripe_webhook_secret", ""):
        raise HTTPException(status_code=503, detail="Webhook secret not configured.")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, getattr(settings, "stripe_webhook_secret", ""))
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    db = next(get_db())
    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = int(session["metadata"]["user_id"])
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"status": "user_not_found"}

            if "tier" in session["metadata"]:
                tier = SubscriptionTier(session["metadata"]["tier"])
                activate_subscription(user, tier, db,
                                      stripe_payment_id=session.get("payment_intent", ""),
                                      stripe_invoice_id=session.get("invoice", ""))
                if tier == SubscriptionTier.ENTERPRISE and not user.api_key:
                    user.api_key = generate_api_key()
                    db.commit()

            elif "credit_package" in session["metadata"]:
                purchase_credits(user, session["metadata"]["credit_package"], db,
                                 stripe_payment_id=session.get("payment_intent", ""))

        elif event["type"] == "customer.subscription.deleted":
            # Subscription cancelled from Stripe dashboard
            customer_id = event["data"]["object"]["customer"]
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                cancel_subscription(user, db)

    finally:
        db.close()

    return {"status": "ok"}


@router.get("/revenue")
def revenue_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin: platform-wide revenue metrics."""
    # In production, add admin role check
    return get_revenue_summary(db)


@router.get("/transactions")
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User's billing history."""
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": t.id,
            "type": t.type,
            "amount": t.amount,
            "credits_delta": t.credits_delta,
            "description": t.description,
            "created_at": t.created_at,
        }
        for t in txs
    ]
