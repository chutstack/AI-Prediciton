from trader.risk.caps import apply_crypto_cap
from trader.risk.sizing import confidence_fraction, target_weight


def test_confidence_ladder_and_weight() -> None:
    assert confidence_fraction(0.57, 0.58) == 0.0
    assert confidence_fraction(0.60, 0.58) == 0.25
    w = target_weight(prob=0.75, p_long=0.60, sigma20=0.02, vol_target=0.01, cap=0.30)
    assert 0 <= w <= 0.30


def test_crypto_cap_scaling() -> None:
    out = apply_crypto_cap({"BTC-USD": 0.3, "ETH-USD": 0.3, "SPY": 0.5}, total_cap=0.4)
    assert abs(out["BTC-USD"] + out["ETH-USD"] - 0.4) < 1e-8
