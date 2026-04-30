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
    GROUPS: List[Tuple[str, List[str], Dict[str, float]]] = [
        ("PEBBLES", ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"], {"PEBBLES_XS": 1, "PEBBLES_S": 2, "PEBBLES_M": 3, "PEBBLES_L": 4, "PEBBLES_XL": 5}),
        ("SLEEP", ["SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON", "SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL"], {"SLEEP_POD_POLYESTER": 1.0, "SLEEP_POD_NYLON": 1.6, "SLEEP_POD_COTTON": 2.2, "SLEEP_POD_SUEDE": 4.0, "SLEEP_POD_LAMB_WOOL": 5.0}),
        ("MICRO", ["MICROCHIP_TRIANGLE", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_OVAL", "MICROCHIP_CIRCLE"], {"MICROCHIP_TRIANGLE": 3.0, "MICROCHIP_SQUARE": 4.0, "MICROCHIP_RECTANGLE": 4.6, "MICROCHIP_OVAL": 5.5, "MICROCHIP_CIRCLE": 6.0}),
        ("PANEL", ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"], {"PANEL_1X2": 2, "PANEL_2X2": 4, "PANEL_1X4": 4.2, "PANEL_2X4": 8, "PANEL_4X4": 16}),
        ("UV", ["UV_VISOR_RED", "UV_VISOR_ORANGE", "UV_VISOR_AMBER", "UV_VISOR_YELLOW", "UV_VISOR_MAGENTA"], {"UV_VISOR_RED": 1, "UV_VISOR_ORANGE": 2, "UV_VISOR_AMBER": 2.5, "UV_VISOR_YELLOW": 3, "UV_VISOR_MAGENTA": 5}),
    ]
    ACTIVE = {"PEBBLES_XL", "PEBBLES_M", "PEBBLES_L", "PEBBLES_S", "PEBBLES_XS", "MICROCHIP_SQUARE", "UV_VISOR_AMBER"}

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        opportunities = []
        for group, products, xmap in self.GROUPS:
            books = {p: self.book(state, p) for p in products}
            if any(books[p] is None for p in products):
                continue
            mids = {p: books[p]["mid"] for p in products}
            fairs = {p: self.fit_predict([xmap[q] for q in products if q != p], [mids[q] for q in products if q != p], xmap[p]) for p in products}
            for product in products:
                residual = mids[product] - fairs[product]
                rvol = self.std(self.push(cache, group + product, residual, 140)[-70:], 5.0 if group == "PEBBLES" else 90.0)
                score = abs(residual) / max(rvol, 1.0)
                if product in self.ACTIVE:
                    opportunities.append((score, product, group, books[product], fairs[product], rvol))
        opportunities.sort(reverse=True, key=lambda x: x[0])
        for _, product, group, book, fair, rvol in opportunities[:7]:
            result[product] = self.trade(product, group, book, fair, state.position.get(product, 0), rvol)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, group: str, book: dict, fair: float, pos: int, rvol: float) -> List[Order]:
        min_edge = max(2.0, min(10.0 if group == "PEBBLES" else 75.0, (0.34 if group == "PEBBLES" else 0.28) * rvol))
        if product == "MICROCHIP_SQUARE":
            hist = book.get("hist", 0)
            min_edge = max(min_edge, 28.0)
        fair -= 0.85 * pos
        buy_price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
        sell_price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
        orders: List[Order] = []
        if fair - buy_price > min_edge and pos < self.LIMIT:
            orders.append(Order(product, buy_price, self.LIMIT - pos if fair - buy_price > min_edge * 1.8 else min(6, self.LIMIT - pos)))
        if sell_price - fair > min_edge and pos > -self.LIMIT:
            orders.append(Order(product, sell_price, -(self.LIMIT + pos if sell_price - fair > min_edge * 1.8 else min(6, self.LIMIT + pos))))
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
