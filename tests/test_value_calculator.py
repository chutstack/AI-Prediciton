"""Tests for EV calculation and Kelly criterion."""
import pytest
from app.services.value_calculator import (
    calculate_ev,
    kelly_fraction,
    recommended_bet_size,
    find_value_bets,
)
from app.services.odds_service import get_mock_events


def test_ev_positive_when_model_above_implied():
    # Model says 60%, odds imply 50% (2.0 decimal) → positive EV
    ev = calculate_ev(0.60, 2.0)
    assert ev > 0
    assert round(ev, 2) == 0.20  # +20%


def test_ev_negative_when_model_below_implied():
    # Model says 45%, odds imply 52.6% (1.90) → negative EV
    ev = calculate_ev(0.45, 1.90)
    assert ev < 0


def test_ev_zero_at_fair_value():
    # Model exactly matches implied probability → EV ≈ 0
    ev = calculate_ev(0.5, 2.0)
    assert abs(ev) < 1e-9


def test_kelly_positive_when_edge_exists():
    k = kelly_fraction(0.60, 2.0)
    assert k > 0
    assert k == 0.20  # (1*0.6 - 0.4) / 1 = 0.20


def test_kelly_zero_when_no_edge():
    # No edge (coin flip at fair odds)
    k = kelly_fraction(0.50, 2.0)
    assert k == 0.0


def test_kelly_zero_when_negative_ev():
    k = kelly_fraction(0.45, 1.90)
    assert k == 0.0


def test_recommended_bet_size_structure():
    sizes = recommended_bet_size(1000.0, 0.60, 2.0)
    assert "full_kelly_usd" in sizes
    assert "quarter_kelly_usd" in sizes
    assert "flat_1pct_usd" in sizes
    assert sizes["flat_1pct_usd"] == 10.0
    # Quarter Kelly should be ≤ Half Kelly ≤ Full Kelly
    assert sizes["quarter_kelly_usd"] <= sizes["half_kelly_usd"] <= sizes["full_kelly_usd"]


def test_find_value_bets_with_mock_events():
    events = get_mock_events()
    # Assign model probabilities that guarantee value on home team
    model_preds = {
        e.id: {
            e.home_team: 0.75,   # Strong model edge
            e.away_team: 0.25,
        }
        for e in events
    }
    value_bets = find_value_bets(events, model_preds, min_ev_threshold=0.03)
    assert len(value_bets) > 0
    # All should be positive EV given 75% confidence
    positive_ev = [v for v in value_bets if v.is_value]
    assert len(positive_ev) > 0


def test_find_value_bets_sorted_by_ev():
    events = get_mock_events()
    model_preds = {e.id: {e.home_team: 0.70, e.away_team: 0.30} for e in events}
    bets = find_value_bets(events, model_preds, min_ev_threshold=0.0)
    ev_values = [b.ev_percent for b in bets]
    assert ev_values == sorted(ev_values, reverse=True)


def test_no_value_bets_when_model_weak():
    events = get_mock_events()
    # Both teams assigned very low confidence → below implied probability → all negative EV
    # Mock odds imply ~50-55% for home, ~45-50% for away — set model well below both
    model_preds = {e.id: {e.home_team: 0.25, e.away_team: 0.30} for e in events}
    bets = find_value_bets(events, model_preds, min_ev_threshold=0.05)
    value = [b for b in bets if b.is_value]
    assert len(value) == 0
