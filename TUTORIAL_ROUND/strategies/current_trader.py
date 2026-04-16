from __future__ import annotations

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


class Trader:
    # Tutorial product limits
    POSITION_LIMITS = {"EMERALDS": 80, "TOMATOES": 80}

    # Strategy 3: aggressive upside variant
    EMERALDS_FAIR = 10000
    EMERALDS_MAKER_EDGE = 2
    EMERALDS_TAKE_EDGE = 1
    EMERALDS_BASE_SIZE = 16
    EMERALDS_SKEW = 0.06

    TOMATOES_MAKER_EDGE = 1
    TOMATOES_TAKE_EDGE = 1
    TOMATOES_BASE_SIZE = 16
    TOMATOES_SKEW = 0.09
    TOMATOES_DISLOCATION = 1.0
    TOMATOES_STRONG_DISLOCATION = 2.5
    TOMATOES_IMBALANCE_WEIGHT = 2.5
    TOMATOES_DEVIATION_WEIGHT = 1.0

    EMERALDS_SOFT_LIMIT = 65
    TOMATOES_SOFT_LIMIT = 70
    TOMATOES_HARD_FLATTEN = 74

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        for product in ("EMERALDS", "TOMATOES"):
            depth = state.order_depths.get(product)
            if depth is None:
                result[product] = []
                continue

            position = state.position.get(product, 0)
            if product == "EMERALDS":
                orders = self.trade_emeralds(depth, position)
            else:
                orders = self.trade_tomatoes(depth, position)
            result[product] = orders

        return result, 0, ""

    def trade_emeralds(self, depth: OrderDepth, position: int) -> List[Order]:
        fair = float(self.EMERALDS_FAIR)
        reservation = fair - position * self.EMERALDS_SKEW
        return self.place_orders(
            product="EMERALDS",
            depth=depth,
            position=position,
            fair_price=fair,
            reservation_price=reservation,
            take_edge=self.EMERALDS_TAKE_EDGE,
            maker_edge=self.EMERALDS_MAKER_EDGE,
            base_size=self.EMERALDS_BASE_SIZE,
            soft_limit=self.EMERALDS_SOFT_LIMIT,
            aggressive=True,
            directional_bias=0.0,
        )

    def trade_tomatoes(self, depth: OrderDepth, position: int) -> List[Order]:
        wall_mid = self.compute_wall_mid(depth)
        raw_mid = self.compute_mid(depth)
        imbalance = self.top_imbalance(depth)
        deviation = wall_mid - raw_mid
        signal = deviation * self.TOMATOES_DEVIATION_WEIGHT + imbalance * self.TOMATOES_IMBALANCE_WEIGHT
        signal = max(-4.0, min(4.0, signal))
        reservation = wall_mid + signal - position * self.TOMATOES_SKEW

        aggressive = abs(raw_mid - wall_mid) >= self.TOMATOES_DISLOCATION or abs(signal) >= 1.5
        orders = self.place_orders(
            product="TOMATOES",
            depth=depth,
            position=position,
            fair_price=wall_mid,
            reservation_price=reservation,
            take_edge=self.TOMATOES_TAKE_EDGE,
            maker_edge=self.TOMATOES_MAKER_EDGE,
            base_size=self.TOMATOES_BASE_SIZE,
            soft_limit=self.TOMATOES_SOFT_LIMIT,
            aggressive=aggressive,
            directional_bias=signal,
        )

        if abs(position) >= self.TOMATOES_HARD_FLATTEN:
            orders.extend(self.force_flatten("TOMATOES", depth, position, wall_mid))

        return self.ensure_within_limits("TOMATOES", position, orders)

    def place_orders(
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
        aggressive: bool,
        directional_bias: float,
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
            sell_capacity = 0
        elif position >= soft_limit:
            buy_capacity = 0

        max_levels = 3 if aggressive else 1

        for index, (ask_price, ask_volume) in enumerate(sell_orders):
            if index >= max_levels or buy_capacity <= 0:
                break
            available = max(0, -ask_volume)
            if available <= 0:
                continue
            edge = fair_price - ask_price
            strong_signal = directional_bias >= -0.5 or edge >= self.TOMATOES_STRONG_DISLOCATION
            if edge >= take_edge and strong_signal:
                size = min(
                    buy_capacity,
                    available,
                    self.take_size(position, limit, base_size, True, aggressive, edge),
                )
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    buy_capacity -= size

        for index, (bid_price, bid_volume) in enumerate(buy_orders):
            if index >= max_levels or sell_capacity <= 0:
                break
            available = max(0, bid_volume)
            if available <= 0:
                continue
            edge = bid_price - fair_price
            strong_signal = directional_bias <= 0.5 or edge >= self.TOMATOES_STRONG_DISLOCATION
            if edge >= take_edge and strong_signal:
                size = min(
                    sell_capacity,
                    available,
                    self.take_size(position, limit, base_size, False, aggressive, edge),
                )
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    sell_capacity -= size

        bid_quote = min(best_bid + 1, int(reservation_price) - maker_edge)
        ask_quote = max(best_ask - 1, int(reservation_price) + maker_edge)

        if aggressive:
            if directional_bias > 1:
                bid_quote += 1
            elif directional_bias < -1:
                ask_quote -= 1

        bid_quote = min(bid_quote, int(fair_price) - 1 if product == "EMERALDS" else bid_quote)
        ask_quote = max(ask_quote, int(fair_price) + 1 if product == "EMERALDS" else ask_quote)

        if buy_capacity > 0 and bid_quote < best_ask:
            bid_size = min(buy_capacity, self.passive_size(position, limit, base_size, True, aggressive))
            if bid_size > 0:
                orders.append(Order(product, int(bid_quote), int(bid_size)))

        if sell_capacity > 0 and ask_quote > best_bid:
            ask_size = min(sell_capacity, self.passive_size(position, limit, base_size, False, aggressive))
            if ask_size > 0:
                orders.append(Order(product, int(ask_quote), int(-ask_size)))

        return self.ensure_within_limits(product, position, orders)

    def force_flatten(self, product: str, depth: OrderDepth, position: int, fair_price: float) -> List[Order]:
        orders: List[Order] = []
        if position > 0:
            buy_orders = sorted(depth.buy_orders.items(), reverse=True)
            if buy_orders:
                best_bid = buy_orders[0][0]
                if best_bid >= fair_price - 1:
                    size = min(position, max(8, position - 40))
                    orders.append(Order(product, int(best_bid), int(-size)))
        elif position < 0:
            sell_orders = sorted(depth.sell_orders.items())
            if sell_orders:
                best_ask = sell_orders[0][0]
                if best_ask <= fair_price + 1:
                    size = min(-position, max(8, (-position) - 40))
                    orders.append(Order(product, int(best_ask), int(size)))
        return orders

    def take_size(self, position: int, limit: int, base_size: int, is_buy: bool, aggressive: bool, edge: float) -> int:
        remaining = (limit - position) if is_buy else (limit + position)
        remaining = max(0, remaining)
        if remaining == 0:
            return 0

        size = base_size + (4 if aggressive else 0)
        if edge >= 2:
            size += 3
        if edge >= 3:
            size += 3
        if abs(position) > limit * 0.8:
            size = max(5, size - 8)
        return min(remaining, size)

    def passive_size(self, position: int, limit: int, base_size: int, is_bid: bool, aggressive: bool) -> int:
        remaining = (limit - position) if is_bid else (limit + position)
        remaining = max(0, remaining)
        if remaining == 0:
            return 0

        size = base_size if aggressive else max(6, base_size - 4)
        if abs(position) > limit * 0.75:
            size = max(4, size - 5)
        return min(remaining, size)

    def compute_mid(self, depth: OrderDepth) -> float:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        if buy_orders and sell_orders:
            return (buy_orders[0][0] + sell_orders[0][0]) / 2
        if buy_orders:
            return float(buy_orders[0][0])
        if sell_orders:
            return float(sell_orders[0][0])
        return 0.0

    def compute_wall_mid(self, depth: OrderDepth) -> float:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        if not buy_orders or not sell_orders:
            return self.compute_mid(depth)
        wall_bid = max(buy_orders, key=lambda item: (item[1], item[0]))[0]
        wall_ask = min(sell_orders, key=lambda item: (-abs(item[1]), item[0]))[0]
        return (wall_bid + wall_ask) / 2

    def top_imbalance(self, depth: OrderDepth) -> float:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        if not buy_orders or not sell_orders:
            return 0.0
        bid_volume = max(0, buy_orders[0][1])
        ask_volume = max(0, -sell_orders[0][1])
        total = bid_volume + ask_volume
        if total == 0:
            return 0.0
        return (bid_volume - ask_volume) / total

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