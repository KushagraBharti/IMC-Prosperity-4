from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, r2_score
from sklearn.preprocessing import StandardScaler


PRODUCTS = [
    "HYDROGEL_PACK",
    "VELVETFRUIT_EXTRACT",
    "VEV_5000",
    "VEV_5100",
    "VEV_5200",
    "VEV_5300",
    "VEV_5400",
    "VEV_5500",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def load_prices(paths: list[Path], label: str) -> pd.DataFrame:
    frames = []
    for path in paths:
        df = pd.read_csv(path, sep=";")
        df["source"] = label
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    for col in df.columns:
        if col not in {"product", "source"}:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def add_micro_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bid_vol = df["bid_volume_1"].fillna(0.0)
    ask_vol = df["ask_volume_1"].fillna(0.0)
    denom = bid_vol + ask_vol
    df["imbalance"] = np.where(denom > 0, (bid_vol - ask_vol) / denom, 0.0)
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["microprice"] = np.where(
        denom > 0,
        (df["ask_price_1"] * bid_vol + df["bid_price_1"] * ask_vol) / denom,
        df["mid_price"],
    )
    df["micro_dev"] = df["microprice"] - df["mid_price"]
    df["wall_mid"] = df[["bid_price_1", "bid_price_2", "bid_price_3", "ask_price_1", "ask_price_2", "ask_price_3"]].mean(axis=1)
    df["wall_dev"] = df["wall_mid"] - df["mid_price"]
    return df


def regression_diagnostics(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    rows = []
    horizons = [1, 2, 5, 10, 25, 50, 100]
    features = ["imbalance", "micro_dev", "wall_dev", "spread"]
    for source in sorted(df["source"].unique()):
        source_df = df[df["source"] == source]
        for product in PRODUCTS:
            g = source_df[source_df["product"] == product].sort_values(["day", "timestamp"]).copy()
            if len(g) < 200:
                continue
            for horizon in horizons:
                g[f"ret_{horizon}"] = g.groupby("day")["mid_price"].shift(-horizon) - g["mid_price"]
                sample = g.dropna(subset=features + [f"ret_{horizon}"]).copy()
                if len(sample) < 100:
                    continue
                split_ts = sample["timestamp"].quantile(0.7)
                train = sample[sample["timestamp"] <= split_ts]
                test = sample[sample["timestamp"] > split_ts]
                if len(train) < 50 or len(test) < 50:
                    train = sample.iloc[: int(0.7 * len(sample))]
                    test = sample.iloc[int(0.7 * len(sample)) :]
                x_train = train[features].values
                y_train = train[f"ret_{horizon}"].values
                x_test = test[features].values
                y_test = test[f"ret_{horizon}"].values
                model = LinearRegression().fit(x_train, y_train)
                pred = model.predict(x_test)
                corr = float(np.corrcoef(pred, y_test)[0, 1]) if np.std(pred) > 0 and np.std(y_test) > 0 else 0.0
                rows.append(
                    {
                        "source": source,
                        "product": product,
                        "horizon": horizon,
                        "n_train": len(train),
                        "n_test": len(test),
                        "corr": corr,
                        "r2": r2_score(y_test, pred),
                        "pred_p10": float(np.percentile(pred, 10)),
                        "pred_p90": float(np.percentile(pred, 90)),
                        **{f"coef_{feat}": coef for feat, coef in zip(features, model.coef_)},
                        "intercept": model.intercept_,
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "microstructure_regressions.csv", index=False)
    return out


def regime_summary(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    rows = []
    for source in sorted(df["source"].unique()):
        source_df = df[df["source"] == source].copy()
        source_df["block"] = (source_df["timestamp"] // 10_000).astype(int)
        for product, g in source_df.groupby("product"):
            if product not in PRODUCTS:
                continue
            block = (
                g.groupby("block", as_index=False)
                .agg(
                    mid_start=("mid_price", "first"),
                    mid_end=("mid_price", "last"),
                    mid_mean=("mid_price", "mean"),
                    mid_std=("mid_price", "std"),
                    spread_mean=("spread", "mean"),
                    imbalance_mean=("imbalance", "mean"),
                    micro_dev_mean=("micro_dev", "mean"),
                )
            )
            block["source"] = source
            block["product"] = product
            block["mid_change"] = block["mid_end"] - block["mid_start"]
            rows.append(block)
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(out_dir / "regime_blocks.csv", index=False)
    return out


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_call(s: float, k: float, t: float, sigma: float) -> float:
    if s <= 0 or k <= 0:
        return 0.0
    if t <= 0 or sigma <= 0:
        return max(0.0, s - k)
    vol = sigma * math.sqrt(t)
    if vol <= 0:
        return max(0.0, s - k)
    d1 = (math.log(s / k) + 0.5 * sigma * sigma * t) / vol
    d2 = d1 - vol
    return s * norm_cdf(d1) - k * norm_cdf(d2)


def option_surface(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    sigmas = {
        5000: 0.2419,
        5100: 0.24035,
        5200: 0.24215,
        5300: 0.24455,
        5400: 0.22960,
        5500: 0.24845,
    }
    strikes = {f"VEV_{k}": k for k in sigmas}
    rows = []
    for source in sorted(df["source"].unique()):
        source_df = df[df["source"] == source]
        vfe = source_df[source_df["product"] == "VELVETFRUIT_EXTRACT"][["day", "timestamp", "mid_price"]].rename(columns={"mid_price": "spot"})
        for product, strike in strikes.items():
            opt = source_df[source_df["product"] == product][["day", "timestamp", "mid_price", "bid_price_1", "ask_price_1"]].copy()
            merged = opt.merge(vfe, on=["day", "timestamp"], how="inner")
            if merged.empty:
                continue
            merged["tte_days"] = np.maximum(0.05, 6.0 - merged["timestamp"] / 1_000_000.0)
            if source == "full":
                # In full data this includes day 0/1/2, corresponding to TTE 8/7/6.
                merged["tte_days"] = np.maximum(0.05, 8.0 - merged["day"] - merged["timestamp"] / 1_000_000.0)
            merged["t"] = merged["tte_days"] / 365.0
            merged["bs"] = [bs_call(s, strike, t, sigmas[strike]) for s, t in zip(merged["spot"], merged["t"])]
            merged["resid_mid_minus_bs"] = merged["mid_price"] - merged["bs"]
            merged["buy_edge"] = merged["bs"] - merged["ask_price_1"]
            merged["sell_edge"] = merged["bid_price_1"] - merged["bs"]
            rows.append(
                {
                    "source": source,
                    "product": product,
                    "strike": strike,
                    "mean_resid": merged["resid_mid_minus_bs"].mean(),
                    "sd_resid": merged["resid_mid_minus_bs"].std(),
                    "p10_resid": merged["resid_mid_minus_bs"].quantile(0.1),
                    "p90_resid": merged["resid_mid_minus_bs"].quantile(0.9),
                    "buy_edge_gt_0_5": float((merged["buy_edge"] > 0.5).mean()),
                    "sell_edge_gt_0_5": float((merged["sell_edge"] > 0.5).mean()),
                    "buy_edge_gt_1_0": float((merged["buy_edge"] > 1.0).mean()),
                    "sell_edge_gt_1_0": float((merged["sell_edge"] > 1.0).mean()),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "option_surface_edges.csv", index=False)
    return out


def save_plots(df: pd.DataFrame, regressions: pd.DataFrame, regimes: pd.DataFrame, out_dir: Path) -> None:
    for source in sorted(df["source"].unique()):
        source_df = df[df["source"] == source]
        fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
        for product in ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"]:
            g = source_df[source_df["product"] == product].sort_values("timestamp")
            axes[0].plot(g["timestamp"], g["mid_price"], label=product)
            axes[1].plot(g["timestamp"], g["imbalance"].rolling(10, min_periods=1).mean(), label=product)
        axes[0].set_title(f"Delta-1 Mids: {source}")
        axes[1].set_title(f"Top Imbalance Rolling Mean: {source}")
        axes[1].set_xlabel("timestamp")
        axes[0].legend()
        axes[1].legend()
        plt.tight_layout()
        plt.savefig(out_dir / f"delta1_{source}.png", dpi=160)
        plt.close()

    if not regressions.empty:
        top = regressions[(regressions["product"].isin(["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"])) & (regressions["horizon"].isin([1, 5, 10, 25]))]
        for source in sorted(top["source"].unique()):
            pivot = top[top["source"] == source].pivot_table(index="horizon", columns="product", values="corr")
            ax = pivot.plot(kind="bar", figsize=(10, 5), title=f"Return Prediction Correlation: {source}")
            ax.set_ylabel("corr(pred, actual)")
            plt.tight_layout()
            plt.savefig(out_dir / f"regression_corr_{source}.png", dpi=160)
            plt.close()


def write_summary(out_dir: Path, regressions: pd.DataFrame, regimes: pd.DataFrame, surface: pd.DataFrame) -> None:
    lines = ["# Round 3 Market Diagnostics", ""]
    if not regressions.empty:
        lines += ["## Top Regression Correlations", ""]
        top = regressions.sort_values("corr", ascending=False).head(30)
        lines += [top.to_markdown(index=False), ""]
    if not regimes.empty:
        lines += ["## Portal Delta-1 Regime Blocks", ""]
        portal = regimes[(regimes["source"] == "portal") & (regimes["product"].isin(["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT"]))]
        lines += [portal.to_markdown(index=False), ""]
    if not surface.empty:
        lines += ["## Option Surface Edges", ""]
        lines += [surface.to_markdown(index=False), ""]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = Path(args.project_root)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    full_paths = [root / "ROUND3" / f"prices_round_3_day_{day}.csv" for day in [0, 1, 2]]
    portal_paths = [root / "outputs" / "official-windows" / "round3_day2_0_99900_from_442527" / "prices_round_3_day_2.csv"]

    df = pd.concat([load_prices(full_paths, "full"), load_prices(portal_paths, "portal")], ignore_index=True)
    df = add_micro_features(df)
    df.to_csv(out_dir / "market_features.csv", index=False)
    regressions = regression_diagnostics(df, out_dir)
    regimes = regime_summary(df, out_dir)
    surface = option_surface(df, out_dir)
    save_plots(df, regressions, regimes, out_dir)
    write_summary(out_dir, regressions, regimes, surface)
    print(out_dir)


if __name__ == "__main__":
    main()
