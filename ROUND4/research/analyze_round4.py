from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUND4_DIR = ROOT / "ROUND4"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prices = sorted(ROUND4_DIR.glob("prices_round_4_day_*.csv"))
    trades = sorted(ROUND4_DIR.glob("trades_round_4_day_*.csv"))
    print(f"Round 4 price files: {len(prices)}")
    for path in prices:
        print(f"  - {path.name}")
    print(f"Round 4 trade files: {len(trades)}")
    for path in trades:
        print(f"  - {path.name}")


if __name__ == "__main__":
    main()
