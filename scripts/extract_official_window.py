from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_activities_log(blob: str) -> list[dict[str, str]]:
    lines = [line for line in blob.splitlines() if line.strip()]
    reader = csv.DictReader(lines, delimiter=";")
    return list(reader)


def infer_day(rows: list[dict[str, str]]) -> int:
    days = {int(row["day"]) for row in rows}
    if len(days) != 1:
        raise ValueError(f"Expected exactly one day in activities log, found {sorted(days)}")
    return next(iter(days))


def write_prices(rows: list[dict[str, str]], round_number: int, output_dir: Path) -> Path:
    day = infer_day(rows)
    output_path = output_dir / f"prices_round_{round_number}_day_{day}.csv"
    fieldnames = [
        "day",
        "timestamp",
        "product",
        "bid_price_1",
        "bid_volume_1",
        "bid_price_2",
        "bid_volume_2",
        "bid_price_3",
        "bid_volume_3",
        "ask_price_1",
        "ask_volume_1",
        "ask_price_2",
        "ask_volume_2",
        "ask_price_3",
        "ask_volume_3",
        "mid_price",
        "profit_and_loss",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def filter_public_trades(source_round_dir: Path, round_number: int, day: int, max_timestamp: int, output_dir: Path) -> Path:
    source_path = source_round_dir / f"trades_round_{round_number}_day_{day}.csv"
    output_path = output_dir / f"trades_round_{round_number}_day_{day}.csv"

    with source_path.open("r", encoding="utf-8", newline="") as source_handle:
        reader = csv.DictReader(source_handle, delimiter=";")
        rows = [row for row in reader if int(row["timestamp"]) <= max_timestamp]
        fieldnames = reader.fieldnames

    if fieldnames is None:
        raise ValueError(f"Could not read header from {source_path}")

    with output_path.open("w", encoding="utf-8", newline="") as output_handle:
        writer = csv.DictWriter(output_handle, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract an official Prosperity submission window into local CSVs.")
    parser.add_argument("artifact", help="Path to official submission .log or .json")
    parser.add_argument("--round-number", required=True, type=int, help="Round number, e.g. 1")
    parser.add_argument(
        "--source-round-dir",
        required=True,
        help="Directory containing the public prices/trades CSVs for that round, e.g. ROUND1",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write the extracted prices/trades CSVs into",
    )
    parser.add_argument(
        "--metadata-path",
        help="Optional path to write extraction metadata JSON. Defaults to <output-dir>/metadata.json",
    )
    args = parser.parse_args()

    artifact = Path(args.artifact)
    payload = load_payload(artifact)
    activities = payload.get("activitiesLog")
    if not activities:
        raise ValueError(f"{artifact} does not contain activitiesLog")

    rows = parse_activities_log(activities)
    if not rows:
        raise ValueError(f"{artifact} activitiesLog is empty")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    day = infer_day(rows)
    timestamps = sorted(int(row["timestamp"]) for row in rows)
    max_timestamp = timestamps[-1]

    prices_path = write_prices(rows, args.round_number, output_dir)
    trades_path = filter_public_trades(
        source_round_dir=Path(args.source_round_dir),
        round_number=args.round_number,
        day=day,
        max_timestamp=max_timestamp,
        output_dir=output_dir,
    )

    metadata = {
        "artifact": str(artifact),
        "round_number": args.round_number,
        "day": day,
        "row_count": len(rows),
        "timestamp_min": timestamps[0],
        "timestamp_max": max_timestamp,
        "prices_path": str(prices_path),
        "trades_path": str(trades_path),
        "reported_profit": payload.get("profit"),
    }

    metadata_path = Path(args.metadata_path) if args.metadata_path else (output_dir / "metadata.json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
