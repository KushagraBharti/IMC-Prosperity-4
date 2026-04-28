from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


try:
    from datamodel import Order, OrderDepth, TradingState
except ImportError:
    @dataclass
    class Order:
        symbol: str
        price: int
        quantity: int

    @dataclass
    class OrderDepth:
        buy_orders: Dict[int, int] = field(default_factory=dict)
        sell_orders: Dict[int, int] = field(default_factory=dict)

    @dataclass
    class TradingState:
        order_depths: Dict[str, OrderDepth]
        position: Dict[str, int] = field(default_factory=dict)
        traderData: str = ""


class Trader:
    """Round 4 scratch trader for analysis and experiment work."""

    def run(self, state: TradingState):
        orders: Dict[str, List[Order]] = {}
        for product in state.order_depths:
            orders[product] = []
        return orders, 0, ""
