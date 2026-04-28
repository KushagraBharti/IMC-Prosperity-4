from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND4"
OUT_DIR = ROUND_DIR / "research" / "outputs" / "mini_experiments"

PRODUCTS = [
    "HYDROGEL_PACK",
    "VELVETFRUIT_EXTRACT",
    "VEV_4000",
    "VEV_4500",
    "VEV_5000",
    "VEV_5100",
    "VEV_5200",
    "VEV_5300",
    "VEV_5400",
    "VEV_5500",
    "VEV_6000",
    "VEV_6500",
]

STRIKES = {
    "VEV_4000": 4000,
    "VEV_4500": 4500,
    "VEV_5000": 5000,
    "VEV_5100": 5100,
    "VEV_5200": 5200,
    "VEV_5300": 5300,
    "VEV_5400": 5400,
    "VEV_5500": 5500,
    "VEV_6000": 6000,
    "VEV_6500": 6500,
}

SIGMA = {
    4000: 0.5244,
    4500: 0.3056,
    5000: 0.2500,
    5100: 0.2550,
    5200: 0.24215,
    5300: 0.24455,
    5400: 0.22960,
    5500: 0.24845,
    6000: 0.3775,
    6500: 0.5701,
}

HORIZONS = [100, 500, 1000, 5000, 10000, 25000, 50000]


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call(spot: float, strike: int, t_years: float, sigma: float) -> float:
    if spot <= 0 or strike <= 0:
        return 0.0
    if t_years <= 0 or sigma <= 0:
        return max(0.0, spot - strike)
    vol_term = sigma * math.sqrt(t_years)
    if vol_term <= 0:
        return max(0.0, spot - strike)
    d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * t_years) / vol_term
    d2 = d1 - vol_term
    return spot * norm_cdf(d1) - strike * norm_cdf(d2)


def bs_delta(spot: float, strike: int, t_years: float, sigma: float) -> float:
    if spot <= 0 or strike <= 0:
        return 0.0
    if t_years <= 0 or sigma <= 0:
        return 1.0 if spot > strike else 0.0
    vol_term = sigma * math.sqrt(t_years)
    if vol_term <= 0:
        return 1.0 if spot > strike else 0.0
    d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * t_years) / vol_term
    return norm_cdf(d1)


