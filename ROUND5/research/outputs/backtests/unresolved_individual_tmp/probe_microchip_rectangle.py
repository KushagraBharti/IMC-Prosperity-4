
from __future__ import annotations
import json, math
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
    PRODUCT = "MICROCHIP_RECTANGLE"
    MODE = "reversal"
    LOOKBACK = 100
    THRESHOLD = 0.95
    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        book = self.book(state, self.PRODUCT)
        if not book:
            return result, 0, json.dumps(cache, separators=(",", ":"))
        hist = self.push(cache, self.PRODUCT, book["mid"], 230)
        if len(hist) <= self.LOOKBACK + 2:
            result[self.PRODUCT] = []
            return result, 0, json.dumps(cache, separators=(",", ":"))
        signal = (hist[-1] - hist[-1 - self.LOOKBACK]) / max(self.vol(hist[-140:]), 1.0)
        if self.MODE == "reversal":
            signal = -signal
        signal += 0.08 * book["imb"]
        result[self.PRODUCT] = self.trade(book, state.position.get(self.PRODUCT, 0), signal)
        return result, 0, json.dumps(cache, separators=(",", ":"))
    def trade(self, book: dict, pos: int, signal: float) -> List[Order]:
        if abs(signal) < self.THRESHOLD:
            return []
        if signal > 0 and pos < self.LIMIT:
            price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
            return [Order(self.PRODUCT, price, self.LIMIT - pos if signal > self.THRESHOLD + 0.9 else min(6, self.LIMIT - pos))]
        if signal < 0 and pos > -self.LIMIT:
            price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
            return [Order(self.PRODUCT, price, -(self.LIMIT + pos if signal < -self.THRESHOLD - 0.9 else min(6, self.LIMIT + pos)))]
        return []
    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid, ask = max(d.buy_orders), min(d.sell_orders)
        bv, av = max(0, d.buy_orders[bid]), max(0, -d.sell_orders[ask])
        total = bv + av
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid, "imb": 0.0 if total == 0 else (bv - av) / total}
    def push(self, cache: dict, product: str, mid: float, keep: int) -> List[float]:
        hist = cache.get(product, [])
        if not isinstance(hist, list): hist = []
        hist.append(float(mid)); cache[product] = hist[-keep:]; return cache[product]
    def vol(self, hist: List[float]) -> float:
        if len(hist) < 3: return 1.0
        diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
        m = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - m) ** 2 for x in diffs) / len(diffs)))
    def load_cache(self, raw: str) -> dict:
        try: return json.loads(raw) if raw else {}
        except Exception: return {}
