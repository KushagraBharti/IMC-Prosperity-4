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
    PRODUCT = "PEBBLES_XL"

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        book = self.book(state, self.PRODUCT)
        if book:
            hist = self.push(cache, self.PRODUCT, book["mid"])
            if len(hist) >= 45:
                vol = self.vol(hist[-120:])
                z = self.zscore(hist, 420, vol)
                past = (hist[-1] - hist[max(0, len(hist) - 81)]) / max(vol, 1.0)
                signal = -z - 0.10 * past + 0.20 * book["imb"]
                result[self.PRODUCT] = self.trade(book, state.position.get(self.PRODUCT, 0), signal, 1.05)
            else:
                result[self.PRODUCT] = []
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, book: dict, pos: int, signal: float, threshold: float) -> List[Order]:
        if abs(signal) < threshold:
            if pos > 6:
                return [Order(self.PRODUCT, book["bid"], -min(5, pos))]
            if pos < -6:
                return [Order(self.PRODUCT, book["ask"], min(5, -pos))]
            return []
        size = 5 if abs(signal) < threshold + 0.7 else 10
        take = abs(signal) > threshold + 0.45 and book["spread"] <= 18
        if signal > 0 and pos < self.LIMIT:
            return [Order(self.PRODUCT, book["ask"] if take else min(book["bid"] + 1, book["ask"] - 1), min(size, self.LIMIT - pos))]
        if signal < 0 and pos > -self.LIMIT:
            return [Order(self.PRODUCT, book["bid"] if take else max(book["ask"] - 1, book["bid"] + 1), -min(size, self.LIMIT + pos))]
        return []

    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid = max(d.buy_orders)
        ask = min(d.sell_orders)
        bid_vol = max(0, d.buy_orders[bid])
        ask_vol = max(0, -d.sell_orders[ask])
        total = bid_vol + ask_vol
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid, "imb": 0.0 if total == 0 else (bid_vol - ask_vol) / total}

    def push(self, cache: dict, product: str, mid: float) -> List[float]:
        key = "h_" + product
        hist = cache.get(key, [])
        if not isinstance(hist, list):
            hist = []
        hist.append(float(mid))
        cache[key] = hist[-520:]
        return cache[key]

    def zscore(self, hist: List[float], window: int, vol: float) -> float:
        sample = hist[-min(window, len(hist)) :]
        mean = sum(sample) / len(sample)
        return (hist[-1] - mean) / max(vol, 1.0)

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
