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
    PEBBLES = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]
    PEB_X = {"PEBBLES_XS": 1.0, "PEBBLES_S": 2.0, "PEBBLES_M": 3.0, "PEBBLES_L": 4.0, "PEBBLES_XL": 5.0}
    MICRO = ["MICROCHIP_TRIANGLE", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_OVAL", "MICROCHIP_CIRCLE"]
    MICRO_X = {"MICROCHIP_TRIANGLE": 3.0, "MICROCHIP_SQUARE": 4.0, "MICROCHIP_RECTANGLE": 4.6, "MICROCHIP_OVAL": 5.5, "MICROCHIP_CIRCLE": 6.0}
    UV = ["UV_VISOR_RED", "UV_VISOR_ORANGE", "UV_VISOR_AMBER", "UV_VISOR_YELLOW", "UV_VISOR_MAGENTA"]
    UV_X = {"UV_VISOR_RED": 1.0, "UV_VISOR_ORANGE": 2.0, "UV_VISOR_AMBER": 2.5, "UV_VISOR_YELLOW": 3.0, "UV_VISOR_MAGENTA": 5.0}

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        self.pebbles(state, cache, result)
        self.add_single_group(state, cache, result, self.MICRO, self.MICRO_X, ["MICROCHIP_SQUARE"], 85.0, "micro")
        self.add_single_group(state, cache, result, self.UV, self.UV_X, ["UV_VISOR_AMBER"], 55.0, "uv")
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def pebbles(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        books = {p: self.book(state, p) for p in self.PEBBLES}
        if any(books[p] is None for p in self.PEBBLES):
            return
        mids = {p: books[p]["mid"] for p in self.PEBBLES}
        for product in self.PEBBLES:
            fair = self.fit_predict([self.PEB_X[q] for q in self.PEBBLES if q != product], [mids[q] for q in self.PEBBLES if q != product], self.PEB_X[product])
            residual = mids[product] - fair
            rvol = self.std(self.push(cache, "p" + product, residual, 120), 4.0)
            result[product] = self.trade(product, books[product], fair, state.position.get(product, 0), max(1.5, min(8.0, 0.35 * rvol)), allow_cross=True)

    def add_single_group(self, state: TradingState, cache: dict, result: Dict[str, List[Order]], products: List[str], xmap: Dict[str, float], active: List[str], base_threshold: float, key: str) -> None:
        books = {p: self.book(state, p) for p in products}
        if any(books[p] is None for p in products):
            return
        mids = {p: books[p]["mid"] for p in products}
        for product in active:
            fair = self.fit_predict([xmap[q] for q in products if q != product], [mids[q] for q in products if q != product], xmap[product])
            residual = mids[product] - fair
            rvol = self.std(self.push(cache, key + product, residual, 120), base_threshold)
            result[product] = self.trade(product, books[product], fair, state.position.get(product, 0), max(base_threshold, 0.35 * rvol), allow_cross=False)

    def trade(self, product: str, book: dict, fair: float, pos: int, threshold: float, allow_cross: bool) -> List[Order]:
        fair -= 0.85 * pos
        buy_price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
        sell_price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
        orders: List[Order] = []
        if fair - buy_price > threshold and pos < self.LIMIT:
            orders.append(Order(product, buy_price, self.LIMIT - pos if fair - buy_price > threshold + 4 else min(8, self.LIMIT - pos)))
        if sell_price - fair > threshold and pos > -self.LIMIT:
            orders.append(Order(product, sell_price, -(self.LIMIT + pos if sell_price - fair > threshold + 4 else min(8, self.LIMIT + pos))))
        if allow_cross and abs(book["mid"] - fair) > max(9.0, 1.6 * threshold):
            if fair - book["ask"] > threshold + 4.5 and pos < self.LIMIT:
                orders = [Order(product, book["ask"], self.LIMIT - pos)]
            elif book["bid"] - fair > threshold + 4.5 and pos > -self.LIMIT:
                orders = [Order(product, book["bid"], -(self.LIMIT + pos))]
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

    def push(self, cache: dict, key: str, value: float, keep: int) -> List[float]:
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
