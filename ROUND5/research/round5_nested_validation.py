from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / "ROUND5"
OUT = ROUND / "research" / "outputs"
TABLES = OUT / "tables"

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


def load_prices() -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        frames.append(pd.read_csv(ROUND / f"prices_round_5_day_{day}.csv", sep=";"))
    df = pd.concat(frames, ignore_index=True)
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
    for h in [10, 25, 50, 100]:
        df[f"future_mid_diff_{h}"] = g["mid_price"].shift(-h) - df["mid_price"]
    for h in [5, 10, 25, 50, 100]:
        df[f"past_mid_diff_{h}"] = df["mid_price"] - g["mid_price"].shift(h)
    for w in [25, 50, 100, 250, 500]:
        mean = g["mid_price"].transform(lambda s: s.rolling(w, min_periods=max(10, w // 5)).mean())
        std = g["mid_price"].transform(lambda s: s.rolling(w, min_periods=max(10, w // 5)).std())
        df[f"roll_z_{w}"] = (df["mid_price"] - mean) / std.replace(0, np.nan)
    df["block20"] = pd.cut(df["timestamp"], bins=20, labels=False, include_lowest=True)
    return df


def evaluate_combo(g: pd.DataFrame, combo: dict, days: list[int]) -> dict:
    data = g[g["day"].isin(days)].copy()
    feature = combo["feature"]
    horizon = int(combo["horizon"])
    direction = float(combo["direction"])
    threshold = float(combo["threshold"])
    cost_mult = float(combo["cost_mult"])
    data = data[["day", "block20", "spread", feature, f"future_mid_diff_{horizon}"]].dropna()
    active = data[data[feature].abs() >= threshold].copy()
    if len(active) < 80:
        return {
            "edge": np.nan,
            "t": np.nan,
            "count": len(active),
            "active_rate": len(active) / max(len(data), 1),
            "positive_days": 0,
            "positive_blocks": 0,
            "min_day_edge": np.nan,
            "min_block_edge": np.nan,
        }
    signed = direction * np.sign(active[feature]) * active[f"future_mid_diff_{horizon}"] - cost_mult * active["spread"] / 2.0
    day_mean = signed.groupby(active["day"]).mean()
    block_mean = signed.groupby(active["block20"]).mean()
    return {
        "edge": signed.mean(),
        "t": signed.mean() / (signed.std() / math.sqrt(len(signed))) if signed.std() else np.nan,
        "count": len(active),
        "active_rate": len(active) / max(len(data), 1),
        "positive_days": int((day_mean > 0).sum()),
        "positive_blocks": int((block_mean > 0).sum()),
        "min_day_edge": day_mean.min(),
        "min_block_edge": block_mean.min(),
    }


def combo_grid(g: pd.DataFrame) -> list[dict]:
    combos = []
    specs = []
    for w in [25, 50, 100, 250, 500]:
        specs.append(("z_revert", f"roll_z_{w}", -1.0, [0.5, 0.75, 1.0, 1.5, 2.0]))
    for h in [5, 10, 25, 50, 100]:
        for signal, direction in [("past_revert", -1.0), ("past_momentum", 1.0)]:
            feature = f"past_mid_diff_{h}"
            qs = [0.5, 0.65, 0.8, 0.9]
            thresholds = [float(g[feature].abs().quantile(q)) for q in qs if feature in g]
            specs.append((signal, feature, direction, thresholds))
    for feature, signal in [("microprice_edge", "microprice_follow"), ("top_imbalance", "imbalance_follow")]:
        thresholds = [float(g[feature].abs().quantile(q)) for q in [0.0, 0.25, 0.5, 0.75]]
        specs.append((signal, feature, 1.0, thresholds))
    for signal, feature, direction, thresholds in specs:
        if feature not in g:
            continue
        for horizon in [10, 25, 50, 100]:
            for threshold in thresholds:
                if not np.isfinite(threshold):
                    continue
                for cost_mult in [0.5, 1.0]:
                    combos.append(
                        {
                            "signal": signal,
                            "feature": feature,
                            "direction": direction,
                            "horizon": horizon,
                            "threshold": threshold,
                            "cost_mult": cost_mult,
                        }
                    )
    return combos


def nested_validate(df: pd.DataFrame) -> None:
    selection_rows = []
    test_rows = []
    all_combo_rows = []
    for product, g in df.groupby("product"):
        print(f"nested validation: {product}", flush=True)
        combos = combo_grid(g)
        for test_day in [2, 3, 4]:
            train_days = [d for d in [2, 3, 4] if d != test_day]
            scored = []
            for combo in combos:
                train = evaluate_combo(g, combo, train_days)
                if train["count"] < 120 or train["active_rate"] < 0.01:
                    continue
                score = train["edge"] * train["positive_blocks"] / 20.0 + min(train["min_day_edge"], 0)
                row = {**combo, **{f"train_{k}": v for k, v in train.items()}, "train_score": score}
                scored.append(row)
            if not scored:
                continue
            scored_df = pd.DataFrame(scored).sort_values("train_score", ascending=False)
            all_combo_rows.append(scored_df.assign(product=product, category=PRODUCT_TO_CATEGORY[product], test_day=test_day).head(25))
            best = scored_df.iloc[0].to_dict()
            test = evaluate_combo(g, best, [test_day])
            selection_rows.append(
                {
                    "product": product,
                    "category": PRODUCT_TO_CATEGORY[product],
                    "test_day": test_day,
                    **{k: best[k] for k in ["signal", "feature", "horizon", "threshold", "cost_mult", "direction"]},
                    "train_edge": best["train_edge"],
                    "train_score": best["train_score"],
                    "train_positive_blocks": best["train_positive_blocks"],
                    "test_edge": test["edge"],
                    "test_t": test["t"],
                    "test_count": test["count"],
                    "test_active_rate": test["active_rate"],
                    "test_positive_blocks": test["positive_blocks"],
                    "test_min_block_edge": test["min_block_edge"],
                }
            )
        product_rows = [r for r in selection_rows if r["product"] == product]
        if product_rows:
            pr = pd.DataFrame(product_rows)
            test_rows.append(
                {
                    "product": product,
                    "category": PRODUCT_TO_CATEGORY[product],
                    "mean_test_edge": pr["test_edge"].mean(),
                    "min_test_edge": pr["test_edge"].min(),
                    "positive_test_days": int((pr["test_edge"] > 0).sum()),
                    "mean_train_edge": pr["train_edge"].mean(),
                    "overfit_ratio": pr["test_edge"].mean() / pr["train_edge"].mean() if pr["train_edge"].mean() else np.nan,
                    "selected_signals": "|".join(pr["signal"].astype(str)),
                }
            )
    pd.DataFrame(selection_rows).to_csv(TABLES / "extension_nested_signal_selection.csv", index=False)
    pd.DataFrame(test_rows).sort_values(["positive_test_days", "mean_test_edge"], ascending=False).to_csv(TABLES / "extension_nested_signal_product_summary.csv", index=False)
    if all_combo_rows:
        pd.concat(all_combo_rows, ignore_index=True).to_csv(TABLES / "extension_nested_top_train_combos.csv", index=False)


def update_notes() -> None:
    summary = pd.read_csv(TABLES / "extension_nested_signal_product_summary.csv")
    selections = pd.read_csv(TABLES / "extension_nested_signal_selection.csv")
    text_path = OUT / "round5_learning_outputs.md"
    text = text_path.read_text(encoding="utf-8")
    top = summary.head(15)
    bad = summary.sort_values(["positive_test_days", "mean_test_edge"]).head(15)
    sel_top = selections.sort_values("test_edge", ascending=False).head(12)
    block = [
        "",
        "## Nested Validation Addendum",
        "",
        "A further nested validation pass was run after the extension exposed a possible parameter-selection artifact. For each product and held-out day, signal/window/horizon/threshold/cost settings were selected only on the other two days, then evaluated on the held-out day.",
        "",
        "New tables:",
        "",
        "- `extension_nested_signal_selection.csv`",
        "- `extension_nested_signal_product_summary.csv`",
        "- `extension_nested_top_train_combos.csv`",
        "",
        "Best product summaries by held-out-day performance:",
        "",
        top.to_markdown(index=False),
        "",
        "Worst product summaries by held-out-day performance:",
        "",
        bad.to_markdown(index=False),
        "",
        "Best individual held-out selections:",
        "",
        sel_top[["product", "category", "test_day", "signal", "feature", "horizon", "threshold", "cost_mult", "train_edge", "test_edge", "test_positive_blocks"]].to_markdown(index=False),
        "",
        "Nested-validation interpretation:",
        "",
        "- The large in-sample/cost-stressed `PEBBLES_XL` rolling-z signal remains useful but is materially less clean under train-days-to-held-out-day selection than the raw grid implied.",
        "- Products with all three held-out days positive deserve more trust than products with a spectacular average driven by one held-out day.",
        "- This reduces confidence in blindly deploying the most extreme long-horizon parameter screen and increases confidence in diversified candidate directions with explicit product selection and conservative thresholds.",
    ]
    marker = "\n## Completion Status\n"
    insert = "\n".join(block)
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n" + insert + marker + text.split(marker, 1)[1]
    else:
        text += "\n" + insert
    text_path.write_text(text, encoding="utf-8")


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    df = load_prices()
    nested_validate(df)
    update_notes()
    print("nested validation complete", flush=True)


if __name__ == "__main__":
    main()
