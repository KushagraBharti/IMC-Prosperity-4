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
    POSITION_LIMITS = {"EMERALDS": 80, "TOMATOES": 80}

    # Highest-upside aggressive variant
    EMERALDS_FAIR = 10000.0
    EMERALDS_BASE_SIZE = 16
    EMERALDS_TAKE_EDGE = 1.0
    EMERALDS_MAKER_EDGE = 1.0
    EMERALDS_QUOTE_IMPROVE = 3
    EMERALDS_SKEW = 0.12
    EMERALDS_SOFT_LIMIT = 40
    EMERALDS_FLATTEN_TRIGGER = 22
    EMERALDS_ENDGAME = 175000

    TOMATOES_BASE_SIZE = 16
    TOMATOES_TAKE_EDGE = 1.0
    TOMATOES_MAKER_EDGE = 0.0
    TOMATOES_QUOTE_IMPROVE = 2
    TOMATOES_SKEW = 0.18
    TOMATOES_SOFT_LIMIT = 34
    TOMATOES_FLATTEN_TRIGGER = 20
    TOMATOES_ENDGAME = 160000
    TOMATOES_DEVIATION_WEIGHT = 1.25
    TOMATOES_IMBALANCE_WEIGHT = 2.50
    TOMATOES_TREND_WEIGHT = 0.55
    TOMATOES_MICRO_TREND_WEIGHT = 0.35

    HISTORY_LIMIT = 28

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_data(getattr(state, "traderData", ""))
        result: Dict[str, List[Order]] = {}

        tomato_depth = state.order_depths.get("TOMATOES")
        if tomato_depth is not None:
            tomato_book = self.book_snapshot(tomato_depth)
            self.push_history(cache, "tomato_wall", tomato_book["wall_mid"])
            self.push_history(cache, "tomato_mid", tomato_book["mid"])
            self.push_history(cache, "tomato_imbalance", tomato_book["imbalance"])

        for product in ("EMERALDS", "TOMATOES"):
            depth = state.order_depths.get(product)
            if depth is None:
                result[product] = []
                continue
            position = state.position.get(product, 0)
            if product == "EMERALDS":
                orders = self.trade_emeralds(depth, position, timestamp)
            else:
                orders = self.trade_tomatoes(depth, position, timestamp, cache)
            result[product] = orders

        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade_emeralds(self, depth: OrderDepth, position: int, timestamp: int) -> List[Order]:
        book = self.book_snapshot(depth)
        fair = self.EMERALDS_FAIR
        reservation = fair - position * self.EMERALDS_SKEW
        return self.generate_orders(
            product="EMERALDS",
            book=book,
            position=position,
            fair=fair,
            reservation=reservation,
            timestamp=timestamp,
            base_size=self.EMERALDS_BASE_SIZE,
            take_edge=self.EMERALDS_TAKE_EDGE,
            maker_edge=self.EMERALDS_MAKER_EDGE,
            quote_improve=self.EMERALDS_QUOTE_IMPROVE,
            soft_limit=self.EMERALDS_SOFT_LIMIT,
            flatten_trigger=self.EMERALDS_FLATTEN_TRIGGER,
            endgame_start=self.EMERALDS_ENDGAME,
            signal=0.0,
            sweep_levels=2,
            aggressive=True,
        )

    def trade_tomatoes(self, depth: OrderDepth, position: int, timestamp: int, cache: Dict[str, List[float]]) -> List[Order]:
        book = self.book_snapshot(depth)
        wall = book["wall_mid"]
        deviation = wall - book["mid"]
        imbalance = book["imbalance"]
        trend = self.trend_signal(cache.get("tomato_wall", []), 4, 12)
        micro_trend = self.trend_signal(cache.get("tomato_wall", []), 2, 6)
        alpha = (
            deviation * self.TOMATOES_DEVIATION_WEIGHT
            + imbalance * self.TOMATOES_IMBALANCE_WEIGHT
            + trend * self.TOMATOES_TREND_WEIGHT
            + micro_trend * self.TOMATOES_MICRO_TREND_WEIGHT
        )
        alpha = self.clip(alpha, -4.0, 4.0)
        reservation = wall + alpha - position * self.TOMATOES_SKEW
        strong_dislocation = abs(deviation) >= 1.0 or abs(alpha) >= 1.5
        sweep_levels = 3 if strong_dislocation else 2

        return self.generate_orders(
            product="TOMATOES",
            book=book,
            position=position,
            fair=wall,
            reservation=reservation,
            timestamp=timestamp,
            base_size=self.TOMATOES_BASE_SIZE,
            take_edge=self.TOMATOES_TAKE_EDGE,
            maker_edge=self.TOMATOES_MAKER_EDGE,
            quote_improve=self.TOMATOES_QUOTE_IMPROVE,
            soft_limit=self.TOMATOES_SOFT_LIMIT,
            flatten_trigger=self.TOMATOES_FLATTEN_TRIGGER,
            endgame_start=self.TOMATOES_ENDGAME,
            signal=alpha,
            sweep_levels=sweep_levels,
            aggressive=strong_dislocation,
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
        aggressive: bool,
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
        bid_scale = self.clip(1.0 - 1.15 * long_pressure + 0.40 * short_pressure, 0.05, 1.60)
        ask_scale = self.clip(1.0 - 1.15 * short_pressure + 0.40 * long_pressure, 0.05, 1.60)

        if timestamp >= endgame_start:
            bid_scale *= 0.30
            ask_scale *= 0.30

        for level, (ask_price, ask_volume) in enumerate(sell_orders):
            if level >= sweep_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            edge = fair - ask_price
            flatten_buy = position < -flatten_trigger and edge >= -0.5
            if edge >= take_edge or flatten_buy:
                if signal >= -0.80 or flatten_buy or edge >= 2.0:
                    size = min(
                        buy_capacity,
                        available,
                        self.take_size(base_size, buy_capacity, bid_scale, edge, aggressive, timestamp >= endgame_start),
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
                if signal <= 0.80 or flatten_sell or edge >= 2.0:
                    size = min(
                        sell_capacity,
                        available,
                        self.take_size(base_size, sell_capacity, ask_scale, edge, aggressive, timestamp >= endgame_start),
                    )
                    if size > 0:
                        orders.append(Order(product, int(bid_price), int(-size)))
                        sell_capacity -= size

        if position > flatten_trigger and sell_capacity > 0:
            flatten_price = max(best_bid, int(math.floor(fair)))
            flatten_size = min(sell_capacity, max(6, min(position - flatten_trigger + 6, base_size + 4)))
            orders.append(Order(product, int(flatten_price), int(-flatten_size)))
        elif position < -flatten_trigger and buy_capacity > 0:
            flatten_price = min(best_ask, int(math.ceil(fair)))
            flatten_size = min(buy_capacity, max(6, min((-position) - flatten_trigger + 6, base_size + 4)))
            orders.append(Order(product, int(flatten_price), int(flatten_size)))

        bid_quote = min(best_bid + quote_improve, int(math.floor(reservation - maker_edge)))
        ask_quote = max(best_ask - quote_improve, int(math.ceil(reservation + maker_edge)))

        if signal > 1.0:
            bid_quote += 1
        elif signal < -1.0:
            ask_quote -= 1

        if product == "EMERALDS":
            bid_quote = min(bid_quote, 9999)
            ask_quote = max(ask_quote, 10001)

        if buy_capacity > 0 and bid_quote < best_ask:
            size = self.passive_size(base_size, buy_capacity, bid_scale, aggressive, timestamp >= endgame_start)
            if size > 0:
                orders.append(Order(product, int(bid_quote), int(size)))

        if sell_capacity > 0 and ask_quote > best_bid:
            size = self.passive_size(base_size, sell_capacity, ask_scale, aggressive, timestamp >= endgame_start)
            if size > 0:
                orders.append(Order(product, int(ask_quote), int(-size)))

        return self.ensure_within_limits(product, position, orders)

    def take_size(self, base_size: int, capacity: int, scale: float, edge: float, aggressive: bool, endgame: bool) -> int:
        size = int(round(base_size * scale))
        if aggressive:
            size += 3
        if edge >= 2:
            size += 3
        if edge >= 3:
            size += 3
        if endgame:
            size = max(2, size - 3)
        return min(capacity, max(2, size))

    def passive_size(self, base_size: int, capacity: int, scale: float, aggressive: bool, endgame: bool) -> int:
        size = int(round(base_size * scale))
        if aggressive:
            size += 1
        if endgame:
            size = max(2, size // 2)
        return min(capacity, max(2, size))

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

    def trend_signal(self, history: List[float], short_window: int, long_window: int) -> float:
        if len(history) < long_window:
            return 0.0
        short = self.average(history[-short_window:])
        long = self.average(history[-long_window:])
        return short - long

    def push_history(self, cache: Dict[str, List[float]], key: str, value: float) -> None:
        series = cache.setdefault(key, [])
        series.append(float(value))
        if len(series) > self.HISTORY_LIMIT:
            del series[:-self.HISTORY_LIMIT]

    def average(self, values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def load_data(self, raw: str) -> Dict[str, List[float]]:
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def ensure_within_limits(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        running = position
        filtered: List[Order] = []
        for order in orders:
            if order.quantity == 0:
                continue
            next_position = running + order.quantity
            if -limit <= next_position <= limit:
                filtered.append(order)
                running = next_position
        return filtered