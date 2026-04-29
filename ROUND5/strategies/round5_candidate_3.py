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
        "PEBBLES_XL": ("z_revert", 500, 1.8, 3),
        "ROBOT_LAUNDRY": ("past_revert", 100, 1.9, 2),
        "PEBBLES_L": ("z_revert", 250, 1.6, 2),
        "OXYGEN_SHAKE_CHOCOLATE": ("past_revert", 50, 1.7, 1),
        "PANEL_1X4": ("past_momentum", 100, 2.1, 1),
    }

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        for product, (mode, window, threshold, max_size) in self.CONFIG.items():
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"])
            if len(hist) < 40:
                result[product] = []
                continue
            pos = state.position.get(product, 0)
            vol = self.vol(hist[-120:])
            signal = self.compute_signal(mode, hist, window, vol)
            if book["spread"] > 2.5 * vol + 8:
                signal *= 0.45
            result[product] = self.trade(product, book, pos, signal, threshold, max_size, vol)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def compute_signal(self, mode: str, hist: List[float], window: int, vol: float) -> float:
        lb = min(window, len(hist) - 1)
        if lb < 20:
            return 0.0
        if mode == "z_revert":
            sample = hist[-lb:]
            mean = sum(sample) / len(sample)
            return -(hist[-1] - mean) / max(vol, 1.0)
        move = (hist[-1] - hist[-1 - lb]) / max(vol, 1.0)
        if mode == "past_revert":
            return -move
        return move

    def trade(self, product: str, book: dict, pos: int, signal: float, threshold: float, max_size: int, vol: float) -> List[Order]:
        orders: List[Order] = []
        if abs(signal) < threshold:
            if pos > 6:
                return [Order(product, book["bid"], -1)]
            if pos < -6:
                return [Order(product, book["ask"], 1)]
            return []
        size = min(max_size, 1 + int(abs(signal) > threshold + 1.2))
        can_take = abs(signal) > threshold + 1.8 and book["spread"] <= max(12, 0.7 * vol)
        if signal > 0 and pos < self.LIMIT:
            price = book["ask"] if can_take else min(book["bid"] + 1, book["ask"] - 1)
            orders.append(Order(product, int(price), min(size, self.LIMIT - pos)))
        elif signal < 0 and pos > -self.LIMIT:
            price = book["bid"] if can_take else max(book["ask"] - 1, book["bid"] + 1)
            orders.append(Order(product, int(price), -min(size, self.LIMIT + pos)))
        return orders

    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid = max(d.buy_orders)
        ask = min(d.sell_orders)
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid}

    def push(self, cache: dict, product: str, mid: float) -> List[float]:
        key = "h_" + product
        hist = cache.get(key, [])
        if not isinstance(hist, list):
            hist = []
        hist.append(float(mid))
        cache[key] = hist[-620:]
        return cache[key]

    def vol(self, hist: List[float]) -> float:
        if len(hist) < 3:
            return 1.0
        diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
        mean = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - mean) ** 2 for x in diffs) / len(diffs)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
