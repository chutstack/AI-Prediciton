"""Simple signal-based back-testing engine."""
from __future__ import annotations

import pandas as pd
import numpy as np


class BacktestEngine:
    """Back-test an ML signal against OHLCV data.

    Strategy: go long (buy) the next day when signal == 1,
    stay in cash when signal == 0.  No short-selling.
    """

    def __init__(self, initial_capital: float = 10_000.0):
        self.initial_capital = initial_capital
        self.results: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    def run(
        self,
        df: pd.DataFrame,
        signals: np.ndarray,
    ) -> "BacktestEngine":
        """
        Parameters
        ----------
        df      : OHLCV DataFrame aligned with *signals*.
        signals : 1-D array of 0/1 trade signals (1 = be long tomorrow).
        """
        prices = df["Close"].values
        n = len(signals)
        assert len(prices) == n, "signals and prices must have the same length"

        cash = self.initial_capital
        shares = 0.0
        portfolio = []

        for i in range(n - 1):
            sig = signals[i]
            next_open = df["Open"].iloc[i + 1]

            if sig == 1 and cash > 0:
                shares = cash / next_open
                cash = 0.0
            elif sig == 0 and shares > 0:
                cash = shares * next_open
                shares = 0.0

            portfolio_value = cash + shares * prices[i + 1]
            portfolio.append(portfolio_value)

        self.results = pd.DataFrame(
            {"portfolio": portfolio, "close": prices[1:]},
            index=df.index[1:],
        )
        self.results["buy_hold"] = (
            self.initial_capital * prices[1:] / prices[0]
        )
        return self

    # ------------------------------------------------------------------
    def summary(self) -> dict:
        """Return a dict of key performance metrics."""
        if self.results is None:
            raise RuntimeError("Call run() first.")

        r = self.results
        final = r["portfolio"].iloc[-1]
        bh_final = r["buy_hold"].iloc[-1]

        port_returns = r["portfolio"].pct_change().dropna()
        trading_days = len(port_returns)

        sharpe = (
            port_returns.mean() / port_returns.std() * np.sqrt(252)
            if port_returns.std() > 0
            else 0.0
        )

        rolling_max = r["portfolio"].cummax()
        drawdown = (r["portfolio"] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        return {
            "initial_capital": self.initial_capital,
            "final_value": round(final, 2),
            "total_return_pct": round((final / self.initial_capital - 1) * 100, 2),
            "buy_hold_return_pct": round((bh_final / self.initial_capital - 1) * 100, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "trading_days": trading_days,
        }
