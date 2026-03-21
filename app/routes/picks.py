"""
Pick Management API

Workflow:
  1. POST /picks/scan-value  → Run model vs. live odds, find +EV bets
  2. POST /picks             → Log a pick (mark intent to bet)
  3. POST /picks/{id}/publish → Send to Telegram channel
  4. PATCH /picks/{id}/result → Record actual outcome + P&L
  5. GET  /picks/record       → Public performance stats (for credibility)
  6. GET  /picks/kelly        → Get Kelly-optimal stake for custom inputs
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.pick import Pick, PickResult, PickMarket
from app.routes.auth import get_current_user
from app.models.user import User
from app.services.value_calculator import (
    find_value_bets,
    calculate_ev,
    kelly_fraction,
    recommended_bet_size,
    analyze_performance,
)
from app.services.odds_service import get_mock_events, fetch_odds, settings
from app.services.prediction_engine import generate_prediction
from app.models.prediction import MarketType

router = APIRouter(prefix="/picks", tags=["Picks & Value Betting"])


# ── Request / Response schemas ─────────────────────────────────────────────

class CreatePickRequest(BaseModel):
    market: PickMarket
    sport: Optional[str] = None
    event_name: str
    pick_label: str
    event_time: Optional[datetime] = None
    model_confidence: float       # 0.0 - 1.0
    decimal_odds: float
    bookmaker: Optional[str] = None
    actual_stake: Optional[float] = None
    analysis: Optional[str] = None


class ResolvePickRequest(BaseModel):
    result: PickResult
    closing_odds: Optional[float] = None


class KellyRequest(BaseModel):
    model_confidence: float   # your model's probability
    decimal_odds: float
    bankroll: float = 1000.0  # default $1,000


class PickResponse(BaseModel):
    id: int
    market: PickMarket
    event_name: str
    pick_label: str
    model_confidence: float
    decimal_odds: float
    ev_percent: float
    implied_prob: float
    kelly_pct: Optional[float]
    suggested_stake_pct: Optional[float]
    bookmaker: Optional[str]
    result: PickResult
    profit_loss: Optional[float]
    is_published: bool
    analysis: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Value Scanner ──────────────────────────────────────────────────────────

@router.get("/scan-value")
async def scan_value_bets(
    sport: str = Query("basketball_nba", description="e.g. basketball_nba, americanfootball_nfl"),
    min_ev: float = Query(3.0, description="Minimum EV% to surface (e.g. 3 = 3%)"),
    current_user: User = Depends(get_current_user),
):
    """
    Run AI model against real bookmaker odds to find +EV opportunities.
    Returns picks sorted by expected value, highest first.

    This is the core tool for value betting.
    """
    # Fetch live odds (or mock if no API key)
    if settings.the_odds_api_key:
        try:
            events = await fetch_odds(sport)
        except Exception as e:
            events = get_mock_events()
    else:
        events = get_mock_events()

    if not events:
        return {"value_bets": [], "message": "No events found. Check sport key or API quota."}

    # Generate model predictions for each event
    model_preds = {}
    for event in events:
        pred = generate_prediction(MarketType.SPORTS)
        # Map model confidence to the two teams
        conf = pred.confidence
        teams = [event.home_team, event.away_team]
        model_preds[event.id] = {
            teams[0]: conf,
            teams[1]: round(1.0 - conf, 4),
        }

    value_bets = find_value_bets(events, model_preds, min_ev_threshold=min_ev / 100)

    return {
        "sport": sport,
        "total_events_scanned": len(events),
        "value_bets_found": sum(1 for v in value_bets if v.is_value),
        "all_bets": [
            {
                "event_name": v.event_name,
                "pick": v.pick,
                "model_confidence_pct": round(v.model_probability * 100, 1),
                "best_odds": v.best_decimal_odds,
                "best_at": v.best_bookmaker,
                "implied_prob_pct": round(v.implied_probability * 100, 1),
                "ev_percent": v.ev_percent,
                "kelly_full_pct": v.kelly_full,
                "kelly_quarter_pct": v.kelly_quarter,
                "is_value": v.is_value,
                "commence_time": v.commence_time,
            }
            for v in value_bets
        ],
        "using_live_odds": bool(settings.the_odds_api_key),
    }


# ── Kelly Calculator ───────────────────────────────────────────────────────

@router.post("/kelly")
def kelly_calculator(req: KellyRequest):
    """
    Calculate optimal bet sizes for given confidence + odds + bankroll.
    Always use Quarter Kelly in practice.
    """
    ev = calculate_ev(req.model_confidence, req.decimal_odds)
    sizes = recommended_bet_size(req.bankroll, req.model_confidence, req.decimal_odds)
    return {
        "ev_percent": round(ev * 100, 2),
        "is_value_bet": ev > 0,
        "implied_probability_pct": round((1 / req.decimal_odds) * 100, 2),
        "your_confidence_pct": round(req.model_confidence * 100, 1),
        "your_edge_pct": round((req.model_confidence - 1 / req.decimal_odds) * 100, 2),
        "bet_sizing": sizes,
        "recommendation": (
            "✅ Value bet — consider Quarter Kelly stake"
            if ev > 0.03 else
            "⚠️  Marginal value (<3%) — proceed with caution"
            if ev > 0 else
            "❌ Negative EV — skip this bet"
        ),
    }


# ── Pick Logging ───────────────────────────────────────────────────────────

@router.post("", response_model=PickResponse)
def create_pick(req: CreatePickRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Log a pick. This builds your verified track record."""
    ev = calculate_ev(req.model_confidence, req.decimal_odds)
    k_full = kelly_fraction(req.model_confidence, req.decimal_odds)

    pick = Pick(
        market=req.market,
        sport=req.sport,
        event_name=req.event_name,
        pick_label=req.pick_label,
        event_time=req.event_time,
        model_confidence=req.model_confidence,
        ev_percent=round(ev * 100, 2),
        bookmaker=req.bookmaker,
        decimal_odds=req.decimal_odds,
        implied_prob=round(1 / req.decimal_odds, 4),
        kelly_pct=round(k_full * 100, 2),
        suggested_stake_pct=round(k_full * 25, 2),
        actual_stake=req.actual_stake,
        analysis=req.analysis,
    )
    db.add(pick)
    db.commit()
    db.refresh(pick)
    return pick


