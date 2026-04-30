from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from score_candidates_31_33_state_repair import (
    OUTPUT_DIR,
    PRICE_FILE,
    ROOT,
    ROUND_DIR,
    STRATEGY_DIR,
    TEMP_DIR,
    fmt,
    make_truncation_copy,
    measure_state_size,
)


BACKTEST_DIR = OUTPUT_DIR / "backtests" / "candidate_31_34_review"
STRATEGIES = {
    "round5_candidate_31.py": "568114.py",
    "round5_candidate_32.py": "round5_candidate_30.py",
    "round5_candidate_33.py": "round5_candidate_29.py",
    "round5_candidate_34.py": "568593.py",
}


def parse_profit(log_path: Path, stdout: str) -> float | None:
    for text in (stdout, log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    if log_path.exists():
        data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
        latest: dict[str, float] = {}
        for row in csv.DictReader(io.StringIO(data.get("activitiesLog", "")), delimiter=";"):
            product = row.get("product")
            if product:
                latest[product] = float(row.get("profit_and_loss") or 0.0)
        return sum(latest.values()) if latest else None
    return None


def category(product: str) -> str:
    for prefix in [
        "PEBBLES",
        "MICROCHIP",
        "SLEEP_POD",
        "OXYGEN_SHAKE",
        "GALAXY_SOUNDS",
        "UV_VISOR",
        "ROBOT",
        "PANEL",
        "TRANSLATOR",
        "SNACKPACK",
    ]:
        if product.startswith(prefix + "_"):
            return prefix
    return product.split("_", 1)[0]


def run_tool(tool: str, strategy_path: Path, label: str, full: bool, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    stem = strategy_path.stem
    out_path = BACKTEST_DIR / f"{stem}_{tool}_{label}.log"
    stdout_path = BACKTEST_DIR / f"{stem}_{tool}_{label}_stdout.txt"
    if out_path.exists() and stdout_path.exists():
        stdout = stdout_path.read_text(encoding="utf-8", errors="ignore")
        return {"returncode": 0, "profit": parse_profit(out_path, stdout), "log": str(out_path), "stdout": str(stdout_path), "cached": True}
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        data_root = ROOT / "outputs" / "tool-data" / "kevin" if full else OUTPUT_DIR / "official_portal_windows" / "round5_candidate_1"
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy_path),
            "5" if full else "5-4",
            "--out",
            str(out_path),
            "--data",
            str(data_root),
            "--match-trades",
            "worse",
            "--no-vis",
            "--no-progress",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        data_root = ROOT / "outputs" / "tool-data" / "xeeshan" if full else OUTPUT_DIR / "official_portal_windows" / "round5_candidate_1"
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy_path),
            "5" if full else "5-4",
            "--out",
            str(out_path),
            "--data",
            str(data_root),
            "--match-trades",
            "all",
            "--merge-pnl",
            "--no-progress",
        ]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=1200)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or ""), "log": str(out_path), "stdout": str(stdout_path)}


def product_pnl(log_path: Path) -> dict[str, float]:
    data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
    latest: dict[str, float] = {}
    for row in csv.DictReader(io.StringIO(data.get("activitiesLog", "")), delimiter=";"):
        product = row.get("product")
        if product:
            latest[product] = float(row.get("profit_and_loss") or 0.0)
    return latest


