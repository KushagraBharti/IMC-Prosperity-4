from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

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
    GROUPS: List[Tuple[str, List[str], Dict[str, float], List[str], float]] = [
        ("SLEEP", ["SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON", "SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL"], {"SLEEP_POD_POLYESTER": 1.0, "SLEEP_POD_NYLON": 1.6, "SLEEP_POD_COTTON": 2.2, "SLEEP_POD_SUEDE": 4.0, "SLEEP_POD_LAMB_WOOL": 5.0}, ["SLEEP_POD_POLYESTER", "SLEEP_POD_COTTON"], 0.45),
        ("PANEL", ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"], {"PANEL_1X2": 2, "PANEL_2X2": 4, "PANEL_1X4": 4.2, "PANEL_2X4": 8, "PANEL_4X4": 16}, ["PANEL_2X2"], 0.45),
        ("UV", ["UV_VISOR_RED", "UV_VISOR_ORANGE", "UV_VISOR_AMBER", "UV_VISOR_YELLOW", "UV_VISOR_MAGENTA"], {"UV_VISOR_RED": 1, "UV_VISOR_ORANGE": 2, "UV_VISOR_AMBER": 2.5, "UV_VISOR_YELLOW": 3, "UV_VISOR_MAGENTA": 5}, ["UV_VISOR_AMBER"], 0.35),
    ]

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        for group, products, xmap, active, mult in self.GROUPS:
            books = {p: self.book(state, p) for p in products}
            if any(books[p] is None for p in products):
                continue
            mids = {p: books[p]["mid"] for p in products}
            for product in active:
                fair = self.fit_predict([xmap[q] for q in products if q != product], [mids[q] for q in products if q != product], xmap[product])
                residual = mids[product] - fair
                hist = self.push(cache, group + product, residual, 160)
                result[product] = self.trade(product, books[product], fair, state.position.get(product, 0), max(50.0, mult * self.std(hist, 100.0)))
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, book: dict, fair: float, pos: int, threshold: float) -> List[Order]:
        fair -= 0.90 * pos
        buy_price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
        sell_price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
        orders: List[Order] = []
        if fair - buy_price > threshold and pos < self.LIMIT:
            orders.append(Order(product, buy_price, self.LIMIT - pos if fair - buy_price > threshold * 1.8 else min(5, self.LIMIT - pos)))
        if sell_price - fair > threshold and pos > -self.LIMIT:
            orders.append(Order(product, sell_price, -(self.LIMIT + pos if sell_price - fair > threshold * 1.8 else min(5, self.LIMIT + pos))))
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
