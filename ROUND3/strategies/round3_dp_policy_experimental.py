from datamodel import Order, TradingState
import json
import math


LIMITS = {
    "HYDROGEL_PACK": 200,
    "VELVETFRUIT_EXTRACT": 200,
    "VEV_5000": 300,
    "VEV_5100": 300,
    "VEV_5200": 300,
    "VEV_5300": 300,
    "VEV_5400": 300,
    "VEV_5500": 300,
}


# Distilled from DP oracle schedules:
# buy zones: mid below long average and short average below long average
# sell zones: mid above long average and short average above long average
CONFIG = {
    "HYDROGEL_PACK": {
        "default": 9991.0,
        "edge": 8.0,
        "entry_z": 1.15,
        "size": 60,
        "mr": 0.65,
        "anti_trend": 0.45,
        "imb": 3.0,
        "skew": 0.020,
        "max_levels": 2,
    },
    "VELVETFRUIT_EXTRACT": {
        "default": 5260.0,
        "edge": 4.0,
        "entry_z": 1.10,
        "size": 45,
        "mr": 0.75,
        "anti_trend": 0.45,
        "imb": 1.5,
        "skew": 0.015,
        "max_levels": 2,
    },
    "VEV_5000": {"default": 265.0, "edge": 1.4, "entry_z": 1.15, "size": 50, "mr": 0.90, "anti_trend": 0.55, "imb": 0.2, "skew": 0.000, "max_levels": 2},
    "VEV_5100": {"default": 174.0, "edge": 1.3, "entry_z": 1.15, "size": 50, "mr": 0.95, "anti_trend": 0.55, "imb": 0.2, "skew": 0.000, "max_levels": 2},
    "VEV_5200": {"default": 101.0, "edge": 1.1, "entry_z": 1.15, "size": 50, "mr": 1.00, "anti_trend": 0.60, "imb": 0.1, "skew": 0.000, "max_levels": 2},
    "VEV_5300": {"default": 50.0, "edge": 0.9, "entry_z": 1.20, "size": 45, "mr": 1.10, "anti_trend": 0.60, "imb": 0.1, "skew": 0.000, "max_levels": 2},
    "VEV_5400": {"default": 16.0, "edge": 0.7, "entry_z": 1.20, "size": 40, "mr": 1.25, "anti_trend": 0.65, "imb": 0.0, "skew": 0.000, "max_levels": 2},
    "VEV_5500": {"default": 6.5, "edge": 0.9, "entry_z": 1.35, "size": 25, "mr": 1.10, "anti_trend": 0.60, "imb": 0.0, "skew": 0.000, "max_levels": 1},
}


HISTORY_LIMIT = 64


def bids(depth):
    return sorted(((int(price), int(volume)) for price, volume in depth.buy_orders.items()), reverse=True)


def asks(depth):
    return sorted(((int(price), abs(int(volume))) for price, volume in depth.sell_orders.items()))


def mid_price(depth):
    bs = bids(depth)
    az = asks(depth)
    if bs and az:
        return (bs[0][0] + az[0][0]) / 2.0
    if bs:
        return float(bs[0][0])
    if az:
        return float(az[0][0])
    return None


def imbalance(depth):
    bs = bids(depth)
    az = asks(depth)
    if not bs or not az:
        return 0.0
    total = bs[0][1] + az[0][1]
    if total <= 0:
        return 0.0
    return (bs[0][1] - az[0][1]) / total


def load_cache(raw):
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def push_history(cache, product, value):
    key = "h_" + product
    hist = cache.get(key, [])
    if not isinstance(hist, list):
        hist = []
    hist.append(float(value))
    if len(hist) > HISTORY_LIMIT:
        hist = hist[-HISTORY_LIMIT:]
    cache[key] = hist
    return hist


class Trader:
    def run(self, state: TradingState):
        cache = load_cache(state.traderData)
        result = {}

        for product, cfg in CONFIG.items():
            depth = state.order_depths.get(product)
            if depth is None:
                continue
            m = mid_price(depth)
            if m is None:
                continue
            hist = push_history(cache, product, m)
            orders = self.trade_product(product, depth, state.position.get(product, 0), hist, cfg)
            if orders:
                result[product] = orders

        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade_product(self, product, depth, position, hist, cfg):
        bs = bids(depth)
        az = asks(depth)
        if not bs or not az:
            return []

        long_window = min(len(hist), 20)
        short_window = min(len(hist), 5)
        long_avg = sum(hist[-20:]) / long_window if long_window else float(cfg["default"])
        short_avg = sum(hist[-5:]) / short_window if short_window else long_avg
        variance = sum((x - long_avg) * (x - long_avg) for x in hist[-20:]) / long_window if long_window else 0.0
        stdev = max(math.sqrt(variance), 0.5)
        m = (bs[0][0] + az[0][0]) / 2.0
        dev = long_avg - m
        trend = short_avg - long_avg
        z = dev / stdev
        trend_z = trend / stdev

        fair = (
            long_avg
            + float(cfg["mr"]) * dev
            - float(cfg["anti_trend"]) * trend
            + float(cfg["imb"]) * imbalance(depth)
            - float(cfg["skew"]) * position
        )

        limit = LIMITS[product]
        buy_cap = max(0, limit - position)
        sell_cap = max(0, limit + position)
        edge_threshold = float(cfg["edge"])
        entry_z = float(cfg["entry_z"])
        size = int(cfg["size"])
        max_levels = int(cfg["max_levels"])
        orders = []
        buy_regime = z >= entry_z and trend_z <= 0.20
        sell_regime = z <= -entry_z and trend_z >= -0.20

        for price, volume in az[:max_levels]:
            if buy_cap <= 0:
                break
            edge = fair - price
            if buy_regime and edge >= edge_threshold:
                qty = size if edge < edge_threshold * 2.5 else size * 2
                qty = min(qty, volume, buy_cap)
                if qty > 0:
                    orders.append(Order(product, price, qty))
                    buy_cap -= qty

        for price, volume in bs[:max_levels]:
            if sell_cap <= 0:
                break
            edge = price - fair
            if sell_regime and edge >= edge_threshold:
                qty = size if edge < edge_threshold * 2.5 else size * 2
                qty = min(qty, volume, sell_cap)
                if qty > 0:
                    orders.append(Order(product, price, -qty))
                    sell_cap -= qty

        # If inventory is near the hard limit and the signal has crossed neutral,
        # force a partial unwind instead of waiting for full edge confirmation.
        planned = position + sum(o.quantity for o in orders)
        neutral_band = max(0.8, edge_threshold * 0.5)
        if planned > int(0.80 * limit) and bs:
            if z < 0.25 or fair < m + neutral_band:
                qty = min(planned - int(0.55 * limit), bs[0][1])
                if qty > 0:
                    orders.append(Order(product, bs[0][0], -qty))
        elif planned < -int(0.80 * limit) and az:
            if z > -0.25 or fair > m - neutral_band:
                qty = min(-planned - int(0.55 * limit), az[0][1])
                if qty > 0:
                    orders.append(Order(product, az[0][0], qty))

        return orders
