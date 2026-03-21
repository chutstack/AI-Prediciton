"""
Pick — a formal betting recommendation with full accountability.

This is the core credibility engine. Every pick is logged with:
  - Your model's confidence at time of pick
  - The odds you got (line shopped)
  - EV% at time of bet
  - Recommended stake (Kelly)
  - Actual outcome + P&L

A verified public track record is what makes your picks worth selling.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class PickResult(str, enum.Enum):
    PENDING = "pending"
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"       # tie/refund
    VOID = "void"       # cancelled event


class PickMarket(str, enum.Enum):
    SPORTS = "sports"
    CRYPTO = "crypto"
    PREDICTION_MARKET = "prediction_market"  # Polymarket, Kalshi


class Pick(Base):
    __tablename__ = "picks"

    id = Column(Integer, primary_key=True, index=True)

    # What the pick is
    market = Column(Enum(PickMarket), nullable=False)
    sport = Column(String, nullable=True)             # e.g. basketball_nba
    event_name = Column(String, nullable=False)       # "Lakers vs Warriors"
    pick_label = Column(String, nullable=False)       # "Los Angeles Lakers ML"
    event_time = Column(DateTime, nullable=True)

    # Model data at time of pick
    model_confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    ev_percent = Column(Float, nullable=False)        # Expected value %
    bookmaker = Column(String, nullable=True)         # Where to bet
    decimal_odds = Column(Float, nullable=False)      # Odds at time of pick
    implied_prob = Column(Float, nullable=False)      # Bookmaker's implied prob

    # Stake management
    kelly_pct = Column(Float, nullable=True)          # Recommended Kelly %
    suggested_stake_pct = Column(Float, nullable=True) # Quarter Kelly (recommended)
    actual_stake = Column(Float, nullable=True)       # What user actually bet ($)

    # Outcome
    result = Column(Enum(PickResult), default=PickResult.PENDING)
    profit_loss = Column(Float, nullable=True)        # Dollar P&L
    closing_odds = Column(Float, nullable=True)       # Odds at event start (CLV)
    resolved_at = Column(DateTime, nullable=True)

    # Publishing
    is_published = Column(Boolean, default=False)     # Sent to Telegram/Discord
    published_at = Column(DateTime, nullable=True)
    telegram_message_id = Column(String, nullable=True)

    # Notes
    analysis = Column(String, nullable=True)          # Your written rationale

    created_at = Column(DateTime, default=datetime.utcnow)
