from __future__ import annotations

import csv
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
OUT = ROUND_DIR / "research" / "outputs" / "missing_edge"
PLOTS = OUT / "plots"

LIMIT = 10
LEADERBOARD_PNLS = [
    453994.316, 436939.137, 382430.461, 336978.320, 315441.078,
    239598.633, 235382.488, 223894.555, 219769.625, 207795.242,
    207174.426, 201767.156, 192881.688, 184660.242, 183699.484,
    183507.320, 182381.328, 178684.484, 168744.859, 161241.523,
    159550.727, 155540.445, 154544.516, 154270.305, 153493.931,
    152122.180, 152103.461, 152045.320, 152045.320, 152034.320,
    152029.039, 151761.352, 151072.671, 150884.242, 150879.242,
    150832.538, 150390.523, 150112.537, 149585.875, 147648.242,
    147370.242, 147307.445, 146547.320, 145669.555, 144588.664,
    140560.898, 140420.272, 137335.156, 137179.939, 136486.631,
    132388.614, 130019.922, 129601.175, 128821.633, 126497.250,
    126433.848, 124112.313, 122983.631, 122089.246, 119331.241,
    114411.436, 114406.867, 113285.262, 111136.984, 111074.054,
    109229.275, 108913.207, 108233.281, 107355.328, 107331.445,
    106718.098, 104630.730, 103769.813, 103133.486, 103037.316,
    100791.309, 100527.602, 99892.023, 99570.848, 98677.730,
    97357.299, 96997.055, 95543.649, 94726.344, 92937.852,
    90574.574, 89879.531, 89869.480, 88529.902, 88471.016,
    85887.883, 84802.945, 84116.828, 84050.070, 81684.086,
    79965.852, 78283.707, 78187.125, 77972.125, 77335.539,
]


CATEGORY_PREFIXES = {
    "PEBBLES": "PEBBLES_",
    "SNACKPACK": "SNACKPACK_",
    "TRANSLATOR": "TRANSLATOR_",
    "UV_VISOR": "UV_VISOR_",
    "GALAXY_SOUNDS": "GALAXY_SOUNDS_",
    "MICROCHIP": "MICROCHIP_",
    "OXYGEN_SHAKE": "OXYGEN_SHAKE_",
    "PANEL": "PANEL_",
    "SLEEP_POD": "SLEEP_POD_",
    "ROBOT": "ROBOT_",
}

NAME_FEATURES = {
    "PEBBLES": {
        "PEBBLES_XS": {"ordinal": 1, "size": 1},
        "PEBBLES_S": {"ordinal": 2, "size": 2},
        "PEBBLES_M": {"ordinal": 3, "size": 3},
        "PEBBLES_L": {"ordinal": 4, "size": 4},
        "PEBBLES_XL": {"ordinal": 5, "size": 5},
    },
    "PANEL": {
        "PANEL_1X2": {"width": 1, "height": 2, "area": 2, "perimeter": 6, "ratio": 0.5},
        "PANEL_1X4": {"width": 1, "height": 4, "area": 4, "perimeter": 10, "ratio": 0.25},
        "PANEL_2X2": {"width": 2, "height": 2, "area": 4, "perimeter": 8, "ratio": 1.0},
        "PANEL_2X4": {"width": 2, "height": 4, "area": 8, "perimeter": 12, "ratio": 0.5},
        "PANEL_4X4": {"width": 4, "height": 4, "area": 16, "perimeter": 16, "ratio": 1.0},
    },
    "MICROCHIP": {
        "MICROCHIP_CIRCLE": {"sides": 99, "curved": 1, "ordinal": 5},
        "MICROCHIP_OVAL": {"sides": 99, "curved": 1, "ordinal": 4},
        "MICROCHIP_TRIANGLE": {"sides": 3, "curved": 0, "ordinal": 1},
        "MICROCHIP_SQUARE": {"sides": 4, "curved": 0, "ordinal": 2},
        "MICROCHIP_RECTANGLE": {"sides": 4, "curved": 0, "ordinal": 3},
    },
    "UV_VISOR": {
        "UV_VISOR_RED": {"wavelength": 700, "ordinal": 6},
        "UV_VISOR_ORANGE": {"wavelength": 610, "ordinal": 5},
        "UV_VISOR_YELLOW": {"wavelength": 580, "ordinal": 4},
        "UV_VISOR_AMBER": {"wavelength": 590, "ordinal": 4.5},
        "UV_VISOR_MAGENTA": {"wavelength": 450, "ordinal": 1},
    },
    "SLEEP_POD": {
        "SLEEP_POD_COTTON": {"ordinal": 2, "synthetic": 0, "premium": 2},
        "SLEEP_POD_POLYESTER": {"ordinal": 1, "synthetic": 1, "premium": 1},
        "SLEEP_POD_NYLON": {"ordinal": 1.5, "synthetic": 1, "premium": 1},
        "SLEEP_POD_SUEDE": {"ordinal": 4, "synthetic": 0, "premium": 4},
        "SLEEP_POD_LAMB_WOOL": {"ordinal": 5, "synthetic": 0, "premium": 5},
    },
}

