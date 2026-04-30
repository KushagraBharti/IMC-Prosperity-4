from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
STRATEGY_DIR = ROUND_DIR / "strategies"
OUTPUT_DIR = ROUND_DIR / "research" / "outputs"
PORTAL_ROOT = OUTPUT_DIR / "official_portal_windows" / "round5_candidate_1"
PORTAL_PRICE_FILE = PORTAL_ROOT / "round5" / "prices_round_5_day_4.csv"
TEMP_DIR = ROUND_DIR / "research" / "temp_round5_backtester"


@dataclass(frozen=True)
class StrategyRef:
    label: str
    path: Path


@dataclass(frozen=True)
class RunTask:
    strategy: StrategyRef
    tool: str
    suite: str
    capped: bool
    strategy_path: Path
    save_json_log: bool


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


def category(product: str) -> str:
    if product.startswith("OXYGEN_SHAKE_"):
        return "OXYGEN_SHAKE"
    if product.startswith("GALAXY_SOUNDS_"):
        return "GALAXY_SOUNDS"
    if product.startswith("SLEEP_POD_"):
        return "SLEEP_POD"
    if product.startswith("UV_VISOR_"):
        return "UV_VISOR"
    return product.split("_")[0]


def load_config() -> dict[str, Any]:
    return json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))


def resolve_strategy(raw: str) -> StrategyRef:
    path = Path(raw)
    if not path.suffix:
        path = path.with_suffix(".py")
    if not path.is_absolute():
        if not path.exists():
            path = STRATEGY_DIR / path.name
        else:
            path = ROOT / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return StrategyRef(path.name, path)


def make_cap_copy(strategy: StrategyRef) -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    text = strategy.path.read_text(encoding="utf-8")
    replacements = [
        ("return result, 0, self.dump_cache(cache)", "td = self.dump_cache(cache)\n        return result, 0, td[:50000]"),
        (
            'return result, 0, json.dumps(cache, separators=(",", ":"))',
            'td = json.dumps(cache, separators=(",", ":"))\n        return result, 0, td[:50000]',
        ),
    ]
    for old, new in replacements:
        if old in text:
            dst = TEMP_DIR / f"{strategy.path.stem}_50kcap.py"
            dst.write_text(text.replace(old, new), encoding="utf-8")
            return dst
    raise RuntimeError(f"Cannot identify traderData return in {strategy.path}")


def parse_profit_from_text(text: str) -> float | None:
    matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
    if matches:
        return float(matches[-1].replace(",", ""))
    return None


def parse_json_log(log_path: Path) -> dict[str, Any]:
    if not log_path.exists() or log_path.stat().st_size == 0:
        return {}
    try:
        data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}

    product_pnl: dict[str, float] = {}
    block_pnl: dict[str, float] = {}
    activities = data.get("activitiesLog", "")
    if activities:
        for row in csv.DictReader(io.StringIO(activities), delimiter=";"):
            product = row.get("product")
            if not product:
                continue
            try:
                pnl = float(row.get("profit_and_loss") or 0.0)
            except Exception:
                continue
            product_pnl[product] = pnl
            try:
                ts = int(float(row.get("timestamp") or 0))
                day = row.get("day", "")
                block = f"{day}:{(ts // 10000) * 10000}"
                block_pnl[block] = block_pnl.get(block, 0.0) + pnl
            except Exception:
                pass

    category_pnl: dict[str, float] = {}
    for product, pnl in product_pnl.items():
        category_pnl[category(product)] = category_pnl.get(category(product), 0.0) + pnl

    trades = data.get("tradeHistory", []) or []
    filled_qty = 0.0
    for trade in trades:
        try:
            filled_qty += abs(float(trade.get("quantity", 0)))
        except Exception:
            pass
    return {
        "submission_id": data.get("submissionId"),
        "product_pnl": product_pnl,
        "category_pnl": category_pnl,
        "block_pnl": block_pnl,
        "trade_count": len(trades),
        "filled_quantity": filled_qty,
        "avg_fill_quantity": (filled_qty / len(trades)) if trades else 0.0,
        "logs_count": len(data.get("logs", []) or []),
    }


