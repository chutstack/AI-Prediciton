from __future__ import annotations

import numpy as np
import pandas as pd


def generate_synthetic_ohlcv(symbol: str, periods: int = 1200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(abs(hash(symbol)) % (2**16) + seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=periods, freq="B")
    drift = 0.0003 if symbol == "SPY" else 0.0008
    vol = 0.01 if symbol == "SPY" else 0.025
    rets = rng.normal(drift, vol, size=periods)
    close = 100 * np.exp(np.cumsum(rets))
    open_ = close * (1 + rng.normal(0, vol / 3, size=periods))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0.001, 0.005, size=periods)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0.001, 0.005, size=periods)))
    volume = rng.integers(1_000, 20_000, size=periods).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=dates
    )
