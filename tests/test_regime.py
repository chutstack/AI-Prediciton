import numpy as np
import pandas as pd

from trader.features.compute import compute_features
from trader.risk.regime import regime_is_bad, regime_status


def test_regime_flag_returns_bool() -> None:
    idx = pd.date_range("2020-01-01", periods=300, freq="D")
    close = pd.Series(np.linspace(100, 130, len(idx)), index=idx)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1000.0,
        }
    )
    feats = compute_features(df)
    bad = regime_is_bad("SPY", feats)
    assert isinstance(bad, bool)


def test_regime_status_exposes_trigger_details() -> None:
    idx = pd.date_range("2020-01-01", periods=300, freq="D")
    close = pd.Series(np.linspace(100, 60, len(idx)), index=idx)
    df = pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1000.0,
        }
    )
    feats = compute_features(df)
    status = regime_status("SPY", feats)
    assert status["bad"] is True
    assert status["drawdown_breach"] is True
    assert status["drawdown"] > status["drawdown_limit"]
