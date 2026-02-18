from __future__ import annotations

from typing import Any

import pandas as pd


def predict_probability(model: Any, latest: pd.DataFrame, feature_order: list[str]) -> float:
    row = latest[feature_order].tail(1)
    return float(model.predict_proba(row)[:, 1][0])
