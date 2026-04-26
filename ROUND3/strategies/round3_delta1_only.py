from datamodel import Order, TradingState
import json
import math

# Round 3 combined strategy:
# 1) HYDROGEL_PACK stable-fair spread capture
# 2) VELVETFRUIT_EXTRACT stable/deep-option-implied fair spread capture
# 3) VEV voucher Black-Scholes relative-value taker
# Designed to be active-fill heavy, with only light passive quoting on delta-1 products.

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
for p in STRIKES:
    LIMITS[p] = 300

# Fitted from historical days 0/1/2 using decaying TTE and 365-day convention.
# 4000/4500 are deep ITM and 6000/6500 are near-dead; active trading focuses on 5000-5500.
SIGMA = {
    4000: 0.5244,
    4500: 0.3056,
    5000: 0.2419,
    5100: 0.24035,
    5200: 0.24215,
    5300: 0.24455,
    5400: 0.22960,
    5500: 0.24845,
    6000: 0.3775,
    6500: 0.5701,
}

# Active option subset. 5300 was noisier in replay; 6000/6500 are basically dead.
ACTIVE_VOUCHERS = ["VEV_5000", "VEV_5100", "VEV_5200", "VEV_5400", "VEV_5500"]

# Thresholds are edge versus best ask/bid, not edge versus mid.
OPTION_EDGE = {
    5000: 0.50,
    5100: 0.50,
    5200: 0.50,
    5300: 1.25,
    5400: 0.50,
    5500: 0.50,
}


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
    # Prosperity sell volumes are negative in TradingState.
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
    # Delta-1 product settings from historical active-fill replay.
    HYDROGEL_FAIR = 10005.0
    HYDROGEL_TAKE_EDGE = 12.0
    HYDROGEL_SKEW = 0.04
    HYDROGEL_TAKE_SIZE = 25
    HYDROGEL_PASSIVE_SIZE = 8

    VFE_ANCHOR = 5255.0
    VFE_ANCHOR_WEIGHT = 0.70
    VFE_TAKE_EDGE = 7.0
    VFE_SKEW = 0.03
    VFE_TAKE_SIZE = 25
    VFE_PASSIVE_SIZE = 6

    OPTION_INV_SKEW = 0.004
    OPTION_SIZE = 40

    def run(self, state: TradingState):
        result = {}
        positions = state.position

        self.trade_hydrogel(state, result, positions)
        self.trade_vfe(state, result, positions)

        trader_data = ""
        conversions = 0
        return result, conversions, trader_data

    def add_orders(self, result, product, orders):
        if orders:
            result[product] = result.get(product, []) + orders

    def trade_hydrogel(self, state, result, positions):
        od = state.order_depths.get(HYDROGEL)
        if od is None:
            return
        m = mid_price(od)
        if m is None:
            return
        wall_mid, imb = wall_mid_and_imbalance(od)
        pos = positions.get(HYDROGEL, 0)
        builder = OrderBuilder(HYDROGEL, pos, LIMITS[HYDROGEL])

        micro_adj = clamp(0.06 * (m - self.HYDROGEL_FAIR) + 0.15 * (wall_mid - m) + 2.0 * imb, -5.0, 5.0)
        fair = self.HYDROGEL_FAIR + micro_adj
        fair_adj = fair - pos * self.HYDROGEL_SKEW

        for ask, vol in get_asks(od):
            edge = fair_adj - ask
            if edge >= self.HYDROGEL_TAKE_EDGE:
                qty = self.HYDROGEL_TAKE_SIZE if edge < self.HYDROGEL_TAKE_EDGE + 5 else 2 * self.HYDROGEL_TAKE_SIZE
                builder.add_buy(ask, min(vol, qty))

        for bid, vol in get_bids(od):
            edge = bid - fair_adj
            if edge >= self.HYDROGEL_TAKE_EDGE:
                qty = self.HYDROGEL_TAKE_SIZE if edge < self.HYDROGEL_TAKE_EDGE + 5 else 2 * self.HYDROGEL_TAKE_SIZE
                builder.add_sell(bid, min(vol, qty))

        # Light passive quotes. These are not required for edge; they are upside if bots cross us.
        bb = best_bid(od)
        ba = best_ask(od)
        if bb is not None and ba is not None:
            passive_bid = int(min(bb + 1, math.floor(fair_adj - 6)))
            passive_ask = int(max(ba - 1, math.ceil(fair_adj + 6)))
            if passive_bid < ba and pos < 150:
                builder.add_buy(passive_bid, self.HYDROGEL_PASSIVE_SIZE)
            if passive_ask > bb and pos > -150:
                builder.add_sell(passive_ask, self.HYDROGEL_PASSIVE_SIZE)

        self.add_orders(result, HYDROGEL, builder.orders)

    def vfe_fair(self, state):
        od = state.order_depths.get(VFE)
        if od is None:
            return None
        base = self.VFE_ANCHOR
        deep_vals = []
        m4000 = voucher_mid(state.order_depths, "VEV_4000")
        m4500 = voucher_mid(state.order_depths, "VEV_4500")
        if m4000 is not None:
            deep_vals.append((m4000 + 4000.0, 0.25))
        if m4500 is not None:
            deep_vals.append((m4500 + 4500.0, 0.35))
        if deep_vals:
            implied = sum(v * w for v, w in deep_vals) / sum(w for _, w in deep_vals)
            return self.VFE_ANCHOR_WEIGHT * base + (1.0 - self.VFE_ANCHOR_WEIGHT) * implied
        return base

    def trade_vfe(self, state, result, positions):
        od = state.order_depths.get(VFE)
        if od is None:
            return
        fair = self.vfe_fair(state)
        if fair is None:
            return
        pos = positions.get(VFE, 0)
        builder = OrderBuilder(VFE, pos, LIMITS[VFE])
        fair_adj = fair - pos * self.VFE_SKEW

        for ask, vol in get_asks(od):
            if fair_adj - ask >= self.VFE_TAKE_EDGE:
                builder.add_buy(ask, min(vol, self.VFE_TAKE_SIZE))

        for bid, vol in get_bids(od):
            if bid - fair_adj >= self.VFE_TAKE_EDGE:
                builder.add_sell(bid, min(vol, self.VFE_TAKE_SIZE))

        # Light passive VFE quotes. Smaller than Hydrogel because VFE is the option underlying.
        bb = best_bid(od)
        ba = best_ask(od)
        if bb is not None and ba is not None:
            passive_bid = int(min(bb + 1, math.floor(fair_adj - 2)))
            passive_ask = int(max(ba - 1, math.ceil(fair_adj + 2)))
            if passive_bid < ba and pos < 140:
                builder.add_buy(passive_bid, self.VFE_PASSIVE_SIZE)
            if passive_ask > bb and pos > -140:
                builder.add_sell(passive_ask, self.VFE_PASSIVE_SIZE)

        self.add_orders(result, VFE, builder.orders)

    def trade_vouchers(self, state, result, positions):
        s = self.vfe_fair(state)
        if s is None:
            od = state.order_depths.get(VFE)
            s = mid_price(od) if od is not None else None
        if s is None:
            return

        # Round 3 starts at TTE 5d and decays throughout the simulation day.
        tte_days = max(0.05, 5.0 - state.timestamp / 1_000_000.0)
        t = tte_days / 365.0

        # Net option delta is used only as a soft risk penalty, not as a full hedge.
        net_delta = positions.get(VFE, 0)
        for product in ACTIVE_VOUCHERS:
            k = STRIKES[product]
            sigma = SIGMA[k]
            net_delta += positions.get(product, 0) * bs_delta(s, k, t, sigma)

        for product in ACTIVE_VOUCHERS:
            od = state.order_depths.get(product)
            if od is None:
                continue
            k = STRIKES[product]
            sigma = SIGMA[k]
            fair = bs_call_price(s, k, t, sigma)
            delta = bs_delta(s, k, t, sigma)
            pos = positions.get(product, 0)
            edge_threshold = OPTION_EDGE[k]

            # Inventory and soft delta penalties stop runaway same-direction option loading.
            delta_penalty = 0.0015 * net_delta * delta
            fair_adj = fair - pos * self.OPTION_INV_SKEW - delta_penalty

            builder = OrderBuilder(product, pos, LIMITS[product])

            for ask, vol in get_asks(od):
                edge = fair_adj - ask
                if edge >= edge_threshold:
                    qty = self.OPTION_SIZE if edge < edge_threshold + 2.0 else 2 * self.OPTION_SIZE
                    builder.add_buy(ask, min(vol, qty))

            for bid, vol in get_bids(od):
                edge = bid - fair_adj
                if edge >= edge_threshold:
                    qty = self.OPTION_SIZE if edge < edge_threshold + 2.0 else 2 * self.OPTION_SIZE
                    builder.add_sell(bid, min(vol, qty))

            self.add_orders(result, product, builder.orders)
