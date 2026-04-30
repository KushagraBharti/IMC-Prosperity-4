from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ROUND5" / "research" / "outputs"
BACKTEST_DIR = OUT / "backtests" / "non_pebbles_promising_full"
PROBES = ["non_pebbles_probe_longhorizon_breadth.py", "non_pebbles_probe_longhorizon_microchip.py"]


def parse_profit(path: Path, stdout: str) -> float | None:
    for text in (stdout, path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    return None


def run(tool: str, strategy_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BACKTEST_DIR / f"{strategy_path.stem}_{tool}_full.log"
    stdout_path = BACKTEST_DIR / f"{strategy_path.stem}_{tool}_full_stdout.txt"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5", "--out", str(out_path), "--data", str(ROOT / "outputs" / "tool-data" / "kevin"), "--match-trades", "worse", "--no-vis", "--no-progress"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5", "--out", str(out_path), "--data", str(ROOT / "outputs" / "tool-data" / "xeeshan"), "--match-trades", "all", "--merge-pnl", "--no-progress"]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=360)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or ""), "log": str(out_path), "stdout": str(stdout_path)}


def fmt(value: Any) -> str:
    return "" if value is None else f"{float(value):.2f}"


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    probe_dir = ROOT / "ROUND5" / "research" / "probes"
    raw = {}
    rows = []
    for probe in PROBES:
        print(f"Full scoring {probe}...")
        path = probe_dir / probe
        raw[probe] = {"kevin_full": run("kevin", path, config), "xeeshan_full": run("xeeshan", path, config)}
        rows.append({"Probe": probe, "Kevin Full": fmt(raw[probe]["kevin_full"]["profit"]), "Xeeshan Full": fmt(raw[probe]["xeeshan_full"]["profit"])})
    (OUT / "non_pebbles_promising_full_raw.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    with (OUT / "non_pebbles_promising_full_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Probe", "Kevin Full", "Xeeshan Full"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
