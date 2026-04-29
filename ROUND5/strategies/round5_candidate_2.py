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
        "ROBOT_LAUNDRY": ("past_revert", 100, 2.0),
        "TRANSLATOR_GRAPHITE_MIST": ("past_revert", 100, 2.0),
        "PEBBLES_L": ("past_momentum", 100, 1.8),
        "TRANSLATOR_ASTRO_BLACK": ("z_revert", 250, 1.35),
        "ROBOT_IRONING": ("past_momentum", 100, 1.7),
        "SLEEP_POD_SUEDE": ("z_revert", 100, 1.25),
        "MICROCHIP_OVAL": ("past_revert", 50, 1.8),
        "UV_VISOR_ORANGE": ("past_revert", 50, 1.8),
    }

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        for product, (mode, lookback, threshold) in self.CONFIG.items():
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"])
            if len(hist) < min(20, lookback // 2):
                result[product] = []
                continue
            pos = state.position.get(product, 0)
            vol = self.realized_vol(hist[-80:])
            signal = self.signal(mode, hist, lookback, vol)
            if book["spread"] > max(26, 3.0 * vol):
                signal *= 0.55
            result[product] = self.execute(product, book, pos, signal, threshold, vol)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def signal(self, mode: str, hist: List[float], lookback: int, vol: float) -> float:
        lb = min(lookback, len(hist) - 1)
        if lb <= 2 or vol <= 0:
            return 0.0
        move = (hist[-1] - hist[-1 - lb]) / vol
        if mode == "past_revert":
            return -move
        if mode == "past_momentum":
            return move
        mean = sum(hist[-lb:]) / lb
        z = (hist[-1] - mean) / max(vol, 1.0)
        return -z

    def execute(self, product: str, book: dict, pos: int, signal: float, threshold: float, vol: float) -> List[Order]:
        if abs(signal) < threshold:
            return self.inventory_relief(product, book, pos)
        size = 1 if abs(signal) < threshold + 0.8 else 2
        orders: List[Order] = []
        take = abs(signal) > threshold + 1.5 and book["spread"] <= max(10, 0.8 * vol)
        if signal > 0 and pos < self.LIMIT:
            price = book["ask"] if take else min(book["bid"] + 1, book["ask"] - 1)
            orders.append(Order(product, int(price), min(size, self.LIMIT - pos)))
        elif signal < 0 and pos > -self.LIMIT:
            price = book["bid"] if take else max(book["ask"] - 1, book["bid"] + 1)
            orders.append(Order(product, int(price), -min(size, self.LIMIT + pos)))
        if abs(pos) >= 8:
            orders.extend(self.inventory_relief(product, book, pos))
        return self.clamp(product, pos, orders)

    def inventory_relief(self, product: str, book: dict, pos: int) -> List[Order]:
        if pos > 7:
            return [Order(product, book["bid"], -1)]
        if pos < -7:
            return [Order(product, book["ask"], 1)]
        return []

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
        cache[key] = hist[-160:]
        return cache[key]

    def realized_vol(self, hist: List[float]) -> float:
        if len(hist) < 3:
            return 1.0
        diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
        mean = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - mean) * (x - mean) for x in diffs) / len(diffs)))

    def clamp(self, product: str, pos: int, orders: List[Order]) -> List[Order]:
        buy = self.LIMIT - pos
        sell = self.LIMIT + pos
        out: List[Order] = []
        for order in orders:
            q = int(order.quantity)
            if q > 0:
                q = min(q, buy)
                buy -= q
            else:
                q = -min(-q, sell)
                sell += q
            if q:
                out.append(Order(product, order.price, q))
        return out

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
