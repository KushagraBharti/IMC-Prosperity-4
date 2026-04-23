from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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


class Round2ResearchTrader:
    POSITION_LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80,
    }

    HISTORY_LIMIT = 60
    MARKET_ACCESS_FEE_BID = 3001

    PEPPER_MODE: Optional[str] = None
    OSMIUM_MODE: Optional[str] = None

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

    def bid(self):
        return self.MARKET_ACCESS_FEE_BID

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_cache(getattr(state, "traderData", ""))
        result: Dict[str, List[Order]] = {
            "ASH_COATED_OSMIUM": [],
            "INTARIAN_PEPPER_ROOT": [],
        }

        if self.OSMIUM_MODE:
            osmium_depth = state.order_depths.get("ASH_COATED_OSMIUM")
            if osmium_depth is not None:
                osmium_book = self.book_snapshot(osmium_depth)
                self.push_history(cache, "osmium_mid", osmium_book["mid"])
                self.push_history(cache, "osmium_wall_mid", osmium_book["wall_mid"])
                self.push_history(cache, "osmium_imbalance_1", osmium_book["imbalance_1"])
                self.push_history(cache, "osmium_depth_imbalance_3", osmium_book["depth_imbalance_3"])
                position = state.position.get("ASH_COATED_OSMIUM", 0)
                result["ASH_COATED_OSMIUM"] = self.trade_osmium(osmium_book, position, timestamp, cache)

        if self.PEPPER_MODE:
            pepper_depth = state.order_depths.get("INTARIAN_PEPPER_ROOT")
            if pepper_depth is not None:
                pepper_book = self.book_snapshot(pepper_depth)
                if pepper_book["has_both_sides"]:
                    observed_anchor = pepper_book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP
                    self.update_anchor(cache, observed_anchor)
                    self.push_history(cache, "pepper_mid", pepper_book["mid"])
                    self.push_history(cache, "pepper_wall_mid", pepper_book["wall_mid"])
                    self.push_history(cache, "pepper_imbalance_1", pepper_book["imbalance_1"])
                    self.push_history(cache, "pepper_micro_gap", pepper_book["microprice_gap"])
                position = state.position.get("INTARIAN_PEPPER_ROOT", 0)
                result["INTARIAN_PEPPER_ROOT"] = self.trade_pepper(pepper_book, position, timestamp, cache)

        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade_osmium(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        if self.OSMIUM_MODE == "legacy":
            return self.trade_osmium_legacy(book, position, timestamp, cache)
        if self.OSMIUM_MODE == "simple10002":
            return self.trade_osmium_simple10002(book, position, timestamp, cache)
        if self.OSMIUM_MODE == "adaptive":
            return self.trade_osmium_adaptive(book, position, timestamp, cache)
        return []

    def trade_pepper(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        if self.PEPPER_MODE == "baseline":
            return self.trade_pepper_baseline(book, position, timestamp, cache)
        if self.PEPPER_MODE == "harvest":
            return self.trade_pepper_harvest(book, position, timestamp, cache)
        if self.PEPPER_MODE == "adaptive":
            return self.trade_pepper_adaptive(book, position, timestamp, cache)
        return []

    def trade_osmium_legacy(
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
        imbalance_trend = self.trend_signal(cache.get("osmium_imbalance_1", []), 3, 10)
        alpha = (
            (book["wall_mid"] - book["mid"]) * self.OSMIUM_DEV_WEIGHT
            + book["imbalance_1"] * self.OSMIUM_IMBALANCE_WEIGHT
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
                size = min(buy_capacity, available, self.osmium_take_size_legacy(edge, position, timestamp))
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
                size = min(sell_capacity, available, self.osmium_take_size_legacy(edge, position, timestamp))
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
            size = min(buy_capacity, self.osmium_passive_size_legacy(position, timestamp, alpha, True))
            if size > 0:
                orders.append(Order(product, int(bid_quote), int(size)))

        if sell_capacity > 0 and ask_quote > best_bid:
            size = min(sell_capacity, self.osmium_passive_size_legacy(position, timestamp, alpha, False))
            if size > 0:
                orders.append(Order(product, int(ask_quote), int(-size)))

        return self.ensure_within_limits(product, position, orders)

    def trade_osmium_simple10002(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        product = "ASH_COATED_OSMIUM"
        limit = self.POSITION_LIMITS[product]
        original_position = position
        fair = 10002.0
        best_bid = book["best_bid"]
        best_ask = book["best_ask"]
        buy_orders = book["buy_orders"]
        sell_orders = book["sell_orders"]
        orders: List[Order] = []

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        for ask_price, ask_volume in sell_orders[:3]:
            if buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            edge = fair - ask_price
            if edge > 0 or (position < -14 and edge >= 0):
                size = min(buy_capacity, available, 24 if edge >= 2 else 12)
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    position += size
                    buy_capacity -= size

        for bid_price, bid_volume in buy_orders[:3]:
            if sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            edge = bid_price - fair
            if edge > 0 or (position > 14 and edge >= 0):
                size = min(sell_capacity, available, 24 if edge >= 2 else 12)
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    position -= size
                    sell_capacity -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        if position > 18 and sell_capacity > 0:
            flatten_size = min(sell_capacity, min(position - 14, 24))
            if flatten_size > 0:
                orders.append(Order(product, max(best_bid, int(fair)), int(-flatten_size)))
        elif position < -18 and buy_capacity > 0:
            flatten_size = min(buy_capacity, min((-position) - 14, 24))
            if flatten_size > 0:
                orders.append(Order(product, min(best_ask, int(fair)), int(flatten_size)))

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        bid_quote = min(best_bid + 1, 10001 if position < limit - 30 else 10000)
        ask_quote = max(best_ask - 1, 10003 if position > -(limit - 30) else 10004)

        if buy_capacity > 0 and bid_quote < best_ask:
            size = 24 if position < 0 else 14
            orders.append(Order(product, int(bid_quote), int(min(size, buy_capacity))))

        if sell_capacity > 0 and ask_quote > best_bid:
            size = 24 if position > 0 else 14
            orders.append(Order(product, int(ask_quote), int(-min(size, sell_capacity))))

        return self.ensure_within_limits(product, original_position, orders)

    def trade_osmium_adaptive(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        product = "ASH_COATED_OSMIUM"
        limit = self.POSITION_LIMITS[product]
        original_position = position
        orders: List[Order] = []

        dev = book["mid"] - 10000.0
        wall_trend = self.trend_signal(cache.get("osmium_wall_mid", []), 3, 9)
        alpha = (
            -0.08 * dev
            + 1.35 * book["imbalance_1"]
            + 0.90 * book["depth_imbalance_3"]
            + 0.80 * book["wall_gap"]
            + 0.35 * book["microprice_gap"]
            + 0.12 * wall_trend
        )
        alpha = self.clip(alpha, -4.5, 4.5)
        fair = 10000.0 + alpha
        reservation = fair - 0.12 * position
        target_position = int(self.clip(round(alpha * 7), -28, 28))
        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        for ask_price, ask_volume in book["sell_orders"][:3]:
            if buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            edge = fair - ask_price
            if edge >= 0.8 or (position < target_position and edge >= 0):
                size = min(
                    buy_capacity,
                    available,
                    18 if edge >= 2 else (14 if edge >= 1 else 8),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    position += size
                    buy_capacity -= size

        for bid_price, bid_volume in book["buy_orders"][:3]:
            if sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            edge = bid_price - fair
            if edge >= 0.8 or (position > target_position and edge >= 0):
                size = min(
                    sell_capacity,
                    available,
                    18 if edge >= 2 else (14 if edge >= 1 else 8),
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    position -= size
                    sell_capacity -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        if position > 28 and sell_capacity > 0:
            flatten_size = min(sell_capacity, min(position - 20, 16))
            if flatten_size > 0:
                orders.append(Order(product, max(book["best_bid"], int(math.floor(fair))), int(-flatten_size)))
        elif position < -28 and buy_capacity > 0:
            flatten_size = min(buy_capacity, min((-position) - 20, 16))
            if flatten_size > 0:
                orders.append(Order(product, min(book["best_ask"], int(math.ceil(fair))), int(flatten_size)))

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        bid_quote = min(book["best_bid"] + 1, int(math.floor(reservation - 0.8)))
        ask_quote = max(book["best_ask"] - 1, int(math.ceil(reservation + 0.8)))

        if alpha > 1.2:
            bid_quote += 1
        elif alpha < -1.2:
            ask_quote -= 1

        if buy_capacity > 0 and bid_quote < book["best_ask"]:
            size = min(buy_capacity, 10 if position > 20 else (16 if position < 0 else 12))
            if size > 0:
                orders.append(Order(product, int(bid_quote), int(size)))

        if sell_capacity > 0 and ask_quote > book["best_bid"]:
            size = min(sell_capacity, 10 if position < -20 else (16 if position > 0 else 12))
            if size > 0:
                orders.append(Order(product, int(ask_quote), int(-size)))

        return self.ensure_within_limits(product, original_position, orders)

    def trade_pepper_baseline(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        return self.trade_pepper_common(book, position, timestamp, cache, mode="baseline")

    def trade_pepper_harvest(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        return self.trade_pepper_common(book, position, timestamp, cache, mode="harvest")

    def trade_pepper_adaptive(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        return self.trade_pepper_common(book, position, timestamp, cache, mode="adaptive")

    def trade_pepper_common(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
        mode: str,
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
        imbalance_trend = self.trend_signal(cache.get("pepper_imbalance_1", []), 3, 9)
        mid_trend = self.trend_signal(cache.get("pepper_mid", []), 4, 12)
        deviation = book["wall_mid"] - book["mid"]
        residual = book["mid"] - base_fair

        alpha = (
            deviation * self.PEPPER_DEV_WEIGHT
            + book["imbalance_1"] * self.PEPPER_IMBALANCE_WEIGHT
            + wall_trend * self.PEPPER_TREND_WEIGHT
            + imbalance_trend * self.PEPPER_IMBALANCE_TREND_WEIGHT
            + mid_trend * self.PEPPER_MID_TREND_WEIGHT
        )
        alpha = self.clip(alpha, -self.PEPPER_ALPHA_CLIP, self.PEPPER_ALPHA_CLIP)
        forward_fair = base_fair + self.PEPPER_FORWARD_PREMIUM + alpha

        raw_target = (
            self.PEPPER_BASE_TARGET
            + int(round(self.clip(alpha, -self.PEPPER_TARGET_CLIP, self.PEPPER_TARGET_CLIP) * self.PEPPER_TARGET_SLOPE))
            + int(round(max(0.0, book["imbalance_1"]) * self.PEPPER_IMB_TARGET_BONUS))
        )

        if mode == "harvest":
            raw_target += int(round(self.clip(-1.8 * residual, -14, 6)))
            min_target = 56
        elif mode == "adaptive":
            raw_target += int(round(self.clip(-2.4 * residual, -20, 8)))
            raw_target += int(round(self.clip(-2.5 * book["microprice_gap"], -6, 4)))
            min_target = 48
        else:
            min_target = self.PEPPER_MIN_TARGET

        target_position = int(self.clip(raw_target, min_target, self.PEPPER_MAX_TARGET))
        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, position)
        gap_to_target = max(0, target_position - position)

        sweep_levels = 1
        if mode == "adaptive" and residual <= -1.5:
            sweep_levels = 2

        for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
            if level >= sweep_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            if available <= 0:
                continue
            edge = forward_fair - ask_price
            catchup_edge = self.PEPPER_CATCHUP_EDGE_LARGE if gap_to_target >= self.PEPPER_LARGE_GAP else self.PEPPER_CATCHUP_EDGE_SMALL

            if edge >= self.PEPPER_TAKE_EDGE or (gap_to_target > 0 and edge >= catchup_edge):
                size = min(
                    buy_capacity,
                    available,
                    self.pepper_buy_size(gap_to_target, edge, residual, mode),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size
                    position += size
                    gap_to_target = max(0, target_position - position)

        if mode in {"harvest", "adaptive"} and sell_capacity > 0:
            trim_floor = 56 if mode == "harvest" else 48
            trim_threshold = 2.5 if mode == "harvest" else 2.0
            sell_levels = 1 if mode == "harvest" else 2
            for level, (bid_price, bid_volume) in enumerate(book["buy_orders"]):
                if level >= sell_levels or position <= trim_floor:
                    break
                available = max(0, bid_volume)
                if available <= 0:
                    continue
                sell_edge = bid_price - (base_fair + self.PEPPER_FORWARD_PREMIUM)
                should_trim = residual >= trim_threshold and sell_edge >= 0.5
                if mode == "adaptive":
                    should_trim = should_trim or (position > target_position + 8 and sell_edge >= 0)
                if should_trim:
                    size = min(
                        available,
                        position - trim_floor,
                        5 if mode == "harvest" else 8,
                    )
                    if size > 0:
                        orders.append(Order(product, int(bid_price), int(-size)))
                        position -= size
                        sell_capacity -= size

        if mode == "adaptive":
            buy_capacity = max(0, limit - position)
            if buy_capacity > 0 and residual <= -1.5 and gap_to_target >= 4:
                best_bid = int(book["best_bid"])
                best_ask = int(book["best_ask"])
                bid_quote = min(best_bid + 1, int(math.floor(base_fair + 6.5)))
                if bid_quote < best_ask:
                    bid_size = min(buy_capacity, 4)
                    if bid_size > 0:
                        orders.append(Order(product, int(bid_quote), int(bid_size)))

            if position > 52 and residual >= 2.8:
                best_bid = int(book["best_bid"])
                ask_quote = max(best_bid + 1, int(math.ceil(base_fair + 9.5)))
                if ask_quote > best_bid:
                    ask_size = min(position - 52, 4)
                    if ask_size > 0:
                        orders.append(Order(product, int(ask_quote), int(-ask_size)))

        return self.ensure_long_within_limit(limit, original_position, orders)

    def pepper_buy_size(self, gap_to_target: int, edge: float, residual: float, mode: str) -> int:
        size = self.PEPPER_BUY_BASE + min(self.PEPPER_BUY_GAP_CAP, gap_to_target)
        if edge >= self.PEPPER_STRONG_BUY_EDGE:
            size += self.PEPPER_STRONG_BUY_BONUS
        if mode == "adaptive" and residual <= -2.0:
            size += 2
        if mode == "harvest" and residual >= 2.0:
            size = max(2, size - 2)
        return max(2, size)

    def book_snapshot(self, depth: OrderDepth) -> Dict[str, object]:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        best_bid = buy_orders[0][0] if buy_orders else 0
        best_ask = sell_orders[0][0] if sell_orders else 0
        has_both_sides = bool(buy_orders) and bool(sell_orders)
        mid = self.compute_mid(buy_orders, sell_orders)
        wall_mid = self.compute_wall_mid(buy_orders, sell_orders)
        imbalance_1 = self.top_imbalance(buy_orders, sell_orders)
        microprice = self.compute_microprice(buy_orders, sell_orders)
        depth_imbalance_3 = self.depth_imbalance(buy_orders, sell_orders, 3)
        return {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid": mid,
            "wall_mid": wall_mid,
            "imbalance_1": imbalance_1,
            "microprice": microprice,
            "microprice_gap": microprice - mid,
            "wall_gap": wall_mid - mid,
            "depth_imbalance_3": depth_imbalance_3,
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

    def compute_microprice(self, buy_orders: List[tuple], sell_orders: List[tuple]) -> float:
        if not buy_orders or not sell_orders:
            return self.compute_mid(buy_orders, sell_orders)
        bid_price, bid_volume = buy_orders[0]
        ask_price, ask_volume = sell_orders[0]
        ask_size = max(0, -ask_volume)
        bid_size = max(0, bid_volume)
        total = bid_size + ask_size
        if total == 0:
            return self.compute_mid(buy_orders, sell_orders)
        return (ask_price * bid_size + bid_price * ask_size) / total

    def depth_imbalance(self, buy_orders: List[tuple], sell_orders: List[tuple], levels: int) -> float:
        bid = sum(max(0, volume) for _, volume in buy_orders[:levels])
        ask = sum(max(0, -volume) for _, volume in sell_orders[:levels])
        total = bid + ask
        if total == 0:
            return 0.0
        return (bid - ask) / total

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

    def ensure_long_within_limit(self, limit: int, position: int, orders: List[Order]) -> List[Order]:
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

    def osmium_take_size_legacy(self, edge: float, position: int, timestamp: int) -> int:
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

    def osmium_passive_size_legacy(self, position: int, timestamp: int, alpha: float, is_bid: bool) -> int:
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
