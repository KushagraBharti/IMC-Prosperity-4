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
    PEBBLES = []
    PEB_X = {"PEBBLES_XS": 1.0, "PEBBLES_S": 2.0, "PEBBLES_M": 3.0, "PEBBLES_L": 4.0, "PEBBLES_XL": 5.0}
    PEB_BOOST = {"PEBBLES_XL": 1.15, "PEBBLES_M": 1.08, "PEBBLES_L": 1.0, "PEBBLES_S": 0.92, "PEBBLES_XS": 0.92}
    SIGNAL_CONFIG = {'UV_VISOR_ORANGE': ('momentum', 100, 0.95, 1.2), 'SLEEP_POD_COTTON': ('momentum', 100, 0.95, 1.1), 'TRANSLATOR_GRAPHITE_MIST': ('momentum', 100, 1.1, 0.9), 'SLEEP_POD_POLYESTER': ('reversal', 100, 1.0, 0.9), 'PANEL_2X4': ('momentum', 50, 1.0, 0.85), 'ROBOT_MOPPING': ('momentum', 50, 1.0, 0.85), 'TRANSLATOR_VOID_BLUE': ('reversal', 100, 1.0, 0.8), 'MICROCHIP_RECTANGLE': ('momentum', 50, 1.0, 0.7), 'SLEEP_POD_NYLON': ('reversal', 100, 1.05, 0.65), 'SLEEP_POD_LAMB_WOOL': ('momentum', 100, 1.05, 0.55)}
    MAX_SIGNAL_PRODUCTS = 8

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        if self.PEBBLES:
            self.run_pebbles(state, cache, result)
        if self.SIGNAL_CONFIG:
            self.run_signals(state, cache, result)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def run_pebbles(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        books = {p: self.book(state, p) for p in self.PEBBLES}
        if any(books[p] is None for p in self.PEBBLES):
            return
        mids = {p: books[p]["mid"] for p in self.PEBBLES}
        fairs = {p: self.fit_predict([self.PEB_X[q] for q in mids if q != p], [mids[q] for q in mids if q != p], self.PEB_X[p]) for p in mids}
        for product in self.PEBBLES:
            residual = mids[product] - fairs[product]
            rvol = self.std(self.push(cache, "r_" + product, residual, 160)[-80:], 4.0)
            result[product] = self.quote_pebble(product, books[product], fairs[product], state.position.get(product, 0), rvol)

    def quote_pebble(self, product: str, book: dict, fair: float, pos: int, rvol: float) -> List[Order]:
        orders: List[Order] = []
        fair -= 0.90 * pos
        edge_floor = max(1.8, min(8.5, 0.30 * rvol)) / self.PEB_BOOST[product]
        buy_price = self.improve_bid(book)
        sell_price = self.improve_ask(book)
        buy_edge = fair - buy_price
        sell_edge = sell_price - fair
        if buy_edge > edge_floor and pos < self.LIMIT:
            qty = self.LIMIT - pos if buy_edge > edge_floor + 3.2 else min(8, self.LIMIT - pos)
            orders.append(Order(product, buy_price, qty))
        if sell_edge > edge_floor and pos > -self.LIMIT:
            qty = self.LIMIT + pos if sell_edge > edge_floor + 3.2 else min(8, self.LIMIT + pos)
            orders.append(Order(product, sell_price, -qty))
        if abs(book["mid"] - fair) > max(11.0, 1.9 * rvol):
            if fair - book["ask"] > edge_floor + 6.0 and pos < self.LIMIT:
                orders = [Order(product, book["ask"], self.LIMIT - pos)]
            elif book["bid"] - fair > edge_floor + 6.0 and pos > -self.LIMIT:
                orders = [Order(product, book["bid"], -(self.LIMIT + pos))]
        return orders

    def run_signals(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for product, (mode, lookback, threshold, weight) in self.SIGNAL_CONFIG.items():
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, "h_" + product, book["mid"], max(240, lookback + 140))
            if len(hist) <= lookback + 2:
                continue
            signal = (hist[-1] - hist[-1 - lookback]) / max(self.vol(hist[-140:]), 1.0)
            if mode == "reversal":
                signal = -signal
            signal += 0.08 * book["imb"]
            score = abs(signal) / max(threshold, 0.01) * weight
            if abs(signal) >= threshold:
                scored.append((score, product, book, signal, threshold))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _, product, book, signal, threshold in scored[: self.MAX_SIGNAL_PRODUCTS]:
            result[product] = self.trade_signal(product, book, state.position.get(product, 0), signal, threshold)

    def trade_signal(self, product: str, book: dict, pos: int, signal: float, threshold: float) -> List[Order]:
        if signal > 0 and pos < self.LIMIT:
            price = self.improve_bid(book)
            qty = self.LIMIT - pos if signal > threshold + 1.0 else min(6, self.LIMIT - pos)
            return [Order(product, price, qty)]
        if signal < 0 and pos > -self.LIMIT:
            price = self.improve_ask(book)
            qty = self.LIMIT + pos if signal < -threshold - 1.0 else min(6, self.LIMIT + pos)
            return [Order(product, price, -qty)]
        return []

    def fit_predict(self, xs: List[float], ys: List[float], x0: float) -> float:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        den = sum((x - mx) ** 2 for x in xs)
        if den <= 1e-9:
            return my
        slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs))) / den
        return my + slope * (x0 - mx)

    def improve_bid(self, book: dict) -> int:
        return min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]

    def improve_ask(self, book: dict) -> int:
        return max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]

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

    def std(self, values: List[float], default: float) -> float:
        if len(values) < 3:
            return default
        m = sum(values) / len(values)
        return max(default, math.sqrt(sum((x - m) ** 2 for x in values) / len(values)))

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
