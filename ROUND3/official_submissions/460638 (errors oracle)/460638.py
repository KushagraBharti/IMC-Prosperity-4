from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


PRODUCT_LIMITS = {
    "HYDROGEL_PACK": 200,
    "VELVETFRUIT_EXTRACT": 200,
    "VEV_4000": 300,
    "VEV_4500": 300,
    "VEV_5000": 300,
    "VEV_5100": 300,
    "VEV_5200": 300,
    "VEV_5300": 300,
    "VEV_5400": 300,
    "VEV_5500": 300,
    "VEV_6000": 300,
    "VEV_6500": 300,
}


DEFAULT_PRODUCTS = [
    "HYDROGEL_PACK",
    "VELVETFRUIT_EXTRACT",
    "VEV_5000",
    "VEV_5100",
    "VEV_5200",
    "VEV_5300",
    "VEV_5400",
    "VEV_5500",
]


@dataclass(frozen=True)
class BookRow:
    day: int
    timestamp: int
    product: str
    bids: tuple[tuple[int, int], ...]
    asks: tuple[tuple[int, int], ...]
    mid: float


@dataclass
class OracleResult:
    product: str
    day: int
    limit: int
    terminal_fair: float
    oracle_pnl: float
    trades: pd.DataFrame
    inventory_path: pd.DataFrame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Round 3 dynamic-programming oracle scheduler")
    parser.add_argument("--data-dir", default="ROUND3", help="Directory containing prices_round_3_day_X.csv files")
    parser.add_argument("--day", type=int, default=2)
    parser.add_argument("--out-dir", default="outputs/dp_oracle/round3")
    parser.add_argument("--products", nargs="*", default=DEFAULT_PRODUCTS)
    parser.add_argument("--max-depth", type=int, default=3, choices=[1, 2, 3])
    parser.add_argument(
        "--terminal",
        choices=["last-mid", "zero"],
        default="last-mid",
        help="Terminal mark. last-mid matches local backtester-style liquidation best.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=0,
        help="Optional prefix length for quick tests. 0 means all timestamps in the file.",
    )
    parser.add_argument("--write-replay-strategy", default="", help="Optional path for non-submit-safe oracle replay strategy")
    return parser.parse_args()


def _int_or_none(value) -> int | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text == "":
        return None
    return int(float(text))


def _book_side(row: pd.Series, side: str, max_depth: int) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for level in range(1, max_depth + 1):
        price = _int_or_none(row.get(f"{side}_price_{level}"))
        volume = _int_or_none(row.get(f"{side}_volume_{level}"))
        if price is None or volume is None:
            continue
        qty = abs(int(volume))
        if qty > 0:
            out.append((int(price), qty))
    if side == "bid":
        out.sort(reverse=True)
    else:
        out.sort()
    return tuple(out)


def load_books(data_dir: Path, day: int, product: str, max_depth: int, max_steps: int) -> list[BookRow]:
    path = data_dir / f"prices_round_3_day_{day}.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, sep=";")
    df = df[df["product"] == product].sort_values("timestamp")
    if max_steps > 0:
        df = df.head(max_steps)
    rows: list[BookRow] = []
    for _, row in df.iterrows():
        bids = _book_side(row, "bid", max_depth)
        asks = _book_side(row, "ask", max_depth)
        mid = float(row["mid_price"])
        rows.append(
            BookRow(
                day=int(row["day"]),
                timestamp=int(row["timestamp"]),
                product=product,
                bids=bids,
                asks=asks,
                mid=mid,
            )
        )
    if not rows:
        raise ValueError(f"No rows for product={product} day={day} in {path}")
    return rows


def side_cash_for_qty(book: BookRow, qty: int) -> float | None:
    if qty == 0:
        return 0.0
    if qty > 0:
        remaining = qty
        cash = 0.0
        for price, volume in book.asks:
            take = min(remaining, volume)
            cash -= price * take
            remaining -= take
            if remaining == 0:
                return cash
        return None

    remaining = -qty
    cash = 0.0
    for price, volume in book.bids:
        take = min(remaining, volume)
        cash += price * take
        remaining -= take
        if remaining == 0:
            return cash
    return None


def feasible_actions(book: BookRow) -> list[tuple[int, float]]:
    buy_capacity = sum(volume for _, volume in book.asks)
    sell_capacity = sum(volume for _, volume in book.bids)
    actions: list[tuple[int, float]] = []
    for qty in range(-sell_capacity, buy_capacity + 1):
        cash = side_cash_for_qty(book, qty)
        if cash is not None:
            actions.append((qty, cash))
    return actions


