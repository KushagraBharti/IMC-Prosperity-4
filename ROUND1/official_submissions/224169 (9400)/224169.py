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

    OSMIUM_FAIR = 10000.0
    OSMIUM_BASE_SIZE = 20
    OSMIUM_TAKE_EDGE = 1.0
    OSMIUM_DEV_WEIGHT = 1.10
    OSMIUM_IMBALANCE_WEIGHT = 2.40
    OSMIUM_TREND_WEIGHT = 0.20
    OSMIUM_SKEW = 0.10
    OSMIUM_SOFT_LIMIT = 80
    OSMIUM_FLATTEN_TRIGGER = 40
    OSMIUM_QUOTE_IMPROVE = 1
    OSMIUM_ENDGAME = 970000

    PEPPER_TREND_PER_TIMESTAMP = 0.001
    PEPPER_DEFAULT_ANCHOR = 13000.0
    PEPPER_FORWARD_PREMIUM = 6.0
    PEPPER_BASE_TARGET = 68
    PEPPER_TARGET_SLOPE = 8
    PEPPER_DEV_WEIGHT = 1.30
    PEPPER_IMBALANCE_WEIGHT = 3.10
    PEPPER_TREND_WEIGHT = 0.55
    PEPPER_TAKE_EDGE = 1.0
    PEPPER_STRONG_BUY_EDGE = 2.5
    PEPPER_MAKER_EDGE = 1.0
    PEPPER_BID_IMPROVE = 7
    PEPPER_ASK_IMPROVE = 0
    PEPPER_SOFT_LIMIT = 80
    PEPPER_ENDGAME = 950000
    PEPPER_ANCHOR_SMOOTHING = 0.10

    HISTORY_LIMIT = 40

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_cache(getattr(state, "traderData", ""))
        result: Dict[str, List[Order]] = {
            "ASH_COATED_OSMIUM": [],
            "INTARIAN_PEPPER_ROOT": [],
        }

        osmium_depth = state.order_depths.get("ASH_COATED_OSMIUM")
        if osmium_depth is not None:
            osmium_book = self.book_snapshot(osmium_depth)
            self.push_history(cache, "osmium_wall_mid", osmium_book["wall_mid"])
            self.push_history(cache, "osmium_imbalance", osmium_book["imbalance"])
            osmium_position = state.position.get("ASH_COATED_OSMIUM", 0)
            result["ASH_COATED_OSMIUM"] = self.trade_osmium(osmium_book, osmium_position, timestamp, cache)

        pepper_depth = state.order_depths.get("INTARIAN_PEPPER_ROOT")
        if pepper_depth is not None:
            pepper_book = self.book_snapshot(pepper_depth)
            observed_anchor = pepper_book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP
            self.update_anchor(cache, observed_anchor)
            self.push_history(cache, "pepper_wall_mid", pepper_book["wall_mid"])
            self.push_history(cache, "pepper_mid", pepper_book["mid"])
            self.push_history(cache, "pepper_imbalance", pepper_book["imbalance"])
            pepper_position = state.position.get("INTARIAN_PEPPER_ROOT", 0)
            result["INTARIAN_PEPPER_ROOT"] = self.trade_pepper(pepper_book, pepper_position, timestamp, cache)

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
                size = min(buy_capacity, available, self.osmium_take_size(edge, position, timestamp))
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
                size = min(sell_capacity, available, self.osmium_take_size(edge, position, timestamp))
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
            size = min(buy_capacity, self.osmium_passive_size(position, timestamp, alpha, True))
            if size > 0:
                orders.append(Order(product, int(bid_quote), int(size)))

        if sell_capacity > 0 and ask_quote > best_bid:
            size = min(sell_capacity, self.osmium_passive_size(position, timestamp, alpha, False))
            if size > 0:
                orders.append(Order(product, int(ask_quote), int(-size)))

        return self.ensure_within_limits(product, position, orders)

    def trade_pepper(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        product = "INTARIAN_PEPPER_ROOT"
        limit = self.POSITION_LIMITS[product]
        original_position = position

        anchor = float(cache.get("pepper_anchor", self.PEPPER_DEFAULT_ANCHOR))
        base_fair = anchor + timestamp * self.PEPPER_TREND_PER_TIMESTAMP
        micro_trend = self.trend_signal(cache.get("pepper_wall_mid", []), 3, 9)
        imbalance_trend = self.trend_signal(cache.get("pepper_imbalance", []), 3, 9)
        deviation = book["wall_mid"] - book["mid"]

        alpha = (
            deviation * self.PEPPER_DEV_WEIGHT
            + book["imbalance"] * self.PEPPER_IMBALANCE_WEIGHT
            + micro_trend * self.PEPPER_TREND_WEIGHT
            + imbalance_trend * 0.50
        )
        alpha = self.clip(alpha, -4.5, 4.5)

        forward_fair = base_fair + self.PEPPER_FORWARD_PREMIUM + alpha
        unwind_fair = base_fair + alpha

        raw_target = self.PEPPER_BASE_TARGET + int(round(self.clip(alpha, -2.5, 2.5) * self.PEPPER_TARGET_SLOPE))
        target_position = int(self.clip(raw_target, 0, limit))

        if timestamp >= self.PEPPER_ENDGAME:
            target_position = min(target_position, 12)

        orders: List[Order] = []
        buy_orders = book["buy_orders"]
        sell_orders = book["sell_orders"]
        best_bid = book["best_bid"]
        best_ask = book["best_ask"]

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, position)

        if position >= self.PEPPER_SOFT_LIMIT:
            buy_capacity = 0

        for level, (ask_price, ask_volume) in enumerate(sell_orders):
            if level >= 3 or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            edge = forward_fair - ask_price
            need_inventory = position < target_position
            if edge >= self.PEPPER_TAKE_EDGE or (need_inventory and edge >= 0):
                size = min(
                    buy_capacity,
                    available,
                    self.pepper_buy_size(position, target_position, available, edge, timestamp >= self.PEPPER_ENDGAME),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size
                    position += size

        for level, (bid_price, bid_volume) in enumerate(buy_orders):
            if level >= 2 or sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            edge = bid_price - unwind_fair
            over_target = position > target_position
            if edge >= 2.0 or (over_target and edge >= 0):
                size = min(
                    sell_capacity,
                    available,
                    self.pepper_sell_size(position, target_position, available, edge, timestamp >= self.PEPPER_ENDGAME),
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    sell_capacity -= size
                    position -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, position)

        if buy_capacity > 0 and position < target_position:
            bid_quote = min(best_bid + self.PEPPER_BID_IMPROVE, int(math.floor(forward_fair - self.PEPPER_MAKER_EDGE)))
            if bid_quote < best_ask:
                bid_size = min(buy_capacity, max(2, min(target_position - position, 10)))
                orders.append(Order(product, int(bid_quote), int(bid_size)))

        should_offer = position > target_position + 4 or timestamp >= self.PEPPER_ENDGAME
        if sell_capacity > 0 and should_offer:
            ask_bias = 1.5 if timestamp < self.PEPPER_ENDGAME else 0.5
            ask_quote = max(best_ask - self.PEPPER_ASK_IMPROVE, int(math.ceil(unwind_fair + ask_bias)))
            if ask_quote > best_bid:
                ask_size = min(sell_capacity, max(2, min(position - target_position if position > target_position else position, 8)))
                if ask_size > 0:
                    orders.append(Order(product, int(ask_quote), int(-ask_size)))

        return self.enforce_long_only_limit(limit, original_position, orders)

    def osmium_take_size(self, edge: float, position: int, timestamp: int) -> int:
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

    def osmium_passive_size(self, position: int, timestamp: int, alpha: float, is_bid: bool) -> int:
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

    def pepper_buy_size(self, position: int, target_position: int, available: int, edge: float, endgame: bool) -> int:
        size = 4
        if position < target_position:
            size += min(10, max(0, target_position - position))
        if edge >= self.PEPPER_STRONG_BUY_EDGE:
            size += 4
        if endgame:
            size = max(2, size // 2)
        return min(available, max(2, size))

    def pepper_sell_size(self, position: int, target_position: int, available: int, edge: float, endgame: bool) -> int:
        excess = max(0, position - target_position)
        size = max(2, min(available, excess + 2))
        if edge >= 3.0:
            size += 2
        if endgame:
            size = max(size, min(available, position))
        return min(available, size)

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

    def update_anchor(self, cache: Dict[str, object], observed_anchor: float) -> None:
        if "pepper_anchor" not in cache:
            cache["pepper_anchor"] = observed_anchor
            return
        current = float(cache["pepper_anchor"])
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

    def enforce_long_only_limit(self, limit: int, position: int, orders: List[Order]) -> List[Order]:
        running = position
        filtered: List[Order] = []
        for order in orders:
            next_position = running + order.quantity
            if 0 <= next_position <= limit:
                filtered.append(order)
                running = next_position
        return filtered

    def clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))