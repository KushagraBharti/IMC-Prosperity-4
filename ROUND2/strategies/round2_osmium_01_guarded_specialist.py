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
    Round 2 diagnostic OSMIUM-only strategy.

    This file intentionally leaves INTARIAN_PEPPER_ROOT empty so portal/local runs
    isolate the osmium module. The MAF bid is zero on purpose; evaluate access
    fee only after selecting the final combined strategy.
    """

    MODE = "guarded_specialist"

    POSITION_LIMITS = {
        "ASH_COATED_OSMIUM": 80,
        "INTARIAN_PEPPER_ROOT": 80,
    }

    PRODUCT = "ASH_COATED_OSMIUM"
    LIMIT = 80
    FAIR = 10000.0
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
                self.push_history(cache, "osmium_mid", book["mid"])
                self.push_history(cache, "osmium_wall_mid", book["wall_mid"])
                self.push_history(cache, "osmium_imbalance", book["imbalance"])
            position = state.position.get(self.PRODUCT, 0)
            result[self.PRODUCT] = self.trade_osmium(book, position, timestamp, cache)

        return result, 0, json.dumps(cache, separators=(",", ":"))

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
        residual = mid - self.FAIR
        wall_dev = book["wall_mid"] - mid
        imbalance = book["imbalance"]
        wall_trend = self.trend_signal(cache.get("osmium_wall_mid", []), 3, 10)
        imb_trend = self.trend_signal(cache.get("osmium_imbalance", []), 3, 10)
        mid_mom = self.trend_signal(cache.get("osmium_mid", []), 3, 8)

        orders: List[Order] = []

        if self.MODE == "guarded_specialist":
            # Repair of the old 224169/314134 specialist: same alpha family,
            # but with strict gross-side limit control and anti-hard-limit guard.
            alpha = self.clip(1.10 * wall_dev + 2.40 * imbalance + 0.20 * wall_trend + 0.40 * imb_trend, -4.0, 4.0)
            fair = self.FAIR + alpha
            target = int(self.clip(round(alpha * 5), -18, 18))
            if position <= -55:
                target = max(target, -15)
            if position >= 55:
                target = min(target, 15)
            reservation = fair - (position - target) * 0.10

            self.take_toward_target(orders, book, position, fair, target, max_levels=3 if abs(alpha) >= 1.4 else 2, max_size=18, edge=1.0)
            projected = position + self.projected_delta(orders)

            # Force de-risking before the portal can strand us at +/-80.
            if projected < -48:
                self.buy_best(orders, book, min((-projected) - 32, 12), max_price=fair + 2.0)
            elif projected > 48:
                self.sell_best(orders, book, min(projected - 32, 12), min_price=fair - 2.0)

            projected = position + self.projected_delta(orders)
            if abs(projected) < 62:
                best_bid = book["best_bid"]
                best_ask = book["best_ask"]
                bid_quote = min(best_bid + 1, int(math.floor(reservation - 1)))
                ask_quote = max(best_ask - 1, int(math.ceil(reservation + 1)))
                size = 12 if abs(projected) < 35 else 7
                if bid_quote < best_ask:
                    orders.append(Order(self.PRODUCT, int(bid_quote), int(size)))
                if ask_quote > best_bid:
                    orders.append(Order(self.PRODUCT, int(ask_quote), -int(size)))

        elif self.MODE == "mean_reversion_taker":
            # Active-only mean reversion. Designed to be less dependent on
            # passive matching and less prone to the -80 trap seen in Round 2.
            fair = self.FAIR - 0.15 * mid_mom + 1.50 * imbalance
            target = int(self.clip(round(-3.0 * residual + 8.0 * imbalance - 0.60 * mid_mom), -36, 36))
            self.take_toward_target(orders, book, position, fair, target, max_levels=2, max_size=10, edge=0.5)

            projected = position + self.projected_delta(orders)
            if projected < -60:
                self.buy_best(orders, book, min((-projected) - 40, 10), max_price=self.FAIR + 2.0)
            elif projected > 60:
                self.sell_best(orders, book, min(projected - 40, 10), min_price=self.FAIR - 2.0)

        elif self.MODE == "regime_mm":
            # GMM/Markov-inspired market maker. The data pass found three
            # regimes: neutral, oversold/down-momentum with positive forward
            # excess, and overbought/up-momentum with negative forward excess.
            score = -0.80 * residual - 0.60 * mid_mom + 6.00 * imbalance + 0.40 * imb_trend
            fair = self.FAIR + self.clip(score * 0.25, -3.0, 3.0)
            target = int(self.clip(round(score * 2.0), -30, 30))
            if position <= -45:
                target = max(target, -20)
            if position >= 45:
                target = min(target, 20)

            self.take_toward_target(orders, book, position, fair, target, max_levels=3, max_size=12, edge=0.5)

            projected = position + self.projected_delta(orders)
            reservation = fair - (projected - target) * 0.08
            if abs(projected) < 55:
                best_bid = book["best_bid"]
                best_ask = book["best_ask"]
                bid_quote = min(best_bid + 1, int(math.floor(reservation - 1)))
                ask_quote = max(best_ask - 1, int(math.ceil(reservation + 1)))
                size = 10 if abs(projected) < 30 else 6
                if bid_quote < best_ask:
                    orders.append(Order(self.PRODUCT, int(bid_quote), int(size)))
                if ask_quote > best_bid:
                    orders.append(Order(self.PRODUCT, int(ask_quote), -int(size)))
        else:
            return []

        return self.strict_filter(self.PRODUCT, position, orders)

    def take_toward_target(
        self,
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
                        orders.append(Order(self.PRODUCT, int(ask_price), int(size)))
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
                        orders.append(Order(self.PRODUCT, int(bid_price), -int(size)))
                        gap -= size

    def buy_best(self, orders: List[Order], book: Dict[str, object], desired: int, max_price: float) -> None:
        qty_left = max(0, int(desired))
        if qty_left <= 0:
            return
        for ask_price, ask_volume in book["sell_orders"][:1]:
            if ask_price <= max_price:
                size = min(qty_left, max(0, abs(int(ask_volume))), 12)
                if size > 0:
                    orders.append(Order(self.PRODUCT, int(ask_price), int(size)))

    def sell_best(self, orders: List[Order], book: Dict[str, object], desired: int, min_price: float) -> None:
        qty_left = max(0, int(desired))
        if qty_left <= 0:
            return
        for bid_price, bid_volume in book["buy_orders"][:1]:
            if bid_price >= min_price:
                size = min(qty_left, max(0, int(bid_volume)), 12)
                if size > 0:
                    orders.append(Order(self.PRODUCT, int(bid_price), -int(size)))

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

    def clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))
