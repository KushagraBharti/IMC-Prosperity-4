from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "research" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DAYS = [-1, 0, 1]


def load_prices() -> pd.DataFrame:
    frames = []
    for day in DAYS:
        df = pd.read_csv(ROOT / f"prices_round_2_day_{day}.csv", sep=";")
        df["source_day"] = day
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def prepare_features(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.copy()
    price_cols = [
        "bid_price_1",
        "bid_price_2",
        "bid_price_3",
        "ask_price_1",
        "ask_price_2",
        "ask_price_3",
    ]
    vol_cols = [
        "bid_volume_1",
        "bid_volume_2",
        "bid_volume_3",
        "ask_volume_1",
        "ask_volume_2",
        "ask_volume_3",
    ]
    for col in price_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in vol_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df = df[(df["bid_price_1"] > 0) & (df["ask_price_1"] > 0)].copy()
    df["mid"] = (df["bid_price_1"] + df["ask_price_1"]) / 2.0
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["bid_size_1"] = df["bid_volume_1"].abs()
    df["ask_size_1"] = df["ask_volume_1"].abs()
    df["imbalance_1"] = (
        (df["bid_size_1"] - df["ask_size_1"])
        / (df["bid_size_1"] + df["ask_size_1"]).replace(0.0, np.nan)
    ).fillna(0.0)
    df["microprice_1"] = (
        df["ask_price_1"] * df["bid_size_1"] + df["bid_price_1"] * df["ask_size_1"]
    ) / (df["bid_size_1"] + df["ask_size_1"]).replace(0.0, np.nan)
    df["microprice_1"] = df["microprice_1"].fillna(df["mid"])
    df["microprice_gap"] = df["microprice_1"] - df["mid"]

    depth_bid = (
        df["bid_volume_1"].abs() + df["bid_volume_2"].abs() + df["bid_volume_3"].abs()
    )
    depth_ask = (
        df["ask_volume_1"].abs() + df["ask_volume_2"].abs() + df["ask_volume_3"].abs()
    )
    df["depth_imbalance_3"] = (
        (depth_bid - depth_ask) / (depth_bid + depth_ask).replace(0.0, np.nan)
    ).fillna(0.0)

    wall_bid_prices = pd.concat(
        {"p1": df["bid_price_1"], "p2": df["bid_price_2"], "p3": df["bid_price_3"]},
        axis=1,
    )
    wall_bid_sizes = pd.concat(
        {
            "p1": df["bid_volume_1"].abs(),
            "p2": df["bid_volume_2"].abs(),
            "p3": df["bid_volume_3"].abs(),
        },
        axis=1,
    )
    wall_ask_prices = pd.concat(
        {"p1": df["ask_price_1"], "p2": df["ask_price_2"], "p3": df["ask_price_3"]},
        axis=1,
    )
    wall_ask_sizes = pd.concat(
        {
            "p1": df["ask_volume_1"].abs(),
            "p2": df["ask_volume_2"].abs(),
            "p3": df["ask_volume_3"].abs(),
        },
        axis=1,
    )

    wall_bid_idx = wall_bid_sizes.idxmax(axis=1)
    wall_ask_idx = wall_ask_sizes.idxmax(axis=1)
    df["wall_bid"] = [wall_bid_prices.loc[i, j] for i, j in zip(df.index, wall_bid_idx)]
    df["wall_ask"] = [wall_ask_prices.loc[i, j] for i, j in zip(df.index, wall_ask_idx)]
    df["wall_mid"] = (df["wall_bid"] + df["wall_ask"]) / 2.0
    df["wall_gap"] = df["wall_mid"] - df["mid"]

    df = df.sort_values(["product", "source_day", "timestamp"]).reset_index(drop=True)
    df["next_mid"] = df.groupby(["product", "source_day"])["mid"].shift(-1)
    df["next_ret"] = df["next_mid"] - df["mid"]
    df["next_up"] = (df["next_ret"] > 0).astype(float)
    df["prev_mid"] = df.groupby(["product", "source_day"])["mid"].shift(1)
    df["prev_ret"] = df["mid"] - df["prev_mid"]
    return df


def add_pepper_regimes(df: pd.DataFrame) -> pd.DataFrame:
    pepper = df[df["product"] == "INTARIAN_PEPPER_ROOT"].copy()
    for day, group in pepper.groupby("source_day", sort=True):
        mask = pepper["source_day"] == day
        slope = np.polyfit(group["timestamp"].to_numpy(), group["mid"].to_numpy(), deg=1)[0]
        intercept = group["mid"].mean() - slope * group["timestamp"].mean()
        pepper.loc[mask, "trend_fit"] = intercept + slope * pepper.loc[mask, "timestamp"]
    pepper["trend_residual"] = pepper["mid"] - pepper["trend_fit"]
    pepper["regime_state"] = "neutral"
    pepper.loc[pepper["trend_residual"] <= -2.5, "regime_state"] = "oversold"
    pepper.loc[pepper["trend_residual"] >= 2.5, "regime_state"] = "overbought"
    return pepper


def add_osmium_regimes(df: pd.DataFrame) -> pd.DataFrame:
    osmium = df[df["product"] == "ASH_COATED_OSMIUM"].copy()
    osmium["deviation_10000"] = osmium["mid"] - 10000.0
    osmium["regime_state"] = "neutral"
    osmium.loc[
        (osmium["deviation_10000"] <= -3.0) & (osmium["microprice_gap"] >= 0.5),
        "regime_state",
    ] = "rebound_long"
    osmium.loc[
        (osmium["deviation_10000"] >= 3.0) & (osmium["microprice_gap"] <= -0.5),
        "regime_state",
    ] = "rebound_short"
    return osmium


def transition_report(df: pd.DataFrame, product_name: str) -> pd.DataFrame:
    rows = []
    state_order = sorted(df["regime_state"].dropna().unique())
    for day, group in df.groupby("source_day", sort=True):
        current = group["regime_state"]
        nxt = current.shift(-1)
        counts = (
            pd.crosstab(current, nxt, dropna=True)
            .reindex(index=state_order, columns=state_order, fill_value=0)
            .astype(float)
        )
        probs = counts.div(counts.sum(axis=1).replace(0.0, np.nan), axis=0).fillna(0.0)
        for src in state_order:
            for dst in state_order:
                rows.append(
                    {
                        "product": product_name,
                        "day": day,
                        "from_state": src,
                        "to_state": dst,
                        "count": int(counts.loc[src, dst]),
                        "probability": float(probs.loc[src, dst]),
                    }
                )
    return pd.DataFrame(rows)


def leave_one_day_out_logistic(
    df: pd.DataFrame, product_name: str, feature_cols: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    coef_rows = []
    for test_day in DAYS:
        train = df[df["source_day"] != test_day].dropna(subset=feature_cols + ["next_ret"]).copy()
        test = df[df["source_day"] == test_day].dropna(subset=feature_cols + ["next_ret"]).copy()
        train = train[train["next_ret"] != 0].copy()
        test = test[test["next_ret"] != 0].copy()
        if train.empty or test.empty:
            continue

        x_train = train[feature_cols].to_numpy()
        x_test = test[feature_cols].to_numpy()
        y_train = (train["next_ret"] > 0).astype(int).to_numpy()
        y_test = (test["next_ret"] > 0).astype(int).to_numpy()

        scaler = StandardScaler()
        x_train_scaled = scaler.fit_transform(x_train)
        x_test_scaled = scaler.transform(x_test)

        model = LogisticRegression(max_iter=500)
        model.fit(x_train_scaled, y_train)
        prob_up = model.predict_proba(x_test_scaled)[:, 1]
        pred_up = (prob_up >= 0.5).astype(int)

        rows.append(
            {
                "product": product_name,
                "test_day": test_day,
                "samples": int(len(test)),
                "up_rate": float(y_test.mean()),
                "accuracy": float(accuracy_score(y_test, pred_up)),
                "auc": float(roc_auc_score(y_test, prob_up)),
                "mean_predicted_up_prob": float(prob_up.mean()),
            }
        )

        for idx, col in enumerate(feature_cols):
            coef_rows.append(
                {
                    "product": product_name,
                    "test_day": test_day,
                    "feature": col,
                    "coef": float(model.coef_[0][idx]),
                }
            )

    return pd.DataFrame(rows), pd.DataFrame(coef_rows)


def pca_report(df: pd.DataFrame, product_name: str, feature_cols: list[str]) -> pd.DataFrame:
    clean = df.dropna(subset=feature_cols).copy()
    x = clean[feature_cols].to_numpy()
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    cov = np.cov(x_scaled, rowvar=False)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    explained = eigvals / eigvals.sum()
    rows = []
    for pc_idx in range(min(3, len(feature_cols))):
        for feature_idx, feature in enumerate(feature_cols):
            rows.append(
                {
                    "product": product_name,
                    "component": f"PC{pc_idx + 1}",
                    "explained_variance_ratio": float(explained[pc_idx]),
                    "feature": feature,
                    "loading": float(eigvecs[feature_idx, pc_idx]),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    prices = load_prices()
    books = prepare_features(prices)
    pepper = add_pepper_regimes(books)
    osmium = add_osmium_regimes(books)

    pepper_features = ["trend_residual", "spread", "microprice_gap", "imbalance_1", "prev_ret"]
    osmium_features = [
        "deviation_10000",
        "imbalance_1",
        "depth_imbalance_3",
        "microprice_gap",
        "wall_gap",
        "spread",
        "prev_ret",
    ]

    pepper_transitions = transition_report(pepper, "INTARIAN_PEPPER_ROOT")
    osmium_transitions = transition_report(osmium, "ASH_COATED_OSMIUM")
    pepper_logit, pepper_coefs = leave_one_day_out_logistic(
        pepper, "INTARIAN_PEPPER_ROOT", pepper_features
    )
    osmium_logit, osmium_coefs = leave_one_day_out_logistic(
        osmium, "ASH_COATED_OSMIUM", osmium_features
    )
    pepper_pca = pca_report(pepper, "INTARIAN_PEPPER_ROOT", pepper_features)
    osmium_pca = pca_report(osmium, "ASH_COATED_OSMIUM", osmium_features)

    pepper_transitions.to_csv(OUTPUT_DIR / "pepper_markov_transition_report.csv", index=False)
    osmium_transitions.to_csv(OUTPUT_DIR / "osmium_markov_transition_report.csv", index=False)
    pepper_logit.to_csv(OUTPUT_DIR / "pepper_logistic_report.csv", index=False)
    pepper_coefs.to_csv(OUTPUT_DIR / "pepper_logistic_coefficients.csv", index=False)
    osmium_logit.to_csv(OUTPUT_DIR / "osmium_logistic_report.csv", index=False)
    osmium_coefs.to_csv(OUTPUT_DIR / "osmium_logistic_coefficients.csv", index=False)
    pepper_pca.to_csv(OUTPUT_DIR / "pepper_pca_report.csv", index=False)
    osmium_pca.to_csv(OUTPUT_DIR / "osmium_pca_report.csv", index=False)

    summary = {
        "pepper_logistic": pepper_logit.to_dict(orient="records"),
        "osmium_logistic": osmium_logit.to_dict(orient="records"),
    }
    (OUTPUT_DIR / "round2_regime_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("Wrote:")
    for name in [
        "pepper_markov_transition_report.csv",
        "osmium_markov_transition_report.csv",
        "pepper_logistic_report.csv",
        "pepper_logistic_coefficients.csv",
        "osmium_logistic_report.csv",
        "osmium_logistic_coefficients.csv",
        "pepper_pca_report.csv",
        "osmium_pca_report.csv",
        "round2_regime_summary.json",
    ]:
        print(OUTPUT_DIR / name)


if __name__ == "__main__":
    main()
