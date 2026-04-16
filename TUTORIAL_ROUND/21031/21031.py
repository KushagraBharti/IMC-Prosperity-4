from __future__ import annotations

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


class Trader:
    # Tutorial product limits
    POSITION_LIMITS = {"EMERALDS": 80, "TOMATOES": 80}

    # Strategy 1: safest baseline
    EMERALDS_FAIR = 10000
    EMERALDS_MAKER_EDGE = 2
    EMERALDS_TAKE_EDGE = 1
    EMERALDS_BASE_SIZE = 12
    EMERALDS_SOFT_LIMIT = 60

    TOMATOES_TAKE_EDGE = 1
    TOMATOES_MAKER_EDGE = 2
    TOMATOES_BASE_SIZE = 10
    TOMATOES_SOFT_LIMIT = 55

    INVENTORY_SKEW = {
        "EMERALDS": 0.03,
        "TOMATOES": 0.05,
    }

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}

        for product in ("EMERALDS", "TOMATOES"):
            order_depth = state.order_depths.get(product)
            if order_depth is None:
                result[product] = []
                continue

            position = state.position.get(product, 0)
            if product == "EMERALDS":
                orders = self.trade_emeralds(order_depth, position)
            else:
                orders = self.trade_tomatoes(order_depth, position)
            result[product] = orders

        conversions = 0
        trader_data = ""
        return result, conversions, trader_data

    def trade_emeralds(self, depth: OrderDepth, position: int) -> List[Order]:
        fair = float(self.EMERALDS_FAIR)
        reservation = fair - position * self.INVENTORY_SKEW["EMERALDS"]
        return self.build_strategy_orders(
            product="EMERALDS",
            depth=depth,
            position=position,
            fair_price=fair,
            reservation_price=reservation,
            take_edge=self.EMERALDS_TAKE_EDGE,
            maker_edge=self.EMERALDS_MAKER_EDGE,
            base_size=self.EMERALDS_BASE_SIZE,
            soft_limit=self.EMERALDS_SOFT_LIMIT,
            aggressive_mode=False,
        )

    def trade_tomatoes(self, depth: OrderDepth, position: int) -> List[Order]:
        wall_mid = self.compute_wall_mid(depth)
        reservation = wall_mid - position * self.INVENTORY_SKEW["TOMATOES"]
        return self.build_strategy_orders(
            product="TOMATOES",
            depth=depth,
            position=position,
            fair_price=wall_mid,
            reservation_price=reservation,
            take_edge=self.TOMATOES_TAKE_EDGE,
            maker_edge=self.TOMATOES_MAKER_EDGE,
            base_size=self.TOMATOES_BASE_SIZE,
            soft_limit=self.TOMATOES_SOFT_LIMIT,
            aggressive_mode=False,
        )

    def build_strategy_orders(
        self,
        product: str,
        depth: OrderDepth,
        position: int,
        fair_price: float,
        reservation_price: float,
        take_edge: int,
        maker_edge: int,
        base_size: int,
        soft_limit: int,
        aggressive_mode: bool,
    ) -> List[Order]:
        orders: List[Order] = []
        limit = self.POSITION_LIMITS[product]

        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())

        best_bid = buy_orders[0][0] if buy_orders else int(fair_price) - 1
        best_ask = sell_orders[0][0] if sell_orders else int(fair_price) + 1

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)

        if position <= -soft_limit:
            buy_capacity = max(buy_capacity, min(limit - position, base_size * 2))
            sell_capacity = 0
        elif position >= soft_limit:
            sell_capacity = max(sell_capacity, min(limit + position, base_size * 2))
            buy_capacity = 0

        for ask_price, ask_volume in sell_orders:
            if buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            if available <= 0:
                continue
            if ask_price <= fair_price - take_edge:
                size = min(buy_capacity, available)
                orders.append(Order(product, int(ask_price), int(size)))
                buy_capacity -= size

        for bid_price, bid_volume in buy_orders:
            if sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            if available <= 0:
                continue
            if bid_price >= fair_price + take_edge:
                size = min(sell_capacity, available)
                orders.append(Order(product, int(bid_price), int(-size)))
                sell_capacity -= size

        if buy_capacity > 0:
            bid_quote = min(best_bid + 1, int(reservation_price) - maker_edge)
            bid_quote = min(bid_quote, int(fair_price) - 1)
            if bid_quote < best_ask:
                bid_size = min(buy_capacity, self.quote_size(position, limit, base_size, True, aggressive_mode))
                if bid_size > 0:
                    orders.append(Order(product, int(bid_quote), int(bid_size)))

        if sell_capacity > 0:
            ask_quote = max(best_ask - 1, int(reservation_price) + maker_edge)
            ask_quote = max(ask_quote, int(fair_price) + 1)
            if ask_quote > best_bid:
                ask_size = min(sell_capacity, self.quote_size(position, limit, base_size, False, aggressive_mode))
                if ask_size > 0:
                    orders.append(Order(product, int(ask_quote), int(-ask_size)))

        return self.ensure_within_limits(product, position, orders)

    def quote_size(self, position: int, limit: int, base_size: int, is_bid: bool, aggressive_mode: bool) -> int:
        remaining = (limit - position) if is_bid else (limit + position)
        remaining = max(0, remaining)
        if remaining == 0:
            return 0

        utilization = abs(position) / limit if limit else 0
        size = base_size
        if utilization > 0.75:
            size = max(3, base_size // 2)
        elif utilization > 0.5:
            size = max(4, (base_size * 2) // 3)

        if aggressive_mode:
            size += 2

        return min(remaining, size)

    def compute_wall_mid(self, depth: OrderDepth) -> float:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        if not buy_orders or not sell_orders:
            if buy_orders and sell_orders:
                return (buy_orders[0][0] + sell_orders[0][0]) / 2
            if buy_orders:
                return float(buy_orders[0][0])
            if sell_orders:
                return float(sell_orders[0][0])
            return 0.0

        wall_bid = max(buy_orders, key=lambda item: (item[1], item[0]))[0]
        wall_ask = min(sell_orders, key=lambda item: (-abs(item[1]), item[0]))[0]
        return (wall_bid + wall_ask) / 2

    def ensure_within_limits(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        running_position = position
        filtered: List[Order] = []

        for order in orders:
            next_position = running_position + order.quantity
            if -limit <= next_position <= limit:
                filtered.append(order)
                running_position = next_position

        return filtered