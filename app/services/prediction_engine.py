"""
AI Prediction Engine

Generates predictions using ML models for different markets.
In production, replace the mock data fetchers with real APIs:
  - Sports: The Odds API, Sportradar, Pinnacle API
  - Crypto: Binance, CoinGecko, Messari
  - Stocks: Alpaca, Polygon.io, Yahoo Finance
  - Forex: OANDA, Alpha Vantage
"""
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

from app.models.prediction import MarketType


class PredictionResult:
    def __init__(
        self,
        event_name: str,
        market: MarketType,
        prediction_label: str,
        confidence: float,
        signal_strength: float,
        target_value: Optional[float],
        model_version: str,
        features: dict,
    ):
        self.event_name = event_name
        self.market = market
        self.prediction_label = prediction_label
        self.confidence = round(confidence, 4)
        self.signal_strength = round(signal_strength, 4)
        self.target_value = target_value
        self.model_version = model_version
        self.features = features
        self.event_starts_at = datetime.utcnow() + timedelta(hours=random.randint(1, 48))

    def is_premium_signal(self) -> bool:
        """High-confidence signals (>80%) are premium-only."""
        return self.confidence > 0.80 or self.signal_strength > 0.75


# ---------------------------------------------------------------------------
# Sports Prediction Model
# ---------------------------------------------------------------------------
SPORTS_EVENTS = [
    ("Lakers vs Warriors", ["Lakers Win", "Warriors Win", "Over 220.5 pts"]),
    ("Manchester City vs Arsenal", ["Man City Win", "Arsenal Win", "Draw", "Both Teams Score"]),
    ("Chiefs vs Eagles", ["Chiefs -3.5", "Eagles +3.5", "Over 48.5"]),
    ("Djokovic vs Alcaraz", ["Djokovic Win", "Alcaraz Win"]),
    ("Real Madrid vs Barcelona", ["Real Madrid Win", "Barcelona Win", "Draw"]),
]


def predict_sports(event_name: Optional[str] = None) -> PredictionResult:
    event, outcomes = random.choice(SPORTS_EVENTS) if not event_name else (event_name, ["Home Win", "Away Win"])

    # Simulate model features
    home_form = random.uniform(0.3, 0.9)
    away_form = random.uniform(0.3, 0.9)
    h2h_edge = random.uniform(-0.2, 0.2)
    market_movement = random.uniform(-0.15, 0.15)

    features = {
        "home_form_last5": round(home_form, 3),
        "away_form_last5": round(away_form, 3),
        "h2h_edge": round(h2h_edge, 3),
        "line_movement": round(market_movement, 3),
        "public_money_pct": round(random.uniform(0.3, 0.7), 3),
    }

    # Model output: logistic-style aggregation
    raw_score = (home_form - away_form) + h2h_edge + market_movement
    confidence = 1 / (1 + np.exp(-raw_score * 3))  # sigmoid
    confidence = float(np.clip(confidence, 0.52, 0.92))
    signal_strength = abs(raw_score) * random.uniform(0.4, 0.8)
    signal_strength = float(np.clip(signal_strength, 0.1, 0.9))

    label = outcomes[0] if raw_score > 0 else outcomes[min(1, len(outcomes) - 1)]

    return PredictionResult(
        event_name=event,
        market=MarketType.SPORTS,
        prediction_label=label,
        confidence=confidence,
        signal_strength=signal_strength,
        target_value=None,
        model_version="sports-v1.2",
        features=features,
    )


# ---------------------------------------------------------------------------
# Crypto Prediction Model
# ---------------------------------------------------------------------------
CRYPTO_PAIRS = ["BTC/USD", "ETH/USD", "SOL/USD", "BNB/USD", "XRP/USD"]


