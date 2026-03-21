from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class MarketType(str, enum.Enum):
    SPORTS = "sports"
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FOREX = "forex"


class PredictionStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED_WIN = "resolved_win"
    RESOLVED_LOSS = "resolved_loss"
    CANCELLED = "cancelled"


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = public signal

    # What we're predicting
    market = Column(Enum(MarketType), nullable=False)
    event_name = Column(String, nullable=False)       # e.g. "BTC/USD", "Lakers vs Warriors"
    prediction_label = Column(String, nullable=False)  # e.g. "Price UP", "Home Win"
    target_value = Column(Float, nullable=True)        # e.g. target price $45,000

    # Model output
    confidence = Column(Float, nullable=False)         # 0.0-1.0
    signal_strength = Column(Float, nullable=False)    # 0.0-1.0 (edge over market)
    model_version = Column(String, default="v1")
    features_used = Column(JSON, nullable=True)        # feature importance snapshot

    # Outcome tracking
    status = Column(Enum(PredictionStatus), default=PredictionStatus.PENDING)
    actual_outcome = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    pnl = Column(Float, nullable=True)                 # profit/loss if tracked

    # Monetization flags
    is_premium = Column(Boolean, default=False)        # premium-only signal
    credits_charged = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    event_starts_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="predictions")
