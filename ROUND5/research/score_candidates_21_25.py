from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
OUTPUT_DIR = ROUND_DIR / "research" / "outputs"
BACKTEST_DIR = OUTPUT_DIR / "backtests" / "candidate_21_25"
STRATEGIES = [f"round5_candidate_{i}.py" for i in range(21, 26)]


def parse_profit(log_path: Path, stdout: str) -> float | None:
    for text in (stdout, log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    return None


def run_tool(tool: str, strategy_name: str, day_arg: str, data_root: Path, label: str, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    strategy_path = ROUND_DIR / "strategies" / strategy_name
    out_path = BACKTEST_DIR / f"{strategy_name.replace('.py', '')}_{tool}_{label}.log"
    stdout_path = BACKTEST_DIR / f"{strategy_name.replace('.py', '')}_{tool}_{label}_stdout.txt"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), day_arg, "--out", str(out_path), "--data", str(data_root), "--match-trades", "worse", "--no-vis", "--no-progress"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), day_arg, "--out", str(out_path), "--data", str(data_root), "--match-trades", "all", "--merge-pnl", "--no-progress"]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=360)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or ""), "log": str(out_path), "stdout": str(stdout_path), "stderr_tail": (proc.stderr or "")[-1000:]}


def fmt(value: Any) -> str:
    return "" if value is None or value == "" else f"{float(value):.2f}"


def write_tables(rows: list[dict[str, Any]]) -> None:
    headers = ["Strategy", "Kevin Full", "Xeeshan Full", "Portal Window Kevin", "Portal Window Xeeshan", "Rust Full", "Official Portal Score"]
    with (OUTPUT_DIR / "candidate_21_25_score_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    lines = ["| Strategy | Kevin Full | Xeeshan Full | Portal Window Kevin | Portal Window Xeeshan | Rust Full | Official Portal Score |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['Strategy']} | {row['Kevin Full']} | {row['Xeeshan Full']} | {row['Portal Window Kevin']} | {row['Portal Window Xeeshan']} | {row['Rust Full']} | {row['Official Portal Score']} |")
    lines.append("")
    lines.append("Rust Full skipped: not needed for this controlled integration batch.")
    (OUTPUT_DIR / "candidate_21_25_score_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    full_roots = {"kevin": ROOT / "outputs" / "tool-data" / "kevin", "xeeshan": ROOT / "outputs" / "tool-data" / "xeeshan"}
    portal_root = OUTPUT_DIR / "official_portal_windows" / "round5_candidate_1"
    raw: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for strategy in STRATEGIES:
        print(f"Scoring portal {strategy}...")
        raw[strategy] = {
            "kevin_portal": run_tool("kevin", strategy, "5-4", portal_root, "portal_day4", config),
            "xeeshan_portal": run_tool("xeeshan", strategy, "5-4", portal_root, "portal_day4", config),
        }
    for strategy in STRATEGIES:
        print(f"Scoring full {strategy}...")
        raw[strategy]["kevin_full"] = run_tool("kevin", strategy, "5", full_roots["kevin"], "full", config)
        raw[strategy]["xeeshan_full"] = run_tool("xeeshan", strategy, "5", full_roots["xeeshan"], "full", config)
        rows.append(
            {
                "Strategy": strategy,
                "Kevin Full": fmt(raw[strategy]["kevin_full"]["profit"]),
                "Xeeshan Full": fmt(raw[strategy]["xeeshan_full"]["profit"]),
                "Portal Window Kevin": fmt(raw[strategy]["kevin_portal"]["profit"]),
                "Portal Window Xeeshan": fmt(raw[strategy]["xeeshan_portal"]["profit"]),
                "Rust Full": "",
                "Official Portal Score": "pending",
            }
        )
    (OUTPUT_DIR / "candidate_21_25_raw_backtests.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    write_tables(rows)


if __name__ == "__main__":
    main()
