from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analyze_fill_patterns import parse_trade_history


def normalize_submission_fills(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for trade in trades:
        buyer = trade.get("buyer", "")
        seller = trade.get("seller", "")
        if buyer == "SUBMISSION":
            side = "buy"
        elif seller == "SUBMISSION":
            side = "sell"
        else:
            continue

        normalized.append(
            {
                "timestamp": int(trade["timestamp"]),
                "symbol": trade["symbol"],
                "side": side,
                "price": int(float(trade["price"])),
                "quantity": int(trade["quantity"]),
            }
        )

    return normalized


def trade_key(trade: dict[str, Any]) -> tuple[int, str, str, int, int]:
    return (
        trade["timestamp"],
        trade["symbol"],
        trade["side"],
        trade["price"],
        trade["quantity"],
    )


def aggregate_by_timestamp(trades: list[dict[str, Any]]) -> dict[int, Counter]:
    grouped: dict[int, Counter] = defaultdict(Counter)
    for trade in trades:
        grouped[trade["timestamp"]][trade_key(trade)[1:]] += 1
    return grouped


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare submission fill sequences between two Prosperity artifacts.")
    parser.add_argument("reference", help="Reference artifact, usually official .log")
    parser.add_argument("candidate", help="Candidate artifact, usually a local backtester log")
    parser.add_argument("--show", type=int, default=12, help="Number of differing timestamps to print")
    args = parser.parse_args()

    reference_path = Path(args.reference)
    candidate_path = Path(args.candidate)

    reference_trades = normalize_submission_fills(parse_trade_history(reference_path))
    candidate_trades = normalize_submission_fills(parse_trade_history(candidate_path))

    output: dict[str, Any] = {
        "reference_path": str(reference_path),
        "candidate_path": str(candidate_path),
        "reference_trade_count": len(reference_trades),
        "candidate_trade_count": len(candidate_trades),
    }

    first_mismatch = None
    for index, (left, right) in enumerate(zip(reference_trades, candidate_trades)):
        if trade_key(left) != trade_key(right):
            first_mismatch = {
                "index": index,
                "reference": left,
                "candidate": right,
            }
            break

    if first_mismatch is None and len(reference_trades) != len(candidate_trades):
        if len(reference_trades) > len(candidate_trades):
            first_mismatch = {
                "index": len(candidate_trades),
                "reference": reference_trades[len(candidate_trades)],
                "candidate": None,
            }
        else:
            first_mismatch = {
                "index": len(reference_trades),
                "reference": None,
                "candidate": candidate_trades[len(reference_trades)],
            }

    output["first_mismatch"] = first_mismatch

    reference_counts = aggregate_by_timestamp(reference_trades)
    candidate_counts = aggregate_by_timestamp(candidate_trades)
    timestamps = sorted(set(reference_counts) | set(candidate_counts))

    differing_timestamps: list[dict[str, Any]] = []
    for timestamp in timestamps:
        if reference_counts.get(timestamp, Counter()) == candidate_counts.get(timestamp, Counter()):
            continue

        ref_only = reference_counts.get(timestamp, Counter()) - candidate_counts.get(timestamp, Counter())
        cand_only = candidate_counts.get(timestamp, Counter()) - reference_counts.get(timestamp, Counter())

        differing_timestamps.append(
            {
                "timestamp": timestamp,
                "reference_only": [
                    {
                        "symbol": symbol,
                        "side": side,
                        "price": price,
                        "quantity": quantity,
                        "count": count,
                    }
                    for (symbol, side, price, quantity), count in sorted(ref_only.items())
                ],
                "candidate_only": [
                    {
                        "symbol": symbol,
                        "side": side,
                        "price": price,
                        "quantity": quantity,
                        "count": count,
                    }
                    for (symbol, side, price, quantity), count in sorted(cand_only.items())
                ],
            }
        )

    output["differing_timestamp_count"] = len(differing_timestamps)
    output["differing_timestamps"] = differing_timestamps[: args.show]

    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
