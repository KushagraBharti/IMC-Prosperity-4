
from datamodel import Order, TradingState
import json
import math

HYDROGEL = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"

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

LIMITS = {HYDROGEL: 200, VFE: 200}
for _p in STRIKES:
    LIMITS[_p] = 300

# Round 4 historical fit using day1/day2/day3 as roughly 7/6/5 days to expiry.
# Live Round 4 starts at 4 days to expiry, so Trader.LIVE_TTE_START_DAYS = 4.0.
SIGMA = {
    4000: 0.5665,
    4500: 0.3301,
    5000: 0.2425,
    5100: 0.2373,
    5200: 0.2428,
    5300: 0.2467,
    5400: 0.2304,
    5500: 0.2497,
    6000: 0.4024,
    6500: 0.6087,
}

ACTIVE_VOUCHERS = ['VEV_4000', 'VEV_4500', 'VEV_5000', 'VEV_5100', 'VEV_5200', 'VEV_5300', 'VEV_5400', 'VEV_5500']
OPTION_EDGE = {4000: 1.1, 4500: 0.9, 5000: 0.9, 5100: 0.8, 5200: 1.25, 5300: 1.0, 5400: 0.85, 5500: 1.0}
OPTION_SIZE = {4000: 14, 4500: 14, 5000: 14, 5100: 16, 5200: 14, 5300: 10, 5400: 10, 5500: 10}

# Counterparty alpha. Positive weight means follow the Mark's signed flow.
# Negative weight means fade the Mark's signed flow.
VFE_MARK_WEIGHTS = {'Mark 67': 0.03, 'Mark 49': -0.026, 'Mark 55': 0.007, 'Mark 14': -0.01, 'Mark 22': -0.012, 'Mark 01': -0.003}
HYDRO_MARK_WEIGHTS = {'Mark 14': 0.009, 'Mark 38': -0.009}
VOUCHER_MARK_WEIGHTS = {'Mark 01': 0.0035, 'Mark 22': -0.0035, 'Mark 14': 0.0025}


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call_price(s: float, k: float, t: float, sigma: float) -> float:
    if s <= 0 or k <= 0:
        return 0.0
    if t <= 0 or sigma <= 0:
        return max(0.0, s - k)
    vol_sqrt_t = sigma * math.sqrt(t)
    if vol_sqrt_t <= 0:
        return max(0.0, s - k)
    d1 = (math.log(s / k) + 0.5 * sigma * sigma * t) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return s * norm_cdf(d1) - k * norm_cdf(d2)


def bs_delta(s: float, k: float, t: float, sigma: float) -> float:
    if s <= 0 or k <= 0:
        return 0.0
    if t <= 0 or sigma <= 0:
        return 1.0 if s > k else 0.0
    vol_sqrt_t = sigma * math.sqrt(t)
    if vol_sqrt_t <= 0:
        return 1.0 if s > k else 0.0
    d1 = (math.log(s / k) + 0.5 * sigma * sigma * t) / vol_sqrt_t
    return norm_cdf(d1)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def get_bids(order_depth):
    return sorted(order_depth.buy_orders.items(), reverse=True)


def get_asks(order_depth):
    return sorted((price, abs(volume)) for price, volume in order_depth.sell_orders.items())


def best_bid(order_depth):
    return max(order_depth.buy_orders.keys()) if order_depth.buy_orders else None


def best_ask(order_depth):
    return min(order_depth.sell_orders.keys()) if order_depth.sell_orders else None


def mid_price(order_depth):
    bb = best_bid(order_depth)
    ba = best_ask(order_depth)
    if bb is not None and ba is not None:
        return (bb + ba) / 2.0
    if bb is not None:
        return float(bb)
    if ba is not None:
        return float(ba)
    return None


def wall_mid_and_imbalance(order_depth):
    bids = get_bids(order_depth)
    asks = get_asks(order_depth)
    m = mid_price(order_depth)
    if not bids or not asks or m is None:
        return m, 0.0
    wall_bid = max(bids, key=lambda x: x[1])[0]
    wall_ask = max(asks, key=lambda x: x[1])[0]
    top_bid_vol = bids[0][1]
    top_ask_vol = asks[0][1]
    denom = top_bid_vol + top_ask_vol
    imbalance = (top_bid_vol - top_ask_vol) / denom if denom > 0 else 0.0
    return (wall_bid + wall_ask) / 2.0, imbalance


def short_long_trend(hist, short_n=4, long_n=18):
    if len(hist) < max(short_n, long_n):
        return 0.0
    s = sum(hist[-short_n:]) / short_n
    l = sum(hist[-long_n:]) / long_n
    return s - l


