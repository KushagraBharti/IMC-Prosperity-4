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
BACKTEST_DIR = OUTPUT_DIR / "backtests" / "candidate_35_36"
TEMP_DIR = ROUND_DIR / "research" / "temp_candidate_35_36_score"
PORTAL_ROOT = OUTPUT_DIR / "official_portal_windows" / "round5_candidate_1"
PRICE_FILE = PORTAL_ROOT / "round5" / "prices_round_5_day_4.csv"

STRATEGIES = {
    "round5_candidate_35.py": {
        "base": "round5_candidate_33.py",
        "role": "robust alpha composite",
    },
    "round5_candidate_36.py": {
        "base": "round5_candidate_34.py",
        "role": "cleaned portal-upside strategy",
    },
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


def parse_profit(log_path: Path | None, stdout: str) -> float | None:
    texts = [stdout]
    if log_path and log_path.exists():
        texts.append(log_path.read_text(encoding="utf-8", errors="ignore"))
    for text in texts:
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    if log_path and log_path.exists():
        data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
        latest: dict[str, float] = {}
        for row in csv.DictReader(io.StringIO(data.get("activitiesLog", "")), delimiter=";"):
            product = row.get("product")
            if product:
                latest[product] = float(row.get("profit_and_loss") or 0.0)
        return sum(latest.values()) if latest else None
    return None


def run_portal(tool: str, strategy_path: Path, label: str, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BACKTEST_DIR / f"{strategy_path.stem}_{tool}_{label}.log"
    stdout_path = BACKTEST_DIR / f"{strategy_path.stem}_{tool}_{label}_stdout.txt"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5-4", "--out", str(out_path), "--data", str(PORTAL_ROOT), "--match-trades", "worse", "--no-vis", "--no-progress"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5-4", "--out", str(out_path), "--data", str(PORTAL_ROOT), "--match-trades", "all", "--merge-pnl", "--no-progress"]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=420)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or ""), "log": str(out_path), "stdout": str(stdout_path), "stderr_tail": (proc.stderr or "")[-1200:]}


def run_full_score(tool: str, strategy_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    stdout_path = BACKTEST_DIR / f"{strategy_path.stem}_{tool}_full_noout_stdout.txt"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        data_root = ROOT / "outputs" / "tool-data" / "kevin"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5", "--no-out", "--data", str(data_root), "--match-trades", "worse", "--no-vis", "--no-progress"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        data_root = ROOT / "outputs" / "tool-data" / "xeeshan"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5", "--no-out", "--data", str(data_root), "--match-trades", "all", "--merge-pnl", "--no-progress"]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=1200)
    text = (proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else "")
    stdout_path.write_text(text, encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(None, text), "stdout": str(stdout_path), "stderr_tail": (proc.stderr or "")[-1200:]}


def make_cap_copy(strategy_path: Path) -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    text = strategy_path.read_text(encoding="utf-8")
    old = "return result, 0, self.dump_cache(cache)"
    if old not in text:
        raise RuntimeError(f"Cannot find dump return in {strategy_path}")
    dst = TEMP_DIR / f"{strategy_path.stem}_50kcap.py"
    dst.write_text(text.replace(old, "td = self.dump_cache(cache)\n        return result, 0, td[:50000]"), encoding="utf-8")
    return dst


def load_strategy(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
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


def measure_state(path: Path) -> int:
    trader = load_strategy(path)
    trader_data = ""
    max_len = 0
    rows_by_ts: dict[int, dict[str, SimpleDepth]] = {}
    with PRICE_FILE.open("r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            rows_by_ts.setdefault(int(row["timestamp"]), {})[row["product"]] = depth_from_row(row)
    for ts in sorted(rows_by_ts):
        _orders, _conv, trader_data = trader.run(SimpleState(order_depths=rows_by_ts[ts], traderData=trader_data, timestamp=ts))
        max_len = max(max_len, len(trader_data))
    return max_len


def fmt(value: Any) -> str:
    return "" if value is None else f"{float(value):.0f}"


def write_outputs(raw: dict[str, Any]) -> None:
    rows = []
    for strategy, meta in STRATEGIES.items():
        if strategy not in raw:
            continue
        r = raw[strategy]
        rows.append(
            {
                "Strategy": strategy,
                "Base": meta["base"],
                "Portal Kevin": fmt(r["portal_kevin"]["profit"]),
                "Portal Xeeshan": fmt(r["portal_xeeshan"]["profit"]),
                "Portal Kevin 50k Cap": fmt(r["portal_kevin_cap"]["profit"]),
                "Portal Xeeshan 50k Cap": fmt(r["portal_xeeshan_cap"]["profit"]),
                "Full Kevin": fmt(r["full_kevin"]["profit"]),
                "Full Xeeshan": fmt(r["full_xeeshan"]["profit"]),
                "Max State": r["max_state"],
                "Role": meta["role"],
            }
        )
    headers = list(rows[0].keys())
    with (OUTPUT_DIR / "candidate_35_36_score_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "| Strategy | Base | Portal Kevin | Portal Xeeshan | Portal Kevin 50k Cap | Portal Xeeshan 50k Cap | Full Kevin | Full Xeeshan | Max State | Role |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['Strategy']}` | `{row['Base']}` | {row['Portal Kevin']} | {row['Portal Xeeshan']} | {row['Portal Kevin 50k Cap']} | {row['Portal Xeeshan 50k Cap']} | {row['Full Kevin']} | {row['Full Xeeshan']} | {row['Max State']} | {row['Role']} |")
    (OUTPUT_DIR / "candidate_35_36_score_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    raw_path = OUTPUT_DIR / "candidate_35_36_raw_scores.json"
    raw: dict[str, Any] = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
    for strategy in STRATEGIES:
        if strategy in raw and all(key in raw[strategy] for key in ("portal_kevin", "portal_xeeshan", "portal_kevin_cap", "portal_xeeshan_cap", "full_kevin", "full_xeeshan")):
            print(f"Skipping completed {strategy}...", flush=True)
            continue
        print(f"Scoring {strategy}...", flush=True)
        path = STRATEGY_DIR / strategy
        cap = make_cap_copy(path)
        raw[strategy] = {"max_state": measure_state(path)}
        raw[strategy]["portal_kevin"] = run_portal("kevin", path, "portal", config)
        raw[strategy]["portal_xeeshan"] = run_portal("xeeshan", path, "portal", config)
        raw[strategy]["portal_kevin_cap"] = run_portal("kevin", cap, "portal_50kcap", config)
        raw[strategy]["portal_xeeshan_cap"] = run_portal("xeeshan", cap, "portal_50kcap", config)
        print(f"  portal {fmt(raw[strategy]['portal_kevin']['profit'])} / cap {fmt(raw[strategy]['portal_kevin_cap']['profit'])}, state {raw[strategy]['max_state']}", flush=True)
        print(f"  full Kevin {strategy}...", flush=True)
        raw[strategy]["full_kevin"] = run_full_score("kevin", path, config)
        print(f"  full Xeeshan {strategy}...", flush=True)
        raw[strategy]["full_xeeshan"] = run_full_score("xeeshan", path, config)
        raw_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        write_outputs(raw)
        print(f"  full {fmt(raw[strategy]['full_kevin']['profit'])} / {fmt(raw[strategy]['full_xeeshan']['profit'])}", flush=True)
    write_outputs(raw)


if __name__ == "__main__":
    main()
