from __future__ import annotations

import numpy as np
import pandas as pd


def add_cross_features(base: pd.DataFrame, asset: str, prices: dict[str, pd.DataFrame], include_spy_for_crypto: bool = True, include_crypto_for_spy: bool = False) -> pd.DataFrame:
    out = base.copy()
    if asset in {"BTC-USD", "ETH-USD"}:
        other = "ETH-USD" if asset == "BTC-USD" else "BTC-USD"
        other_r = np.log(prices[other]["close"]).diff()
        out[f"{other}_r1"] = other_r
        out[f"{other}_r5"] = np.log(prices[other]["close"]).diff(5)
        out[f"{other}_vol10"] = other_r.rolling(10).std()
        self_r = np.log(prices[asset]["close"]).diff()
        out["corr_20_crypto"] = self_r.rolling(20).corr(other_r)
        spread = np.log(prices["BTC-USD"]["close"]) - np.log(prices["ETH-USD"]["close"])
        out["z_spread_60"] = (spread - spread.rolling(60).mean()) / spread.rolling(60).std()
        if include_spy_for_crypto and "SPY" in prices:
            spy_r = np.log(prices["SPY"]["close"]).diff()
            out["SPY_r1"] = spy_r
            out["SPY_r5"] = np.log(prices["SPY"]["close"]).diff(5)
            out["corr_60_spy"] = self_r.rolling(60).corr(spy_r)
    elif asset == "SPY" and include_crypto_for_spy and "BTC-USD" in prices:
        btc_r = np.log(prices["BTC-USD"]["close"]).diff()
        out["BTC_r1"] = btc_r
    return out
