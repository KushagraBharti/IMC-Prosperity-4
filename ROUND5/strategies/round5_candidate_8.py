from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List

try:
    from datamodel import Order, TradingState
except ImportError:
    @dataclass
    class Order:
        symbol: str
        price: int
        quantity: int

    @dataclass
    class TradingState:
        order_depths: Dict[str, object]
        position: Dict[str, int] = field(default_factory=dict)
        traderData: str = ""


class Trader:
    LIMIT = 10
    PRODUCTS = {"ROBOT_DISHES": 0.46, "ROBOT_IRONING": 0.40}

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        for product, threshold in self.PRODUCTS.items():
            book = self.book(state, product)
            if not book:
                continue
            stat = self.update_stat(cache, product, book["mid"], 0.04)
            trend = book["mid"] - stat["mean"]
            signal = book["imb"] + 0.35 * book["micro"] + 0.02 * trend
            result[product] = self.trade(product, book, state.position.get(product, 0), signal, threshold)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, book: dict, pos: int, signal: float, threshold: float) -> List[Order]:
        orders: List[Order] = []
        if abs(signal) < threshold:
            if pos > 8:
                orders.append(Order(product, book["bid"], -min(3, pos)))
            elif pos < -8:
                orders.append(Order(product, book["ask"], min(3, -pos)))
            return orders
        size = 3 if abs(signal) < threshold + 0.35 else 5
        if signal > 0 and pos < self.LIMIT:
            price = book["ask"] if book["spread"] <= 8 and signal > threshold + 0.55 else min(book["bid"] + 1, book["ask"] - 1)
            orders.append(Order(product, int(price), min(size, self.LIMIT - pos)))
        elif signal < 0 and pos > -self.LIMIT:
            price = book["bid"] if book["spread"] <= 8 and -signal > threshold + 0.55 else max(book["ask"] - 1, book["bid"] + 1)
            orders.append(Order(product, int(price), -min(size, self.LIMIT + pos)))
        return orders

    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid = max(d.buy_orders)
        ask = min(d.sell_orders)
        bid_vol = max(0, d.buy_orders[bid])
        ask_vol = max(0, -d.sell_orders[ask])
        total = bid_vol + ask_vol
        imb = 0.0 if total == 0 else (bid_vol - ask_vol) / total
        micro = 0.0 if total == 0 else ((ask * bid_vol + bid * ask_vol) / total - (bid + ask) / 2.0) / max(1.0, ask - bid)
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid, "imb": imb, "micro": micro}

    def update_stat(self, cache: dict, key: str, value: float, alpha: float) -> dict:
        stat = cache.setdefault(key, {"mean": value})
        stat["mean"] = (1.0 - alpha) * float(stat["mean"]) + alpha * value
        return stat

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
