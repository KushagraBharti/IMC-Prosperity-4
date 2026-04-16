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
        "ASH_COATED_OSMIUM": 50,
        "INTARIAN_PEPPER_ROOT": 50,
    }

    # Pepper root behaved like a clean rising trend with stable anchor:
    # fair ~= anchor + timestamp / 1000, with short-horizon book pressure adding timing value.
    PEPPER_TREND_PER_TIMESTAMP = 0.001
    PEPPER_DEFAULT_ANCHOR = 13000.0
    PEPPER_FORWARD_PREMIUM = 6.0
    PEPPER_BASE_TARGET = 42
    PEPPER_TARGET_SLOPE = 8
    PEPPER_DEV_WEIGHT = 1.30
    PEPPER_IMBALANCE_WEIGHT = 3.10
    PEPPER_TREND_WEIGHT = 0.55
    PEPPER_TAKE_EDGE = 1.0
    PEPPER_STRONG_BUY_EDGE = 2.5
    PEPPER_MAKER_EDGE = 1.0
    PEPPER_BID_IMPROVE = 6
    PEPPER_ASK_IMPROVE = 1
    PEPPER_SOFT_LIMIT = 50
    PEPPER_ENDGAME = 940000
    PEPPER_ANCHOR_SMOOTHING = 0.10
    HISTORY_LIMIT = 40

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_cache(getattr(state, "traderData", ""))
        result: Dict[str, List[Order]] = {
            "ASH_COATED_OSMIUM": [],
            "INTARIAN_PEPPER_ROOT": [],
        }

        depth = state.order_depths.get("INTARIAN_PEPPER_ROOT")
        if depth is not None:
            book = self.book_snapshot(depth)
            observed_anchor = book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP
            self.update_anchor(cache, observed_anchor)
            self.push_history(cache, "pepper_wall_mid", book["wall_mid"])
            self.push_history(cache, "pepper_mid", book["mid"])
            self.push_history(cache, "pepper_imbalance", book["imbalance"])
            position = state.position.get("INTARIAN_PEPPER_ROOT", 0)
            result["INTARIAN_PEPPER_ROOT"] = self.trade_pepper(depth, position, timestamp, cache)

        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade_pepper(
        self,
        depth: OrderDepth,
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        product = "INTARIAN_PEPPER_ROOT"
        limit = self.POSITION_LIMITS[product]
        original_position = position
        book = self.book_snapshot(depth)

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
            target_position = min(target_position, 10)

        orders: List[Order] = []
        buy_orders = book["buy_orders"]
        sell_orders = book["sell_orders"]
        best_bid = book["best_bid"]
        best_ask = book["best_ask"]

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, position)

        if position >= self.PEPPER_SOFT_LIMIT:
            buy_capacity = 0

        # Long-biased taker logic: accumulate inventory when the forward-looking fair says the ask is cheap.
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
                    self.buy_size(position, target_position, available, edge, timestamp >= self.PEPPER_ENDGAME),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size
                    position += size

        # Sell only to trim longs when the bid is rich relative to trend fair.
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
                    self.sell_size(position, target_position, available, edge, timestamp >= self.PEPPER_ENDGAME),
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    sell_capacity -= size
                    position -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, position)

        # Keep a strong bid working so we can participate in pullbacks while the drift does the heavy lifting.
        if buy_capacity > 0 and position < target_position:
            bid_quote = min(best_bid + self.PEPPER_BID_IMPROVE, int(math.floor(forward_fair - self.PEPPER_MAKER_EDGE)))
            if bid_quote < best_ask:
                bid_size = min(buy_capacity, max(2, min(target_position - position, 10)))
                orders.append(Order(product, int(bid_quote), int(bid_size)))

        # Ask only when we're already long enough or late in the session.
        should_offer = position > target_position + 4 or timestamp >= self.PEPPER_ENDGAME
        if sell_capacity > 0 and should_offer:
            ask_bias = 1.5 if timestamp < self.PEPPER_ENDGAME else 0.5
            ask_quote = max(best_ask - self.PEPPER_ASK_IMPROVE, int(math.ceil(unwind_fair + ask_bias)))
            if ask_quote > best_bid:
                ask_size = min(sell_capacity, max(2, min(position - target_position if position > target_position else position, 8)))
                if ask_size > 0:
                    orders.append(Order(product, int(ask_quote), int(-ask_size)))

        return self.enforce_long_only_limit(limit, original_position, orders)

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

    def buy_size(self, position: int, target_position: int, available: int, edge: float, endgame: bool) -> int:
        size = 4
        if position < target_position:
            size += min(10, max(0, target_position - position))
        if edge >= self.PEPPER_STRONG_BUY_EDGE:
            size += 4
        if endgame:
            size = max(2, size // 2)
        return min(available, max(2, size))

    def sell_size(self, position: int, target_position: int, available: int, edge: float, endgame: bool) -> int:
        excess = max(0, position - target_position)
        size = max(2, min(available, excess + 2))
        if edge >= 3.0:
            size += 2
        if endgame:
            size = max(size, min(available, position))
        return min(available, size)

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
        if "pepper_anchor" not in cache:
            cache["pepper_anchor"] = observed_anchor
            return
        current = float(cache["pepper_anchor"])
        updated = (1.0 - self.PEPPER_ANCHOR_SMOOTHING) * current + self.PEPPER_ANCHOR_SMOOTHING * observed_anchor
        cache["pepper_anchor"] = updated

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