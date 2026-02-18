from __future__ import annotations


def apply_crypto_cap(weights: dict[str, float], total_cap: float = 0.4) -> dict[str, float]:
    crypto = [a for a in ["BTC-USD", "ETH-USD"] if a in weights]
    s = sum(weights[a] for a in crypto)
    if s <= total_cap or s <= 0:
        return weights
    scale = total_cap / s
    out = weights.copy()
    for a in crypto:
        out[a] *= scale
    return out
