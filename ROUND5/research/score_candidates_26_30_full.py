from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
OUTPUT_DIR = ROUND_DIR / "research" / "outputs"
BACKTEST_DIR = OUTPUT_DIR / "backtests" / "candidate_26_30"
RAW_PATH = OUTPUT_DIR / "candidate_26_30_raw_backtests.json"
STRATEGIES = [f"round5_candidate_{i}.py" for i in range(26, 31)]
ROLES = {
    "round5_candidate_26.py": "clean validated add-ons",
    "round5_candidate_27.py": "MICROCHIP specialist/info",
    "round5_candidate_28.py": "robust multi-engine",
    "round5_candidate_29.py": "portal-upside broad integration",
    "round5_candidate_30.py": "balanced competition portfolio",
}


def parse_profit(log_path: Path, stdout: str) -> float | None:
    for text in (stdout, log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    if log_path.exists():
        try:
            data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
            activities = data.get("activitiesLog", "")
            if activities:
                rows = list(csv.DictReader(io.StringIO(activities), delimiter=";"))
                latest: dict[str, float] = {}
                for row in rows:
                    product = row.get("product")
                    if product:
                        latest[product] = float(row.get("profit_and_loss") or 0.0)
                return sum(latest.values())
        except Exception:
            pass
    return None


def run_full(tool: str, strategy_name: str, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    strategy_path = ROUND_DIR / "strategies" / strategy_name
    out_path = BACKTEST_DIR / f"{strategy_name.replace('.py', '')}_{tool}_full.log"
    stdout_path = BACKTEST_DIR / f"{strategy_name.replace('.py', '')}_{tool}_full_stdout.txt"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        data_root = ROOT / "outputs" / "tool-data" / "kevin"
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy_path),
            "5",
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
        data_root = ROOT / "outputs" / "tool-data" / "xeeshan"
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy_path),
            "5",
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
    if out_path.exists() and stdout_path.exists():
        stdout = stdout_path.read_text(encoding="utf-8", errors="ignore")
        return {
            "returncode": 0,
            "profit": parse_profit(out_path, stdout),
            "log": str(out_path),
            "stdout": str(stdout_path),
            "stderr_tail": "",
            "cached": True,
        }
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=900)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {
        "returncode": proc.returncode,
        "profit": parse_profit(out_path, proc.stdout or ""),
        "log": str(out_path),
        "stdout": str(stdout_path),
        "stderr_tail": (proc.stderr or "")[-1500:],
    }


def fmt(value: Any) -> str:
    return "" if value is None else f"{float(value):.2f}"


def write_tables(raw: dict[str, dict[str, Any]]) -> None:
    headers = [
        "Strategy",
        "Kevin Full",
        "Xeeshan Full",
        "Portal Window Kevin",
        "Portal Window Xeeshan",
        "Role",
        "Official Portal Score",
    ]
    rows = []
    for strategy in STRATEGIES:
        runs = raw.get(strategy, {})
        rows.append(
            {
                "Strategy": strategy,
                "Kevin Full": fmt(runs.get("kevin_full", {}).get("profit")),
                "Xeeshan Full": fmt(runs.get("xeeshan_full", {}).get("profit")),
                "Portal Window Kevin": fmt(runs.get("kevin_portal", {}).get("profit")),
                "Portal Window Xeeshan": fmt(runs.get("xeeshan_portal", {}).get("profit")),
                "Role": ROLES[strategy],
                "Official Portal Score": "pending",
            }
        )
    with (OUTPUT_DIR / "candidate_26_30_full_score_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "| Strategy | Kevin Full | Xeeshan Full | Portal Window Kevin | Portal Window Xeeshan | Role | Official Portal Score |",
        "|---|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['Strategy']} | {row['Kevin Full']} | {row['Xeeshan Full']} | {row['Portal Window Kevin']} | {row['Portal Window Xeeshan']} | {row['Role']} | {row['Official Portal Score']} |"
        )
    (OUTPUT_DIR / "candidate_26_30_full_score_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    raw: dict[str, dict[str, Any]] = json.loads(RAW_PATH.read_text(encoding="utf-8")) if RAW_PATH.exists() else {}
    for strategy in STRATEGIES:
        raw.setdefault(strategy, {})
        print(f"Full Kevin {strategy}...", flush=True)
        raw[strategy]["kevin_full"] = run_full("kevin", strategy, config)
        RAW_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        write_tables(raw)
        print(f"  Kevin done: {fmt(raw[strategy]['kevin_full']['profit'])}", flush=True)
        print(f"Full Xeeshan {strategy}...", flush=True)
        raw[strategy]["xeeshan_full"] = run_full("xeeshan", strategy, config)
        RAW_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        write_tables(raw)
        print(f"  Xeeshan done: {fmt(raw[strategy]['xeeshan_full']['profit'])}", flush=True)
    write_tables(raw)


if __name__ == "__main__":
    main()
