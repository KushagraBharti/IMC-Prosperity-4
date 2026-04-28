from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "ROUND4" / "research" / "outputs" / "official_feedback" / "window_match_modes"
WINDOW_DIR = ROOT / "outputs" / "official-windows" / "round4_day3_0_99900_from_522830"
STRATEGIES = [
    ROOT / "ROUND4" / "strategies" / "round4_candidate_1_522830_base.py",
    ROOT / "ROUND4" / "strategies" / "round4_candidate_2_option9_hydrofairoff.py",
    ROOT / "ROUND4" / "strategies" / "round4_candidate_3_option9_nohydro.py",
]
MODES = ["none", "worse", "all"]


def load_config() -> dict:
    return json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))


def make_window_data() -> Path:
    data_root = OUT_DIR / "data"
    round_dir = data_root / "round4"
    round_dir.mkdir(parents=True, exist_ok=True)
    for name in ["prices_round_4_day_3.csv", "trades_round_4_day_3.csv"]:
        shutil.copy2(WINDOW_DIR / name, round_dir / name)
    return data_root


def extract_total(stdout: str) -> str:
    matches = re.findall(r"Total profit:\s*([-0-9,.]+)", stdout)
    return matches[-1].replace(",", "") if matches else ""


def run_tool(tool: str, strategy: Path, mode: str, data_root: Path) -> tuple[str, int]:
    config = load_config()
    repo = Path(config["paths"][f"{tool}BacktesterRepo"])
    python = Path(config["envs"][f"{tool}Venv"]) / "Scripts" / "python.exe"
    out_path = OUT_DIR / f"{strategy.stem}_{tool}_{mode}.log"
    cmd = [
        str(python),
        "-m",
        "prosperity4bt",
        str(strategy),
        "4-3",
        "--out",
        str(out_path),
        "--data",
        str(data_root),
        "--match-trades",
        mode,
        "--no-progress",
    ]
    env = os.environ.copy()
    if tool == "kevin":
        env["PYTHONPATH"] = str(repo / "prosperity4bt")
        cmd.append("--no-vis")
    else:
        cmd.append("--merge-pnl")
    completed = subprocess.run(cmd, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    (OUT_DIR / f"{strategy.stem}_{tool}_{mode}.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    return extract_total(completed.stdout), completed.returncode


def fmt(value: str) -> str:
    if not value:
        return "failed"
    return f"{float(value):,.0f}"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_root = make_window_data()
    rows = []
    for strategy in STRATEGIES:
        for mode in MODES:
            row = {"strategy": strategy.name, "match_trades": mode}
            for tool in ["kevin", "xeeshan"]:
                total, code = run_tool(tool, strategy, mode, data_root)
                row[tool] = fmt(total) if code == 0 else "failed"
            rows.append(row)
            print(row, flush=True)

    with (OUT_DIR / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["strategy", "match_trades", "kevin", "xeeshan"])
        writer.writeheader()
        writer.writerows(rows)

    markdown = [
        "| Strategy | Match Trades | Kevin | Xeeshan |",
        "|---|---|---:|---:|",
    ]
    for row in rows:
        markdown.append(f"| `{row['strategy']}` | `{row['match_trades']}` | {row['kevin']} | {row['xeeshan']} |")
    (OUT_DIR / "summary.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
