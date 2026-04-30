from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
STRATEGY_DIR = ROUND_DIR / "strategies"
OUTPUT_DIR = ROUND_DIR / "research" / "outputs"
BACKTEST_DIR = OUTPUT_DIR / "backtests" / "candidate_31_33_state_repair"
TEMP_DIR = ROUND_DIR / "research" / "temp_state_repair"
PORTAL_ROOT = OUTPUT_DIR / "official_portal_windows" / "round5_candidate_1"
PRICE_FILE = PORTAL_ROOT / "round5" / "prices_round_5_day_4.csv"

STRATEGIES = {
    "round5_candidate_31.py": "568114.py",
    "round5_candidate_32.py": "round5_candidate_30.py",
    "round5_candidate_33.py": "round5_candidate_29.py",
    "round5_candidate_34.py": "568593.py",
}


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


def parse_profit(log_path: Path, stdout: str) -> float | None:
    for text in (stdout, log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    if log_path.exists():
        data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
        activities = data.get("activitiesLog", "")
        latest: dict[str, float] = {}
        for row in csv.DictReader(io.StringIO(activities), delimiter=";"):
            product = row.get("product")
            if product:
                latest[product] = float(row.get("profit_and_loss") or 0.0)
        return sum(latest.values()) if latest else None
    return None


def run_tool(tool: str, strategy_path: Path, label: str, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    stem = strategy_path.stem
    out_path = BACKTEST_DIR / f"{stem}_{tool}_{label}.log"
    stdout_path = BACKTEST_DIR / f"{stem}_{tool}_{label}_stdout.txt"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy_path),
            "5-4",
            "--out",
            str(out_path),
            "--data",
            str(PORTAL_ROOT),
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
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy_path),
            "5-4",
            "--out",
            str(out_path),
            "--data",
            str(PORTAL_ROOT),
            "--match-trades",
            "all",
            "--merge-pnl",
            "--no-progress",
        ]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=360)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {
        "returncode": proc.returncode,
        "profit": parse_profit(out_path, proc.stdout or ""),
        "log": str(out_path),
        "stdout": str(stdout_path),
        "stderr_tail": (proc.stderr or "")[-1500:],
    }


def make_truncation_copy(strategy: str) -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    src = STRATEGY_DIR / strategy
    dst = TEMP_DIR / f"{Path(strategy).stem}_50kcap.py"
    text = src.read_text(encoding="utf-8")
    old = "return result, 0, self.dump_cache(cache)"
    new = "td = self.dump_cache(cache)\n        return result, 0, td[:50000]"
    if old not in text:
        raise ValueError(f"Cannot find dump return in {strategy}")
    dst.write_text(text.replace(old, new), encoding="utf-8")
    return dst


def make_truncation_copy_from_path(src: Path, label: str) -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    dst = TEMP_DIR / f"{label}_50kcap.py"
    text = src.read_text(encoding="utf-8")
    old = 'return result, 0, json.dumps(cache, separators=(",", ":"))'
    if old in text:
        new = 'td = json.dumps(cache, separators=(",", ":"))\n        return result, 0, td[:50000]'
        dst.write_text(text.replace(old, new), encoding="utf-8")
        return dst
    old = "return result, 0, self.dump_cache(cache)"
    if old in text:
        new = "td = self.dump_cache(cache)\n        return result, 0, td[:50000]"
        dst.write_text(text.replace(old, new), encoding="utf-8")
        return dst
    raise ValueError(f"Cannot find traderData return in {src}")


