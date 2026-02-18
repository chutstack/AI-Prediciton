import pandas as pd

from trader.data.synthetic import generate_synthetic_ohlcv
from trader.features.compute import make_dataset
from trader.model.splitter import WalkForwardSplitter
from trader.model.train import _find_best_params, _optimize_cutoff


def test_training_search_and_cutoff_optimization_ranges() -> None:
    prices = {
        "BTC-USD": generate_synthetic_ohlcv("BTC-USD", periods=420),
        "ETH-USD": generate_synthetic_ohlcv("ETH-USD", periods=420),
        "SPY": generate_synthetic_ohlcv("SPY", periods=420),
    }
    X, y = make_dataset("BTC-USD", prices, threshold=0.005)
    splitter = WalkForwardSplitter(train_days=220, test_days=50, step_days=50, embargo_days=1)

    params, auc, ll = _find_best_params(X, y, splitter)
    cutoff = _optimize_cutoff(X, y, splitter, params, default_cutoff=0.60)

    assert isinstance(params, dict)
    assert 0.0 <= auc <= 1.0
    assert ll > 0.0
    assert 0.50 <= cutoff <= 0.70
