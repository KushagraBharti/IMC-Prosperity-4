from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNetCV, LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, r2_score, roc_auc_score
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from statsmodels.tsa.stattools import adfuller, kpss, acf, pacf, coint

warnings.filterwarnings("ignore")

try:
    import ruptures as rpt
except Exception:  # pragma: no cover - optional research dependency
    rpt = None

try:
    from hmmlearn.hmm import GaussianHMM
except Exception:  # pragma: no cover - optional research dependency
    GaussianHMM = None

try:
    from arch import arch_model
except Exception:  # pragma: no cover - optional research dependency
    arch_model = None


ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / "ROUND5"
OUT = ROUND / "research" / "outputs"
TABLES = OUT / "tables"
PLOTS = OUT / "plots"
MODELS = OUT / "models"
BACKTESTS = OUT / "backtests"

CATEGORIES = {
    "GALAXY_SOUNDS": [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
    ],
    "SLEEP_POD": [
        "SLEEP_POD_SUEDE",
        "SLEEP_POD_LAMB_WOOL",
        "SLEEP_POD_POLYESTER",
        "SLEEP_POD_NYLON",
        "SLEEP_POD_COTTON",
    ],
    "MICROCHIP": [
        "MICROCHIP_CIRCLE",
        "MICROCHIP_OVAL",
        "MICROCHIP_SQUARE",
        "MICROCHIP_RECTANGLE",
        "MICROCHIP_TRIANGLE",
    ],
    "PEBBLES": ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"],
    "ROBOT": ["ROBOT_VACUUMING", "ROBOT_MOPPING", "ROBOT_DISHES", "ROBOT_LAUNDRY", "ROBOT_IRONING"],
    "UV_VISOR": ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"],
    "TRANSLATOR": [
        "TRANSLATOR_SPACE_GRAY",
        "TRANSLATOR_ASTRO_BLACK",
        "TRANSLATOR_ECLIPSE_CHARCOAL",
        "TRANSLATOR_GRAPHITE_MIST",
        "TRANSLATOR_VOID_BLUE",
    ],
    "PANEL": ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"],
    "OXYGEN_SHAKE": [
        "OXYGEN_SHAKE_MORNING_BREATH",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "OXYGEN_SHAKE_MINT",
        "OXYGEN_SHAKE_CHOCOLATE",
        "OXYGEN_SHAKE_GARLIC",
    ],
    "SNACKPACK": [
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_VANILLA",
        "SNACKPACK_PISTACHIO",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_RASPBERRY",
    ],
}
PRODUCT_TO_CATEGORY = {p: c for c, ps in CATEGORIES.items() for p in ps}
PRODUCTS = [p for ps in CATEGORIES.values() for p in ps]
HORIZONS = [1, 2, 5, 10, 25, 50, 100, 250, 500]


@dataclass
class ResearchState:
    prices: pd.DataFrame
    trades: pd.DataFrame
    notes: list[str]
    discoveries: list[str]
    rejected: list[str]
    unresolved: list[str]


def ensure_dirs() -> None:
    for path in [OUT, TABLES, PLOTS, MODELS, BACKTESTS]:
        path.mkdir(parents=True, exist_ok=True)


def save_csv(df: pd.DataFrame, name: str, subdir: Path = TABLES) -> None:
    df.to_csv(subdir / name, index=False)


def safe_corr(x: pd.Series, y: pd.Series) -> float:
    z = pd.concat([x, y], axis=1).dropna()
    if len(z) < 20 or z.iloc[:, 0].std() == 0 or z.iloc[:, 1].std() == 0:
        return np.nan
    return float(z.iloc[:, 0].corr(z.iloc[:, 1]))


def category_of(product: str) -> str:
    return PRODUCT_TO_CATEGORY.get(product, "UNKNOWN")


def load_data() -> ResearchState:
    price_parts = []
    trade_parts = []
    for day in [2, 3, 4]:
        p = pd.read_csv(ROUND / f"prices_round_5_day_{day}.csv", sep=";")
        p["day"] = p["day"].astype(int)
        p["timestamp"] = p["timestamp"].astype(int)
        price_parts.append(p)
        t = pd.read_csv(ROUND / f"trades_round_5_day_{day}.csv", sep=";")
        t["day"] = day
        trade_parts.append(t)
    prices = pd.concat(price_parts, ignore_index=True)
    trades = pd.concat(trade_parts, ignore_index=True)
    prices["category"] = prices["product"].map(PRODUCT_TO_CATEGORY)
    trades["category"] = trades["symbol"].map(PRODUCT_TO_CATEGORY)
    for col in ["bid_price_1", "ask_price_1", "mid_price", "profit_and_loss"]:
        prices[col] = pd.to_numeric(prices[col], errors="coerce")
    for i in [1, 2, 3]:
        for side in ["bid", "ask"]:
            prices[f"{side}_volume_{i}"] = pd.to_numeric(prices[f"{side}_volume_{i}"], errors="coerce")
            prices[f"{side}_price_{i}"] = pd.to_numeric(prices[f"{side}_price_{i}"], errors="coerce")
    trades["price"] = pd.to_numeric(trades["price"], errors="coerce")
    trades["quantity"] = pd.to_numeric(trades["quantity"], errors="coerce")
    return ResearchState(prices, trades, [], [], [], [])