def read_prices() -> dict[tuple[int, str], dict[int, dict[str, float]]]:
    books: dict[tuple[int, str], dict[int, dict[str, float]]] = defaultdict(dict)
    for path in sorted(ROUND_DIR.glob("prices_round_4_day_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter=";"):
                day = int(row["day"])
                ts = int(row["timestamp"])
                product = row["product"]
                def num(key: str) -> float | None:
                    raw = row.get(key, "")
                    return float(raw) if raw not in {"", None} else None

                bid = num("bid_price_1")
                ask = num("ask_price_1")
                books[(day, product)][ts] = {
                    "mid": float(row["mid_price"]),
                    "bid": bid if bid is not None else float("nan"),
                    "ask": ask if ask is not None else float("nan"),
                    "bid_vol": num("bid_volume_1") or 0.0,
                    "ask_vol": num("ask_volume_1") or 0.0,
                }
    return books


def read_trades() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(ROUND_DIR.glob("trades_round_4_day_*.csv")):
        day = int(path.stem.rsplit("_", 1)[1])
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter=";"):
                rows.append(
                    {
                        "day": day,
                        "timestamp": int(row["timestamp"]),
                        "buyer": row["buyer"],
                        "seller": row["seller"],
                        "product": row["symbol"],
                        "price": float(row["price"]),
                        "quantity": int(row["quantity"]),
                    }
                )
    return rows


def classify_aggressor(price: float, book: dict[str, float]) -> str:
    bid = book.get("bid", float("nan"))
    ask = book.get("ask", float("nan"))
    if math.isnan(bid) or math.isnan(ask):
        return "unknown"
    if price >= ask:
        return "buyer_aggressive"
    if price <= bid:
        return "seller_aggressive"
    return "inside"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def mark_diagnostics(books: dict[tuple[int, str], dict[int, dict[str, float]]], trades: list[dict[str, object]]) -> None:
    activity = Counter()
    pair_activity = Counter()
    signed = {h: defaultdict(float) for h in HORIZONS}
    qty = {h: defaultdict(float) for h in HORIZONS}
    events = {h: Counter() for h in HORIZONS}
    day_signed = {h: defaultdict(float) for h in HORIZONS}
    day_qty = {h: defaultdict(float) for h in HORIZONS}
    role_signed = {h: defaultdict(float) for h in HORIZONS}
    role_qty = {h: defaultdict(float) for h in HORIZONS}

    for trade in trades:
        day = int(trade["day"])
        ts = int(trade["timestamp"])
        product = str(trade["product"])
        buyer = str(trade["buyer"])
        seller = str(trade["seller"])
        price = float(trade["price"])
        q = int(trade["quantity"])
        book = books[(day, product)].get(ts)
        if not book:
            continue
        activity[(buyer, product)] += 1
        activity[(seller, product)] += 1
        pair_activity[(buyer, seller, product)] += 1
        role = classify_aggressor(price, book)
        base_mid = float(book["mid"])

        participants = [(buyer, 1), (seller, -1)]
        for horizon in HORIZONS:
            future = books[(day, product)].get(ts + horizon)
            if future is None:
                continue
            future_ret = float(future["mid"]) - base_mid
            for mark, sign in participants:
                key = (mark, product, horizon)
                value = sign * q * future_ret
                signed[horizon][(mark, product)] += value
                qty[horizon][(mark, product)] += q
                events[horizon][(mark, product)] += 1
                day_signed[horizon][(mark, product, day)] += value
                day_qty[horizon][(mark, product, day)] += q

            role_key_buyer = (buyer, product, role, "buyer")
            role_key_seller = (seller, product, role, "seller")
            role_signed[horizon][role_key_buyer] += q * future_ret
            role_qty[horizon][role_key_buyer] += q
            role_signed[horizon][role_key_seller] -= q * future_ret
            role_qty[horizon][role_key_seller] += q

    rows = []
    for horizon in HORIZONS:
        for (mark, product), total in signed[horizon].items():
            q = qty[horizon][(mark, product)]
            if q <= 0:
                continue
            day_scores = []
            represented_days = 0
            for day in (1, 2, 3):
                dq = day_qty[horizon].get((mark, product, day), 0.0)
                if dq > 0:
                    represented_days += 1
                    day_scores.append(day_signed[horizon][(mark, product, day)] / dq)
            sign_agree = 0.0
            if day_scores:
                overall_sign = 1 if total / q >= 0 else -1
                sign_agree = sum(1 for s in day_scores if (1 if s >= 0 else -1) == overall_sign) / len(day_scores)
            rows.append(
                {
                    "horizon": horizon,
                    "mark": mark,
                    "product": product,
                    "events": events[horizon][(mark, product)],
                    "quantity": q,
                    "score": total / q,
                    "total_signed_markout": total,
                    "days": represented_days,
                    "sign_agreement": sign_agree,
                    "activity_count": activity[(mark, product)],
                }
            )
    write_csv(OUT_DIR / "mark_scores.csv", rows)

    role_rows = []
    for horizon in HORIZONS:
        for (mark, product, role, side), total in role_signed[horizon].items():
            q = role_qty[horizon][(mark, product, role, side)]
            if q > 0:
                role_rows.append(
                    {
                        "horizon": horizon,
                        "mark": mark,
                        "product": product,
                        "role": role,
                        "side": side,
                        "quantity": q,
                        "score": total / q,
                    }
                )
    write_csv(OUT_DIR / "mark_aggressor_scores.csv", role_rows)

    pair_rows = [
        {"buyer": b, "seller": s, "product": p, "events": count}
        for (b, s, p), count in pair_activity.items()
    ]
    write_csv(OUT_DIR / "mark_pair_activity.csv", pair_rows)


def option_diagnostics(books: dict[tuple[int, str], dict[int, dict[str, float]]]) -> None:
    rows = []
    for day in (1, 2, 3):
        vfe = books[(day, "VELVETFRUIT_EXTRACT")]
        for product, strike in STRIKES.items():
            opt = books[(day, product)]
            for ts, opt_book in opt.items():
                spot_book = vfe.get(ts)
                if spot_book is None:
                    continue
                for start_days in (7.0, 6.0, 5.0, 4.0):
                    t_days = max(0.05, start_days - (day - 1) - ts / 1_000_000.0)
                    fair = bs_call(float(spot_book["mid"]), strike, t_days / 365.0, SIGMA[strike])
                    rows.append(
                        {
                            "day": day,
                            "timestamp": ts,
                            "product": product,
                            "strike": strike,
                            "start_days": start_days,
                            "mid": opt_book["mid"],
                            "bs_fair": fair,
                            "mid_minus_fair": float(opt_book["mid"]) - fair,
                            "buy_edge": fair - float(opt_book["ask"]),
                            "sell_edge": float(opt_book["bid"]) - fair,
                        }
                    )
    write_csv(OUT_DIR / "option_edges.csv", rows)

    summary = []
    grouped: dict[tuple[str, float], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["product"]), float(row["start_days"]))].append(row)
    for (product, start_days), group in grouped.items():
        buy_edges = [float(r["buy_edge"]) for r in group if not math.isnan(float(r["buy_edge"]))]
        sell_edges = [float(r["sell_edge"]) for r in group if not math.isnan(float(r["sell_edge"]))]
        residuals = [float(r["mid_minus_fair"]) for r in group]
        summary.append(
            {
                "product": product,
                "start_days": start_days,
                "n": len(group),
                "avg_mid_minus_fair": sum(residuals) / len(residuals),
                "buy_edge_gt_1_pct": sum(1 for x in buy_edges if x > 1.0) / len(buy_edges),
                "sell_edge_gt_1_pct": sum(1 for x in sell_edges if x > 1.0) / len(sell_edges),
                "buy_edge_p95": sorted(buy_edges)[int(0.95 * (len(buy_edges) - 1))],
                "sell_edge_p95": sorted(sell_edges)[int(0.95 * (len(sell_edges) - 1))],
            }
        )
    write_csv(OUT_DIR / "option_edge_summary.csv", summary)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    books = read_prices()
    trades = read_trades()
    mark_diagnostics(books, trades)
    option_diagnostics(books)
    print(OUT_DIR)


if __name__ == "__main__":
    main()