def predict_crypto(pair: Optional[str] = None) -> PredictionResult:
    symbol = pair or random.choice(CRYPTO_PAIRS)

    # Simulate technical indicators
    rsi = random.uniform(25, 75)
    macd_signal = random.uniform(-1, 1)
    bb_position = random.uniform(0, 1)     # position within Bollinger Bands
    volume_delta = random.uniform(-0.3, 0.5)
    sentiment_score = random.uniform(-0.5, 0.5)

    features = {
        "rsi_14": round(rsi, 2),
        "macd_signal": round(macd_signal, 4),
        "bb_position": round(bb_position, 3),
        "volume_delta_24h": round(volume_delta, 3),
        "social_sentiment": round(sentiment_score, 3),
        "fear_greed_index": random.randint(20, 80),
    }

    # Simple directional model
    bull_score = (
        (1 if rsi < 40 else -0.5 if rsi > 65 else 0)
        + macd_signal * 0.5
        + (1 - bb_position - 0.5)
        + volume_delta * 0.3
        + sentiment_score * 0.4
    )

    confidence = float(np.clip(0.5 + bull_score * 0.1, 0.50, 0.88))
    signal_strength = float(np.clip(abs(bull_score) * 0.3, 0.05, 0.85))

    direction = "LONG (Price UP)" if bull_score > 0 else "SHORT (Price DOWN)"

    # Estimate target price (mock current price)
    mock_prices = {"BTC/USD": 68000, "ETH/USD": 3400, "SOL/USD": 185, "BNB/USD": 610, "XRP/USD": 0.62}
    current_price = mock_prices.get(symbol, 100)
    target_pct = random.uniform(0.02, 0.08) * (1 if bull_score > 0 else -1)
    target_value = round(current_price * (1 + target_pct), 4)

    return PredictionResult(
        event_name=symbol,
        market=MarketType.CRYPTO,
        prediction_label=direction,
        confidence=confidence,
        signal_strength=signal_strength,
        target_value=target_value,
        model_version="crypto-v2.1",
        features=features,
    )


# ---------------------------------------------------------------------------
# Stock Prediction Model  (Pro+ only)
# ---------------------------------------------------------------------------
STOCKS = ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "META", "GOOGL"]


def predict_stock(ticker: Optional[str] = None) -> PredictionResult:
    symbol = ticker or random.choice(STOCKS)

    pe_ratio = random.uniform(15, 80)
    earnings_surprise = random.uniform(-0.1, 0.2)
    institutional_flow = random.uniform(-0.3, 0.5)
    momentum_score = random.uniform(-1, 1)
    analyst_consensus = random.uniform(0.3, 0.9)

    features = {
        "pe_ratio": round(pe_ratio, 2),
        "earnings_surprise": round(earnings_surprise, 4),
        "institutional_flow": round(institutional_flow, 3),
        "momentum_90d": round(momentum_score, 3),
        "analyst_buy_pct": round(analyst_consensus, 3),
    }

    bull_score = earnings_surprise * 2 + institutional_flow + momentum_score * 0.5 + (analyst_consensus - 0.5)
    confidence = float(np.clip(0.5 + bull_score * 0.08, 0.50, 0.87))
    signal_strength = float(np.clip(abs(bull_score) * 0.25, 0.05, 0.80))

    direction = "BUY" if bull_score > 0 else "SELL/SHORT"
    horizon = random.choice(["1-week", "2-week", "1-month"])

    return PredictionResult(
        event_name=f"{symbol} ({horizon} horizon)",
        market=MarketType.STOCKS,
        prediction_label=direction,
        confidence=confidence,
        signal_strength=signal_strength,
        target_value=None,
        model_version="stocks-v1.0",
        features=features,
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
def generate_prediction(market: MarketType, symbol: Optional[str] = None) -> PredictionResult:
    dispatchers = {
        MarketType.SPORTS: lambda: predict_sports(symbol),
        MarketType.CRYPTO: lambda: predict_crypto(symbol),
        MarketType.STOCKS: lambda: predict_stock(symbol),
    }
    fn = dispatchers.get(market)
    if fn is None:
        raise ValueError(f"Market '{market}' not supported yet.")
    return fn()
