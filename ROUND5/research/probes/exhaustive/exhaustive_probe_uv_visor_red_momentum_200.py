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
    CONFIG = {'UV_VISOR_RED': ('momentum', 200, 1.05)}

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        scored = []
        for product, (mode, lookback, threshold) in self.CONFIG.items():
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"], max(620, lookback + 160))
            if len(hist) <= lookback + 2:
                continue
            signal = (hist[-1] - hist[-1 - lookback]) / max(self.vol(hist[-160:]), 1.0)
            if mode == "reversal":
                signal = -signal
            signal += 0.08 * book["imb"]
            if abs(signal) >= threshold:
                scored.append((abs(signal) / threshold, product, book, signal, threshold))
        scored.sort(reverse=True, key=lambda x: x[0])
        for _, product, book, signal, threshold in scored[:10]:
            result[product] = self.trade(product, book, state.position.get(product, 0), signal, threshold)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, book: dict, pos: int, signal: float, threshold: float) -> List[Order]:
        if signal > 0 and pos < self.LIMIT:
            price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
            qty = self.LIMIT - pos if signal > threshold + 1.0 else min(6, self.LIMIT - pos)
            return [Order(product, price, qty)]
        if signal < 0 and pos > -self.LIMIT:
            price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
            qty = self.LIMIT + pos if signal < -threshold - 1.0 else min(6, self.LIMIT + pos)
            return [Order(product, price, -qty)]
        return []

    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid, ask = max(d.buy_orders), min(d.sell_orders)
        bv, av = max(0, d.buy_orders[bid]), max(0, -d.sell_orders[ask])
        total = bv + av
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid, "imb": 0.0 if total == 0 else (bv - av) / total}

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
        m = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - m) ** 2 for x in diffs) / len(diffs)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