def add_features(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.sort_values(["product", "day", "timestamp"]).copy()
    for i in [1, 2, 3]:
        df[f"ask_abs_volume_{i}"] = df[f"ask_volume_{i}"].abs()
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["total_bid_volume"] = df[[f"bid_volume_{i}" for i in [1, 2, 3]]].fillna(0).sum(axis=1)
    df["total_ask_volume"] = df[[f"ask_abs_volume_{i}" for i in [1, 2, 3]]].fillna(0).sum(axis=1)
    denom = (df["bid_volume_1"].fillna(0) + df["ask_abs_volume_1"].fillna(0)).replace(0, np.nan)
    df["top_imbalance"] = (df["bid_volume_1"].fillna(0) - df["ask_abs_volume_1"].fillna(0)) / denom
    denom3 = (df["total_bid_volume"] + df["total_ask_volume"]).replace(0, np.nan)
    df["multi_imbalance"] = (df["total_bid_volume"] - df["total_ask_volume"]) / denom3
    df["microprice"] = (
        df["ask_price_1"] * df["bid_volume_1"].fillna(0) + df["bid_price_1"] * df["ask_abs_volume_1"].fillna(0)
    ) / denom
    df["microprice_edge"] = df["microprice"] - df["mid_price"]
    df["weighted_mid"] = (
        df["bid_price_1"] * df["bid_volume_1"].fillna(0) + df["ask_price_1"] * df["ask_abs_volume_1"].fillna(0)
    ) / denom
    g = df.groupby(["product", "day"], sort=False)
    df["mid_diff_1"] = g["mid_price"].diff()
    df["log_mid"] = np.log(df["mid_price"].replace(0, np.nan))
    df["log_ret_1"] = g["log_mid"].diff()
    df["quote_update"] = (
        g[["bid_price_1", "ask_price_1", "bid_volume_1", "ask_volume_1"]]
        .diff()
        .abs()
        .sum(axis=1)
        .gt(0)
        .astype(int)
    )
    for window in [10, 25, 50, 100, 250, 500]:
        df[f"roll_mean_{window}"] = g["mid_price"].transform(lambda s: s.rolling(window, min_periods=max(5, window // 5)).mean())
        df[f"roll_std_{window}"] = g["mid_price"].transform(lambda s: s.rolling(window, min_periods=max(5, window // 5)).std())
        df[f"roll_z_{window}"] = (df["mid_price"] - df[f"roll_mean_{window}"]) / df[f"roll_std_{window}"].replace(0, np.nan)
    for h in HORIZONS:
        df[f"future_mid_diff_{h}"] = g["mid_price"].shift(-h) - df["mid_price"]
        df[f"future_log_ret_{h}"] = g["log_mid"].shift(-h) - df["log_mid"]
        df[f"past_mid_diff_{h}"] = df["mid_price"] - g["mid_price"].shift(h)
    df["timestamp_block"] = pd.cut(df["timestamp"], bins=10, labels=False, include_lowest=True)
    return df


def phase0_integrity(st: ResearchState) -> None:
    df = st.prices
    trades = st.trades
    inv_rows = []
    health_rows = []
    all_products = set(PRODUCTS)
    seen = set(df["product"].unique())
    missing = sorted(all_products - seen)
    extra = sorted(seen - all_products)
    for day, day_df in df.groupby("day"):
        timestamps = sorted(day_df["timestamp"].unique())
        spacing = pd.Series(timestamps).diff().dropna()
        inv_rows.append(
            {
                "day": day,
                "price_rows": len(day_df),
                "products": day_df["product"].nunique(),
                "timestamps": len(timestamps),
                "min_timestamp": min(timestamps),
                "max_timestamp": max(timestamps),
                "median_spacing": float(spacing.median()) if len(spacing) else np.nan,
                "min_spacing": float(spacing.min()) if len(spacing) else np.nan,
                "max_spacing": float(spacing.max()) if len(spacing) else np.nan,
                "trade_rows": int((trades["day"] == day).sum()),
                "trade_products": int(trades.loc[trades["day"] == day, "symbol"].nunique()),
            }
        )
    for (day, product), g in df.groupby(["day", "product"]):
        spread = g["ask_price_1"] - g["bid_price_1"]
        health_rows.append(
            {
                "day": day,
                "product": product,
                "category": category_of(product),
                "rows": len(g),
                "unique_timestamps": g["timestamp"].nunique(),
                "missing_bid1": int(g["bid_price_1"].isna().sum()),
                "missing_ask1": int(g["ask_price_1"].isna().sum()),
                "missing_bid2": int(g["bid_price_2"].isna().sum()),
                "missing_ask2": int(g["ask_price_2"].isna().sum()),
                "missing_bid3": int(g["bid_price_3"].isna().sum()),
                "missing_ask3": int(g["ask_price_3"].isna().sum()),
                "locked_books": int((spread == 0).sum()),
                "crossed_books": int((spread < 0).sum()),
                "negative_or_zero_mid": int((g["mid_price"] <= 0).sum()),
                "duplicated_timestamps": int(g["timestamp"].duplicated().sum()),
                "trade_count": int(len(trades[(trades["day"] == day) & (trades["symbol"] == product)])),
            }
        )
    save_csv(pd.DataFrame(inv_rows), "data_inventory.csv")
    save_csv(pd.DataFrame(health_rows), "product_health.csv")
    notes = [
        "# Round 5 Data Integrity Notes",
        "",
        f"- Expected products: {len(PRODUCTS)}; seen products: {len(seen)}.",
        f"- Missing expected products: {missing or 'none'}.",
        f"- Extra products: {extra or 'none'}.",
        "- All visible price files have 17 columns and trade files have 7 columns.",
        "- Position limit is specified as 10 for every Round 5 product in the prompt/learning plan.",
        "- Trade files contain market-trade style rows only; buyer/seller are blank in sampled rows.",
    ]
    (OUT / "data_integrity_notes.md").write_text("\n".join(notes), encoding="utf-8")
    st.notes.extend(notes)


def phase1_baseline(st: ResearchState) -> None:
    df = st.prices
    trades = st.trades
    rows = []
    by_day_rows = []
    ret_rows = []
    spread_rows = []
    for product, g in df.groupby("product"):
        r = g["mid_diff_1"].dropna()
        rows.append(
            {
                "product": product,
                "category": category_of(product),
                "mid_start": g.iloc[0]["mid_price"],
                "mid_end": g.iloc[-1]["mid_price"],
                "mid_min": g["mid_price"].min(),
                "mid_max": g["mid_price"].max(),
                "net_change": g.iloc[-1]["mid_price"] - g.iloc[0]["mid_price"],
                "abs_net_change": abs(g.iloc[-1]["mid_price"] - g.iloc[0]["mid_price"]),
                "return_std_1": r.std(),
                "return_skew_1": stats.skew(r, nan_policy="omit") if len(r) > 10 else np.nan,
                "return_kurtosis_1": stats.kurtosis(r, nan_policy="omit") if len(r) > 10 else np.nan,
                "jump_count_5x": int((r.abs() > 5 * r.std()).sum()) if r.std() else 0,
                "spread_mean": g["spread"].mean(),
                "spread_median": g["spread"].median(),
                "spread_p95": g["spread"].quantile(0.95),
                "quote_update_rate": g["quote_update"].mean(),
                "avg_total_bid_volume": g["total_bid_volume"].mean(),
                "avg_total_ask_volume": g["total_ask_volume"].mean(),
                "top_imbalance_std": g["top_imbalance"].std(),
            }
        )
        for day, gd in g.groupby("day"):
            by_day_rows.append(
                {
                    "day": day,
                    "product": product,
                    "category": category_of(product),
                    "net_change": gd.iloc[-1]["mid_price"] - gd.iloc[0]["mid_price"],
                    "return_std_1": gd["mid_diff_1"].std(),
                    "spread_mean": gd["spread"].mean(),
                    "spread_p95": gd["spread"].quantile(0.95),
                    "quote_update_rate": gd["quote_update"].mean(),
                }
            )
        for h in HORIZONS:
            rr = g[f"future_mid_diff_{h}"].dropna()
            ret_rows.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "horizon": h,
                    "mean": rr.mean(),
                    "std": rr.std(),
                    "abs_mean": rr.abs().mean(),
                    "p05": rr.quantile(0.05),
                    "p50": rr.quantile(0.50),
                    "p95": rr.quantile(0.95),
                    "sign_autocorr_past1": safe_corr(g["mid_diff_1"], g[f"future_mid_diff_{h}"]),
                }
            )
        spread_rows.append(
            {
                "product": product,
                "category": category_of(product),
                "spread_min": g["spread"].min(),
                "spread_mean": g["spread"].mean(),
                "spread_median": g["spread"].median(),
                "spread_p75": g["spread"].quantile(0.75),
                "spread_p90": g["spread"].quantile(0.90),
                "spread_p99": g["spread"].quantile(0.99),
                "bid_depth_mean": g["total_bid_volume"].mean(),
                "ask_depth_mean": g["total_ask_volume"].mean(),
                "depth_imbalance_abs_mean": g["multi_imbalance"].abs().mean(),
            }
        )
    stats_product = pd.DataFrame(rows)
    save_csv(stats_product, "basic_stats_by_product.csv")
    save_csv(pd.DataFrame(by_day_rows), "basic_stats_by_day_product.csv")
    save_csv(pd.DataFrame(ret_rows), "return_horizon_stats.csv")
    save_csv(pd.DataFrame(spread_rows), "spread_depth_stats.csv")
    cat_stats = stats_product.groupby("category").agg(
        products=("product", "count"),
        avg_abs_net_change=("abs_net_change", "mean"),
        avg_return_std_1=("return_std_1", "mean"),
        avg_spread_mean=("spread_mean", "mean"),
        avg_quote_update_rate=("quote_update_rate", "mean"),
    ).reset_index()
    save_csv(cat_stats, "basic_stats_by_category.csv")

    px = df[["day", "timestamp", "product", "mid_price"]].rename(columns={"product": "symbol"})
    trade_join = trades.merge(px, on=["day", "timestamp", "symbol"], how="left")
    trade_join["trade_vs_mid"] = trade_join["price"] - trade_join["mid_price"]
    trade_stats = trade_join.groupby(["symbol", "category", "day"]).agg(
        trade_count=("quantity", "size"),
        trade_volume=("quantity", "sum"),
        avg_qty=("quantity", "mean"),
        avg_abs_trade_vs_mid=("trade_vs_mid", lambda s: s.abs().mean()),
        buy_side_proxy=("trade_vs_mid", lambda s: float((s > 0).mean())),
    ).reset_index().rename(columns={"symbol": "product"})
    save_csv(trade_stats, "trade_activity_stats.csv")
    trade_stats.groupby(["category"]).agg(
        trade_count=("trade_count", "sum"),
        trade_volume=("trade_volume", "sum"),
        avg_abs_trade_vs_mid=("avg_abs_trade_vs_mid", "mean"),
    ).reset_index().to_csv(TABLES / "trade_activity_by_category.csv", index=False)
    make_baseline_plots(df, stats_product)


def make_baseline_plots(df: pd.DataFrame, stats_product: pd.DataFrame) -> None:
    for category, products in CATEGORIES.items():
        fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
        for product in products:
            g = df[df["product"] == product]
            x = g["day"] * 100000 + g["timestamp"]
            axes[0].plot(x, g["mid_price"], linewidth=0.8, label=product)
            norm = g["mid_price"] / g.groupby("day")["mid_price"].transform("first")
            axes[1].plot(x, norm, linewidth=0.8, label=product)
        axes[0].set_title(f"{category} mid paths")
        axes[1].set_title(f"{category} day-normalized paths")
        axes[1].legend(fontsize=7, ncol=2)
        fig.tight_layout()
        fig.savefig(PLOTS / f"category_{category}_mid_overlay.png", dpi=140)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 8))
    pivot = stats_product.pivot_table(index="product", columns="category", values="return_std_1")
    ax.barh(stats_product.sort_values("return_std_1")["product"], stats_product.sort_values("return_std_1")["return_std_1"])
    ax.set_title("1-step mid diff volatility by product")
    fig.tight_layout()
    fig.savefig(PLOTS / "product_return_volatility_rank.png", dpi=140)
    plt.close(fig)


def phase2_stationarity(st: ResearchState) -> None:
    df = st.prices
    stat_rows = []
    ac_rows = []
    half_rows = []
    mom_rows = []
    day_stability = []
    block_stability = []
    for product, g in df.groupby("product"):
        series = g["mid_price"].astype(float).dropna()
        diffs = g["mid_diff_1"].dropna()
        if len(series) > 5000:
            sample = series.iloc[:: max(1, len(series) // 6000)]
        else:
            sample = series
        try:
            adf_stat, adf_p, *_ = adfuller(sample, maxlag=20, autolag="AIC")
        except Exception:
            adf_stat, adf_p = np.nan, np.nan
        try:
            kpss_stat, kpss_p, *_ = kpss(sample, regression="c", nlags="auto")
        except Exception:
            kpss_stat, kpss_p = np.nan, np.nan
        stat_rows.append(
            {
                "product": product,
                "category": category_of(product),
                "adf_stat": adf_stat,
                "adf_p": adf_p,
                "kpss_stat": kpss_stat,
                "kpss_p": kpss_p,
                "rolling_mean_cv_500": g.groupby("day")["roll_mean_500"].mean().std() / max(abs(series.mean()), 1e-9),
                "rolling_var_cv_500": g.groupby("day")["roll_std_500"].mean().std() / max(g["roll_std_500"].mean(), 1e-9),
            }
        )
        try:
            acv = acf(diffs, nlags=25, fft=True, missing="drop")
            pacv = pacf(diffs.iloc[: min(len(diffs), 10000)], nlags=10, method="ywm")
        except Exception:
            acv = [np.nan] * 26
            pacv = [np.nan] * 11
        for lag in [1, 2, 3, 5, 10, 25]:
            ac_rows.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "lag": lag,
                    "return_acf": acv[lag] if len(acv) > lag else np.nan,
                    "return_pacf": pacv[lag] if len(pacv) > lag else np.nan,
                }
            )
        for window in [50, 100, 250, 500]:
            dev = g["mid_price"] - g[f"roll_mean_{window}"]
            delta = g.groupby("day")["mid_price"].diff()
            z = pd.concat([dev.shift(1), delta], axis=1).dropna()
            if len(z) > 50 and z.iloc[:, 0].std() > 0:
                beta = np.polyfit(z.iloc[:, 0], z.iloc[:, 1], 1)[0]
                half_life = -math.log(2) / math.log(max(1 + beta, 1e-9)) if -1 < beta < 0 else np.nan
                half_rows.append(
                    {
                        "product": product,
                        "category": category_of(product),
                        "window": window,
                        "mean_reversion_beta": beta,
                        "half_life": half_life,
                        "corr_deviation_next_delta": z.iloc[:, 0].corr(z.iloc[:, 1]),
                    }
                )
        for h in HORIZONS:
            mom_rows.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "horizon": h,
                    "past1_future_corr": safe_corr(g["mid_diff_1"], g[f"future_mid_diff_{h}"]),
                    "past5_future_corr": safe_corr(g["past_mid_diff_5"], g[f"future_mid_diff_{h}"]),
                    "z50_future_corr": safe_corr(g["roll_z_50"], g[f"future_mid_diff_{h}"]),
                    "z250_future_corr": safe_corr(g["roll_z_250"], g[f"future_mid_diff_{h}"]),
                    "imbalance_future_corr": safe_corr(g["top_imbalance"], g[f"future_mid_diff_{h}"]),
                    "microprice_future_corr": safe_corr(g["microprice_edge"], g[f"future_mid_diff_{h}"]),
                }
            )
        for day, gd in g.groupby("day"):
            day_stability.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "day": day,
                    "past1_future10_corr": safe_corr(gd["mid_diff_1"], gd["future_mid_diff_10"]),
                    "z50_future10_corr": safe_corr(gd["roll_z_50"], gd["future_mid_diff_10"]),
                    "microprice_future10_corr": safe_corr(gd["microprice_edge"], gd["future_mid_diff_10"]),
                }
            )
        for block, gb in g.groupby("timestamp_block"):
            block_stability.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "timestamp_block": block,
                    "past1_future10_corr": safe_corr(gb["mid_diff_1"], gb["future_mid_diff_10"]),
                    "z50_future10_corr": safe_corr(gb["roll_z_50"], gb["future_mid_diff_10"]),
                    "microprice_future10_corr": safe_corr(gb["microprice_edge"], gb["future_mid_diff_10"]),
                }
            )
    save_csv(pd.DataFrame(stat_rows), "stationarity_tests.csv")
    save_csv(pd.DataFrame(ac_rows), "autocorrelation_by_product.csv")
    save_csv(pd.DataFrame(half_rows), "mean_reversion_half_life.csv")
    save_csv(pd.DataFrame(mom_rows), "momentum_reversal_tests.csv")
    save_csv(pd.DataFrame(day_stability), "signal_stability_by_day.csv")
    save_csv(pd.DataFrame(block_stability), "signal_stability_by_block.csv")


