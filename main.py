from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
CONFIG_DEFAULTS = ROOT / "config" / "defaults.json"


def read_defaults() -> dict:
    with CONFIG_DEFAULTS.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def powershell_command(script_name: str, *args: str) -> list[str]:
    return [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPTS / script_name),
        *args,
    ]


def run_step(label: str, command: list[str]) -> None:
    print(f"\n=== {label} ===")
    print(" ".join(command))
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def parse_args() -> argparse.Namespace:
    defaults = read_defaults()

    parser = argparse.ArgumentParser(
        description="Run the full Prosperity workbench loop."
    )
    parser.add_argument(
        "--round",
        default=defaults.get("activeRound", "round1"),
        help="Replay round for the replay backtesters. Examples: tutorial, round1.",
    )
    parser.add_argument(
        "--days",
        nargs="*",
        type=int,
        default=[],
        help="Optional replay days. Example: --days 0 or --days -2 -1 0",
    )
    parser.add_argument(
        "--strategy",
        default="",
        help="Optional explicit strategy path for the replay backtesters.",
    )
    parser.add_argument(
        "--tutorial-strategy",
        default="",
        help="Optional explicit strategy path for Chris Monte Carlo.",
    )
    parser.add_argument(
        "--match-trades-xeeshan",
        choices=("all", "worse", "none"),
        default="all",
        help="Trade matching mode for Xeeshan.",
    )
    parser.add_argument(
        "--match-trades-kevin",
        choices=("all", "worse", "none"),
        default="worse",
        help="Trade matching mode for Kevin.",
    )
    parser.add_argument(
        "--match-trades-rust",
        choices=("all", "worse", "none"),
        default="all",
        help="Trade matching mode for the Rust backtester.",
    )
    parser.add_argument(
        "--carry-rust",
        action="store_true",
        help="Carry state across days in the Rust backtester.",
    )
    parser.add_argument(
        "--preset",
        choices=("default", "quick", "heavy"),
        default="quick",
        help="Chris Monte Carlo preset.",
    )
    parser.add_argument(
        "--force-chris",
        action="store_true",
        help="Run Chris Monte Carlo even when the replay round is not tutorial.",
    )
    parser.add_argument(
        "--skip-chris",
        action="store_true",
        help="Skip Chris Monte Carlo entirely.",
    )
    return parser.parse_args()


def build_replay_args(round_key: str, days: list[int], strategy: str) -> list[str]:
    args = [round_key]
    if days:
        args.extend(["-Days", *[str(day) for day in days]])
    if strategy:
        args.extend(["-Strategy", strategy])
    return args


def build_chris_args(preset: str, strategy: str) -> list[str]:
    args = ["tutorial", "-Preset", preset]
    if strategy:
        args.extend(["-Strategy", strategy])
    return args


def normalize_round_key(round_key: str) -> str:
    normalized = round_key.strip().lower()
    if normalized in {"0", "round0", "tutorial_round", "tutorial"}:
        return "tutorial"
    if normalized in {"1", "round1", "round_1"}:
        return "round1"
    return normalized


def main() -> int:
    args = parse_args()

    round_key = normalize_round_key(args.round)
    replay_args = build_replay_args(args.round, args.days, args.strategy)
    xeeshan_args = replay_args + ["-MatchTrades", args.match_trades_xeeshan]
    kevin_args = replay_args + ["-MatchTrades", args.match_trades_kevin]
    rust_args = replay_args + ["-TradeMatchMode", args.match_trades_rust]
    if args.carry_rust:
        rust_args.append("-Carry")
    chris_args = build_chris_args(args.preset, args.tutorial_strategy)

    run_step("Xeeshan backtester", powershell_command("bt-xeeshan.ps1", *xeeshan_args))
    run_step("Kevin backtester", powershell_command("bt-kevin.ps1", *kevin_args))
    run_step("Rust backtester", powershell_command("bt-rust.ps1", *rust_args))
    run_step("gsgill visualizer", powershell_command("viz-gsgill.ps1"))
    run_step("Kevin visualizer", powershell_command("viz-kevin.ps1"))

    should_run_chris = not args.skip_chris and (round_key == "tutorial" or args.force_chris)
    if should_run_chris:
        run_step("Chris Monte Carlo", powershell_command("stress-chris.ps1", *chris_args))
    else:
        print("\n=== Chris Monte Carlo ===")
        print("Skipped. Chris is tutorial-round only; use --force-chris to run it anyway.")

    print("\nFinished all selected tools.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
