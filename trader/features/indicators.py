from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_slope(series: pd.Series, window: int) -> pd.Series:
    x = np.arange(window)

    def _slope(vals: np.ndarray) -> float:
        if np.any(~np.isfinite(vals)):
            return np.nan
        y = vals
        x_mean = x.mean()
        y_mean = y.mean()
        num = ((x - x_mean) * (y - y_mean)).sum()
        den = ((x - x_mean) ** 2).sum()
        return float(num / den) if den else 0.0

    return np.log(series).rolling(window).apply(_slope, raw=True)


def atr14(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(14).mean()
