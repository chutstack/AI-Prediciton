"""Best-of strategy model for easy niche tabular problems.

This module builds a lightweight ensemble by:
1) Training multiple simple-but-strong strategies.
2) Scoring each on a validation split.
3) Blending the top performers with normalized weights.

The goal is to solve "easy niche" problems quickly without heavy infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple
import math
import random


Row = Dict[str, float]
MIN_STRATEGY_WEIGHT = 1e-6
PHOTO_QUALITY_WEIGHT = 1.8
PRICE_SCORE_WEIGHT = -1.5
RESPONSE_DELAY_WEIGHT = -0.8


def train_validation_split(
    X: Sequence[Row], y: Sequence[int], validation_ratio: float = 0.25, seed: int = 42
) -> Tuple[List[Row], List[int], List[Row], List[int]]:
    idx = list(range(len(X)))
    rng = random.Random(seed)
    rng.shuffle(idx)

    cut = max(1, int(len(X) * (1.0 - validation_ratio)))
    train_idx, val_idx = idx[:cut], idx[cut:]

    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_val = [X[i] for i in val_idx]
    y_val = [y[i] for i in val_idx]
    return X_train, y_train, X_val, y_val


def accuracy_score(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    if not y_true:
        return 0.0
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    return correct / len(y_true)


class Strategy:
    name: str = "base"

    def fit(self, X: Sequence[Row], y: Sequence[int]) -> None:
        raise NotImplementedError

    def predict_proba(self, row: Row) -> float:
        raise NotImplementedError


class PriorStrategy(Strategy):
    """Strong baseline for heavily imbalanced niche tasks."""

    name = "prior"

    def __init__(self) -> None:
        self.p = 0.5

    def fit(self, X: Sequence[Row], y: Sequence[int]) -> None:
        self.p = (sum(y) + 1.0) / (len(y) + 2.0)

    def predict_proba(self, row: Row) -> float:
        return self.p


class SingleFeatureThresholdStrategy(Strategy):
    """Finds the best one-feature threshold stump."""

    name = "feature_threshold"

    def __init__(self) -> None:
        self.feature = ""
        self.threshold = 0.0
        self.left_p = 0.5
        self.right_p = 0.5

    def fit(self, X: Sequence[Row], y: Sequence[int]) -> None:
        features = sorted(X[0].keys()) if X else []
        best_acc = -1.0

        for f in features:
            values = sorted(set(row[f] for row in X))
            if len(values) < 2:
                continue
            candidates = [(a + b) / 2.0 for a, b in zip(values[:-1], values[1:])]
            for t in candidates:
                left = [yi for row, yi in zip(X, y) if row[f] <= t]
                right = [yi for row, yi in zip(X, y) if row[f] > t]
                if not left or not right:
                    continue

                left_p = (sum(left) + 1.0) / (len(left) + 2.0)
                right_p = (sum(right) + 1.0) / (len(right) + 2.0)

                preds = []
                for row in X:
                    p = left_p if row[f] <= t else right_p
                    preds.append(1 if p >= 0.5 else 0)
                acc = accuracy_score(y, preds)
                if acc > best_acc:
                    best_acc = acc
                    self.feature = f
                    self.threshold = t
                    self.left_p = left_p
                    self.right_p = right_p

        if best_acc < 0:  # fallback if no split was available
            self.feature = features[0] if features else ""
            self.threshold = 0.0
            p = (sum(y) + 1.0) / (len(y) + 2.0)
            self.left_p = p
            self.right_p = p

    def predict_proba(self, row: Row) -> float:
        if not self.feature:
            return 0.5
        return self.left_p if row[self.feature] <= self.threshold else self.right_p


class NearestCentroidStrategy(Strategy):
    """Computes class centroids and scores by distance."""

    name = "nearest_centroid"

    def __init__(self) -> None:
        self.features: List[str] = []
        self.c0: Dict[str, float] = {}
        self.c1: Dict[str, float] = {}

    def fit(self, X: Sequence[Row], y: Sequence[int]) -> None:
        self.features = sorted(X[0].keys()) if X else []
        X0 = [row for row, yi in zip(X, y) if yi == 0]
        X1 = [row for row, yi in zip(X, y) if yi == 1]

        def centroid(rows: Sequence[Row]) -> Dict[str, float]:
            if not rows:
                return {f: 0.0 for f in self.features}
            return {f: sum(r[f] for r in rows) / len(rows) for f in self.features}

        self.c0 = centroid(X0)
        self.c1 = centroid(X1)

    def predict_proba(self, row: Row) -> float:
        if not self.features:
            return 0.5

        d0 = math.sqrt(sum((row[f] - self.c0[f]) ** 2 for f in self.features))
        d1 = math.sqrt(sum((row[f] - self.c1[f]) ** 2 for f in self.features))

        # Convert distance into pseudo-probability
        if d0 + d1 == 0:
            return 0.5
        return d0 / (d0 + d1)


@dataclass
class StrategyResult:
    name: str
    score: float
    strategy: Strategy


class BestOfBlendModel:
    """Train many simple strategies, keep the best, and blend them."""

    def __init__(self, top_k: int = 2) -> None:
        self.top_k = top_k
        self.selected: List[StrategyResult] = []

    def fit(self, X: Sequence[Row], y: Sequence[int]) -> None:
        X_train, y_train, X_val, y_val = train_validation_split(X, y)

        candidates: List[Strategy] = [
            PriorStrategy(),
            SingleFeatureThresholdStrategy(),
            NearestCentroidStrategy(),
        ]

        scored: List[StrategyResult] = []
        for strategy in candidates:
            strategy.fit(X_train, y_train)
            preds = [1 if strategy.predict_proba(row) >= 0.5 else 0 for row in X_val]
            score = accuracy_score(y_val, preds)
            scored.append(StrategyResult(strategy.name, score, strategy))

        scored.sort(key=lambda s: s.score, reverse=True)
        self.selected = scored[: max(1, min(self.top_k, len(scored)))]

    def predict_proba(self, row: Row) -> float:
        if not self.selected:
            return 0.5
        total = sum(max(MIN_STRATEGY_WEIGHT, s.score) for s in self.selected)
        weighted_sum = sum(
            s.strategy.predict_proba(row) * max(MIN_STRATEGY_WEIGHT, s.score)
            for s in self.selected
        )
        return weighted_sum / total

    def predict(self, row: Row) -> int:
        return 1 if self.predict_proba(row) >= 0.5 else 0

    def summary(self) -> List[Tuple[str, float]]:
        return [(s.name, round(s.score, 4)) for s in self.selected]


def demo_dataset(n: int = 200, seed: int = 7) -> Tuple[List[Row], List[int]]:
    """Synthetic micro-niche dataset: local listing lead conversion."""
    rng = random.Random(seed)
    X: List[Row] = []
    y: List[int] = []

    for _ in range(n):
        price_score = rng.random()  # lower is better
        response_delay = rng.random()  # lower is better
        photo_quality = rng.random()  # higher is better

        # Easy niche pattern with slight noise
        raw = (
            PHOTO_QUALITY_WEIGHT * photo_quality
            + PRICE_SCORE_WEIGHT * price_score
            + RESPONSE_DELAY_WEIGHT * response_delay
        )
        raw += rng.uniform(-0.2, 0.2)
        target = 1 if raw > -0.2 else 0

        X.append(
            {
                "price_score": price_score,
                "response_delay": response_delay,
                "photo_quality": photo_quality,
            }
        )
        y.append(target)

    return X, y


if __name__ == "__main__":
    X, y = demo_dataset()

    model = BestOfBlendModel(top_k=2)
    model.fit(X, y)

    preds = [model.predict(row) for row in X]
    acc = accuracy_score(y, preds)

    print("Selected strategies:", model.summary())
    print("Training-set accuracy:", round(acc, 4))
