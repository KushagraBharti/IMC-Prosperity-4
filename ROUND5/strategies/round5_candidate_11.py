from __future__ import annotations

import json
import math
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
    PRODUCT = "ROBOT_DISHES"
    LIMIT = 10

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        book = self.book(state, self.PRODUCT)
        if not book:
            return result, 0, json.dumps(cache, separators=(",", ":"))

        hist = self.push(cache, "mid", book["mid"], 140)
        result[self.PRODUCT] = []
        if len(hist) >= 12:
            vol = self.vol(hist[-80:])
            move10 = hist[-1] - hist[-11]
            move3 = hist[-1] - hist[-4] if len(hist) >= 4 else 0.0
            signal = -move10 / max(vol, 1.0)
            if move10 * move3 < 0:
                signal *= 0.65
            signal += 0.22 * book["imb"]
            result[self.PRODUCT] = self.trade(book, state.position.get(self.PRODUCT, 0), signal, vol)

        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, book: dict, pos: int, signal: float, vol: float) -> List[Order]:
        orders: List[Order] = []
        threshold = 1.20
        hard_threshold = 1.95
        if signal > threshold and pos < self.LIMIT:
            qty = self.LIMIT - pos if signal > hard_threshold else min(7, self.LIMIT - pos)
            price = self.passive_buy(book)
            if qty > 0:
                orders.append(Order(self.PRODUCT, price, qty))
        elif signal < -threshold and pos > -self.LIMIT:
            qty = self.LIMIT + pos if signal < -hard_threshold else min(7, self.LIMIT + pos)
            price = self.passive_sell(book)
            if qty > 0:
                orders.append(Order(self.PRODUCT, price, -qty))
        else:
            if pos > 5 and signal <= 0.15:
                orders.append(Order(self.PRODUCT, self.passive_sell(book), -min(pos, 6)))
            elif pos < -5 and signal >= -0.15:
                orders.append(Order(self.PRODUCT, self.passive_buy(book), min(-pos, 6)))
        return orders

    def passive_buy(self, book: dict) -> int:
        if book["spread"] >= 3:
            return min(book["bid"] + 1, book["ask"] - 1)
        return book["bid"]

    def passive_sell(self, book: dict) -> int:
        if book["spread"] >= 3:
            return max(book["ask"] - 1, book["bid"] + 1)
        return book["ask"]

    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid = max(d.buy_orders)
        ask = min(d.sell_orders)
        bid_vol = max(0, d.buy_orders[bid])
        ask_vol = max(0, -d.sell_orders[ask])
        total = bid_vol + ask_vol
        return {
            "bid": bid,
            "ask": ask,
            "mid": (bid + ask) / 2.0,
            "spread": ask - bid,
            "imb": 0.0 if total == 0 else (bid_vol - ask_vol) / total,
        }

    def push(self, cache: dict, key: str, value: float, keep: int) -> List[float]:
        hist = cache.get(key, [])
        if not isinstance(hist, list):
            hist = []
        hist.append(float(value))
        cache[key] = hist[-keep:]
        return cache[key]

    def vol(self, hist: List[float]) -> float:
        if len(hist) < 3:
            return 1.0
        diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
        mean = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - mean) * (x - mean) for x in diffs) / len(diffs)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
