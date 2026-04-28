from __future__ import annotations

import json
import math
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
    class Trade:
        symbol: str
        price: int
        quantity: int
        buyer: str | None = None
        seller: str | None = None
        timestamp: int = 0

    @dataclass
    class TradingState:
        order_depths: Dict[str, OrderDepth]
        position: Dict[str, int] = field(default_factory=dict)
        market_trades: Dict[str, List[Trade]] = field(default_factory=dict)
        own_trades: Dict[str, List[Trade]] = field(default_factory=dict)
        traderData: str = ""
        timestamp: int = 0


class Trader:
    POSITION_LIMITS = {
        "HYDROGEL_PACK": 200,
        "VELVETFRUIT_EXTRACT": 200,
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

    HISTORY_LIMIT = 48
    TRADE_START_TIMESTAMP = 0
    VELVET_TRADE_START_TIMESTAMP = 0
    OPTION_TRADE_START_TIMESTAMP = 0

    HYDRO_DEFAULT_FAIR = 9991.0
    HYDRO_SMOOTHING = 0.05
    HYDRO_IMBALANCE_WEIGHT = 10.5
    HYDRO_DEVIATION_WEIGHT = 0.04
    HYDRO_TREND_WEIGHT = 0.03
    HYDRO_SIGNAL_THRESHOLD = 1.1
    HYDRO_TAKE_EDGE = 10.0
    HYDRO_MAKER_EDGE = 2.0
    HYDRO_QUOTE_SIZE = 96
    HYDRO_TAKE_SIZE = 120
    HYDRO_SOFT_LIMIT = 200
    HYDRO_FLATTEN_TRIGGER = 130
    HYDRO_EXIT_TIMESTAMP = 999_999
    HYDRO_MARK_FAIR_WEIGHT = 0.0
    HYDRO_MARK_EXEC_THRESHOLD = 99.0
    HYDRO_MARK_EXEC_SIZE = 0
    HYDRO_PASSIVE_MARK_THRESHOLD = 0.2
    HYDRO_PASSIVE_MARK_EDGE = 1.0
    HYDRO_PASSIVE_MARK_SIZE = 48
    HYDRO_PASSIVE_MAX_SPREAD = 30
    HYDRO_MM_ENABLED = True
    HYDRO_MM_EDGE = 1.0
    HYDRO_MM_SIZE = 48
    HYDRO_MM_MAX_SPREAD = 40
    HYDRO_MM_MIN_SPREAD = 14
    HYDRO_MM_INV_SKEW = 0.10

    VELVET_DEFAULT_FAIR = 5250.0
    VELVET_SMOOTHING = 0.06
    VELVET_IMBALANCE_WEIGHT = 0.8
    VELVET_DEVIATION_WEIGHT = 0.09
    VELVET_TREND_WEIGHT = 0.09
    VELVET_SIGNAL_THRESHOLD = 1.1
    VELVET_TAKE_EDGE = 4.5
    VELVET_MAKER_EDGE = 1.0
    VELVET_QUOTE_SIZE = 4
    VELVET_TAKE_SIZE = 6
    VELVET_SOFT_LIMIT = 10
    VELVET_FLATTEN_TRIGGER = 6

    OPTION_VOL = 0.233
    STRIKES = {
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
    STRIKE_VOL = {
        4000: 0.5244,
        4500: 0.3056,
        5000: 0.2500,
        5100: 0.2550,
        5200: 0.24215,
        5300: 0.24455,
        5400: 0.22960,
        5500: 0.24845,
        6000: 0.3775,
        6500: 0.5701,
    }
    ACTIVE_VOUCHERS = [
        "VEV_4000",
        "VEV_4500",
        "VEV_5000",
        "VEV_5100",
        "VEV_5200",
        "VEV_5300",
        "VEV_5400",
        "VEV_5500",
        "VEV_6000",
        "VEV_6500",
    ]
    OPTION_EDGE = {
        4000: 10.00,
        4500: 2.00,
        5000: 1.50,
        5100: 0.50,
        5200: 7.00,
        5300: 3.00,
        5400: 1.00,
        5500: 3.00,
        6000: 0.50,
        6500: 0.50,
    }
    OPTION_INV_SKEW = 0.0
    OPTION_DELTA_PENALTY = 0.0
    OPTION_SIZE = 20
    OPTION_SIZE_BY_STRIKE = {5000: 9, 5100: 9}
    FREE_OPTION_BID_SIZE = 24
    WEAK_OPTION_EXIT_TIMESTAMP = 86_600
    WEAK_OPTION_EXIT_SET = {"VEV_5200", "VEV_5300"}
    VELVET_EXIT_TIMESTAMP = 71_900
    TIMED_OPTION_EXIT = {"VEV_5000": 71_900}
    VELVET_IMPLIED_ANCHOR = 5260.0
    VELVET_IMPLIED_WEIGHT = 0.55
    VELVET_REL_TAKE_EDGE = 5.0
    VELVET_REL_SKEW = 0.0025
    VELVET_REL_TAKE_SIZE = 70
    VELVET_REL_PASSIVE_SIZE = 24
    VELVET_MARK_FAIR_WEIGHT = 0.25
    OPTION_MARK_SPOT_WEIGHT = 0.0

    HYDRO_MARK_WEIGHTS = {
        "Mark 14": 1.0,
        "Mark 38": -1.0,
        "Mark 22": 0.25,
    }
    VELVET_MARK_WEIGHTS = {
        "Mark 01": 0.0,
        "Mark 14": -0.7,
        "Mark 67": 1.0,
        "Mark 55": 1.0,
        "Mark 49": -1.0,
        "Mark 22": -0.5,
    }

    def run(self, state: TradingState):
        cache = self.load_cache(getattr(state, "traderData", ""))
        timestamp = getattr(state, "timestamp", 0)
        results = {product: [] for product in self.POSITION_LIMITS}

        books = {product: self.book_snapshot(depth) for product, depth in state.order_depths.items()}
        hydro_mark_signal = self.mark_flow_signal(cache, state, "HYDROGEL_PACK", self.HYDRO_MARK_WEIGHTS, "hydro_mark_flow")
        velvet_mark_signal = self.mark_flow_signal(cache, state, "VELVETFRUIT_EXTRACT", self.VELVET_MARK_WEIGHTS, "velvet_mark_flow")

        hydro_book = books.get("HYDROGEL_PACK")
        if hydro_book and hydro_book["has_both_sides"]:
            hydro_fair = self.compute_linear_fair(
                cache=cache,
                key="hydro_anchor",
                history_key="hydro_mid",
                observed_mid=hydro_book["mid"],
                default=self.HYDRO_DEFAULT_FAIR,
                smoothing=self.HYDRO_SMOOTHING,
                imbalance_weight=self.HYDRO_IMBALANCE_WEIGHT,
                deviation_weight=self.HYDRO_DEVIATION_WEIGHT,
                trend_weight=self.HYDRO_TREND_WEIGHT,
                imbalance=hydro_book["imbalance"],
            )
            hydro_fair += self.HYDRO_MARK_FAIR_WEIGHT * hydro_mark_signal
            hydro_pos = state.position.get("HYDROGEL_PACK", 0)
            if timestamp >= self.TRADE_START_TIMESTAMP:
                if timestamp >= self.HYDRO_EXIT_TIMESTAMP:
                    results["HYDROGEL_PACK"] = self.flatten_position_orders("HYDROGEL_PACK", hydro_book, hydro_pos)
                else:
                    hydro_orders = self.trade_signal_product(
                        product="HYDROGEL_PACK",
                        book=hydro_book,
                        fair=hydro_fair,
                        position=hydro_pos,
                        signal_threshold=self.HYDRO_SIGNAL_THRESHOLD,
                        take_edge=self.HYDRO_TAKE_EDGE,
                        maker_edge=self.HYDRO_MAKER_EDGE,
                        quote_size=self.HYDRO_QUOTE_SIZE,
                        take_size=self.HYDRO_TAKE_SIZE,
                        soft_limit=self.HYDRO_SOFT_LIMIT,
                        flatten_trigger=self.HYDRO_FLATTEN_TRIGGER,
                        min_price=1,
                    )
                    hydro_orders.extend(self.trade_hydro_mark_flow(hydro_book, hydro_pos, hydro_mark_signal))
                    hydro_orders.extend(self.trade_hydro_passive_mark(hydro_book, hydro_pos, hydro_fair, hydro_mark_signal))
                    hydro_orders.extend(self.trade_hydro_market_make(hydro_book, hydro_pos, hydro_fair))
                    results["HYDROGEL_PACK"] = self.ensure_within_hard_limit("HYDROGEL_PACK", hydro_pos, hydro_orders)

        velvet_book = books.get("VELVETFRUIT_EXTRACT")
        if velvet_book and velvet_book["has_both_sides"]:
            velvet_linear_fair = self.compute_linear_fair(
                cache=cache,
                key="velvet_anchor",
                history_key="velvet_mid",
                observed_mid=velvet_book["mid"],
                default=self.VELVET_DEFAULT_FAIR,
                smoothing=self.VELVET_SMOOTHING,
                imbalance_weight=self.VELVET_IMBALANCE_WEIGHT,
                deviation_weight=self.VELVET_DEVIATION_WEIGHT,
                trend_weight=self.VELVET_TREND_WEIGHT,
                imbalance=velvet_book["imbalance"],
            )
            velvet_implied_fair = self.vfe_implied_fair(books)
            velvet_fair = 0.35 * velvet_linear_fair + 0.65 * velvet_implied_fair + self.VELVET_MARK_FAIR_WEIGHT * velvet_mark_signal
            velvet_pos = state.position.get("VELVETFRUIT_EXTRACT", 0)
            if timestamp >= self.VELVET_TRADE_START_TIMESTAMP:
                if timestamp >= self.VELVET_EXIT_TIMESTAMP:
                    results["VELVETFRUIT_EXTRACT"] = self.flatten_position_orders("VELVETFRUIT_EXTRACT", velvet_book, velvet_pos)
                else:
                    results["VELVETFRUIT_EXTRACT"] = self.trade_velvet_relative(velvet_book, velvet_implied_fair, velvet_pos)
        else:
            velvet_fair = float(cache.get("velvet_anchor", self.VELVET_DEFAULT_FAIR))

        t_years = self.time_to_expiry_years(timestamp)
        if timestamp >= self.OPTION_TRADE_START_TIMESTAMP:
            option_orders = self.trade_vouchers_relative(
                books,
                state.position,
                velvet_fair + self.OPTION_MARK_SPOT_WEIGHT * velvet_mark_signal,
                t_years,
                timestamp,
            )
            for symbol, orders in option_orders.items():
                results[symbol] = orders

        return results, 0, json.dumps(cache, separators=(",", ":"))

    def trade_signal_product(
        self,
        product: str,
        book: Dict[str, object],
        fair: float,
        position: int,
        signal_threshold: float,
        take_edge: float,
        maker_edge: float,
        quote_size: int,
        take_size: int,
        soft_limit: int,
        flatten_trigger: int,
        min_price: int,
    ) -> List[Order]:
        original_position = position
        orders: List[Order] = []
        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        signal = fair - float(book["mid"])

        buy_capacity = max(0, soft_limit - position)
        sell_capacity = max(0, soft_limit + position)

        for ask_price, ask_volume in book["sell_orders"][:2]:
            if buy_capacity <= 0:
                break
            edge = fair - ask_price
            if edge >= take_edge:
                size = min(take_size, buy_capacity, max(0, -int(ask_volume)))
                if size > 0:
                    orders.append(Order(product, int(ask_price), int(size)))
                    position += size
                    buy_capacity -= size

        for bid_price, bid_volume in book["buy_orders"][:2]:
            if sell_capacity <= 0:
                break
            edge = bid_price - fair
            if edge >= take_edge:
                size = min(take_size, sell_capacity, max(0, int(bid_volume)))
                if size > 0:
                    orders.append(Order(product, int(bid_price), int(-size)))
                    position -= size
                    sell_capacity -= size

        buy_capacity = max(0, soft_limit - position)
        sell_capacity = max(0, soft_limit + position)

        if position > flatten_trigger and sell_capacity > 0:
            size = min(quote_size + 4, sell_capacity, position)
            price = max(best_bid, int(round(fair)))
            orders.append(Order(product, price, int(-size)))
        elif position < -flatten_trigger and buy_capacity > 0:
            size = min(quote_size + 4, buy_capacity, -position)
            price = min(best_ask, int(round(fair)))
            orders.append(Order(product, price, int(size)))
        else:
            if signal >= signal_threshold and buy_capacity > 0:
                bid_quote = min(best_bid + 1, int(math.floor(fair - maker_edge)))
                bid_quote = max(min_price, bid_quote)
                if bid_quote < best_ask:
                    orders.append(Order(product, bid_quote, int(min(quote_size, buy_capacity))))
            elif signal <= -signal_threshold and sell_capacity > 0:
                ask_quote = max(best_ask - 1, int(math.ceil(fair + maker_edge)))
                ask_quote = max(min_price, ask_quote)
                if ask_quote > best_bid:
                    orders.append(Order(product, ask_quote, int(-min(quote_size, sell_capacity))))

        return self.ensure_within_hard_limit(product, original_position, orders)

    def flatten_position_orders(self, product: str, book: Dict[str, object], position: int) -> List[Order]:
        if position < 0 and book["sell_orders"]:
            return self.ensure_within_hard_limit(product, position, [Order(product, int(book["sell_orders"][-1][0]), int(-position))])
        if position > 0 and book["buy_orders"]:
            return self.ensure_within_hard_limit(product, position, [Order(product, int(book["buy_orders"][-1][0]), int(-position))])
        return []

    def trade_hydro_market_make(self, book: Dict[str, object], position: int, fair: float) -> List[Order]:
        if not self.HYDRO_MM_ENABLED:
            return []
        orders: List[Order] = []
        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        spread = best_ask - best_bid
        if spread < self.HYDRO_MM_MIN_SPREAD or spread > self.HYDRO_MM_MAX_SPREAD:
            return orders

        limit = self.POSITION_LIMITS["HYDROGEL_PACK"]
        fair_adj = fair - position * self.HYDRO_MM_INV_SKEW
        bid_price = min(best_bid + 1, int(math.floor(fair_adj - self.HYDRO_MM_EDGE)))
        ask_price = max(best_ask - 1, int(math.ceil(fair_adj + self.HYDRO_MM_EDGE)))

        if bid_price < best_ask and position < limit:
            orders.append(Order("HYDROGEL_PACK", bid_price, int(min(self.HYDRO_MM_SIZE, limit - position))))
        if ask_price > best_bid and position > -limit:
            orders.append(Order("HYDROGEL_PACK", ask_price, int(-min(self.HYDRO_MM_SIZE, limit + position))))
        return orders

    def trade_hydro_passive_mark(self, book: Dict[str, object], position: int, fair: float, signal: float) -> List[Order]:
        orders: List[Order] = []
        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        spread = best_ask - best_bid
        if spread <= 0 or spread > self.HYDRO_PASSIVE_MAX_SPREAD:
            return orders

        limit = self.POSITION_LIMITS["HYDROGEL_PACK"]
        size = self.HYDRO_PASSIVE_MARK_SIZE

        if signal > self.HYDRO_PASSIVE_MARK_THRESHOLD and position < limit:
            price = min(best_bid + 1, int(math.floor(fair - self.HYDRO_PASSIVE_MARK_EDGE)))
            if price < best_ask:
                orders.append(Order("HYDROGEL_PACK", price, int(min(size, limit - position))))
        elif signal < -self.HYDRO_PASSIVE_MARK_THRESHOLD and position > -limit:
            price = max(best_ask - 1, int(math.ceil(fair + self.HYDRO_PASSIVE_MARK_EDGE)))
            if price > best_bid:
                orders.append(Order("HYDROGEL_PACK", price, int(-min(size, limit + position))))

        return orders

    def trade_hydro_mark_flow(self, book: Dict[str, object], position: int, signal: float) -> List[Order]:
        if abs(signal) < self.HYDRO_MARK_EXEC_THRESHOLD:
            return []
        spread = int(book["best_ask"]) - int(book["best_bid"])
        if spread <= 0 or spread > 24:
            return []
        qty = min(self.HYDRO_MARK_EXEC_SIZE, int(8 + 6 * abs(signal)))
        if signal > 0 and position < self.POSITION_LIMITS["HYDROGEL_PACK"]:
            qty = min(qty, self.POSITION_LIMITS["HYDROGEL_PACK"] - position)
            return [Order("HYDROGEL_PACK", int(book["best_ask"]), int(qty))] if qty > 0 else []
        if signal < 0 and position > -self.POSITION_LIMITS["HYDROGEL_PACK"]:
            qty = min(qty, self.POSITION_LIMITS["HYDROGEL_PACK"] + position)
            return [Order("HYDROGEL_PACK", int(book["best_bid"]), int(-qty))] if qty > 0 else []
        return []

    def trade_option(
        self,
        symbol: str,
        book: Dict[str, object],
        fair: float,
        position: int,
        cfg: Dict[str, object],
    ) -> List[Order]:
        original_position = position
        soft_limit = int(cfg["soft_limit"])
        size = int(cfg["size"])
        edge = float(cfg["edge"])
        mode = str(cfg["mode"])
        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        orders: List[Order] = []

        buy_capacity = max(0, soft_limit - position)
        sell_capacity = max(0, soft_limit + position)

        can_buy = mode != "short_bias" or position < 0
        can_sell = mode != "long_bias" or position > 0

        for ask_price, ask_volume in book["sell_orders"][:2]:
            if buy_capacity <= 0:
                break
            if can_buy and fair - ask_price >= edge:
                qty = min(size, buy_capacity, max(0, -int(ask_volume)))
                if qty > 0:
                    orders.append(Order(symbol, int(ask_price), int(qty)))
                    position += qty
                    buy_capacity -= qty

        for bid_price, bid_volume in book["buy_orders"][:2]:
            if sell_capacity <= 0:
                break
            if can_sell and bid_price - fair >= edge:
                qty = min(size, sell_capacity, max(0, int(bid_volume)))
                if qty > 0:
                    orders.append(Order(symbol, int(bid_price), int(-qty)))
                    position -= qty
                    sell_capacity -= qty

        buy_capacity = max(0, soft_limit - position)
        sell_capacity = max(0, soft_limit + position)

        if position > size and sell_capacity > 0:
            orders.append(Order(symbol, max(best_bid, int(round(fair))), int(-min(size, sell_capacity, position))))
        elif position < -size and buy_capacity > 0:
            orders.append(Order(symbol, min(best_ask, int(round(fair))), int(min(size, buy_capacity, -position))))
        else:
            if mode in {"two_sided", "long_bias"} and buy_capacity > 0:
                bid_quote = min(best_bid + 1, int(math.floor(fair - max(0.5, edge - 0.5))))
                bid_quote = max(0, bid_quote)
                if bid_quote < best_ask:
                    orders.append(Order(symbol, bid_quote, int(min(size, buy_capacity))))
            if mode in {"two_sided", "short_bias"} and sell_capacity > 0:
                ask_quote = max(best_ask - 1, int(math.ceil(fair + max(0.5, edge - 0.5))))
                ask_quote = max(0, ask_quote)
                if ask_quote > best_bid:
                    orders.append(Order(symbol, ask_quote, int(-min(size, sell_capacity))))

        return self.ensure_within_hard_limit(symbol, original_position, orders)

    def vfe_implied_fair(self, books: Dict[str, Dict[str, object]]) -> float:
        deep_values = []
        book_4000 = books.get("VEV_4000")
        book_4500 = books.get("VEV_4500")
        if book_4000 and book_4000["has_both_sides"]:
            deep_values.append((float(book_4000["mid"]) + 4000.0, 0.25))
        if book_4500 and book_4500["has_both_sides"]:
            deep_values.append((float(book_4500["mid"]) + 4500.0, 0.35))
        if not deep_values:
            return self.VELVET_IMPLIED_ANCHOR
        implied = sum(value * weight for value, weight in deep_values) / sum(weight for _, weight in deep_values)
        return self.VELVET_IMPLIED_WEIGHT * self.VELVET_IMPLIED_ANCHOR + (1.0 - self.VELVET_IMPLIED_WEIGHT) * implied

    def trade_velvet_relative(self, book: Dict[str, object], fair: float, position: int) -> List[Order]:
        product = "VELVETFRUIT_EXTRACT"
        original_position = position
        orders: List[Order] = []
        fair_adj = fair - position * self.VELVET_REL_SKEW

        for ask_price, ask_volume in book["sell_orders"]:
            edge = fair_adj - ask_price
            if edge >= self.VELVET_REL_TAKE_EDGE:
                qty = min(self.VELVET_REL_TAKE_SIZE, max(0, -int(ask_volume)))
                if qty > 0:
                    orders.append(Order(product, int(ask_price), int(qty)))
                    position += qty

        for bid_price, bid_volume in book["buy_orders"]:
            edge = bid_price - fair_adj
            if edge >= self.VELVET_REL_TAKE_EDGE:
                qty = min(self.VELVET_REL_TAKE_SIZE, max(0, int(bid_volume)))
                if qty > 0:
                    orders.append(Order(product, int(bid_price), int(-qty)))
                    position -= qty

        best_bid = int(book["best_bid"])
        best_ask = int(book["best_ask"])
        passive_bid = min(best_bid + 1, int(math.floor(fair_adj - 2)))
        passive_ask = max(best_ask - 1, int(math.ceil(fair_adj + 2)))
        if passive_bid < best_ask and position < 140:
            orders.append(Order(product, int(passive_bid), int(self.VELVET_REL_PASSIVE_SIZE)))
        if passive_ask > best_bid and position > -140:
            orders.append(Order(product, int(passive_ask), int(-self.VELVET_REL_PASSIVE_SIZE)))

        return self.ensure_within_hard_limit(product, original_position, orders)

    def trade_vouchers_relative(
        self,
        books: Dict[str, Dict[str, object]],
        positions: Dict[str, int],
        spot_fair: float,
        t_years: float,
        timestamp: int,
    ) -> Dict[str, List[Order]]:
        net_delta = positions.get("VELVETFRUIT_EXTRACT", 0)
        for symbol in self.ACTIVE_VOUCHERS:
            strike = self.STRIKES[symbol]
            sigma = self.STRIKE_VOL[strike]
            net_delta += positions.get(symbol, 0) * self.black_scholes_delta(spot_fair, strike, t_years, sigma)

        results: Dict[str, List[Order]] = {}
        for symbol in self.ACTIVE_VOUCHERS:
            book = books.get(symbol)
            if not book or not book["has_both_sides"]:
                continue
            strike = self.STRIKES[symbol]
            sigma = self.STRIKE_VOL[strike]
            fair = self.black_scholes_call(spot_fair, strike, t_years, sigma)
            delta = self.black_scholes_delta(spot_fair, strike, t_years, sigma)
            position = positions.get(symbol, 0)
            edge_threshold = self.OPTION_EDGE[strike]
            fair_adj = fair - position * self.OPTION_INV_SKEW - self.OPTION_DELTA_PENALTY * net_delta * delta
            original_position = position
            orders: List[Order] = []

            timed_exit = self.TIMED_OPTION_EXIT.get(symbol)
            if timed_exit is not None and timestamp >= timed_exit:
                if position < 0 and book["sell_orders"]:
                    close_price = int(book["sell_orders"][-1][0])
                    orders.append(Order(symbol, close_price, int(-position)))
                elif position > 0 and book["buy_orders"]:
                    close_price = int(book["buy_orders"][-1][0])
                    orders.append(Order(symbol, close_price, int(-position)))
                checked = self.ensure_within_hard_limit(symbol, original_position, orders)
                if checked:
                    results[symbol] = checked
                continue

            if symbol in self.WEAK_OPTION_EXIT_SET and timestamp >= self.WEAK_OPTION_EXIT_TIMESTAMP:
                if position < 0 and book["sell_orders"]:
                    close_price = int(book["sell_orders"][-1][0])
                    orders.append(Order(symbol, close_price, int(-position)))
                elif position > 0 and book["buy_orders"]:
                    close_price = int(book["buy_orders"][-1][0])
                    orders.append(Order(symbol, close_price, int(-position)))
                checked = self.ensure_within_hard_limit(symbol, original_position, orders)
                if checked:
                    results[symbol] = checked
                continue

            for ask_price, ask_volume in book["sell_orders"]:
                edge = fair_adj - ask_price
                if edge >= edge_threshold:
                    base_size = self.OPTION_SIZE_BY_STRIKE.get(strike, self.OPTION_SIZE)
                    qty = base_size if edge < edge_threshold + 2.0 else 2 * base_size
                    qty = min(qty, max(0, -int(ask_volume)))
                    if qty > 0:
                        orders.append(Order(symbol, int(ask_price), int(qty)))
                        position += qty

            for bid_price, bid_volume in book["buy_orders"]:
                edge = bid_price - fair_adj
                if edge >= edge_threshold:
                    base_size = self.OPTION_SIZE_BY_STRIKE.get(strike, self.OPTION_SIZE)
                    qty = base_size if edge < edge_threshold + 2.0 else 2 * base_size
                    qty = min(qty, max(0, int(bid_volume)))
                    if qty > 0:
                        orders.append(Order(symbol, int(bid_price), int(-qty)))
                        position -= qty

            if symbol in {"VEV_6000", "VEV_6500"} and position < self.POSITION_LIMITS[symbol]:
                # Mark01/Mark22 often print these far OTM vouchers at zero. Bidding only at
                # zero gives us convexity if filled, without risking positive premium.
                qty = min(self.FREE_OPTION_BID_SIZE, self.POSITION_LIMITS[symbol] - position)
                if qty > 0 and int(book["best_bid"]) <= 0:
                    orders.append(Order(symbol, 0, int(qty)))

            checked = self.ensure_within_hard_limit(symbol, original_position, orders)
            if checked:
                results[symbol] = checked
        return results

    def option_fair(self, spot_fair: float, strike: int, t_years: float) -> float:
        return self.black_scholes_call(spot_fair, strike, t_years, self.OPTION_VOL)

    def compute_option_scalp_fair(self, cache: Dict[str, object], symbol: str, book: Dict[str, object]) -> float:
        anchor_key = f"{symbol}_anchor"
        return self.update_anchor(
            cache,
            anchor_key,
            float(book["mid"]),
            float(book["mid"]),
            0.22,
        )

    def compute_smile_fairs(
        self,
        books: Dict[str, Dict[str, object]],
        spot_fair: float,
        t_years: float,
    ) -> Dict[str, float]:
        observations = []
        for symbol, cfg in self.OPTION_CONFIG.items():
            book = books.get(symbol)
            if not book or not book["has_both_sides"]:
                continue
            strike = int(cfg["strike"])
            observed_price = float(book["mid"])
            iv = self.implied_vol(observed_price, spot_fair, strike, t_years)
            if iv is None:
                continue
            moneyness = math.log(strike / spot_fair) / max(math.sqrt(t_years), 1e-6)
            observations.append((moneyness, iv))

        if len(observations) < 3:
            return {
                symbol: self.option_fair(spot_fair, int(cfg["strike"]), t_years)
                for symbol, cfg in self.OPTION_CONFIG.items()
            }

        a, b, c = self.fit_quadratic(observations)
        fairs: Dict[str, float] = {}
        for symbol, cfg in self.OPTION_CONFIG.items():
            strike = int(cfg["strike"])
            moneyness = math.log(strike / spot_fair) / max(math.sqrt(t_years), 1e-6)
            vol = a * moneyness * moneyness + b * moneyness + c
            vol = max(0.05, min(0.90, vol))
            fairs[symbol] = self.black_scholes_call(spot_fair, strike, t_years, vol)
        return fairs

    def implied_vol(self, price: float, spot: float, strike: int, t_years: float) -> float | None:
        intrinsic = max(spot - strike, 0.0)
        if price <= intrinsic + 0.05 or spot <= 0 or strike <= 0 or t_years <= 0:
            return None
        low = 0.01
        high = 1.50
        for _ in range(32):
            mid = (low + high) / 2.0
            model = self.black_scholes_call(spot, strike, t_years, mid)
            if model < price:
                low = mid
            else:
                high = mid
        return (low + high) / 2.0

    def fit_quadratic(self, observations: List[tuple[float, float]]) -> tuple[float, float, float]:
        s0 = float(len(observations))
        s1 = sum(x for x, _ in observations)
        s2 = sum(x * x for x, _ in observations)
        s3 = sum(x * x * x for x, _ in observations)
        s4 = sum(x * x * x * x for x, _ in observations)
        y0 = sum(y for _, y in observations)
        y1 = sum(x * y for x, y in observations)
        y2 = sum(x * x * y for x, y in observations)
        return self.solve_3x3(
            [[s4, s3, s2], [s3, s2, s1], [s2, s1, s0]],
            [y2, y1, y0],
        )

    def solve_3x3(self, matrix: List[List[float]], vector: List[float]) -> tuple[float, float, float]:
        a = [row[:] for row in matrix]
        b = vector[:]
        for col in range(3):
            pivot = max(range(col, 3), key=lambda row: abs(a[row][col]))
            a[col], a[pivot] = a[pivot], a[col]
            b[col], b[pivot] = b[pivot], b[col]
            denom = a[col][col]
            if abs(denom) < 1e-12:
                return 0.0, 0.0, self.OPTION_VOL
            for j in range(col, 3):
                a[col][j] /= denom
            b[col] /= denom
            for row in range(3):
                if row == col:
                    continue
                factor = a[row][col]
                for j in range(col, 3):
                    a[row][j] -= factor * a[col][j]
                b[row] -= factor * b[col]
        return b[0], b[1], b[2]

    def black_scholes_call(self, spot: float, strike: int, t_years: float, sigma: float) -> float:
        if spot <= 0 or strike <= 0:
            return 0.0
        if t_years <= 0 or sigma <= 0:
            return max(spot - strike, 0.0)
        vol_term = sigma * math.sqrt(t_years)
        if vol_term <= 0:
            return max(spot - strike, 0.0)
        d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * t_years) / vol_term
        d2 = d1 - vol_term
        return spot * self.norm_cdf(d1) - strike * self.norm_cdf(d2)

    def black_scholes_delta(self, spot: float, strike: int, t_years: float, sigma: float) -> float:
        if spot <= 0 or strike <= 0:
            return 0.0
        if t_years <= 0 or sigma <= 0:
            return 1.0 if spot > strike else 0.0
        vol_term = sigma * math.sqrt(t_years)
        if vol_term <= 0:
            return 1.0 if spot > strike else 0.0
        d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * t_years) / vol_term
        return self.norm_cdf(d1)

    def norm_cdf(self, x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    def time_to_expiry_years(self, timestamp: int) -> float:
        days_remaining = max(0.25, 4.0 - (timestamp / 1_000_000.0))
        return days_remaining / 365.0

    def mark_flow_signal(
        self,
        cache: Dict[str, object],
        state: TradingState,
        product: str,
        weights: Dict[str, float],
        cache_key: str,
    ) -> float:
        raw_signal = 0.0
        market_trades = getattr(state, "market_trades", {}) or {}
        for trade in market_trades.get(product, []):
            quantity = max(1.0, float(self.trade_attr(trade, "quantity", 1)))
            size_weight = math.sqrt(quantity)
            buyer = self.trade_attr(trade, "buyer", None)
            seller = self.trade_attr(trade, "seller", None)
            if buyer in weights:
                raw_signal += weights[buyer] * size_weight
            if seller in weights:
                raw_signal -= weights[seller] * size_weight

        previous = float(cache.get(cache_key, 0.0))
        updated = 0.55 * previous + raw_signal
        updated = max(-4.0, min(4.0, updated))
        cache[cache_key] = updated
        return updated

    def trade_attr(self, trade, name: str, default):
        if isinstance(trade, dict):
            return trade.get(name, default)
        return getattr(trade, name, default)

    def compute_linear_fair(
        self,
        cache: Dict[str, object],
        key: str,
        history_key: str,
        observed_mid: float,
        default: float,
        smoothing: float,
        imbalance_weight: float,
        deviation_weight: float,
        trend_weight: float,
        imbalance: float,
    ) -> float:
        anchor = self.update_anchor(cache, key, observed_mid, default, smoothing)
        self.push_history(cache, history_key, observed_mid)
        history = cache.get(history_key, [])
        long_avg = sum(history[-20:]) / min(len(history), 20) if history else observed_mid
        short_avg = sum(history[-5:]) / min(len(history), 5) if history else observed_mid
        deviation = long_avg - observed_mid
        trend = short_avg - long_avg
        return anchor + imbalance_weight * imbalance + deviation_weight * deviation + trend_weight * trend

    def book_snapshot(self, depth: OrderDepth) -> Dict[str, object]:
        buy_orders = sorted(depth.buy_orders.items(), reverse=True)
        sell_orders = sorted(depth.sell_orders.items())
        best_bid = buy_orders[0][0] if buy_orders else 0
        best_ask = sell_orders[0][0] if sell_orders else 0
        return {
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid": self.compute_mid(buy_orders, sell_orders),
            "imbalance": self.top_imbalance(buy_orders, sell_orders),
            "has_both_sides": bool(buy_orders) and bool(sell_orders),
        }

    def compute_mid(self, buy_orders: List[tuple], sell_orders: List[tuple]) -> float:
        if buy_orders and sell_orders:
            return (buy_orders[0][0] + sell_orders[0][0]) / 2.0
        if buy_orders:
            return float(buy_orders[0][0])
        if sell_orders:
            return float(sell_orders[0][0])
        return 0.0

    def top_imbalance(self, buy_orders: List[tuple], sell_orders: List[tuple]) -> float:
        if not buy_orders or not sell_orders:
            return 0.0
        bid_volume = max(0, int(buy_orders[0][1]))
        ask_volume = max(0, -int(sell_orders[0][1]))
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

    def update_anchor(self, cache: Dict[str, object], key: str, observed: float, default: float, smoothing: float) -> float:
        current = float(cache.get(key, default))
        updated = (1.0 - smoothing) * current + smoothing * observed
        cache[key] = updated
        return updated

    def ensure_within_hard_limit(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        limit = self.POSITION_LIMITS[product]
        buy_remaining = max(0, limit - position)
        sell_remaining = max(0, limit + position)

        indexed_orders = list(enumerate(orders))
        buys = [(idx, order) for idx, order in indexed_orders if int(order.quantity) > 0]
        sells = [(idx, order) for idx, order in indexed_orders if int(order.quantity) < 0]
        kept: List[tuple[int, Order]] = []

        for idx, order in sorted(buys, key=lambda item: (int(item[1].price), item[0])):
            qty = min(int(order.quantity), buy_remaining)
            if qty > 0:
                kept.append((idx, Order(order.symbol, order.price, qty)))
                buy_remaining -= qty

        for idx, order in sorted(sells, key=lambda item: (-int(item[1].price), item[0])):
            qty = min(-int(order.quantity), sell_remaining)
            if qty > 0:
                kept.append((idx, Order(order.symbol, order.price, -qty)))
                sell_remaining -= qty

        kept.sort(key=lambda item: item[0])
        return [order for _, order in kept]
