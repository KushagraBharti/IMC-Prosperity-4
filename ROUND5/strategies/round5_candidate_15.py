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
        (
            "pebbles",
            ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
            {"PEBBLES_XS": 1.0, "PEBBLES_S": 2.0, "PEBBLES_M": 3.0, "PEBBLES_L": 4.0, "PEBBLES_XL": 5.0},
            ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
            0.40,
        ),
        (
            "sleep",
            ["SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON", "SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL"],
            {"SLEEP_POD_POLYESTER": 1.0, "SLEEP_POD_NYLON": 1.6, "SLEEP_POD_COTTON": 2.2, "SLEEP_POD_SUEDE": 4.0, "SLEEP_POD_LAMB_WOOL": 5.0},
            ["SLEEP_POD_POLYESTER", "SLEEP_POD_COTTON"],
            0.22,
        ),
        (
            "microchip",
            ["MICROCHIP_TRIANGLE", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_OVAL", "MICROCHIP_CIRCLE"],
            {"MICROCHIP_TRIANGLE": 3.0, "MICROCHIP_SQUARE": 4.0, "MICROCHIP_RECTANGLE": 4.6, "MICROCHIP_OVAL": 5.5, "MICROCHIP_CIRCLE": 6.0},
            ["MICROCHIP_SQUARE"],
            0.28,
        ),
    ]

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        scored: List[Tuple[float, str, dict, float, float]] = []
        for group, products, xmap, trade_list, vol_mult in self.GROUPS:
            books = {p: self.book(state, p) for p in products}
            if any(books[p] is None for p in products):
                continue
            mids = {p: books[p]["mid"] for p in products}
            fairs = self.leave_one_line(mids, xmap)
            for product in trade_list:
                residual = mids[product] - fairs[product]
                hist = self.push(cache, group + "_r_" + product, residual, 180)
                rvol = self.std(hist[-80:], 4.0 if group == "pebbles" else 80.0)
                score = abs(residual) / max(rvol, 1.0)
                scored.append((score, product, books[product], fairs[product], max(2.0, vol_mult * rvol)))

        scored.sort(reverse=True, key=lambda row: row[0])
        for _, product, book, fair, cushion in scored[:7]:
            result[product] = self.trade(product, book, fair, state.position.get(product, 0), cushion)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, book: dict, fair: float, pos: int, cushion: float) -> List[Order]:
        orders: List[Order] = []
        adj_fair = fair - 0.80 * pos
        buy_price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
        sell_price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
        buy_edge = adj_fair - buy_price
        sell_edge = sell_price - adj_fair
        if buy_edge > cushion and pos < self.LIMIT:
            qty = self.LIMIT - pos if buy_edge > cushion * 1.7 else min(7, self.LIMIT - pos)
            orders.append(Order(product, buy_price, qty))
        if sell_edge > cushion and pos > -self.LIMIT:
            qty = self.LIMIT + pos if sell_edge > cushion * 1.7 else min(7, self.LIMIT + pos)
            orders.append(Order(product, sell_price, -qty))
        return orders

    def leave_one_line(self, mids: Dict[str, float], xmap: Dict[str, float]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for target in mids:
            xs = [xmap[p] for p in mids if p != target]
            ys = [mids[p] for p in mids if p != target]
            out[target] = self.fit_predict(xs, ys, xmap[target])
        return out

    def fit_predict(self, xs: List[float], ys: List[float], x0: float) -> float:
        mx = sum(xs) / len(xs)
        my = sum(ys) / len(ys)
        den = sum((x - mx) * (x - mx) for x in xs)
        if den <= 1e-9:
            return my
        slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs))) / den
        return my + slope * (x0 - mx)

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
        mean = sum(values) / len(values)
        return max(default, math.sqrt(sum((x - mean) * (x - mean) for x in values) / len(values)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
