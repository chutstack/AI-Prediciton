from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TransactionType(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    CREDIT_PURCHASE = "credit_purchase"
    CREDIT_SPEND = "credit_spend"
    REFUND = "refund"
    AFFILIATE_PAYOUT = "affiliate_payout"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)      # positive = revenue, negative = payout
    credits_delta = Column(Float, default=0.0)  # change in user credit balance
    description = Column(String)
    stripe_payment_id = Column(String, nullable=True)
    stripe_invoice_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
