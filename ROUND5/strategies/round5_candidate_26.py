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
    PEBBLES = ['PEBBLES_XS', 'PEBBLES_S', 'PEBBLES_M', 'PEBBLES_L', 'PEBBLES_XL']
    PEB_X = {"PEBBLES_XS": 1.0, "PEBBLES_S": 2.0, "PEBBLES_M": 3.0, "PEBBLES_L": 4.0, "PEBBLES_XL": 5.0}
    PEB_BOOST = {"PEBBLES_XL": 1.15, "PEBBLES_M": 1.08, "PEBBLES_L": 1.0, "PEBBLES_S": 0.92, "PEBBLES_XS": 0.92}
    PEB_AGGRESSION = 1.0
    PEB_ALLOW_TAKE = 1
    SIGNAL_CONFIG = {'UV_VISOR_ORANGE': ('momentum', 200, 0.92, 1.25, 'passive'), 'ROBOT_IRONING': ('vol_norm_momentum', 100, 0.92, 1.1, 'passive'), 'SLEEP_POD_COTTON': ('momentum', 100, 0.95, 1.05, 'passive'), 'OXYGEN_SHAKE_GARLIC': ('reversal', 200, 0.86, 1.3, 'passive'), 'PANEL_4X4': ('momentum', 50, 0.78, 1.35, 'passive'), 'MICROCHIP_OVAL': ('breakout_low_reversal', 200, 0.82, 1.15, 'passive'), 'OXYGEN_SHAKE_EVENING_BREATH': ('reversal', 100, 1.02, 0.8, 'passive')}
    MAX_SIGNAL_PRODUCTS = 11

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        self.run_pebbles(state, cache, result)
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
            rvol = self.std(self.push(cache, "r_" + product, residual, 180)[-90:], 4.0)
            result[product] = self.quote_pebble(product, books[product], fairs[product], state.position.get(product, 0), rvol)

    def quote_pebble(self, product: str, book: dict, fair: float, pos: int, rvol: float) -> List[Order]:
        orders: List[Order] = []
        fair -= 0.90 * pos
        edge_floor = max(1.7, min(8.3, 0.29 * rvol)) / (self.PEB_BOOST[product] * self.PEB_AGGRESSION)
        buy_price = self.improve_bid(book)
        sell_price = self.improve_ask(book)
        buy_edge = fair - buy_price
        sell_edge = sell_price - fair
        if buy_edge > edge_floor and pos < self.LIMIT:
            qty = self.LIMIT - pos if buy_edge > edge_floor + 3.0 else min(8, self.LIMIT - pos)
            orders.append(Order(product, buy_price, qty))
        if sell_edge > edge_floor and pos > -self.LIMIT:
            qty = self.LIMIT + pos if sell_edge > edge_floor + 3.0 else min(8, self.LIMIT + pos)
            orders.append(Order(product, sell_price, -qty))
        if self.PEB_ALLOW_TAKE and abs(book["mid"] - fair) > max(10.5, 1.85 * rvol):
            if fair - book["ask"] > edge_floor + 5.8 and pos < self.LIMIT:
                orders = [Order(product, book["ask"], self.LIMIT - pos)]
            elif book["bid"] - fair > edge_floor + 5.8 and pos > -self.LIMIT:
                orders = [Order(product, book["bid"], -(self.LIMIT + pos))]
        return orders

    def run_signals(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for product, cfg in self.SIGNAL_CONFIG.items():
            mode, lookback, threshold, weight = cfg[:4]
            style = cfg[4] if len(cfg) > 4 else "passive"
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, "h_" + product, book["mid"], max(620, lookback + 180))
            if len(hist) <= lookback + 3:
                continue
            signal = self.signal(mode, hist, lookback)
            signal += 0.08 * book["imb"]
            spread_penalty = max(0.0, book["spread"] - 9) * 0.015
            threshold = threshold + spread_penalty
            score = abs(signal) / max(threshold, 0.01) * weight
            if abs(signal) >= threshold:
                scored.append((score, product, book, signal, threshold, weight, style))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _, product, book, signal, threshold, weight, style in scored[: self.MAX_SIGNAL_PRODUCTS]:
            result[product] = self.trade_signal(product, book, state.position.get(product, 0), signal, threshold, weight, style)

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

    def trade_signal(self, product: str, book: dict, pos: int, signal: float, threshold: float, weight: float, style: str) -> List[Order]:
        strong = abs(signal) > threshold + 0.85
        base_qty = 10 if strong or weight >= 1.2 else 6
        if signal > 0 and pos < self.LIMIT:
            price = book["ask"] if style == "hybrid" and abs(signal) > threshold + 0.55 else self.improve_bid(book)
            return [Order(product, price, min(base_qty, self.LIMIT - pos))]
        if signal < 0 and pos > -self.LIMIT:
            price = book["bid"] if style == "hybrid" and abs(signal) > threshold + 0.55 else self.improve_ask(book)
            return [Order(product, price, -min(base_qty, self.LIMIT + pos))]
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