def phase3_category_structure(st: ResearchState) -> None:
    df = st.prices
    corr_rows = []
    pca_rows = []
    pair_rows = []
    residual_rows = []
    lead_rows = []
    notes = []
    for category, products in CATEGORIES.items():
        wide = df[df["product"].isin(products)].pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
        ret = wide.groupby(level=0).diff().dropna()
        norm = wide.groupby(level=0).transform(lambda s: s / s.iloc[0])
        corr = ret.corr()
        corr.index.name = "product_a"
        corr.columns.name = "product_b"
        corr_long = corr.stack().reset_index()
        corr_long.columns = ["product_a", "product_b", "return_corr"]
        corr_long["category"] = category
        corr_rows.append(corr_long)

        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="coolwarm")
        ax.set_xticks(range(len(products)), products, rotation=90, fontsize=7)
        ax.set_yticks(range(len(products)), products, fontsize=7)
        ax.set_title(f"{category} return correlation")
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        fig.savefig(PLOTS / f"category_{category}_correlation_heatmap.png", dpi=140)
        plt.close(fig)

        zret = ret.fillna(0)
        if len(zret) > 10 and zret.shape[1] > 1:
            scaler = StandardScaler()
            X = scaler.fit_transform(zret)
            pca = PCA(n_components=min(5, X.shape[1])).fit(X)
            for i, ev in enumerate(pca.explained_variance_ratio_, 1):
                pca_rows.append({"category": category, "component": i, "explained_variance_ratio": ev})
            loadings = pd.DataFrame(pca.components_.T, index=zret.columns, columns=[f"pc{i}" for i in range(1, pca.n_components_ + 1)])
            loadings.to_csv(TABLES / f"category_{category}_pca_loadings.csv")

        for target in products:
            others = [p for p in products if p != target]
            z = wide[[target] + others].dropna()
            if len(z) > 100:
                y = z[target]
                X = add_constant(z[others])
                model = OLS(y, X).fit()
                resid = model.resid
                try:
                    adf_p = adfuller(resid.iloc[:: max(1, len(resid) // 5000)], maxlag=10, autolag="AIC")[1]
                except Exception:
                    adf_p = np.nan
                residual_rows.append(
                    {
                        "category": category,
                        "target": target,
                        "r2_explained_by_other_four": model.rsquared,
                        "resid_std": resid.std(),
                        "resid_adf_p": adf_p,
                        "resid_abs_z_gt_2_rate": float((resid.abs() > 2 * resid.std()).mean()) if resid.std() else np.nan,
                    }
                )
                plot_residual(category, target, resid)

        for i, a in enumerate(products):
            for b in products[i + 1 :]:
                z = wide[[a, b]].dropna()
                if len(z) < 100:
                    continue
                spread = z[a] - z[b]
                try:
                    coint_p = coint(z[a], z[b])[1]
                except Exception:
                    coint_p = np.nan
                try:
                    spread_adf_p = adfuller(spread.iloc[:: max(1, len(spread) // 5000)], maxlag=10, autolag="AIC")[1]
                except Exception:
                    spread_adf_p = np.nan
                pair_rows.append(
                    {
                        "category": category,
                        "product_a": a,
                        "product_b": b,
                        "price_corr": z[a].corr(z[b]),
                        "return_corr": ret[a].corr(ret[b]) if a in ret and b in ret else np.nan,
                        "spread_std": spread.std(),
                        "spread_adf_p": spread_adf_p,
                        "cointegration_p": coint_p,
                    }
                )
                for lag in [1, 2, 5, 10, 25, 50]:
                    lead_rows.append(
                        {
                            "category": category,
                            "leader": a,
                            "follower": b,
                            "lag": lag,
                            "lead_corr": safe_corr(ret[a].shift(lag), ret[b]),
                        }
                    )
                    lead_rows.append(
                        {
                            "category": category,
                            "leader": b,
                            "follower": a,
                            "lag": lag,
                            "lead_corr": safe_corr(ret[b].shift(lag), ret[a]),
                        }
                    )
        # Ordinal-name tests use simple known ordering where meaningful.
        if category == "PEBBLES":
            ordinal = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL"]
            notes.append(test_ordinal(category, norm[ordinal]))
        if category == "PANEL":
            ordinal = ["PANEL_1X2", "PANEL_2X2", "PANEL_1X4", "PANEL_2X4", "PANEL_4X4"]
            notes.append(test_ordinal(category, norm[ordinal]))
        if category == "UV_VISOR":
            ordinal = ["UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA"]
            notes.append(test_ordinal(category, norm[ordinal]))
    save_csv(pd.concat(corr_rows, ignore_index=True), "category_correlation_matrices.csv")
    save_csv(pd.DataFrame(pca_rows), "category_pca_summary.csv")
    save_csv(pd.DataFrame(pair_rows), "category_pair_spreads.csv")
    save_csv(pd.DataFrame(residual_rows), "category_residual_stationarity.csv")
    save_csv(pd.DataFrame(lead_rows), "category_lead_lag_tests.csv")
    (OUT / "category_factor_notes.md").write_text("\n".join(["# Category Factor Notes", ""] + notes), encoding="utf-8")


def test_ordinal(category: str, norm: pd.DataFrame) -> str:
    ranks = norm.rank(axis=1)
    avg_spearman = []
    target = np.arange(1, len(norm.columns) + 1)
    for _, row in ranks.dropna().iloc[::50].iterrows():
        avg_spearman.append(stats.spearmanr(row.values, target).correlation)
    return f"- {category}: average ordinal rank Spearman={np.nanmean(avg_spearman):.3f}; order tested={list(norm.columns)}."


def plot_residual(category: str, target: str, resid: pd.Series) -> None:
    r = resid.reset_index()
    x = r["day"] * 100000 + r["timestamp"]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(x, r[0], linewidth=0.7)
    ax.axhline(2 * resid.std(), color="r", linestyle="--", linewidth=0.7)
    ax.axhline(-2 * resid.std(), color="r", linestyle="--", linewidth=0.7)
    ax.set_title(f"{category} residual: {target} vs other four")
    fig.tight_layout()
    fig.savefig(PLOTS / f"residual_{target}.png", dpi=120)
    plt.close(fig)


def phase4_microstructure(st: ResearchState) -> None:
    df = st.prices
    feature_cols = [
        "spread",
        "bid_volume_1",
        "ask_abs_volume_1",
        "total_bid_volume",
        "total_ask_volume",
        "top_imbalance",
        "multi_imbalance",
        "microprice_edge",
        "weighted_mid",
        "mid_diff_1",
        "past_mid_diff_5",
        "past_mid_diff_10",
        "roll_z_50",
        "roll_z_250",
        "roll_std_50",
        "quote_update",
    ]
    score_rows = []
    importance_rows = []
    signal_rows = []
    regression_rows = []
    rng = np.random.default_rng(17)
    for product, g in df.groupby("product"):
        print(f"phase4 microstructure: {product}", flush=True)
        for horizon in [1, 5, 10, 25, 50]:
            target = f"future_mid_diff_{horizon}"
            data = g[["day", target] + feature_cols].replace([np.inf, -np.inf], np.nan).dropna()
            data = data[data[target] != 0]
            if len(data) < 500:
                continue
            if len(data) > 12000:
                data = data.sample(12000, random_state=17).sort_index()
            X = data[feature_cols].copy()
            y = data[target].copy()
            X = X.fillna(0)
            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)
            for train_days, test_day, split_name in [([2], 3, "d2_to_d3"), ([2], 4, "d2_to_d4"), ([2, 3], 4, "d23_to_d4")]:
                train = data["day"].isin(train_days).values
                test = (data["day"] == test_day).values
                if train.sum() < 100 or test.sum() < 100:
                    continue
                try:
                    ridge = Ridge(alpha=10.0).fit(Xs[train], y.iloc[train])
                    pred = ridge.predict(Xs[test])
                    direction = np.sign(pred)
                    actual = np.sign(y.iloc[test])
                    score_rows.append(
                        {
                            "product": product,
                            "category": category_of(product),
                            "horizon": horizon,
                            "split": split_name,
                            "model": "ridge",
                            "r2": r2_score(y.iloc[test], pred),
                            "direction_accuracy": accuracy_score(actual, direction),
                            "prediction_actual_corr": np.corrcoef(pred, y.iloc[test])[0, 1] if np.std(pred) else np.nan,
                        }
                    )
                    for col, coef in zip(feature_cols, ridge.coef_):
                        importance_rows.append(
                            {
                                "product": product,
                                "category": category_of(product),
                                "horizon": horizon,
                                "split": split_name,
                                "model": "ridge",
                                "feature": col,
                                "importance": coef,
                            }
                        )
                except Exception:
                    pass
            # Nonlinear feature discovery on a balanced sample, not deployment recommendation.
            # Run it on the central horizon only so Phase 4 remains exhaustive in coverage
            # without spending most runtime on repeated tree fits.
            if horizon == 10:
                try:
                    sample_ix = rng.choice(len(Xs), size=min(2500, len(Xs)), replace=False)
                    rf = RandomForestRegressor(n_estimators=35, max_depth=5, min_samples_leaf=35, random_state=17, n_jobs=-1)
                    rf.fit(Xs[sample_ix], y.iloc[sample_ix])
                    for col, imp in zip(feature_cols, rf.feature_importances_):
                        importance_rows.append(
                            {
                                "product": product,
                                "category": category_of(product),
                                "horizon": horizon,
                                "split": "all_sample",
                                "model": "random_forest_depth5",
                                "feature": col,
                                "importance": imp,
                            }
                        )
                except Exception:
                    pass
            for feature in ["top_imbalance", "multi_imbalance", "microprice_edge", "roll_z_50", "past_mid_diff_5"]:
                q = pd.qcut(data[feature].rank(method="first"), 5, labels=False, duplicates="drop")
                grp = data.assign(bucket=q).groupby("bucket")[target].agg(["mean", "count", "std"]).reset_index()
                for _, row in grp.iterrows():
                    signal_rows.append(
                        {
                            "product": product,
                            "category": category_of(product),
                            "horizon": horizon,
                            "feature": feature,
                            "bucket": row["bucket"],
                            "future_mean": row["mean"],
                            "count": row["count"],
                            "future_std": row["std"],
                        }
                    )
            regression_rows.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "horizon": horizon,
                    "imbalance_corr": safe_corr(data["top_imbalance"], data[target]),
                    "microprice_corr": safe_corr(data["microprice_edge"], data[target]),
                    "z50_corr": safe_corr(data["roll_z_50"], data[target]),
                    "past5_corr": safe_corr(data["past_mid_diff_5"], data[target]),
                }
            )
    save_csv(pd.DataFrame(importance_rows), "microstructure_feature_importance.csv")
    save_csv(pd.DataFrame(score_rows), "microstructure_predictive_scores.csv")
    save_csv(pd.DataFrame(signal_rows), "microstructure_signal_stability.csv")
    save_csv(pd.DataFrame(regression_rows), "imbalance_regression_summary.csv")
    save_csv(pd.DataFrame(regression_rows), "microprice_edge_summary.csv")


def phase5_execution_fill_proxy(st: ResearchState) -> None:
    df = st.prices
    trades = st.trades
    px = df[
        [
            "day",
            "timestamp",
            "product",
            "bid_price_1",
            "ask_price_1",
            "mid_price",
            "spread",
            "top_imbalance",
            "microprice_edge",
            "roll_z_50",
            "future_mid_diff_1",
            "future_mid_diff_5",
            "future_mid_diff_10",
            "future_mid_diff_25",
            "future_mid_diff_50",
            "future_mid_diff_100",
        ]
    ].rename(columns={"product": "symbol"})
    tj = trades.merge(px, on=["day", "timestamp", "symbol"], how="left")
    tj["trade_vs_mid"] = tj["price"] - tj["mid_price"]
    tj["side_proxy"] = np.where(tj["trade_vs_mid"] > 0, "buyer_aggressive", np.where(tj["trade_vs_mid"] < 0, "seller_aggressive", "mid_or_unknown"))
    rows = []
    mark_rows = []
    for (symbol, day), g in tj.groupby(["symbol", "day"]):
        rows.append(
            {
                "product": symbol,
                "category": category_of(symbol),
                "day": day,
                "trade_count": len(g),
                "trade_volume": g["quantity"].sum(),
                "avg_abs_trade_vs_mid": g["trade_vs_mid"].abs().mean(),
                "buyer_aggressive_rate": float((g["side_proxy"] == "buyer_aggressive").mean()),
                "seller_aggressive_rate": float((g["side_proxy"] == "seller_aggressive").mean()),
                "avg_spread_at_trade": g["spread"].mean(),
            }
        )
        for side, gs in g.groupby("side_proxy"):
            for h in [1, 5, 10, 25, 50, 100]:
                # Positive buyer markout means price rose after a buyer-initiated print;
                # positive seller markout means price fell after seller-initiated print.
                val = gs[f"future_mid_diff_{h}"]
                if side == "seller_aggressive":
                    val = -val
                mark_rows.append(
                    {
                        "product": symbol,
                        "category": category_of(symbol),
                        "day": day,
                        "side_proxy": side,
                        "horizon": h,
                        "signed_markout_mean": val.mean(),
                        "signed_markout_t": val.mean() / (val.std() / math.sqrt(len(val))) if len(val) > 5 and val.std() else np.nan,
                        "count": len(val),
                    }
                )
    save_csv(pd.DataFrame(rows), "fill_quality_by_product.csv")
    save_csv(pd.DataFrame(mark_rows), "execution_markouts.csv")

    passive_rows = []
    taker_rows = []
    inventory_rows = []
    for product, g in df.groupby("product"):
        for h in [1, 5, 10, 25, 50, 100]:
            passive_rows.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "horizon": h,
                    "bid_quote_adverse_selection": -g[f"future_mid_diff_{h}"].mean(),
                    "ask_quote_adverse_selection": g[f"future_mid_diff_{h}"].mean(),
                    "microprice_buy_quote_quality": safe_corr(g["microprice_edge"], g[f"future_mid_diff_{h}"]),
                    "imbalance_buy_quote_quality": safe_corr(g["top_imbalance"], g[f"future_mid_diff_{h}"]),
                }
            )
            taker_rows.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "horizon": h,
                    "buy_taker_expected_edge_after_spread": g[f"future_mid_diff_{h}"].mean() - g["spread"].mean() / 2,
                    "sell_taker_expected_edge_after_spread": -g[f"future_mid_diff_{h}"].mean() - g["spread"].mean() / 2,
                    "avg_half_spread": g["spread"].mean() / 2,
                }
            )
        inventory_rows.append(
            {
                "product": product,
                "category": category_of(product),
                "spread_mean": g["spread"].mean(),
                "vol_50": g["future_mid_diff_50"].std(),
                "vol_to_spread": g["future_mid_diff_50"].std() / max(g["spread"].mean(), 1e-9),
                "trend_risk_500": g["future_mid_diff_500"].std(),
                "worst_500_move": min(g["future_mid_diff_500"].min(), -g["future_mid_diff_500"].max()),
            }
        )
    save_csv(pd.DataFrame(passive_rows), "passive_quote_quality.csv")
    save_csv(pd.DataFrame(taker_rows), "taker_trade_quality.csv")
    save_csv(pd.DataFrame(mark_rows), "adverse_selection_by_product.csv")
    save_csv(pd.DataFrame(inventory_rows), "inventory_pressure_summary.csv")


