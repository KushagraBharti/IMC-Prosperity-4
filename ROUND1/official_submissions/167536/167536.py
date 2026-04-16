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
    # These limits are a conservative local assumption so the strategy is safe to iterate on.
    # If you confirm official limits later, update them here.
    POSITION_LIMITS = {
        "ASH_COATED_OSMIUM": 50,
        "INTARIAN_PEPPER_ROOT": 50,
    }

    OSMIUM_FAIR = 10000.0
    OSMIUM_BASE_SIZE = 12
    OSMIUM_TAKE_EDGE = 2.0
    OSMIUM_MAKER_EDGE = 1.0
    OSMIUM_QUOTE_IMPROVE = 6
    OSMIUM_SKEW = 0.12
    OSMIUM_SOFT_LIMIT = 32
    OSMIUM_FLATTEN_TRIGGER = 20
    OSMIUM_ENDGAME = 940000
    OSMIUM_DEV_WEIGHT = 0.95
    OSMIUM_IMBALANCE_WEIGHT = 2.0
    OSMIUM_TREND_WEIGHT = 0.30

    PEPPER_TREND_PER_TIMESTAMP = 0.001
    PEPPER_INITIAL_ANCHOR = 13000.0
    PEPPER_BASE_SIZE = 14
    PEPPER_TAKE_EDGE = 1.0
    PEPPER_MAKER_EDGE = 1.0
    PEPPER_QUOTE_IMPROVE = 5
    PEPPER_SKEW = 0.16
    PEPPER_SOFT_LIMIT = 30
    PEPPER_FLATTEN_TRIGGER = 18
    PEPPER_ENDGAME = 935000
    PEPPER_DEV_WEIGHT = 1.10
    PEPPER_IMBALANCE_WEIGHT = 2.30
    PEPPER_TREND_WEIGHT = 0.45
    PEPPER_ANCHOR_SMOOTHING = 0.12

    HISTORY_LIMIT = 32

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_cache(getattr(state, "traderData", ""))
        result: Dict[str, List[Order]] = {}

        osmium_depth = state.order_depths.get("ASH_COATED_OSMIUM")
        if osmium_depth is not None:
            osmium_book = self.book_snapshot(osmium_depth)
            self.push_history(cache, "osmium_wall_mid", osmium_book["wall_mid"])

        pepper_depth = state.order_depths.get("INTARIAN_PEPPER_ROOT")
        if pepper_depth is not None:
            pepper_book = self.book_snapshot(pepper_depth)
            self.push_history(cache, "pepper_wall_mid", pepper_book["wall_mid"])
            self.push_history(cache, "pepper_mid", pepper_book["mid"])
            observed_anchor = pepper_book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP
            self.update_anchor(cache, observed_anchor)

        for product in ("ASH_COATED_OSMIUM", "INTARIAN_PEPPER_ROOT"):
            depth = state.order_depths.get(product)
            if depth is None:
                result[product] = []
                continue

            position = state.position.get(product, 0)
            if product == "ASH_COATED_OSMIUM":
                result[product] = self.trade_osmium(depth, position, timestamp, cache)
            else:
                result[product] = self.trade_pepper(depth, position, timestamp, cache)

        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade_osmium(
        self,
        depth: OrderDepth,
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        book = self.book_snapshot(depth)
        trend = self.trend_signal(cache.get("osmium_wall_mid", []), 3, 10)
        alpha = (
            (book["wall_mid"] - book["mid"]) * self.OSMIUM_DEV_WEIGHT
            + book["imbalance"] * self.OSMIUM_IMBALANCE_WEIGHT
            + trend * self.OSMIUM_TREND_WEIGHT
        )
        alpha = self.clip(alpha, -3.0, 3.0)
        fair = self.OSMIUM_FAIR + alpha
        reservation = fair - position * self.OSMIUM_SKEW

        return self.generate_orders(
            product="ASH_COATED_OSMIUM",
            book=book,
            position=position,
            fair=fair,
            reservation=reservation,
            timestamp=timestamp,
            base_size=self.OSMIUM_BASE_SIZE,
            take_edge=self.OSMIUM_TAKE_EDGE,
            maker_edge=self.OSMIUM_MAKER_EDGE,
            quote_improve=self.OSMIUM_QUOTE_IMPROVE,
            soft_limit=self.OSMIUM_SOFT_LIMIT,
            flatten_trigger=self.OSMIUM_FLATTEN_TRIGGER,
            endgame_start=self.OSMIUM_ENDGAME,
            signal=alpha,
            sweep_levels=2,
        )

    def trade_pepper(
        self,
        depth: OrderDepth,
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        book = self.book_snapshot(depth)
        anchor = float(cache.get("pepper_anchor", self.PEPPER_INITIAL_ANCHOR))
        base_fair = anchor + timestamp * self.PEPPER_TREND_PER_TIMESTAMP
        micro_trend = self.trend_signal(cache.get("pepper_wall_mid", []), 3, 9)
        alpha = (
            (book["wall_mid"] - book["mid"]) * self.PEPPER_DEV_WEIGHT
            + book["imbalance"] * self.PEPPER_IMBALANCE_WEIGHT
            + micro_trend * self.PEPPER_TREND_WEIGHT
        )
        alpha = self.clip(alpha, -4.0, 4.0)
        fair = base_fair + alpha
        reservation = fair - position * self.PEPPER_SKEW

        return self.generate_orders(
            product="INTARIAN_PEPPER_ROOT",
            book=book,
            position=position,
            fair=fair,
            reservation=reservation,
            timestamp=timestamp,
            base_size=self.PEPPER_BASE_SIZE,
            take_edge=self.PEPPER_TAKE_EDGE,
            maker_edge=self.PEPPER_MAKER_EDGE,
            quote_improve=self.PEPPER_QUOTE_IMPROVE,
            soft_limit=self.PEPPER_SOFT_LIMIT,
            flatten_trigger=self.PEPPER_FLATTEN_TRIGGER,
            endgame_start=self.PEPPER_ENDGAME,
            signal=alpha,
            sweep_levels=3 if abs(alpha) >= 1.5 else 2,
        )

    def generate_orders(
        self,
        product: str,
        book: Dict[str, object],
        position: int,
        fair: float,
        reservation: float,
        timestamp: int,
        base_size: int,
        take_edge: float,
        maker_edge: float,
        quote_improve: int,
        soft_limit: int,
        flatten_trigger: int,
        endgame_start: int,
        signal: float,
        sweep_levels: int,
    ) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        orders: List[Order] = []
        buy_orders = book["buy_orders"]
        sell_orders = book["sell_orders"]
        best_bid = book["best_bid"]
        best_ask = book["best_ask"]

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        if position >= soft_limit:
            buy_capacity = 0
        elif position <= -soft_limit:
            sell_capacity = 0

        long_pressure = max(0.0, position / soft_limit) if soft_limit else 0.0
        short_pressure = max(0.0, -position / soft_limit) if soft_limit else 0.0
        bid_scale = self.clip(1.0 - long_pressure + 0.25 * short_pressure, 0.15, 1.35)
        ask_scale = self.clip(1.0 - short_pressure + 0.25 * long_pressure, 0.15, 1.35)

        if timestamp >= endgame_start:
            bid_scale *= 0.45
            ask_scale *= 0.45

        for level, (ask_price, ask_volume) in enumerate(sell_orders):
            if level >= sweep_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            edge = fair - ask_price
            flatten_buy = position < -flatten_trigger and edge >= -0.5
            if edge >= take_edge or flatten_buy:
                size = min(
                    buy_capacity,
                    available,
                    self.take_size(base_size, buy_capacity, bid_scale, edge, timestamp >= endgame_start),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size

        for level, (bid_price, bid_volume) in enumerate(buy_orders):
            if level >= sweep_levels or sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            edge = bid_price - fair
            flatten_sell = position > flatten_trigger and edge >= -0.5
            if edge >= take_edge or flatten_sell:
                size = min(
                    sell_capacity,
                    available,
                    self.take_size(base_size, sell_capacity, ask_scale, edge, timestamp >= endgame_start),
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    sell_capacity -= size

        if position > flatten_trigger and sell_capacity > 0:
            flatten_price = max(best_bid, int(math.floor(fair)))
            flatten_size = min(sell_capacity, max(4, min(position - flatten_trigger + 4, base_size + 2)))
            orders.append(Order(product, int(flatten_price), int(-flatten_size)))
        elif position < -flatten_trigger and buy_capacity > 0:
            flatten_price = min(best_ask, int(math.ceil(fair)))
            flatten_size = min(buy_capacity, max(4, min((-position) - flatten_trigger + 4, base_size + 2)))
            orders.append(Order(product, int(flatten_price), int(flatten_size)))

        bid_quote = min(best_bid + quote_improve, int(math.floor(reservation - maker_edge)))
        ask_quote = max(best_ask - quote_improve, int(math.ceil(reservation + maker_edge)))

        if signal > 1.2:
            bid_quote += 1
            ask_quote += 1
        elif signal < -1.2:
            bid_quote -= 1
            ask_quote -= 1

        if buy_capacity > 0 and bid_quote < best_ask:
            size = self.passive_size(base_size, buy_capacity, bid_scale, timestamp >= endgame_start)
            if size > 0:
                orders.append(Order(product, int(bid_quote), int(size)))

        if sell_capacity > 0 and ask_quote > best_bid:
            size = self.passive_size(base_size, sell_capacity, ask_scale, timestamp >= endgame_start)
            if size > 0:
                orders.append(Order(product, int(ask_quote), int(-size)))

        return self.ensure_within_limits(product, position, orders)

    def book_snapshot(self, depth: OrderDepth) -> Dict[str, object]:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        best_bid = buy_orders[0][0] if buy_orders else 0
        best_ask = sell_orders[0][0] if sell_orders else 0
        mid = self.compute_mid(buy_orders, sell_orders)
        wall_mid = self.compute_wall_mid(buy_orders, sell_orders)
        imbalance = self.top_imbalance(buy_orders, sell_orders)
        return {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid": mid,
            "wall_mid": wall_mid,
            "imbalance": imbalance,
        }

    def compute_mid(self, buy_orders: List[tuple], sell_orders: List[tuple]) -> float:
        if buy_orders and sell_orders:
            return (buy_orders[0][0] + sell_orders[0][0]) / 2
        if buy_orders:
            return float(buy_orders[0][0])
        if sell_orders:
            return float(sell_orders[0][0])
        return 0.0

    def compute_wall_mid(self, buy_orders: List[tuple], sell_orders: List[tuple]) -> float:
        if not buy_orders or not sell_orders:
            return self.compute_mid(buy_orders, sell_orders)
        wall_bid = max(buy_orders, key=lambda item: (item[1], item[0]))[0]
        wall_ask = min(sell_orders, key=lambda item: (-abs(item[1]), item[0]))[0]
        return (wall_bid + wall_ask) / 2

    def top_imbalance(self, buy_orders: List[tuple], sell_orders: List[tuple]) -> float:
        if not buy_orders or not sell_orders:
            return 0.0
        bid_volume = max(0, buy_orders[0][1])
        ask_volume = max(0, -sell_orders[0][1])
        total = bid_volume + ask_volume
        if total == 0:
            return 0.0
        return (bid_volume - ask_volume) / total

    def take_size(self, base_size: int, capacity: int, scale: float, edge: float, endgame: bool) -> int:
        size = int(round(base_size * scale))
        if edge >= 2.0:
            size += 2
        if edge >= 3.0:
            size += 2
        if endgame:
            size = max(2, size - 2)
        return min(capacity, max(2, size))

    def passive_size(self, base_size: int, capacity: int, scale: float, endgame: bool) -> int:
        size = int(round(base_size * scale))
        if endgame:
            size = max(2, size // 2)
        return min(capacity, max(2, size))

    def trend_signal(self, history: List[float], short_window: int, long_window: int) -> float:
        if len(history) < long_window:
            return 0.0
        short_avg = sum(history[-short_window:]) / short_window
        long_avg = sum(history[-long_window:]) / long_window
        return short_avg - long_avg

    def load_cache(self, raw: str) -> Dict[str, object]:
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def push_history(self, cache: Dict[str, object], key: str, value: float) -> None:
        history = cache.get(key)
        if not isinstance(history, list):
            history = []
            cache[key] = history
        history.append(float(value))
        if len(history) > self.HISTORY_LIMIT:
            del history[:-self.HISTORY_LIMIT]

    def update_anchor(self, cache: Dict[str, object], observed_anchor: float) -> None:
        current = float(cache.get("pepper_anchor", self.PEPPER_INITIAL_ANCHOR))
        updated = (1.0 - self.PEPPER_ANCHOR_SMOOTHING) * current + self.PEPPER_ANCHOR_SMOOTHING * observed_anchor
        cache["pepper_anchor"] = updated

    def ensure_within_limits(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        running = position
        filtered: List[Order] = []
        for order in orders:
            next_position = running + order.quantity
            if -limit <= next_position <= limit:
                filtered.append(order)
                running = next_position
        return filtered

    def clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))