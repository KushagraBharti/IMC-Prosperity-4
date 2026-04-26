from datamodel import Order, TradingState

from round3_iterative_2 import Trader as BaseTrader


# Experimental causal approximation of the DP tail-voucher oracle.
# Keeps Iterative 2 for Hydrogel/VFE/VEV_5000/VEV_5100 and replaces weak tail
# voucher handling with broad buy-low/sell-high bands inferred from oracle labels.

BANDS = {
    "VEV_5200": {"buy": 99, "sell": 104, "limit": 300, "size": 100, "levels": 3},
    "VEV_5300": {"buy": 49, "sell": 52, "limit": 300, "size": 100, "levels": 3},
    "VEV_5400": {"buy": 15, "sell": 17, "limit": 300, "size": 100, "levels": 3},
    "VEV_5500": {"buy": 6, "sell": 7, "limit": 300, "size": 60, "levels": 2},
}


def asks(depth):
    return sorted(((int(price), abs(int(volume))) for price, volume in depth.sell_orders.items()))


def bids(depth):
    return sorted(((int(price), int(volume)) for price, volume in depth.buy_orders.items()), reverse=True)


class Trader:
    def __init__(self):
        self.base = BaseTrader()

    def run(self, state: TradingState):
        result, conversions, trader_data = self.base.run(state)

        for product in BANDS:
            result.pop(product, None)
            depth = state.order_depths.get(product)
            if depth is None:
                continue
            pos = state.position.get(product, 0)
            cfg = BANDS[product]
            limit = int(cfg["limit"])
            size = int(cfg["size"])
            levels = int(cfg["levels"])
            buy_cap = max(0, limit - pos)
            sell_cap = max(0, limit + pos)
            orders = []

            for price, volume in asks(depth)[:levels]:
                if buy_cap <= 0:
                    break
                if price <= int(cfg["buy"]):
                    qty = min(size, volume, buy_cap)
                    if qty > 0:
                        orders.append(Order(product, price, qty))
                        buy_cap -= qty

            for price, volume in bids(depth)[:levels]:
                if sell_cap <= 0:
                    break
                if price >= int(cfg["sell"]):
                    qty = min(size, volume, sell_cap)
                    if qty > 0:
                        orders.append(Order(product, price, -qty))
                        sell_cap -= qty

            if orders:
                result[product] = orders

        return result, conversions, trader_data
