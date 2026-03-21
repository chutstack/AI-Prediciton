"""
Seed demo data — creates sample users across all tiers for testing.
Run: python -m scripts.seed_demo
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import engine, SessionLocal, Base
from app.models.user import User, SubscriptionTier
from app.models.prediction import Prediction, MarketType
from app.services.auth import hash_password, generate_api_key
from app.services.prediction_engine import generate_prediction
from app.services.monetization import activate_subscription, purchase_credits

Base.metadata.create_all(bind=engine)
db = SessionLocal()

DEMO_USERS = [
    ("free@demo.com", "password", "Free User", SubscriptionTier.FREE),
    ("basic@demo.com", "password", "Basic User", SubscriptionTier.BASIC),
    ("pro@demo.com", "password", "Pro User", SubscriptionTier.PRO),
    ("enterprise@demo.com", "password", "Enterprise User", SubscriptionTier.ENTERPRISE),
]

for email, password, name, tier in DEMO_USERS:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"  Skipping {email} (already exists)")
        continue

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=name,
        credits=10.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if tier != SubscriptionTier.FREE:
        activate_subscription(user, tier, db, stripe_payment_id="seed", stripe_invoice_id="seed")

    if tier == SubscriptionTier.ENTERPRISE:
        user.api_key = generate_api_key()
        db.commit()

    # Generate some predictions for history
    for market in [MarketType.SPORTS, MarketType.CRYPTO]:
        for _ in range(3):
            r = generate_prediction(market)
            db.add(Prediction(
                user_id=user.id,
                market=r.market,
                event_name=r.event_name,
                prediction_label=r.prediction_label,
                confidence=r.confidence,
                signal_strength=r.signal_strength,
                target_value=r.target_value,
                model_version=r.model_version,
                features_used=r.features,
                is_premium=r.is_premium_signal(),
                event_starts_at=r.event_starts_at,
            ))
            user.predictions_this_month += 1
    db.commit()
    print(f"  Created {email} ({tier.value})")

db.close()
print("\nDemo users created! Login at http://localhost:8000")
print("  free@demo.com / password")
print("  basic@demo.com / password")
print("  pro@demo.com / password")
print("  enterprise@demo.com / password")
