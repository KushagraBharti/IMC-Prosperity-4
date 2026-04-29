from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.stattools import adfuller


ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / "ROUND5"
OUT = ROUND / "research" / "outputs"
TABLES = OUT / "tables"
PLOTS = OUT / "plots"

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


def save(df: pd.DataFrame, name: str) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES / name, index=False)


def load_prices() -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        df = pd.read_csv(ROUND / f"prices_round_5_day_{day}.csv", sep=";")
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["category"] = df["product"].map(PRODUCT_TO_CATEGORY)
    for i in [1, 2, 3]:
        df[f"ask_abs_volume_{i}"] = df[f"ask_volume_{i}"].abs()
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    denom = (df["bid_volume_1"].fillna(0) + df["ask_abs_volume_1"].fillna(0)).replace(0, np.nan)
    df["top_imbalance"] = (df["bid_volume_1"].fillna(0) - df["ask_abs_volume_1"].fillna(0)) / denom
    df["microprice"] = (
        df["ask_price_1"] * df["bid_volume_1"].fillna(0) + df["bid_price_1"] * df["ask_abs_volume_1"].fillna(0)
    ) / denom
    df["microprice_edge"] = df["microprice"] - df["mid_price"]
    df = df.sort_values(["product", "day", "timestamp"]).copy()
    g = df.groupby(["product", "day"], sort=False)
    df["mid_diff_1"] = g["mid_price"].diff()
    for h in [1, 5, 10, 25, 50, 100]:
        df[f"future_mid_diff_{h}"] = g["mid_price"].shift(-h) - df["mid_price"]
        df[f"past_mid_diff_{h}"] = df["mid_price"] - g["mid_price"].shift(h)
    for w in [25, 50, 100, 250, 500]:
        mean = g["mid_price"].transform(lambda s: s.rolling(w, min_periods=max(10, w // 5)).mean())
        std = g["mid_price"].transform(lambda s: s.rolling(w, min_periods=max(10, w // 5)).std())
        df[f"roll_z_{w}"] = (df["mid_price"] - mean) / std.replace(0, np.nan)
    df["timestamp_block"] = pd.cut(df["timestamp"], bins=20, labels=False, include_lowest=True)
    return df


def pebbles_structure(df: pd.DataFrame) -> None:
    products = CATEGORIES["PEBBLES"]
    wide = df[df["product"].isin(products)].pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
    rows = []
    coef_rows = []
    for target in products:
        others = [p for p in products if p != target]
        for test_day in [2, 3, 4]:
            train = wide[wide.index.get_level_values("day") != test_day].dropna()
            test = wide[wide.index.get_level_values("day") == test_day].dropna()
            X_train = train[others]
            y_train = train[target]
            X_test = test[others]
            y_test = test[target]
            model = Ridge(alpha=1e-6).fit(X_train, y_train)
            pred = model.predict(X_test)
            resid = y_test - pred
            rows.append(
                {
                    "target": target,
                    "test_day": test_day,
                    "r2": r2_score(y_test, pred),
                    "resid_mean": resid.mean(),
                    "resid_std": resid.std(),
                    "resid_max_abs": resid.abs().max(),
                    "resid_adf_p": adfuller(resid.iloc[:: max(1, len(resid) // 4000)], maxlag=10, autolag="AIC")[1],
                    "future10_contrarian_edge": (-np.sign(resid) * (y_test.shift(-10) - y_test)).mean(),
                }
            )
            for p, c in zip(others, model.coef_):
                coef_rows.append({"target": target, "test_day": test_day, "feature": p, "coef": c})
            coef_rows.append({"target": target, "test_day": test_day, "feature": "intercept", "coef": model.intercept_})
    save(pd.DataFrame(rows), "extension_pebbles_leave_day_residuals.csv")
    save(pd.DataFrame(coef_rows), "extension_pebbles_leave_day_coefficients.csv")

    pair_rows = []
    for i, a in enumerate(products):
        for b in products[i + 1 :]:
            spread = wide[a] - wide[b]
            day_means = spread.groupby(level=0).mean()
            day_stds = spread.groupby(level=0).std()
            pair_rows.append(
                {
                    "product_a": a,
                    "product_b": b,
                    "spread_mean_all": spread.mean(),
                    "spread_std_all": spread.std(),
                    "day_mean_range": day_means.max() - day_means.min(),
                    "day_std_range": day_stds.max() - day_stds.min(),
                    "adf_p": adfuller(spread.iloc[:: max(1, len(spread) // 4000)], maxlag=10, autolag="AIC")[1],
                }
            )
    save(pd.DataFrame(pair_rows), "extension_pebbles_pair_spread_stability.csv")


def signal_sensitivity(df: pd.DataFrame) -> None:
    rows = []
    features = {
        "z_revert": ("roll_z_{window}", -1.0, [25, 50, 100, 250, 500]),
        "past_revert": ("past_mid_diff_{window}", -1.0, [5, 10, 25, 50, 100]),
        "past_momentum": ("past_mid_diff_{window}", 1.0, [5, 10, 25, 50, 100]),
        "microprice_follow": ("microprice_edge", 1.0, [None]),
        "imbalance_follow": ("top_imbalance", 1.0, [None]),
    }
    for product, g in df.groupby("product"):
        for signal, (template, direction, windows) in features.items():
            for window in windows:
                feature = template.format(window=window) if window is not None else template
                for horizon in [1, 5, 10, 25, 50, 100]:
                    if feature not in g:
                        continue
                    data = g[["day", "timestamp_block", "spread", feature, f"future_mid_diff_{horizon}"]].dropna()
                    if len(data) < 500:
                        continue
                    if signal in ["microprice_follow", "imbalance_follow"]:
                        thresholds = [data[feature].abs().quantile(q) for q in [0.0, 0.25, 0.5, 0.75]]
                    elif "z" in signal:
                        thresholds = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
                    else:
                        thresholds = [data[feature].abs().quantile(q) for q in [0.25, 0.5, 0.75, 0.9]]
                    for threshold in thresholds:
                        active = data[data[feature].abs() >= threshold].copy()
                        if len(active) < 100:
                            continue
                        active["gross_edge"] = direction * np.sign(active[feature]) * active[f"future_mid_diff_{horizon}"]
                        # Cost proxy assumes one spread crossing equivalent for taker and half-spread for passive adverse-selection stress.
                        for cost_mult in [0.0, 0.25, 0.5, 1.0]:
                            net = active["gross_edge"] - cost_mult * active["spread"] / 2.0
                            day_mean = net.groupby(active["day"]).mean()
                            block_mean = net.groupby(active["timestamp_block"]).mean()
                            rows.append(
                                {
                                    "product": product,
                                    "category": PRODUCT_TO_CATEGORY[product],
                                    "signal": signal,
                                    "feature": feature,
                                    "window": window if window is not None else "",
                                    "horizon": horizon,
                                    "threshold": threshold,
                                    "cost_mult": cost_mult,
                                    "active_rate": len(active) / len(data),
                                    "net_edge_mean": net.mean(),
                                    "net_edge_t": net.mean() / (net.std() / math.sqrt(len(net))) if net.std() else np.nan,
                                    "positive_days": int((day_mean > 0).sum()),
                                    "min_day_edge": day_mean.min(),
                                    "positive_blocks": int((block_mean > 0).sum()),
                                    "min_block_edge": block_mean.min(),
                                    "count": len(net),
                                }
                            )
    sens = pd.DataFrame(rows)
    save(sens, "extension_signal_parameter_sensitivity.csv")
    robust = sens[
        (sens["cost_mult"] >= 0.5)
        & (sens["positive_days"] == 3)
        & (sens["positive_blocks"] >= 12)
        & (sens["net_edge_mean"] > 0)
        & (sens["active_rate"].between(0.02, 0.8))
    ].copy()
    robust["robust_score"] = robust["net_edge_mean"] * robust["positive_blocks"] / 20.0 + robust["min_day_edge"].clip(upper=0)
    save(robust.sort_values("robust_score", ascending=False), "extension_cost_stressed_robust_signals.csv")

    top = robust.sort_values("robust_score", ascending=False).head(30)
    if not top.empty:
        fig, ax = plt.subplots(figsize=(12, 8))
        labels = top["product"] + " " + top["signal"] + " h" + top["horizon"].astype(str)
        ax.barh(labels[::-1], top["robust_score"].iloc[::-1])
        ax.set_title("Top cost-stressed robust signal screens")
        fig.tight_layout()
        fig.savefig(PLOTS / "extension_cost_stressed_robust_signals.png", dpi=140)
        plt.close(fig)


def ml_stability(df: pd.DataFrame) -> None:
    feature_cols = [
        "spread",
        "top_imbalance",
        "microprice_edge",
        "mid_diff_1",
        "past_mid_diff_5",
        "past_mid_diff_10",
        "roll_z_25",
        "roll_z_50",
        "roll_z_100",
        "roll_z_250",
    ]
    rows = []
    imp_rows = []
    for product, g in df.groupby("product"):
        data = g[["day", "future_mid_diff_10"] + feature_cols].replace([np.inf, -np.inf], np.nan).dropna()
        if len(data) > 9000:
            data = data.sample(9000, random_state=29).sort_index()
        if len(data) < 1000:
            continue
        for test_day in [2, 3, 4]:
            train = data[data["day"] != test_day]
            test = data[data["day"] == test_day]
            if len(train) < 500 or len(test) < 300:
                continue
            scaler = StandardScaler().fit(train[feature_cols])
            X_train = scaler.transform(train[feature_cols])
            X_test = scaler.transform(test[feature_cols])
            y_train = train["future_mid_diff_10"]
            y_test = test["future_mid_diff_10"]
            ridge = Ridge(alpha=20.0).fit(X_train, y_train)
            pred = ridge.predict(X_test)
            rows.append(
                {
                    "product": product,
                    "category": PRODUCT_TO_CATEGORY[product],
                    "test_day": test_day,
                    "model": "ridge_lodo",
                    "r2": r2_score(y_test, pred),
                    "pred_actual_corr": np.corrcoef(pred, y_test)[0, 1] if pred.std() else np.nan,
                    "direction_accuracy": (np.sign(pred) == np.sign(y_test)).mean(),
                }
            )
            for f, c in zip(feature_cols, ridge.coef_):
                imp_rows.append({"product": product, "category": PRODUCT_TO_CATEGORY[product], "test_day": test_day, "model": "ridge_lodo", "feature": f, "importance": c})
            rf = RandomForestRegressor(n_estimators=50, max_depth=4, min_samples_leaf=50, random_state=29, n_jobs=-1)
            rf.fit(X_train, y_train)
            pred_rf = rf.predict(X_test)
            rows.append(
                {
                    "product": product,
                    "category": PRODUCT_TO_CATEGORY[product],
                    "test_day": test_day,
                    "model": "rf_depth4_lodo",
                    "r2": r2_score(y_test, pred_rf),
                    "pred_actual_corr": np.corrcoef(pred_rf, y_test)[0, 1] if pred_rf.std() else np.nan,
                    "direction_accuracy": (np.sign(pred_rf) == np.sign(y_test)).mean(),
                }
            )
            for f, c in zip(feature_cols, rf.feature_importances_):
                imp_rows.append({"product": product, "category": PRODUCT_TO_CATEGORY[product], "test_day": test_day, "model": "rf_depth4_lodo", "feature": f, "importance": c})
    scores = pd.DataFrame(rows)
    imps = pd.DataFrame(imp_rows)
    save(scores, "extension_leave_one_day_ml_scores.csv")
    save(imps, "extension_leave_one_day_feature_importance.csv")
    if not imps.empty:
        sign_rows = []
        ridge = imps[imps["model"] == "ridge_lodo"].copy()
        for (product, feature), h in ridge.groupby(["product", "feature"]):
            signs = np.sign(h["importance"])
            sign_rows.append(
                {
                    "product": product,
                    "category": PRODUCT_TO_CATEGORY[product],
                    "feature": feature,
                    "mean_coef": h["importance"].mean(),
                    "same_sign_days": int((signs == np.sign(h["importance"].mean())).sum()),
                    "coef_abs_mean": h["importance"].abs().mean(),
                }
            )
        save(pd.DataFrame(sign_rows), "extension_ridge_feature_sign_stability.csv")


def category_exclusion_risk(df: pd.DataFrame) -> None:
    robust = pd.read_csv(TABLES / "extension_cost_stressed_robust_signals.csv")
    rows = []
    if robust.empty:
        save(pd.DataFrame(), "extension_category_exclusion_risk.csv")
        return
    top = robust.sort_values("robust_score", ascending=False).groupby("product").head(1).head(30)
    for category in sorted(CATEGORIES):
        kept = top[top["category"] != category]
        rows.append(
            {
                "excluded_category": category,
                "remaining_products": kept["product"].nunique(),
                "remaining_score_sum": kept["robust_score"].sum(),
                "remaining_edge_mean": kept["net_edge_mean"].mean(),
                "lost_score": top["robust_score"].sum() - kept["robust_score"].sum(),
            }
        )
    save(pd.DataFrame(rows).sort_values("lost_score", ascending=False), "extension_category_exclusion_risk.csv")


def update_learning_outputs() -> None:
    summary_path = OUT / "round5_learning_outputs.md"
    text = summary_path.read_text(encoding="utf-8")
    robust = pd.read_csv(TABLES / "extension_cost_stressed_robust_signals.csv")
    peb = pd.read_csv(TABLES / "extension_pebbles_leave_day_residuals.csv")
    ml = pd.read_csv(TABLES / "extension_leave_one_day_ml_scores.csv")
    weak = pd.read_csv(TABLES / "extension_category_exclusion_risk.csv")
    robust_view = robust.sort_values("robust_score", ascending=False).head(12)
    peb_view = peb.sort_values(["r2", "future10_contrarian_edge"], ascending=False).head(10)
    ml_view = ml.sort_values(["direction_accuracy", "pred_actual_corr"], ascending=False).head(10)

    block = [
        "",
        "## Extension Pass Findings",
        "",
        "Additional research was run because the first pass still had useful unresolved questions around residual stability, cost-stressed signal robustness, and model stability.",
        "",
        "New tables:",
        "",
        "- `extension_pebbles_leave_day_residuals.csv`",
        "- `extension_pebbles_leave_day_coefficients.csv`",
        "- `extension_pebbles_pair_spread_stability.csv`",
        "- `extension_signal_parameter_sensitivity.csv`",
        "- `extension_cost_stressed_robust_signals.csv`",
        "- `extension_leave_one_day_ml_scores.csv`",
        "- `extension_leave_one_day_feature_importance.csv`",
        "- `extension_ridge_feature_sign_stability.csv`",
        "- `extension_category_exclusion_risk.csv`",
        "",
        "Top cost-stressed robust signal screens:",
        "",
        robust_view[["product", "category", "signal", "feature", "horizon", "threshold", "cost_mult", "active_rate", "net_edge_mean", "positive_days", "positive_blocks", "robust_score"]].to_markdown(index=False) if not robust_view.empty else "_No cost-stressed robust rows._",
        "",
        "`PEBBLES` leave-one-day residual validation:",
        "",
        peb_view[["target", "test_day", "r2", "resid_std", "resid_adf_p", "future10_contrarian_edge"]].to_markdown(index=False),
        "",
        "Best leave-one-day ML diagnostics:",
        "",
        ml_view[["product", "category", "test_day", "model", "r2", "pred_actual_corr", "direction_accuracy"]].to_markdown(index=False),
        "",
        "Category exclusion risk from top stressed screens:",
        "",
        weak.head(10).to_markdown(index=False),
        "",
        "Updated interpretation:",
        "",
        "- `PEBBLES` residual structure survives leave-one-day fitting with extremely high R2 and stationary residuals. This is now the best-evidenced category-structure direction.",
        "- Cost-stressed screens still favor selective mean reversion, but the exact signal/window/horizon matters. This argues for candidate diversity and sensitivity-aware thresholds, not one fixed global rule.",
        "- ML remains diagnostic, not a direct deployment plan. Leave-one-day models show pockets of directionality, but not enough broad accuracy to justify a heavy model-family assumption.",
        "- Category exclusion risk confirms concentration: removing `PEBBLES`, `OXYGEN_SHAKE`, or selected `ROBOT`/`SNACKPACK` structures costs most of the robust-screen score; many other categories are optional unless used for diversification.",
        "- Remaining unresolved item is exact simulator fill behavior, which cannot be settled until neutral candidate strategies are written and backtested. The research evidence base is otherwise materially stronger than the initial pass.",
    ]
    marker = "\n## Completion Status\n"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n" + "\n".join(block) + marker + text.split(marker, 1)[1]
    else:
        text += "\n" + "\n".join(block)
    summary_path.write_text(text, encoding="utf-8")


def main() -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    df = load_prices()
    print("extension: pebbles structure", flush=True)
    pebbles_structure(df)
    print("extension: signal sensitivity and cost stress", flush=True)
    signal_sensitivity(df)
    print("extension: leave-one-day ML stability", flush=True)
    ml_stability(df)
    print("extension: category exclusion risk", flush=True)
    category_exclusion_risk(df)
    print("extension: update learning outputs", flush=True)
    update_learning_outputs()
    print("extension complete", flush=True)


if __name__ == "__main__":
    main()
