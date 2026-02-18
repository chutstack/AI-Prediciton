import pandas as pd

from trader.data.synthetic import generate_synthetic_ohlcv
from trader.features.compute import compute_features


def test_feature_generation_has_expected_columns() -> None:
    df = generate_synthetic_ohlcv("BTC-USD", periods=300)
    feats = compute_features(df)
    expected = {"r1", "r5", "sma20_dist", "slope20", "atr_pct", "distance_from_high_20"}
    assert expected.issubset(set(feats.columns))
    assert feats.dropna().shape[0] > 0
