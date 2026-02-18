from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

from trader.features.compute import make_dataset
from trader.model.artifacts import ArtifactStore
from trader.model.splitter import WalkForwardSplitter

try:
    from xgboost import XGBClassifier

    def build_model(params: dict[str, Any] | None = None) -> Any:
        base: dict[str, Any] = {
            "n_estimators": 180,
            "max_depth": 4,
            "learning_rate": 0.03,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "random_state": 42,
            "eval_metric": "logloss",
            "n_jobs": 1,
        }
        if params:
            base.update(params)
        return XGBClassifier(**base)


    def parameter_candidates() -> list[dict[str, Any]]:
        return [
            {"n_estimators": 120, "max_depth": 3, "learning_rate": 0.05, "subsample": 0.9, "colsample_bytree": 0.9},
            {"n_estimators": 180, "max_depth": 4, "learning_rate": 0.03, "subsample": 0.85, "colsample_bytree": 0.85},
            {"n_estimators": 240, "max_depth": 3, "learning_rate": 0.02, "subsample": 0.9, "colsample_bytree": 0.8},
            {"n_estimators": 220, "max_depth": 5, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.8},
        ]
except Exception:
    from sklearn.ensemble import GradientBoostingClassifier

    def build_model(params: dict[str, Any] | None = None) -> Any:
        base: dict[str, Any] = {"random_state": 42, "n_estimators": 150, "learning_rate": 0.05, "max_depth": 3}
        if params:
            base.update(params)
        return GradientBoostingClassifier(**base)

    def parameter_candidates() -> list[dict[str, Any]]:
        return [
            {"n_estimators": 120, "learning_rate": 0.08, "max_depth": 2},
            {"n_estimators": 180, "learning_rate": 0.05, "max_depth": 3},
            {"n_estimators": 240, "learning_rate": 0.03, "max_depth": 3},
        ]


def _evaluate_model(
    X: pd.DataFrame,
    y: pd.Series,
    splitter: WalkForwardSplitter,
    params: dict[str, Any] | None = None,
) -> tuple[float, float]:
    aucs: list[float] = []
    losses: list[float] = []
    for tr_idx, te_idx in splitter.split(X.index):
        y_tr = y.loc[tr_idx]
        if y_tr.nunique() < 2:
            continue
        scale_pos_weight = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))
        model_params = dict(params or {})
        if "scale_pos_weight" not in model_params:
            model_params["scale_pos_weight"] = scale_pos_weight
        model = build_model(model_params)
        model.fit(X.loc[tr_idx], y_tr)
        proba = model.predict_proba(X.loc[te_idx])[:, 1]
        y_te = y.loc[te_idx]
        if y_te.nunique() > 1:
            aucs.append(float(roc_auc_score(y_te, proba)))
        losses.append(float(log_loss(y_te, np.clip(proba, 1e-6, 1 - 1e-6))))
    mean_auc = float(np.mean(aucs)) if aucs else 0.5
    mean_logloss = float(np.mean(losses)) if losses else 0.693
    return mean_auc, mean_logloss


def _find_best_params(X: pd.DataFrame, y: pd.Series, splitter: WalkForwardSplitter) -> tuple[dict[str, Any], float, float]:
    best_params: dict[str, Any] = {}
    best_auc = -1.0
    best_logloss = float("inf")
    for params in parameter_candidates():
        auc, ll = _evaluate_model(X, y, splitter, params)
        if auc > best_auc or (np.isclose(auc, best_auc) and ll < best_logloss):
            best_auc = auc
            best_logloss = ll
            best_params = params
    return best_params, best_auc, best_logloss


def _optimize_cutoff(
    X: pd.DataFrame,
    y: pd.Series,
    splitter: WalkForwardSplitter,
    params: dict[str, Any],
    default_cutoff: float,
) -> float:
    thresholds = np.arange(0.50, 0.71, 0.01)
    scores = {float(t): [] for t in thresholds}

    for tr_idx, te_idx in splitter.split(X.index):
        y_tr = y.loc[tr_idx]
        if y_tr.nunique() < 2:
            continue
        scale_pos_weight = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))
        model_params = dict(params)
        model_params["scale_pos_weight"] = scale_pos_weight
        model = build_model(model_params)
        model.fit(X.loc[tr_idx], y_tr)
        proba = model.predict_proba(X.loc[te_idx])[:, 1]
        y_te = y.loc[te_idx].to_numpy()
        for th in thresholds:
            pred = (proba >= th).astype(int)
            tp = int(((pred == 1) & (y_te == 1)).sum())
            tn = int(((pred == 0) & (y_te == 0)).sum())
            fp = int(((pred == 1) & (y_te == 0)).sum())
            fn = int(((pred == 0) & (y_te == 1)).sum())
            tpr = tp / max(tp + fn, 1)
            tnr = tn / max(tn + fp, 1)
            scores[float(th)].append(0.5 * (tpr + tnr))

    best_t = default_cutoff
    best_score = -1.0
    for th, vals in scores.items():
        if not vals:
            continue
        s = float(np.mean(vals))
        if s > best_score:
            best_score = s
            best_t = th
    return float(best_t)


def train_asset(asset: str, prices: dict[str, pd.DataFrame], cfg: dict[str, Any], store: ArtifactStore) -> dict[str, float]:
    threshold = float(cfg["thresholds"][asset])
    default_p_long = float(cfg["p_long"][asset])
    X, y = make_dataset(asset, prices, threshold, include_crypto_for_spy=bool(cfg.get("include_crypto_for_spy", False)))
    splitter = WalkForwardSplitter(**cfg["walkforward"])

    best_params, best_auc, best_logloss = _find_best_params(X, y, splitter)
    calibrated_p_long = _optimize_cutoff(X, y, splitter, best_params, default_p_long)

    scale_pos_weight = float((y == 0).sum() / max((y == 1).sum(), 1))
    final_params = dict(best_params)
    final_params["scale_pos_weight"] = scale_pos_weight
    final_model = build_model(final_params)
    final_model.fit(X, y)

    meta = {
        "features": list(X.columns),
        "threshold": threshold,
        "p_long": calibrated_p_long,
        "p_long_default": default_p_long,
        "vol_target": cfg["vol_target"][asset],
        "per_asset_cap": cfg["caps"]["per_asset"][asset],
        "best_params": best_params,
        "cv_auc": best_auc,
        "cv_logloss": best_logloss,
        "trained_rows": int(len(X)),
        "timestamp": pd.Timestamp.utcnow().isoformat(),
    }
    store.save(asset, final_model, meta)
    return {"mean_auc": best_auc, "mean_logloss": best_logloss, "calibrated_p_long": calibrated_p_long}
