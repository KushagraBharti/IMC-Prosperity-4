from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_DIR = ROOT / "ROUND4" / "official_submissions"
STRATEGY_DIR = ROOT / "ROUND4" / "strategies"
OUT_DIR = ROOT / "ROUND4" / "research" / "outputs" / "official_plateau"

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

LIMITS = {
    "HYDROGEL_PACK": 200,
    "VELVETFRUIT_EXTRACT": 200,
    "VEV_4000": 300,
    "VEV_4500": 300,
    "VEV_5000": 300,
    "VEV_5100": 300,
    "VEV_5200": 300,
    "VEV_5300": 300,
    "VEV_5400": 300,
    "VEV_5500": 300,
    "VEV_6000": 300,
    "VEV_6500": 300,
}

CHECKPOINTS = [0, 10_000, 20_000, 30_000, 40_000, 41_000, 50_000, 60_000, 70_000, 80_000, 85_000, 90_000, 99_900]


def artifact_candidates() -> list[Path]:
    discovered = [p for p in OFFICIAL_DIR.iterdir() if p.is_dir() or p.suffix == ".zip"]
    by_stem: dict[str, Path] = {}
    for artifact in discovered:
        current = by_stem.get(artifact.stem)
        if current is None or artifact.suffix == ".zip":
            by_stem[artifact.stem] = artifact
    return sorted(by_stem.values(), key=lambda p: p.name)


def read_zip_member(path: Path, suffix: str) -> bytes | None:
    with zipfile.ZipFile(path) as archive:
        name = next((n for n in archive.namelist() if n.endswith(suffix)), None)
        if name is None:
            return None
        return archive.read(name)


def read_artifact_json(path: Path, suffix: str) -> dict[str, Any] | None:
    if path.is_dir():
        member = next(path.glob(f"*{suffix}"), None)
        if member is None:
            return None
        return json.loads(member.read_text(encoding="utf-8"))
    raw = read_zip_member(path, suffix)
    return json.loads(raw.decode("utf-8")) if raw else None


def read_artifact_py_hash(path: Path) -> str | None:
    if path.is_dir():
        member = next(path.glob("*.py"), None)
        if member is None:
            return None
        return hashlib.sha256(member.read_bytes()).hexdigest()
    raw = read_zip_member(path, ".py")
    return hashlib.sha256(raw).hexdigest() if raw else None


def strategy_hashes() -> dict[str, str]:
    return {hashlib.sha256(path.read_bytes()).hexdigest(): path.name for path in STRATEGY_DIR.glob("round4_candidate_*.py")}


def parse_activities(activities_log: str) -> tuple[list[int], dict[int, dict[str, float]], dict[int, dict[str, float]]]:
    pnl_by_ts: dict[int, dict[str, float]] = defaultdict(dict)
    mid_by_ts: dict[int, dict[str, float]] = defaultdict(dict)
    rows = csv.DictReader(io.StringIO(activities_log), delimiter=";")
    for row in rows:
        ts = int(row["timestamp"])
        product = row["product"]
        pnl_by_ts[ts][product] = float(row["profit_and_loss"])
        mid_by_ts[ts][product] = float(row["mid_price"])
    return sorted(pnl_by_ts), pnl_by_ts, mid_by_ts


def total_series(timestamps: list[int], product_pnl: dict[int, dict[str, float]]) -> dict[int, float]:
    return {ts: sum(product_pnl[ts].values()) for ts in timestamps}


def nearest_ts(timestamps: list[int], checkpoint: int) -> int:
    return min(timestamps, key=lambda ts: abs(ts - checkpoint))


