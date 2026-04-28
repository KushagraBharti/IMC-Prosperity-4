from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND4"
OUT_DIR = ROUND_DIR / "research" / "outputs" / "post40_mark_inventory"

PRODUCTS = [
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

STATIC_SHORTS = {"VEV_4000", "VEV_4500", "VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500"}
ACTIVE_MIDS = {"VEV_5000", "VEV_5100"}
HORIZONS = [500, 1000, 5000, 10000, 20000, 40000]
SEGMENTS = {
    "pre40": lambda ts: ts < 40_000,
    "transition": lambda ts: 38_000 <= ts <= 43_000,
    "post40": lambda ts: ts >= 40_000,
    "late": lambda ts: ts >= 60_000,
}


def read_prices() -> dict[tuple[int, str], dict[int, float]]:
    mids: dict[tuple[int, str], dict[int, float]] = defaultdict(dict)
    for path in sorted(ROUND_DIR.glob("prices_round_4_day_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter=";"):
                mids[(int(row["day"]), row["product"])][int(row["timestamp"])] = float(row["mid_price"])
    return mids


def read_trades() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(ROUND_DIR.glob("trades_round_4_day_*.csv")):
        day = int(path.stem.rsplit("_", 1)[1])
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter=";"):
                rows.append(
                    {
                        "day": day,
                        "timestamp": int(row["timestamp"]),
                        "product": row["symbol"],
                        "buyer": row["buyer"],
                        "seller": row["seller"],
                        "price": float(row["price"]),
                        "quantity": int(row["quantity"]),
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sign_agreement(values: list[float], total: float) -> float:
    if not values:
        return 0.0
    overall = 1 if total >= 0 else -1
    return sum(1 for value in values if (1 if value >= 0 else -1) == overall) / len(values)


def mark_scores(mids: dict[tuple[int, str], dict[int, float]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    totals = defaultdict(float)
    quantities = defaultdict(float)
    events = Counter()
    day_totals = defaultdict(float)
    day_qty = defaultdict(float)

    for trade in trades:
        product = str(trade["product"])
        if product not in PRODUCTS:
            continue
        day = int(trade["day"])
        ts = int(trade["timestamp"])
        base = mids[(day, product)].get(ts)
        if base is None:
            continue
        participants = [(str(trade["buyer"]), 1), (str(trade["seller"]), -1)]
        for segment, pred in SEGMENTS.items():
            if not pred(ts):
                continue
            for horizon in HORIZONS:
                future = mids[(day, product)].get(ts + horizon)
                if future is None:
                    continue
                future_ret = future - base
                for mark, side in participants:
                    key = (segment, product, horizon, mark)
                    value = side * int(trade["quantity"]) * future_ret
                    totals[key] += value
                    quantities[key] += int(trade["quantity"])
                    events[key] += 1
                    day_totals[(*key, day)] += value
                    day_qty[(*key, day)] += int(trade["quantity"])

    rows = []
    for key, total in totals.items():
        segment, product, horizon, mark = key
        qty = quantities[key]
        if qty <= 0:
            continue
        day_scores = []
        days = 0
        for day in [1, 2, 3]:
            dq = day_qty.get((*key, day), 0.0)
            if dq > 0:
                days += 1
                day_scores.append(day_totals[(*key, day)] / dq)
        rows.append(
            {
                "segment": segment,
                "product": product,
                "horizon": horizon,
                "mark": mark,
                "events": events[key],
                "quantity": qty,
                "score": total / qty,
                "total_signed_markout": total,
                "days": days,
                "sign_agreement": sign_agreement(day_scores, total),
                "family": "static_short" if product in STATIC_SHORTS else "active_mid" if product in ACTIVE_MIDS else "far_otm",
            }
        )
    return sorted(rows, key=lambda row: (row["segment"], row["product"], int(row["horizon"]), row["mark"]))


def pair_scores(mids: dict[tuple[int, str], dict[int, float]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    totals = defaultdict(float)
    quantities = defaultdict(float)
    events = Counter()
    for trade in trades:
        product = str(trade["product"])
        if product not in PRODUCTS:
            continue
        day = int(trade["day"])
        ts = int(trade["timestamp"])
        base = mids[(day, product)].get(ts)
        if base is None:
            continue
        for segment, pred in SEGMENTS.items():
            if not pred(ts):
                continue
            for horizon in HORIZONS:
                future = mids[(day, product)].get(ts + horizon)
                if future is None:
                    continue
                key = (segment, product, horizon, str(trade["buyer"]), str(trade["seller"]))
                totals[key] += int(trade["quantity"]) * (future - base)
                quantities[key] += int(trade["quantity"])
                events[key] += 1
    rows = []
    for key, total in totals.items():
        segment, product, horizon, buyer, seller = key
        qty = quantities[key]
        rows.append(
            {
                "segment": segment,
                "product": product,
                "horizon": horizon,
                "buyer": buyer,
                "seller": seller,
                "events": events[key],
                "quantity": qty,
                "buyer_direction_score": total / qty if qty else 0.0,
                "family": "static_short" if product in STATIC_SHORTS else "active_mid" if product in ACTIVE_MIDS else "far_otm",
            }
        )
    return sorted(rows, key=lambda row: (row["segment"], row["product"], int(row["horizon"]), row["buyer"], row["seller"]))


def recommended_weights(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["segment"] not in {"post40", "late"}:
            continue
        if int(row["horizon"]) not in {5000, 10000, 20000}:
            continue
        if int(row["events"]) < 8:
            continue
        if float(row["days"]) < 2:
            continue
        if float(row["sign_agreement"]) < 0.5:
            continue
        grouped[(str(row["segment"]), str(row["product"]), str(row["mark"]))].append(row)

    out = []
    for (segment, product, mark), items in grouped.items():
        weighted = sum(float(item["score"]) * math.sqrt(float(item["quantity"])) for item in items)
        denom = sum(math.sqrt(float(item["quantity"])) for item in items)
        score = weighted / denom if denom else 0.0
        if abs(score) < 0.35:
            continue
        out.append(
            {
                "segment": segment,
                "product": product,
                "mark": mark,
                "recommended_weight": round(max(-2.0, min(2.0, score / 2.0)), 4),
                "avg_score": score,
                "evidence_rows": len(items),
                "total_events": sum(int(item["events"]) for item in items),
                "family": "static_short" if product in STATIC_SHORTS else "active_mid" if product in ACTIVE_MIDS else "far_otm",
            }
        )
    return sorted(out, key=lambda row: (row["segment"], row["product"], -abs(float(row["recommended_weight"]))))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mids = read_prices()
    trades = read_trades()
    score_rows = mark_scores(mids, trades)
    pair_rows = pair_scores(mids, trades)
    weight_rows = recommended_weights(score_rows)
    write_csv(OUT_DIR / "post40_mark_scores.csv", score_rows)
    write_csv(OUT_DIR / "post40_pair_scores.csv", pair_rows)
    write_csv(OUT_DIR / "recommended_post40_weights.csv", weight_rows)

    md = [
        "# Post-40k Mark Inventory Analysis",
        "",
        "Purpose: use Marks to manage stale voucher inventory after the opening repricing has saturated positions.",
        "",
        "## Recommended Weights",
        "",
        "| Segment | Product | Mark | Weight | Avg Score | Events | Family |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in weight_rows[:80]:
        md.append(
            f"| `{row['segment']}` | `{row['product']}` | `{row['mark']}` | {row['recommended_weight']:.4f} | "
            f"{float(row['avg_score']):.4f} | {row['total_events']} | {row['family']} |"
        )
    md.extend(
        [
            "",
            "Interpretation: positive weight means Mark buying predicts higher future voucher mid; if we are short, it is a cover signal. Negative weight means Mark buying predicts lower future voucher mid; if we are short, it is a hold/re-short signal.",
            "",
            "Use this as a research signal, not a final production table; sparse rows still need portal validation.",
        ]
    )
    (OUT_DIR / "post40_mark_inventory_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