def parse_profit(log_path: Path | None, stdout: str) -> float | None:
    profit = parse_profit_from_text(stdout)
    if profit is not None:
        return profit
    if log_path and log_path.exists():
        text = log_path.read_text(encoding="utf-8", errors="ignore")
        profit = parse_profit_from_text(text)
        if profit is not None:
            return profit
        parsed = parse_json_log(log_path)
        product_pnl = parsed.get("product_pnl", {})
        if product_pnl:
            return float(sum(product_pnl.values()))
    return None


def command_for_task(task: RunTask, config: dict[str, Any], out_path: Path | None) -> tuple[list[str], Path, dict[str, str]]:
    if task.tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        data_root = PORTAL_ROOT if task.suite == "portal" else ROOT / "outputs" / "tool-data" / "kevin"
        match = "worse"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
        cmd = [str(python), "-m", "prosperity4bt", str(task.strategy_path), "5-4" if task.suite == "portal" else "5"]
        if out_path:
            cmd += ["--out", str(out_path)]
        else:
            cmd += ["--no-out"]
        cmd += ["--data", str(data_root), "--match-trades", match, "--no-vis", "--no-progress"]
        return cmd, repo, env

    repo = Path(config["paths"]["xeeshanBacktesterRepo"])
    python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
    data_root = PORTAL_ROOT if task.suite == "portal" else ROOT / "outputs" / "tool-data" / "xeeshan"
    env = os.environ.copy()
    cmd = [str(python), "-m", "prosperity4bt", str(task.strategy_path), "5-4" if task.suite == "portal" else "5"]
    if out_path:
        cmd += ["--out", str(out_path)]
    else:
        cmd += ["--no-out"]
    cmd += ["--data", str(data_root), "--match-trades", "all", "--merge-pnl", "--no-progress"]
    return cmd, repo, env


def run_task(task: RunTask, config: dict[str, Any], run_dir: Path, timeout: int, reuse: bool) -> dict[str, Any]:
    suffix = "_50kcap" if task.capped else ""
    stem = f"{task.strategy.path.stem}{suffix}_{task.tool}_{task.suite}"
    log_path = run_dir / f"{stem}.log" if task.save_json_log else None
    stdout_path = run_dir / f"{stem}_stdout.txt"

    if reuse and stdout_path.exists() and (not task.save_json_log or (log_path and log_path.exists())):
        stdout = stdout_path.read_text(encoding="utf-8", errors="ignore")
        parsed_log = parse_json_log(log_path) if log_path else {}
        return {
            "strategy": task.strategy.label,
            "tool": task.tool,
            "suite": task.suite,
            "capped": task.capped,
            "returncode": 0,
            "profit": parse_profit(log_path, stdout),
            "duration_sec": 0.0,
            "json_log": "" if log_path is None else str(log_path),
            "stdout": str(stdout_path),
            "cached": True,
            **parsed_log,
        }

    cmd, cwd, env = command_for_task(task, config, log_path)
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    duration = time.perf_counter() - started
    stdout = (proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else "")
    stdout_path.write_text(stdout, encoding="utf-8")
    parsed_log = parse_json_log(log_path) if log_path else {}
    return {
        "strategy": task.strategy.label,
        "tool": task.tool,
        "suite": task.suite,
        "capped": task.capped,
        "returncode": proc.returncode,
        "profit": parse_profit(log_path, stdout),
        "duration_sec": round(duration, 2),
        "json_log": "" if log_path is None else str(log_path),
        "stdout": str(stdout_path),
        "stderr_tail": (proc.stderr or "")[-1200:],
        **parsed_log,
    }


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


def price_files_for_state(scope: str) -> list[Path]:
    if scope == "none":
        return []
    if scope == "portal":
        return [PORTAL_PRICE_FILE]
    return sorted((ROOT / "outputs" / "tool-data" / "kevin" / "round5").glob("prices_round_5_day_*.csv"))


