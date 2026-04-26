from datamodel import Order, TradingState
from pathlib import Path
import csv

from round3_iterative_2 import Trader as BaseTrader


# EXPERIMENTAL / NON-SUBMIT-SAFE.
# Uses the current Iterative 2 strategy everywhere except tail vouchers, where it
# replays the DP oracle schedule from the known portal-window data. This isolates
# the amount of edge we are missing in VEV_5200/5300/5400/5500.

TAIL_PRODUCTS = {"VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500"}


def load_tail_schedule():
    project_root = Path(__file__).resolve().parents[2]
    oracle_dir = project_root / "outputs" / "dp_oracle" / "round3_portal_window_v1"
    schedule = {}
    for product in TAIL_PRODUCTS:
        path = oracle_dir / f"{product.lower()}_oracle_trades.csv"
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                ts = int(float(row["timestamp"]))
                qty = int(float(row["qty"]))
                if qty:
                    schedule.setdefault(ts, {})[product] = qty
    return schedule


SCHEDULE = load_tail_schedule()


def asks(depth):
    return sorted(((int(price), abs(int(volume))) for price, volume in depth.sell_orders.items()))


def bids(depth):
    return sorted(((int(price), int(volume)) for price, volume in depth.buy_orders.items()), reverse=True)


class Trader:
    def __init__(self):
        self.base = BaseTrader()

    def run(self, state: TradingState):
        result, conversions, trader_data = self.base.run(state)

        for product in TAIL_PRODUCTS:
            result.pop(product, None)

        actions = SCHEDULE.get(int(state.timestamp), {})
        for product, target_qty in actions.items():
            depth = state.order_depths.get(product)
            if depth is None:
                continue
            remaining = abs(int(target_qty))
            orders = []
            if target_qty > 0:
                for price, volume in asks(depth):
                    if remaining <= 0:
                        break
                    qty = min(remaining, volume)
                    if qty > 0:
                        orders.append(Order(product, price, qty))
                        remaining -= qty
            else:
                for price, volume in bids(depth):
                    if remaining <= 0:
                        break
                    qty = min(remaining, volume)
                    if qty > 0:
                        orders.append(Order(product, price, -qty))
                        remaining -= qty
            if orders:
                result[product] = orders

        return result, conversions, trader_data
