from __future__ import annotations

import io
import os
from typing import Any

import pandas as pd
import requests

from trader.data.synthetic import generate_synthetic_ohlcv


def _to_coinbase_product(symbol: str) -> str:
    if "-" in symbol:
        return symbol
    if symbol.endswith("USD") and len(symbol) > 3:
        return f"{symbol[:-3]}-USD"
    return symbol


class CryptoAdapter:
    def fetch(self, symbol: str, limit: int = 1200) -> pd.DataFrame:
        product = _to_coinbase_product(symbol)
        url = f"https://api.exchange.coinbase.com/products/{product}/candles"
        params = {"granularity": 86400, "limit": min(300, limit)}
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            rows: list[list[Any]] = resp.json()
            if not rows:
                raise ValueError("empty payload")
            df = pd.DataFrame(rows, columns=["time", "low", "high", "open", "close", "volume"])
            df["time"] = pd.to_datetime(df["time"], unit="s", utc=True).tz_convert(None)
            df = df.set_index("time").sort_index()
            return df[["open", "high", "low", "close", "volume"]].astype(float).tail(limit)
        except Exception:
            return generate_synthetic_ohlcv(symbol, periods=limit)


class EquityAdapter:
    def fetch(self, symbol: str, limit: int = 1200) -> pd.DataFrame:
        key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_API_SECRET")
        if key and secret:
            try:
                url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
                params = {"timeframe": "1Day", "limit": limit}
                headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                resp.raise_for_status()
                bars = resp.json().get("bars", [])
                if bars:
                    df = pd.DataFrame(bars)
                    df["t"] = pd.to_datetime(df["t"], utc=True).dt.tz_convert(None)
                    df = df.set_index("t").rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
                    return df[["open", "high", "low", "close", "volume"]].astype(float).tail(limit)
            except Exception:
                pass

        try:
            stooq_url = f"https://stooq.com/q/d/l/?s={symbol.lower()}.us&i=d"
            resp = requests.get(stooq_url, timeout=10)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
            if {"Date", "Open", "High", "Low", "Close"}.issubset(df.columns):
                df = df.rename(
                    columns={
                        "Date": "time",
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Volume": "volume",
                    }
                )
                df["time"] = pd.to_datetime(df["time"])
                if "volume" not in df.columns:
                    df["volume"] = 0.0
                df = df.set_index("time").sort_index()
                return df[["open", "high", "low", "close", "volume"]].astype(float).tail(limit)
        except Exception:
            pass

        return generate_synthetic_ohlcv(symbol, periods=limit)
