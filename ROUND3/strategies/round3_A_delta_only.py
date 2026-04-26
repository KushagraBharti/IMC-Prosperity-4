from __future__ import annotations

import json
import math
import os
from typing import Dict, List, Tuple


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
    HYDROGEL = "HYDROGEL_PACK"
    VELVET = "VELVETFRUIT_EXTRACT"
    VOUCHERS = {
        "VEV_4000": 4000,
        "VEV_4500": 4500,
        "VEV_5000": 5000,
        "VEV_5100": 5100,
        "VEV_5200": 5200,
        "VEV_5300": 5300,
        "VEV_5400": 5400,
        "VEV_5500": 5500,
        "VEV_6000": 6000,
        "VEV_6500": 6500,
    }
    ACTIVE_VOUCHERS = {
        "VEV_5000",
        "VEV_5100",
        "VEV_5200",
        "VEV_5300",
        "VEV_5400",
        "VEV_5500",
    }
    POSITION_LIMITS = {
        HYDROGEL: 200,
        VELVET: 200,
        "VEV_4000": 300,
        "VEV_4500": 300,
        "VEV_5000": 300,
        "VEV_5100": 300,
        "VEV_5200": 300,
        "VEV_5300": 300,
        "VEV_5400": 300,
        "VEV_5500": 300,
        "VEV_6000": 300,
        "VEV_6500": 300,
    }

    # Per-strike annualized IVs from the Round 3 capsule, using intraday TTE decay.
    # Deep ITM strikes are intentionally not actively traded because their edge is
    # mostly eaten by wide spreads; 6000/6500 are tick-floor products.
    STRIKE_SIGMA = {
        5000: 0.241855,
        5100: 0.240294,
        5200: 0.242138,
        5300: 0.244513,
        5400: 0.229575,
        5500: 0.248447,
    }

    ENABLE_HYDROGEL = True
    ENABLE_OPTIONS = False
    ENABLE_HEDGE = False
    ENABLE_VELVET_MM = True

    HYDROGEL_AGGRESSION = 1.00
    OPTION_AGGRESSION = 1.00
    HEDGE_BAND = 28
    HISTORY_LIMIT = 80

    def run(self, state: TradingState):
        timestamp = getattr(state, "timestamp", 0)
        cache = self.load_cache(getattr(state, "traderData", ""))
        result: Dict[str, List[Order]] = {product: [] for product in state.order_depths}
        books = {
            product: self.book_snapshot(depth)
            for product, depth in state.order_depths.items()
        }

        if self.HYDROGEL in books:
            self.push_history(cache, "hydro_mid", books[self.HYDROGEL]["mid"])
            self.push_history(cache, "hydro_imb", books[self.HYDROGEL]["imbalance"])
        if self.VELVET in books:
            self.push_history(cache, "velvet_mid", books[self.VELVET]["mid"])
            self.push_history(cache, "velvet_imb", books[self.VELVET]["imbalance"])

        velvet_fair = None
        option_deltas: Dict[str, float] = {}
        if self.VELVET in books:
            velvet_fair = self.velvet_fair(books[self.VELVET], cache)

        if self.ENABLE_HYDROGEL and self.HYDROGEL in books:
            position = state.position.get(self.HYDROGEL, 0)
            hydro_orders = self.trade_hydrogel(books[self.HYDROGEL], position, timestamp, cache)
            result[self.HYDROGEL] = self.enforce_limits(self.HYDROGEL, position, hydro_orders)

        if self.ENABLE_OPTIONS and velvet_fair is not None:
            for product in self.ACTIVE_VOUCHERS:
                if product not in books:
                    continue
                position = state.position.get(product, 0)
                fair, delta = self.option_fair_and_delta(
                    product,
                    velvet_fair,
                    timestamp,
                    books[product],
                    cache,
                )
                option_deltas[product] = delta
                option_orders = self.trade_option(product, books[product], position, fair, delta)
                result[product] = self.enforce_limits(product, position, option_orders)

        if self.VELVET in books and velvet_fair is not None:
            position = state.position.get(self.VELVET, 0)
            velvet_orders: List[Order] = []
            if self.ENABLE_VELVET_MM:
                velvet_orders.extend(self.trade_velvet_mm(books[self.VELVET], position, velvet_fair, cache))
            if self.ENABLE_HEDGE and option_deltas:
                projected_positions = self.project_positions(state.position, result)
                velvet_orders.extend(
                    self.trade_velvet_hedge(
                        books[self.VELVET],
                        projected_positions,
                        option_deltas,
                        velvet_fair,
                    )
                )
            result[self.VELVET] = self.enforce_limits(self.VELVET, position, velvet_orders)

        return result, 0, json.dumps(cache, separators=(",", ":"))

    # ----- Delta-one products -----

    def trade_hydrogel(
        self,
        book: Dict[str, object],
        position: int,
        timestamp: int,
        cache: Dict[str, object],
    ) -> List[Order]:
        product = self.HYDROGEL
        limit = self.POSITION_LIMITS[product]
        fair = self.hydrogel_fair(book, cache)
        signal = fair - book["mid"]
        target = int(self.clip(round(signal * 15.0), -110, 110))
        reservation = fair - (position - target) * 0.055
        orders: List[Order] = []

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        take_edge = 3.0 / self.HYDROGEL_AGGRESSION

        for level, (ask, volume) in enumerate(book["sell_orders"][:2]):
            if buy_capacity <= 0:
                break
            available = max(0, -volume)
            edge = fair - ask
            if edge >= take_edge or (position < target - 35 and edge >= take_edge - 1.25):
                size = min(buy_capacity, available, self.delta_take_size(edge, 18, 36))
                if size > 0:
                    orders.append(Order(product, int(ask), int(size)))
                    buy_capacity -= size
                    position += size

        for level, (bid, volume) in enumerate(book["buy_orders"][:2]):
            if sell_capacity <= 0:
                break
            available = max(0, volume)
            edge = bid - fair
            if edge >= take_edge or (position > target + 35 and edge >= take_edge - 1.25):
                size = min(sell_capacity, available, self.delta_take_size(edge, 18, 36))
                if size > 0:
                    orders.append(Order(product, int(bid), int(-size)))
                    sell_capacity -= size
                    position -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        if best_bid <= 0 or best_ask <= 0:
            return orders

        bid_quote = min(best_bid + 1, int(math.floor(reservation - 1.0)))
        ask_quote = max(best_ask - 1, int(math.ceil(reservation + 1.0)))
        if signal > 3.0:
            bid_quote = min(best_ask - 1, bid_quote + 1)
        elif signal < -3.0:
            ask_quote = max(best_bid + 1, ask_quote - 1)

        passive_size = self.delta_passive_size(position, limit, 22)
        if buy_capacity > 0 and bid_quote < best_ask:
            orders.append(Order(product, int(max(1, bid_quote)), int(min(passive_size, buy_capacity))))
        if sell_capacity > 0 and ask_quote > best_bid:
            orders.append(Order(product, int(ask_quote), int(-min(passive_size, sell_capacity))))

        if timestamp >= 970000:
            orders.extend(self.flatten_orders(product, book, position, fair, trigger=120, max_size=35))
        return orders

    def trade_velvet_mm(
        self,
        book: Dict[str, object],
        position: int,
        fair: float,
        cache: Dict[str, object],
    ) -> List[Order]:
        product = self.VELVET
        limit = self.POSITION_LIMITS[product]
        signal = fair - book["mid"]
        target = int(self.clip(round(signal * 22.0), -45, 45))
        reservation = fair - (position - target) * 0.035
        orders: List[Order] = []
        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        if best_bid <= 0 or best_ask <= 0:
            return orders

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        take_edge = 1.45

        if buy_capacity > 0:
            ask, volume = book["sell_orders"][0]
            edge = fair - ask
            if edge >= take_edge:
                size = min(buy_capacity, max(0, -volume), self.delta_take_size(edge, 8, 18))
                if size > 0:
                    orders.append(Order(product, int(ask), int(size)))
                    buy_capacity -= size
                    position += size

        if sell_capacity > 0:
            bid, volume = book["buy_orders"][0]
            edge = bid - fair
            if edge >= take_edge:
                size = min(sell_capacity, max(0, volume), self.delta_take_size(edge, 8, 18))
                if size > 0:
                    orders.append(Order(product, int(bid), int(-size)))
                    sell_capacity -= size
                    position -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        bid_quote = min(best_bid + 1, int(math.floor(reservation - 0.7)))
        ask_quote = max(best_ask - 1, int(math.ceil(reservation + 0.7)))
        passive_size = self.delta_passive_size(position, limit, 10)
        if buy_capacity > 0 and bid_quote < best_ask:
            orders.append(Order(product, int(max(1, bid_quote)), int(min(passive_size, buy_capacity))))
        if sell_capacity > 0 and ask_quote > best_bid:
            orders.append(Order(product, int(ask_quote), int(-min(passive_size, sell_capacity))))
        return orders

    def hydrogel_fair(self, book: Dict[str, object], cache: Dict[str, object]) -> float:
        micro_shift = book["micro"] - book["mid"]
        trend = self.trend_signal(cache.get("hydro_mid", []), 3, 18)
        imbalance_trend = self.trend_signal(cache.get("hydro_imb", []), 3, 18)
        signal = (
            0.72 * micro_shift
            + 1.65 * book["imbalance"]
            + 0.12 * trend
            + 0.55 * imbalance_trend
        )
        return book["mid"] + self.clip(signal, -7.5, 7.5)

    def velvet_fair(self, book: Dict[str, object], cache: Dict[str, object]) -> float:
        micro_shift = book["micro"] - book["mid"]
        trend = self.trend_signal(cache.get("velvet_mid", []), 4, 22)
        signal = 0.42 * micro_shift + 0.55 * book["imbalance"] + 0.08 * trend
        return book["mid"] + self.clip(signal, -2.5, 2.5)

    # ----- Options -----

    def option_fair_and_delta(
        self,
        product: str,
        underlying_fair: float,
        timestamp: int,
        book: Dict[str, object],
        cache: Dict[str, object],
    ) -> Tuple[float, float]:
        strike = self.VOUCHERS[product]
        tte_days = self.tte_days(timestamp)
        t = max(tte_days / 365.0, 1e-6)
        sigma = self.STRIKE_SIGMA[strike]

        # Tiny adaptive blend: enough to follow broad IV regime changes, not enough
        # to erase the strike-specific edge from the calibrated surface.
        market_iv = self.implied_vol(max(0.01, book["mid"]), underlying_fair, strike, t)
        if 0.05 <= market_iv <= 0.80:
            key = f"iv_{product}"
            previous = float(cache.get(key, sigma))
            updated = 0.97 * previous + 0.03 * market_iv
            cache[key] = self.clip(updated, sigma - 0.035, sigma + 0.035)
            sigma = 0.80 * sigma + 0.20 * float(cache[key])

        fair = self.black_scholes_call(underlying_fair, strike, t, sigma)
        delta = self.black_scholes_delta(underlying_fair, strike, t, sigma)
        return fair, delta

    def trade_option(
        self,
        product: str,
        book: Dict[str, object],
        position: int,
        fair: float,
        delta: float,
    ) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        orders: List[Order] = []
        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        if best_ask <= 0:
            return orders

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        spread = max(1.0, float(book["spread"]))
        take_edge = max(0.85, 0.43 * spread) / self.OPTION_AGGRESSION
        maker_edge = max(0.35, 0.22 * spread) / self.OPTION_AGGRESSION
        base_size = self.option_base_size(delta)

        for ask, volume in book["sell_orders"][:2]:
            if buy_capacity <= 0:
                break
            available = max(0, -volume)
            edge = fair - ask
            if edge >= take_edge:
                size = min(buy_capacity, available, self.edge_size(base_size, edge, take_edge, 2.2))
                if size > 0:
                    orders.append(Order(product, int(ask), int(size)))
                    buy_capacity -= size
                    position += size

        for bid, volume in book["buy_orders"][:2]:
            if sell_capacity <= 0:
                break
            available = max(0, volume)
            edge = bid - fair
            if edge >= take_edge:
                size = min(sell_capacity, available, self.edge_size(base_size, edge, take_edge, 2.2))
                if size > 0:
                    orders.append(Order(product, int(bid), int(-size)))
                    sell_capacity -= size
                    position -= size

        buy_capacity = max(0, limit - position)
        sell_capacity = max(0, limit + position)
        bid_quote = min(best_bid + 1, int(math.floor(fair - maker_edge)))
        ask_quote = max(best_ask - 1, int(math.ceil(fair + maker_edge)))
        passive_size = max(6, min(base_size, 24))

        if buy_capacity > 0 and bid_quote > best_bid and bid_quote < best_ask:
            orders.append(Order(product, int(bid_quote), int(min(passive_size, buy_capacity))))
        if sell_capacity > 0 and ask_quote < best_ask and ask_quote > best_bid:
            orders.append(Order(product, int(ask_quote), int(-min(passive_size, sell_capacity))))

        return orders

    def trade_velvet_hedge(
        self,
        book: Dict[str, object],
        projected_positions: Dict[str, int],
        option_deltas: Dict[str, float],
        velvet_fair: float,
    ) -> List[Order]:
        option_delta = 0.0
        for product, delta in option_deltas.items():
            option_delta += projected_positions.get(product, 0) * delta

        current_velvet = projected_positions.get(self.VELVET, 0)
        target_velvet = int(self.clip(round(-option_delta), -self.POSITION_LIMITS[self.VELVET], self.POSITION_LIMITS[self.VELVET]))
        gap = target_velvet - current_velvet
        if abs(gap) <= self.HEDGE_BAND:
            return []

        orders: List[Order] = []
        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        if gap > 0:
            capacity = self.POSITION_LIMITS[self.VELVET] - current_velvet
            size = min(max(0, capacity), gap, 28 if abs(gap) < 70 else 45)
            if size > 0:
                if abs(gap) > 95 and best_ask - velvet_fair <= 2.0:
                    orders.append(Order(self.VELVET, best_ask, int(size)))
                else:
                    quote = min(best_ask - 1, best_bid + 1)
                    orders.append(Order(self.VELVET, int(max(1, quote)), int(size)))
        else:
            capacity = self.POSITION_LIMITS[self.VELVET] + current_velvet
            size = min(max(0, capacity), -gap, 28 if abs(gap) < 70 else 45)
            if size > 0:
                if abs(gap) > 95 and velvet_fair - best_bid <= 2.0:
                    orders.append(Order(self.VELVET, best_bid, int(-size)))
                else:
                    quote = max(best_bid + 1, best_ask - 1)
                    orders.append(Order(self.VELVET, int(quote), int(-size)))
        return orders

    # ----- Math and utilities -----

    def tte_days(self, timestamp: int) -> float:
        # Official Round 3 final run starts at TTE=5d. Optional env override makes
        # local day-specific experiments possible without breaking portal behavior.
        raw = os.environ.get("ROUND3_TTE_START_DAYS")
        if raw:
            try:
                start = float(raw)
            except ValueError:
                start = 5.0
        else:
            start = 5.0
        return max(0.01, start - timestamp / 1_000_000.0)

    def black_scholes_call(self, s: float, k: int, t: float, sigma: float) -> float:
        if t <= 0 or sigma <= 0:
            return max(0.0, s - k)
        vol = sigma * math.sqrt(t)
        if vol <= 0:
            return max(0.0, s - k)
        d1 = (math.log(max(1e-9, s / k)) + 0.5 * sigma * sigma * t) / vol
        d2 = d1 - vol
        return s * self.norm_cdf(d1) - k * self.norm_cdf(d2)

    def black_scholes_delta(self, s: float, k: int, t: float, sigma: float) -> float:
        if t <= 0 or sigma <= 0:
            return 1.0 if s > k else 0.0
        vol = sigma * math.sqrt(t)
        if vol <= 0:
            return 1.0 if s > k else 0.0
        d1 = (math.log(max(1e-9, s / k)) + 0.5 * sigma * sigma * t) / vol
        return self.norm_cdf(d1)

    def implied_vol(self, price: float, s: float, k: int, t: float) -> float:
        intrinsic = max(0.0, s - k)
        if price <= intrinsic + 1e-6:
            return 0.0
        low, high = 1e-4, 1.2
        for _ in range(28):
            mid = (low + high) / 2.0
            value = self.black_scholes_call(s, k, t, mid)
            if value < price:
                low = mid
            else:
                high = mid
        return (low + high) / 2.0

    def norm_cdf(self, x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    def book_snapshot(self, depth: OrderDepth) -> Dict[str, object]:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        best_bid = buy_orders[0][0] if buy_orders else 0
        best_ask = sell_orders[0][0] if sell_orders else 0
        has_both = bool(buy_orders) and bool(sell_orders)
        if has_both:
            mid = (best_bid + best_ask) / 2.0
            bid_volume = max(0, buy_orders[0][1])
            ask_volume = max(0, -sell_orders[0][1])
            total = bid_volume + ask_volume
            imbalance = (bid_volume - ask_volume) / total if total else 0.0
            micro = (best_bid * ask_volume + best_ask * bid_volume) / total if total else mid
            spread = best_ask - best_bid
        elif buy_orders:
            mid = float(best_bid)
            micro = mid
            imbalance = 0.0
            spread = 0.0
        elif sell_orders:
            mid = float(best_ask)
            micro = mid
            imbalance = 0.0
            spread = 0.0
        else:
            mid = 0.0
            micro = 0.0
            imbalance = 0.0
            spread = 0.0
        return {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid": mid,
            "micro": micro,
            "imbalance": imbalance,
            "spread": spread,
            "has_both": has_both,
        }

    def project_positions(self, positions: Dict[str, int], orders_by_product: Dict[str, List[Order]]) -> Dict[str, int]:
        projected = dict(positions)
        for product, orders in orders_by_product.items():
            current = projected.get(product, 0)
            for order in orders:
                current += int(order.quantity)
            projected[product] = current
        return projected

    def enforce_limits(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        buy_remaining = max(0, limit - position)
        sell_remaining = max(0, limit + position)
        filtered: List[Order] = []
        for order in orders:
            qty = int(order.quantity)
            if qty > 0:
                allowed = min(qty, buy_remaining)
                if allowed > 0:
                    filtered.append(Order(order.symbol, int(order.price), int(allowed)))
                    buy_remaining -= allowed
            elif qty < 0:
                allowed = min(-qty, sell_remaining)
                if allowed > 0:
                    filtered.append(Order(order.symbol, int(order.price), int(-allowed)))
                    sell_remaining -= allowed
        return filtered

    def flatten_orders(
        self,
        product: str,
        book: Dict[str, object],
        position: int,
        fair: float,
        trigger: int,
        max_size: int,
    ) -> List[Order]:
        if position > trigger and book["best_bid"] > 0:
            return [Order(product, int(max(book["best_bid"], math.floor(fair))), -min(max_size, position - trigger))]
        if position < -trigger and book["best_ask"] > 0:
            return [Order(product, int(min(book["best_ask"], math.ceil(fair))), min(max_size, -position - trigger))]
        return []

    def delta_take_size(self, edge: float, base: int, cap: int) -> int:
        return int(max(1, min(cap, base + max(0, edge - 1.0) * 3.0)))

    def delta_passive_size(self, position: int, limit: int, base: int) -> int:
        pressure = abs(position) / max(1, limit)
        if pressure > 0.75:
            return max(4, base // 2)
        if pressure > 0.55:
            return max(6, (base * 2) // 3)
        return base

    def option_base_size(self, delta: float) -> int:
        if delta >= 0.75:
            return 10
        if delta >= 0.50:
            return 14
        if delta >= 0.20:
            return 20
        return 24

    def edge_size(self, base: int, edge: float, threshold: float, cap_mult: float) -> int:
        extra = max(0.0, edge - threshold)
        return int(max(1, min(base * cap_mult, base + extra * 4.0)))

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

    def clip(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

