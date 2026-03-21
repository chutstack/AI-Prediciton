"""
AI Prediction Platform — Main Application

Monetization model:
  ┌─────────────┬──────────┬──────────────┬───────────────────────────┐
  │ Tier        │ Price    │ Predictions  │ Features                  │
  ├─────────────┼──────────┼──────────────┼───────────────────────────┤
  │ Free        │ $0       │ 5/month      │ Sports only, basic signals│
  │ Basic       │ $9.99/mo │ 50/month     │ Sports + Crypto           │
  │ Pro         │ $29.99/mo│ 500/month    │ All markets, premium sigs │
  │ Enterprise  │ $99.99/mo│ Unlimited    │ API access, white-label   │
  └─────────────┴──────────┴──────────────┴───────────────────────────┘

  + Pay-per-prediction credits: $5 = 25 credits (for premium signals)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
from app.routes import auth, predictions, billing

# Seed public signals on startup for the demo teaser page
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_public_signals()
    yield


def _seed_public_signals():
    """Pre-populate a few public signals so the landing page isn't empty."""
    from app.database import SessionLocal
    from app.models.prediction import Prediction, MarketType
    from app.services.prediction_engine import generate_prediction

    db = SessionLocal()
    try:
        existing = db.query(Prediction).filter(Prediction.user_id == None).count()
        if existing >= 6:
            return
        for market in [MarketType.SPORTS, MarketType.CRYPTO, MarketType.SPORTS,
                       MarketType.CRYPTO, MarketType.SPORTS, MarketType.CRYPTO]:
            result = generate_prediction(market)
            db.add(Prediction(
                user_id=None,
                market=result.market,
                event_name=result.event_name,
                prediction_label=result.prediction_label,
                confidence=result.confidence,
                signal_strength=result.signal_strength,
                target_value=result.target_value,
                model_version=result.model_version,
                features_used=result.features,
                is_premium=result.is_premium_signal(),
                event_starts_at=result.event_starts_at,
            ))
        db.commit()
    finally:
        db.close()


app = FastAPI(
    title="AI Prediction Platform",
    description="Turn AI predictions into revenue. Tiered subscriptions, credit packs, and API access.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router)
app.include_router(predictions.router)
app.include_router(billing.router)

# Serve frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
static_dir = os.path.join(frontend_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(os.path.join(frontend_dir, "templates", "index.html"))


@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    return FileResponse(os.path.join(frontend_dir, "templates", "dashboard.html"))


@app.get("/pricing", include_in_schema=False)
def serve_pricing():
    return FileResponse(os.path.join(frontend_dir, "templates", "pricing.html"))


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
