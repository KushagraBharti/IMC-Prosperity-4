from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUND3_DIR = ROOT / "ROUND3"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = sorted(ROUND3_DIR.glob("prices_round_3_day_*.csv"))
    trades = sorted(ROUND3_DIR.glob("trades_round_3_day_*.csv"))
    print(f"Round 3 price files: {len(prices)}")
    for path in prices:
        print(f"  - {path.name}")
    print(f"Round 3 trade files: {len(trades)}")
    for path in trades:
        print(f"  - {path.name}")


if __name__ == "__main__":
    main()
