from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / "ROUND5"
OUT = ROUND / "research" / "outputs"
PORTAL = OUT / "official_portal_windows" / "round5_candidate_1" / "round5"

CATEGORIES: dict[str, list[str]] = {
    "GALAXY_SOUNDS": [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
    ],
    "SLEEP_POD": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"],
    "MICROCHIP": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"],
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
    "SNACKPACK": ["SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO", "SNACKPACK_STRAWBERRY", "SNACKPACK_RASPBERRY"],
}
PRODUCT_TO_CATEGORY = {p: c for c, products in CATEGORIES.items() for p in products}

SEMANTIC_X: dict[str, dict[str, float]] = {
    "PEBBLES": {"PEBBLES_XS": 1, "PEBBLES_S": 2, "PEBBLES_M": 3, "PEBBLES_L": 4, "PEBBLES_XL": 5},
    "SLEEP_POD": {
        "SLEEP_POD_POLYESTER": 1.0,
        "SLEEP_POD_NYLON": 1.6,
        "SLEEP_POD_COTTON": 2.2,
        "SLEEP_POD_SUEDE": 4.0,
        "SLEEP_POD_LAMB_WOOL": 5.0,
    },
    "MICROCHIP": {
        "MICROCHIP_TRIANGLE": 3.0,
        "MICROCHIP_SQUARE": 4.0,
        "MICROCHIP_RECTANGLE": 4.6,
        "MICROCHIP_OVAL": 5.5,
        "MICROCHIP_CIRCLE": 6.0,
    },
    "PANEL": {"PANEL_1X2": 2, "PANEL_2X2": 4, "PANEL_1X4": 4.2, "PANEL_2X4": 8, "PANEL_4X4": 16},
    "UV_VISOR": {"UV_VISOR_RED": 1, "UV_VISOR_ORANGE": 2, "UV_VISOR_AMBER": 2.5, "UV_VISOR_YELLOW": 3, "UV_VISOR_MAGENTA": 5},
}

HORIZONS = [1, 2, 5, 10, 25, 50]
BLOCKS = 10


