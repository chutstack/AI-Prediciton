"""Technical-indicator feature engineering."""
from __future__ import annotations

import pandas as pd


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add common technical indicators to an OHLCV DataFrame."""
    try:
        import ta
    except ImportError as exc:
        raise ImportError("ta is required: pip install ta") from exc

    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Trend
    df["sma_20"] = ta.trend.sma_indicator(close, window=20)
    df["sma_50"] = ta.trend.sma_indicator(close, window=50)
    df["ema_12"] = ta.trend.ema_indicator(close, window=12)
    df["ema_26"] = ta.trend.ema_indicator(close, window=26)
    df["macd"] = ta.trend.macd(close)
    df["macd_signal"] = ta.trend.macd_signal(close)

    # Momentum
    df["rsi"] = ta.momentum.rsi(close, window=14)
    df["stoch_k"] = ta.momentum.stoch(high, low, close)
    df["stoch_d"] = ta.momentum.stoch_signal(high, low, close)

    # Volatility
    df["bb_upper"] = ta.volatility.bollinger_hband(close)
    df["bb_lower"] = ta.volatility.bollinger_lband(close)
    df["atr"] = ta.volatility.average_true_range(high, low, close)

    # Volume
    df["obv"] = ta.volume.on_balance_volume(close, volume)

    return df


def build_features(df: pd.DataFrame, horizon: int = 1) -> tuple[pd.DataFrame, pd.Series]:
    """Return feature matrix X and binary target y.

    Target: 1 if Close rises over the next *horizon* trading days, else 0.
    """
    df = add_technical_indicators(df)

    # Price-derived features
    df["return_1d"] = df["Close"].pct_change(1)
    df["return_5d"] = df["Close"].pct_change(5)
    df["return_10d"] = df["Close"].pct_change(10)
    df["volume_change"] = df["Volume"].pct_change(1)

    # Target
    df["target"] = (df["Close"].shift(-horizon) > df["Close"]).astype(int)

    df = df.dropna()

    feature_cols = [
        "sma_20", "sma_50", "ema_12", "ema_26", "macd", "macd_signal",
        "rsi", "stoch_k", "stoch_d", "bb_upper", "bb_lower", "atr", "obv",
        "return_1d", "return_5d", "return_10d", "volume_change",
    ]

    X = df[feature_cols]
    y = df["target"]
    return X, y
