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
    PRODUCTS = [
        "ROBOT_LAUNDRY",
        "TRANSLATOR_GRAPHITE_MIST",
        "PEBBLES_L",
        "TRANSLATOR_ASTRO_BLACK",
        "ROBOT_IRONING",
        "SLEEP_POD_SUEDE",
        "MICROCHIP_OVAL",
        "UV_VISOR_ORANGE",
        "PEBBLES_XL",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "SNACKPACK_STRAWBERRY",
    ]

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        active_count = 0
        signals = []
        for product in self.PRODUCTS:
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"])
            vol = self.vol(hist[-80:])
            if len(hist) < 35:
                result[product] = []
                continue
            z = self.zscore(hist, 80, vol)
            past = (hist[-1] - hist[max(0, len(hist) - 61)]) / max(vol, 1.0)
            signal = self.direction(product, z, past, book)
            regime = self.regime_multiplier(book, vol, abs(z), abs(past))
            signal *= regime
            signals.append((product, book, state.position.get(product, 0), signal, vol))
        for product, book, pos, signal, vol in sorted(signals, key=lambda x: abs(x[3]), reverse=True):
            if active_count >= 7 and abs(pos) < 6:
                result[product] = []
                continue
            orders = self.trade(product, book, pos, signal, vol)
            if orders:
                active_count += 1
            result[product] = orders
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def direction(self, product: str, z: float, past: float, book: dict) -> float:
        if product in {"PEBBLES_L", "ROBOT_IRONING"}:
            base = 0.65 * past - 0.35 * z
        elif product in {"PEBBLES_XL", "OXYGEN_SHAKE_EVENING_BREATH", "SNACKPACK_STRAWBERRY", "TRANSLATOR_ASTRO_BLACK", "SLEEP_POD_SUEDE"}:
            base = -0.8 * z - 0.2 * past
        else:
            base = -0.7 * past - 0.3 * z
        return base + 0.25 * book["imb"]

    def regime_multiplier(self, book: dict, vol: float, abs_z: float, abs_past: float) -> float:
        spread = book["spread"]
        if spread > 3.5 * vol + 10:
            return 0.35
        if abs_z > 1.2 or abs_past > 1.5:
            return 1.0
        return 0.55

    def trade(self, product: str, book: dict, pos: int, signal: float, vol: float) -> List[Order]:
        threshold = 1.15 if product in {"ROBOT_LAUNDRY", "TRANSLATOR_GRAPHITE_MIST", "PEBBLES_L"} else 1.45
        if abs(signal) < threshold:
            if pos > 7:
                return [Order(product, book["bid"], -1)]
            if pos < -7:
                return [Order(product, book["ask"], 1)]
            return []
        size = 1 + int(abs(signal) > threshold + 1.0)
        take = abs(signal) > threshold + 1.6 and book["spread"] <= max(8, 0.75 * vol)
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

    def push(self, cache: dict, product: str, mid: float) -> List[float]:
        key = "h_" + product
        hist = cache.get(key, [])
        if not isinstance(hist, list):
            hist = []
        hist.append(float(mid))
        cache[key] = hist[-140:]
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
        return max(1.0, math.sqrt(sum((x - mean) ** 2 for x in diffs) / len(diffs)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