def load_strategy(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module.Trader()


def depth_from_row(row: dict[str, str]) -> SimpleDepth:
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
    return depth


def measure_state_size(strategy_path: Path) -> dict[str, Any]:
    trader = load_strategy(strategy_path)
    trader_data = ""
    max_len = 0
    first_above_45k: int | None = None
    first_above_50k: int | None = None
    rows_by_ts: dict[int, dict[str, SimpleDepth]] = {}
    with PRICE_FILE.open("r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            ts = int(row["timestamp"])
            rows_by_ts.setdefault(ts, {})[row["product"]] = depth_from_row(row)
    for ts in sorted(rows_by_ts):
        state = SimpleState(order_depths=rows_by_ts[ts], position={}, traderData=trader_data, timestamp=ts)
        _orders, _conv, trader_data = trader.run(state)
        size = len(trader_data)
        max_len = max(max_len, size)
        if size > 45000 and first_above_45k is None:
            first_above_45k = ts
        if size > 50000 and first_above_50k is None:
            first_above_50k = ts
    return {"max_len": max_len, "first_above_45k": first_above_45k, "first_above_50k": first_above_50k}


def fmt(value: Any) -> str:
    return "" if value is None else f"{float(value):.2f}"


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    raw: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    size_rows: list[dict[str, Any]] = []

    for strategy, base in STRATEGIES.items():
        print(f"Scoring {strategy}...", flush=True)
        strategy_path = STRATEGY_DIR / strategy
        capped_path = make_truncation_copy(strategy)
        size = measure_state_size(strategy_path)
        raw[strategy] = {
            "base": base,
            "state_size": size,
            "kevin_uncapped": run_tool("kevin", strategy_path, "portal_uncapped", config),
            "xeeshan_uncapped": run_tool("xeeshan", strategy_path, "portal_uncapped", config),
            "kevin_capped": run_tool("kevin", capped_path, "portal_50kcap", config),
            "xeeshan_capped": run_tool("xeeshan", capped_path, "portal_50kcap", config),
        }
        ku = raw[strategy]["kevin_uncapped"]["profit"]
        xu = raw[strategy]["xeeshan_uncapped"]["profit"]
        kc = raw[strategy]["kevin_capped"]["profit"]
        xc = raw[strategy]["xeeshan_capped"]["profit"]
        official_safe = "yes" if size["max_len"] < 45000 and abs((ku or 0) - (kc or 0)) <= 5 and abs((xu or 0) - (xc or 0)) <= 5 else "check"
        rows.append(
            {
                "Strategy": strategy,
                "Base": base,
                "Portal Kevin Uncapped": fmt(ku),
                "Portal Xeeshan Uncapped": fmt(xu),
                "Portal Kevin 50k Cap": fmt(kc),
                "Portal Xeeshan 50k Cap": fmt(xc),
                "Max traderData Length": size["max_len"],
                "Official-Safe?": official_safe,
            }
        )
        size_rows.append(
            {
                "Strategy": strategy,
                "Base": base,
                "Max traderData Length": size["max_len"],
                "First Timestamp Above 45k": "" if size["first_above_45k"] is None else size["first_above_45k"],
                "First Timestamp Above 50k": "" if size["first_above_50k"] is None else size["first_above_50k"],
            }
        )
        print(f"  {strategy}: max state {size['max_len']}, Kevin {fmt(ku)} / cap {fmt(kc)}", flush=True)

    (OUTPUT_DIR / "candidate_31_33_raw_backtests.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")

    headers = [
        "Strategy",
        "Base",
        "Portal Kevin Uncapped",
        "Portal Xeeshan Uncapped",
        "Portal Kevin 50k Cap",
        "Portal Xeeshan 50k Cap",
        "Max traderData Length",
        "Official-Safe?",
    ]
    with (OUTPUT_DIR / "candidate_31_33_score_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    md = [
        "| Strategy | Base | Portal Kevin Uncapped | Portal Xeeshan Uncapped | Portal Kevin 50k Cap | Portal Xeeshan 50k Cap | Max traderData Length | Official-Safe? |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        md.append(
            f"| {row['Strategy']} | {row['Base']} | {row['Portal Kevin Uncapped']} | {row['Portal Xeeshan Uncapped']} | {row['Portal Kevin 50k Cap']} | {row['Portal Xeeshan 50k Cap']} | {row['Max traderData Length']} | {row['Official-Safe?']} |"
        )
    (OUTPUT_DIR / "candidate_31_33_score_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (OUTPUT_DIR / "candidate_31_34_score_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with (OUTPUT_DIR / "candidate_31_34_score_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    with (OUTPUT_DIR / "candidate_31_33_state_size_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Strategy", "Base", "Max traderData Length", "First Timestamp Above 45k", "First Timestamp Above 50k"])
        writer.writeheader()
        writer.writerows(size_rows)
    with (OUTPUT_DIR / "candidate_31_34_state_size_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Strategy", "Base", "Max traderData Length", "First Timestamp Above 45k", "First Timestamp Above 50k"])
        writer.writeheader()
        writer.writerows(size_rows)

    best = max(rows, key=lambda row: float(row["Portal Kevin 50k Cap"]))
    raw_568593 = diagnose_raw_568593(config)
    with (OUTPUT_DIR / "candidate_31_33_state_repair_notes.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Validation Results\n")
        handle.write("- Forced 50k cap was tested by temporary strategy copies under `ROUND5/research/temp_state_repair/`.\n")
        handle.write("- Max state length was measured on the official portal-window market data using the repaired serializer.\n")
        handle.write("- Uncapped and 50k-capped replay should match when the repair is complete.\n\n")
        handle.write(f"Recommended first submission: `{best['Strategy']}` because it has the highest capped portal replay among repaired candidates.\n")
        handle.write("\n## 568593 Raw Diagnosis\n")
        handle.write(f"- Raw 568593 max local state: `{raw_568593['state_size']['max_len']}`.\n")
        handle.write(f"- Raw uncapped Kevin/Xeeshan: `{fmt(raw_568593['kevin_uncapped']['profit'])}` / `{fmt(raw_568593['xeeshan_uncapped']['profit'])}`.\n")
        handle.write(f"- Raw 50k-cap Kevin/Xeeshan: `{fmt(raw_568593['kevin_capped']['profit'])}` / `{fmt(raw_568593['xeeshan_capped']['profit'])}`.\n")
        mismatch = abs((raw_568593["kevin_uncapped"]["profit"] or 0) - (raw_568593["kevin_capped"]["profit"] or 0))
        handle.write(f"- Conclusion: {'state-cap mismatch confirmed' if mismatch > 100 else 'no material state-cap mismatch detected'}.\n")
    (OUTPUT_DIR / "candidate_31_34_state_repair_notes.md").write_text(
        (OUTPUT_DIR / "candidate_31_33_state_repair_notes.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def diagnose_raw_568593(config: dict[str, Any]) -> dict[str, Any]:
    src = ROUND_DIR / "official_submissions" / "568593" / "568593.py"
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    raw_copy = TEMP_DIR / "568593_raw.py"
    raw_copy.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    capped_copy = make_truncation_copy_from_path(src, "568593_raw")
    result = {
        "state_size": measure_state_size(src),
        "kevin_uncapped": run_tool("kevin", raw_copy, "raw568593_uncapped", config),
        "xeeshan_uncapped": run_tool("xeeshan", raw_copy, "raw568593_uncapped", config),
        "kevin_capped": run_tool("kevin", capped_copy, "raw568593_50kcap", config),
        "xeeshan_capped": run_tool("xeeshan", capped_copy, "raw568593_50kcap", config),
    }
    (OUTPUT_DIR / "submission_568593_state_diagnosis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [
        "# Submission 568593 State Diagnosis",
        "",
        f"- Official portal score from JSON: `41,485.68`.",
        f"- Raw max local `traderData` length: `{result['state_size']['max_len']}`.",
        f"- Raw uncapped Kevin/Xeeshan portal replay: `{fmt(result['kevin_uncapped']['profit'])}` / `{fmt(result['xeeshan_uncapped']['profit'])}`.",
        f"- Raw forced-50k Kevin/Xeeshan portal replay: `{fmt(result['kevin_capped']['profit'])}` / `{fmt(result['xeeshan_capped']['profit'])}`.",
    ]
    mismatch = abs((result["kevin_uncapped"]["profit"] or 0) - (result["kevin_capped"]["profit"] or 0))
    lines.append(f"- Verdict: {'state cap is a material problem' if mismatch > 100 else 'state cap is not a material problem'}.")
    lines.append("- Repair: `round5_candidate_34.py` applies the same compact state serializer as candidates 31-33.")
    (OUTPUT_DIR / "submission_568593_state_diagnosis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    main()
