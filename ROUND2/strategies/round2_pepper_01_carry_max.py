from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


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
    """
    Round 2 diagnostic PEPPER-only strategy.

    This file intentionally leaves ASH_COATED_OSMIUM empty so portal/local runs
    isolate the pepper module. The MAF bid is zero on purpose; evaluate access
    fee only after selecting the final combined strategy.
    """

    MODE = "carry_max"

    POSITION_LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80,
    }

    PRODUCT = "INTARIAN_PEPPER_ROOT"
    LIMIT = 80

    TREND_PER_TIMESTAMP = 0.001
    ANCHOR_SMOOTHING = 0.08
    HISTORY_LIMIT = 64

    def bid(self):
        return 0

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_cache(getattr(state, "traderData", ""))

        result: Dict[str, List[Order]] = {
            "ASH_COATED_OSMIUM": [],
            "INTARIAN_PEPPER_ROOT": [],
        }

        depth = state.order_depths.get(self.PRODUCT)
        if depth is not None:
            book = self.book_snapshot(depth)
            if book["has_both_sides"]:
                observed_anchor = book["mid"] - timestamp * self.TREND_PER_TIMESTAMP
                self.update_anchor(cache, observed_anchor)
                self.push_history(cache, "pepper_mid", book["mid"])
                self.push_history(cache, "pepper_wall_mid", book["wall_mid"])
                self.push_history(cache, "pepper_imbalance", book["imbalance"])
            position = state.position.get(self.PRODUCT, 0)
            result[self.PRODUCT] = self.trade_pepper(book, position, timestamp, cache)

        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade_pepper(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        if not book["has_both_sides"]:
            return []

        anchor = float(cache.get("pepper_anchor", book["mid"] - timestamp * self.TREND_PER_TIMESTAMP))
        base = anchor + timestamp * self.TREND_PER_TIMESTAMP
        residual = book["mid"] - base
        imbalance = book["imbalance"]
        wall_dev = book["wall_mid"] - book["mid"]
        mid_mom = self.trend_signal(cache.get("pepper_mid", []), 3, 8)
        imb_trend = self.trend_signal(cache.get("pepper_imbalance", []), 3, 8)

        orders: List[Order] = []

        if self.MODE == "carry_max":
            # Baseline robust carry: express the structural +0.001/timestamp drift
            # quickly, but without timestamp-specific prices. It has a tiny
            # emergency sell valve for extreme short-term overpricing.
            alpha = self.clip(0.70 * wall_dev + 2.00 * imbalance - 0.35 * residual + 0.10 * mid_mom, -4.0, 4.0)
            forward_fair = base + 8.5 + alpha
            target = self.LIMIT

            if position > 76 and residual > 7.0 and imbalance < -0.55:
                self.sell_best(orders, book, position - 72, 4, min_price=base + 6.5)

            self.buy_to_target(
                orders=orders,
                book=book,
                position=position + self.projected_delta(orders),
                target=target,
                fair=forward_fair,
                levels=2,
                base_size=16,
                catchup_large=-1.00,
                catchup_small=-0.35,
            )

        elif self.MODE == "residual_swing":
            # Core/satellite design. Core stays long; satellite sells only when
            # residual is rich and book pressure is against us, then reloads.
            target = 76
            if residual < -2.5 or imbalance > 0.35:
                target = 80
            if residual > 3.2 and imbalance < -0.25:
                target = 66

            if position > target:
                self.sell_best(
                    orders,
                    book,
                    max(0, position - target),
                    8,
                    min_price=base + 4.0 + max(0.0, residual * 0.20),
                )

            forward_fair = base + 8.0 + 1.50 * imbalance - 0.25 * residual + 0.10 * imb_trend
            self.buy_to_target(
                orders=orders,
                book=book,
                position=position + self.projected_delta(orders),
                target=target,
                fair=forward_fair,
                levels=2,
                base_size=12,
                catchup_large=-0.75,
                catchup_small=-0.25,
            )

        elif self.MODE == "regime_markov":
            # Markov/GMM-inspired state score from the data pass:
            # negative residual / negative momentum / positive imbalance tends to
            # have positive future excess return; rich residual does the opposite.
            score = -0.55 * residual - 0.18 * mid_mom + 3.00 * imbalance + 0.20 * imb_trend
            if score > 2.5:
                target = 80
            elif score < -3.0:
                target = 64
            else:
                target = 74

            if position > target and residual > 2.5 and score < -1.0:
                self.sell_best(orders, book, max(0, position - target), 6, min_price=base + 4.5)

            forward_fair = base + 7.5 + self.clip(score * 0.60, -4.0, 4.0)
            self.buy_to_target(
                orders=orders,
                book=book,
                position=position + self.projected_delta(orders),
                target=target,
                fair=forward_fair,
                levels=3,
                base_size=14 if score > 1.0 else 8,
                catchup_large=-1.20,
                catchup_small=-0.80 if score > 1.0 else -0.20,
            )

        else:
            return []

        return self.strict_filter(self.PRODUCT, position, orders)

    def buy_to_target(
        self,
        orders: List[Order],
        book: Dict[str, object],
        position: int,
        target: int,
        fair: float,
        levels: int,
        base_size: int,
        catchup_large: float,
        catchup_small: float,
    ) -> None:
        gap = max(0, min(self.LIMIT, target) - position)
        if gap <= 0:
            return
        for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
            if level >= levels or gap <= 0:
                break
            available = max(0, abs(int(ask_volume)))
            if available <= 0:
                continue
            edge = fair - ask_price
            catchup_edge = catchup_large if gap >= 20 else catchup_small
            if edge >= 0.0 or edge >= catchup_edge:
                size = min(available, gap, max(2, min(base_size, gap)))
                if size > 0:
                    orders.append(Order(self.PRODUCT, int(ask_price), int(size)))
                    gap -= size

    def sell_best(
        self,
        orders: List[Order],
        book: Dict[str, object],
        desired: int,
        max_size: int,
        min_price: float,
    ) -> None:
        qty_left = max(0, desired)
        if qty_left <= 0:
            return
        for bid_price, bid_volume in book["buy_orders"][:1]:
            if qty_left <= 0:
                break
            if bid_price >= min_price:
                size = min(max(0, int(bid_volume)), qty_left, max_size)
                if size > 0:
                    orders.append(Order(self.PRODUCT, int(bid_price), -int(size)))
                    qty_left -= size

    def projected_delta(self, orders: List[Order]) -> int:
        return sum(order.quantity for order in orders)

    def book_snapshot(self, depth: OrderDepth) -> Dict[str, object]:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        best_bid = buy_orders[0][0] if buy_orders else 0
        best_ask = sell_orders[0][0] if sell_orders else 0
        has_both_sides = bool(buy_orders) and bool(sell_orders)
        mid = (best_bid + best_ask) / 2 if has_both_sides else float(best_bid or best_ask or 0)
        wall_mid = self.compute_wall_mid(buy_orders, sell_orders, mid)
        imbalance = self.top_imbalance(buy_orders, sell_orders)
        return {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "has_both_sides": has_both_sides,
            "mid": mid,
            "wall_mid": wall_mid,
            "imbalance": imbalance,
        }

    def compute_wall_mid(self, buy_orders: List[Tuple[int, int]], sell_orders: List[Tuple[int, int]], fallback: float) -> float:
        if not buy_orders or not sell_orders:
            return fallback
        wall_bid = max(buy_orders, key=lambda item: (item[1], item[0]))[0]
        wall_ask = min(sell_orders, key=lambda item: (-abs(item[1]), item[0]))[0]
        return (wall_bid + wall_ask) / 2

    def top_imbalance(self, buy_orders: List[Tuple[int, int]], sell_orders: List[Tuple[int, int]]) -> float:
        if not buy_orders or not sell_orders:
            return 0.0
        bid_volume = max(0, buy_orders[0][1])
        ask_volume = abs(min(0, sell_orders[0][1])) if sell_orders[0][1] < 0 else abs(sell_orders[0][1])
        total = bid_volume + ask_volume
        return 0.0 if total == 0 else (bid_volume - ask_volume) / total

    def strict_filter(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        buy_cap = max(0, limit - position)
        sell_cap = max(0, limit + position)
        filtered: List[Order] = []
        for order in orders:
            if order.quantity > 0:
                qty = min(order.quantity, buy_cap)
                if qty > 0:
                    filtered.append(Order(order.symbol, order.price, int(qty)))
                    buy_cap -= qty
            elif order.quantity < 0:
                qty = min(-order.quantity, sell_cap)
                if qty > 0:
                    filtered.append(Order(order.symbol, order.price, -int(qty)))
                    sell_cap -= qty
        return filtered

    def trend_signal(self, history: List[float], short_window: int, long_window: int) -> float:
        if len(history) < long_window:
            return 0.0
        return sum(history[-short_window:]) / short_window - sum(history[-long_window:]) / long_window

    def load_cache(self, raw: str) -> Dict[str, object]:
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def push_history(self, cache: Dict[str, object], key: str, value: float) -> None:
        history = cache.get(key)
        if not isinstance(history, list):
            history = []
        history.append(float(value))
        cache[key] = history[-self.HISTORY_LIMIT :]

    def update_anchor(self, cache: Dict[str, object], observed_anchor: float) -> None:
        if "pepper_anchor" not in cache:
            cache["pepper_anchor"] = float(observed_anchor)
        else:
            current = float(cache["pepper_anchor"])
            cache["pepper_anchor"] = (1.0 - self.ANCHOR_SMOOTHING) * current + self.ANCHOR_SMOOTHING * float(observed_anchor)

    def clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))
