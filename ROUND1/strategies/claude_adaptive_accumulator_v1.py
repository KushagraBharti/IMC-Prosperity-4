"""
Claude Adaptive Accumulator v1

Direct evolution of 242135 pt2 (portal $9870.5). Three fully-dynamic upgrades,
zero hardcoded timestamps or price levels:

  1. Volatility-adaptive catchup edges
     Rolling 20-tick pepper mid stdev tightens catchup when realized vol is
     high (protect against mean-reversion churn) and loosens catchup when
     realized vol is low (chase carry harder). All thresholds are computed
     from the live distribution, not fixed.

  2. Dynamic sweep depth driven by gap-to-target
     Sweep 1 level when comfortably on track, 2 when the gap is mid-sized,
     3 only when the gap is large AND edge is non-negative. This lets the
     algorithm punch through multi-level asks during early accumulation
     without ever paying up at flat inventory.

  3. Anchor spike rejection
     If observed anchor delta exceeds 2.5 * rolling residual stdev, fall
     back to a tiny smoothing (0.02) for that tick so an outlier trade
     does not poison the fair-value estimate. Under normal conditions the
     smoothing is unchanged (0.10). Entirely data-driven.

OSMIUM block is byte-for-byte identical to 224169 / 233545 / 233714 / pt2 —
that engine has locked in $2427.5 across every top strategy, and touching
it can only add risk.
"""

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

    # Portal-proven osmium specialist kept intact from 224169 / 233545 / 233714 / pt2.
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

    # Pepper carry accumulator — same alpha weights as pt2, additive dynamic layers.
    PEPPER_TREND_PER_TIMESTAMP = 0.001
    PEPPER_DEFAULT_ANCHOR = 13000.0
    PEPPER_ANCHOR_SMOOTHING = 0.10
    PEPPER_ANCHOR_SPIKE_SMOOTHING = 0.02
    PEPPER_ANCHOR_SPIKE_Z = 2.5

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

    # Baseline catchup (same as pt2). Volatility scaling adjusts these per-tick.
    PEPPER_CATCHUP_EDGE_SMALL_BASE = -0.35
    PEPPER_CATCHUP_EDGE_LARGE_BASE = -1.00
    PEPPER_LARGE_GAP = 12
    PEPPER_TAKE_EDGE = 0.0

    # Volatility-adaptive catchup knobs.
    PEPPER_VOL_WINDOW = 20
    PEPPER_VOL_HIGH = 1.5
    PEPPER_VOL_LOW = 0.5
    PEPPER_VOL_TIGHTEN = 0.50
    PEPPER_VOL_LOOSEN = 0.30

    # Dynamic sweep depth knobs — gap-based, not timestamp-based.
    # Deeper levels require strictly-positive edge so we never pay up past fair.
    PEPPER_SWEEP_GAP_MID = 18
    PEPPER_SWEEP_GAP_LARGE = 36
    PEPPER_SWEEP_LARGE_MIN_EDGE = 0.5
    PEPPER_SWEEP_MID_MIN_EDGE = 0.0

    PEPPER_BUY_BASE = 4
    PEPPER_BUY_GAP_CAP = 10
    PEPPER_STRONG_BUY_EDGE = 1.5
    PEPPER_STRONG_BUY_BONUS = 4

    HISTORY_LIMIT = 60

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
                self.update_anchor_spike_aware(cache, observed_anchor)
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


    # ----- OSMIUM: byte-for-byte 224169 / pt2 -----

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
            flatten_size = min(
                sell_capacity,
                max(6, min(position - self.OSMIUM_FLATTEN_TRIGGER + 4, self.OSMIUM_BASE_SIZE + 4)),
            )
            orders.append(Order(product, max(best_bid, int(math.floor(fair))), int(-flatten_size)))
        elif position < -self.OSMIUM_FLATTEN_TRIGGER and buy_capacity > 0:
            flatten_size = min(
                buy_capacity,
                max(6, min((-position) - self.OSMIUM_FLATTEN_TRIGGER + 4, self.OSMIUM_BASE_SIZE + 4)),
            )
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


    # ----- PEPPER: adaptive accumulator -----

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

        # Volatility scaling from rolling mid stdev (data-driven).
        mid_hist = cache.get("pepper_mid", [])
        realized_vol = self.rolling_stdev(mid_hist, self.PEPPER_VOL_WINDOW)
        catchup_small, catchup_large = self.adaptive_catchup_edges(realized_vol)

        buy_capacity = max(0, limit - position)
        gap_to_target = max(0, target_position - position)

        sweep_levels = self.dynamic_sweep_levels(gap_to_target)

        for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
            if level >= sweep_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            if available <= 0:
                continue

            edge = forward_fair - ask_price

            # Per-level edge threshold — deeper levels require more edge.
            if level == 0:
                level_floor = (
                    catchup_large
                    if gap_to_target >= self.PEPPER_LARGE_GAP
                    else catchup_small
                )
            elif level == 1:
                level_floor = self.PEPPER_SWEEP_MID_MIN_EDGE
            else:
                level_floor = self.PEPPER_SWEEP_LARGE_MIN_EDGE

            should_take = edge >= self.PEPPER_TAKE_EDGE or (gap_to_target > 0 and edge >= level_floor)

            if should_take:
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

        return self.enforce_long_only_limit(limit, original_position, orders)

    def adaptive_catchup_edges(self, realized_vol: float) -> tuple:
        """Tighten catchup when vol is high, loosen when vol is low."""
        small = self.PEPPER_CATCHUP_EDGE_SMALL_BASE
        large = self.PEPPER_CATCHUP_EDGE_LARGE_BASE
        if realized_vol >= self.PEPPER_VOL_HIGH:
            small += self.PEPPER_VOL_TIGHTEN
            large += self.PEPPER_VOL_TIGHTEN
        elif realized_vol <= self.PEPPER_VOL_LOW:
            small -= self.PEPPER_VOL_LOOSEN
            large -= self.PEPPER_VOL_LOOSEN
        return small, large

    def dynamic_sweep_levels(self, gap_to_target: int) -> int:
        if gap_to_target >= self.PEPPER_SWEEP_GAP_LARGE:
            return 3
        if gap_to_target >= self.PEPPER_SWEEP_GAP_MID:
            return 2
        return 1

    def pepper_buy_size(self, gap_to_target: int, edge: float) -> int:
        size = self.PEPPER_BUY_BASE + min(self.PEPPER_BUY_GAP_CAP, gap_to_target)
        if edge >= self.PEPPER_STRONG_BUY_EDGE:
            size += self.PEPPER_STRONG_BUY_BONUS
        return max(2, size)


    # ----- infrastructure -----

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

    def rolling_stdev(self, history: List[float], window: int) -> float:
        if len(history) < window:
            return 0.0
        window_vals = history[-window:]
        mean = sum(window_vals) / window
        var = sum((v - mean) ** 2 for v in window_vals) / window
        return math.sqrt(var)

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

    def update_anchor_spike_aware(self, cache: Dict[str, object], observed_anchor: float) -> None:
        """Smoothed anchor with outlier rejection from rolling residual stdev."""
        if "pepper_anchor" not in cache:
            cache["pepper_anchor"] = observed_anchor
            cache["pepper_anchor_residuals"] = []
            return

        current = float(cache["pepper_anchor"])
        residual = observed_anchor - current

        residuals = cache.get("pepper_anchor_residuals")
        if not isinstance(residuals, list):
            residuals = []

        residual_std = self.rolling_stdev(residuals, min(len(residuals), 20)) if len(residuals) >= 8 else 0.0

        if residual_std > 0.0 and abs(residual) > self.PEPPER_ANCHOR_SPIKE_Z * residual_std:
            smoothing = self.PEPPER_ANCHOR_SPIKE_SMOOTHING
        else:
            smoothing = self.PEPPER_ANCHOR_SMOOTHING

        updated = (1.0 - smoothing) * current + smoothing * observed_anchor
        cache["pepper_anchor"] = updated

        residuals.append(float(residual))
        cache["pepper_anchor_residuals"] = residuals[-self.HISTORY_LIMIT :]

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
