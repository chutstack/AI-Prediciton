from __future__ import annotations

import numpy as np
import pandas as pd

from trader.features.cross_asset import add_cross_features
from trader.features.indicators import atr14, rolling_slope


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    lr = np.log(out["close"]).diff()
    out["r1"] = lr
    for n in [3, 5, 10, 20]:
        out[f"r{n}"] = np.log(out["close"]).diff(n)
    out["sma20_dist"] = out["close"] / out["close"].rolling(20).mean() - 1
    out["sma50_dist"] = out["close"] / out["close"].rolling(50).mean() - 1
    out["slope20"] = rolling_slope(out["close"], 20)
    out["slope50"] = rolling_slope(out["close"], 50)
    out["vol5"] = lr.rolling(5).std()
    out["vol10"] = lr.rolling(10).std()
    out["vol20"] = lr.rolling(20).std()
    out["vol60"] = lr.rolling(60).std()
    out["vol_ratio"] = out["vol5"] / out["vol20"].replace(0, np.nan)
    out["atr14"] = atr14(out)
    out["atr_pct"] = out["atr14"] / out["close"]
    out["hl_pct"] = (out["high"] - out["low"]) / out["close"]
    out["upper_wick"] = (out["high"] - out[["open", "close"]].max(axis=1)) / out["close"]
    out["lower_wick"] = (out[["open", "close"]].min(axis=1) - out["low"]) / out["close"]
    out["vol_z20"] = (out["volume"] - out["volume"].rolling(20).mean()) / out["volume"].rolling(20).std()
    dollar_vol = out["volume"] * out["close"]
    out["dollar_vol_z20"] = (dollar_vol - dollar_vol.rolling(20).mean()) / dollar_vol.rolling(20).std()
    out["z_close_20"] = (out["close"] - out["close"].rolling(20).mean()) / out["close"].rolling(20).std()
    out["z_return_20"] = (lr - lr.rolling(20).mean()) / lr.rolling(20).std()
    out["distance_from_high_20"] = out["close"] / out["high"].rolling(20).max() - 1
    out["distance_from_low_20"] = out["close"] / out["low"].rolling(20).min() - 1
    return out


def make_dataset(asset: str, prices: dict[str, pd.DataFrame], threshold: float, include_crypto_for_spy: bool = False) -> tuple[pd.DataFrame, pd.Series]:
    feats = compute_features(prices[asset])
    feats = add_cross_features(feats, asset, prices, include_crypto_for_spy=include_crypto_for_spy)
    fut_ret = prices[asset]["close"].shift(-1) / prices[asset]["close"] - 1
    y = (fut_ret > threshold).astype(int)
    aligned = feats.join(y.rename("y"), how="inner").dropna()
    return aligned.drop(columns=["y"]), aligned["y"]
