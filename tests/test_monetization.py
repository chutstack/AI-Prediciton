"""
Tests for the monetization service layer.
Run: pytest tests/
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.models.user import User, SubscriptionTier
from app.models.prediction import MarketType
from app.services.monetization import (
    check_and_consume_prediction,
    can_access_market,
    can_use_api,
    purchase_credits,
    activate_subscription,
    cancel_subscription,
    QuotaExceeded,
    InsufficientCredits,
    CREDIT_PACKAGES,
)


def make_user(tier=SubscriptionTier.FREE, credits=0.0, predictions_this_month=0):
    u = User()
    u.id = 1
    u.subscription_tier = tier
    u.credits = credits
    u.predictions_this_month = predictions_this_month
    u.month_reset_date = datetime.utcnow()
    u.api_key = None
    u.stripe_customer_id = None
    u.transactions = []
    return u


def make_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


# --- Market Access ---

def test_free_user_can_access_sports():
    user = make_user(SubscriptionTier.FREE)
    assert can_access_market(user, "sports") is True


def test_free_user_cannot_access_crypto():
    user = make_user(SubscriptionTier.FREE)
    assert can_access_market(user, "crypto") is False


def test_pro_user_can_access_all_markets():
    user = make_user(SubscriptionTier.PRO)
    for market in ["sports", "crypto", "stocks", "forex"]:
        assert can_access_market(user, market) is True


def test_api_access_only_for_enterprise():
    assert can_use_api(make_user(SubscriptionTier.FREE)) is False
    assert can_use_api(make_user(SubscriptionTier.BASIC)) is False
    assert can_use_api(make_user(SubscriptionTier.PRO)) is False
    assert can_use_api(make_user(SubscriptionTier.ENTERPRISE)) is True


# --- Quota Enforcement ---

def test_free_user_quota_exceeded():
    user = make_user(SubscriptionTier.FREE, predictions_this_month=5)
    db = make_db()
    with pytest.raises(QuotaExceeded):
        check_and_consume_prediction(user, is_premium=False, db=db)


def test_free_user_within_quota():
    user = make_user(SubscriptionTier.FREE, predictions_this_month=0)
    db = make_db()
    credits = check_and_consume_prediction(user, is_premium=False, db=db)
    assert credits == 0.0
    assert user.predictions_this_month == 1


def test_enterprise_user_no_quota():
    user = make_user(SubscriptionTier.ENTERPRISE, predictions_this_month=9999)
    db = make_db()
    # Should not raise
    credits = check_and_consume_prediction(user, is_premium=True, db=db)
    assert credits == 0.0


# --- Premium Signal Gating ---

def test_free_user_cannot_access_premium_without_credits():
    user = make_user(SubscriptionTier.FREE, credits=0.0)
    db = make_db()
    with pytest.raises(InsufficientCredits):
        check_and_consume_prediction(user, is_premium=True, db=db)


def test_free_user_premium_with_credits():
    user = make_user(SubscriptionTier.FREE, credits=3.0)
    db = make_db()
    credits_charged = check_and_consume_prediction(user, is_premium=True, db=db)
    assert credits_charged == 1.0
    assert user.credits == 2.0


def test_pro_user_premium_no_charge():
    user = make_user(SubscriptionTier.PRO, credits=0.0, predictions_this_month=0)
    db = make_db()
    credits_charged = check_and_consume_prediction(user, is_premium=True, db=db)
    assert credits_charged == 0.0


# --- Credit Purchases ---

def test_purchase_credits_starter():
    user = make_user(credits=0.0)
    db = make_db()
    result = purchase_credits(user, "starter", db, stripe_payment_id="test")
    assert result["credits_added"] == CREDIT_PACKAGES["starter"]["credits"]
    assert user.credits == CREDIT_PACKAGES["starter"]["credits"]


def test_purchase_invalid_package():
    user = make_user()
    db = make_db()
    with pytest.raises(ValueError):
        purchase_credits(user, "nonexistent", db)


# --- Subscription Lifecycle ---

def test_activate_subscription():
    user = make_user(SubscriptionTier.FREE)
    db = make_db()
    activate_subscription(user, SubscriptionTier.PRO, db)
    assert user.subscription_tier == SubscriptionTier.PRO
    assert user.subscription_expires_at is not None


def test_cancel_subscription():
    user = make_user(SubscriptionTier.PRO)
    db = make_db()
    cancel_subscription(user, db)
    assert user.subscription_tier == SubscriptionTier.FREE
    assert user.subscription_expires_at is None
