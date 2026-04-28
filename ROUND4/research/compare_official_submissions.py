from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_DIR = ROOT / "ROUND4" / "official_submissions"
STRATEGY_DIR = ROOT / "ROUND4" / "strategies"
OUT_DIR = ROOT / "ROUND4" / "research" / "outputs" / "official_feedback"


def read_json_from_artifact(path: Path) -> tuple[dict[str, Any], str | None]:
    if path.is_dir():
        json_path = next(path.glob("*.json"), None)
        if json_path is None:
            raise FileNotFoundError(f"No JSON in {path}")
        return json.loads(json_path.read_text(encoding="utf-8")), None
    with zipfile.ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".json"))
        return json.loads(archive.read(name).decode("utf-8")), name


def read_log_from_artifact(path: Path) -> dict[str, Any] | None:
    if path.is_dir():
        log_path = next(path.glob("*.log"), None)
        if log_path is None:
            return None
        raw = log_path.read_text(encoding="utf-8")
    else:
        with zipfile.ZipFile(path) as archive:
            name = next((n for n in archive.namelist() if n.endswith(".log")), None)
            if name is None:
                return None
            raw = archive.read(name).decode("utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def read_py_hash(path: Path) -> str | None:
    if path.is_dir():
        py_path = next(path.glob("*.py"), None)
        if py_path is None:
            return None
        return hashlib.sha256(py_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        name = next((n for n in archive.namelist() if n.endswith(".py")), None)
        if name is None:
            return None
        return hashlib.sha256(archive.read(name)).hexdigest()


def strategy_hashes() -> dict[str, str]:
    return {hashlib.sha256(path.read_bytes()).hexdigest(): path.name for path in STRATEGY_DIR.glob("round4_candidate_*.py")}


def final_product_pnl(activities_log: str) -> dict[str, float]:
    rows = csv.DictReader(io.StringIO(activities_log), delimiter=";")
    result: dict[str, float] = {}
    for row in rows:
        if int(row["timestamp"]) == 99_900:
            result[row["product"]] = float(row["profit_and_loss"])
    return result


def fill_summary(trade_history: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for trade in trade_history:
        symbol = trade["symbol"]
        quantity = int(trade["quantity"])
        price = float(trade["price"])
        record = result.setdefault(
            symbol,
            {
                "trade_count": 0,
                "buy_qty": 0,
                "sell_qty": 0,
                "buy_notional": 0.0,
                "sell_notional": 0.0,
            },
        )
        record["trade_count"] += 1
        if trade["buyer"] == "SUBMISSION":
            record["buy_qty"] += quantity
            record["buy_notional"] += quantity * price
        elif trade["seller"] == "SUBMISSION":
            record["sell_qty"] += quantity
            record["sell_notional"] += quantity * price
    for record in result.values():
        record["net_pos"] = record["buy_qty"] - record["sell_qty"]
        record["cash"] = record["sell_notional"] - record["buy_notional"]
        record["avg_buy"] = record["buy_notional"] / record["buy_qty"] if record["buy_qty"] else 0.0
        record["avg_sell"] = record["sell_notional"] / record["sell_qty"] if record["sell_qty"] else 0.0
    return result


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
    hashes = strategy_hashes()
    discovered = [p for p in OFFICIAL_DIR.iterdir() if p.is_dir() or p.suffix == ".zip"]
    by_stem: dict[str, Path] = {}
    for artifact in discovered:
        # If both an extracted folder and the original zip exist, prefer the zip:
        # it contains the full official log JSON with tradeHistory.
        current = by_stem.get(artifact.stem)
        if current is None or artifact.suffix == ".zip":
            by_stem[artifact.stem] = artifact
    artifacts = sorted(by_stem.values(), key=lambda p: p.name)

    summary_rows: list[dict[str, Any]] = []
    pnl_rows: list[dict[str, Any]] = []
    fill_rows: list[dict[str, Any]] = []
    loaded: dict[str, dict[str, Any]] = {}

    for artifact in artifacts:
        try:
            data, _ = read_json_from_artifact(artifact)
        except (FileNotFoundError, StopIteration, json.JSONDecodeError, zipfile.BadZipFile):
            continue
        log_data = read_log_from_artifact(artifact)
        py_hash = read_py_hash(artifact)
        strategy = hashes.get(py_hash or "", "")
        submission = artifact.stem
        loaded[submission] = {
            "data": data,
            "log": log_data,
            "strategy": strategy,
            "artifact": artifact.name,
        }
        trade_history = (log_data or {}).get("tradeHistory", [])
        product_pnl = final_product_pnl(data["activitiesLog"])
        fills = fill_summary(trade_history)
        summary_rows.append(
            {
                "submission": submission,
                "artifact": artifact.name,
                "strategy": strategy,
                "status": data.get("status", ""),
                "profit": data.get("profit", ""),
                "trade_count": len(trade_history),
                "activities_lines": len(data.get("activitiesLog", "").splitlines()),
            }
        )
        for product, pnl in sorted(product_pnl.items()):
            pnl_rows.append(
                {
                    "submission": submission,
                    "strategy": strategy,
                    "product": product,
                    "pnl": pnl,
                }
            )
        for product, record in sorted(fills.items()):
            row = {"submission": submission, "strategy": strategy, "product": product}
            row.update(record)
            fill_rows.append(row)

    write_csv(OUT_DIR / "official_submission_summary.csv", summary_rows)
    write_csv(OUT_DIR / "official_product_pnl.csv", pnl_rows)
    write_csv(OUT_DIR / "official_fill_summary.csv", fill_rows)

    baseline = next((row for row in summary_rows if row["strategy"] == "round4_candidate_1_522830_base.py"), None)
    if baseline:
        baseline_name = baseline["submission"]
        baseline_pnl = {
            row["product"]: float(row["pnl"])
            for row in pnl_rows
            if row["submission"] == baseline_name
        }
        delta_rows = []
        for row in pnl_rows:
            if row["submission"] == baseline_name:
                continue
            delta_rows.append(
                {
                    "submission": row["submission"],
                    "strategy": row["strategy"],
                    "product": row["product"],
                    "pnl": row["pnl"],
                    "delta_vs_baseline": float(row["pnl"]) - baseline_pnl.get(row["product"], 0.0),
                }
            )
        write_csv(OUT_DIR / "official_product_delta_vs_baseline.csv", delta_rows)

    markdown = [
        "| Submission | Strategy | Official | Trades |",
        "|---|---|---:|---:|",
    ]
    for row in summary_rows:
        profit = row["profit"]
        official = f"{float(profit):,.2f}" if profit != "" else ""
        markdown.append(f"| `{row['submission']}` | `{row['strategy']}` | {official} | {row['trade_count']} |")
    (OUT_DIR / "official_submission_summary.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
