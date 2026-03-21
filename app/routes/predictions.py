from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.prediction import Prediction, MarketType, PredictionStatus
from app.models.user import User, TIER_LIMITS
from app.routes.auth import get_current_user
from app.services.prediction_engine import generate_prediction
from app.services.monetization import (
    check_and_consume_prediction,
    can_access_market,
    QuotaExceeded,
    InsufficientCredits,
)

router = APIRouter(prefix="/predictions", tags=["Predictions"])


class PredictionRequest(BaseModel):
    market: MarketType
    symbol: Optional[str] = None  # e.g. "BTC/USD", "AAPL", specific event name


class PredictionResponse(BaseModel):
    id: int
    market: MarketType
    event_name: str
    prediction_label: str
    confidence: float
    signal_strength: float
    target_value: Optional[float]
    model_version: str
    is_premium: bool
    credits_charged: float
    status: PredictionStatus
    created_at: datetime
    event_starts_at: Optional[datetime]
    features_used: Optional[dict]

    class Config:
        from_attributes = True


class PublicSignal(BaseModel):
    """Stripped-down signal shown to non-authenticated / free users (teaser)."""
    market: MarketType
    event_name: str
    prediction_label: str
    confidence_band: str  # e.g. "High (>80%)" — hides exact value
    is_premium: bool
    teaser: str


@router.get("/public", response_model=List[PublicSignal])
def get_public_signals(db: Session = Depends(get_db)):
    """
    Free teaser signals — no auth required.
    Shows recent predictions with confidence blurred to encourage sign-up.
    """
    recent = (
        db.query(Prediction)
        .filter(Prediction.user_id == None)
        .order_by(Prediction.created_at.desc())
        .limit(6)
        .all()
    )

    results = []
    for p in recent:
        if p.confidence >= 0.80:
            band = "High (80%+)"
        elif p.confidence >= 0.65:
            band = "Medium (65-80%)"
        else:
            band = "Standard (50-65%)"

        results.append(PublicSignal(
            market=p.market,
            event_name=p.event_name,
            prediction_label=p.prediction_label if not p.is_premium else "🔒 Premium Signal",
            confidence_band=band,
            is_premium=p.is_premium,
            teaser="Sign up to see full confidence, signal strength, and model features.",
        ))
    return results


@router.post("/generate", response_model=PredictionResponse)
def generate(
    req: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a new AI prediction.
    - Market access depends on subscription tier.
    - Premium signals require Pro+ or credits.
    """
    if not can_access_market(current_user, req.market.value):
        allowed = TIER_LIMITS[current_user.subscription_tier]["markets"]
        raise HTTPException(
            status_code=403,
            detail=f"Market '{req.market}' not available on your plan. Allowed: {allowed}. Upgrade to access more markets."
        )

    result = generate_prediction(req.market, req.symbol)

    try:
        credits_charged = check_and_consume_prediction(current_user, result.is_premium_signal(), db)
    except (QuotaExceeded, InsufficientCredits) as e:
        raise HTTPException(status_code=402, detail=str(e))

    prediction = Prediction(
        user_id=current_user.id,
        market=result.market,
        event_name=result.event_name,
        prediction_label=result.prediction_label,
        confidence=result.confidence,
        signal_strength=result.signal_strength,
        target_value=result.target_value,
        model_version=result.model_version,
        features_used=result.features,
        is_premium=result.is_premium_signal(),
        credits_charged=credits_charged,
        event_starts_at=result.event_starts_at,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.get("/history", response_model=List[PredictionResponse])
def get_history(
    limit: int = Query(20, le=100),
    market: Optional[MarketType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the user's prediction history."""
    q = db.query(Prediction).filter(Prediction.user_id == current_user.id)
    if market:
        q = q.filter(Prediction.market == market)
    return q.order_by(Prediction.created_at.desc()).limit(limit).all()


@router.get("/stats")
def get_prediction_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Win rate and performance stats for the user's predictions."""
    preds = db.query(Prediction).filter(
        Prediction.user_id == current_user.id,
        Prediction.status != PredictionStatus.PENDING,
    ).all()

    total = len(preds)
    wins = sum(1 for p in preds if p.status == PredictionStatus.RESOLVED_WIN)
    win_rate = wins / total if total else None

    limits = TIER_LIMITS[current_user.subscription_tier]
    quota_used = current_user.predictions_this_month
    quota_max = limits["monthly_predictions"]

    return {
        "total_predictions": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate": round(win_rate * 100, 1) if win_rate is not None else None,
        "predictions_this_month": quota_used,
        "monthly_quota": quota_max if quota_max != -1 else "unlimited",
        "credits_balance": current_user.credits,
        "subscription": current_user.subscription_tier,
    }
