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
    PRODUCTS = ["MICROCHIP_TRIANGLE", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_OVAL", "MICROCHIP_CIRCLE"]
    ACTIVE = ["MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"]
    X = {"MICROCHIP_TRIANGLE": 3.0, "MICROCHIP_SQUARE": 4.0, "MICROCHIP_RECTANGLE": 4.6, "MICROCHIP_OVAL": 5.5, "MICROCHIP_CIRCLE": 6.0}

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        books = {p: self.book(state, p) for p in self.PRODUCTS}
        if any(books[p] is None for p in self.PRODUCTS):
            return result, 0, json.dumps(cache, separators=(",", ":"))
        mids = {p: books[p]["mid"] for p in self.PRODUCTS}
        fairs = {p: self.fit_predict([self.X[q] for q in self.PRODUCTS if q != p], [mids[q] for q in self.PRODUCTS if q != p], self.X[p]) for p in self.PRODUCTS}
        for product in self.ACTIVE:
            hist = self.push(cache, "m_" + product, mids[product], 90)
            residual = mids[product] - fairs[product]
            rvol = self.std(self.push(cache, "r_" + product, residual, 180), 120.0)
            signal = -residual
            if len(hist) >= 26:
                signal += -0.35 * (hist[-1] - hist[-26])
            result[product] = self.trade(product, books[product], signal, state.position.get(product, 0), rvol)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, book: dict, signal: float, pos: int, rvol: float) -> List[Order]:
        threshold = max(45.0, min(160.0, 0.42 * rvol))
        orders: List[Order] = []
        if signal > threshold and pos < self.LIMIT:
            price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 4 else book["bid"]
            orders.append(Order(product, price, self.LIMIT - pos if signal > threshold * 2 else min(6, self.LIMIT - pos)))
        elif signal < -threshold and pos > -self.LIMIT:
            price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 4 else book["ask"]
            orders.append(Order(product, price, -(self.LIMIT + pos if signal < -threshold * 2 else min(6, self.LIMIT + pos))))
        return orders

    def fit_predict(self, xs: List[float], ys: List[float], x0: float) -> float:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        den = sum((x - mx) ** 2 for x in xs)
        slope = 0.0 if den <= 1e-9 else sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs))) / den
        return my + slope * (x0 - mx)

    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid, ask = max(d.buy_orders), min(d.sell_orders)
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid}

    def push(self, cache: dict, key: str, value: float, keep: int = 180) -> List[float]:
        hist = cache.get(key, [])
        if not isinstance(hist, list):
            hist = []
        hist.append(float(value))
        cache[key] = hist[-keep:]
        return cache[key]

    def std(self, values: List[float], default: float) -> float:
        if len(values) < 3:
            return default
        m = sum(values) / len(values)
        return max(default, math.sqrt(sum((x - m) ** 2 for x in values) / len(values)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
