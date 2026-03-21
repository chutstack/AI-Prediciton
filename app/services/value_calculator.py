"""
Value Betting + Kelly Criterion Calculator

The core math for finding +EV bets and sizing them correctly.

Key concepts:
  - EV% = (model_probability × decimal_odds) - 1
    Positive EV means you have an edge over the bookmaker.
    A bet with 5% EV means for every $100 bet you expect $5 profit.

  - Kelly fraction = (edge / odds_ratio) = (b*p - q) / b
    Tells you what % of your bankroll to bet to maximize long-term growth.
    Always use Fractional Kelly (25-33%) to reduce variance.

  - Line shopping: Always bet at the highest available odds for your pick.
    The difference between 1.90 and 2.00 is the difference between -5% EV and +5% EV.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ValueBet:
    event_name: str
    sport: str
    pick: str                    # Team/outcome name
    model_probability: float     # Your model's confidence (0.0 - 1.0)
    best_decimal_odds: float     # Best odds available across bookmakers
    best_bookmaker: str
    implied_probability: float   # What bookmaker thinks (1 / odds)
    ev_percent: float            # Expected value as %
    kelly_full: float            # Full Kelly fraction
    kelly_quarter: float         # Quarter Kelly (recommended)
    is_value: bool               # True if EV > threshold
    commence_time: str


def calculate_ev(model_prob: float, decimal_odds: float) -> float:
    """
    Expected value as a percentage of stake.
    EV% = (p × odds) - 1
    Example: model says 60%, odds are 2.10 → EV = (0.60 × 2.10) - 1 = 0.26 = +26%
    """
    return (model_prob * decimal_odds) - 1.0


def kelly_fraction(model_prob: float, decimal_odds: float) -> float:
    """
    Full Kelly criterion.
    f = (b*p - q) / b  where b = decimal_odds - 1, q = 1 - p
    Returns fraction of bankroll to bet (0 if no edge).
    """
    b = decimal_odds - 1.0
    p = model_prob
    q = 1.0 - p
    if b <= 0:
        return 0.0
    k = (b * p - q) / b
    return max(0.0, round(k, 4))


def recommended_bet_size(bankroll: float, model_prob: float, decimal_odds: float) -> dict:
    """
    Calculate safe bet sizes at different Kelly fractions.
    Returns absolute dollar amounts for a given bankroll.
    """
    full_k = kelly_fraction(model_prob, decimal_odds)
    return {
        "full_kelly_pct": round(full_k * 100, 2),
        "full_kelly_usd": round(bankroll * full_k, 2),
        "half_kelly_pct": round(full_k * 50, 2),
        "half_kelly_usd": round(bankroll * full_k * 0.5, 2),
        "quarter_kelly_pct": round(full_k * 25, 2),
        "quarter_kelly_usd": round(bankroll * full_k * 0.25, 2),  # Recommended
        "flat_1pct_usd": round(bankroll * 0.01, 2),               # Conservative floor
    }


def find_value_bets(
    events: list,
    model_predictions: dict,    # {event_id: {team_name: model_prob}}
    min_ev_threshold: float = 0.03,  # Only surface 3%+ EV bets
) -> list[ValueBet]:
    """
    Cross-reference model predictions against live bookmaker odds.
    Returns list of +EV opportunities sorted by EV%.

    model_predictions format:
    {
        "event_id": {
            "Los Angeles Lakers": 0.62,
            "Golden State Warriors": 0.38,
        }
    }
    """
    value_bets = []

    for event in events:
        preds = model_predictions.get(event.id, {})
        if not preds:
            continue

        all_odds = event.all_h2h_odds()

        for team, model_prob in preds.items():
            odds_list = all_odds.get(team, [])
            if not odds_list:
                continue

            # Find best available odds (line shopping)
            best_bookmaker, best_odds = max(odds_list, key=lambda x: x[1])
            implied_prob = 1.0 / best_odds
            ev = calculate_ev(model_prob, best_odds)
            k_full = kelly_fraction(model_prob, best_odds)

            value_bets.append(ValueBet(
                event_name=f"{event.home_team} vs {event.away_team}",
                sport=event.sport,
                pick=team,
                model_probability=round(model_prob, 4),
                best_decimal_odds=best_odds,
                best_bookmaker=best_bookmaker,
                implied_probability=round(implied_prob, 4),
                ev_percent=round(ev * 100, 2),
                kelly_full=round(k_full * 100, 2),
                kelly_quarter=round(k_full * 25, 2),
                is_value=ev >= min_ev_threshold,
                commence_time=event.commence_time,
            ))

    # Sort by EV% descending, value bets first
    value_bets.sort(key=lambda x: x.ev_percent, reverse=True)
    return value_bets


def analyze_performance(picks: list) -> dict:
    """
    Calculate ROI, win rate, and CLV (closing line value) from resolved picks.
    CLV = your odds vs closing odds — positive CLV means you beat the market.
    """
    resolved = [p for p in picks if p.get("resolved")]
    if not resolved:
        return {"total": 0, "message": "No resolved picks yet."}

    total_staked = sum(p["stake"] for p in resolved)
    total_return = sum(p["stake"] * p["decimal_odds"] for p in resolved if p.get("won"))
    profit = total_return - total_staked
    roi = (profit / total_staked * 100) if total_staked > 0 else 0
    wins = sum(1 for p in resolved if p.get("won"))
    win_rate = wins / len(resolved) * 100

    avg_ev = sum(p.get("ev_at_time", 0) for p in resolved) / len(resolved)
    avg_odds = sum(p["decimal_odds"] for p in resolved) / len(resolved)

    # At these avg odds, breakeven win rate
    breakeven_wr = (1 / avg_odds) * 100

    return {
        "total_picks": len(resolved),
        "wins": wins,
        "losses": len(resolved) - wins,
        "win_rate_pct": round(win_rate, 1),
        "breakeven_win_rate_pct": round(breakeven_wr, 1),
        "total_staked": round(total_staked, 2),
        "total_profit": round(profit, 2),
        "roi_pct": round(roi, 2),
        "avg_odds": round(avg_odds, 3),
        "avg_ev_at_bet": round(avg_ev, 2),
        "edge_over_market": round(roi - 0, 2),  # simplified — real CLV needs closing lines
    }
