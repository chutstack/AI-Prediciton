"""Market data fetching and caching."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"


def fetch_ohlcv(ticker: str, days: int = 365, use_cache: bool = True) -> pd.DataFrame:
    """Return OHLCV DataFrame for *ticker* covering the last *days* calendar days.

    Data is cached as a CSV under ``.cache/<ticker>.csv`` and refreshed when the
    most-recent row is older than today.
    """
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{ticker.upper()}.csv"

    if use_cache and cache_file.exists():
        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        if not df.empty:
            return df

    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("yfinance is required: pip install yfinance") from exc

    end = pd.Timestamp.today()
    start = end - pd.Timedelta(days=days)
    df = yf.download(ticker, start=start.date(), end=end.date(), progress=False)

    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'")

    # Flatten multi-level columns produced by yfinance ≥ 0.2
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "Date"
    df.to_csv(cache_file)
    return df
