from __future__ import annotations

import json
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
    Controlled upgrade of round2_combined_01_official_best_pepper_best_osmium.

    Changes are targeted at the observed shortcomings:
    - Pepper keeps the same carry/regime core, but can trim obvious short-term
      overpricing instead of being pure buy-and-hold.
    - Osmium keeps the same 352020-style market maker, but with mild
      microstructure fair-value adjustments and explicit late-session de-risking
      so it does not carry an oversized residual position into the close.
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
    OSMIUM_FAIR = 10002.0
    OSMIUM_PASSIVE_SIZE = 14
    OSMIUM_TAKE_SIZE = 12
    OSMIUM_STRONG_TAKE_SIZE = 24
    OSMIUM_INVENTORY_TRIGGER = 14
    OSMIUM_FLATTEN_TRIGGER = 18

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

        # Satellite monetization path: keep the long carry core, but trim a few
        # lots when the book is rich versus the structural path and the tape is
        # leaning against us.
        if position > 72 and residual > 5.0 and imbalance < -0.35:
            self.sell_to_floor(
                product=self.PEPPER_PRODUCT,
                orders=orders,
                book=book,
                current_position=position + self.projected_delta(orders),
                floor=max(target, 68),
                max_levels=2,
                max_size=8,
                min_price=base + 5.5,
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
        product = self.OSMIUM_PRODUCT
        limit = self.POSITION_LIMITS[product]
        original_position = position

        best_bid = book["best_bid"]
        best_ask = book["best_ask"]
        buy_orders = book["buy_orders"]
        sell_orders = book["sell_orders"]
        mid = book["mid"]
        wall_dev = book["wall_mid"] - mid
        imbalance = book["imbalance"]
        wall_trend = self.trend_signal(cache.get("osmium_wall_mid", []), 3, 10)
        imb_trend = self.trend_signal(cache.get("osmium_imbalance", []), 3, 10)

        alpha = self.clip(0.85 * wall_dev + 1.90 * imbalance + 0.20 * wall_trend + 0.25 * imb_trend, -2.5, 2.5)
        fair = self.OSMIUM_FAIR + alpha

        orders: List[Order] = []
        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        for ask_price, ask_volume in sell_orders[:3]:
            if buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            edge = fair - ask_price
            if edge > 0 or (position < -self.OSMIUM_INVENTORY_TRIGGER and edge >= -0.25):
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
            if edge > 0 or (position > self.OSMIUM_INVENTORY_TRIGGER and edge >= -0.25):
                size = min(
                    sell_capacity,
                    available,
                    self.OSMIUM_STRONG_TAKE_SIZE if edge >= 2 else self.OSMIUM_TAKE_SIZE,
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    position -= size
                    sell_capacity -= size

        projected = position
        late_cap = self.osmium_position_cap(timestamp)
        if projected > late_cap:
            self.sell_to_floor(
                product=product,
                orders=orders,
                book=book,
                current_position=projected,
                floor=late_cap,
                max_levels=2,
                max_size=16,
                min_price=fair - 1.0,
            )
        elif projected < -late_cap:
            self.buy_to_ceiling(
                product=product,
                orders=orders,
                book=book,
                current_position=projected,
                ceiling=-late_cap,
                max_levels=2,
                max_size=16,
                max_price=fair + 1.0,
            )

        projected = position + self.projected_delta(orders)

        if projected > self.OSMIUM_FLATTEN_TRIGGER:
            flatten_size = min(
                max(0, limit + projected),
                min(projected - self.OSMIUM_INVENTORY_TRIGGER, self.OSMIUM_STRONG_TAKE_SIZE),
            )
            if flatten_size > 0:
                orders.append(Order(product, max(best_bid, int(fair)), int(-flatten_size)))
        elif projected < -self.OSMIUM_FLATTEN_TRIGGER:
            flatten_size = min(
                max(0, limit - projected),
                min((-projected) - self.OSMIUM_INVENTORY_TRIGGER, self.OSMIUM_STRONG_TAKE_SIZE),
            )
            if flatten_size > 0:
                orders.append(Order(product, min(best_ask, int(fair)), int(flatten_size)))

        projected = position + self.projected_delta(orders)
        buy_capacity = max(0, limit - projected)
        sell_capacity = max(0, limit + projected)

        bid_quote = min(best_bid + 1, int(fair - 1) if projected < limit - 30 else int(fair - 2))
        ask_quote = max(best_ask - 1, int(fair + 1) if projected > -(limit - 30) else int(fair + 2))

        late = timestamp >= 90000
        if buy_capacity > 0 and bid_quote < best_ask and (not late or projected <= 0):
            size = self.OSMIUM_STRONG_TAKE_SIZE if projected < -20 else self.OSMIUM_PASSIVE_SIZE
            orders.append(Order(product, int(bid_quote), int(min(size, buy_capacity))))

        if sell_capacity > 0 and ask_quote > best_bid and (not late or projected >= 0):
            size = self.OSMIUM_STRONG_TAKE_SIZE if projected > 20 else self.OSMIUM_PASSIVE_SIZE
            orders.append(Order(product, int(ask_quote), int(-min(size, sell_capacity))))

        return self.ensure_within_limits(product, original_position, orders)

    def osmium_position_cap(self, timestamp: int) -> int:
        if timestamp < 80000:
            return 80
        if timestamp < 90000:
            return 56
        if timestamp < 96000:
            return 36
        return 18

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

    def buy_to_ceiling(
        self,
        product: str,
        orders: List[Order],
        book: Dict[str, object],
        current_position: int,
        ceiling: int,
        max_levels: int,
        max_size: int,
        max_price: float,
    ) -> None:
        gap = max(0, ceiling - current_position)
        if gap <= 0:
            return
        for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
            if level >= max_levels or gap <= 0:
                break
            if ask_price > max_price:
                continue
            size = min(gap, max_size, max(0, abs(int(ask_volume))))
            if size > 0:
                orders.append(Order(product, int(ask_price), int(size)))
                gap -= size

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

    def sell_to_floor(
        self,
        product: str,
        orders: List[Order],
        book: Dict[str, object],
        current_position: int,
        floor: int,
        max_levels: int,
        max_size: int,
        min_price: float,
    ) -> None:
        gap = max(0, current_position - floor)
        if gap <= 0:
            return
        for level, (bid_price, bid_volume) in enumerate(book["buy_orders"]):
            if level >= max_levels or gap <= 0:
                break
            if bid_price < min_price:
                continue
            size = min(gap, max_size, max(0, int(bid_volume)))
            if size > 0:
                orders.append(Order(product, int(bid_price), -int(size)))
                gap -= size

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

    def ensure_within_limits(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        buy_remaining = max(0, limit - position)
        sell_remaining = max(0, limit + position)
        filtered: List[Order] = []
        for order in orders:
            qty = int(order.quantity)
            if qty > 0:
                allowed = min(qty, buy_remaining)
                if allowed > 0:
                    filtered.append(Order(order.symbol, order.price, allowed))
                    buy_remaining -= allowed
            elif qty < 0:
                allowed = min(-qty, sell_remaining)
                if allowed > 0:
                    filtered.append(Order(order.symbol, order.price, -allowed))
                    sell_remaining -= allowed
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
