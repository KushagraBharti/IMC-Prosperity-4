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
        "PEBBLES_XL": (420, 1.05, 1.00),
        "PEBBLES_L": (220, 1.80, 0.55),
    }

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        for product, (window, threshold, weight) in self.CONFIG.items():
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"], max(520, window + 40))
            if len(hist) < 50:
                result[product] = []
                continue
            vol = self.vol(hist[-120:])
            z = self.zscore(hist, window, vol)
            past = (hist[-1] - hist[max(0, len(hist) - 81)]) / max(vol, 1.0)
            signal = weight * (-z - 0.10 * past + 0.18 * book["imb"])
            result[product] = self.trade(product, book, state.position.get(product, 0), signal, threshold)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, book: dict, pos: int, signal: float, threshold: float) -> List[Order]:
        if abs(signal) < threshold:
            if pos > 6:
                return [Order(product, book["bid"], -min(4, pos))]
            if pos < -6:
                return [Order(product, book["ask"], min(4, -pos))]
            return []
        size = 4 if abs(signal) < threshold + 0.6 else 9
        take = abs(signal) > threshold + 0.40 and book["spread"] <= 18
        if signal > 0 and pos < self.LIMIT:
            return [Order(product, book["ask"] if take else min(book["bid"] + 1, book["ask"] - 1), min(size, self.LIMIT - pos))]
        if signal < 0 and pos > -self.LIMIT:
            return [Order(product, book["bid"] if take else max(book["ask"] - 1, book["bid"] + 1), -min(size, self.LIMIT + pos))]
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

    def push(self, cache: dict, product: str, mid: float, keep: int) -> List[float]:
        key = "h_" + product
        hist = cache.get(key, [])
        if not isinstance(hist, list):
            hist = []
        hist.append(float(mid))
        cache[key] = hist[-keep:]
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
