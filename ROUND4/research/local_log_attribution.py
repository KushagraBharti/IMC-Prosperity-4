from __future__ import annotations

import argparse
import csv
import io
import json
from collections import defaultdict
from pathlib import Path


PRODUCTS = [
    "HYDROGEL_PACK",
    "VELVETFRUIT_EXTRACT",
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

BLOCKS = [(0, 20_000), (20_000, 40_000), (40_000, 60_000), (60_000, 80_000), (80_000, 100_000)]


def nearest(timestamps: list[int], target: int) -> int:
    return min(timestamps, key=lambda ts: abs(ts - target))


def parse_log(path: Path) -> tuple[list[int], dict[int, dict[str, float]], list[dict[str, object]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    pnl: dict[int, dict[str, float]] = defaultdict(dict)
    for row in csv.DictReader(io.StringIO(data["activitiesLog"]), delimiter=";"):
        pnl[int(row["timestamp"])][row["product"]] = float(row["profit_and_loss"])
    trades = data.get("tradeHistory", [])
    seen = set()
    own = []
    for trade in trades:
        if trade.get("buyer") != "SUBMISSION" and trade.get("seller") != "SUBMISSION":
            continue
        # Kevin logs can include the same fill once with an empty counterparty and
        # once with the resolved Mark. Ignore counterparty for position counting.
        key = (trade.get("timestamp"), trade.get("symbol"), trade.get("price"), trade.get("quantity"), trade.get("buyer") == "SUBMISSION")
        if key in seen:
            continue
        seen.add(key)
        own.append(trade)
    return sorted(pnl), pnl, own


def summarize(path: Path) -> None:
    timestamps, pnl, own = parse_log(path)
    final_ts = timestamps[-1]
    print(f"\n{path}")
    print("product,final,max,max_ts,post40,trades_post40,final_pos")
    positions = {product: 0 for product in PRODUCTS}
    trades_by_ts: dict[int, list[dict[str, object]]] = defaultdict(list)
    for trade in own:
        trades_by_ts[int(trade["timestamp"])].append(trade)
    pos_by_ts: dict[int, dict[str, int]] = {}
    for ts in timestamps:
        for trade in trades_by_ts.get(ts, []):
            product = str(trade["symbol"])
            qty = int(trade["quantity"])
            if trade.get("buyer") == "SUBMISSION":
                positions[product] += qty
            elif trade.get("seller") == "SUBMISSION":
                positions[product] -= qty
        pos_by_ts[ts] = dict(positions)

    ts40 = nearest(timestamps, 40_000)
    for product in PRODUCTS:
        series = {ts: pnl[ts].get(product, 0.0) for ts in timestamps}
        max_ts = max(timestamps, key=lambda ts: series[ts])
        post40_trades = sum(1 for t in own if t.get("symbol") == product and int(t["timestamp"]) >= 40_000)
        print(
            f"{product},{series[final_ts]:.2f},{series[max_ts]:.2f},{max_ts},"
            f"{series[final_ts] - series[ts40]:.2f},{post40_trades},{pos_by_ts[final_ts].get(product, 0)}"
        )

    total = {ts: sum(pnl[ts].values()) for ts in timestamps}
    print("block,total_delta")
    for start, end in BLOCKS:
        a = nearest(timestamps, start)
        b = nearest(timestamps, end)
        print(f"{start}-{end},{total[b] - total[a]:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+")
    args = parser.parse_args()
    for raw in args.logs:
        summarize(Path(raw))


if __name__ == "__main__":
    main()
