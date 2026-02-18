from __future__ import annotations

import os

from trader.execution.broker_base import BrokerBase


class LiveBrokerPlaceholder(BrokerBase):
    def __init__(self) -> None:
        if os.getenv("ENABLE_LIVE_TRADING", "false").lower() != "true":
            raise RuntimeError("Live trading disabled. Set ENABLE_LIVE_TRADING=true explicitly.")

    def rebalance(self, symbol: str, target_weight: float, price: float) -> dict:
        raise NotImplementedError("Integrate real broker APIs before live use.")

    def snapshot(self) -> dict:
        return {}