OFFICIAL_CANDIDATE_PNL = {
    "round5_candidate_1.py": {"PEBBLES_XL": 1410, "PEBBLES_L": 644, "PEBBLES_M": -104, "PEBBLES_XS": -85},
    "round5_candidate_2.py": {"ROBOT_LAUNDRY": -8782, "MICROCHIP_OVAL": -8732, "TRANSLATOR_GRAPHITE_MIST": -8191, "TRANSLATOR_ASTRO_BLACK": -4756, "SLEEP_POD_SUEDE": 152},
    "round5_candidate_3.py": {"PEBBLES_XL": 3273, "PANEL_1X4": 2022, "PEBBLES_L": 2007, "ROBOT_LAUNDRY": -4982, "OXYGEN_SHAKE_CHOCOLATE": -3214},
    "round5_candidate_4.py": {"ROBOT_IRONING": 3106, "ROBOT_DISHES": 1201, "SNACKPACK_CHOCOLATE": 901, "SNACKPACK_VANILLA": -1340, "SNACKPACK_RASPBERRY": -1040},
    "round5_candidate_5.py": {"PEBBLES_XL": 3740, "SLEEP_POD_SUEDE": 2662, "OXYGEN_SHAKE_EVENING_BREATH": 1749, "TRANSLATOR_GRAPHITE_MIST": 1193, "MICROCHIP_OVAL": -3482},
}


def category(product: str) -> str:
    for name, prefix in CATEGORY_PREFIXES.items():
        if product.startswith(prefix):
            return name
    return product.split("_", 1)[0]


def load_prices() -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        path = ROUND_DIR / f"prices_round_5_day_{day}.csv"
        df = pd.read_csv(path, sep=";")
        df["day"] = day
        df["category"] = df["product"].map(category)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_trades() -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        path = ROUND_DIR / f"trades_round_5_day_{day}.csv"
        df = pd.read_csv(path, sep=";")
        df["day"] = day
        df["category"] = df["symbol"].map(category)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def make_wide(prices: pd.DataFrame, field: str) -> dict[int, pd.DataFrame]:
    out = {}
    for day, sub in prices.groupby("day"):
        out[int(day)] = sub.pivot(index="timestamp", columns="product", values=field).sort_index()
    return out


def dp_taker_oracle(bids: np.ndarray, asks: np.ndarray, mids: np.ndarray) -> tuple[float, list[int]]:
    positions = np.arange(-LIMIT, LIMIT + 1)
    npos = len(positions)
    dp = np.full(npos, -1e18)
    dp[LIMIT] = 0.0
    prev_choice: list[np.ndarray] = []
    delta = positions[None, :] - positions[:, None]
    buy_qty = np.maximum(delta, 0)
    sell_qty = np.maximum(-delta, 0)
    for t in range(len(mids)):
        bid = bids[t]
        ask = asks[t]
        vals = dp[:, None] - buy_qty * ask + sell_qty * bid
        prev_idx = np.argmax(vals, axis=0).astype(np.int16)
        dp = vals[prev_idx, np.arange(npos)]
        prev_choice.append(prev_idx)
    terminal = dp + positions * mids[-1]
    idx = int(np.argmax(terminal))
    path = []
    for t in range(len(prev_choice) - 1, -1, -1):
        path.append(int(positions[idx]))
        idx = int(prev_choice[t][idx])
    path.reverse()
    return float(terminal.max()), path


