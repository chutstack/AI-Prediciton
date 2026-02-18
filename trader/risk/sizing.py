from __future__ import annotations

import numpy as np


def confidence_fraction(prob: float, p_long: float) -> float:
    if prob < p_long:
        return 0.0
    if prob < p_long + 0.04:
        return 0.25
    if prob < p_long + 0.08:
        return 0.50
    if prob < p_long + 0.12:
        return 0.75
    return 1.0


def target_weight(prob: float, p_long: float, sigma20: float, vol_target: float, cap: float) -> float:
    raw = vol_target / max(sigma20, 1e-8)
    return float(np.clip(raw, 0.0, cap) * confidence_fraction(prob, p_long))
