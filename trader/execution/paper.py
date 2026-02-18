from __future__ import annotations

from trader.data.storage import JsonStateStore
from trader.execution.broker_base import BrokerBase


class PaperBroker(BrokerBase):
    def __init__(self, state_path: str = "logs/paper_state.json", fee_bps: float = 1.0, slippage_bps: float = 2.0) -> None:
        self.store = JsonStateStore(state_path)
        self.state = self.store.load()
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps

    def equity(self, prices: dict[str, float] | None = None) -> float:
        prices = prices or {}
        pos_val = sum(q * prices.get(sym, 0.0) for sym, q in self.state["positions"].items())
        return float(self.state["cash"] + pos_val)

    def rebalance(self, symbol: str, target_weight: float, price: float) -> dict:
        eq = self.equity({symbol: price})
        target_notional = eq * target_weight
        current_qty = float(self.state["positions"].get(symbol, 0.0))
        current_notional = current_qty * price
        delta_notional = target_notional - current_notional
        fill_price = price * (1 + self.slippage_bps / 10000)
        qty = delta_notional / fill_price
        fee = abs(delta_notional) * self.fee_bps / 10000
        self.state["cash"] -= qty * fill_price + fee
        self.state["positions"][symbol] = current_qty + qty
        self.store.save(self.state)
        return {"symbol": symbol, "qty": qty, "fill_price": fill_price, "fee": fee}

    def snapshot(self) -> dict:
        return self.state