def own_trades(log_data: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for trade in log_data.get("tradeHistory", []):
        if trade.get("buyer") == "SUBMISSION" or trade.get("seller") == "SUBMISSION":
            result.append(trade)
    return result


def position_timeline(timestamps: list[int], trades: list[dict[str, Any]]) -> dict[int, dict[str, int]]:
    trades_by_ts: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        trades_by_ts[int(trade["timestamp"])].append(trade)
    positions = {product: 0 for product in PRODUCTS}
    out: dict[int, dict[str, int]] = {}
    for ts in timestamps:
        for trade in trades_by_ts.get(ts, []):
            product = trade["symbol"]
            quantity = int(trade["quantity"])
            if trade["buyer"] == "SUBMISSION":
                positions[product] += quantity
            elif trade["seller"] == "SUBMISSION":
                positions[product] -= quantity
        out[ts] = dict(positions)
    return out


def fill_counts(trades: list[dict[str, Any]], cutoff: int = 40_000) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for product in PRODUCTS:
        result[product] = {
            "trades_pre40": 0,
            "trades_post40": 0,
            "buy_pre40": 0,
            "buy_post40": 0,
            "sell_pre40": 0,
            "sell_post40": 0,
            "cash_pre40": 0.0,
            "cash_post40": 0.0,
        }
    for trade in trades:
        product = trade["symbol"]
        if product not in result:
            continue
        ts = int(trade["timestamp"])
        price = float(trade["price"])
        quantity = int(trade["quantity"])
        segment = "pre40" if ts <= cutoff else "post40"
        result[product][f"trades_{segment}"] += 1
        if trade["buyer"] == "SUBMISSION":
            result[product][f"buy_{segment}"] += quantity
            result[product][f"cash_{segment}"] -= price * quantity
        elif trade["seller"] == "SUBMISSION":
            result[product][f"sell_{segment}"] += quantity
            result[product][f"cash_{segment}"] += price * quantity
    return result


def interval_delta(series: dict[int, float], timestamps: list[int], start: int, end: int) -> float:
    a = nearest_ts(timestamps, start)
    b = nearest_ts(timestamps, end)
    return series[b] - series[a]


def rolling_windows(series: dict[int, float], timestamps: list[int], width: int, min_start: int = 0) -> list[dict[str, float]]:
    rows = []
    ts_set = set(timestamps)
    for start in timestamps:
        if start < min_start:
            continue
        end = start + width
        if end in ts_set:
            rows.append({"start": start, "end": end, "delta": series[end] - series[start]})
    return rows


def drawdown(series: dict[int, float], timestamps: list[int]) -> tuple[float, int, int]:
    peak = -math.inf
    peak_ts = timestamps[0]
    worst = 0.0
    worst_start = timestamps[0]
    worst_end = timestamps[0]
    for ts in timestamps:
        value = series[ts]
        if value > peak:
            peak = value
            peak_ts = ts
        dd = peak - value
        if dd > worst:
            worst = dd
            worst_start = peak_ts
            worst_end = ts
    return worst, worst_start, worst_end


def role_for_product(product: str, final_pnl: float, post40_delta: float, trades_post40: float, final_pos: int) -> str:
    if product in {"VEV_6000", "VEV_6500"} and abs(final_pnl) < 100:
        return "dead optionality / no realized edge"
    if abs(final_pnl) < 1_000 and trades_post40 <= 2:
        return "flat / underused"
    if final_pnl > 8_000 and post40_delta >= 0:
        return "core contributor"
    if final_pnl > 8_000 and post40_delta < 0:
        return "core early contributor, post-40k drag"
    if post40_delta < -500:
        return "post-40k drag"
    if trades_post40 == 0 and abs(final_pos) >= 0.95 * LIMITS.get(product, 10**9):
        return "saturated inventory hold"
    if final_pnl > 2_000:
        return "secondary contributor"
    return "low contribution"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    hashes = strategy_hashes()
    summary_rows = []
    checkpoint_rows = []
    product_rows = []
    segment_rows = []
    window_rows = []
    transition_rows = []
    transition_product_rows = []
    position_checkpoint_rows = []
    mid_checkpoint_rows = []

    for artifact in artifact_candidates():
        data = read_artifact_json(artifact, ".json")
        log_data = read_artifact_json(artifact, ".log")
        if data is None or log_data is None:
            continue
        strategy = hashes.get(read_artifact_py_hash(artifact) or "", "")
        submission = artifact.stem
        timestamps, product_pnl, product_mid = parse_activities(data["activitiesLog"])
        totals = total_series(timestamps, product_pnl)
        trades = own_trades(log_data)
        positions = position_timeline(timestamps, trades)
        fills = fill_counts(trades)

        ts40 = nearest_ts(timestamps, 40_000)
        final_ts = timestamps[-1]
        final_total = totals[final_ts]
        total_40 = totals[ts40]
        first_70 = next((ts for ts in timestamps if totals[ts] >= 70_000), None)
        first_95_final = next((ts for ts in timestamps if totals[ts] >= 0.95 * final_total), None)
        max_ts = max(timestamps, key=lambda ts: totals[ts])
        min_ts = min(timestamps, key=lambda ts: totals[ts])
        worst_dd, dd_start, dd_end = drawdown(totals, timestamps)
        post40_values = [totals[ts] for ts in timestamps if ts >= ts40]

        summary_rows.append(
            {
                "submission": submission,
                "strategy": strategy,
                "official_profit": data.get("profit"),
                "final_total": final_total,
                "total_at_40000": total_40,
                "pre40_delta": total_40 - totals[timestamps[0]],
                "post40_delta": final_total - total_40,
                "post40_max": max(post40_values),
                "post40_min": min(post40_values),
                "post40_range": max(post40_values) - min(post40_values),
                "first_ts_ge_70000": first_70,
                "first_ts_ge_95pct_final": first_95_final,
                "max_total": totals[max_ts],
                "max_total_ts": max_ts,
                "min_total": totals[min_ts],
                "min_total_ts": min_ts,
                "max_drawdown": worst_dd,
                "max_drawdown_start": dd_start,
                "max_drawdown_end": dd_end,
                "own_trade_count": len(trades),
            }
        )

        for checkpoint in CHECKPOINTS:
            ts = nearest_ts(timestamps, checkpoint)
            row = {
                "submission": submission,
                "strategy": strategy,
                "checkpoint": checkpoint,
                "timestamp": ts,
                "total": totals[ts],
            }
            for product in PRODUCTS:
                row[product] = product_pnl[ts].get(product, 0.0)
            checkpoint_rows.append(row)
            mid_row = {
                "submission": submission,
                "strategy": strategy,
                "checkpoint": checkpoint,
                "timestamp": ts,
            }
            for product in PRODUCTS:
                mid_row[product] = product_mid[ts].get(product, 0.0)
            mid_checkpoint_rows.append(mid_row)

        for checkpoint in [35_000, 38_000, 39_000, 40_000, 40_500, 41_000, 41_500, 42_000, 45_000, 50_000, 60_000, 70_000, 80_000, 85_000, 90_000, 99_900]:
            ts = nearest_ts(timestamps, checkpoint)
            row = {
                "submission": submission,
                "strategy": strategy,
                "checkpoint": checkpoint,
                "timestamp": ts,
                "total": totals[ts],
            }
            for product in PRODUCTS:
                row[product] = positions[ts].get(product, 0)
            position_checkpoint_rows.append(row)

        for checkpoint in range(38_000, 43_001, 500):
            ts = nearest_ts(timestamps, checkpoint)
            transition_rows.append(
                {
                    "submission": submission,
                    "strategy": strategy,
                    "checkpoint": checkpoint,
                    "timestamp": ts,
                    "total": totals[ts],
                    "delta_100": totals[ts] - totals.get(ts - 100, totals[ts]),
                    "delta_500": totals[ts] - totals.get(ts - 500, totals[ts]),
                }
            )

        start_ts = nearest_ts(timestamps, 40_000)
        end_ts = nearest_ts(timestamps, 41_000)
        for product in PRODUCTS:
            transition_product_rows.append(
                {
                    "submission": submission,
                    "strategy": strategy,
                    "product": product,
                    "pnl_40000": product_pnl[start_ts].get(product, 0.0),
                    "pnl_41000": product_pnl[end_ts].get(product, 0.0),
                    "delta_40000_41000": product_pnl[end_ts].get(product, 0.0) - product_pnl[start_ts].get(product, 0.0),
                    "pos_40000": positions[start_ts].get(product, 0),
                    "pos_41000": positions[end_ts].get(product, 0),
                    "mid_40000": product_mid[start_ts].get(product, 0.0),
                    "mid_41000": product_mid[end_ts].get(product, 0.0),
                }
            )

        for start in range(0, 100_000, 10_000):
            end = min(start + 10_000, final_ts)
            row = {
                "submission": submission,
                "strategy": strategy,
                "start": start,
                "end": end,
                "total_delta": interval_delta(totals, timestamps, start, end),
            }
            for product in PRODUCTS:
                product_series = {ts: product_pnl[ts].get(product, 0.0) for ts in timestamps}
                row[product] = interval_delta(product_series, timestamps, start, end)
            segment_rows.append(row)

        for width in [5_000, 10_000, 20_000]:
            windows = rolling_windows(totals, timestamps, width, min_start=40_000)
            if windows:
                best = max(windows, key=lambda row: row["delta"])
                worst = min(windows, key=lambda row: row["delta"])
                window_rows.append({"submission": submission, "strategy": strategy, "width": width, "kind": "best", **best})
                window_rows.append({"submission": submission, "strategy": strategy, "width": width, "kind": "worst", **worst})

        for product in PRODUCTS:
            series = {ts: product_pnl[ts].get(product, 0.0) for ts in timestamps}
            final_pnl = series[final_ts]
            at40 = series[ts40]
            pos_at40 = positions[ts40].get(product, 0)
            final_pos = positions[final_ts].get(product, 0)
            limit = LIMITS[product]
            sat_pre = sum(1 for ts in timestamps if ts <= ts40 and abs(positions[ts].get(product, 0)) >= limit)
            sat_post = sum(1 for ts in timestamps if ts > ts40 and abs(positions[ts].get(product, 0)) >= limit)
            product_rows.append(
                {
                    "submission": submission,
                    "strategy": strategy,
                    "product": product,
                    "pnl_at_40000": at40,
                    "final_pnl": final_pnl,
                    "post40_delta": final_pnl - at40,
                    "max_pnl": max(series.values()),
                    "max_pnl_ts": max(timestamps, key=lambda ts: series[ts]),
                    "min_pnl": min(series.values()),
                    "min_pnl_ts": min(timestamps, key=lambda ts: series[ts]),
                    "pos_at_40000": pos_at40,
                    "final_pos": final_pos,
                    "limit": limit,
                    "sat_ticks_pre40": sat_pre,
                    "sat_ticks_post40": sat_post,
                    **fills[product],
                    "role": role_for_product(product, final_pnl, final_pnl - at40, fills[product]["trades_post40"], final_pos),
                }
            )

    write_csv(OUT_DIR / "submission_plateau_summary.csv", summary_rows)
    write_csv(OUT_DIR / "checkpoint_pnl.csv", checkpoint_rows)
    write_csv(OUT_DIR / "product_edge_report.csv", product_rows)
    write_csv(OUT_DIR / "tenk_segment_pnl.csv", segment_rows)
    write_csv(OUT_DIR / "post40_rolling_windows.csv", window_rows)
    write_csv(OUT_DIR / "transition_38k_43k.csv", transition_rows)
    write_csv(OUT_DIR / "transition_product_40k_41k.csv", transition_product_rows)
    write_csv(OUT_DIR / "position_checkpoints.csv", position_checkpoint_rows)
    write_csv(OUT_DIR / "mid_checkpoints.csv", mid_checkpoint_rows)

    baseline = next((row for row in summary_rows if row["strategy"] == "round4_candidate_1_522830_base.py" and row["submission"].startswith("524123")), None)
    if baseline is None:
        baseline = next((row for row in summary_rows if row["strategy"] == "round4_candidate_1_522830_base.py"), None)
    candidate = next((row for row in summary_rows if row["strategy"] == "round4_candidate_2_option9_hydrofairoff.py"), None)
    baseline_submission = baseline["submission"] if baseline else ""

    md = [
        "# Round 4 Official Plateau Analysis",
        "",
        "## Submission Summary",
        "",
        "| Submission | Strategy | Final | At 40k | Pre-40k | Post-40k | First >=70k | Max | Max TS | Drawdown |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        md.append(
            f"| `{row['submission']}` | `{row['strategy']}` | {row['final_total']:,.2f} | {row['total_at_40000']:,.2f} | "
            f"{row['pre40_delta']:,.2f} | {row['post40_delta']:,.2f} | {row['first_ts_ge_70000']} | "
            f"{row['max_total']:,.2f} | {row['max_total_ts']} | {row['max_drawdown']:,.2f} |"
        )

    if baseline and candidate:
        md.extend(
            [
                "",
                "## First Conclusions",
                "",
                f"- Baseline reaches {baseline['total_at_40000']:,.0f} by timestamp 40,000 and ends at {baseline['final_total']:,.0f}. Post-40k net improvement is only {baseline['post40_delta']:,.0f}.",
                f"- Candidate 2 reaches {candidate['total_at_40000']:,.0f} by timestamp 40,000 and ends at {candidate['final_total']:,.0f}. Post-40k net improvement is only {candidate['post40_delta']:,.0f}.",
                "- The chart plateau is real in the official logs: most of the final score is earned before or around 40k, then the strategy spends the rest of the session marking inventory with limited new edge.",
                "- Candidate 2 and candidate 3 have the same official trade history, so they are one live behavior for diagnosis.",
            ]
        )

    md.extend(
        [
            "",
            "## Baseline 38k-43k Transition",
            "",
            "| Timestamp | Total | Delta 100 | Delta 500 |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in transition_rows:
        if row["submission"] == baseline_submission:
            md.append(f"| {row['timestamp']} | {row['total']:,.2f} | {row['delta_100']:,.2f} | {row['delta_500']:,.2f} |")

    md.extend(
        [
            "",
            "## Baseline Product Delta From 40k To 41k",
            "",
            "| Product | PnL 40k | PnL 41k | Delta | Pos 40k | Pos 41k | Mid 40k | Mid 41k |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in transition_product_rows:
        if row["submission"] == baseline_submission:
            md.append(
                f"| `{row['product']}` | {row['pnl_40000']:,.2f} | {row['pnl_41000']:,.2f} | {row['delta_40000_41000']:,.2f} | "
                f"{row['pos_40000']} | {row['pos_41000']} | {row['mid_40000']:,.2f} | {row['mid_41000']:,.2f} |"
            )

    md.extend(
        [
            "",
            "## Baseline Product Edge Report",
            "",
            "| Product | PnL 40k | Final PnL | Post-40k | Pos 40k | Final Pos | Post-40k Trades | Role |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in product_rows:
        if row["submission"] == baseline_submission:
            md.append(
                f"| `{row['product']}` | {row['pnl_at_40000']:,.2f} | {row['final_pnl']:,.2f} | {row['post40_delta']:,.2f} | "
                f"{row['pos_at_40000']} | {row['final_pos']} | {row['trades_post40']} | {row['role']} |"
            )

    md.extend(
        [
            "",
            "## Files",
            "",
            "- `submission_plateau_summary.csv`: high-level plateau metrics.",
            "- `checkpoint_pnl.csv`: total and product PnL at fixed timestamps.",
            "- `product_edge_report.csv`: product-level PnL, inventory, saturation, and fills.",
            "- `tenk_segment_pnl.csv`: PnL by 10k timestamp block.",
            "- `post40_rolling_windows.csv`: best/worst post-40k rolling windows.",
            "- `transition_38k_43k.csv`: exact transition around the jump into the plateau.",
            "- `transition_product_40k_41k.csv`: product attribution for the key 40k to 41k jump.",
            "- `position_checkpoints.csv`: position snapshots through the plateau.",
            "- `mid_checkpoints.csv`: market mid snapshots at the same checkpoints.",
        ]
    )
    (OUT_DIR / "plateau_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
