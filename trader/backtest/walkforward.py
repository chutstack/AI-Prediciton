from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

from trader.features.compute import make_dataset
from trader.model.splitter import WalkForwardSplitter
from trader.model.train import build_model


def run_walkforward(prices: dict[str, pd.DataFrame], cfg: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for asset in cfg["assets"]:
        X, y = make_dataset(asset, prices, cfg["thresholds"][asset])
        splitter = WalkForwardSplitter(**cfg["walkforward"])
        for i, (tr, te) in enumerate(splitter.split(X.index)):
            y_tr = y.loc[tr]
            if y_tr.nunique() < 2:
                continue
            scale_pos_weight = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))
            model = build_model({"scale_pos_weight": scale_pos_weight})
            model.fit(X.loc[tr], y_tr)
            p = model.predict_proba(X.loc[te])[:, 1]
            pred = (p >= cfg["p_long"][asset]).astype(int)
            y_te = y.loc[te].values
            acc = float((pred == y_te).mean())
            auc = float(roc_auc_score(y_te, p)) if len(np.unique(y_te)) > 1 else 0.5
            ll = float(log_loss(y_te, np.clip(p, 1e-6, 1 - 1e-6)))
            rows.append({"asset": asset, "split": i, "accuracy": acc, "auc": auc, "logloss": ll, "n_test": len(te)})
    return pd.DataFrame(rows)