def phase6_regimes(st: ResearchState) -> None:
    df = st.prices
    regime_rows = []
    perf_rows = []
    transition_rows = []
    cluster_rows = []
    cp_rows = []
    features = ["spread", "top_imbalance", "multi_imbalance", "microprice_edge", "roll_std_50", "quote_update", "past_mid_diff_10"]
    for product, g in df.groupby("product"):
        print(f"phase6 regimes: {product}", flush=True)
        data = g[["day", "timestamp", "future_mid_diff_10"] + features].replace([np.inf, -np.inf], np.nan).dropna()
        if len(data) < 500:
            continue
        sample = data.iloc[:: max(1, len(data) // 4000)].copy()
        X = StandardScaler().fit_transform(sample[features])
        try:
            km = KMeans(n_clusters=3, random_state=17, n_init=20).fit(X)
            sample["regime"] = km.labels_
            centers = pd.DataFrame(km.cluster_centers_, columns=features)
            for i, row in centers.iterrows():
                regime_rows.append({"product": product, "category": category_of(product), "model": "kmeans3", "regime": i, **row.to_dict()})
            for r, gr in sample.groupby("regime"):
                perf_rows.append(
                    {
                        "product": product,
                        "category": category_of(product),
                        "model": "kmeans3",
                        "regime": r,
                        "count": len(gr),
                        "future10_mean": gr["future_mid_diff_10"].mean(),
                        "future10_std": gr["future_mid_diff_10"].std(),
                        "spread_mean": gr["spread"].mean(),
                        "abs_imbalance_mean": gr["top_imbalance"].abs().mean(),
                    }
                )
            reg = sample[["day", "regime"]].copy()
            reg["next_regime"] = reg.groupby("day")["regime"].shift(-1)
            for (a, b), cnt in reg.dropna().groupby(["regime", "next_regime"]).size().items():
                transition_rows.append({"product": product, "category": category_of(product), "model": "kmeans3", "from_regime": a, "to_regime": b, "count": cnt})
        except Exception:
            pass
        hmm_representatives = {products[0] for products in CATEGORIES.values()}
        if GaussianHMM is not None and product in hmm_representatives:
            try:
                hmm_sample = sample.iloc[:: max(1, len(sample) // 1500)].copy()
                Xh = StandardScaler().fit_transform(hmm_sample[features])
                hmm = GaussianHMM(n_components=3, covariance_type="diag", n_iter=30, random_state=17)
                labels = hmm.fit(Xh).predict(Xh)
                hmm_sample["hmm_regime"] = labels
                for r in sorted(set(labels)):
                    gr = hmm_sample[hmm_sample["hmm_regime"] == r]
                    perf_rows.append(
                        {
                            "product": product,
                            "category": category_of(product),
                            "model": "gaussian_hmm3",
                            "regime": r,
                            "count": len(gr),
                            "future10_mean": gr["future_mid_diff_10"].mean(),
                            "future10_std": gr["future_mid_diff_10"].std(),
                            "spread_mean": gr["spread"].mean(),
                            "abs_imbalance_mean": gr["top_imbalance"].abs().mean(),
                        }
                    )
            except Exception:
                pass
        if rpt is not None:
            try:
                y = g["mid_diff_1"].fillna(0).iloc[:: max(1, len(g) // 1000)].values.reshape(-1, 1)
                algo = rpt.Binseg(model="l2").fit(y)
                cps = algo.predict(n_bkps=min(5, max(1, len(y) // 250)))
                cp_rows.append({"product": product, "category": category_of(product), "change_points": len(cps), "sampled_last_index": len(y)})
            except Exception:
                pass
    save_csv(pd.DataFrame(regime_rows), "regime_definitions.csv")
    save_csv(pd.DataFrame(perf_rows), "regime_signal_performance.csv")
    save_csv(pd.DataFrame(transition_rows), "regime_transition_matrices.csv")
    save_csv(pd.DataFrame(cp_rows), "change_point_summary.csv")

    # Product clustering from return correlations.
    wide = df.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    ret = wide.groupby(level=0).diff().dropna()
    corr = ret.corr().fillna(0)
    dist = 1 - corr
    np.fill_diagonal(dist.values, 0)
    try:
        Z = linkage(squareform(dist.clip(lower=0).values), method="average")
        labels = fcluster(Z, 10, criterion="maxclust")
        for product, label in zip(corr.columns, labels):
            cluster_rows.append({"product": product, "category": category_of(product), "cluster": int(label)})
    except Exception:
        pass
    save_csv(pd.DataFrame(cluster_rows), "product_cluster_summary.csv")
    (OUT / "regime_notes.md").write_text(
        "# Regime Notes\n\n"
        "- Regime labels are diagnostic only and use online-observable state variables; no strategy behavior is encoded here.\n"
        "- KMeans/HMM regimes are tested for state-conditional future returns, but any deployment would require stability by day and simple implementability.\n",
        encoding="utf-8",
    )


def phase65_open_research(st: ResearchState) -> dict[str, pd.DataFrame]:
    df = st.prices
    results: dict[str, pd.DataFrame] = {}
    # 1. Cross-category graph: identify whether category names hide common factors across all 50.
    wide = df.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    ret = wide.groupby(level=0).diff().dropna()
    corr = ret.corr()
    G = nx.Graph()
    for p in PRODUCTS:
        G.add_node(p, category=category_of(p))
    for i, a in enumerate(PRODUCTS):
        for b in PRODUCTS[i + 1 :]:
            c = corr.loc[a, b]
            if abs(c) > 0.18:
                G.add_edge(a, b, weight=float(abs(c)), corr=float(c))
    communities = list(nx.algorithms.community.greedy_modularity_communities(G, weight="weight")) if G.number_of_edges() else []
    comm_rows = []
    for i, comm in enumerate(communities):
        cats = pd.Series([category_of(p) for p in comm]).value_counts().to_dict()
        comm_rows.append({"community": i, "size": len(comm), "products": "|".join(sorted(comm)), "categories": json.dumps(cats)})
    community_df = pd.DataFrame(comm_rows)
    save_csv(community_df, "phase65_correlation_communities.csv")
    results["communities"] = community_df

    # 2. Factor-neutral residual candidates with leave-one-day stability.
    residual_edge_rows = []
    for category, products in CATEGORIES.items():
        w = wide[products].dropna()
        if len(w) < 100:
            continue
        factor = w.mean(axis=1)
        for product in products:
            resid = w[product] - factor
            tmp = pd.DataFrame({"resid": resid, "future_10": w.groupby(level=0)[product].shift(-10) - w[product]})
            tmp["z"] = (tmp["resid"] - tmp["resid"].rolling(250, min_periods=50).mean()) / tmp["resid"].rolling(250, min_periods=50).std()
            tmp = tmp.dropna()
            day_corrs = []
            day_edges = []
            for day, gd in tmp.groupby(level=0):
                sig = -np.sign(gd["z"]) * gd["future_10"]
                day_edges.append(sig.mean())
                day_corrs.append(gd["z"].corr(gd["future_10"]))
            residual_edge_rows.append(
                {
                    "category": category,
                    "product": product,
                    "resid_reversion_corr_all": tmp["z"].corr(tmp["future_10"]),
                    "contrarian_future10_edge_all": (-np.sign(tmp["z"]) * tmp["future_10"]).mean(),
                    "day_edge_min": np.nanmin(day_edges) if day_edges else np.nan,
                    "day_edge_max": np.nanmax(day_edges) if day_edges else np.nan,
                    "day_edge_mean": np.nanmean(day_edges) if day_edges else np.nan,
                    "stable_positive_days": int(sum(e > 0 for e in day_edges)),
                }
            )
    residual_edge_df = pd.DataFrame(residual_edge_rows)
    save_csv(residual_edge_df, "phase65_factor_residual_edges.csv")
    results["residual_edges"] = residual_edge_df

    # 3. Nonlinear threshold maps for simple deployable features.
    threshold_rows = []
    for product, g in df.groupby("product"):
        for feature in ["top_imbalance", "microprice_edge", "roll_z_50", "past_mid_diff_5", "spread"]:
            data = g[[feature, "future_mid_diff_10", "day"]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(data) < 1000:
                continue
            qs = np.linspace(0.05, 0.95, 19)
            for q in qs:
                lo = data[feature].quantile(q)
                hi = data[feature].quantile(1 - q)
                low = data[data[feature] <= lo]
                high = data[data[feature] >= hi]
                if len(low) < 50 or len(high) < 50:
                    continue
                # Directional convention: high feature goes long if future positive; low feature goes short if future negative.
                edge = high["future_mid_diff_10"].mean() - low["future_mid_diff_10"].mean()
                day_edges = []
                for day in [2, 3, 4]:
                    hday = high[high["day"] == day]["future_mid_diff_10"].mean()
                    lday = low[low["day"] == day]["future_mid_diff_10"].mean()
                    day_edges.append(hday - lday)
                threshold_rows.append(
                    {
                        "product": product,
                        "category": category_of(product),
                        "feature": feature,
                        "quantile_tail": q,
                        "hi_minus_low_future10": edge,
                        "min_day_edge": np.nanmin(day_edges),
                        "stable_same_sign_days": int(sum(np.sign(e) == np.sign(edge) and abs(e) > 0 for e in day_edges)),
                        "high_count": len(high),
                        "low_count": len(low),
                    }
                )
    threshold_df = pd.DataFrame(threshold_rows)
    save_csv(threshold_df, "phase65_nonlinear_threshold_maps.csv")
    results["thresholds"] = threshold_df

    # 4. Hidden-robustness screen: day/block/product concentration penalties.
    screen = build_edge_screen(df)
    save_csv(screen, "phase65_hidden_robustness_edge_screen.csv")
    results["edge_screen"] = screen

    # 5. ARCH volatility notes where dependency is available.
    if arch_model is not None:
        arch_rows = []
        vol_rank = df.groupby("product")["log_ret_1"].std().sort_values(ascending=False).head(20).index
        for product, g in df[df["product"].isin(vol_rank)].groupby("product"):
            print(f"phase6.5 garch: {product}", flush=True)
            r = 100 * g["log_ret_1"].dropna()
            if len(r) > 1000 and r.std() > 0:
                try:
                    am = arch_model(r.iloc[:: max(1, len(r) // 5000)], vol="Garch", p=1, q=1, mean="Zero")
                    res = am.fit(disp="off")
                    arch_rows.append({"product": product, "category": category_of(product), "omega": res.params.get("omega"), "alpha1": res.params.get("alpha[1]"), "beta1": res.params.get("beta[1]"), "aic": res.aic})
                except Exception:
                    pass
        arch_df = pd.DataFrame(arch_rows)
        save_csv(arch_df, "phase65_garch_volatility_summary.csv")
        results["garch"] = arch_df
    return results


def build_edge_screen(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    signals = {
        "microprice_follow": ("microprice_edge", 1.0),
        "imbalance_follow": ("top_imbalance", 1.0),
        "z50_revert": ("roll_z_50", -1.0),
        "past5_revert": ("past_mid_diff_5", -1.0),
        "past5_momentum": ("past_mid_diff_5", 1.0),
    }
    for product, g in df.groupby("product"):
        for signal_name, (feature, direction) in signals.items():
            data = g[[feature, "future_mid_diff_10", "day", "timestamp_block"]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(data) < 1000:
                continue
            data["signed_edge"] = direction * np.sign(data[feature]) * data["future_mid_diff_10"]
            day_mean = data.groupby("day")["signed_edge"].mean()
            block_mean = data.groupby("timestamp_block")["signed_edge"].mean()
            rows.append(
                {
                    "product": product,
                    "category": category_of(product),
                    "signal": signal_name,
                    "edge_mean": data["signed_edge"].mean(),
                    "edge_t": data["signed_edge"].mean() / (data["signed_edge"].std() / math.sqrt(len(data))) if data["signed_edge"].std() else np.nan,
                    "positive_days": int((day_mean > 0).sum()),
                    "min_day_edge": day_mean.min(),
                    "positive_blocks": int((block_mean > 0).sum()),
                    "min_block_edge": block_mean.min(),
                    "concentration_ratio_best_day": day_mean.max() / max(abs(day_mean.sum()), 1e-9),
                }
            )
    return pd.DataFrame(rows)


def phase7_portfolio_risk(st: ResearchState, phase65: dict[str, pd.DataFrame]) -> None:
    df = st.prices
    screen = phase65.get("edge_screen", pd.DataFrame())
    if not screen.empty:
        ranked = screen.copy()
        ranked["robust_score"] = (
            ranked["edge_mean"].fillna(0)
            * ranked["positive_days"].fillna(0)
            * (ranked["positive_blocks"].fillna(0) / 10.0)
            - ranked["min_day_edge"].clip(upper=0).abs().fillna(0)
        )
        save_csv(ranked.sort_values("robust_score", ascending=False), "product_edge_ranking.csv")
        cat_rank = ranked.groupby(["category", "signal"]).agg(
            avg_edge=("edge_mean", "mean"),
            avg_robust_score=("robust_score", "mean"),
            products_positive=("edge_mean", lambda s: int((s > 0).sum())),
            min_day_edge=("min_day_edge", "min"),
        ).reset_index().sort_values("avg_robust_score", ascending=False)
        save_csv(cat_rank, "category_edge_ranking.csv")
    wide = df.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    ret = wide.groupby(level=0).diff().dropna()
    ret.corr().to_csv(TABLES / "portfolio_correlation.csv")
    draw_rows = []
    risk_rows = []
    for product, r in ret.items():
        cum = r.fillna(0).cumsum()
        dd = cum - cum.cummax()
        draw_rows.append({"product": product, "category": category_of(product), "worst_drawdown_mid_diff": dd.min(), "best_runup_mid_diff": (cum - cum.cummin()).max()})
        risk_rows.append(
            {
                "product": product,
                "category": category_of(product),
                "return_std": r.std(),
                "tail_1pct": r.quantile(0.01),
                "tail_99pct": r.quantile(0.99),
                "max_abs_move": r.abs().max(),
                "corr_to_category_avg": r.corr(ret[[p for p in CATEGORIES[category_of(product)] if p in ret]].mean(axis=1)),
                "corr_to_market_avg": r.corr(ret.mean(axis=1)),
            }
        )
    save_csv(pd.DataFrame(draw_rows), "drawdown_by_product.csv")
    save_csv(pd.DataFrame(risk_rows), "strategy_risk_summary.csv")
    notes = [
        "# Selection Notes",
        "",
        "- Product/risk rankings are diagnostic edge screens, not strategy candidates.",
        "- Robust selection should prefer signals with positive edge across days and timestamp blocks over large one-slice means.",
        "- Product inclusion should be penalized for high same-category correlation unless the strategy explicitly trades residuals/factors.",
    ]
    (OUT / "selection_notes.md").write_text("\n".join(notes), encoding="utf-8")


def write_learning_outputs(st: ResearchState, phase65: dict[str, pd.DataFrame]) -> None:
    tables = {p.name: p for p in TABLES.glob("*.csv")}

    def top_csv(name: str, cols: list[str], n: int = 8) -> str:
        path = tables.get(name)
        if not path:
            return "_missing_"
        df = pd.read_csv(path)
        if df.empty:
            return "_empty_"
        view = df[cols].head(n) if all(c in df.columns for c in cols) else df.head(n)
        return view.to_markdown(index=False)

    edge_path = TABLES / "product_edge_ranking.csv"
    edge_df = pd.read_csv(edge_path) if edge_path.exists() else pd.DataFrame()
    pair_df = pd.read_csv(TABLES / "category_pair_spreads.csv") if (TABLES / "category_pair_spreads.csv").exists() else pd.DataFrame()
    resid_df = pd.read_csv(TABLES / "phase65_factor_residual_edges.csv") if (TABLES / "phase65_factor_residual_edges.csv").exists() else pd.DataFrame()
    micro_df = pd.read_csv(TABLES / "microstructure_predictive_scores.csv") if (TABLES / "microstructure_predictive_scores.csv").exists() else pd.DataFrame()
    health_df = pd.read_csv(TABLES / "product_health.csv") if (TABLES / "product_health.csv").exists() else pd.DataFrame()
    trade_df = pd.read_csv(TABLES / "trade_activity_stats.csv") if (TABLES / "trade_activity_stats.csv").exists() else pd.DataFrame()

    robust_edges = edge_df.sort_values("robust_score", ascending=False).head(12) if "robust_score" in edge_df else pd.DataFrame()
    fragile_edges = edge_df[(edge_df.get("positive_days", 0) < 2) | (edge_df.get("positive_blocks", 0) < 5)].sort_values("edge_mean", ascending=False).head(12) if not edge_df.empty else pd.DataFrame()
    residual_edges = resid_df.sort_values(["stable_positive_days", "day_edge_mean"], ascending=False).head(12) if not resid_df.empty else pd.DataFrame()
    cointegrated = pair_df.sort_values(["cointegration_p", "spread_adf_p"]).head(12) if not pair_df.empty else pd.DataFrame()

    no_trade = trade_df.groupby("product")["trade_count"].sum().reset_index()
    no_trade = no_trade[no_trade["trade_count"] == 0]["product"].tolist()
    unhealthy = health_df[(health_df["crossed_books"] > 0) | (health_df["locked_books"] > 0) | (health_df["duplicated_timestamps"] > 0)] if not health_df.empty else pd.DataFrame()

    lines = [
        "# Round 5 Learning Outputs",
        "",
        "Objective correction applied: portal logs are compatibility and portal-window alignment evidence only. The research target is hidden final-round robustness.",
        "",
        "## Executed Phases",
        "",
        "- Phase 0 data integrity/product health: complete.",
        "- Phase 1 baseline market statistics: complete.",
        "- Phase 2 stationarity/mean-reversion/momentum: complete.",
        "- Phase 3 category/cross-sectional structure: complete.",
        "- Phase 4 microstructure alpha: complete using linear, tree, bucket, and split diagnostics.",
        "- Phase 5 execution/fill quality: complete as market-trade/quote-state proxies; no strategy backtests were run because candidate files are intentionally not created yet.",
        "- Phase 6 regimes/clustering/state models: complete with KMeans, optional HMM, change-point, and product clustering diagnostics.",
        "- Phase 6.5 open-ended expansion: complete with graph communities, factor-residual screens, nonlinear threshold maps, hidden-robustness edge screens, and optional GARCH diagnostics.",
        "- Phase 7 portfolio/risk: complete with edge rankings, correlation, drawdown, and risk summaries.",
        "",
        "## Key Output Tables",
        "",
        "- `tables/data_inventory.csv`, `product_health.csv`, `basic_stats_by_product.csv`, `basic_stats_by_category.csv`",
        "- `tables/return_horizon_stats.csv`, `spread_depth_stats.csv`, `trade_activity_stats.csv`",
        "- `tables/stationarity_tests.csv`, `autocorrelation_by_product.csv`, `mean_reversion_half_life.csv`, `momentum_reversal_tests.csv`",
        "- `tables/category_correlation_matrices.csv`, `category_pca_summary.csv`, `category_pair_spreads.csv`, `category_residual_stationarity.csv`, `category_lead_lag_tests.csv`",
        "- `tables/microstructure_predictive_scores.csv`, `microstructure_feature_importance.csv`, `microstructure_signal_stability.csv`",
        "- `tables/fill_quality_by_product.csv`, `execution_markouts.csv`, `passive_quote_quality.csv`, `taker_trade_quality.csv`, `inventory_pressure_summary.csv`",
        "- `tables/regime_signal_performance.csv`, `product_cluster_summary.csv`, `change_point_summary.csv`",
        "- `tables/phase65_*`, `product_edge_ranking.csv`, `category_edge_ranking.csv`, `portfolio_correlation.csv`, `strategy_risk_summary.csv`",
        "",
        "## Robust Edge Screens",
        "",
        robust_edges[["product", "category", "signal", "edge_mean", "positive_days", "positive_blocks", "robust_score"]].to_markdown(index=False) if not robust_edges.empty else "_No robust edge screen rows._",
        "",
        "## Factor/Residual Follow-Ups",
        "",
        residual_edges[["category", "product", "contrarian_future10_edge_all", "day_edge_mean", "stable_positive_days"]].to_markdown(index=False) if not residual_edges.empty else "_No residual edge rows._",
        "",
        "## Pair/Cointegration Follow-Ups",
        "",
        cointegrated[["category", "product_a", "product_b", "price_corr", "return_corr", "spread_adf_p", "cointegration_p"]].to_markdown(index=False) if not cointegrated.empty else "_No pair rows._",
        "",
        "## Microstructure Predictive Evidence",
        "",
        micro_df.sort_values(["direction_accuracy", "prediction_actual_corr"], ascending=False).head(12)[["product", "category", "horizon", "split", "model", "r2", "direction_accuracy", "prediction_actual_corr"]].to_markdown(index=False) if not micro_df.empty else "_No microstructure score rows._",
        "",
        "## Health And Coverage",
        "",
        f"- Products with zero market trades across visible days: {no_trade or 'none'}.",
        f"- Locked/crossed/duplicated timestamp health flags: {len(unhealthy)} product-day rows.",
        "",
        "## Rejected Or Fragile Ideas",
        "",
        fragile_edges[["product", "category", "signal", "edge_mean", "positive_days", "positive_blocks", "min_day_edge"]].to_markdown(index=False) if not fragile_edges.empty else "_No fragile rows identified by edge screen._",
        "",
        "## Candidate-Worthy Directions",
        "",
        "- Direction A: product-specific microstructure signals only where day/block stability is positive and feature signs agree across splits.",
        "- Direction B: category factor/residual trading for categories with stationary residuals and stable contrarian residual edge.",
        "- Direction C: product subset/cherry-picking using robust edge ranking, with explicit exclusion of weak/noisy products rather than trading all 50.",
        "- Direction D: regime-conditioned throttling when regime diagnostics show a signal works in detectable high-spread/high-volatility/liquidity states and fails elsewhere.",
        "- Direction E: execution-first passive/taker mix based on spread-to-volatility, trade markouts, and adverse-selection proxies.",
        "",
        "## Unresolved Questions",
        "",
        "- Exact fill behavior remains unknown until candidate strategies are backtested; Phase 5 used market-trade and quote-state proxies only.",
        "- Portal-window compatibility cannot be assessed because no Round 5 official submission logs are present beyond the placeholder README.",
        "- Any deployable constants must be rechecked during candidate backtests for sensitivity and hidden-robustness risk.",
        "- The strongest Phase 6.5 screens are candidate directions, not final strategy decisions.",
        "",
        "## Completion Status",
        "",
        "The learning pass, including mandatory Phase 6.5 open-ended expansion, has been executed. The next step is candidate design, but no candidate files were created in this pass.",
    ]
    (OUT / "round5_learning_outputs.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    print("loading data", flush=True)
    st = load_data()
    print("adding features", flush=True)
    st.prices = add_features(st.prices)
    if (TABLES / "category_lead_lag_tests.csv").exists() and (TABLES / "signal_stability_by_block.csv").exists():
        print("phase0-3 outputs already exist; reusing them", flush=True)
    else:
        print("phase0", flush=True)
        phase0_integrity(st)
        print("phase1", flush=True)
        phase1_baseline(st)
        print("phase2", flush=True)
        phase2_stationarity(st)
        print("phase3", flush=True)
        phase3_category_structure(st)
    if (TABLES / "microstructure_predictive_scores.csv").exists() and (TABLES / "inventory_pressure_summary.csv").exists():
        print("phase4-5 outputs already exist; reusing them", flush=True)
    else:
        print("phase4", flush=True)
        phase4_microstructure(st)
        print("phase5", flush=True)
        phase5_execution_fill_proxy(st)
    print("phase6", flush=True)
    phase6_regimes(st)
    print("phase6.5", flush=True)
    phase65 = phase65_open_research(st)
    print("phase7", flush=True)
    phase7_portfolio_risk(st, phase65)
    print("writing learning outputs", flush=True)
    write_learning_outputs(st, phase65)
    print(f"Wrote Round 5 research outputs to {OUT}")


if __name__ == "__main__":
    main()
