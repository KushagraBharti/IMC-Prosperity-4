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
    Recommended upgrade over round2_combined_01_official_best_pepper_best_osmium.

    Pepper:
    - exact official-best pepper leg (350754 / round2_pepper_03_regime_markov)

    Osmium:
    - guarded specialist leg, which was stronger on all 3 local engines and was
      explicitly built to avoid the hard-limit / stranded-inventory failure mode.
    """

    POSITION_LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80,
    }

    MARKET_ACCESS_FEE_BID = 0

    PEPPER_PRODUCT = "INTARIAN_PEPPER_ROOT"
    PEPPER_LIMIT = 80
    PEPPER_TREND_PER_TIMESTAMP = 0.001
    PEPPER_ANCHOR_SMOOTHING = 0.08

    OSMIUM_PRODUCT = "ASH_COATED_OSMIUM"
    OSMIUM_FAIR = 10000.0

    HISTORY_LIMIT = 64

    def bid(self):
        return self.MARKET_ACCESS_FEE_BID

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_cache(getattr(state, "traderData", ""))

        result: Dict[str, List[Order]] = {
            "ASH_COATED_OSMIUM": [],
            "INTARIAN_PEPPER_ROOT": [],
        }

        pepper_depth = state.order_depths.get(self.PEPPER_PRODUCT)
        if pepper_depth is not None:
            pepper_book = self.book_snapshot(pepper_depth)
            if pepper_book["has_both_sides"]:
                observed_anchor = pepper_book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP
                self.update_anchor(cache, observed_anchor)
                self.push_history(cache, "pepper_mid", pepper_book["mid"])
                self.push_history(cache, "pepper_wall_mid", pepper_book["wall_mid"])
                self.push_history(cache, "pepper_imbalance", pepper_book["imbalance"])
            pepper_position = state.position.get(self.PEPPER_PRODUCT, 0)
            result[self.PEPPER_PRODUCT] = self.trade_pepper(pepper_book, pepper_position, timestamp, cache)

        osmium_depth = state.order_depths.get(self.OSMIUM_PRODUCT)
        if osmium_depth is not None:
            osmium_book = self.book_snapshot(osmium_depth)
            if osmium_book["has_both_sides"]:
                self.push_history(cache, "osmium_mid", osmium_book["mid"])
                self.push_history(cache, "osmium_wall_mid", osmium_book["wall_mid"])
                self.push_history(cache, "osmium_imbalance", osmium_book["imbalance"])
            osmium_position = state.position.get(self.OSMIUM_PRODUCT, 0)
            result[self.OSMIUM_PRODUCT] = self.trade_osmium(osmium_book, osmium_position, timestamp, cache)

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

        anchor = float(cache.get("pepper_anchor", book["mid"] - timestamp * self.PEPPER_TREND_PER_TIMESTAMP))
        base = anchor + timestamp * self.PEPPER_TREND_PER_TIMESTAMP
        residual = book["mid"] - base
        imbalance = book["imbalance"]
        mid_mom = self.trend_signal(cache.get("pepper_mid", []), 3, 8)
        imb_trend = self.trend_signal(cache.get("pepper_imbalance", []), 3, 8)

        score = -0.55 * residual - 0.18 * mid_mom + 3.00 * imbalance + 0.20 * imb_trend
        if score > 2.5:
            target = 80
        elif score < -3.0:
            target = 64
        else:
            target = 74

        orders: List[Order] = []

        if position > target and residual > 2.5 and score < -1.0:
            self.sell_best(
                product=self.PEPPER_PRODUCT,
                orders=orders,
                book=book,
                desired=max(0, position - target),
                max_size=6,
                min_price=base + 4.5,
            )

        forward_fair = base + 7.5 + self.clip(score * 0.60, -4.0, 4.0)
        self.buy_to_target(
            product=self.PEPPER_PRODUCT,
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

        return self.strict_filter(self.PEPPER_PRODUCT, position, orders)

    def trade_osmium(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        if not book["has_both_sides"]:
            return []

        mid = book["mid"]
        residual = mid - self.OSMIUM_FAIR
        wall_dev = book["wall_mid"] - mid
        imbalance = book["imbalance"]
        wall_trend = self.trend_signal(cache.get("osmium_wall_mid", []), 3, 10)
        imb_trend = self.trend_signal(cache.get("osmium_imbalance", []), 3, 10)

        alpha = self.clip(1.10 * wall_dev + 2.40 * imbalance + 0.20 * wall_trend + 0.40 * imb_trend, -4.0, 4.0)
        fair = self.OSMIUM_FAIR + alpha
        target = int(self.clip(round(alpha * 5), -18, 18))
        if position <= -55:
            target = max(target, -15)
        if position >= 55:
            target = min(target, 15)
        reservation = fair - (position - target) * 0.10

        orders: List[Order] = []
        self.take_toward_target(
            product=self.OSMIUM_PRODUCT,
            orders=orders,
            book=book,
            position=position,
            fair=fair,
            target=target,
            max_levels=3 if abs(alpha) >= 1.4 else 2,
            max_size=18,
            edge=1.0,
        )

        projected = position + self.projected_delta(orders)

        if projected < -48:
            self.buy_best_osmium(
                orders=orders,
                book=book,
                desired=min((-projected) - 32, 12),
                max_price=fair + 2.0,
            )
        elif projected > 48:
            self.sell_best_osmium(
                orders=orders,
                book=book,
                desired=min(projected - 32, 12),
                min_price=fair - 2.0,
            )

        projected = position + self.projected_delta(orders)
        if abs(projected) < 62:
            best_bid = book["best_bid"]
            best_ask = book["best_ask"]
            bid_quote = min(best_bid + 1, int(math.floor(reservation - 1)))
            ask_quote = max(best_ask - 1, int(math.ceil(reservation + 1)))
            size = 12 if abs(projected) < 35 else 7
            if bid_quote < best_ask:
                orders.append(Order(self.OSMIUM_PRODUCT, int(bid_quote), int(size)))
            if ask_quote > best_bid:
                orders.append(Order(self.OSMIUM_PRODUCT, int(ask_quote), -int(size)))

        return self.strict_filter(self.OSMIUM_PRODUCT, position, orders)

    def buy_to_target(
        self,
        product: str,
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
        gap = max(0, min(self.PEPPER_LIMIT, target) - position)
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
                    orders.append(Order(product, int(ask_price), int(size)))
                    gap -= size

    def take_toward_target(
        self,
        product: str,
        orders: List[Order],
        book: Dict[str, object],
        position: int,
        fair: float,
        target: int,
        max_levels: int,
        max_size: int,
        edge: float,
    ) -> None:
        current = position + self.projected_delta(orders)

        if current < target:
            gap = target - current
            for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
                if level >= max_levels or gap <= 0:
                    break
                available = max(0, abs(int(ask_volume)))
                price_edge = fair - ask_price
                if price_edge >= edge or (gap >= 20 and price_edge >= -0.5):
                    size = min(available, gap, max_size)
                    if size > 0:
                        orders.append(Order(product, int(ask_price), int(size)))
                        gap -= size

        current = position + self.projected_delta(orders)

        if current > target:
            gap = current - target
            for level, (bid_price, bid_volume) in enumerate(book["buy_orders"]):
                if level >= max_levels or gap <= 0:
                    break
                available = max(0, int(bid_volume))
                price_edge = bid_price - fair
                if price_edge >= edge or (gap >= 20 and price_edge >= -0.5):
                    size = min(available, gap, max_size)
                    if size > 0:
                        orders.append(Order(product, int(bid_price), -int(size)))
                        gap -= size

    def buy_best_osmium(self, orders: List[Order], book: Dict[str, object], desired: int, max_price: float) -> None:
        qty_left = max(0, int(desired))
        if qty_left <= 0:
            return
        for ask_price, ask_volume in book["sell_orders"][:1]:
            if ask_price <= max_price:
                size = min(qty_left, max(0, abs(int(ask_volume))), 12)
                if size > 0:
                    orders.append(Order(self.OSMIUM_PRODUCT, int(ask_price), int(size)))

    def sell_best_osmium(self, orders: List[Order], book: Dict[str, object], desired: int, min_price: float) -> None:
        qty_left = max(0, int(desired))
        if qty_left <= 0:
            return
        for bid_price, bid_volume in book["buy_orders"][:1]:
            if bid_price >= min_price:
                size = min(qty_left, max(0, int(bid_volume)), 12)
                if size > 0:
                    orders.append(Order(self.OSMIUM_PRODUCT, int(bid_price), -int(size)))

    def sell_best(
        self,
        product: str,
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
                    orders.append(Order(product, int(bid_price), -int(size)))
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

    def compute_wall_mid(
        self,
        buy_orders: List[Tuple[int, int]],
        sell_orders: List[Tuple[int, int]],
        fallback: float,
    ) -> float:
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
            cache["pepper_anchor"] = (
                (1.0 - self.PEPPER_ANCHOR_SMOOTHING) * current
                + self.PEPPER_ANCHOR_SMOOTHING * float(observed_anchor)
            )

    def clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))
