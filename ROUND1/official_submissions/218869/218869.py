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
    POSITION_LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80,
    }

    # Osmium looks like a stationary market around 10_000 with strong short-horizon
    # order-book pressure. This version is a best-price market maker with small alpha bias.
    OSMIUM_FAIR = 10000.0
    OSMIUM_BASE_SIZE = 14
    OSMIUM_TAKE_EDGE = 1.0
    OSMIUM_DEV_WEIGHT = 1.10
    OSMIUM_IMBALANCE_WEIGHT = 2.40
    OSMIUM_TREND_WEIGHT = 0.20
    OSMIUM_SKEW = 0.10
    OSMIUM_SOFT_LIMIT = 58
    OSMIUM_FLATTEN_TRIGGER = 34
    OSMIUM_QUOTE_IMPROVE = 1
    OSMIUM_ENDGAME = 970000
    HISTORY_LIMIT = 24

    def run(self, state: TradingState):
        cache = self.load_cache(getattr(state, "traderData", ""))
        result: Dict[str, List[Order]] = {
            "ASH_COATED_OSMIUM": [],
            "INTARIAN_PEPPER_ROOT": [],
        }

        depth = state.order_depths.get("ASH_COATED_OSMIUM")
        if depth is not None:
            book = self.book_snapshot(depth)
            self.push_history(cache, "osmium_wall_mid", book["wall_mid"])
            self.push_history(cache, "osmium_imbalance", book["imbalance"])
            position = state.position.get("ASH_COATED_OSMIUM", 0)
            timestamp = getattr(state, "timestamp", 0)
            result["ASH_COATED_OSMIUM"] = self.trade_osmium(book, position, timestamp, cache)

        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade_osmium(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        product = "ASH_COATED_OSMIUM"
        limit = self.POSITION_LIMITS[product]
        orders: List[Order] = []

        trend = self.trend_signal(cache.get("osmium_wall_mid", []), 3, 10)
        imbalance_trend = self.trend_signal(cache.get("osmium_imbalance", []), 3, 10)
        alpha = (
            (book["wall_mid"] - book["mid"]) * self.OSMIUM_DEV_WEIGHT
            + book["imbalance"] * self.OSMIUM_IMBALANCE_WEIGHT
            + trend * self.OSMIUM_TREND_WEIGHT
            + imbalance_trend * 0.40
        )
        alpha = self.clip(alpha, -4.0, 4.0)
        fair = self.OSMIUM_FAIR + alpha
        reservation = fair - position * self.OSMIUM_SKEW
        target_position = int(self.clip(round(alpha * 5), -20, 20))

        buy_orders = book["buy_orders"]
        sell_orders = book["sell_orders"]
        best_bid = book["best_bid"]
        best_ask = book["best_ask"]
        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        if position >= self.OSMIUM_SOFT_LIMIT:
            buy_capacity = 0
        elif position <= -self.OSMIUM_SOFT_LIMIT:
            sell_capacity = 0

        sweep_levels = 3 if abs(alpha) >= 1.4 else 2

        for level, (ask_price, ask_volume) in enumerate(sell_orders):
            if level >= sweep_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            edge = fair - ask_price
            if edge >= self.OSMIUM_TAKE_EDGE or (position < target_position and edge >= 0):
                size = min(buy_capacity, available, self.take_size(edge, position, timestamp))
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size
                    position += size

        for level, (bid_price, bid_volume) in enumerate(buy_orders):
            if level >= sweep_levels or sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            edge = bid_price - fair
            if edge >= self.OSMIUM_TAKE_EDGE or (position > target_position and edge >= 0):
                size = min(sell_capacity, available, self.take_size(edge, position, timestamp))
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    sell_capacity -= size
                    position -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        if position > self.OSMIUM_FLATTEN_TRIGGER and sell_capacity > 0:
            flatten_size = min(sell_capacity, max(6, min(position - self.OSMIUM_FLATTEN_TRIGGER + 4, self.OSMIUM_BASE_SIZE + 4)))
            orders.append(Order(product, max(best_bid, int(math.floor(fair))), int(-flatten_size)))
        elif position < -self.OSMIUM_FLATTEN_TRIGGER and buy_capacity > 0:
            flatten_size = min(buy_capacity, max(6, min((-position) - self.OSMIUM_FLATTEN_TRIGGER + 4, self.OSMIUM_BASE_SIZE + 4)))
            orders.append(Order(product, min(best_ask, int(math.ceil(fair))), int(flatten_size)))

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        bid_quote = min(best_bid + self.OSMIUM_QUOTE_IMPROVE, int(math.floor(reservation - 1)))
        ask_quote = max(best_ask - self.OSMIUM_QUOTE_IMPROVE, int(math.ceil(reservation + 1)))

        if alpha > 1.0:
            bid_quote += 1
        elif alpha < -1.0:
            ask_quote -= 1

        if buy_capacity > 0 and bid_quote < best_ask:
            size = min(buy_capacity, self.passive_size(position, timestamp, alpha, True))
            if size > 0:
                orders.append(Order(product, int(bid_quote), int(size)))

        if sell_capacity > 0 and ask_quote > best_bid:
            size = min(sell_capacity, self.passive_size(position, timestamp, alpha, False))
            if size > 0:
                orders.append(Order(product, int(ask_quote), int(-size)))

        return self.ensure_within_limits(product, position, orders)

    def take_size(self, edge: float, position: int, timestamp: int) -> int:
        size = self.OSMIUM_BASE_SIZE
        if edge >= 2:
            size += 2
        if edge >= 3:
            size += 2
        if abs(position) > self.POSITION_LIMITS["ASH_COATED_OSMIUM"] * 0.6:
            size = max(4, size - 4)
        if timestamp >= self.OSMIUM_ENDGAME:
            size = max(3, size - 3)
        return size

    def passive_size(self, position: int, timestamp: int, alpha: float, is_bid: bool) -> int:
        size = self.OSMIUM_BASE_SIZE
        limit = self.POSITION_LIMITS["ASH_COATED_OSMIUM"]
        if abs(position) > limit * 0.7:
            size = max(4, self.OSMIUM_BASE_SIZE // 2)
        elif abs(position) > limit * 0.5:
            size = max(5, (self.OSMIUM_BASE_SIZE * 2) // 3)
        if is_bid and alpha > 1.2:
            size += 2
        if (not is_bid) and alpha < -1.2:
            size += 2
        if timestamp >= self.OSMIUM_ENDGAME:
            size = max(3, size // 2)
        return size

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
        history.append(float(value))
        cache[key] = history[-self.HISTORY_LIMIT :]

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