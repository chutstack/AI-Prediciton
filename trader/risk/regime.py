from __future__ import annotations

import numpy as np
import pandas as pd


def regime_status(asset: str, feats: pd.DataFrame) -> dict[str, float | bool]:
    """Return per-rule regime checks for the latest bar."""
    vol20 = feats["vol20"]
    latest_vol20 = float(vol20.iloc[-1])
    p95 = float(vol20.rolling(252).quantile(0.95).iloc[-1])
    vol60 = float(feats["vol60"].iloc[-1])
    vol_ratio = float(feats["vol5"].iloc[-1] / max(vol60, 1e-9))
    close = feats["close"]
    drawdown = float(1 - close.iloc[-1] / close.rolling(252).max().iloc[-1])
    dd_limit = 0.18 if asset == "SPY" else 0.25

    vol_spike = bool(np.isfinite(p95) and latest_vol20 > p95)
    vol_ratio_spike = bool(vol_ratio > 2.2)
    drawdown_breach = bool(drawdown > dd_limit)
    bad = bool(vol_spike or vol_ratio_spike or drawdown_breach)
    return {
        "bad": bad,
        "vol20": latest_vol20,
        "vol20_p95": p95,
        "vol_spike": vol_spike,
        "vol_ratio": vol_ratio,
        "vol_ratio_spike": vol_ratio_spike,
        "drawdown": drawdown,
        "drawdown_limit": dd_limit,
        "drawdown_breach": drawdown_breach,
    }


def regime_is_bad(asset: str, feats: pd.DataFrame) -> bool:
    return bool(regime_status(asset, feats)["bad"])
