from __future__ import annotations

import json
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
    """
    Exact ASH_COATED_OSMIUM trader extracted from official submission 349113.
    INTARIAN_PEPPER_ROOT is intentionally disabled so local/portal runs isolate
    only the osmium leg from that submission.
    """

    POSITION_LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80,
    }

    MARKET_ACCESS_FEE_BID = 651

    OSMIUM_FAIR = 10002.0
    OSMIUM_PASSIVE_SIZE = 14
    OSMIUM_TAKE_SIZE = 12
    OSMIUM_STRONG_TAKE_SIZE = 24
    OSMIUM_INVENTORY_TRIGGER = 14
    OSMIUM_FLATTEN_TRIGGER = 18
    OSMIUM_ENDGAME = 970000

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

        if position > self.OSMIUM_FLATTEN_TRIGGER and sell_capacity > 0:
            flatten_size = min(
                sell_capacity,
                min(position - self.OSMIUM_INVENTORY_TRIGGER, self.OSMIUM_STRONG_TAKE_SIZE),
            )
            if flatten_size > 0:
                orders.append(Order(product, max(best_bid, int(fair)), int(-flatten_size)))
        elif position < -self.OSMIUM_FLATTEN_TRIGGER and buy_capacity > 0:
            flatten_size = min(
                buy_capacity,
                min((-position) - self.OSMIUM_INVENTORY_TRIGGER, self.OSMIUM_STRONG_TAKE_SIZE),
            )
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