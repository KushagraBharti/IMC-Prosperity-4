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
    PRODUCTS = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]
    X = {"PEBBLES_XS": 1.0, "PEBBLES_S": 2.0, "PEBBLES_M": 3.0, "PEBBLES_L": 4.0, "PEBBLES_XL": 5.0}

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        books = {p: self.book(state, p) for p in self.PRODUCTS}
        if any(books[p] is None for p in self.PRODUCTS):
            return result, 0, json.dumps(cache, separators=(",", ":"))

        mids = {p: books[p]["mid"] for p in self.PRODUCTS}
        fairs = self.leave_one_line(mids, self.X)
        for product in self.PRODUCTS:
            residual = mids[product] - fairs[product]
            rhist = self.push(cache, "r_" + product, residual, 180)
            rvol = self.std(rhist[-80:])
            result[product] = self.trade_fair_value(
                product,
                books[product],
                fairs[product],
                state.position.get(product, 0),
                max(2.5, min(12.0, 0.65 * rvol)),
            )
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade_fair_value(self, product: str, book: dict, fair: float, pos: int, cushion: float) -> List[Order]:
        orders: List[Order] = []
        adj_fair = fair - 0.55 * pos
        buy_price = self.passive_buy(book)
        sell_price = self.passive_sell(book)
        buy_edge = adj_fair - buy_price
        sell_edge = sell_price - adj_fair
        if buy_edge > cushion and pos < self.LIMIT:
            qty = self.LIMIT - pos if buy_edge > cushion * 1.8 else min(6, self.LIMIT - pos)
            orders.append(Order(product, buy_price, qty))
        if sell_edge > cushion and pos > -self.LIMIT:
            qty = self.LIMIT + pos if sell_edge > cushion * 1.8 else min(6, self.LIMIT + pos)
            orders.append(Order(product, sell_price, -qty))
        if not orders and pos > 7 and sell_edge > 0:
            orders.append(Order(product, sell_price, -min(5, pos)))
        elif not orders and pos < -7 and buy_edge > 0:
            orders.append(Order(product, buy_price, min(5, -pos)))
        return orders

    def leave_one_line(self, mids: Dict[str, float], xmap: Dict[str, float]) -> Dict[str, float]:
        fairs: Dict[str, float] = {}
        for target in mids:
            xs = [xmap[p] for p in mids if p != target]
            ys = [mids[p] for p in mids if p != target]
            fairs[target] = self.fit_predict(xs, ys, xmap[target])
        return fairs

    def fit_predict(self, xs: List[float], ys: List[float], x0: float) -> float:
        mx = sum(xs) / len(xs)
        my = sum(ys) / len(ys)
        den = sum((x - mx) * (x - mx) for x in xs)
        if den <= 1e-9:
            return my
        slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs))) / den
        return my + slope * (x0 - mx)

    def passive_buy(self, book: dict) -> int:
        return min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]

    def passive_sell(self, book: dict) -> int:
        return max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]

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

    def std(self, values: List[float]) -> float:
        if len(values) < 3:
            return 4.0
        mean = sum(values) / len(values)
        return max(1.0, math.sqrt(sum((x - mean) * (x - mean) for x in values) / len(values)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
