from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"        # $9.99/mo  - 50 predictions/mo
    PRO = "pro"            # $29.99/mo - 500 predictions/mo + advanced signals
    ENTERPRISE = "enterprise"  # $99.99/mo - unlimited + API access + white-label


TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "monthly_predictions": 5,
        "markets": ["sports"],
        "signal_quality": "basic",
        "api_access": False,
        "advanced_analytics": False,
        "price_monthly": 0.0,
    },
    SubscriptionTier.BASIC: {
        "monthly_predictions": 50,
        "markets": ["sports", "crypto"],
        "signal_quality": "standard",
        "api_access": False,
        "advanced_analytics": False,
        "price_monthly": 9.99,
    },
    SubscriptionTier.PRO: {
        "monthly_predictions": 500,
        "markets": ["sports", "crypto", "stocks", "forex"],
        "signal_quality": "premium",
        "api_access": False,
        "advanced_analytics": True,
        "price_monthly": 29.99,
    },
    SubscriptionTier.ENTERPRISE: {
        "monthly_predictions": -1,  # unlimited
        "markets": ["sports", "crypto", "stocks", "forex", "custom"],
        "signal_quality": "elite",
        "api_access": True,
        "advanced_analytics": True,
        "price_monthly": 99.99,
    },
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)

    # Monetization
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)
    credits = Column(Float, default=0.0)  # pay-per-prediction credits ($0.25/credit)
    stripe_customer_id = Column(String, nullable=True)

    # Usage tracking
    predictions_this_month = Column(Integer, default=0)
    month_reset_date = Column(DateTime, default=datetime.utcnow)

    # API access (Enterprise)
    api_key = Column(String, unique=True, nullable=True)
    api_calls_this_month = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
