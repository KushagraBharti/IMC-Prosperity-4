"""
Claude Scalp-and-Hold v1

Aggressive evolution of claude_adaptive_accumulator_v1 that adds a fully
dynamic z-score-driven scalp overlay. The goal is to recover the ~$80 of
scalping PnL that 233545 booked from its hardcoded 11-step pepper script —
but without any timestamp or price constants.

Design:

  BASE LAYER
  ==========
  Identical to claude_adaptive_accumulator_v1:
    - vol-adaptive catchup
    - dynamic sweep depth (1/2/3 levels gap-driven)
    - anchor spike rejection
    - pt2 alpha weights and targets

  SCALP OVERLAY
  =============
  Two-state machine per-tick, all gates computed from live distribution:

    LONG  (default; pure accumulator behavior)
    SCALPED (1-3 lots trimmed; accumulator is paused via target=position)

  LONG -> SCALPED (TRIM) when ALL of:
    - position >= SCALP_TRIM_POS_MIN    (near full carry)
    - z_score >= SCALP_TRIM_Z           (statistically high residual vs recent)
    - imbalance <= SCALP_TRIM_IMB       (ask-heavy book — weakness signal)
    - best_bid >= base_fair + max(SCALP_MIN_BID_EDGE, 1.5*residual_std)
      (compare against accumulation base, NOT forward_fair which includes premium)
    - ticks since last scalp >= SCALP_COOLDOWN (overfit protection)
    - would not drop below SCALP_FLOOR

  SCALPED -> LONG (RELOAD) when:
    - z_score <= SCALP_RELOAD_Z, OR
    - ticks in state >= SCALP_STATE_TIMEOUT (safety)

  In SCALPED state we override target_position = position so the
  accumulator does not immediately re-buy.  When RELOAD fires the
  accumulator resumes normally and will re-fill via catchup edges.

  ALL thresholds are derived from live data, the trim size is small (<= 3),
  the cooldown is long (40 ticks), and the floor is high (74).  This
  capital-preserves the carry engine while harvesting statistically-
  clear local highs.
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

    # Portal-proven osmium specialist.
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

    # Pepper accumulator constants.
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

    PEPPER_CATCHUP_EDGE_SMALL_BASE = -0.35
    PEPPER_CATCHUP_EDGE_LARGE_BASE = -1.00
    PEPPER_LARGE_GAP = 12
    PEPPER_TAKE_EDGE = 0.0

    PEPPER_VOL_WINDOW = 20
    PEPPER_VOL_HIGH = 1.5
    PEPPER_VOL_LOW = 0.5
    PEPPER_VOL_TIGHTEN = 0.50
    PEPPER_VOL_LOOSEN = 0.30

    PEPPER_SWEEP_GAP_MID = 18
    PEPPER_SWEEP_GAP_LARGE = 36
    PEPPER_SWEEP_LARGE_MIN_EDGE = 0.5
    PEPPER_SWEEP_MID_MIN_EDGE = 0.0

    PEPPER_BUY_BASE = 4
    PEPPER_BUY_GAP_CAP = 10
    PEPPER_STRONG_BUY_EDGE = 1.5
    PEPPER_STRONG_BUY_BONUS = 4

    # --- SCALP OVERLAY ---
    SCALP_WINDOW = 60
    SCALP_MIN_SAMPLES = 25
    SCALP_TRIM_Z = 2.5
    SCALP_RELOAD_Z = 0.3
    SCALP_TRIM_POS_MIN = 78
    SCALP_TRIM_IMB = -0.15
    SCALP_MIN_BID_EDGE = 3.0
    SCALP_STD_MULT = 1.5
    SCALP_COOLDOWN = 40
    SCALP_STATE_TIMEOUT = 300
    SCALP_TRIM_SIZE_MAX = 3
    SCALP_FLOOR = 74
    SCALP_STD_FLOOR = 0.5

    HISTORY_LIMIT = 120

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
            result["INTARIAN_PEPPER_ROOT"] = self.trade_pepper_scalp_and_hold(
                pepper_book,
                pepper_position,
                timestamp,
                cache,
            )

        return result, 0, json.dumps(cache, separators=(",", ":"))


    # ----- OSMIUM -----

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


    # ----- PEPPER: accumulator + scalp overlay -----

    def trade_pepper_scalp_and_hold(
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

        # ----- scalp residual tracking -----
        residual = float(book["mid"]) - forward_fair
        self.push_history(cache, "pepper_residual", residual)
        residuals = cache.get("pepper_residual", [])
        res_mean, res_std = self.rolling_stats(residuals, self.SCALP_WINDOW)
        effective_std = max(res_std, self.SCALP_STD_FLOOR)
        z_score = (residual - res_mean) / effective_std if effective_std > 0 else 0.0

        scalp_state = cache.get("scalp_state", "LONG")
        last_scalp_ts = int(cache.get("last_scalp_ts", -10 ** 9))
        state_entered_ts = int(cache.get("state_entered_ts", -10 ** 9))
        if not isinstance(scalp_state, str):
            scalp_state = "LONG"

        have_samples = len(residuals) >= self.SCALP_MIN_SAMPLES

        # ---- SCALPED -> LONG transition ----
        if scalp_state == "SCALPED":
            if have_samples and (
                z_score <= self.SCALP_RELOAD_Z
                or (timestamp - state_entered_ts) >= self.SCALP_STATE_TIMEOUT * 100
            ):
                scalp_state = "LONG"
                state_entered_ts = timestamp

        # ---- LONG -> SCALPED decision ----
        trim_size = 0
        if scalp_state == "LONG" and have_samples:
            cooldown_ok = (timestamp - last_scalp_ts) >= self.SCALP_COOLDOWN * 100
            pos_ok = position >= self.SCALP_TRIM_POS_MIN
            z_ok = z_score >= self.SCALP_TRIM_Z
            imb_ok = book["imbalance"] <= self.SCALP_TRIM_IMB
            min_bid_edge = max(self.SCALP_MIN_BID_EDGE, self.SCALP_STD_MULT * effective_std)
            # Compare against base_fair (anchor + drift, no premium) — sells can't clear fwd_fair.
            bid_ok = book["best_bid"] >= base_fair + min_bid_edge

            if pos_ok and z_ok and imb_ok and bid_ok and cooldown_ok:
                headroom = position - self.SCALP_FLOOR
                trim_size = max(0, min(self.SCALP_TRIM_SIZE_MAX, headroom))

        # ---- execute scalp trim if armed ----
        if trim_size > 0:
            best_bid = int(book["best_bid"])
            best_bid_volume = max(0, book["buy_orders"][0][1])
            exec_size = min(trim_size, best_bid_volume)
            if exec_size > 0:
                orders.append(Order(product, best_bid, int(-exec_size)))
                position -= exec_size
                scalp_state = "SCALPED"
                state_entered_ts = timestamp
                last_scalp_ts = timestamp

        cache["scalp_state"] = scalp_state
        cache["state_entered_ts"] = state_entered_ts
        cache["last_scalp_ts"] = last_scalp_ts

        # ---- accumulator logic (suppressed while SCALPED) ----
        if scalp_state == "SCALPED":
            target_position = position

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

        return self.scalp_aware_limit(limit, original_position, orders)

    def adaptive_catchup_edges(self, realized_vol: float) -> tuple:
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

    def rolling_stats(self, history: List[float], window: int) -> tuple:
        if len(history) < 2:
            return 0.0, 0.0
        effective_window = min(window, len(history))
        window_vals = history[-effective_window:]
        mean = sum(window_vals) / effective_window
        var = sum((v - mean) ** 2 for v in window_vals) / effective_window
        return mean, math.sqrt(var)

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

    def scalp_aware_limit(self, limit: int, position: int, orders: List[Order]) -> List[Order]:
        """Allow both buys (accumulator) and sells (scalp trim), clamp to [SCALP_FLOOR, limit]."""
        running = position
        filtered: List[Order] = []
        for order in orders:
            next_position = running + order.quantity
            if order.quantity < 0:
                if next_position >= self.SCALP_FLOOR and next_position <= limit:
                    filtered.append(order)
                    running = next_position
            else:
                if 0 <= next_position <= limit:
                    filtered.append(order)
                    running = next_position
        return filtered

    def clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))
