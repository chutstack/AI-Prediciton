import pandas as pd

from trader.model.splitter import WalkForwardSplitter


def test_walkforward_splitter_embargo() -> None:
    idx = pd.date_range("2020-01-01", periods=1000, freq="B")
    splitter = WalkForwardSplitter(train_days=200, test_days=50, step_days=50, embargo_days=1)
    splits = splitter.split(idx)
    assert len(splits) > 0
    tr, te = splits[0]
    assert te.min() > tr.max()
    assert (te.min() - tr.max()).days >= 2
