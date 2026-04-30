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
    CONFIG = {'SLEEP_POD_LAMB_WOOL': ('breakout_low_reversal', 200, 0.95, 1.0)}
    MAX_ACTIVE = 10

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        scored = []
        for product, cfg in self.CONFIG.items():
            mode, lookback, threshold, weight = cfg[:4]
            style = cfg[4] if len(cfg) > 4 else "passive"
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"], max(620, lookback + 180))
            if len(hist) <= lookback + 3:
                continue
            signal = self.signal(mode, hist, lookback)
            signal += 0.08 * book["imb"]
            score = abs(signal) / max(threshold, 0.01) * weight
            if abs(signal) >= threshold:
                scored.append((score, product, book, signal, threshold, weight, style))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _, product, book, signal, threshold, weight, style in scored[: self.MAX_ACTIVE]:
            result[product] = self.trade(product, book, state.position.get(product, 0), signal, threshold, weight, style)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def signal(self, mode: str, hist: List[float], lookback: int) -> float:
        vol = max(self.vol(hist[-160:]), 1.0)
        move = hist[-1] - hist[-1 - lookback]
        if mode == "momentum":
            return move / vol
        if mode == "reversal":
            return -move / vol
        if mode == "vol_norm_momentum":
            return move / vol
        if mode == "vol_norm_reversal":
            return -move / vol
        window = hist[-lookback:]
        mean = sum(window) / len(window)
        hi = max(window[:-1]) if len(window) > 1 else hist[-1]
        lo = min(window[:-1]) if len(window) > 1 else hist[-1]
        if mode == "rolling_mean_reversion":
            return -(hist[-1] - mean) / vol
        if mode == "breakout_high":
            return (hist[-1] - hi) / vol
        if mode == "breakout_low_reversal":
            return (lo - hist[-1]) / vol
        return move / vol

    def trade(self, product: str, book: dict, pos: int, signal: float, threshold: float, weight: float, style: str) -> List[Order]:
        strong = abs(signal) > threshold + 0.85
        base_qty = 10 if strong or weight >= 1.2 else 6
        if signal > 0 and pos < self.LIMIT:
            if style == "hybrid" and abs(signal) > threshold + 0.55:
                price = book["ask"]
            else:
                price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
            return [Order(product, price, min(base_qty, self.LIMIT - pos))]
        if signal < 0 and pos > -self.LIMIT:
            if style == "hybrid" and abs(signal) > threshold + 0.55:
                price = book["bid"]
            else:
                price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
            return [Order(product, price, -min(base_qty, self.LIMIT + pos))]
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
