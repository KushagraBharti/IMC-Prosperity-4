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


class Trader:
    LIMIT = 10
    ANCHOR = 10_000
    CACHE_SCALE = 10
    MAX_CACHE_CHARS = 45_000

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
        "SLEEP_POD_COTTON": ("momentum", 220, 0.60, 0.95),
        "TRANSLATOR_GRAPHITE_MIST": ("momentum", 220, 0.60, 0.90),
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
    MOMENTUM_EXTRAS = {
        "TRANSLATOR_SPACE_GRAY": (220, 0.70, 0.80),
        "GALAXY_SOUNDS_PLANETARY_RINGS": (220, 2.00, 0.75),
        "UV_VISOR_AMBER": (150, 0.75, 0.70),
        "ROBOT_LAUNDRY": (100, 1.25, 0.65),
        "ROBOT_DISHES": (150, 0.75, 0.65),
        "PANEL_4X4": (220, 0.75, 0.60),
        "MICROCHIP_TRIANGLE": (150, 0.95, -0.60),
        "PANEL_2X4": (150, 1.60, 0.55),
        "SLEEP_POD_LAMB_WOOL": (220, 2.00, 0.50),
        "MICROCHIP_RECTANGLE": (220, 2.00, 0.45),
        "PEBBLES_XS": (220, 1.20, 0.45),
        "PANEL_1X4": (220, 0.60, 0.40),
        "PANEL_2X2": (150, 0.80, 0.35),
        "OXYGEN_SHAKE_GARLIC": (150, 0.60, 0.45),
        "UV_VISOR_MAGENTA": (150, 2.00, 0.35),
        "SNACKPACK_CHOCOLATE": (150, 1.00, 0.45),
        "SNACKPACK_VANILLA": (150, 2.00, 0.35),
    }
    MAX_MOMENTUM_EXTRAS = 9

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}

        self.run_anchor(state, result)
        self.run_pebbles(state, cache, result)
        self.run_signals(state, cache, result)
        self.run_extra_relative(state, cache, result)
        self.run_momentum_extras(state, cache, result)

        return result, 0, self.serialize_cache(cache)

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
            hist = self.push(cache, "h_" + product, book["mid"], max(70, lookback + 8))
            if len(hist) <= lookback + 2:
                continue
            signal = (hist[-1] - hist[-1 - lookback]) / max(self.vol(hist[-80:]), 1.0)
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
                hist = self.push(cache, "xrel_" + product, residual, 180)
                if len(hist) < 45:
                    continue
                center_window = hist[-150:]
                center = sum(center_window) / len(center_window)
                sigma = self.std(hist[-100:], 4.0)
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
            hist = self.push(cache, "mom_" + product, book["mid"], max(80, lookback + 8))
            if len(hist) <= lookback + 5:
                continue
            raw = (hist[-1] - hist[-1 - lookback]) / max(self.vol(hist[-80:]), 1.0)
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
        hist = self.decode_series(cache.get(key, []))
        hist.append(float(value))
        hist = hist[-keep:]
        cache[key] = [int(round(x * self.CACHE_SCALE)) for x in hist]
        return hist

    def decode_series(self, raw) -> List[float]:
        if not isinstance(raw, list):
            return []
        if not raw:
            return []
        if isinstance(raw[0], int):
            return [x / self.CACHE_SCALE for x in raw]
        return [float(x) for x in raw]

    def serialize_cache(self, cache: dict) -> str:
        raw = json.dumps(cache, separators=(",", ":"))
        if len(raw) <= self.MAX_CACHE_CHARS:
            return raw

        # Safety valve for IMC's traderData cap: trim the least recent samples
        # from the largest histories rather than risking a full state reset.
        compact = dict(cache)
        while len(raw) > self.MAX_CACHE_CHARS:
            candidates = [
                (len(values), key)
                for key, values in compact.items()
                if isinstance(values, list) and len(values) > 80
            ]
            if not candidates:
                break
            length, key = max(candidates)
            compact[key] = compact[key][-max(80, int(length * 0.8)) :]
            raw = json.dumps(compact, separators=(",", ":"))
        return raw

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

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}