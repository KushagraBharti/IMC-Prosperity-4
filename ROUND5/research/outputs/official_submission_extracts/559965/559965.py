from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List

try:
    from datamodel import Order, TradingState
except ImportError:
    @dataclass
    class Order:
        symbol: str
        price: int
        quantity: int

    @dataclass
    class TradingState:
        order_depths: Dict[str, object]
        position: Dict[str, int] = field(default_factory=dict)
        traderData: str = ""


class Trader:
    LIMIT = 10
    PRODUCTS = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        orders: Dict[str, List[Order]] = {}
        books = {p: self.book(state, p) for p in self.PRODUCTS}
        mids = {p: b["mid"] for p, b in books.items() if b}

        anchors = cache.setdefault("anchors", {})
        for product, mid in mids.items():
            anchors.setdefault(product, mid)
            anchors[product] = 0.999 * float(anchors[product]) + 0.001 * mid

        if len(mids) >= 4:
            normalized = {p: mids[p] / max(float(anchors[p]), 1.0) for p in mids}
            factor = sum(normalized.values()) / len(normalized)
            for product in self.PRODUCTS:
                book = books.get(product)
                if not book or product not in normalized:
                    continue
                residual = normalized[product] - factor
                stat = self.update_stat(cache, "resid_" + product, residual, 0.035)
                z = 0.0 if stat["var"] <= 1e-12 else (residual - stat["mean"]) / math.sqrt(stat["var"])

                # Conservative factor-residual mean reversion. Prefer taking clear dislocations,
                # otherwise place one inside-spread quote in the reversion direction.
                pos = state.position.get(product, 0)
                signal = -z
                min_abs = 1.15 if product in {"PEBBLES_XL", "PEBBLES_XS", "PEBBLES_L"} else 1.55
                size = 2 if abs(z) < 2.0 else 3
                orders[product] = self.trade_signal(product, book, pos, signal, min_abs, size, take=False)

        return orders, 0, json.dumps(cache, separators=(",", ":"))

    def trade_signal(self, product: str, book: dict, pos: int, signal: float, threshold: float, size: int, take: bool) -> List[Order]:
        if abs(signal) < threshold:
            return self.flatten_if_stale(product, book, pos)
        result: List[Order] = []
        spread = book["ask"] - book["bid"]
        buy_room = self.LIMIT - pos
        sell_room = self.LIMIT + pos
        inv_skew = pos / self.LIMIT
        if signal > 0 and buy_room > 0:
            qty = min(size, buy_room)
            px = book["ask"] if take and spread <= 8 and signal > threshold + 0.8 else min(book["bid"] + 1, book["ask"] - 1)
            if px < book["ask"] or take:
                result.append(Order(product, int(px), int(qty)))
        elif signal < 0 and sell_room > 0:
            qty = min(size, sell_room)
            px = book["bid"] if take and spread <= 8 and -signal > threshold + 0.8 else max(book["ask"] - 1, book["bid"] + 1)
            if px > book["bid"] or take:
                result.append(Order(product, int(px), int(-qty)))
        if abs(pos) >= 8 and abs(signal) < threshold + 0.3:
            result.extend(self.flatten_if_stale(product, book, pos))
        return self.clamp(product, pos, result)

    def flatten_if_stale(self, product: str, book: dict, pos: int) -> List[Order]:
        if pos >= 7:
            return [Order(product, book["bid"], -min(2, pos))]
        if pos <= -7:
            return [Order(product, book["ask"], min(2, -pos))]
        return []

    def book(self, state: TradingState, product: str):
        depth = state.order_depths.get(product)
        if not depth or not depth.buy_orders or not depth.sell_orders:
            return None
        bid = max(depth.buy_orders)
        ask = min(depth.sell_orders)
        bid_vol = max(0, depth.buy_orders[bid])
        ask_vol = max(0, -depth.sell_orders[ask])
        total = bid_vol + ask_vol
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "imb": 0.0 if total == 0 else (bid_vol - ask_vol) / total}

    def update_stat(self, cache: dict, key: str, value: float, alpha: float) -> dict:
        stat = cache.setdefault(key, {"mean": value, "var": 1e-8})
        old = float(stat["mean"])
        mean = (1.0 - alpha) * old + alpha * value
        var = (1.0 - alpha) * float(stat["var"]) + alpha * (value - old) * (value - old)
        stat["mean"] = mean
        stat["var"] = max(var, 1e-10)
        return stat

    def clamp(self, product: str, pos: int, orders: List[Order]) -> List[Order]:
        buy = self.LIMIT - pos
        sell = self.LIMIT + pos
        out: List[Order] = []
        for order in orders:
            qty = int(order.quantity)
            if qty > 0:
                q = min(qty, buy)
                buy -= q
                if q > 0:
                    out.append(Order(product, order.price, q))
            elif qty < 0:
                q = min(-qty, sell)
                sell -= q
                if q > 0:
                    out.append(Order(product, order.price, -q))
        return out

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}