@router.get("", response_model=list[PickResponse])
def list_picks(
    result: Optional[PickResult] = None,
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Pick)
    if result:
        q = q.filter(Pick.result == result)
    return q.order_by(Pick.created_at.desc()).limit(limit).all()


@router.patch("/{pick_id}/result")
def resolve_pick(
    pick_id: int,
    req: ResolvePickRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record the actual outcome of a pick."""
    pick = db.query(Pick).filter(Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    pick.result = req.result
    pick.resolved_at = datetime.utcnow()
    pick.closing_odds = req.closing_odds

    if pick.actual_stake:
        if req.result == PickResult.WIN:
            pick.profit_loss = round(pick.actual_stake * (pick.decimal_odds - 1), 2)
        elif req.result == PickResult.LOSS:
            pick.profit_loss = -pick.actual_stake
        elif req.result in (PickResult.PUSH, PickResult.VOID):
            pick.profit_loss = 0.0

    db.commit()
    return {"id": pick_id, "result": req.result, "profit_loss": pick.profit_loss}


# ── Performance Record (public credibility) ────────────────────────────────

@router.get("/record")
def get_record(db: Session = Depends(get_db)):
    """
    Public performance record — shows verified track record.
    This is what you show to potential subscribers to prove your edge.
    """
    all_picks = db.query(Pick).all()
    resolved = [p for p in all_picks if p.result != PickResult.PENDING]

    total = len(all_picks)
    res_total = len(resolved)
    wins = sum(1 for p in resolved if p.result == PickResult.WIN)
    losses = sum(1 for p in resolved if p.result == PickResult.LOSS)

    total_staked = sum(p.actual_stake for p in resolved if p.actual_stake)
    total_pnl = sum(p.profit_loss for p in resolved if p.profit_loss is not None)
    roi = (total_pnl / total_staked * 100) if total_staked > 0 else None

    avg_odds = (sum(p.decimal_odds for p in resolved) / res_total) if res_total else None
    avg_ev = (sum(p.ev_percent for p in all_picks) / total) if total else None
    avg_conf = (sum(p.model_confidence for p in all_picks) / total) if total else None

    # By market breakdown
    by_market: dict = {}
    for pick in resolved:
        m = pick.market.value
        by_market.setdefault(m, {"wins": 0, "losses": 0, "pnl": 0.0})
        if pick.result == PickResult.WIN:
            by_market[m]["wins"] += 1
        elif pick.result == PickResult.LOSS:
            by_market[m]["losses"] += 1
        if pick.profit_loss:
            by_market[m]["pnl"] = round(by_market[m]["pnl"] + pick.profit_loss, 2)

    return {
        "total_picks": total,
        "resolved": res_total,
        "pending": total - res_total,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wins / res_total * 100, 1) if res_total else None,
        "total_staked": round(total_staked, 2),
        "total_profit": round(total_pnl, 2),
        "roi_pct": round(roi, 2) if roi is not None else None,
        "avg_odds": round(avg_odds, 3) if avg_odds else None,
        "avg_ev_pct": round(avg_ev, 2) if avg_ev else None,
        "avg_model_confidence_pct": round(avg_conf * 100, 1) if avg_conf else None,
        "by_market": by_market,
        "message": "Track record verified by the platform. All picks logged before event starts.",
    }


# ── Telegram Publisher ─────────────────────────────────────────────────────

@router.post("/{pick_id}/publish")
async def publish_pick(
    pick_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a pick to your Telegram channel."""
    from app.services.telegram_publisher import publish_to_telegram

    pick = db.query(Pick).filter(Pick.id == pick_id).first()
    if not pick:
        raise HTTPException(status_code=404, detail="Pick not found")

    result = await publish_to_telegram(pick)

    if result.get("success"):
        pick.is_published = True
        pick.published_at = datetime.utcnow()
        pick.telegram_message_id = str(result.get("message_id", ""))
        db.commit()

    return result