class OrderBuilder:
    def __init__(self, product: str, position: int, limit: int):
        self.product = product
        self.position = position
        self.limit = limit
        self.orders = []
        self.planned_buy = 0
        self.planned_sell = 0

    def add_buy(self, price: int, qty: int):
        qty = int(qty)
        if qty <= 0:
            return
        cap = self.limit - self.position - self.planned_buy
        if cap <= 0:
            return
        qty = min(qty, cap)
        if qty > 0:
            self.orders.append(Order(self.product, int(price), qty))
            self.planned_buy += qty

    def add_sell(self, price: int, qty: int):
        qty = int(qty)
        if qty <= 0:
            return
        cap = self.limit + self.position - self.planned_sell
        if cap <= 0:
            return
        qty = min(qty, cap)
        if qty > 0:
            self.orders.append(Order(self.product, int(price), -qty))
            self.planned_sell += qty


def voucher_mid(order_depths, product):
    od = order_depths.get(product)
    if od is None:
        return None
    return mid_price(od)


class Trader:
    # Round 4 starts with VEV TTE = 4 days. It decays through the simulation day.
    LIVE_TTE_START_DAYS = 4.0

    # Hydrogel dynamic fair settings, ported from the Round 3 official-family design.
    HYDRO_DEFAULT_FAIR = 9991.0
    HYDRO_ANCHOR_SMOOTH = 0.05
    HYDRO_IMB_WEIGHT = 10.5
    HYDRO_DEVIATION_WEIGHT = 0.04
    HYDRO_TREND_WEIGHT = 0.03
    HYDRO_TAKE_EDGE = 9.0
    HYDRO_MAKER_EDGE = 4.0
    HYDRO_TAKE_SIZE = 70
    HYDRO_QUOTE_SIZE = 64
    HYDRO_FLATTEN_TRIGGER = 140

    # VFE fair settings. Deep vouchers are used as information, not necessarily as inventory targets.
    VFE_ANCHOR = 5260.0
    VFE_ANCHOR_WEIGHT = 0.52
    VFE_TAKE_EDGE = 4.5
    VFE_SKEW = 0.0025
    VFE_TAKE_SIZE = 70
    VFE_PASSIVE_SIZE = 24

    OPTION_INV_SKEW = 0.0025
    OPTION_DELTA_PENALTY = 0.0
    OPTION_SPOT_MARK_MULT = 0.75

    MARK_DECAY_TAU = 8000.0
    VFE_MARK_CAP = 8.0
    HYDRO_MARK_CAP = 5.0
    VOUCHER_MARK_CAP = 2.5
    HISTORY_LIMIT = 40

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        self.decay_cache(cache, state.timestamp)
        self.update_mark_alpha(cache, state)

        result = {}
        positions = state.position

        self.trade_hydrogel(state, result, positions, cache)
        self.trade_vfe(state, result, positions, cache)
        self.trade_vouchers(state, result, positions, cache)

        cache["last_ts"] = state.timestamp
        trader_data = json.dumps(cache, separators=(",", ":"))
        return result, 0, trader_data

    def load_cache(self, trader_data: str):
        if trader_data:
            try:
                cache = json.loads(trader_data)
                if isinstance(cache, dict):
                    return cache
            except Exception:
                pass
        return {
            "last_ts": 0,
            "last_trade_ts": -1,
            "anchors": {},
            "hist": {},
            "mark": {"VFE": 0.0, "HYDRO": 0.0, "VOUCHERS": {}},
        }

    def decay_cache(self, cache, timestamp: int):
        last_ts = cache.get("last_ts", timestamp)
        dt = max(0, timestamp - last_ts)
        if dt <= 0:
            return
        decay = math.exp(-dt / max(1.0, self.MARK_DECAY_TAU))
        mark = cache.setdefault("mark", {"VFE": 0.0, "HYDRO": 0.0, "VOUCHERS": {}})
        mark["VFE"] = mark.get("VFE", 0.0) * decay
        mark["HYDRO"] = mark.get("HYDRO", 0.0) * decay
        vouchers = mark.setdefault("VOUCHERS", {})
        for p in list(vouchers.keys()):
            vouchers[p] *= decay

    def update_mark_alpha(self, cache, state):
        mark_cache = cache.setdefault("mark", {"VFE": 0.0, "HYDRO": 0.0, "VOUCHERS": {}})
        voucher_cache = mark_cache.setdefault("VOUCHERS", {})
        last_trade_ts = cache.get("last_trade_ts", -1)
        max_seen = last_trade_ts

        for product, trades in getattr(state, "market_trades", {}).items():
            for tr in trades:
                ts = getattr(tr, "timestamp", state.timestamp)
                if ts <= last_trade_ts:
                    continue
                max_seen = max(max_seen, ts)
                qty = getattr(tr, "quantity", 0) or 0
                if qty <= 0:
                    continue
                buyer = getattr(tr, "buyer", None)
                seller = getattr(tr, "seller", None)
                for mark, side in ((buyer, 1.0), (seller, -1.0)):
                    if not mark:
                        continue
                    if product == VFE:
                        w = VFE_MARK_WEIGHTS.get(mark, 0.0)
                        if w:
                            mark_cache["VFE"] = clamp(mark_cache.get("VFE", 0.0) + side * qty * w,
                                                        -self.VFE_MARK_CAP, self.VFE_MARK_CAP)
                    elif product == HYDROGEL:
                        w = HYDRO_MARK_WEIGHTS.get(mark, 0.0)
                        if w:
                            mark_cache["HYDRO"] = clamp(mark_cache.get("HYDRO", 0.0) + side * qty * w,
                                                          -self.HYDRO_MARK_CAP, self.HYDRO_MARK_CAP)
                    elif product in STRIKES:
                        w = VOUCHER_MARK_WEIGHTS.get(mark, 0.0)
                        if w:
                            cur = voucher_cache.get(product, 0.0)
                            voucher_cache[product] = clamp(cur + side * qty * w,
                                                           -self.VOUCHER_MARK_CAP, self.VOUCHER_MARK_CAP)
        cache["last_trade_ts"] = max_seen

    def hist_append(self, cache, key: str, value: float):
        hist = cache.setdefault("hist", {}).setdefault(key, [])
        hist.append(float(value))
        if len(hist) > self.HISTORY_LIMIT:
            del hist[:-self.HISTORY_LIMIT]
        return hist

    def add_orders(self, result, product, orders):
        if orders:
            result[product] = result.get(product, []) + orders

    def dynamic_anchor(self, cache, key: str, observed: float, default: float, smoothing: float):
        anchors = cache.setdefault("anchors", {})
        prev = anchors.get(key, default)
        updated = (1.0 - smoothing) * prev + smoothing * observed
        anchors[key] = updated
        return updated

    def trade_hydrogel(self, state, result, positions, cache):
        od = state.order_depths.get(HYDROGEL)
        if od is None:
            return
        m = mid_price(od)
        if m is None:
            return
        wall_mid, imb = wall_mid_and_imbalance(od)
        if wall_mid is None:
            wall_mid = m
        anchor = self.dynamic_anchor(cache, "hydro_anchor", m, self.HYDRO_DEFAULT_FAIR, self.HYDRO_ANCHOR_SMOOTH)
        mid_hist = self.hist_append(cache, "hydro_mid", m)
        trend = short_long_trend(mid_hist, 4, 18)
        mark_alpha = cache.get("mark", {}).get("HYDRO", 0.0)
        fair = anchor + self.HYDRO_IMB_WEIGHT * imb + self.HYDRO_DEVIATION_WEIGHT * (m - anchor) + self.HYDRO_TREND_WEIGHT * trend + mark_alpha

        pos = positions.get(HYDROGEL, 0)
        builder = OrderBuilder(HYDROGEL, pos, LIMITS[HYDROGEL])
        fair_adj = fair - 0.035 * pos

        for ask, vol in get_asks(od):
            edge = fair_adj - ask
            if edge >= self.HYDRO_TAKE_EDGE:
                qty = self.HYDRO_TAKE_SIZE if edge < self.HYDRO_TAKE_EDGE + 4.0 else 2 * self.HYDRO_TAKE_SIZE
                builder.add_buy(ask, min(vol, qty))
        for bid, vol in get_bids(od):
            edge = bid - fair_adj
            if edge >= self.HYDRO_TAKE_EDGE:
                qty = self.HYDRO_TAKE_SIZE if edge < self.HYDRO_TAKE_EDGE + 4.0 else 2 * self.HYDRO_TAKE_SIZE
                builder.add_sell(bid, min(vol, qty))

        bb = best_bid(od)
        ba = best_ask(od)
        if bb is not None and ba is not None:
            # Inventory relief first.
            if pos > self.HYDRO_FLATTEN_TRIGGER:
                builder.add_sell(max(bb, int(math.floor(fair_adj - 2))), min(abs(pos) - self.HYDRO_FLATTEN_TRIGGER + 20, self.HYDRO_TAKE_SIZE))
            elif pos < -self.HYDRO_FLATTEN_TRIGGER:
                builder.add_buy(min(ba, int(math.ceil(fair_adj + 2))), min(abs(pos) - self.HYDRO_FLATTEN_TRIGGER + 20, self.HYDRO_TAKE_SIZE))
            else:
                signal = abs(fair - m)
                if signal >= 1.1:
                    passive_bid = int(min(bb + 1, math.floor(fair_adj - self.HYDRO_MAKER_EDGE)))
                    passive_ask = int(max(ba - 1, math.ceil(fair_adj + self.HYDRO_MAKER_EDGE)))
                    if passive_bid < ba and pos < 160:
                        builder.add_buy(passive_bid, self.HYDRO_QUOTE_SIZE)
                    if passive_ask > bb and pos > -160:
                        builder.add_sell(passive_ask, self.HYDRO_QUOTE_SIZE)

        self.add_orders(result, HYDROGEL, builder.orders)

    def vfe_fair(self, state, cache):
        base = self.VFE_ANCHOR
        deep_vals = []
        m4000 = voucher_mid(state.order_depths, "VEV_4000")
        m4500 = voucher_mid(state.order_depths, "VEV_4500")
        if m4000 is not None:
            deep_vals.append((m4000 + 4000.0, 0.40))
        if m4500 is not None:
            deep_vals.append((m4500 + 4500.0, 0.60))
        if deep_vals:
            implied = sum(v * w for v, w in deep_vals) / sum(w for _, w in deep_vals)
            fair = self.VFE_ANCHOR_WEIGHT * base + (1.0 - self.VFE_ANCHOR_WEIGHT) * implied
        else:
            fair = base
        fair += cache.get("mark", {}).get("VFE", 0.0)
        return fair

    def trade_vfe(self, state, result, positions, cache):
        od = state.order_depths.get(VFE)
        if od is None:
            return
        fair = self.vfe_fair(state, cache)
        pos = positions.get(VFE, 0)
        builder = OrderBuilder(VFE, pos, LIMITS[VFE])
        fair_adj = fair - pos * self.VFE_SKEW

        for ask, vol in get_asks(od):
            if fair_adj - ask >= self.VFE_TAKE_EDGE:
                builder.add_buy(ask, min(vol, self.VFE_TAKE_SIZE))
        for bid, vol in get_bids(od):
            if bid - fair_adj >= self.VFE_TAKE_EDGE:
                builder.add_sell(bid, min(vol, self.VFE_TAKE_SIZE))

        bb = best_bid(od)
        ba = best_ask(od)
        if bb is not None and ba is not None:
            passive_bid = int(min(bb + 1, math.floor(fair_adj - 2)))
            passive_ask = int(max(ba - 1, math.ceil(fair_adj + 2)))
            if passive_bid < ba and pos < 170:
                builder.add_buy(passive_bid, self.VFE_PASSIVE_SIZE)
            if passive_ask > bb and pos > -170:
                builder.add_sell(passive_ask, self.VFE_PASSIVE_SIZE)

        self.add_orders(result, VFE, builder.orders)

    def trade_vouchers(self, state, result, positions, cache):
        s = self.vfe_fair(state, cache)
        od_vfe = state.order_depths.get(VFE)
        if s is None and od_vfe is not None:
            s = mid_price(od_vfe)
        if s is None:
            return
        # VFE Mark flow should affect option spot, but not with full multiplier unless the branch is aggressive.
        s_for_options = s + self.OPTION_SPOT_MARK_MULT * cache.get("mark", {}).get("VFE", 0.0)

        tte_days = max(0.05, self.LIVE_TTE_START_DAYS - state.timestamp / 1_000_000.0)
        t = tte_days / 365.0

        net_delta = positions.get(VFE, 0)
        for product in ACTIVE_VOUCHERS:
            k = STRIKES[product]
            sigma = SIGMA[k]
            net_delta += positions.get(product, 0) * bs_delta(s_for_options, k, t, sigma)

        voucher_marks = cache.get("mark", {}).get("VOUCHERS", {})
        for product in ACTIVE_VOUCHERS:
            od = state.order_depths.get(product)
            if od is None:
                continue
            k = STRIKES[product]
            sigma = SIGMA[k]
            fair = bs_call_price(s_for_options, k, t, sigma)
            delta = bs_delta(s_for_options, k, t, sigma)
            pos = positions.get(product, 0)
            edge_threshold = OPTION_EDGE[k]
            mark_alpha = voucher_marks.get(product, 0.0)
            delta_penalty = self.OPTION_DELTA_PENALTY * net_delta * delta
            fair_adj = fair + mark_alpha - pos * self.OPTION_INV_SKEW - delta_penalty
            builder = OrderBuilder(product, pos, LIMITS[product])

            for ask, vol in get_asks(od):
                edge = fair_adj - ask
                if edge >= edge_threshold:
                    base_qty = OPTION_SIZE[k]
                    qty = base_qty if edge < edge_threshold + 2.0 else 2 * base_qty
                    builder.add_buy(ask, min(vol, qty))

            for bid, vol in get_bids(od):
                edge = bid - fair_adj
                if edge >= edge_threshold:
                    base_qty = OPTION_SIZE[k]
                    qty = base_qty if edge < edge_threshold + 2.0 else 2 * base_qty
                    builder.add_sell(bid, min(vol, qty))

            self.add_orders(result, product, builder.orders)
