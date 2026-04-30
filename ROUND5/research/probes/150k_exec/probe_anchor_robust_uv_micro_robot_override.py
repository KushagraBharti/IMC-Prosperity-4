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


# Temporary executable 150k probe: probe_c35_anchor_both_micro_uv_conservative
# Temporary broad 10000-anchor probe: probe_anchor_robust_uv_micro_robot_override
class Trader:
    LIMIT = 10
    ANCHOR = 10000
    ANCHOR_PRODUCTS = {'TRANSLATOR_ECLIPSE_CHARCOAL', 'PEBBLES_L'}
    PEBBLES = ['PEBBLES_XS', 'PEBBLES_S', 'PEBBLES_M', 'PEBBLES_L', 'PEBBLES_XL']
    PEB_X = {"PEBBLES_XS": 1.0, "PEBBLES_S": 2.0, "PEBBLES_M": 3.0, "PEBBLES_L": 4.0, "PEBBLES_XL": 5.0}
    PEB_BOOST = {'PEBBLES_XL': 1.15, 'PEBBLES_M': 1.18, 'PEBBLES_L': 1.08, 'PEBBLES_S': 0.92, 'PEBBLES_XS': 1.02}
    PEB_AGGRESSION = 1.08
    PEB_ALLOW_TAKE = 1
    SIGNAL_CONFIG = {'OXYGEN_SHAKE_GARLIC': ('reversal', 200, 0.82, 1.3, 'passive'),
     'UV_VISOR_ORANGE': ('momentum', 200, 0.86, 1.25, 'passive'),
     'PANEL_4X4': ('momentum', 50, 0.76, 1.35, 'passive'),
     'ROBOT_IRONING': ('vol_norm_momentum', 100, 0.88, 1.1, 'passive'),
     'MICROCHIP_OVAL': ('breakout_low_reversal', 200, 0.8, 1.15, 'passive'),
     'GALAXY_SOUNDS_DARK_MATTER': ('breakout_high', 200, 0.96, 0.85, 'passive'),
     'GALAXY_SOUNDS_SOLAR_FLAMES': ('rolling_mean_reversion', 200, 0.96, 0.78, 'passive'),
     'GALAXY_SOUNDS_SOLAR_WINDS': ('rolling_mean_reversion', 200, 1.02, 0.65, 'passive'),
     'GALAXY_SOUNDS_PLANETARY_RINGS': ('breakout_low_reversal', 200, 0.84, 1.05, 'passive'),
     'TRANSLATOR_SPACE_GRAY': ('breakout_high', 500, 0.92, 1.1, 'passive'),
     'PANEL_1X2': ('breakout_low_reversal', 200, 0.96, 0.75, 'passive'),
     'PANEL_1X4': ('breakout_low_reversal', 200, 0.96, 0.72, 'passive'),
     'PANEL_2X2': ('breakout_low_reversal', 200, 1.02, 0.55, 'passive'),
     'OXYGEN_SHAKE_MORNING_BREATH': ('breakout_high', 200, 0.92, 0.95, 'passive'),
     'OXYGEN_SHAKE_CHOCOLATE': ('rolling_mean_reversion', 200, 0.98, 0.75, 'passive'),
     'OXYGEN_SHAKE_EVENING_BREATH': ('reversal', 100, 0.98, 0.8, 'passive'),
     'OXYGEN_SHAKE_MINT': ('breakout_low_reversal', 500, 1.02, 0.58, 'passive'),
     'UV_VISOR_RED': ('momentum', 200, 0.94, 0.82, 'passive'),
     'UV_VISOR_YELLOW': ('breakout_low_reversal', 500, 1.0, 0.58, 'passive'),
     'SLEEP_POD_COTTON': ('momentum', 100, 0.94, 1.0, 'passive'),
     'SLEEP_POD_LAMB_WOOL': ('breakout_low_reversal', 500, 0.98, 0.72, 'passive'),
     'SLEEP_POD_NYLON': ('rolling_mean_reversion', 200, 1.02, 0.55, 'passive'),
     'MICROCHIP_SQUARE': ('breakout_low_reversal', 200, 0.78, 1.15, 'passive'),
     'MICROCHIP_RECTANGLE': ('breakout_low_reversal', 200, 0.88, 0.95, 'passive'),
     'TRANSLATOR_GRAPHITE_MIST': ('momentum', 100, 1.1, 0.9, 'passive'),
     'TRANSLATOR_VOID_BLUE': ('reversal', 100, 1.0, 0.8, 'passive'),
     'SLEEP_POD_POLYESTER': ('reversal', 100, 1.0, 0.9, 'passive'),
     'PANEL_2X4': ('momentum', 50, 0.86, 1.0, 'passive'),
     'SLEEP_POD_SUEDE': ('reversal', 100, 0.94, 1.0, 'passive'),
     'GALAXY_SOUNDS_BLACK_HOLES': ('reversal', 50, 0.98, 0.75, 'passive'),
     'TRANSLATOR_ASTRO_BLACK': ('momentum', 100, 1.0, 0.75, 'passive'),
     'SNACKPACK_STRAWBERRY': ('reversal', 200, 1.08, 0.6, 'passive'),
     'SNACKPACK_RASPBERRY': ('reversal', 200, 1.08, 0.55, 'passive'),
     'SNACKPACK_PISTACHIO': ('reversal', 200, 1.08, 0.5, 'passive'),
     'ROBOT_VACUUMING': ('reversal', 200, 1.02, 0.55, 'passive'),
     'MICROCHIP_TRIANGLE': ('reversal', 150, 1.15, 0.48, 'passive'),
     'UV_VISOR_AMBER': ('momentum', 150, 0.98, 0.52, 'passive')}
    MAX_SIGNAL_PRODUCTS = 37
    BROAD_ANCHOR = 10000
    BROAD_ANCHOR_PRODUCTS = {'UV_VISOR_ORANGE', 'ROBOT_VACUUMING', 'UV_VISOR_YELLOW', 'ROBOT_LAUNDRY', 'MICROCHIP_TRIANGLE', 'MICROCHIP_SQUARE', 'MICROCHIP_RECTANGLE', 'ROBOT_IRONING', 'UV_VISOR_MAGENTA', 'UV_VISOR_AMBER', 'UV_VISOR_RED', 'MICROCHIP_OVAL', 'ROBOT_MOPPING', 'MICROCHIP_CIRCLE'}
    BROAD_ANCHOR_OVERRIDE = True
    BROAD_ANCHOR_TAKE_EDGE = 10
    BROAD_ANCHOR_PASSIVE_EDGE = 2
    BROAD_ANCHOR_SIZE = 5
    BROAD_ANCHOR_MIN_SPREAD = 3
    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        self.run_pebbles(state, cache, result)
        self.run_signals(state, cache, result)
        self.run_broad_anchor(state, result)
        self.run_anchor(state, result)
        return result, 0, self.dump_cache(cache)



    def run_broad_anchor(self, state: TradingState, result: Dict[str, List[Order]]) -> None:
        for product in self.BROAD_ANCHOR_PRODUCTS:
            depth = state.order_depths.get(product)
            if not depth or not depth.buy_orders or not depth.sell_orders:
                continue
            orders = self.trade_broad_anchor(product, depth, state.position.get(product, 0))
            if orders and (self.BROAD_ANCHOR_OVERRIDE or product not in result):
                result[product] = orders

    def trade_broad_anchor(self, product: str, depth, position: int) -> List[Order]:
        orders: List[Order] = []
        start = position
        for ask_price, ask_volume in sorted(depth.sell_orders.items())[:2]:
            if position >= self.LIMIT:
                break
            if self.BROAD_ANCHOR - ask_price >= self.BROAD_ANCHOR_TAKE_EDGE:
                quantity = min(self.LIMIT - position, max(0, -int(ask_volume)))
                if quantity:
                    orders.append(Order(product, int(ask_price), int(quantity)))
                    position += quantity
        for bid_price, bid_volume in sorted(depth.buy_orders.items(), reverse=True)[:2]:
            if position <= -self.LIMIT:
                break
            if bid_price - self.BROAD_ANCHOR >= self.BROAD_ANCHOR_TAKE_EDGE:
                quantity = min(self.LIMIT + position, max(0, int(bid_volume)))
                if quantity:
                    orders.append(Order(product, int(bid_price), int(-quantity)))
                    position -= quantity
        bid = max(depth.buy_orders)
        ask = min(depth.sell_orders)
        if ask - bid >= self.BROAD_ANCHOR_MIN_SPREAD:
            if position < self.LIMIT and self.BROAD_ANCHOR - (bid + 1) >= self.BROAD_ANCHOR_PASSIVE_EDGE:
                orders.append(Order(product, int(bid + 1), int(min(self.BROAD_ANCHOR_SIZE, self.LIMIT - position))))
            if position > -self.LIMIT and (ask - 1) - self.BROAD_ANCHOR >= self.BROAD_ANCHOR_PASSIVE_EDGE:
                orders.append(Order(product, int(ask - 1), int(-min(self.BROAD_ANCHOR_SIZE, self.LIMIT + position))))
        return self.ensure_limit(product, start, orders)

    def run_anchor(self, state: TradingState, result: Dict[str, List[Order]]) -> None:
        for product in self.ANCHOR_PRODUCTS:
            depth = state.order_depths.get(product)
            if not depth or not depth.buy_orders or not depth.sell_orders:
                continue
            orders = self.trade_anchor(product, depth, state.position.get(product, 0))
            if orders:
                result[product] = orders

    def trade_anchor(self, product: str, depth, position: int) -> List[Order]:
        orders: List[Order] = []
        start = position
        for ask_price, ask_volume in sorted(depth.sell_orders.items())[:2]:
            if position >= self.LIMIT:
                break
            if self.ANCHOR - ask_price >= 2:
                quantity = min(self.LIMIT - position, max(0, -int(ask_volume)))
                if quantity:
                    orders.append(Order(product, int(ask_price), int(quantity)))
                    position += quantity
        for bid_price, bid_volume in sorted(depth.buy_orders.items(), reverse=True)[:2]:
            if position <= -self.LIMIT:
                break
            if bid_price - self.ANCHOR >= 2:
                quantity = min(self.LIMIT + position, max(0, int(bid_volume)))
                if quantity:
                    orders.append(Order(product, int(bid_price), int(-quantity)))
                    position -= quantity
        bid = max(depth.buy_orders)
        ask = min(depth.sell_orders)
        if bid + 1 < ask:
            if position < self.LIMIT:
                orders.append(Order(product, int(min(bid + 1, self.ANCHOR - 2)), int(min(3, self.LIMIT - position))))
            if position > -self.LIMIT:
                orders.append(Order(product, int(max(ask - 1, self.ANCHOR + 2)), int(-min(3, self.LIMIT + position))))
        return self.ensure_limit(product, start, orders)

    def ensure_limit(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        checked: List[Order] = []
        for order in orders:
            quantity = int(order.quantity)
            if quantity > 0:
                quantity = min(quantity, self.LIMIT - position)
            elif quantity < 0:
                quantity = -min(-quantity, self.LIMIT + position)
            if quantity:
                checked.append(Order(product, int(order.price), int(quantity)))
                position += quantity
        return checked

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

    STATE_TARGET = 45000
    PRODUCT_ALIASES = {'PEBBLES_XS': '0', 'PEBBLES_S': '1', 'PEBBLES_M': '2', 'PEBBLES_L': '3', 'PEBBLES_XL': '4', 'MICROCHIP_CIRCLE': '5', 'MICROCHIP_OVAL': '6', 'MICROCHIP_SQUARE': '7', 'MICROCHIP_RECTANGLE': '8', 'MICROCHIP_TRIANGLE': '9', 'PANEL_1X2': 'a', 'PANEL_1X4': 'b', 'PANEL_2X2': 'c', 'PANEL_2X4': 'd', 'PANEL_4X4': 'e', 'OXYGEN_SHAKE_MORNING_BREATH': 'f', 'OXYGEN_SHAKE_EVENING_BREATH': 'g', 'OXYGEN_SHAKE_MINT': 'h', 'OXYGEN_SHAKE_CHOCOLATE': 'i', 'OXYGEN_SHAKE_GARLIC': 'j', 'UV_VISOR_YELLOW': 'k', 'UV_VISOR_AMBER': 'l', 'UV_VISOR_ORANGE': 'm', 'UV_VISOR_RED': 'n', 'UV_VISOR_MAGENTA': 'o', 'ROBOT_DISHES': 'p', 'ROBOT_MOPPING': 'q', 'ROBOT_LAUNDRY': 'r', 'ROBOT_IRONING': 's', 'ROBOT_VACUUMING': 't', 'SLEEP_POD_COTTON': 'u', 'SLEEP_POD_POLYESTER': 'v', 'SLEEP_POD_SUEDE': 'w', 'SLEEP_POD_LAMB_WOOL': 'x', 'SLEEP_POD_NYLON': 'y', 'TRANSLATOR_GRAPHITE_MIST': 'z', 'TRANSLATOR_VOID_BLUE': 'A', 'TRANSLATOR_ASTRO_BLACK': 'B', 'TRANSLATOR_SPACE_GRAY': 'C', 'TRANSLATOR_ECLIPSE_CHARCOAL': 'D', 'GALAXY_SOUNDS_PLANETARY_RINGS': 'E', 'GALAXY_SOUNDS_SOLAR_WINDS': 'F', 'GALAXY_SOUNDS_DARK_MATTER': 'G', 'GALAXY_SOUNDS_BLACK_HOLES': 'H', 'GALAXY_SOUNDS_SOLAR_FLAMES': 'I', 'SNACKPACK_RASPBERRY': 'J', 'SNACKPACK_STRAWBERRY': 'K', 'SNACKPACK_CHOCOLATE': 'L', 'SNACKPACK_VANILLA': 'M', 'SNACKPACK_PISTACHIO': 'N'}
    PRODUCT_BY_ALIAS = {v: k for k, v in PRODUCT_ALIASES.items()}
    PREFIX_ALIASES = {"h_": "h", "r_": "r", "xrel_": "x", "mom_": "m"}
    PREFIX_BY_ALIAS = {"h": "h_", "r": "r_", "x": "xrel_", "m": "mom_"}

    def dump_cache(self, cache: dict) -> str:
        compact = {}
        for key, values in cache.items():
            if not isinstance(values, list):
                continue
            keep = self.cache_keep(key)
            trimmed = values[-keep:] if keep > 0 else values
            compact[self.short_key(key)] = self.pack_series(key, trimmed)
        return json.dumps({"c": compact}, separators=(",", ":"))

    def load_cache(self, raw: str) -> dict:
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            return {}
        if isinstance(data, dict) and "c" in data:
            cache = {}
            for short, packed in data.get("c", {}).items():
                key = self.long_key(short)
                cache[key] = self.unpack_series(key, packed)
            return cache
        return data if isinstance(data, dict) else {}

    def pack_series(self, key: str, values: List[float]) -> list:
        if not values:
            return [0, []]
        scale = self.cache_scale(key)
        ints = [int(round(float(value) * scale)) for value in values]
        base = ints[0]
        deltas = [ints[i] - ints[i - 1] for i in range(1, len(ints))]
        return [base, deltas]

    def unpack_series(self, key: str, packed: list) -> List[float]:
        if not isinstance(packed, list) or len(packed) != 2:
            return []
        scale = self.cache_scale(key)
        current = int(packed[0])
        values = [current / scale]
        deltas = packed[1] if isinstance(packed[1], list) else []
        for delta in deltas:
            current += int(delta)
            values.append(current / scale)
        return values

    def cache_scale(self, key: str) -> int:
        if key.startswith("r_"):
            return 1000
        if key.startswith("xrel_"):
            return 100
        return 2

    def cache_keep(self, key: str) -> int:
        if key.startswith("r_"):
            return 90
        if key.startswith("xrel_"):
            return 180
        if key.startswith("mom_"):
            product = key[4:]
            cfg = self.MOMENTUM_EXTRAS.get(product) if hasattr(self, "MOMENTUM_EXTRAS") else None
            lookback = int(cfg[0]) if cfg else 220
            return max(lookback + 6, 140)
        if key.startswith("h_"):
            product = key[2:]
            cfg = self.SIGNAL_CONFIG.get(product) if hasattr(self, "SIGNAL_CONFIG") else None
            lookback = int(cfg[1]) if cfg else 220
            return max(lookback + 6, 180)
        return 220

    def short_key(self, key: str) -> str:
        for prefix, short_prefix in self.PREFIX_ALIASES.items():
            if key.startswith(prefix):
                product = key[len(prefix):]
                return short_prefix + self.PRODUCT_ALIASES.get(product, product)
        return key

    def long_key(self, short: str) -> str:
        if not short:
            return short
        prefix = self.PREFIX_BY_ALIAS.get(short[0])
        if not prefix:
            return short
        product = self.PRODUCT_BY_ALIAS.get(short[1:], short[1:])
        return prefix + product
