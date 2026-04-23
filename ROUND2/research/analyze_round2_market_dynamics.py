from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "research" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DAYS = [-1, 0, 1]
PRODUCTS = ["ASH_COATED_OSMIUM", "INTARIAN_PEPPER_ROOT"]


def load_prices() -> pd.DataFrame:
    frames = []
    for day in DAYS:
        df = pd.read_csv(ROOT / f"prices_round_2_day_{day}.csv", sep=";")
        df["source_day"] = day
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    return data


def load_trades() -> pd.DataFrame:
    frames = []
    for day in DAYS:
        df = pd.read_csv(ROOT / f"trades_round_2_day_{day}.csv", sep=";")
        df["source_day"] = day
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def prepare_book_features(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.copy()
    for col in [
        "bid_price_1",
        "bid_price_2",
        "bid_price_3",
        "ask_price_1",
        "ask_price_2",
        "ask_price_3",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in [
        "bid_volume_1",
        "bid_volume_2",
        "bid_volume_3",
        "ask_volume_1",
        "ask_volume_2",
        "ask_volume_3",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    valid = (df["bid_price_1"] > 0) & (df["ask_price_1"] > 0)
    df = df.loc[valid].copy()

    df["mid"] = (df["bid_price_1"] + df["ask_price_1"]) / 2.0
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["ask_size_1"] = df["ask_volume_1"].abs()
    df["bid_size_1"] = df["bid_volume_1"].abs()
    df["imbalance_1"] = (
        (df["bid_size_1"] - df["ask_size_1"])
        / (df["bid_size_1"] + df["ask_size_1"]).replace(0.0, np.nan)
    ).fillna(0.0)
    df["microprice_1"] = (
        df["ask_price_1"] * df["bid_size_1"] + df["bid_price_1"] * df["ask_size_1"]
    ) / (df["bid_size_1"] + df["ask_size_1"]).replace(0.0, np.nan)
    df["microprice_1"] = df["microprice_1"].fillna(df["mid"])
    df["microprice_gap"] = df["microprice_1"] - df["mid"]

    wall_bid = pd.concat(
        {
            "p1": df["bid_price_1"],
            "p2": df["bid_price_2"],
            "p3": df["bid_price_3"],
        },
        axis=1,
    )
    wall_bid_vol = pd.concat(
        {
            "p1": df["bid_volume_1"].abs(),
            "p2": df["bid_volume_2"].abs(),
            "p3": df["bid_volume_3"].abs(),
        },
        axis=1,
    )
    wall_ask = pd.concat(
        {
            "p1": df["ask_price_1"],
            "p2": df["ask_price_2"],
            "p3": df["ask_price_3"],
        },
        axis=1,
    )
    wall_ask_vol = pd.concat(
        {
            "p1": df["ask_volume_1"].abs(),
            "p2": df["ask_volume_2"].abs(),
            "p3": df["ask_volume_3"].abs(),
        },
        axis=1,
    )

    wall_bid_idx = wall_bid_vol.idxmax(axis=1)
    wall_ask_idx = wall_ask_vol.idxmax(axis=1)
    df["wall_bid"] = [wall_bid.loc[i, j] for i, j in zip(df.index, wall_bid_idx)]
    df["wall_ask"] = [wall_ask.loc[i, j] for i, j in zip(df.index, wall_ask_idx)]
    df["wall_mid"] = (df["wall_bid"] + df["wall_ask"]) / 2.0
    df["wall_gap"] = df["wall_mid"] - df["mid"]

    depth_bid = (
        df["bid_volume_1"].abs() + df["bid_volume_2"].abs() + df["bid_volume_3"].abs()
    )
    depth_ask = (
        df["ask_volume_1"].abs() + df["ask_volume_2"].abs() + df["ask_volume_3"].abs()
    )
    df["depth_imbalance_3"] = (
        (depth_bid - depth_ask) / (depth_bid + depth_ask).replace(0.0, np.nan)
    ).fillna(0.0)

    df = df.sort_values(["product", "source_day", "timestamp"]).reset_index(drop=True)
    df["next_mid"] = df.groupby(["product", "source_day"])["mid"].shift(-1)
    df["next_ret"] = df["next_mid"] - df["mid"]
    df["prev_mid"] = df.groupby(["product", "source_day"])["mid"].shift(1)
    df["prev_ret"] = df["mid"] - df["prev_mid"]
    df["lead2_ret"] = df.groupby(["product", "source_day"])["mid"].shift(-2) - df["mid"]
    return df


def linear_fit(y: np.ndarray, x: np.ndarray) -> tuple[float, float]:
    model = LinearRegression().fit(x.reshape(-1, 1), y)
    return float(model.coef_[0]), float(model.score(x.reshape(-1, 1), y))


def make_pepper_trend_report(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    residual_frames = []
    pepper = df[df["product"] == "INTARIAN_PEPPER_ROOT"].copy()
    for day, group in pepper.groupby("source_day", sort=True):
        group = group.sort_values("timestamp").copy()
        slope, r2 = linear_fit(group["mid"].to_numpy(), group["timestamp"].to_numpy())
        intercept = float(group["mid"].mean() - slope * group["timestamp"].mean())
        group["trend_fit"] = intercept + slope * group["timestamp"]
        group["trend_residual"] = group["mid"] - group["trend_fit"]
        group["next_residual"] = group["trend_residual"].shift(-1)
        group["residual_change"] = group["next_residual"] - group["trend_residual"]
        resid = group["trend_residual"].dropna()
        lag1 = resid.autocorr(lag=1)
        rows.append(
            {
                "day": day,
                "slope_per_timestamp": slope,
                "r2": r2,
                "residual_mean": resid.mean(),
                "residual_std": resid.std(ddof=0),
                "residual_abs_p95": resid.abs().quantile(0.95),
                "residual_abs_p99": resid.abs().quantile(0.99),
                "residual_lag1_autocorr": lag1,
                "positive_residual_predicts_next_change_corr": group["trend_residual"].corr(group["next_ret"]),
                "positive_residual_predicts_2step_change_corr": group["trend_residual"].corr(group["lead2_ret"]),
            }
        )
        residual_frames.append(group)
    return pd.DataFrame(rows), pd.concat(residual_frames, ignore_index=True)


def make_osmium_mean_reversion_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    osmium = df[df["product"] == "ASH_COATED_OSMIUM"].copy()
    for day, group in osmium.groupby("source_day", sort=True):
        group = group.sort_values("timestamp").copy()
        group["deviation_10000"] = group["mid"] - 10000.0
        clean = group.dropna(subset=["next_ret", "prev_ret"]).copy()
        X = clean[
            [
                "deviation_10000",
                "imbalance_1",
                "depth_imbalance_3",
                "microprice_gap",
                "wall_gap",
                "spread",
                "prev_ret",
            ]
        ].to_numpy()
        y = clean["next_ret"].to_numpy()
        reg = LinearRegression().fit(X, y)
        rows.append(
            {
                "day": day,
                "mid_mean": group["mid"].mean(),
                "mid_std": group["mid"].std(ddof=0),
                "deviation_mean": group["deviation_10000"].mean(),
                "deviation_lag1_autocorr": group["deviation_10000"].autocorr(lag=1),
                "corr_dev_next_ret": clean["deviation_10000"].corr(clean["next_ret"]),
                "corr_imb1_next_ret": clean["imbalance_1"].corr(clean["next_ret"]),
                "corr_imb3_next_ret": clean["depth_imbalance_3"].corr(clean["next_ret"]),
                "corr_micro_gap_next_ret": clean["microprice_gap"].corr(clean["next_ret"]),
                "corr_wall_gap_next_ret": clean["wall_gap"].corr(clean["next_ret"]),
                "multi_feature_r2": reg.score(X, y),
                "coef_dev": reg.coef_[0],
                "coef_imb1": reg.coef_[1],
                "coef_imb3": reg.coef_[2],
                "coef_micro_gap": reg.coef_[3],
                "coef_wall_gap": reg.coef_[4],
                "coef_spread": reg.coef_[5],
                "coef_prev_ret": reg.coef_[6],
            }
        )
    return pd.DataFrame(rows)


def make_trade_alignment_report(df: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    price_key = df[["product", "source_day", "timestamp", "mid", "bid_price_1", "ask_price_1"]].copy()
    price_key = price_key.rename(columns={"product": "symbol"})
    merged = trades.merge(price_key, on=["symbol", "source_day", "timestamp"], how="left")
    merged["signed_edge_to_mid"] = merged["price"] - merged["mid"]
    merged["distance_to_bid1"] = merged["price"] - merged["bid_price_1"]
    merged["distance_to_ask1"] = merged["ask_price_1"] - merged["price"]
    for (symbol, day), group in merged.groupby(["symbol", "source_day"], sort=True):
        rows.append(
            {
                "symbol": symbol,
                "day": day,
                "trades": len(group),
                "mean_trade_price_minus_mid": group["signed_edge_to_mid"].mean(),
                "p_trade_above_mid": (group["signed_edge_to_mid"] > 0).mean(),
                "p_trade_below_mid": (group["signed_edge_to_mid"] < 0).mean(),
                "mean_distance_to_bid1": group["distance_to_bid1"].mean(),
                "mean_distance_to_ask1": group["distance_to_ask1"].mean(),
            }
        )
    return pd.DataFrame(rows)


def make_residual_bucket_report(residuals: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day, group in residuals.groupby("source_day", sort=True):
        group = group.dropna(subset=["trend_residual", "next_ret"]).copy()
        group["bucket"] = pd.qcut(group["trend_residual"], q=5, duplicates="drop")
        grouped = group.groupby("bucket", observed=True)
        for bucket, sub in grouped:
            rows.append(
                {
                    "day": day,
                    "bucket": str(bucket),
                    "count": len(sub),
                    "residual_mean": sub["trend_residual"].mean(),
                    "next_ret_mean": sub["next_ret"].mean(),
                    "lead2_ret_mean": sub["lead2_ret"].mean(),
                }
            )
    return pd.DataFrame(rows)


def build_summary_payload(
    pepper_trend: pd.DataFrame,
    osmium_reversion: pd.DataFrame,
    trade_alignment: pd.DataFrame,
) -> dict:
    return {
        "pepper_trend": pepper_trend.to_dict(orient="records"),
        "osmium_reversion": osmium_reversion.to_dict(orient="records"),
        "trade_alignment": trade_alignment.to_dict(orient="records"),
    }


def main() -> None:
    prices = load_prices()
    trades = load_trades()
    books = prepare_book_features(prices)

    pepper_trend, residuals = make_pepper_trend_report(books)
    osmium_reversion = make_osmium_mean_reversion_report(books)
    trade_alignment = make_trade_alignment_report(books, trades)
    residual_buckets = make_residual_bucket_report(residuals)

    pepper_trend.to_csv(OUTPUT_DIR / "pepper_trend_report.csv", index=False)
    residuals.to_csv(OUTPUT_DIR / "pepper_trend_residuals.csv", index=False)
    residual_buckets.to_csv(OUTPUT_DIR / "pepper_residual_buckets.csv", index=False)
    osmium_reversion.to_csv(OUTPUT_DIR / "osmium_mean_reversion_report.csv", index=False)
    trade_alignment.to_csv(OUTPUT_DIR / "trade_alignment_report.csv", index=False)

    summary = build_summary_payload(pepper_trend, osmium_reversion, trade_alignment)
    (OUTPUT_DIR / "round2_market_dynamics_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("Wrote:")
    for name in [
        "pepper_trend_report.csv",
        "pepper_trend_residuals.csv",
        "pepper_residual_buckets.csv",
        "osmium_mean_reversion_report.csv",
        "trade_alignment_report.csv",
        "round2_market_dynamics_summary.json",
    ]:
        print(OUTPUT_DIR / name)


if __name__ == "__main__":
    main()