def solve_oracle(product: str, books: list[BookRow], limit: int, terminal: str) -> OracleResult:
    positions = np.arange(-limit, limit + 1, dtype=np.int16)
    n_pos = len(positions)
    offset = limit
    neg_inf = -1e100

    dp = np.full(n_pos, neg_inf, dtype=np.float64)
    dp[offset] = 0.0
    prev_choice = np.full((len(books), n_pos), -32768, dtype=np.int16)

    for t, book in enumerate(books):
        next_dp = np.full(n_pos, neg_inf, dtype=np.float64)
        next_prev = prev_choice[t]
        for qty, cash in feasible_actions(book):
            if qty >= 0:
                src_start = 0
                src_end = n_pos - qty
                dst_start = qty
                dst_end = n_pos
            else:
                src_start = -qty
                src_end = n_pos
                dst_start = 0
                dst_end = n_pos + qty

            candidates = dp[src_start:src_end] + cash
            target = next_dp[dst_start:dst_end]
            better = candidates > target
            if np.any(better):
                target[better] = candidates[better]
                src_positions = positions[src_start:src_end]
                next_prev[dst_start:dst_end][better] = src_positions[better]
        dp = next_dp

    terminal_fair = 0.0 if terminal == "zero" else books[-1].mid
    terminal_values = dp + positions.astype(np.float64) * terminal_fair
    best_idx = int(np.argmax(terminal_values))
    oracle_pnl = float(terminal_values[best_idx])
    final_position = int(positions[best_idx])

    inventory_by_t = np.zeros(len(books) + 1, dtype=np.int16)
    inventory_by_t[-1] = final_position
    pos = final_position
    for t in range(len(books) - 1, -1, -1):
        prev_pos = int(prev_choice[t, pos + offset])
        if prev_pos == -32768:
            raise RuntimeError(f"Broken DP backpointer product={product} t={t} pos={pos}")
        inventory_by_t[t] = prev_pos
        pos = prev_pos

    trade_rows = []
    inventory_rows = []
    cash = 0.0
    for t, book in enumerate(books):
        prev_pos = int(inventory_by_t[t])
        next_pos = int(inventory_by_t[t + 1])
        qty = next_pos - prev_pos
        step_cash = side_cash_for_qty(book, qty)
        if step_cash is None:
            raise RuntimeError(f"Oracle action became infeasible product={product} timestamp={book.timestamp} qty={qty}")
        cash += step_cash
        inventory_rows.append(
            {
                "day": book.day,
                "timestamp": book.timestamp,
                "product": product,
                "inventory": next_pos,
                "mid": book.mid,
                "cash": cash,
                "marked_pnl": cash + next_pos * book.mid,
            }
        )
        if qty:
            trade_rows.append(
                {
                    "day": book.day,
                    "timestamp": book.timestamp,
                    "product": product,
                    "qty": qty,
                    "cash": step_cash,
                    "prev_pos": prev_pos,
                    "next_pos": next_pos,
                    "mid": book.mid,
                    "terminal_fair": terminal_fair,
                }
            )

    return OracleResult(
        product=product,
        day=books[0].day,
        limit=limit,
        terminal_fair=terminal_fair,
        oracle_pnl=oracle_pnl,
        trades=pd.DataFrame(trade_rows),
        inventory_path=pd.DataFrame(inventory_rows),
    )


def write_replay_strategy(path: Path, schedules: dict[str, list[dict]]) -> None:
    by_timestamp: dict[int, dict[str, int]] = {}
    for product, rows in schedules.items():
        for row in rows:
            ts = int(row["timestamp"])
            qty = int(row["qty"])
            if qty == 0:
                continue
            by_timestamp.setdefault(ts, {})[product] = qty

    schedule_literal = json.dumps(by_timestamp, sort_keys=True, separators=(",", ":"))
    text = f'''from datamodel import Order, TradingState

# EXPERIMENTAL / NON-SUBMIT-SAFE.
# This strategy replays a hindsight DP oracle schedule generated from known data.
# Use it to measure upper bounds and diagnose missed edge, not as a real submission.

SCHEDULE = {schedule_literal}


def asks(depth):
    return sorted((int(price), abs(int(volume))) for price, volume in depth.sell_orders.items())


def bids(depth):
    return sorted(((int(price), int(volume)) for price, volume in depth.buy_orders.items()), reverse=True)


class Trader:
    def run(self, state: TradingState):
        result = {{}}
        actions = SCHEDULE.get(str(int(state.timestamp)), {{}})
        for product, target_qty in actions.items():
            depth = state.order_depths.get(product)
            if depth is None or target_qty == 0:
                continue
            remaining = abs(int(target_qty))
            orders = []
            if target_qty > 0:
                for price, volume in asks(depth):
                    if remaining <= 0:
                        break
                    qty = min(remaining, volume)
                    if qty > 0:
                        orders.append(Order(product, price, qty))
                        remaining -= qty
            else:
                for price, volume in bids(depth):
                    if remaining <= 0:
                        break
                    qty = min(remaining, volume)
                    if qty > 0:
                        orders.append(Order(product, price, -qty))
                        remaining -= qty
            if orders:
                result[product] = orders
        return result, 0, ""
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def summarize(results: Iterable[OracleResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        if result.trades.empty:
            trade_count = 0
            turnover = 0
        else:
            trade_count = len(result.trades)
            turnover = int(result.trades["qty"].abs().sum())
        rows.append(
            {
                "day": result.day,
                "product": result.product,
                "limit": result.limit,
                "terminal_fair": result.terminal_fair,
                "oracle_pnl": result.oracle_pnl,
                "trade_count": trade_count,
                "turnover": turnover,
            }
        )
    return pd.DataFrame(rows).sort_values("oracle_pnl", ascending=False)


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[OracleResult] = []
    replay_schedules: dict[str, list[dict]] = {}

    for product in args.products:
        limit = PRODUCT_LIMITS[product]
        books = load_books(data_dir, args.day, product, args.max_depth, args.max_steps)
        result = solve_oracle(product, books, limit, args.terminal)
        results.append(result)
        safe_product = product.lower()
        result.trades.to_csv(out_dir / f"{safe_product}_oracle_trades.csv", index=False)
        result.inventory_path.to_csv(out_dir / f"{safe_product}_inventory_path.csv", index=False)
        replay_schedules[product] = result.trades.to_dict("records")
        print(f"{product}: oracle_pnl={result.oracle_pnl:.2f} trades={len(result.trades)}")

    summary = summarize(results)
    summary.to_csv(out_dir / "summary.csv", index=False)
    (out_dir / "summary.md").write_text(summary.to_markdown(index=False), encoding="utf-8")
    print(summary.to_string(index=False))

    if args.write_replay_strategy:
        write_replay_strategy(Path(args.write_replay_strategy), replay_schedules)
        print(f"Wrote replay strategy to {args.write_replay_strategy}")


if __name__ == "__main__":
    main()