"""Model training and persistence."""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

MODELS_DIR = Path(__file__).parent.parent.parent / ".models"


class ModelTrainer:
    """Train and evaluate a RandomForest classifier for price-direction forecasting."""

    def __init__(self, ticker: str, n_estimators: int = 200, horizon: int = 1):
        self.ticker = ticker.upper()
        self.n_estimators = n_estimators
        self.horizon = horizon
        self.model: RandomForestClassifier | None = None
        self.scaler: StandardScaler | None = None
        self._model_path = MODELS_DIR / f"{self.ticker}_model.pkl"
        self._scaler_path = MODELS_DIR / f"{self.ticker}_scaler.pkl"

    # ------------------------------------------------------------------
    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train with a walk-forward time-series split; persist the final model."""
        MODELS_DIR.mkdir(exist_ok=True)

        tscv = TimeSeriesSplit(n_splits=5)
        scores: list[float] = []

        for train_idx, val_idx in tscv.split(X):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

            scaler = StandardScaler()
            X_tr_scaled = scaler.fit_transform(X_tr)
            X_val_scaled = scaler.transform(X_val)

            clf = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=6,
                random_state=42,
                n_jobs=-1,
            )
            clf.fit(X_tr_scaled, y_tr)
            scores.append(accuracy_score(y_val, clf.predict(X_val_scaled)))

        # Final model trained on all data
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=6,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled, y)

        # Persist
        with open(self._model_path, "wb") as f:
            pickle.dump(self.model, f)
        with open(self._scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)

        return {
            "cv_accuracy_mean": float(np.mean(scores)),
            "cv_accuracy_std": float(np.std(scores)),
            "cv_scores": scores,
        }

    # ------------------------------------------------------------------
    def load(self) -> None:
        """Load a previously saved model and scaler from disk."""
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"No saved model for {self.ticker}. Run `train` first."
            )
        with open(self._model_path, "rb") as f:
            self.model = pickle.load(f)
        with open(self._scaler_path, "rb") as f:
            self.scaler = pickle.load(f)

    # ------------------------------------------------------------------
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return binary predictions (1 = up, 0 = down/flat) for each row in X."""
        if self.model is None:
            self.load()
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return class probabilities."""
        if self.model is None:
            self.load()
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)

    # ------------------------------------------------------------------
    @property
    def feature_importance(self) -> pd.Series | None:
        if self.model is None:
            return None
        return pd.Series(
            self.model.feature_importances_,
            name="importance",
        ).sort_values(ascending=False)
