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
    OSMIUM_BASE_SIZE = 24
    OSMIUM_TAKE_THRESHOLD = 1.0
    OSMIUM_MAKER_EDGE = 1.0
    OSMIUM_SKEW = 0.11
    OSMIUM_SOFT_LIMIT = 72
    OSMIUM_FLATTEN_TRIGGER = 76
    OSMIUM_ALPHA_WALL = 0.95
    OSMIUM_ALPHA_IMB = 2.85
    OSMIUM_ALPHA_TREND = 0.35
    OSMIUM_ALPHA_IMB_TREND = 0.45
    OSMIUM_ALPHA_MID_TREND = 0.20
    OSMIUM_TARGET_SLOPE = 7.0

    PEPPER_TREND_PER_TIMESTAMP = 0.001
    PEPPER_INITIAL_ANCHOR = 13000.0
    PEPPER_ANCHOR_SMOOTHING = 0.10
    PEPPER_FORWARD_PREMIUM = 8.5
    PEPPER_BASE_TARGET = 62
    PEPPER_TARGET_SLOPE = 10.5
    PEPPER_MIN_TARGET = 36
    PEPPER_MAX_TARGET = 80
    PEPPER_TAKE_THRESHOLD = 0.25
    PEPPER_STRONG_BUY_EDGE = 1.5
    PEPPER_HARD_EXIT_EDGE = 4.0
    PEPPER_MAKER_EDGE = 1.0
    PEPPER_BID_IMPROVE = 5
    PEPPER_ASK_IMPROVE = 1
    PEPPER_SOFT_LIMIT = 76
    PEPPER_ALPHA_WALL = 1.15
    PEPPER_ALPHA_IMB = 3.30
    PEPPER_ALPHA_WALL_TREND = 0.65
    PEPPER_ALPHA_IMB_TREND = 0.70
    PEPPER_ALPHA_MID_TREND = 0.20
    PEPPER_CARRY_BIAS = 0.45
    PEPPER_LATE_TARGET_CAP = 56
    PEPPER_LATE_START = 985000

    HISTORY_LIMIT = 64

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_cache(getattr(state, "traderData", ""))
        orders: Dict[str, List[Order]] = {
            "ASH_COATED_OSMIUM": [],
            "INTARIAN_PEPPER_ROOT": [],
        }

        osmium_depth = state.order_depths.get("ASH_COATED_OSMIUM")
        if osmium_depth is not None:
            osmium_book = self.book_snapshot(osmium_depth)
            self.push_history(cache, "osmium:mid", osmium_book["mid"])
            self.push_history(cache, "osmium:wall_mid", osmium_book["wall_mid"])
            self.push_history(cache, "osmium:imbalance", osmium_book["imbalance"])
            osmium_position = state.position.get("ASH_COATED_OSMIUM", 0)
            orders["ASH_COATED_OSMIUM"] = self.trade_osmium(osmium_book, osmium_position, timestamp, cache)

        pepper_depth = state.order_depths.get("INTARIAN_PEPPER_ROOT")
        if pepper_depth is not None:
            pepper_book = self.book_snapshot(pepper_depth)
            observed_anchor = pepper_book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP
            self.update_anchor(cache, observed_anchor)
            self.push_history(cache, "pepper:mid", pepper_book["mid"])
            self.push_history(cache, "pepper:wall_mid", pepper_book["wall_mid"])
            self.push_history(cache, "pepper:imbalance", pepper_book["imbalance"])
            pepper_position = state.position.get("INTARIAN_PEPPER_ROOT", 0)
            orders["INTARIAN_PEPPER_ROOT"] = self.trade_pepper(pepper_book, pepper_position, timestamp, cache)

        return orders, 0, json.dumps(cache, separators=(",", ":"))

    def trade_osmium(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        wall_trend = self.trend_signal(cache.get("osmium:wall_mid", []), 4, 16)
        imbalance_trend = self.trend_signal(cache.get("osmium:imbalance", []), 4, 16)
        mid_trend = self.trend_signal(cache.get("osmium:mid", []), 3, 10)
        alpha = (
            self.OSMIUM_ALPHA_WALL * (book["wall_mid"] - book["mid"])
            + self.OSMIUM_ALPHA_IMB * book["imbalance"]
            + self.OSMIUM_ALPHA_TREND * wall_trend
            + self.OSMIUM_ALPHA_IMB_TREND * imbalance_trend
            + self.OSMIUM_ALPHA_MID_TREND * mid_trend
        )
        alpha = self.clip(alpha, -4.5, 4.5)
        fair = self.OSMIUM_FAIR + alpha
        target_position = int(self.clip(round(alpha * self.OSMIUM_TARGET_SLOPE), -30, 30))
        reservation = fair - (position - target_position) * self.OSMIUM_SKEW
        return self.aggressive_osmium(
            book=book,
            position=position,
            timestamp=timestamp,
            fair=fair,
            reservation=reservation,
            target_position=target_position,
            alpha=alpha,
        )

    def trade_pepper(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        anchor = float(cache.get("pepper_anchor", self.PEPPER_INITIAL_ANCHOR))
        base_fair = anchor + timestamp * self.PEPPER_TREND_PER_TIMESTAMP
        wall_trend = self.trend_signal(cache.get("pepper:wall_mid", []), 4, 16)
        imbalance_trend = self.trend_signal(cache.get("pepper:imbalance", []), 4, 16)
        mid_trend = self.trend_signal(cache.get("pepper:mid", []), 5, 20)
        alpha = (
            self.PEPPER_ALPHA_WALL * (book["wall_mid"] - book["mid"])
            + self.PEPPER_ALPHA_IMB * book["imbalance"]
            + self.PEPPER_ALPHA_WALL_TREND * wall_trend
            + self.PEPPER_ALPHA_IMB_TREND * imbalance_trend
            + self.PEPPER_ALPHA_MID_TREND * mid_trend
            + self.PEPPER_CARRY_BIAS
        )
        alpha = self.clip(alpha, -5.5, 5.5)

        forward_fair = base_fair + self.PEPPER_FORWARD_PREMIUM + alpha
        unwind_fair = base_fair + alpha

        raw_target = (
            self.PEPPER_BASE_TARGET
            + int(round(self.clip(alpha, -3.0, 3.0) * self.PEPPER_TARGET_SLOPE))
            + int(round(max(0.0, book["imbalance"]) * 7.0))
        )
        target_position = int(self.clip(raw_target, self.PEPPER_MIN_TARGET, self.PEPPER_MAX_TARGET))
        if timestamp >= self.PEPPER_LATE_START:
            target_position = max(self.PEPPER_MIN_TARGET, min(target_position, self.PEPPER_LATE_TARGET_CAP))

        return self.aggressive_pepper(
            book=book,
            position=position,
            timestamp=timestamp,
            forward_fair=forward_fair,
            unwind_fair=unwind_fair,
            target_position=target_position,
            alpha=alpha,
        )

    def aggressive_osmium(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        fair: float,
        reservation: float,
        target_position: int,
        alpha: float,
    ) -> List[Order]:
        product = "ASH_COATED_OSMIUM"
        limit = self.POSITION_LIMITS[product]
        original_position = position
        orders: List[Order] = []

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        if position >= self.OSMIUM_SOFT_LIMIT:
            buy_capacity = 0
        if position <= -self.OSMIUM_SOFT_LIMIT:
            sell_capacity = 0

        sweep_levels = 4 if abs(alpha) >= 2.0 else 3 if abs(alpha) >= 1.1 else 2
        buy_align = max(0, target_position - position)
        sell_align = max(0, position - target_position)

        for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
            if level >= sweep_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            if available <= 0:
                continue
            edge = fair - ask_price
            if edge >= self.OSMIUM_TAKE_THRESHOLD or (buy_align > 0 and edge >= 0.0):
                size = min(
                    available,
                    buy_capacity,
                    self.osmium_take_size(edge=edge, position=position, target_position=target_position, timestamp=timestamp),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size
                    position += size

        for level, (bid_price, bid_volume) in enumerate(book["buy_orders"]):
            if level >= sweep_levels or sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            if available <= 0:
                continue
            edge = bid_price - fair
            if edge >= self.OSMIUM_TAKE_THRESHOLD or (sell_align > 0 and edge >= 0.0):
                size = min(
                    available,
                    sell_capacity,
                    self.osmium_take_size(edge=edge, position=position, target_position=target_position, timestamp=timestamp),
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    sell_capacity -= size
                    position -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        if position > self.OSMIUM_FLATTEN_TRIGGER and sell_capacity > 0:
            flatten_size = min(sell_capacity, max(6, min(position - self.OSMIUM_FLATTEN_TRIGGER + 6, self.OSMIUM_BASE_SIZE + 6)))
            orders.append(Order(product, max(book["best_bid"], int(math.floor(fair))), int(-flatten_size)))
        elif position < -self.OSMIUM_FLATTEN_TRIGGER and buy_capacity > 0:
            flatten_size = min(buy_capacity, max(6, min((-position) - self.OSMIUM_FLATTEN_TRIGGER + 6, self.OSMIUM_BASE_SIZE + 6)))
            orders.append(Order(product, min(book["best_ask"], int(math.ceil(fair))), int(flatten_size)))

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        primary_bid = min(book["best_bid"] + 1, int(math.floor(reservation - self.OSMIUM_MAKER_EDGE)))
        primary_ask = max(book["best_ask"] - 1, int(math.ceil(reservation + self.OSMIUM_MAKER_EDGE)))
        primary_bid = min(primary_bid, book["best_ask"] - 1)
        primary_ask = max(primary_ask, book["best_bid"] + 1)

        if alpha >= 1.6:
            primary_bid = min(book["best_ask"] - 1, primary_bid + 1)
        elif alpha <= -1.6:
            primary_ask = max(book["best_bid"] + 1, primary_ask - 1)

        if buy_capacity > 0 and primary_bid < book["best_ask"]:
            primary_size = min(buy_capacity, self.osmium_passive_size(position, target_position, alpha, True, layer=0))
            if primary_size > 0:
                orders.append(Order(product, int(primary_bid), int(primary_size)))
                buy_capacity -= primary_size

        if buy_capacity > 0:
            second_bid = min(primary_bid - 1, book["best_ask"] - 2)
            if second_bid > 0 and second_bid > book["best_bid"] - 3:
                second_size = min(buy_capacity, self.osmium_passive_size(position, target_position, alpha, True, layer=1))
                if second_size > 0:
                    orders.append(Order(product, int(second_bid), int(second_size)))
                    buy_capacity -= second_size

        if sell_capacity > 0 and primary_ask > book["best_bid"]:
            primary_size = min(sell_capacity, self.osmium_passive_size(position, target_position, alpha, False, layer=0))
            if primary_size > 0:
                orders.append(Order(product, int(primary_ask), int(-primary_size)))
                sell_capacity -= primary_size

        if sell_capacity > 0:
            second_ask = max(primary_ask + 1, book["best_bid"] + 2)
            second_size = min(sell_capacity, self.osmium_passive_size(position, target_position, alpha, False, layer=1))
            if second_ask > book["best_bid"] and second_size > 0:
                orders.append(Order(product, int(second_ask), int(-second_size)))

        return self.ensure_within_limits(product, original_position, orders)

    def aggressive_pepper(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        forward_fair: float,
        unwind_fair: float,
        target_position: int,
        alpha: float,
    ) -> List[Order]:
        product = "INTARIAN_PEPPER_ROOT"
        limit = self.POSITION_LIMITS[product]
        original_position = position
        orders: List[Order] = []

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, position)

        if position >= self.PEPPER_SOFT_LIMIT and alpha < 0.0:
            buy_capacity = 0

        gap_to_target = max(0, target_position - position)
        sweep_levels = 5 if gap_to_target >= 16 or alpha >= 1.5 else 4 if gap_to_target >= 8 else 3

        for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
            if level >= sweep_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            if available <= 0:
                continue
            edge = forward_fair - ask_price
            need_inventory = position < target_position
            catch_up_threshold = -0.65 if gap_to_target >= 16 else -0.35
            if edge >= self.PEPPER_TAKE_THRESHOLD or (need_inventory and edge >= catch_up_threshold) or (alpha >= 1.8 and edge >= -0.45):
                size = min(
                    buy_capacity,
                    available,
                    self.pepper_buy_size(position=position, target_position=target_position, edge=edge, endgame=timestamp >= self.PEPPER_LATE_START),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size
                    position += size

        for level, (bid_price, bid_volume) in enumerate(book["buy_orders"]):
            if level >= 2 or sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            if available <= 0:
                continue
            edge = bid_price - unwind_fair
            over_target = position > target_position + 12
            if edge >= self.PEPPER_HARD_EXIT_EDGE or (over_target and edge >= 0.75):
                size = min(
                    sell_capacity,
                    available,
                    self.pepper_sell_size(position=position, target_position=target_position, edge=edge, endgame=timestamp >= self.PEPPER_LATE_START),
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    sell_capacity -= size
                    position -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, position)

        if buy_capacity > 0 and position < target_position:
            bid_quote = min(book["best_bid"] + self.PEPPER_BID_IMPROVE, int(math.floor(forward_fair - self.PEPPER_MAKER_EDGE)))
            bid_quote = min(bid_quote, book["best_ask"] - 1)
            if bid_quote < book["best_ask"]:
                primary_size = min(buy_capacity, max(8, min(target_position - position, 18)))
                orders.append(Order(product, int(bid_quote), int(primary_size)))
                buy_capacity -= primary_size

            if buy_capacity > 0 and target_position - position > 12:
                second_bid = min(bid_quote - 2, book["best_ask"] - 2)
                if second_bid > 0:
                    second_size = min(buy_capacity, max(5, primary_size // 2))
                    orders.append(Order(product, int(second_bid), int(second_size)))
                    buy_capacity -= second_size

            if buy_capacity > 0 and alpha > 1.8 and target_position - position > 18:
                top_bid = min(book["best_bid"] + self.PEPPER_BID_IMPROVE + 1, book["best_ask"] - 1)
                top_size = min(buy_capacity, max(4, primary_size // 3))
                if top_bid < book["best_ask"] and top_size > 0:
                    orders.append(Order(product, int(top_bid), int(top_size)))

        should_offer = position > target_position + 12 or timestamp >= self.PEPPER_LATE_START
        if sell_capacity > 0 and should_offer:
            ask_bias = 2.25 if timestamp < self.PEPPER_LATE_START else 1.10
            ask_quote = max(book["best_ask"] - self.PEPPER_ASK_IMPROVE, int(math.ceil(unwind_fair + ask_bias)))
            ask_quote = max(ask_quote, book["best_bid"] + 1)
            if ask_quote > book["best_bid"]:
                ask_size = min(sell_capacity, max(3, min(position - target_position if position > target_position else position, 7)))
                if ask_size > 0:
                    orders.append(Order(product, int(ask_quote), int(-ask_size)))

        return self.enforce_long_only_limit(limit, original_position, orders)

    def osmium_take_size(self, edge: float, position: int, target_position: int, timestamp: int) -> int:
        size = self.OSMIUM_BASE_SIZE
        if edge >= 1.2:
            size += 3
        if edge >= 2.5:
            size += 3
        if abs(target_position - position) >= 10:
            size += 2
        if timestamp >= 975000:
            size = max(6, size - 4)
        return size

    def osmium_passive_size(self, position: int, target_position: int, alpha: float, is_bid: bool, layer: int) -> int:
        bias = target_position - position
        base = self.OSMIUM_BASE_SIZE if layer == 0 else max(5, self.OSMIUM_BASE_SIZE // 2)
        if is_bid and bias > 0:
            base += min(10, bias // 3)
        if (not is_bid) and bias < 0:
            base += min(10, (-bias) // 3)
        if is_bid and alpha > 1.5:
            base += 2
        if (not is_bid) and alpha < -1.5:
            base += 2
        if abs(position) >= 68:
            base = max(6, base // 2)
        return base

    def pepper_buy_size(self, position: int, target_position: int, edge: float, endgame: bool) -> int:
        gap = max(0, target_position - position)
        size = 7 + min(15, gap)
        if edge >= self.PEPPER_STRONG_BUY_EDGE:
            size += 7
        if gap >= 18:
            size += 4
        if endgame:
            size = max(4, size - 4)
        return size

    def pepper_sell_size(self, position: int, target_position: int, edge: float, endgame: bool) -> int:
        excess = max(0, position - target_position)
        size = max(3, min(11, excess + 3))
        if edge >= self.PEPPER_HARD_EXIT_EDGE + 1.0:
            size += 4
        if endgame:
            size += 2
        return size

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

    def book_snapshot(self, depth: OrderDepth) -> Dict[str, object]:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        best_bid = buy_orders[0][0] if buy_orders else 0
        best_ask = sell_orders[0][0] if sell_orders else max(1, best_bid + 1)
        if buy_orders and sell_orders:
            mid = (best_bid + best_ask) / 2.0
        elif buy_orders:
            mid = float(best_bid)
        elif sell_orders:
            mid = float(best_ask)
        else:
            mid = 0.0

        bid_volume = max(0, buy_orders[0][1]) if buy_orders else 0
        ask_volume = max(0, -sell_orders[0][1]) if sell_orders else 0
        total = bid_volume + ask_volume
        imbalance = 0.0 if total == 0 else (bid_volume - ask_volume) / total

        wall_bid = self.volume_weighted_wall_price(buy_orders, default=best_bid)
        wall_ask = self.volume_weighted_wall_price(sell_orders, default=best_ask)
        wall_mid = (wall_bid + wall_ask) / 2.0

        return {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid": mid,
            "wall_mid": wall_mid,
            "imbalance": imbalance,
        }

    def volume_weighted_wall_price(self, levels: List[tuple[int, int]], default: int) -> float:
        if not levels:
            return float(default)
        top = levels[:3]
        total = sum(abs(volume) for _, volume in top)
        if total == 0:
            return float(default)
        return sum(price * abs(volume) for price, volume in top) / total

    def trend_signal(self, history: object, short_window: int, long_window: int) -> float:
        if not isinstance(history, list):
            return 0.0
        values = [float(value) for value in history[-long_window:] if value is not None]
        if len(values) < max(short_window, long_window // 2):
            return 0.0
        short_mean = sum(values[-short_window:]) / min(short_window, len(values))
        long_mean = sum(values) / len(values)
        return short_mean - long_mean

    def load_cache(self, raw: str) -> Dict[str, object]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def update_anchor(self, cache: Dict[str, object], observed_anchor: float) -> None:
        current = float(cache.get("pepper_anchor", self.PEPPER_INITIAL_ANCHOR))
        updated = (1.0 - self.PEPPER_ANCHOR_SMOOTHING) * current + self.PEPPER_ANCHOR_SMOOTHING * observed_anchor
        cache["pepper_anchor"] = updated

    def push_history(self, cache: Dict[str, object], key: str, value: float) -> None:
        history = cache.get(key)
        if not isinstance(history, list):
            history = []
        history.append(float(value))
        if len(history) > self.HISTORY_LIMIT:
            history = history[-self.HISTORY_LIMIT :]
        cache[key] = history

    def clip(self, value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))