def simple_oracles(mid: np.ndarray, bid: np.ndarray, ask: np.ndarray) -> dict[str, float]:
    diff1 = np.diff(mid)
    one_step_mid = LIMIT * float(np.abs(diff1).sum())
    trend_end = LIMIT * float(abs(mid[-1] - mid[0]))
    best_long = LIMIT * float(mid[-1] - ask[0])
    best_short = LIMIT * float(bid[0] - mid[-1])
    end_hold = max(best_long, best_short, 0.0)

    vals = {}
    for h in [5, 10, 20, 50, 100]:
        future = mid[h:] - mid[:-h]
        vals[f"h{h}_direction_mid"] = LIMIT * float(np.abs(future).sum() / h)
    vals.update({"one_step_mid": one_step_mid, "trend_end_hold": trend_end, "best_entry_to_end": end_hold})
    return vals


def oracle_tables(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[int]]]:
    rows = []
    path_examples: dict[str, list[int]] = {}
    for (day, product), sub in prices.sort_values(["day", "timestamp"]).groupby(["day", "product"]):
        mid = sub["mid_price"].to_numpy(float)
        bid = sub["bid_price_1"].to_numpy(float)
        ask = sub["ask_price_1"].to_numpy(float)
        dp, path = dp_taker_oracle(bid, ask, mid)
        extra = simple_oracles(mid, bid, ask)
        row = {
            "day": int(day),
            "product": product,
            "category": category(product),
            "dp_taker_oracle": dp,
            "range_x_limit": LIMIT * float(mid.max() - mid.min()),
            "realized_abs_move_x_limit": extra["one_step_mid"],
            "trend_end_hold": extra["trend_end_hold"],
            "best_entry_to_end": extra["best_entry_to_end"],
            "h10_direction_mid": extra["h10_direction_mid"],
            "h50_direction_mid": extra["h50_direction_mid"],
            "h100_direction_mid": extra["h100_direction_mid"],
            "avg_spread": float((sub["ask_price_1"] - sub["bid_price_1"]).mean()),
            "median_spread": float((sub["ask_price_1"] - sub["bid_price_1"]).median()),
            "mid_std": float(np.std(mid)),
            "mid_first": float(mid[0]),
            "mid_last": float(mid[-1]),
            "mid_min": float(mid.min()),
            "mid_max": float(mid.max()),
        }
        rows.append(row)
        if day == 4 and len(path_examples) < 20:
            path_examples[f"{product}_day{day}"] = path
    product_day = pd.DataFrame(rows)
    agg = product_day.groupby(["product", "category"], as_index=False).agg(
        days=("day", "count"),
        dp_taker_sum=("dp_taker_oracle", "sum"),
        dp_taker_day4=("dp_taker_oracle", lambda s: float(product_day.loc[s.index][product_day.loc[s.index, "day"] == 4]["dp_taker_oracle"].sum())),
        range_sum=("range_x_limit", "sum"),
        best_entry_to_end_sum=("best_entry_to_end", "sum"),
        h50_sum=("h50_direction_mid", "sum"),
        avg_spread=("avg_spread", "mean"),
        median_spread=("median_spread", "median"),
        mid_std_avg=("mid_std", "mean"),
    )
    agg = agg.sort_values("dp_taker_day4", ascending=False)
    cat = product_day.groupby(["category", "day"], as_index=False).agg(
        dp_taker_oracle=("dp_taker_oracle", "sum"),
        range_x_limit=("range_x_limit", "sum"),
        best_entry_to_end=("best_entry_to_end", "sum"),
        h50_direction_mid=("h50_direction_mid", "sum"),
        products=("product", "nunique"),
    )
    cat_sum = cat.groupby("category", as_index=False).agg(
        dp_taker_sum=("dp_taker_oracle", "sum"),
        dp_taker_day4=("dp_taker_oracle", lambda s: float(cat.loc[s.index][cat.loc[s.index, "day"] == 4]["dp_taker_oracle"].sum())),
        range_sum=("range_x_limit", "sum"),
        best_entry_to_end_sum=("best_entry_to_end", "sum"),
        h50_sum=("h50_direction_mid", "sum"),
        products=("products", "max"),
    ).sort_values("dp_taker_day4", ascending=False)
    return agg, cat_sum, path_examples


