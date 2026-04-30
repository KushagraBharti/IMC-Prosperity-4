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
    LIMIT = 10
    CONFIG = {
        "MICROCHIP_SQUARE": ("reversal", 100, 0.85),
        "MICROCHIP_TRIANGLE": ("reversal", 50, 0.90),
        "MICROCHIP_OVAL": ("momentum", 100, 1.00),
        "MICROCHIP_RECTANGLE": ("reversal", 100, 1.05),
    }

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        for product, (mode, lookback, threshold) in self.CONFIG.items():
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"], 220)
            if len(hist) <= lookback + 2:
                result[product] = []
                continue
            signal = (hist[-1] - hist[-1 - lookback]) / max(self.vol(hist[-120:]), 1.0)
            if mode == "reversal":
                signal = -signal
            result[product] = self.trade(product, book, state.position.get(product, 0), signal + 0.10 * book["imb"], threshold)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, book: dict, pos: int, signal: float, threshold: float) -> List[Order]:
        if abs(signal) < threshold:
            return []
        if signal > 0 and pos < self.LIMIT:
            price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
            return [Order(product, price, self.LIMIT - pos if signal > threshold + 0.9 else min(6, self.LIMIT - pos))]
        if signal < 0 and pos > -self.LIMIT:
            price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
            return [Order(product, price, -(self.LIMIT + pos if signal < -threshold - 0.9 else min(6, self.LIMIT + pos)))]
        return []

    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid, ask = max(d.buy_orders), min(d.sell_orders)
        bv, av = max(0, d.buy_orders[bid]), max(0, -d.sell_orders[ask])
        total = bv + av
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid, "imb": 0.0 if total == 0 else (bv - av) / total}

    def push(self, cache: dict, product: str, mid: float, keep: int) -> List[float]:
        hist = cache.get(product, [])
        if not isinstance(hist, list):
            hist = []
        hist.append(float(mid))
        cache[product] = hist[-keep:]
        return cache[product]

    def vol(self, hist: List[float]) -> float:
        if len(hist) < 3:
            return 1.0
        diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
        m = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - m) ** 2 for x in diffs) / len(diffs)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
