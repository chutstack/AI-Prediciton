from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class WalkForwardSplitter:
    train_days: int = 756
    test_days: int = 63
    step_days: int = 63
    embargo_days: int = 1

    def split(self, index: pd.Index) -> list[tuple[pd.Index, pd.Index]]:
        dates = pd.Index(index).sort_values()
        out: list[tuple[pd.Index, pd.Index]] = []
        start = 0
        while True:
            train_end = start + self.train_days - 1
            test_start = train_end + self.embargo_days + 1
            test_end = test_start + self.test_days - 1
            if test_end >= len(dates):
                break
            tr_idx = dates[start : train_end + 1]
            te_idx = dates[test_start : test_end + 1]
            out.append((tr_idx, te_idx))
            start += self.step_days
        return out
