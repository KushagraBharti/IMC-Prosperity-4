from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_trade_history(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".log" and text.lstrip().startswith("{"):
        payload = json.loads(text)
        return payload.get("tradeHistory", []) or []

    if path.suffix.lower() == ".json":
        payload = json.loads(text)
        return payload.get("tradeHistory", []) or []

    marker = "Trade History:\n"
    if marker not in text:
        return []

    blob = text.split(marker, 1)[1].strip()
    return json.loads(blob)


def load_quotes(round_dir: Path, round_number: int, day: int) -> dict[int, dict[str, tuple[int | None, int | None]]]:
    price_path = round_dir / f"prices_round_{round_number}_day_{day}.csv"
    quotes: dict[int, dict[str, tuple[int | None, int | None]]] = defaultdict(dict)

    with price_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            timestamp = int(row["timestamp"])
            product = row["product"]

            best_bid = None
            best_ask = None
            if row.get("bid_price_1"):
                best_bid = int(float(row["bid_price_1"]))
            if row.get("ask_price_1"):
                best_ask = int(float(row["ask_price_1"]))

            quotes[timestamp][product] = (best_bid, best_ask)

    return quotes


def infer_side(trade: dict[str, Any]) -> str:
    buyer = trade.get("buyer", "")
    seller = trade.get("seller", "")
    if buyer == "SUBMISSION":
        return "buy"
    if seller == "SUBMISSION":
        return "sell"
    return "unknown"


def classify_fill(price: int, side: str, best_bid: int | None, best_ask: int | None) -> str:
    if best_bid is None or best_ask is None:
        return "missing_book_side"

    if side == "buy":
        if price >= best_ask:
            return "touch_or_cross_ask"
        if best_bid < price < best_ask:
            return "inside_spread"
        if price <= best_bid:
            return "at_or_below_bid"
    elif side == "sell":
        if price <= best_bid:
            return "touch_or_cross_bid"
        if best_bid < price < best_ask:
            return "inside_spread"
        if price >= best_ask:
            return "at_or_above_ask"
    return "unclassified"


def summarize(trades: list[dict[str, Any]], quotes: dict[int, dict[str, tuple[int | None, int | None]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "trade_count": 0,
        "by_product": {},
    }

    product_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    side_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for trade in trades:
        symbol = trade["symbol"]
        timestamp = int(trade["timestamp"])
        price = int(float(trade["price"]))
        side = infer_side(trade)
        best_bid, best_ask = quotes.get(timestamp, {}).get(symbol, (None, None))
        bucket = classify_fill(price, side, best_bid, best_ask)

        product_counts[symbol][bucket] += 1
        side_counts[symbol][side] += 1
        summary["trade_count"] += 1

    for product in sorted(product_counts):
        summary["by_product"][product] = {
            "side_counts": dict(sorted(side_counts[product].items())),
            "fill_buckets": dict(sorted(product_counts[product].items())),
        }

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify Prosperity own trades against the displayed spread.")
    parser.add_argument("artifact", help="Path to an official bundle log/json or local backtester log.")
    parser.add_argument("--round-dir", required=True, help="Round directory containing prices/trades CSVs, e.g. ROUND1")
    parser.add_argument("--round-number", required=True, type=int, help="Round number, e.g. 1")
    parser.add_argument("--day", required=True, type=int, help="Day number to load price quotes for")
    args = parser.parse_args()

    artifact = Path(args.artifact)
    trades = parse_trade_history(artifact)
    quotes = load_quotes(Path(args.round_dir), args.round_number, args.day)
    summary = summarize(trades, quotes)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
