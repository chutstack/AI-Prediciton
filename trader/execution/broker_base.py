from __future__ import annotations

from abc import ABC, abstractmethod


class BrokerBase(ABC):
    @abstractmethod
    def rebalance(self, symbol: str, target_weight: float, price: float) -> dict:
        raise NotImplementedError

    @abstractmethod
    def snapshot(self) -> dict:
        raise NotImplementedError