def write_leaderboard_notes() -> None:
    pnls = np.array(LEADERBOARD_PNLS)
    rows = []
    for target in [10000, 50000, 100000, 150000, 250000, 450000]:
        for fills in [500, 1000, 2500, 5000, 10000, 25000]:
            rows.append(
                {
                    "target_pnl": target,
                    "fills": fills,
                    "avg_edge_per_fill": target / fills,
                    "avg_edge_per_unit_if_fill_size_10": target / fills / 10,
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "leaderboard_required_edge_estimates.csv", index=False)
    notes = f"""# Leaderboard Gap Notes

Top-100 official scores range from {pnls.min():,.0f} to {pnls.max():,.0f}; median top-100 score is {np.median(pnls):,.0f}. Our best official score is 2,821 and best official-window replay is about 8,302.

This is not a parameter-tuning gap. To reach 100k with 10-lot fills requires roughly 10,000 one-tick/unit edges, 2,000 five-tick/unit edges, or 1,000 ten-tick/unit edges. The top score around 454k requires a repeated high-hit-rate source of edge, not sparse single-product z-score trades.

The leaderboard drawdowns are also revealing: many 100k-450k entries have max drawdown near 4k-10k and recovery factors above 15, with the top two above 100. That profile is closer to systematic spread/fair-value harvesting or a deterministic category relation than to noisy forecasting.

Duplicate clusters around 150k suggest a common discoverable public structure. The edge likely comes from a product/category formula, basket/factor residual, market-making/fill mechanism, or an online-detectable official-window regime that our generic screens missed.
"""
    (OUT / "leaderboard_gap_notes.md").write_text(notes, encoding="utf-8")


def product_name_structure_tests(prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, fmap in NAME_FEATURES.items():
        products = list(fmap)
        sub = prices[prices["product"].isin(products)]
        if sub.empty:
            continue
        for day, day_sub in sub.groupby("day"):
            wide = day_sub.pivot(index="timestamp", columns="product", values="mid_price").dropna()
            y_products = [p for p in products if p in wide.columns]
            feature_names = sorted({k for p in y_products for k in fmap[p]})
            X = np.array([[fmap[p].get(f, 0.0) for f in feature_names] for p in y_products], dtype=float)
            X = np.column_stack([np.ones(len(y_products)), X])
            preds = []
            actuals = []
            for _, row in wide[y_products].iterrows():
                y = row.to_numpy(float)
                coef, *_ = np.linalg.lstsq(X, y, rcond=None)
                pred = X @ coef
                preds.append(pred)
                actuals.append(y)
            pred_arr = np.vstack(preds)
            actual_arr = np.vstack(actuals)
            ss_res = float(((actual_arr - pred_arr) ** 2).sum())
            ss_tot = float(((actual_arr - actual_arr.mean()) ** 2).sum())
            r2 = 1 - ss_res / ss_tot if ss_tot else 0
            rmse = math.sqrt(ss_res / actual_arr.size)
            rows.append(
                {
                    "category": cat,
                    "day": int(day),
                    "representation": "+".join(feature_names),
                    "r2_cross_section": r2,
                    "rmse": rmse,
                    "mean_abs_residual": float(np.abs(actual_arr - pred_arr).mean()),
                    "products": ",".join(y_products),
                }
            )
    return pd.DataFrame(rows).sort_values(["r2_cross_section", "mean_abs_residual"], ascending=[False, True])


def category_formula_search(prices: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    rows = []
    notes = ["# Category Formula Candidates", ""]
    for cat, sub in prices.groupby("category"):
        wide_by_day = {}
        products = sorted(sub["product"].unique())
        for day, day_sub in sub.groupby("day"):
            wide_by_day[int(day)] = day_sub.pivot(index="timestamp", columns="product", values="mid_price").dropna()
        for target in products:
            train_days = [2, 3]
            if any(target not in wide_by_day[d].columns for d in train_days + [4]):
                continue
            others = [p for p in products if p != target and all(p in wide_by_day[d].columns for d in train_days + [4])]
            if len(others) < 2:
                continue
            train = pd.concat([wide_by_day[d] for d in train_days])
            X = train[others].to_numpy(float)
            y = train[target].to_numpy(float)
            X1 = np.column_stack([np.ones(len(X)), X])
            coef, *_ = np.linalg.lstsq(X1, y, rcond=None)
            for day in [2, 3, 4]:
                w = wide_by_day[day]
                pred = np.column_stack([np.ones(len(w)), w[others].to_numpy(float)]) @ coef
                resid = w[target].to_numpy(float) - pred
                rmse = float(np.sqrt(np.mean(resid ** 2)))
                corr_next = np.nan
                if len(resid) > 2:
                    corr_next = float(np.corrcoef(resid[:-1], np.diff(w[target].to_numpy(float)))[0, 1])
                rows.append(
                    {
                        "category": cat,
                        "target": target,
                        "drivers": ",".join(others),
                        "day": day,
                        "train_days": "2,3",
                        "rmse": rmse,
                        "resid_std": float(np.std(resid)),
                        "resid_mean_abs": float(np.mean(np.abs(resid))),
                        "resid_min": float(np.min(resid)),
                        "resid_max": float(np.max(resid)),
                        "resid_next_return_corr": corr_next,
                        "coef": json.dumps([float(x) for x in coef]),
                    }
                )
    df = pd.DataFrame(rows)
    summary = df[df["day"] == 4].sort_values("resid_std").head(30)
    for _, row in summary.iterrows():
        notes.append(
            f"- `{row['target']}` from `{row['category']}` has day-4 residual std {row['resid_std']:.2f} "
            f"using `{row['drivers']}`; next-return corr {row['resid_next_return_corr']:.3f}."
        )
    return df, "\n".join(notes) + "\n"


def official_reverse_engineering(product_oracle: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    day4 = product_oracle[["product", "category", "dp_taker_day4", "range_sum", "h50_sum"]].copy()
    all_traded = set()
    candidate_rows = []
    for cand, pnl_map in OFFICIAL_CANDIDATE_PNL.items():
        for p, pnl in pnl_map.items():
            all_traded.add(p)
            oracle = day4[day4["product"] == p]
            candidate_rows.append(
                {
                    "candidate": cand,
                    "product": p,
                    "category": category(p),
                    "candidate_official_product_pnl": pnl,
                    "day4_dp_taker_oracle": float(oracle["dp_taker_day4"].iloc[0]) if not oracle.empty else np.nan,
                    "capture_ratio_vs_taker_oracle": float(pnl / oracle["dp_taker_day4"].iloc[0]) if not oracle.empty and oracle["dp_taker_day4"].iloc[0] else np.nan,
                    "traded_by_us": True,
                }
            )
    for _, row in day4.sort_values("dp_taker_day4", ascending=False).head(50).iterrows():
        if row["product"] not in all_traded:
            candidate_rows.append(
                {
                    "candidate": "MISSED_BY_CANDIDATES_1_5",
                    "product": row["product"],
                    "category": row["category"],
                    "candidate_official_product_pnl": 0,
                    "day4_dp_taker_oracle": row["dp_taker_day4"],
                    "capture_ratio_vs_taker_oracle": 0,
                    "traded_by_us": False,
                }
            )
    df = pd.DataFrame(candidate_rows).sort_values("day4_dp_taker_oracle", ascending=False)
    missed = day4[~day4["product"].isin(all_traded)].sort_values("dp_taker_day4", ascending=False).head(30)
    missed_md = ["# Official Window Missed Products", ""]
    for _, row in missed.iterrows():
        missed_md.append(f"- `{row['product']}` (`{row['category']}`): day-4 taker oracle {row['dp_taker_day4']:.0f}.")
    failure = """# Official Window Failure Modes

The official window contains far more opportunity than our candidates captured. Candidates 1-10 mostly trade PEBBLES/ROBOT subsets and miss large day-4 oracle capacity across several other categories. Our product PnL capture ratios are tiny relative to even a taker-only oracle, so the main failure is not only sizing. It is missing the right products/signals and using generic z-score/microstructure rules instead of a high-hit-rate relation.

Candidate 2 demonstrates that simply trading more products is not enough: broad survivor baskets overtrade and produce adverse markout. The missing edge must be selective and structural.
"""
    return df, "\n".join(missed_md) + "\n", failure


def signal_search(prices: pd.DataFrame, trades: pd.DataFrame, product_oracle: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    high_products = product_oracle.sort_values("dp_taker_day4", ascending=False).head(20)["product"].tolist()
    rows = []
    for product in high_products:
        for day, sub in prices[prices["product"] == product].sort_values(["day", "timestamp"]).groupby("day"):
            mid = sub["mid_price"].to_numpy(float)
            bid = sub["bid_price_1"].to_numpy(float)
            ask = sub["ask_price_1"].to_numpy(float)
            bidv = sub["bid_volume_1"].to_numpy(float)
            askv = -sub["ask_volume_1"].to_numpy(float)
            bid_prices = sub[["bid_price_1", "bid_price_2", "bid_price_3"]].fillna(0).to_numpy(float)
            ask_prices = sub[["ask_price_1", "ask_price_2", "ask_price_3"]].fillna(0).to_numpy(float)
            bid_volumes = sub[["bid_volume_1", "bid_volume_2", "bid_volume_3"]].fillna(0).to_numpy(float)
            ask_volumes = -sub[["ask_volume_1", "ask_volume_2", "ask_volume_3"]].fillna(0).to_numpy(float)
            imb = (bidv - askv) / np.maximum(1.0, bidv + askv)
            spread = ask - bid
            for name, signal in [
                ("imbalance", imb),
                ("microprice", ((ask * bidv + bid * askv) / np.maximum(1.0, bidv + askv) - mid) / np.maximum(1.0, spread)),
                ("ret_1_momentum", np.r_[0, np.diff(mid)]),
                ("ret_10_momentum", np.r_[np.zeros(10), mid[10:] - mid[:-10]]),
                ("ret_50_momentum", np.r_[np.zeros(50), mid[50:] - mid[:-50]]),
                ("ret_10_reversal", -np.r_[np.zeros(10), mid[10:] - mid[:-10]]),
                ("ret_50_reversal", -np.r_[np.zeros(50), mid[50:] - mid[:-50]]),
            ]:
                executable_rows = []
                finite_signal = signal[np.isfinite(signal)]
                if len(finite_signal) == 0:
                    continue
                for pct in [60, 70, 80, 90, 95]:
                    threshold = np.nanpercentile(np.abs(finite_signal), pct)
                    target = np.where(signal > threshold, LIMIT, np.where(signal < -threshold, -LIMIT, 0))
                    cash = 0.0
                    cur = 0
                    trades_count = 0
                    vol_cash = 0.0
                    vol_cur = 0
                    vol_trades_count = 0
                    depth_cash = 0.0
                    depth_cur = 0
                    depth_trades_count = 0
                    for i, tgt in enumerate(target):
                        delta = int(tgt - cur)
                        if delta > 0:
                            cash -= delta * ask[i]
                            trades_count += abs(delta)
                        elif delta < 0:
                            cash += (-delta) * bid[i]
                            trades_count += abs(delta)
                        cur = int(tgt)

                        vol_delta = int(tgt - vol_cur)
                        if vol_delta > 0:
                            fill = min(vol_delta, max(0, int(askv[i])))
                            vol_cash -= fill * ask[i]
                            vol_cur += fill
                            vol_trades_count += fill
                        elif vol_delta < 0:
                            fill = min(-vol_delta, max(0, int(bidv[i])))
                            vol_cash += fill * bid[i]
                            vol_cur -= fill
                            vol_trades_count += fill

                        depth_delta = int(tgt - depth_cur)
                        remaining = abs(depth_delta)
                        if depth_delta > 0:
                            for px, qty_avail in zip(ask_prices[i], ask_volumes[i]):
                                if remaining <= 0:
                                    break
                                if px <= 0 or qty_avail <= 0:
                                    continue
                                fill = min(remaining, int(qty_avail))
                                depth_cash -= fill * px
                                depth_cur += fill
                                depth_trades_count += fill
                                remaining -= fill
                        elif depth_delta < 0:
                            for px, qty_avail in zip(bid_prices[i], bid_volumes[i]):
                                if remaining <= 0:
                                    break
                                if px <= 0 or qty_avail <= 0:
                                    continue
                                fill = min(remaining, int(qty_avail))
                                depth_cash += fill * px
                                depth_cur -= fill
                                depth_trades_count += fill
                                remaining -= fill
                    pnl = cash + cur * mid[-1]
                    vol_pnl = vol_cash + vol_cur * mid[-1]
                    depth_pnl = depth_cash + depth_cur * mid[-1]
                    executable_rows.append((pct, float(pnl), int(trades_count), float(vol_pnl), int(vol_trades_count), float(depth_pnl), int(depth_trades_count)))
                best_exec = max(executable_rows, key=lambda item: item[1])
                best_vol_exec = max(executable_rows, key=lambda item: item[3])
                best_depth_exec = max(executable_rows, key=lambda item: item[5])
                for hold in [1, 5, 10, 25, 50]:
                    if len(mid) <= hold + 2:
                        continue
                    s = signal[:-hold]
                    fwd = mid[hold:] - mid[:-hold]
                    valid = np.isfinite(s) & np.isfinite(fwd)
                    if valid.sum() < 20 or np.std(s[valid]) < 1e-9:
                        continue
                    corr = float(np.corrcoef(s[valid], fwd[valid])[0, 1])
                    thresh = np.nanpercentile(np.abs(s[valid]), 75)
                    pos = np.where(s > thresh, 1, np.where(s < -thresh, -1, 0))
                    gross = LIMIT * float((pos[valid] * fwd[valid]).sum() / hold)
                    rows.append(
                        {
                            "product": product,
                            "category": category(product),
                            "day": int(day),
                            "signal": name,
                            "hold": hold,
                            "corr_fwd_mid": corr,
                            "gross_directional_pnl_proxy": gross,
                            "best_executable_threshold_pct": best_exec[0],
                            "best_executable_taker_pnl": best_exec[1],
                            "best_executable_units_traded": best_exec[2],
                            "best_top1_volume_threshold_pct": best_vol_exec[0],
                            "best_top1_volume_limited_pnl": best_vol_exec[3],
                            "best_top1_volume_units_traded": best_vol_exec[4],
                            "best_top3_depth_threshold_pct": best_depth_exec[0],
                            "best_top3_depth_limited_pnl": best_depth_exec[5],
                            "best_top3_depth_units_traded": best_depth_exec[6],
                            "samples": int(valid.sum()),
                        }
                    )
    df = pd.DataFrame(rows).sort_values(["best_executable_taker_pnl", "gross_directional_pnl_proxy"], ascending=False)
    notes = ["# High Ceiling Signal Notes", ""]
    for _, row in df.head(30).iterrows():
        notes.append(
            f"- `{row['product']}` day {row['day']} `{row['signal']}` hold {row['hold']}: "
            f"exec {row['best_executable_taker_pnl']:.0f} at pct {row['best_executable_threshold_pct']}, "
            f"top1-volume exec {row['best_top1_volume_limited_pnl']:.0f}, "
            f"top3-depth exec {row['best_top3_depth_limited_pnl']:.0f}, "
            f"proxy {row['gross_directional_pnl_proxy']:.0f}, corr {row['corr_fwd_mid']:.3f}."
        )
    return df, "\n".join(notes) + "\n"


def strategy_docs(product_oracle: pd.DataFrame, category_oracle: pd.DataFrame, formula_df: pd.DataFrame, signal_df: pd.DataFrame) -> None:
    top_products = product_oracle.head(12)
    top_categories = category_oracle.head(8)
    text = ["# High Ceiling Strategy Directions", ""]
    text.append("A strategy direction is credible only if it targets products/categories whose day-4 oracle capacity is far above 100k in aggregate or captures a deterministic relation that can be repeated at size.")
    text.append("")
    text.append("## Direction 1: High-ceiling product momentum/reversal search")
    text.append("Use the top day-4 oracle products, not the products from our candidates. Fit only online signals that show high proxy PnL in `high_ceiling_signal_search.csv`; size to +/-10 and cross only when expected move exceeds spread by a large margin.")
    text.append("")
    text.append("## Direction 2: Category formula residual arbitrage")
    text.append("Use leave-one-product fair values inside the best formula categories. Trade only residual extremes with fast reversion evidence. This is closer to the leaderboard profile than generic z-scores because it can fire across many products while keeping drawdown low.")
    text.append("")
    text.append("## Direction 3: Basket/product-name puzzle strategy")
    text.append("Panel dimensions, pebble sizes, color/shape/material orderings should be translated into fair-value curves. If a name-driven representation gives stable residuals, trade the mispriced product versus its synthetic category fair value.")
    text.append("")
    text.append("## Direction 4: Spread-capture plus fair-value filter")
    text.append("Top avg-fill values imply many submissions quote size. Use fair-value confidence from formulas to place full-size passive orders on both sides only where adverse selection is low, instead of our previous single-direction weak orders.")
    text.append("")
    text.append("Top oracle products:")
    for _, row in top_products.iterrows():
        text.append(f"- `{row['product']}` `{row['category']}` day-4 taker oracle {row['dp_taker_day4']:.0f}, three-day oracle {row['dp_taker_sum']:.0f}.")
    text.append("")
    text.append("Top oracle categories:")
    for _, row in top_categories.iterrows():
        text.append(f"- `{row['category']}` day-4 taker oracle {row['dp_taker_day4']:.0f}, three-day oracle {row['dp_taker_sum']:.0f}.")
    (OUT / "high_ceiling_strategy_directions.md").write_text("\n".join(text) + "\n", encoding="utf-8")

    plan = ["# Next Candidate Plan", ""]
    plan.append("Do not build another low-ceiling candidate until one of these directions is implemented directly.")
    plan.append("")
    plan.append("1. Build a high-ceiling oracle-guided candidate over the top 10 day-4 oracle products. Start with the best signal rows in `high_ceiling_signal_search.csv`, but require online execution and spread-aware entry.")
    plan.append("2. Build a category formula residual candidate from the best leave-one-product formulas. It should trade multiple category products with full +/-10 when residual z-score and reversion evidence agree.")
    plan.append("3. Build a product-name puzzle candidate for PANEL/PEBBLES/MICROCHIP/UV/SLEEP where physical/name encodings explain prices. Trade deviations from the encoded curve, not generic time-series z-scores.")
    plan.append("4. Build a market-making/fair-value candidate: quote 10-lot passive orders around synthetic fair value and aggressively flatten when fill direction disagrees with the formula.")
    plan.append("")
    plan.append("Old candidate ideas to abandon: broad nested survivor basket, raw ROBOT microstructure, Snackpack relative factor, broad diversified blend, and single-product PEBBLES variants as final answers. They may be components, but they do not explain 100k+.")
    (OUT / "next_candidate_plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8")


def oracle_path_examples(path_examples: dict[str, list[int]], product_oracle: pd.DataFrame) -> None:
    lines = ["# Oracle Path Examples", ""]
    for _, row in product_oracle.head(12).iterrows():
        key = f"{row['product']}_day4"
        path = path_examples.get(key, [])
        if not path:
            continue
        changes = sum(1 for a, b in zip(path, path[1:]) if a != b)
        lines.append(
            f"- `{row['product']}` day 4: taker oracle {row['dp_taker_day4']:.0f}; "
            f"path changes {changes}; first positions {path[:20]}."
        )
    (OUT / "oracle_path_examples.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    write_leaderboard_notes()

    prices = load_prices()
    trades = load_trades()

    product_oracle, category_oracle, paths = oracle_tables(prices)
    product_oracle.to_csv(OUT / "oracle_ceiling_by_product.csv", index=False)
    category_oracle.to_csv(OUT / "oracle_ceiling_by_category.csv", index=False)
    oracle_path_examples(paths, product_oracle)

    structure = product_name_structure_tests(prices)
    structure.to_csv(OUT / "product_name_structure_tests.csv", index=False)

    formula_df, formula_md = category_formula_search(prices)
    formula_df.to_csv(OUT / "category_structure_rankings.csv", index=False)
    (OUT / "category_formula_candidates.md").write_text(formula_md, encoding="utf-8")

    official_df, missed_md, failure_md = official_reverse_engineering(product_oracle)
    official_df.to_csv(OUT / "official_window_oracle_vs_candidates.csv", index=False)
    (OUT / "official_window_missed_products.md").write_text(missed_md, encoding="utf-8")
    (OUT / "official_window_failure_modes.md").write_text(failure_md, encoding="utf-8")

    signal_df, signal_notes = signal_search(prices, trades, product_oracle)
    signal_df.to_csv(OUT / "high_ceiling_signal_search.csv", index=False)
    (OUT / "high_ceiling_signal_notes.md").write_text(signal_notes, encoding="utf-8")

    strategy_docs(product_oracle, category_oracle, formula_df, signal_df)
    print(f"Wrote missing-edge outputs to {OUT}")


if __name__ == "__main__":
    main()
