from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List


try:
    from datamodel import Order, OrderDepth, TradingState
except ImportError:
    class Order:
        def __init__(self, symbol: str, price: int, quantity: int):
            self.symbol = symbol
            self.price = price
            self.quantity = quantity

    class OrderDepth:
        def __init__(self, buy_orders: Dict[int, int] | None = None, sell_orders: Dict[int, int] | None = None):
            self.buy_orders = buy_orders or {}
            self.sell_orders = sell_orders or {}

    class TradingState:
        def __init__(
            self,
            order_depths: Dict[str, OrderDepth],
            position: Dict[str, int] | None = None,
            traderData: str = "",
            timestamp: int = 0,
        ):
            self.order_depths = order_depths
            self.position = position or {}
            self.traderData = traderData
            self.timestamp = timestamp


class Trader:
    POSITION_LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80,
    }

    OSMIUM_FAIR = 10000.0
    OSMIUM_BASE_SIZE = 20
    OSMIUM_SWEEP_LEVELS = 2
    OSMIUM_TAKE_THRESHOLD = 1.4
    OSMIUM_MAKER_EDGE = 1.0
    OSMIUM_SKEW = 0.12
    OSMIUM_SOFT_LIMIT = 66
    OSMIUM_ALPHA_WALL = 0.85
    OSMIUM_ALPHA_IMB = 2.8
    OSMIUM_ALPHA_TREND = 0.35

    PEPPER_TREND_PER_TIMESTAMP = 0.001
    PEPPER_BASE_SIZE = 24
    PEPPER_SWEEP_LEVELS = 3
    PEPPER_TAKE_THRESHOLD = 1.0
    PEPPER_MAKER_EDGE = 1.0
    PEPPER_SKEW = 0.10
    PEPPER_SOFT_LIMIT = 74
    PEPPER_ALPHA_WALL = 1.20
    PEPPER_ALPHA_IMB = 3.10
    PEPPER_ALPHA_TREND = 0.50
    PEPPER_CARRY_BIAS = 0.35
    PEPPER_TARGET_LONG = 14
    PEPPER_TARGET_MAX = 32
    PEPPER_INITIAL_ANCHOR = 12000.0
    PEPPER_ANCHOR_SMOOTHING = 0.18

    HISTORY_LIMIT = 48

    def run(self, state: TradingState):
        cache = self.load_cache(getattr(state, "traderData", ""))
        timestamp = getattr(state, "timestamp", 0)
        orders: Dict[str, List[Order]] = {}

        for product, depth in state.order_depths.items():
            if depth is None:
                continue
            book = self.book_snapshot(depth)
            self.push_history(cache, f"{product}:mid", book["mid"])
            self.push_history(cache, f"{product}:wall_mid", book["wall_mid"])
            if product == "INTARIAN_PEPPER_ROOT":
                observed_anchor = book["mid"] - self.PEPPER_TREND_PER_TIMESTAMP * timestamp
                self.update_anchor(cache, observed_anchor)

        for product in self.POSITION_LIMITS:
            depth = state.order_depths.get(product)
            if depth is None:
                orders[product] = []
                continue
            position = state.position.get(product, 0)
            if product == "ASH_COATED_OSMIUM":
                orders[product] = self.trade_osmium(depth, position, cache)
            else:
                orders[product] = self.trade_pepper(depth, position, timestamp, cache)

        return orders, 0, json.dumps(cache, separators=(",", ":"))

    def trade_osmium(self, depth: OrderDepth, position: int, cache: Dict[str, object]) -> List[Order]:
        book = self.book_snapshot(depth)
        alpha = (
            self.OSMIUM_ALPHA_WALL * (book["wall_mid"] - book["mid"])
            + self.OSMIUM_ALPHA_IMB * book["imbalance"]
            + self.OSMIUM_ALPHA_TREND * self.trend_signal(cache.get("ASH_COATED_OSMIUM:wall_mid", []), 4, 14)
        )
        alpha = self.clip(alpha, -3.2, 3.2)
        fair = self.OSMIUM_FAIR + alpha
        reservation = fair - position * self.OSMIUM_SKEW
        return self.market_make(
            product="ASH_COATED_OSMIUM",
            book=book,
            position=position,
            fair=fair,
            reservation=reservation,
            target_position=0,
            base_size=self.OSMIUM_BASE_SIZE,
            take_threshold=self.OSMIUM_TAKE_THRESHOLD,
            maker_edge=self.OSMIUM_MAKER_EDGE,
            sweep_levels=self.OSMIUM_SWEEP_LEVELS,
            soft_limit=self.OSMIUM_SOFT_LIMIT,
        )

    def trade_pepper(
        self,
        depth: OrderDepth,
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        book = self.book_snapshot(depth)
        anchor = float(cache.get("pepper_anchor", self.PEPPER_INITIAL_ANCHOR))
        drift_fair = anchor + self.PEPPER_TREND_PER_TIMESTAMP * timestamp
        trend = self.trend_signal(cache.get("INTARIAN_PEPPER_ROOT:wall_mid", []), 4, 16)
        alpha = (
            self.PEPPER_ALPHA_WALL * (book["wall_mid"] - book["mid"])
            + self.PEPPER_ALPHA_IMB * book["imbalance"]
            + self.PEPPER_ALPHA_TREND * trend
            + self.PEPPER_CARRY_BIAS
        )
        alpha = self.clip(alpha, -4.5, 4.5)
        fair = drift_fair + alpha
        target_position = int(
            self.clip(
                self.PEPPER_TARGET_LONG + 10.0 * book["imbalance"] + 4.0 * self.clip(trend, -1.5, 1.5),
                -6,
                self.PEPPER_TARGET_MAX,
            )
        )
        reservation = fair - (position - target_position) * self.PEPPER_SKEW
        return self.market_make(
            product="INTARIAN_PEPPER_ROOT",
            book=book,
            position=position,
            fair=fair,
            reservation=reservation,
            target_position=target_position,
            base_size=self.PEPPER_BASE_SIZE,
            take_threshold=self.PEPPER_TAKE_THRESHOLD,
            maker_edge=self.PEPPER_MAKER_EDGE,
            sweep_levels=self.PEPPER_SWEEP_LEVELS,
            soft_limit=self.PEPPER_SOFT_LIMIT,
        )

    def market_make(
        self,
        product: str,
        book: Dict[str, object],
        position: int,
        fair: float,
        reservation: float,
        target_position: int,
        base_size: int,
        take_threshold: float,
        maker_edge: float,
        sweep_levels: int,
        soft_limit: int,
    ) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        orders: List[Order] = []
        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        if position >= soft_limit:
            buy_capacity = 0
        if position <= -soft_limit:
            sell_capacity = 0

        for level, (ask_price, ask_volume) in enumerate(book["sell_orders"]):
            if level >= sweep_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            if available <= 0:
                continue
            edge = fair - ask_price
            if edge >= take_threshold:
                size = min(available, buy_capacity, self.take_size(base_size, edge, position, target_position, True))
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size

        for level, (bid_price, bid_volume) in enumerate(book["buy_orders"]):
            if level >= sweep_levels or sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            if available <= 0:
                continue
            edge = bid_price - fair
            if edge >= take_threshold:
                size = min(available, sell_capacity, self.take_size(base_size, edge, position, target_position, False))
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    sell_capacity -= size

        bid_quote = min(book["best_bid"] + 1, int(reservation - maker_edge))
        ask_quote = max(book["best_ask"] - 1, int(reservation + maker_edge))

        bid_quote = min(bid_quote, book["best_ask"] - 1)
        ask_quote = max(ask_quote, book["best_bid"] + 1)

        bias = self.clip((target_position - position) / max(1, limit), -1.0, 1.0)
        bid_size = min(buy_capacity, self.passive_size(base_size, bias, True))
        ask_size = min(sell_capacity, self.passive_size(base_size, bias, False))

        if buy_capacity > 0 and bid_quote < book["best_ask"] and bid_size > 0:
            orders.append(Order(product, int(bid_quote), int(bid_size)))
        if sell_capacity > 0 and ask_quote > book["best_bid"] and ask_size > 0:
            orders.append(Order(product, int(ask_quote), int(-ask_size)))

        return self.trim_orders(product, position, orders)

    def take_size(self, base_size: int, edge: float, position: int, target_position: int, is_buy: bool) -> int:
        urgency = 1.0 + min(2.0, edge / 2.0)
        bias = target_position - position
        if is_buy:
            urgency += max(0.0, bias) / 40.0
        else:
            urgency += max(0.0, -bias) / 40.0
        return max(1, int(round(base_size * urgency)))

    def passive_size(self, base_size: int, bias: float, is_buy: bool) -> int:
        if is_buy:
            scale = 1.05 + 0.65 * max(0.0, bias) - 0.50 * max(0.0, -bias)
        else:
            scale = 1.05 + 0.65 * max(0.0, -bias) - 0.50 * max(0.0, bias)
        return max(1, int(round(base_size * self.clip(scale, 0.35, 1.85))))

    def trim_orders(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        buy_total = sum(order.quantity for order in orders if order.quantity > 0)
        sell_total = -sum(order.quantity for order in orders if order.quantity < 0)
        buy_room = max(0, limit - position)
        sell_room = max(0, limit + position)
        if buy_total <= buy_room and sell_total <= sell_room:
            return orders

        trimmed: List[Order] = []
        remaining_buy = buy_room
        remaining_sell = sell_room
        for order in orders:
            if order.quantity > 0:
                size = min(order.quantity, remaining_buy)
                if size > 0:
                    trimmed.append(Order(order.symbol, order.price, size))
                    remaining_buy -= size
            else:
                size = min(-order.quantity, remaining_sell)
                if size > 0:
                    trimmed.append(Order(order.symbol, order.price, -size))
                    remaining_sell -= size
        return trimmed

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

        bid_volume = buy_orders[0][1] if buy_orders else 0
        ask_volume = -sell_orders[0][1] if sell_orders else 0
        imbalance_denominator = bid_volume + ask_volume
        imbalance = 0.0 if imbalance_denominator == 0 else (bid_volume - ask_volume) / imbalance_denominator

        wall_bid = self.volume_weighted_wall_price(buy_orders, default=best_bid)
        wall_ask = self.volume_weighted_wall_price(sell_orders, default=best_ask)
        wall_mid = (wall_bid + wall_ask) / 2.0

        return {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid": mid,
            "imbalance": imbalance,
            "wall_mid": wall_mid,
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
        current_anchor = float(cache.get("pepper_anchor", self.PEPPER_INITIAL_ANCHOR))
        updated = (
            (1.0 - self.PEPPER_ANCHOR_SMOOTHING) * current_anchor
            + self.PEPPER_ANCHOR_SMOOTHING * observed_anchor
        )
        cache["pepper_anchor"] = updated

    def push_history(self, cache: Dict[str, object], key: str, value: float) -> None:
        series = cache.get(key)
        if not isinstance(series, list):
            series = []
        series.append(value)
        if len(series) > self.HISTORY_LIMIT:
            series = series[-self.HISTORY_LIMIT :]
        cache[key] = series

    def clip(self, value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))