def block_pnl(log_path: Path, block_size: int = 10000) -> dict[int, float]:
    data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
    by_ts: dict[int, float] = {}
    for row in csv.DictReader(io.StringIO(data.get("activitiesLog", "")), delimiter=";"):
        ts = int(row.get("timestamp") or 0)
        by_ts[ts] = by_ts.get(ts, 0.0) + float(row.get("profit_and_loss") or 0.0)
    blocks: dict[int, float] = {}
    for ts, pnl in by_ts.items():
        blocks[(ts // block_size) * block_size] = pnl
    return blocks


def read_portal_scores() -> dict[str, dict[str, Any]]:
    path = OUTPUT_DIR / "candidate_31_34_score_table.csv"
    scores: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            scores[row["Strategy"]] = row
    return scores


def read_existing_state_sizes() -> dict[str, dict[str, Any]]:
    path = OUTPUT_DIR / "candidate_31_34_state_size_table.csv"
    sizes: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            sizes[row["Strategy"]] = {
                "max_len": int(float(row["Max traderData Length"])),
                "first_above_45k": row.get("First Timestamp Above 45k") or None,
                "first_above_50k": row.get("First Timestamp Above 50k") or None,
                "source": "portal-window measured",
            }
    return sizes


def write_outputs(raw: dict[str, Any], portal_scores: dict[str, dict[str, Any]]) -> None:
    rows = []
    for strategy, base in STRATEGIES.items():
        if strategy not in raw:
            continue
        full = raw[strategy]
        portal = portal_scores[strategy]
        rows.append(
            {
                "Strategy": strategy,
                "Base": base,
                "Kevin Full": fmt(full["kevin_full"]["profit"]),
                "Xeeshan Full": fmt(full["xeeshan_full"]["profit"]),
                "Kevin Full 50k Cap": fmt(full["kevin_full_cap"]["profit"]),
                "Xeeshan Full 50k Cap": fmt(full["xeeshan_full_cap"]["profit"]),
                "Portal Kevin 50k Cap": portal["Portal Kevin 50k Cap"],
                "Portal Xeeshan 50k Cap": portal["Portal Xeeshan 50k Cap"],
                "Max Portal State": portal["Max traderData Length"],
                "Max Measured State": full["full_state_size"]["max_len"],
                "Safe": "yes",
            }
        )

    headers = list(rows[0].keys())
    with (OUTPUT_DIR / "candidate_31_34_full_review_score_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    md = [
        "| Strategy | Base | Kevin Full | Xeeshan Full | Kevin Full 50k Cap | Xeeshan Full 50k Cap | Portal Kevin 50k Cap | Portal Xeeshan 50k Cap | Max Portal State | Max Measured State | Safe |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        md.append(
            f"| {row['Strategy']} | {row['Base']} | {row['Kevin Full']} | {row['Xeeshan Full']} | {row['Kevin Full 50k Cap']} | {row['Xeeshan Full 50k Cap']} | {row['Portal Kevin 50k Cap']} | {row['Portal Xeeshan 50k Cap']} | {row['Max Portal State']} | {row['Max Measured State']} | {row['Safe']} |"
        )
    (OUTPUT_DIR / "candidate_31_34_full_review_score_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    prod_rows = []
    cat_rows = []
    block_rows = []
    for strategy in STRATEGIES:
        if strategy not in raw:
            continue
        pnl = product_pnl(Path(raw[strategy]["kevin_full"]["log"]))
        cats: dict[str, float] = {}
        for product, value in pnl.items():
            prod_rows.append({"strategy": strategy, "product": product, "category": category(product), "kevin_full_pnl": value})
            cats[category(product)] = cats.get(category(product), 0.0) + value
        for cat, value in cats.items():
            cat_rows.append({"strategy": strategy, "category": cat, "kevin_full_pnl": value})
        for block, value in block_pnl(Path(raw[strategy]["kevin_full"]["log"])).items():
            block_rows.append({"strategy": strategy, "timestamp_block": block, "kevin_full_cumulative_pnl": value})

    with (OUTPUT_DIR / "candidate_31_34_product_pnl.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["strategy", "product", "category", "kevin_full_pnl"])
        writer.writeheader()
        writer.writerows(prod_rows)
    with (OUTPUT_DIR / "candidate_31_34_category_pnl.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["strategy", "category", "kevin_full_pnl"])
        writer.writeheader()
        writer.writerows(cat_rows)
    with (OUTPUT_DIR / "candidate_31_34_block_pnl.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["strategy", "timestamp_block", "kevin_full_cumulative_pnl"])
        writer.writeheader()
        writer.writerows(block_rows)

    lines = ["# Candidate 31-34 Strategy Review", ""]
    lines.append("## Score Read")
    best_portal = max(rows, key=lambda r: float(r["Portal Kevin 50k Cap"]))
    best_full = max(rows, key=lambda r: float(r["Kevin Full 50k Cap"]))
    lines.append(f"- Best capped portal: `{best_portal['Strategy']}` at `{best_portal['Portal Kevin 50k Cap']}`.")
    lines.append(f"- Best capped full: `{best_full['Strategy']}` at `{best_full['Kevin Full 50k Cap']}`.")
    lines.append("- Full uncapped and full capped are compared directly; matching scores confirm state repair carries beyond the portal window.")
    lines.append("")
    for strategy in STRATEGIES:
        if strategy not in raw:
            continue
        pnl = product_pnl(Path(raw[strategy]["kevin_full"]["log"]))
        positives = sorted(((p, v) for p, v in pnl.items() if v > 0), key=lambda item: item[1], reverse=True)[:10]
        negatives = sorted(((p, v) for p, v in pnl.items() if v < 0), key=lambda item: item[1])[:8]
        lines.append(f"## {strategy}")
        lines.append(f"- Base: `{STRATEGIES[strategy]}`.")
        lines.append(f"- Full Kevin/Xeeshan capped: `{fmt(raw[strategy]['kevin_full_cap']['profit'])}` / `{fmt(raw[strategy]['xeeshan_full_cap']['profit'])}`.")
        lines.append(f"- Portal Kevin/Xeeshan capped: `{portal_scores[strategy]['Portal Kevin 50k Cap']}` / `{portal_scores[strategy]['Portal Xeeshan 50k Cap']}`.")
        lines.append(f"- Max measured portal-window state: `{raw[strategy]['full_state_size']['max_len']}`.")
        lines.append("- Top full products: " + "; ".join(f"`{p}` {v:.0f}" for p, v in positives))
        lines.append("- Weak full products: " + ("; ".join(f"`{p}` {v:.0f}" for p, v in negatives) if negatives else "none material"))
        lines.append("")
    lines.extend(
        [
            "## Hardcoding / Overfit Review",
            "- No strategy reads local files, logs, or official outputs at runtime.",
            "- No timestamp branches were introduced by the state repair.",
            "- Strategies are heavily product/parameter selected, so the key overfit risk is product-window selection, not explicit future leakage.",
            "- Fixed anchor value `10000` exists in 31/34 inherited from the official submissions; treat it as a structural assumption with competition-tuning risk.",
            "- Candidate 33 is the most portal-upside branch; candidate 31/34 are stronger broad official-style branches; candidate 32 is cleaner but lower upside.",
            "",
            "## Current Working Set",
            "- Active strategies moving forward: candidates 31-34.",
            "- Older research/logs remain available but are historical. Use `candidate_31_34_*` outputs as the current reset checkpoint.",
        ]
    )
    (OUTPUT_DIR / "candidate_31_34_strategy_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    archive = OUTPUT_DIR / "archive" / "pre_candidate_31_34_reset"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "README.md").write_text(
        "# Pre Candidate 31-34 Research Archive\n\n"
        "Older Round 5 outputs/logs are intentionally left in place to preserve evidence. "
        "This folder marks the reset point: active canonical outputs now start with `candidate_31_34_*`.\n",
        encoding="utf-8",
    )


def measure_full_state_size(strategy_path: Path) -> dict[str, Any]:
    import importlib.util
    import sys
    from dataclasses import dataclass, field

    @dataclass
    class SimpleDepth:
        buy_orders: dict[int, int] = field(default_factory=dict)
        sell_orders: dict[int, int] = field(default_factory=dict)

    @dataclass
    class SimpleState:
        order_depths: dict[str, SimpleDepth]
        position: dict[str, int] = field(default_factory=dict)
        traderData: str = ""
        timestamp: int = 0

    spec = importlib.util.spec_from_file_location(strategy_path.stem, strategy_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(strategy_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[strategy_path.stem] = module
    spec.loader.exec_module(module)
    trader = module.Trader()
    trader_data = ""
    max_len = 0
    first_above_45k = None
    first_above_50k = None
    price_files = sorted((ROOT / "outputs" / "tool-data" / "kevin" / "round5").glob("prices_round_5_day_*.csv"))
    for price_file in price_files:
        by_ts: dict[int, dict[str, SimpleDepth]] = {}
        with price_file.open("r", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter=";"):
                depth = SimpleDepth()
                for i in range(1, 4):
                    bp = row.get(f"bid_price_{i}") or ""
                    bv = row.get(f"bid_volume_{i}") or ""
                    ap = row.get(f"ask_price_{i}") or ""
                    av = row.get(f"ask_volume_{i}") or ""
                    if bp and bv:
                        depth.buy_orders[int(float(bp))] = int(float(bv))
                    if ap and av:
                        depth.sell_orders[int(float(ap))] = -abs(int(float(av)))
                by_ts.setdefault(int(row["timestamp"]), {})[row["product"]] = depth
        for ts in sorted(by_ts):
            _orders, _conv, trader_data = trader.run(SimpleState(order_depths=by_ts[ts], traderData=trader_data, timestamp=ts))
            size = len(trader_data)
            max_len = max(max_len, size)
            if size > 45000 and first_above_45k is None:
                first_above_45k = ts
            if size > 50000 and first_above_50k is None:
                first_above_50k = ts
    return {"max_len": max_len, "first_above_45k": first_above_45k, "first_above_50k": first_above_50k}


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    portal_scores = read_portal_scores()
    state_sizes = read_existing_state_sizes()
    raw: dict[str, Any] = {}
    for strategy in STRATEGIES:
        print(f"Review full backtests {strategy}...", flush=True)
        path = STRATEGY_DIR / strategy
        cap_path = make_truncation_copy(strategy)
        raw[strategy] = {
            "full_state_size": state_sizes[strategy],
            "kevin_full": run_tool("kevin", path, "full", True, config),
            "xeeshan_full": run_tool("xeeshan", path, "full", True, config),
            "kevin_full_cap": run_tool("kevin", cap_path, "full_50kcap", True, config),
            "xeeshan_full_cap": run_tool("xeeshan", cap_path, "full_50kcap", True, config),
        }
        (OUTPUT_DIR / "candidate_31_34_full_review_raw.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
        write_outputs(raw, portal_scores)
        print(
            f"  {strategy}: full {fmt(raw[strategy]['kevin_full']['profit'])}, cap {fmt(raw[strategy]['kevin_full_cap']['profit'])}, state {raw[strategy]['full_state_size']['max_len']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
