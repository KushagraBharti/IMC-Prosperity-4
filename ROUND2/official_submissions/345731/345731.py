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

    # Round 2 only: a one-time Market Access Fee bid for the extra 25% quote flow.
    # Keep this at zero while we are still tuning the trading logic; we can set the
    # game-theoretic final bid later without affecting local testing.
    MARKET_ACCESS_FEE_BID = 0

    # Osmium: still mean-reverting, but the hidden replay is a bit richer than a
    # perfectly symmetric 10_000-fair view, so we bias fair slightly upward.
    OSMIUM_FAIR = 10002.0
    OSMIUM_PASSIVE_SIZE = 14
    OSMIUM_TAKE_SIZE = 12
    OSMIUM_STRONG_TAKE_SIZE = 24
    OSMIUM_INVENTORY_TRIGGER = 14
    OSMIUM_FLATTEN_TRIGGER = 18
    OSMIUM_ENDGAME = 970000

    # Pepper: aggressively accumulate the structural carry, but only through
    # non-hardcoded fair-value logic. This version is more aggressive in how
    # quickly it reaches the long carry position while avoiding passive fill
    # dependence.
    PEPPER_TREND_PER_TIMESTAMP = 0.001
    PEPPER_DEFAULT_ANCHOR = 13000.0
    PEPPER_ANCHOR_SMOOTHING = 0.10

    PEPPER_FORWARD_PREMIUM = 8.5
    PEPPER_DEV_WEIGHT = 1.10
    PEPPER_IMBALANCE_WEIGHT = 2.80
    PEPPER_TREND_WEIGHT = 0.40
    PEPPER_IMBALANCE_TREND_WEIGHT = 0.35
    PEPPER_MID_TREND_WEIGHT = 0.15
    PEPPER_ALPHA_CLIP = 4.0

    PEPPER_BASE_TARGET = 78
    PEPPER_TARGET_SLOPE = 0
    PEPPER_TARGET_CLIP = 2.5
    PEPPER_IMB_TARGET_BONUS = 6
    PEPPER_MIN_TARGET = 64
    PEPPER_MAX_TARGET = 80

    PEPPER_SWEEP_LEVELS = 1
    PEPPER_TAKE_EDGE = 0.0
    PEPPER_CATCHUP_EDGE_SMALL = -0.35
    PEPPER_CATCHUP_EDGE_LARGE = -1.00
    PEPPER_LARGE_GAP = 12

    PEPPER_BUY_BASE = 4
    PEPPER_BUY_GAP_CAP = 10
    PEPPER_STRONG_BUY_EDGE = 1.5
    PEPPER_STRONG_BUY_BONUS = 4

    PEPPER_PASSIVE_GAP_TRIGGER = 999
    PEPPER_PASSIVE_BID_IMPROVE = 2
    PEPPER_PASSIVE_MAKER_EDGE = 0.75
    PEPPER_PASSIVE_MAX_SIZE = 0

    HISTORY_LIMIT = 40

    def bid(self):
        return self.MARKET_ACCESS_FEE_BID

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
            if pepper_book["has_both_sides"]:
                observed_anchor = pepper_book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP
                self.update_anchor(cache, observed_anchor)
                self.push_history(cache, "pepper_wall_mid", pepper_book["wall_mid"])
                self.push_history(cache, "pepper_imbalance", pepper_book["imbalance"])
                self.push_history(cache, "pepper_mid", pepper_book["mid"])
            pepper_position = state.position.get("INTARIAN_PEPPER_ROOT", 0)
            result["INTARIAN_PEPPER_ROOT"] = self.trade_pepper_accumulator(
                pepper_book,
                pepper_position,
                timestamp,
                cache,
            )

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
        original_position = position
        fair = self.OSMIUM_FAIR
        best_bid = book["best_bid"]
        best_ask = book["best_ask"]
        buy_orders = book["buy_orders"]
        sell_orders = book["sell_orders"]
        orders: List[Order] = []

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        # Take obviously favorable prices relative to the stable fair.
        for ask_price, ask_volume in sell_orders[:3]:
            if buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            edge = fair - ask_price
            if edge > 0 or (position < -self.OSMIUM_INVENTORY_TRIGGER and edge >= 0):
                size = min(
                    buy_capacity,
                    available,
                    self.OSMIUM_STRONG_TAKE_SIZE if edge >= 2 else self.OSMIUM_TAKE_SIZE,
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    position += size
                    buy_capacity -= size

        for bid_price, bid_volume in buy_orders[:3]:
            if sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            edge = bid_price - fair
            if edge > 0 or (position > self.OSMIUM_INVENTORY_TRIGGER and edge >= 0):
                size = min(
                    sell_capacity,
                    available,
                    self.OSMIUM_STRONG_TAKE_SIZE if edge >= 2 else self.OSMIUM_TAKE_SIZE,
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    position -= size
                    sell_capacity -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        # Flatten inventory at neutral prices so we can keep recycling risk.
        if position > self.OSMIUM_FLATTEN_TRIGGER and sell_capacity > 0:
            flatten_size = min(sell_capacity, min(position - self.OSMIUM_INVENTORY_TRIGGER, self.OSMIUM_STRONG_TAKE_SIZE))
            if flatten_size > 0:
                orders.append(Order(product, max(best_bid, int(fair)), int(-flatten_size)))
        elif position < -self.OSMIUM_FLATTEN_TRIGGER and buy_capacity > 0:
            flatten_size = min(buy_capacity, min((-position) - self.OSMIUM_INVENTORY_TRIGGER, self.OSMIUM_STRONG_TAKE_SIZE))
            if flatten_size > 0:
                orders.append(Order(product, min(best_ask, int(fair)), int(flatten_size)))

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        bid_quote = min(best_bid + 1, 10001 if position < limit - 30 else 10000)
        ask_quote = max(best_ask - 1, 10003 if position > -(limit - 30) else 10004)

        if buy_capacity > 0 and bid_quote < best_ask:
            size = self.OSMIUM_STRONG_TAKE_SIZE if position < 0 else self.OSMIUM_PASSIVE_SIZE
            if size > 0:
                orders.append(Order(product, int(bid_quote), int(min(size, buy_capacity))))

        if sell_capacity > 0 and ask_quote > best_bid:
            size = self.OSMIUM_STRONG_TAKE_SIZE if position > 0 else self.OSMIUM_PASSIVE_SIZE
            if size > 0:
                orders.append(Order(product, int(ask_quote), int(-min(size, sell_capacity))))

        return self.ensure_within_limits(product, original_position, orders)

    def trade_pepper_accumulator(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        product = "INTARIAN_PEPPER_ROOT"
        limit = self.POSITION_LIMITS[product]
        original_position = position
        orders: List[Order] = []

        if not book["has_both_sides"]:
            return []

        anchor = float(cache.get("pepper_anchor", book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP))
        base_fair = anchor + timestamp * self.PEPPER_TREND_PER_TIMESTAMP

        wall_trend = self.trend_signal(cache.get("pepper_wall_mid", []), 3, 9)
        imbalance_trend = self.trend_signal(cache.get("pepper_imbalance", []), 3, 9)
        mid_trend = self.trend_signal(cache.get("pepper_mid", []), 4, 12)
        deviation = book["wall_mid"] - book["mid"]

        alpha = (
            deviation * self.PEPPER_DEV_WEIGHT
            + book["imbalance"] * self.PEPPER_IMBALANCE_WEIGHT
            + wall_trend * self.PEPPER_TREND_WEIGHT
            + imbalance_trend * self.PEPPER_IMBALANCE_TREND_WEIGHT
            + mid_trend * self.PEPPER_MID_TREND_WEIGHT
        )
        alpha = self.clip(alpha, -self.PEPPER_ALPHA_CLIP, self.PEPPER_ALPHA_CLIP)

        forward_fair = base_fair + self.PEPPER_FORWARD_PREMIUM + alpha
        raw_target = (
            self.PEPPER_BASE_TARGET
            + int(round(self.clip(alpha, -self.PEPPER_TARGET_CLIP, self.PEPPER_TARGET_CLIP) * self.PEPPER_TARGET_SLOPE))
            + int(round(max(0.0, book["imbalance"]) * self.PEPPER_IMB_TARGET_BONUS))
        )
        target_position = int(self.clip(raw_target, self.PEPPER_MIN_TARGET, self.PEPPER_MAX_TARGET))

        buy_capacity = max(0, limit - position)
        gap_to_target = max(0, target_position - position)

        for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
            if level >= self.PEPPER_SWEEP_LEVELS or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            if available <= 0:
                continue

            edge = forward_fair - ask_price
            catchup_edge = (
                self.PEPPER_CATCHUP_EDGE_LARGE
                if gap_to_target >= self.PEPPER_LARGE_GAP
                else self.PEPPER_CATCHUP_EDGE_SMALL
            )

            if edge >= self.PEPPER_TAKE_EDGE or (gap_to_target > 0 and edge >= catchup_edge):
                size = min(
                    buy_capacity,
                    available,
                    self.pepper_buy_size(gap_to_target, edge),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size
                    position += size
                    gap_to_target = max(0, target_position - position)

        if buy_capacity > 0 and gap_to_target >= self.PEPPER_PASSIVE_GAP_TRIGGER:
            best_bid = int(book["best_bid"])
            best_ask = int(book["best_ask"])
            bid_quote = min(
                best_bid + self.PEPPER_PASSIVE_BID_IMPROVE,
                int(math.floor(forward_fair - self.PEPPER_PASSIVE_MAKER_EDGE)),
            )
            if bid_quote < best_ask:
                bid_size = min(
                    buy_capacity,
                    self.PEPPER_PASSIVE_MAX_SIZE,
                    max(4, min(gap_to_target, 8)),
                )
                if bid_size > 0:
                    orders.append(Order(product, int(bid_quote), int(bid_size)))

        return self.enforce_long_only_limit(limit, original_position, orders)

    def pepper_buy_size(self, gap_to_target: int, edge: float) -> int:
        size = self.PEPPER_BUY_BASE + min(self.PEPPER_BUY_GAP_CAP, gap_to_target)
        if edge >= self.PEPPER_STRONG_BUY_EDGE:
            size += self.PEPPER_STRONG_BUY_BONUS
        return max(2, size)

    def book_snapshot(self, depth: OrderDepth) -> Dict[str, object]:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        best_bid = buy_orders[0][0] if buy_orders else 0
        best_ask = sell_orders[0][0] if sell_orders else 0
        has_both_sides = bool(buy_orders) and bool(sell_orders)
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
            "has_both_sides": has_both_sides,
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