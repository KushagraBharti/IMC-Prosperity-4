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
BACKTEST_DIR = OUT / "backtests" / "non_pebbles_probes"
PROBES = [
    "non_pebbles_probe_microchip.py",
    "non_pebbles_probe_robot.py",
    "non_pebbles_probe_uv_oxygen_panel.py",
    "non_pebbles_probe_breadth.py",
    "non_pebbles_probe_longhorizon_breadth.py",
    "non_pebbles_probe_longhorizon_microchip.py",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_profit(log_path: Path, stdout: str) -> float | None:
    for text in (stdout, log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    return None


def run_tool(tool: str, strategy_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    data_root = OUT / "official_portal_windows" / "round5_candidate_1"
    out_path = BACKTEST_DIR / f"{strategy_path.stem}_{tool}_portal.log"
    stdout_path = BACKTEST_DIR / f"{strategy_path.stem}_{tool}_portal_stdout.txt"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5-4", "--out", str(out_path), "--data", str(data_root), "--match-trades", "worse", "--no-vis", "--no-progress"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5-4", "--out", str(out_path), "--data", str(data_root), "--match-trades", "all", "--merge-pnl", "--no-progress"]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=240)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or ""), "log": str(out_path), "stdout": str(stdout_path)}


def fmt(value: Any) -> str:
    return "" if value is None else f"{float(value):.2f}"


def main() -> None:
    config = read_json(ROOT / "config" / "tools.local.json")
    raw = {}
    rows = []
    probe_dir = ROOT / "ROUND5" / "research" / "probes"
    for probe in PROBES:
        path = probe_dir / probe
        print(f"Portal scoring {probe}...")
        raw[probe] = {"kevin_portal": run_tool("kevin", path, config), "xeeshan_portal": run_tool("xeeshan", path, config)}
        rows.append({"Probe": probe, "Portal Window Kevin": fmt(raw[probe]["kevin_portal"]["profit"]), "Portal Window Xeeshan": fmt(raw[probe]["xeeshan_portal"]["profit"])})
    (OUT / "non_pebbles_probe_portal_raw.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    with (OUT / "non_pebbles_probe_portal_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Probe", "Portal Window Kevin", "Portal Window Xeeshan"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
