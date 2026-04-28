from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "ROUND4" / "research" / "outputs" / "strategy_runs"
WINDOW_DIR = ROOT / "outputs" / "official-windows" / "round4_day3_0_99900_from_522830"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score Round 4 candidates in the standard table format.")
    parser.add_argument("strategies", nargs="+", help="Strategy .py files")
    parser.add_argument("--label", default="", help="Optional output label")
    parser.add_argument("--skip-full", action="store_true")
    parser.add_argument("--skip-window", action="store_true")
    return parser.parse_args()


def load_config() -> dict:
    return json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))


def run_command(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> tuple[int, str]:
    completed = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    return completed.returncode, completed.stdout


def extract_total(stdout: str) -> str:
    matches = re.findall(r"Total profit:\s*([-0-9,.]+)", stdout)
    if not matches:
        return ""
    return matches[-1].replace(",", "")


def make_window_data(out_dir: Path) -> Path:
    data_root = out_dir / "window_data"
    round_dir = data_root / "round4"
    round_dir.mkdir(parents=True, exist_ok=True)
    for name in ["prices_round_4_day_3.csv", "trades_round_4_day_3.csv"]:
        shutil.copy2(WINDOW_DIR / name, round_dir / name)
    return data_root


def ensure_full_data() -> None:
    for tool in ["kevin", "xeeshan"]:
        round_dir = ROOT / "outputs" / "tool-data" / tool / "round4"
        round_dir.mkdir(parents=True, exist_ok=True)
        for path in (ROOT / "ROUND4").glob("*_round_4_day_*.csv"):
            shutil.copy2(path, round_dir / path.name)


def run_kevin(
    strategy: Path,
    out_dir: Path,
    data_root: Path | None = None,
    day_arg: str = "4",
    match_trades: str = "worse",
) -> tuple[str, Path, int]:
    config = load_config()
    python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
    repo = Path(config["paths"]["kevinBacktesterRepo"])
    run_dir = out_dir / f"{strategy.stem}_kevin_{'window' if data_root else 'full'}"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_log = run_dir / "kevin.log"
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = str(repo / "prosperity4bt")
    cmd = [
        str(python),
        "-m",
        "prosperity4bt",
        str(strategy.resolve()),
        day_arg,
        "--out",
        str(out_log),
        "--data",
        str(data_root or (ROOT / "outputs" / "tool-data" / "kevin")),
        "--match-trades",
        match_trades,
        "--no-vis",
        "--no-progress",
    ]
    code, stdout = run_command(cmd, cwd=repo, env=env)
    (run_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    return extract_total(stdout), run_dir, code


def run_xeeshan(strategy: Path, out_dir: Path, data_root: Path | None = None, day_arg: str = "4") -> tuple[str, Path, int]:
    config = load_config()
    python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
    repo = Path(config["paths"]["xeeshanBacktesterRepo"])
    run_dir = out_dir / f"{strategy.stem}_xeeshan_{'window' if data_root else 'full'}"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_log = run_dir / "xeeshan.log"
    cmd = [
        str(python),
        "-m",
        "prosperity4bt",
        str(strategy.resolve()),
        day_arg,
        "--out",
        str(out_log),
        "--data",
        str(data_root or (ROOT / "outputs" / "tool-data" / "xeeshan")),
        "--match-trades",
        "all",
        "--merge-pnl",
        "--no-progress",
    ]
    code, stdout = run_command(cmd, cwd=repo)
    (run_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    return extract_total(stdout), run_dir, code


def fmt(value: str) -> str:
    if not value:
        return "failed"
    try:
        num = float(value)
    except ValueError:
        return value
    return f"{num:,.0f}"


def main() -> None:
    args = parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = args.label or "round4_candidates"
    out_dir = OUTPUT_ROOT / f"{label}_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ensure_full_data()
    window_data = make_window_data(out_dir)

    rows = []
    for raw in args.strategies:
        strategy = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
        row: dict[str, str] = {"Strategy": strategy.name}
        if args.skip_full:
            row["Full Kevin"] = "skipped"
            row["Full Xeeshan"] = "skipped"
        else:
            total, run_dir, code = run_kevin(strategy, out_dir)
            row["Full Kevin"] = fmt(total) if code == 0 else "failed"
            row["Full Kevin Run"] = str(run_dir)
            total, run_dir, code = run_xeeshan(strategy, out_dir)
            row["Full Xeeshan"] = fmt(total) if code == 0 else "failed"
            row["Full Xeeshan Run"] = str(run_dir)

        if args.skip_window:
            row["Window Kevin"] = "skipped"
            row["Window Xeeshan"] = "skipped"
        else:
            total, run_dir, code = run_kevin(strategy, out_dir, data_root=window_data, day_arg="4-3", match_trades="all")
            row["Window Kevin"] = fmt(total) if code == 0 else "failed"
            row["Window Kevin Run"] = str(run_dir)
            total, run_dir, code = run_xeeshan(strategy, out_dir, data_root=window_data, day_arg="4-3")
            row["Window Xeeshan"] = fmt(total) if code == 0 else "failed"
            row["Window Xeeshan Run"] = str(run_dir)
        row["Official"] = "pending"
        rows.append(row)
        print(row, flush=True)

    summary_path = out_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    markdown = [
        "| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        markdown.append(
            f"| `{row['Strategy']}` | {row['Full Kevin']} | {row['Full Xeeshan']} | {row['Window Kevin']} | {row['Window Xeeshan']} | {row['Official']} |"
        )
    (out_dir / "summary.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(out_dir)


if __name__ == "__main__":
    main()