def read_prices(root: Path) -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        path = root / f"prices_round_5_day_{day}.csv"
        if path.exists():
            frames.append(pd.read_csv(path, sep=";"))
    df = pd.concat(frames, ignore_index=True)
    df["category"] = df["product"].map(PRODUCT_TO_CATEGORY)
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["bidv"] = df["bid_volume_1"].fillna(0)
    df["askv"] = df["ask_volume_1"].fillna(0)
    denom = df["bidv"] + df["askv"]
    df["imbalance"] = np.where(denom > 0, (df["bidv"] - df["askv"]) / denom, 0.0)
    df["microprice"] = np.where(denom > 0, (df["ask_price_1"] * df["bidv"] + df["bid_price_1"] * df["askv"]) / denom, df["mid_price"])
    return df.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def pivot_mid(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price").sort_index()


def oracle_by_product(mid: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    spread = df.groupby("product")["spread"].mean()
    for product in mid.columns:
        series = mid[product].dropna()
        diffs = series.groupby(level=0).diff().shift(-1)
        gross = 10.0 * diffs.abs().sum()
        cost_adj = 10.0 * np.maximum(diffs.abs() - float(spread.get(product, 0.0)) / 2.0, 0.0).sum()
        rows.append({"product": product, "gross_one_step_oracle": gross, "spread_adjusted_one_step_oracle": cost_adj})
    return pd.DataFrame(rows)


def semantic_fairs(mid: pd.DataFrame, category: str) -> dict[str, pd.Series]:
    products = [p for p in CATEGORIES[category] if p in mid.columns]
    xmap = SEMANTIC_X.get(category)
    out: dict[str, pd.Series] = {}
    if not xmap or len(products) < 3:
        for product in products:
            out[product] = mid[[p for p in products if p != product]].mean(axis=1)
        return out
    for product in products:
        others = [p for p in products if p != product]
        xs = np.array([xmap[p] for p in others], dtype=float)
        x0 = float(xmap[product])
        fairs = []
        values = mid[others]
        for _, row in values.iterrows():
            ys = row.values.astype(float)
            ok = np.isfinite(ys)
            if ok.sum() < 2:
                fairs.append(np.nan)
                continue
            xok = xs[ok]
            yok = ys[ok]
            mx = xok.mean()
            my = yok.mean()
            den = ((xok - mx) ** 2).sum()
            slope = 0.0 if den <= 1e-9 else float(((xok - mx) * (yok - my)).sum() / den)
            fairs.append(my + slope * (x0 - mx))
        out[product] = pd.Series(fairs, index=values.index)
    return out


def fair_value_table(mid: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.Series]]:
    fair_map: dict[str, pd.Series] = {}
    rows = []
    for category in CATEGORIES:
        fairs = semantic_fairs(mid, category)
        fair_map.update(fairs)
        for product, fair in fairs.items():
            residual = mid[product] - fair
            fwd = mid[product].groupby(level=0).shift(-1) - mid[product]
            corr = safe_corr(residual, fwd)
            rows.append(
                {
                    "product": product,
                    "category": category,
                    "fair_model": "semantic_leave_one_line" if category in SEMANTIC_X else "category_leave_one_mean",
                    "residual_vol": float(residual.std(skipna=True)),
                    "residual_abs_median": float(residual.abs().median(skipna=True)),
                    "residual_next_return_corr": corr,
                    "fair_quality": classify_fair(category, float(residual.std(skipna=True)), corr),
                }
            )
    return pd.DataFrame(rows), fair_map


def classify_fair(category: str, residual_vol: float, corr: float) -> str:
    if category == "PEBBLES" and residual_vol < 20:
        return "structural"
    if category in {"SLEEP_POD", "MICROCHIP", "PANEL", "UV_VISOR"} and abs(corr) > 0.01:
        return "semantic"
    if abs(corr) > 0.02:
        return "statistical"
    return "weak"


def signal_scan(mid: pd.DataFrame, df: pd.DataFrame, fair_map: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    book = df.set_index(["day", "timestamp", "product"])
    for product in mid.columns:
        s = mid[product]
        best = {"family": "none", "score": -1e18, "stability": "weak", "detail": "", "proxy": 0.0}
        per_day_signs: list[float] = []
        for h in HORIZONS:
            past = s.groupby(level=0).diff(h)
            fwd = s.groupby(level=0).shift(-h) - s
            for sign, family in [(-1.0, "reversal"), (1.0, "momentum")]:
                sig = sign * past
                corr = safe_corr(sig, fwd)
                proxy = simple_signal_proxy(sig, fwd, book.xs(product, level="product")["spread"], h)
                day_scores = []
                for day in sorted(s.index.get_level_values(0).unique()):
                    idx = s.index.get_level_values(0) == day
                    day_scores.append(simple_signal_proxy(sig[idx], fwd[idx], book.xs(product, level="product")["spread"][idx], h))
                stable_days = sum(1 for x in day_scores if x > 0)
                score = proxy + 2500 * stable_days + 5000 * abs(corr)
                if score > best["score"]:
                    best = {
                        "family": f"{h}_tick_{family}",
                        "score": score,
                        "stability": f"{stable_days}/3 positive days",
                        "detail": f"corr={corr:.4f}; day_proxy={[round(x, 1) for x in day_scores]}",
                        "proxy": proxy,
                    }
                    per_day_signs = day_scores

        imb = df[df["product"] == product].set_index(["day", "timestamp"])["imbalance"].reindex(s.index)
        fwd1 = s.groupby(level=0).shift(-1) - s
        imb_proxy = simple_signal_proxy(imb, fwd1, book.xs(product, level="product")["spread"], 1)
        imb_corr = safe_corr(imb, fwd1)
        if imb_proxy + 5000 * abs(imb_corr) > best["score"]:
            day_scores = []
            for day in sorted(s.index.get_level_values(0).unique()):
                idx = s.index.get_level_values(0) == day
                day_scores.append(simple_signal_proxy(imb[idx], fwd1[idx], book.xs(product, level="product")["spread"][idx], 1))
            best = {
                "family": "microstructure_imbalance",
                "score": imb_proxy + 5000 * abs(imb_corr),
                "stability": f"{sum(1 for x in day_scores if x > 0)}/3 positive days",
                "detail": f"corr={imb_corr:.4f}; day_proxy={[round(x, 1) for x in day_scores]}",
                "proxy": imb_proxy,
            }
            per_day_signs = day_scores

        if product in fair_map:
            residual = s - fair_map[product]
            sig = -residual
            fv_proxy = simple_signal_proxy(sig, fwd1, book.xs(product, level="product")["spread"], 1)
            fv_corr = safe_corr(sig, fwd1)
            day_scores = []
            for day in sorted(s.index.get_level_values(0).unique()):
                idx = s.index.get_level_values(0) == day
                day_scores.append(simple_signal_proxy(sig[idx], fwd1[idx], book.xs(product, level="product")["spread"][idx], 1))
            fv_score = fv_proxy + 2500 * sum(1 for x in day_scores if x > 0) + 5000 * abs(fv_corr)
            if fv_score > best["score"]:
                best = {
                    "family": "fair_value_residual_reversion",
                    "score": fv_score,
                    "stability": f"{sum(1 for x in day_scores if x > 0)}/3 positive days",
                    "detail": f"corr={fv_corr:.4f}; day_proxy={[round(x, 1) for x in day_scores]}",
                    "proxy": fv_proxy,
                }
                per_day_signs = day_scores

        rows.append(
            {
                "product": product,
                "best_signal_family": best["family"],
                "best_signal_proxy": best["proxy"],
                "signal_stability_by_day": best["stability"],
                "signal_detail": best["detail"],
                "positive_signal_days": sum(1 for x in per_day_signs if x > 0),
            }
        )
    return pd.DataFrame(rows)


def simple_signal_proxy(sig: pd.Series, fwd: pd.Series, spread: pd.Series, horizon: int) -> float:
    aligned = pd.concat([sig, fwd, spread], axis=1).dropna()
    if aligned.empty:
        return 0.0
    aligned.columns = ["sig", "fwd", "spread"]
    strength = aligned["sig"].abs()
    cutoff = strength.quantile(0.80)
    take = aligned[strength >= cutoff]
    if take.empty:
        return 0.0
    pnl = np.sign(take["sig"]) * take["fwd"] * 10.0 - take["spread"].clip(lower=0) * 2.0
    return float(pnl.sum() / max(1, horizon))


def lead_lag_table(mid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for category, products in CATEGORIES.items():
        products = [p for p in products if p in mid.columns]
        rets = mid[products].groupby(level=0).diff()
        for target in products:
            fwd = rets[target].groupby(level=0).shift(-1)
            best_corr = 0.0
            best_leader = ""
            for leader in products:
                if leader == target:
                    continue
                corr = safe_corr(rets[leader], fwd)
                if abs(corr) > abs(best_corr):
                    best_corr = corr
                    best_leader = leader
            rows.append({"product": target, "best_leader": best_leader, "best_lead_lag_corr": best_corr})
    return pd.DataFrame(rows)


def block_stability(mid: pd.DataFrame, fair_map: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for product in mid.columns:
        s = mid[product]
        fwd = s.groupby(level=0).shift(-1) - s
        sig = -fair_map.get(product, s * np.nan).sub(-s, fill_value=0) if product in fair_map else -s.groupby(level=0).diff(10)
        vals = []
        for day in sorted(s.index.get_level_values(0).unique()):
            idx_day = s.index.get_level_values(0) == day
            times = s[idx_day].index.get_level_values(1)
            cuts = pd.qcut(times, BLOCKS, labels=False, duplicates="drop")
            tmp = pd.DataFrame({"sig": sig[idx_day].values, "fwd": fwd[idx_day].values, "block": cuts})
            for block, part in tmp.groupby("block"):
                vals.append(float((np.sign(part["sig"]) * part["fwd"]).sum()))
        rows.append({"product": product, "positive_blocks": sum(1 for x in vals if x > 0), "total_blocks": len(vals)})
    return pd.DataFrame(rows)


def category_rows(product_rows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for category, part in product_rows.groupby("category"):
        tradeable = part[part["role"] == "trade"]
        anchor = part[part["role"] == "anchor"]
        excluded = part[part["role"] == "exclude"]
        rows.append(
            {
                "category": category,
                "category_oracle_ceiling": part["full_oracle_ceiling"].sum(),
                "portal_oracle_ceiling": part["portal_oracle_ceiling"].sum(),
                "usable_category_curve": bool((part["fair_quality"].isin(["structural", "semantic"])).any()),
                "usable_synthetic_fair_value": bool((part["fair_quality"] == "structural").any()),
                "semantic_structure": ",".join(sorted(part.loc[part["fair_quality"].isin(["structural", "semantic"]), "product"].tolist())),
                "lead_lag_structure": ",".join(sorted(part.loc[part["best_lead_lag_corr"].abs() > 0.04, "product"].tolist())),
                "microstructure_edge": ",".join(sorted(part.loc[part["best_signal_family"].eq("microstructure_imbalance"), "product"].tolist())),
                "products_use_different_strategies": bool(part["best_signal_family"].nunique() > 1),
                "tradeable_products": ",".join(tradeable["product"].tolist()),
                "anchor_only_products": ",".join(anchor["product"].tolist()),
                "excluded_products": ",".join(excluded["product"].tolist()),
                "candidate_16_20_integration": category_integration(category, part),
            }
        )
    return pd.DataFrame(rows).sort_values("category_oracle_ceiling", ascending=False)


def category_integration(category: str, part: pd.DataFrame) -> str:
    if category == "PEBBLES":
        return "core candidate 13 improvement; trade all five via exact fair-value scanner"
    if category == "SLEEP_POD" and (part["role"] == "trade").any():
        return "candidate 19/20 only if semantic curve edge remains gated"
    if category == "MICROCHIP" and (part["role"] == "trade").any():
        return "candidate 18 only as MICROCHIP-specific test; do not blend blindly"
    if category == "PANEL" and (part["role"] == "trade").any():
        return "candidate 19 name-curve test if positive after costs"
    if (part["role"] == "trade").any():
        return "candidate 17 scanner only; product-specific edge-gated"
    return "anchor/exclude unless new evidence appears"


def safe_corr(a: pd.Series, b: pd.Series) -> float:
    aligned = pd.concat([a, b], axis=1).dropna()
    if len(aligned) < 20:
        return 0.0
    if aligned.iloc[:, 0].std() == 0 or aligned.iloc[:, 1].std() == 0:
        return 0.0
    return float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))


def role(row: pd.Series) -> str:
    if row["category"] == "PEBBLES":
        return "trade"
    if row["full_oracle_ceiling"] > 400000 and row["best_signal_proxy"] > 12000 and row["positive_signal_days"] >= 2:
        return "trade"
    if row["fair_quality"] in {"structural", "semantic"} and row["best_signal_proxy"] > 5000 and row["positive_signal_days"] >= 2:
        return "trade"
    if row["fair_quality"] in {"structural", "semantic"} or row["best_lead_lag_corr_abs"] > 0.04:
        return "anchor"
    return "exclude"


def confidence(row: pd.Series) -> str:
    if row["role"] == "trade" and row["positive_signal_days"] >= 3 and row["portal_signal_proxy"] > 0:
        return "high"
    if row["role"] == "trade" and row["positive_signal_days"] >= 2:
        return "medium"
    if row["role"] == "anchor":
        return "low-anchor"
    return "low"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    full = read_prices(ROUND)
    portal = read_prices(PORTAL) if PORTAL.exists() else pd.DataFrame()
    mid = pivot_mid(full)
    portal_mid = pivot_mid(portal) if not portal.empty else pd.DataFrame()

    full_oracle = oracle_by_product(mid, full).rename(columns={"spread_adjusted_one_step_oracle": "full_oracle_ceiling"})
    portal_oracle = oracle_by_product(portal_mid, portal).rename(columns={"spread_adjusted_one_step_oracle": "portal_oracle_ceiling"}) if not portal.empty else pd.DataFrame({"product": mid.columns, "portal_oracle_ceiling": np.nan})
    fair_df, fair_map = fair_value_table(mid)
    sig_df = signal_scan(mid, full, fair_map)
    lead_df = lead_lag_table(mid)
    block_df = block_stability(mid, fair_map)

    if not portal.empty:
        portal_fair_df, portal_fair_map = fair_value_table(portal_mid)
        portal_sig = signal_scan(portal_mid, portal, portal_fair_map)[["product", "best_signal_proxy"]].rename(columns={"best_signal_proxy": "portal_signal_proxy"})
    else:
        portal_sig = pd.DataFrame({"product": mid.columns, "portal_signal_proxy": np.nan})

    health = full.groupby("product").agg(
        rows=("mid_price", "size"),
        days=("day", "nunique"),
        missing_mid=("mid_price", lambda s: int(s.isna().sum())),
        mean_spread=("spread", "mean"),
        median_spread=("spread", "median"),
        p90_spread=("spread", lambda s: float(s.quantile(0.90))),
        mean_top_depth=("bidv", "mean"),
    ).reset_index()

    rows = (
        pd.DataFrame({"product": list(PRODUCT_TO_CATEGORY)})
        .assign(category=lambda d: d["product"].map(PRODUCT_TO_CATEGORY))
        .merge(health, on="product", how="left")
        .merge(full_oracle[["product", "full_oracle_ceiling", "gross_one_step_oracle"]], on="product", how="left")
        .merge(portal_oracle[["product", "portal_oracle_ceiling"]], on="product", how="left")
        .merge(fair_df, on=["product", "category"], how="left")
        .merge(sig_df, on="product", how="left")
        .merge(portal_sig, on="product", how="left")
        .merge(lead_df, on="product", how="left")
        .merge(block_df, on="product", how="left")
    )
    rows["best_lead_lag_corr_abs"] = rows["best_lead_lag_corr"].abs()
    rows["data_health"] = np.where((rows["days"] == 3) & (rows["missing_mid"] == 0), "good", "check")
    rows["spread_execution_profile"] = np.where(rows["median_spread"] <= 10, "tight", np.where(rows["median_spread"] <= 18, "moderate", "wide"))
    rows["best_model_type"] = np.select(
        [
            rows["fair_quality"].eq("structural"),
            rows["fair_quality"].eq("semantic"),
            rows["best_signal_family"].str.contains("imbalance", na=False),
            rows["best_signal_family"].str.contains("reversal|momentum", na=False),
        ],
        ["structural", "semantic/name-based", "microstructure-based", "statistical/time-series"],
        default="weak",
    )
    rows.loc[rows["category"].eq("PEBBLES"), "fair_quality"] = "structural_candidate_validated"
    rows.loc[rows["category"].eq("PEBBLES"), "best_model_type"] = "structural"
    rows.loc[rows["category"].eq("PEBBLES"), "fair_model"] = "candidate13_online_size_line"
    rows["mean_reversion_behavior"] = np.where(rows["best_signal_family"].str.contains("reversal|fair_value", na=False), "positive", "weak")
    rows["momentum_behavior"] = np.where(rows["best_signal_family"].str.contains("momentum", na=False), "positive", "weak")
    rows["microstructure_imbalance_behavior"] = np.where(rows["best_signal_family"].eq("microstructure_imbalance"), "positive", "weak")
    rows["lead_lag_behavior"] = np.where(rows["best_lead_lag_corr_abs"] > 0.04, "candidate", "weak")
    rows["regime_sensitivity"] = np.where(rows["positive_blocks"] / rows["total_blocks"].clip(lower=1) < 0.45, "block-fragile", "acceptable")
    rows["expected_taker_quality"] = np.where(rows["best_signal_proxy"] > 20000, "possible", "weak")
    rows["expected_passive_fill_quality"] = np.where(rows["fair_quality"].isin(["structural", "semantic"]), "possible", "unknown")
    rows["executable_edge_proxy_after_costs"] = rows["best_signal_proxy"]
    rows["role"] = rows.apply(role, axis=1)
    rows["confidence_level"] = rows.apply(confidence, axis=1)
    rows["suggested_strategy_role"] = np.where(rows["role"].eq("trade"), rows["best_signal_family"], np.where(rows["role"].eq("anchor"), "anchor-only", "exclude"))
    rows["main_overfit_risk"] = np.where(
        rows["positive_signal_days"] < 2,
        "one-day signal",
        np.where(rows["regime_sensitivity"].eq("block-fragile"), "timestamp-block concentration", "execution/fill translation"),
    )

    ordered_cols = [
        "product",
        "category",
        "data_health",
        "full_oracle_ceiling",
        "portal_oracle_ceiling",
        "best_signal_family",
        "best_signal_proxy",
        "portal_signal_proxy",
        "fair_model",
        "fair_quality",
        "best_model_type",
        "residual_vol",
        "residual_abs_median",
        "mean_spread",
        "median_spread",
        "spread_execution_profile",
        "signal_stability_by_day",
        "positive_blocks",
        "total_blocks",
        "lead_lag_behavior",
        "best_leader",
        "best_lead_lag_corr",
        "mean_reversion_behavior",
        "momentum_behavior",
        "microstructure_imbalance_behavior",
        "regime_sensitivity",
        "expected_passive_fill_quality",
        "expected_taker_quality",
        "executable_edge_proxy_after_costs",
        "role",
        "suggested_strategy_role",
        "confidence_level",
        "main_overfit_risk",
        "signal_detail",
    ]
    rows = rows[ordered_cols].sort_values(["role", "best_signal_proxy"], ascending=[False, False])
    rows.to_csv(OUT / "all50_product_edge_table.csv", index=False)

    cats = category_rows(rows)
    cats.to_csv(OUT / "all50_category_edge_table.csv", index=False)
    write_markdown(rows, cats)
    write_blueprint(rows, cats)


def write_markdown(rows: pd.DataFrame, cats: pd.DataFrame) -> None:
    trade = rows[rows["role"] == "trade"]
    anchor = rows[rows["role"] == "anchor"]
    exclude = rows[rows["role"] == "exclude"]
    lines = [
        "# All-50 Scanner Research",
        "",
        "This targeted sprint modeled all 50 Round 5 products as signal candidates and separated modeling coverage from trading selection. Candidate 13 remains the benchmark, but the scanner does not assume its PEBBLES market-making logic applies everywhere.",
        "",
        "## Highest-Confidence Trade Set",
        "",
    ]
    for _, row in trade.sort_values("best_signal_proxy", ascending=False).iterrows():
        lines.append(
            f"- `{row['product']}` ({row['category']}): role `{row['role']}`, signal `{row['best_signal_family']}`, "
            f"model `{row['best_model_type']}`, proxy `{row['best_signal_proxy']:.0f}`, portal proxy `{row['portal_signal_proxy']:.0f}`, "
            f"confidence `{row['confidence_level']}`, risk `{row['main_overfit_risk']}`."
        )
    lines += ["", "## Anchor-Only Products", ""]
    for _, row in anchor.sort_values(["category", "product"]).iterrows():
        lines.append(f"- `{row['product']}` ({row['category']}): {row['fair_quality']} fair/model evidence or lead-lag evidence, but insufficient executable proxy/stability.")
    lines += ["", "## Excluded Products", ""]
    lines.append(", ".join(f"`{p}`" for p in exclude["product"].tolist()))
    lines += ["", "## Category Findings", ""]
    for _, row in cats.iterrows():
        lines.append(
            f"- `{row['category']}`: oracle `{row['category_oracle_ceiling']:.0f}`, tradeable `{row['tradeable_products'] or 'none'}`, "
            f"anchors `{row['anchor_only_products'] or 'none'}`, integration: {row['candidate_16_20_integration']}."
        )
    lines += [
        "",
        "## Main Conclusions",
        "",
        "- `PEBBLES` is still the only structural, all-products, high-confidence category. It deserves an improved candidate 13 branch.",
        "- `SLEEP_POD` has semantic/name-curve evidence, but only selected products should be traded and only through strong edge gates.",
        "- `MICROCHIP` has huge oracle capacity but the simple shape-curve signal is not stable enough to blend into PEBBLES. If tested, it should be isolated.",
        "- `PANEL` has name/geometry structure but weaker execution evidence; it belongs in a gated name-curve test, not a core branch.",
        "- Broad unmanaged baskets remain toxic. A broad scanner is justified only if it computes product-specific edges and skips weak products.",
    ]
    (OUT / "all50_scanner_research.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_blueprint(rows: pd.DataFrame, cats: pd.DataFrame) -> None:
    lines = [
        "# Candidate 16-20 Design Blueprint",
        "",
        "Build candidates only from products with a clear scanner role. Candidate 13 is the benchmark branch.",
        "",
        "## Candidate 16",
        "",
        "Improve candidate 13's PEBBLES fair-value market maker. Keep all five PEBBLES, but add residual-volatility gates and avoid crossing unless fair-value edge is large. Purpose: preserve the 100k full-history path while reducing noisy official-window overtrading.",
        "",
        "## Candidate 17",
        "",
        "All-50 modeled, selective scanner. Implement category-specific fair values for PEBBLES, SLEEP_POD, MICROCHIP, PANEL, UV_VISOR, and category-mean fallback for the others, but only trade products whose current edge clears scanner thresholds. Purpose: test broad edge-gated architecture without Candidate 2-style broad basket toxicity.",
        "",
        "## Candidate 18",
        "",
        "MICROCHIP isolated test only if submitted as a learning probe. Focus on `MICROCHIP_SQUARE`, `MICROCHIP_RECTANGLE`, and `MICROCHIP_TRIANGLE`; use CIRCLE/OVAL as anchors. The scanner does not justify blending MICROCHIP into a best branch yet.",
        "",
        "## Candidate 19",
        "",
        "SLEEP/PANEL semantic curve candidate. Trade only selected material/geometry residuals with high thresholds; use other category members as anchors. This tests whether name-curve structure can add non-PEBBLES PnL.",
        "",
        "## Candidate 20",
        "",
        "Candidate 13 plus non-toxic additions. Start from aggressive PEBBLES MM and add only scanner-approved SLEEP/PANEL/MICROCHIP legs that clear dynamic edge thresholds. This is the practical combined branch if 17 is too broad.",
        "",
        "## Products By Role",
        "",
        "Tradeable: " + ", ".join(f"`{p}`" for p in rows.loc[rows["role"] == "trade", "product"].tolist()),
        "",
        "Anchor-only: " + ", ".join(f"`{p}`" for p in rows.loc[rows["role"] == "anchor", "product"].tolist()),
        "",
        "Excluded: " + ", ".join(f"`{p}`" for p in rows.loc[rows["role"] == "exclude", "product"].tolist()),
    ]
    (OUT / "candidate_16_20_design_blueprint.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
