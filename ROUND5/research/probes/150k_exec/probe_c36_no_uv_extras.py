from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List


try:
    from datamodel import Order, OrderDepth, TradingState
except ImportError:
    @dataclass
    class Order:
        symbol: str
        price: int
        quantity: int

    @dataclass
    class OrderDepth:
        buy_orders: Dict[int, int] = field(default_factory=dict)
        sell_orders: Dict[int, int] = field(default_factory=dict)

    @dataclass
    class TradingState:
        order_depths: Dict[str, OrderDepth]
        position: Dict[str, int] = field(default_factory=dict)
        traderData: str = ""
        timestamp: int = 0


# Temporary executable 150k probe: probe_c36_no_uv_extras
class Trader:
    LIMIT = 10
    ANCHOR = 10_000

    # Added only where the edge survives both the broad CSV replay and the
    # uploaded randomized run. Avoids the tempting but unstable anchor names.
    ANCHOR_PRODUCTS = {
        "TRANSLATOR_ECLIPSE_CHARCOAL",
        "PEBBLES_L",
    }

    PEBBLES = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]
    PEB_X = {
        "PEBBLES_XS": 1.0,
        "PEBBLES_S": 2.0,
        "PEBBLES_M": 3.0,
        "PEBBLES_L": 4.0,
        "PEBBLES_XL": 5.0,
    }
    TRADED_PEBBLES = {"PEBBLES_S", "PEBBLES_M", "PEBBLES_XL"}
    PEB_BOOST = {"PEBBLES_XL": 1.15, "PEBBLES_M": 1.08, "PEBBLES_S": 1.12}

    SIGNAL_CONFIG = {
        "UV_VISOR_ORANGE": ("momentum", 100, 1.00, 1.00),
        "SLEEP_POD_COTTON": ("momentum", 100, 1.00, 0.95),
        "TRANSLATOR_GRAPHITE_MIST": ("momentum", 100, 1.10, 0.90),
        "SLEEP_POD_POLYESTER": ("reversal", 100, 1.00, 0.90),
        "ROBOT_MOPPING": ("momentum", 50, 1.05, 0.75),
        "TRANSLATOR_VOID_BLUE": ("reversal", 100, 1.00, 0.80),
        "SLEEP_POD_NYLON": ("reversal", 100, 1.05, 0.70),
    }
    MAX_SIGNAL_PRODUCTS = 5

    EXTRA_GROUPS = {
        "MICRO": [
            "MICROCHIP_CIRCLE",
            "MICROCHIP_OVAL",
            "MICROCHIP_SQUARE",
            "MICROCHIP_RECTANGLE",
            "MICROCHIP_TRIANGLE",
        ],
        "PANELS": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
        "OXYGEN": [
            "OXYGEN_SHAKE_MORNING_BREATH",
            "OXYGEN_SHAKE_EVENING_BREATH",
            "OXYGEN_SHAKE_MINT",
            "OXYGEN_SHAKE_CHOCOLATE",
            "OXYGEN_SHAKE_GARLIC",
        ],
        "UV": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"],
    }
    EXTRA_PRODUCTS = {
        "MICROCHIP_OVAL": (1.45, 0.85),
        "MICROCHIP_SQUARE": (1.45, 0.85),
        "PANEL_1X2": (1.55, 0.70),
        "OXYGEN_SHAKE_MINT": (1.55, 0.70),
    }
    MOMENTUM_EXTRAS = {'TRANSLATOR_SPACE_GRAY': (220, 0.7, 0.8),
     'GALAXY_SOUNDS_PLANETARY_RINGS': (220, 2.0, 0.75),
     'ROBOT_LAUNDRY': (100, 1.25, 0.65),
     'ROBOT_DISHES': (150, 0.75, 0.65),
     'PANEL_4X4': (220, 0.75, 0.6),
     'MICROCHIP_TRIANGLE': (150, 0.95, -0.6),
     'PANEL_2X4': (150, 1.6, 0.55),
     'SLEEP_POD_LAMB_WOOL': (220, 2.0, 0.5),
     'MICROCHIP_RECTANGLE': (220, 2.0, 0.45),
     'PEBBLES_XS': (220, 1.2, 0.45),
     'PANEL_1X4': (220, 0.6, 0.4),
     'PANEL_2X2': (150, 0.8, 0.35),
     'OXYGEN_SHAKE_GARLIC': (150, 0.6, 0.45)}
    MAX_MOMENTUM_EXTRAS = 7
    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}

        self.run_anchor(state, result)
        self.run_pebbles(state, cache, result)
        self.run_signals(state, cache, result)
        self.run_extra_relative(state, cache, result)
        self.run_momentum_extras(state, cache, result)

        return result, 0, self.dump_cache(cache)

    def run_anchor(self, state: TradingState, result: Dict[str, List[Order]]) -> None:
        for product in self.ANCHOR_PRODUCTS:
            depth = state.order_depths.get(product)
            if not depth:
                continue
            orders = self.trade_anchor(product, depth, state.position.get(product, 0))
            if orders:
                result[product] = orders

    def trade_anchor(self, product: str, depth: OrderDepth, position: int) -> List[Order]:
        if not depth.buy_orders or not depth.sell_orders:
            return []
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

    def run_pebbles(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        books = {product: self.book(state, product) for product in self.PEBBLES}
        if any(books[product] is None for product in self.PEBBLES):
            return
        mids = {product: books[product]["mid"] for product in self.PEBBLES}

        for product in self.TRADED_PEBBLES:
            fair = self.fit_predict(
                [self.PEB_X[p] for p in mids if p != product],
                [mids[p] for p in mids if p != product],
                self.PEB_X[product],
            )
            residual = mids[product] - fair
            rvol = self.std(self.push(cache, "r_" + product, residual, 160)[-80:], 4.0)
            orders = self.quote_pebble(product, books[product], fair, state.position.get(product, 0), rvol)
            if orders:
                result[product] = orders

    def quote_pebble(self, product: str, book: dict, fair: float, position: int, rvol: float) -> List[Order]:
        orders: List[Order] = []
        start = position
        fair -= 0.90 * position
        edge_floor = max(1.8, min(8.5, 0.30 * rvol)) / self.PEB_BOOST[product]
        buy_price = self.improve_bid(book)
        sell_price = self.improve_ask(book)

        if fair - buy_price > edge_floor and position < self.LIMIT:
            quantity = self.LIMIT - position if fair - buy_price > edge_floor + 3.2 else min(8, self.LIMIT - position)
            orders.append(Order(product, int(buy_price), int(quantity)))
        if sell_price - fair > edge_floor and position > -self.LIMIT:
            quantity = self.LIMIT + position if sell_price - fair > edge_floor + 3.2 else min(8, self.LIMIT + position)
            orders.append(Order(product, int(sell_price), int(-quantity)))

        if fair - book["ask"] > edge_floor + max(6.0, 1.3 * rvol) and position < self.LIMIT:
            orders = [Order(product, int(book["ask"]), int(self.LIMIT - position))]
        elif book["bid"] - fair > edge_floor + max(6.0, 1.3 * rvol) and position > -self.LIMIT:
            orders = [Order(product, int(book["bid"]), int(-(self.LIMIT + position)))]

        return self.ensure_limit(product, start, orders)

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
            score = abs(signal) / threshold * weight
            if abs(signal) >= threshold:
                scored.append((score, product, book, signal, threshold))

        scored.sort(reverse=True, key=lambda row: row[0])
        for _, product, book, signal, threshold in scored[: self.MAX_SIGNAL_PRODUCTS]:
            orders = self.trade_signal(product, book, state.position.get(product, 0), signal, threshold)
            if orders:
                result[product] = orders

    def trade_signal(self, product: str, book: dict, position: int, signal: float, threshold: float) -> List[Order]:
        if signal > 0 and position < self.LIMIT:
            quantity = self.LIMIT - position if signal > threshold + 1.0 else min(6, self.LIMIT - position)
            return [Order(product, int(self.improve_bid(book)), int(quantity))]
        if signal < 0 and position > -self.LIMIT:
            quantity = self.LIMIT + position if signal < -threshold - 1.0 else min(6, self.LIMIT + position)
            return [Order(product, int(self.improve_ask(book)), int(-quantity))]
        return []

    def run_extra_relative(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for group_products in self.EXTRA_GROUPS.values():
            books = {product: self.book(state, product) for product in group_products}
            if any(book is None for book in books.values()):
                continue
            mids = {product: books[product]["mid"] for product in group_products}
            group_mid = sum(mids.values()) / len(mids)
            for product in group_products:
                if product not in self.EXTRA_PRODUCTS or product in result:
                    continue
                threshold, weight = self.EXTRA_PRODUCTS[product]
                residual = mids[product] - group_mid
                hist = self.push(cache, "xrel_" + product, residual, 220)
                if len(hist) < 45:
                    continue
                center_window = hist[-180:]
                center = sum(center_window) / len(center_window)
                sigma = self.std(hist[-120:], 4.0)
                z = (residual - center) / max(sigma, 1.0)
                if abs(z) >= threshold:
                    scored.append((abs(z) * weight, product, books[product], z, sigma))

        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, z, sigma in scored[:5]:
            orders = self.trade_extra_relative(product, book, state.position.get(product, 0), z, sigma)
            if orders:
                result[product] = orders

    def trade_extra_relative(self, product: str, book: dict, position: int, z: float, sigma: float) -> List[Order]:
        # Positive residual = expensive versus category basket, so sell.
        start = position
        intensity = min(1.0, max(0.0, (abs(z) - 1.05) / 2.1))
        target = int(round((-self.LIMIT if z > 0 else self.LIMIT) * intensity))
        delta = target - position
        if delta > 0:
            price = self.improve_bid(book)
            if abs(z) > 3.0 and book["ask"] - price <= max(7, 0.40 * sigma):
                price = book["ask"]
            return self.ensure_limit(product, start, [Order(product, int(price), int(delta))])
        if delta < 0:
            price = self.improve_ask(book)
            if abs(z) > 3.0 and price - book["bid"] <= max(7, 0.40 * sigma):
                price = book["bid"]
            return self.ensure_limit(product, start, [Order(product, int(price), int(delta))])
        return []

    def run_momentum_extras(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for product, (lookback, threshold, signed_weight) in self.MOMENTUM_EXTRAS.items():
            if product in result:
                continue
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, "mom_" + product, book["mid"], max(260, lookback + 140))
            if len(hist) <= lookback + 5:
                continue
            raw = (hist[-1] - hist[-1 - lookback]) / max(self.vol(hist[-140:]), 1.0)
            signal = raw if signed_weight > 0 else -raw
            if abs(signal) >= threshold:
                scored.append((abs(signal) * abs(signed_weight), product, book, signal, threshold))

        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, signal, threshold in scored[: self.MAX_MOMENTUM_EXTRAS]:
            orders = self.trade_momentum_extra(product, book, state.position.get(product, 0), signal, threshold)
            if orders:
                result[product] = orders

    def trade_momentum_extra(self, product: str, book: dict, position: int, signal: float, threshold: float) -> List[Order]:
        intensity = min(1.0, max(0.0, (abs(signal) - threshold) / 1.3))
        target = int(round((self.LIMIT if signal > 0 else -self.LIMIT) * intensity))
        delta = target - position
        if delta > 0:
            price = book["ask"] if abs(signal) > threshold + 1.3 else self.improve_bid(book)
            return self.ensure_limit(product, position, [Order(product, int(price), int(delta))])
        if delta < 0:
            price = book["bid"] if abs(signal) > threshold + 1.3 else self.improve_ask(book)
            return self.ensure_limit(product, position, [Order(product, int(price), int(delta))])
        return []

    def book(self, state: TradingState, product: str):
        depth = state.order_depths.get(product)
        if not depth or not depth.buy_orders or not depth.sell_orders:
            return None
        bid = max(depth.buy_orders)
        ask = min(depth.sell_orders)
        bid_volume = max(0, depth.buy_orders[bid])
        ask_volume = max(0, -depth.sell_orders[ask])
        total = bid_volume + ask_volume
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid, "imb": 0.0 if total == 0 else (bid_volume - ask_volume) / total}

    def improve_bid(self, book: dict) -> int:
        return min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]

    def improve_ask(self, book: dict) -> int:
        return max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]

    def fit_predict(self, xs: List[float], ys: List[float], x0: float) -> float:
        mx = sum(xs) / len(xs)
        my = sum(ys) / len(ys)
        den = sum((x - mx) ** 2 for x in xs)
        if den <= 1e-9:
            return my
        slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs))) / den
        return my + slope * (x0 - mx)

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
        return max(default, math.sqrt(sum((x - mean) ** 2 for x in values) / len(values)))

    def vol(self, hist: List[float]) -> float:
        if len(hist) < 3:
            return 1.0
        diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
        mean = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - mean) ** 2 for x in diffs) / len(diffs)))

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