def measure_state(strategy: StrategyRef, scope: str) -> dict[str, Any]:
    files = price_files_for_state(scope)
    if not files:
        return {"strategy": strategy.label, "scope": scope, "max_len": None, "first_above_45k": None, "first_above_50k": None}
    trader = load_strategy(strategy.path)
    trader_data = ""
    max_len = 0
    first_above_45k = None
    first_above_50k = None
    for price_file in files:
        by_ts: dict[int, dict[str, SimpleDepth]] = {}
        with price_file.open("r", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter=";"):
                by_ts.setdefault(int(row["timestamp"]), {})[row["product"]] = depth_from_row(row)
        for ts in sorted(by_ts):
            _orders, _conv, trader_data = trader.run(SimpleState(order_depths=by_ts[ts], traderData=trader_data, timestamp=ts))
            size = len(trader_data)
            max_len = max(max_len, size)
            if size > 45000 and first_above_45k is None:
                first_above_45k = ts
            if size > 50000 and first_above_50k is None:
                first_above_50k = ts
    return {"strategy": strategy.label, "scope": scope, "max_len": max_len, "first_above_45k": first_above_45k, "first_above_50k": first_above_50k}


def write_outputs(run_dir: Path, run_rows: list[dict[str, Any]], state_rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    summary = {"args": vars(args), "runs": run_rows, "state": state_rows}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    run_headers = [
        "strategy",
        "tool",
        "suite",
        "capped",
        "profit",
        "returncode",
        "duration_sec",
        "trade_count",
        "filled_quantity",
        "avg_fill_quantity",
        "json_log",
        "stdout",
    ]
    with (run_dir / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=run_headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(run_rows)

    if state_rows:
        with (run_dir / "state_size.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["strategy", "scope", "max_len", "first_above_45k", "first_above_50k"])
            writer.writeheader()
            writer.writerows(state_rows)

    product_rows = []
    category_rows = []
    block_rows = []
    for row in run_rows:
        prefix = {k: row[k] for k in ("strategy", "tool", "suite", "capped")}
        for product, pnl in (row.get("product_pnl") or {}).items():
            product_rows.append({**prefix, "product": product, "category": category(product), "pnl": pnl})
        for cat, pnl in (row.get("category_pnl") or {}).items():
            category_rows.append({**prefix, "category": cat, "pnl": pnl})
        for block, pnl in (row.get("block_pnl") or {}).items():
            block_rows.append({**prefix, "block": block, "pnl": pnl})

    if product_rows:
        with (run_dir / "product_pnl.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["strategy", "tool", "suite", "capped", "product", "category", "pnl"])
            writer.writeheader()
            writer.writerows(product_rows)
    if category_rows:
        with (run_dir / "category_pnl.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["strategy", "tool", "suite", "capped", "category", "pnl"])
            writer.writeheader()
            writer.writerows(category_rows)
    if block_rows:
        with (run_dir / "block_pnl.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["strategy", "tool", "suite", "capped", "block", "pnl"])
            writer.writeheader()
            writer.writerows(block_rows)

    lines = [
        "# Round 5 Backtest Summary",
        "",
        f"- Run directory: `{run_dir}`",
        f"- Jobs: `{args.jobs}`",
        f"- Full JSON logs: `{args.full_logs}`",
        "",
        "| Strategy | Tool | Suite | Capped | Profit | Return | Seconds | Trades | Avg Fill |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in run_rows:
        profit = "" if row.get("profit") is None else f"{float(row['profit']):.0f}"
        lines.append(
            f"| `{row['strategy']}` | {row['tool']} | {row['suite']} | {str(row['capped']).lower()} | {profit} | {row.get('returncode')} | {row.get('duration_sec', '')} | {row.get('trade_count', '')} | {float(row.get('avg_fill_quantity') or 0):.2f} |"
        )
    if state_rows:
        lines.extend(["", "## State Size", "", "| Strategy | Scope | Max Length | First >45k | First >50k |", "|---|---|---:|---:|---:|"])
        for row in state_rows:
            lines.append(f"| `{row['strategy']}` | {row['scope']} | {row['max_len']} | {row['first_above_45k'] or ''} | {row['first_above_50k'] or ''} |")
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reusable fast Round 5 backtest harness.")
    parser.add_argument("strategies", nargs="+", help="Strategy filenames/paths, e.g. round5_candidate_35.py")
    parser.add_argument("--tools", nargs="+", choices=["kevin", "xeeshan"], default=["kevin", "xeeshan"])
    parser.add_argument("--suites", nargs="+", choices=["portal", "full"], default=["portal"])
    parser.add_argument("--jobs", type=int, default=4, help="Parallel subprocess jobs. Try 4-8 on an i7-13700; reduce if UI/thermal throttles.")
    parser.add_argument("--name", default="", help="Output run name under ROUND5/research/outputs/backtests.")
    parser.add_argument("--reuse", action="store_true", help="Reuse matching existing stdout/json logs in the run directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print tasks and exit.")
    parser.add_argument("--cap-check", action="store_true", help="Also run forced-50k traderData variants.")
    parser.add_argument("--cap-suites", nargs="+", choices=["portal", "full"], default=["portal"], help="Suites where cap-check variants are run.")
    parser.add_argument("--state", choices=["none", "portal", "full"], default="portal", help="Measure max traderData with local simulation.")
    parser.add_argument("--portal-logs", action=argparse.BooleanOptionalAction, default=True, help="Save portal JSON logs for attribution.")
    parser.add_argument("--full-logs", action="store_true", help="Save full JSON logs. Expensive; default full mode uses --no-out score-only.")
    parser.add_argument("--timeout", type=int, default=1200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()
    strategies = [resolve_strategy(raw) for raw in args.strategies]
    run_name = args.name or "round5_backtester_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / "backtests" / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    cap_paths = {strategy.label: make_cap_copy(strategy) for strategy in strategies} if args.cap_check else {}
    tasks: list[RunTask] = []
    for strategy in strategies:
        for suite in args.suites:
            for tool in args.tools:
                save_log = args.portal_logs if suite == "portal" else args.full_logs
                tasks.append(RunTask(strategy, tool, suite, False, strategy.path, save_log))
                if args.cap_check and suite in args.cap_suites:
                    tasks.append(RunTask(strategy, tool, suite, True, cap_paths[strategy.label], save_log))

    state_rows = []
    if args.state != "none":
        for strategy in strategies:
            state_rows.append(measure_state(strategy, args.state))

    if args.dry_run:
        print(f"Run directory: {run_dir}")
        for row in state_rows:
            print("STATE", row)
        for task in tasks:
            print("TASK", task.strategy.label, task.tool, task.suite, "cap" if task.capped else "raw", "json" if task.save_json_log else "no-out")
        return

    print(f"Running {len(tasks)} tasks with jobs={args.jobs}. Output: {run_dir}", flush=True)
    run_rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as executor:
        future_map = {executor.submit(run_task, task, config, run_dir, args.timeout, args.reuse): task for task in tasks}
        for future in as_completed(future_map):
            task = future_map[future]
            try:
                row = future.result()
            except Exception as exc:
                row = {
                    "strategy": task.strategy.label,
                    "tool": task.tool,
                    "suite": task.suite,
                    "capped": task.capped,
                    "returncode": -1,
                    "profit": None,
                    "duration_sec": None,
                    "error": repr(exc),
                }
            run_rows.append(row)
            profit = "" if row.get("profit") is None else f"{float(row['profit']):.0f}"
            print(f"DONE {row['strategy']} {row['tool']} {row['suite']} cap={row['capped']} profit={profit} rc={row.get('returncode')}", flush=True)

    run_rows.sort(key=lambda r: (r["strategy"], r["suite"], r["tool"], str(r["capped"])))
    write_outputs(run_dir, run_rows, state_rows, args)
    print(f"Wrote {run_dir / 'summary.md'}", flush=True)


if __name__ == "__main__":
    main()
