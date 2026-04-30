from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / "ROUND5"
OUT = ROUND / "research" / "outputs"
PORTAL = OUT / "official_portal_windows" / "round5_candidate_1" / "round5"

CATEGORIES = {
    "GALAXY_SOUNDS": [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
    ],
    "SLEEP_POD": ["SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_POLYESTER", "SLEEP_POD_NYLON", "SLEEP_POD_COTTON"],
    "MICROCHIP": ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE"],
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
PRODUCT_TO_CATEGORY = {p: c for c, ps in CATEGORIES.items() for p in ps}

SEM_X = {
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
    "PANEL": {"PANEL_1X2": 2.0, "PANEL_2X2": 4.0, "PANEL_1X4": 4.2, "PANEL_2X4": 8.0, "PANEL_4X4": 16.0},
    "UV_VISOR": {"UV_VISOR_RED": 1.0, "UV_VISOR_ORANGE": 2.0, "UV_VISOR_AMBER": 2.5, "UV_VISOR_YELLOW": 3.0, "UV_VISOR_MAGENTA": 5.0},
}
HORIZONS = [1, 2, 5, 10, 25, 50, 100]


def read_prices(root: Path) -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        path = root / f"prices_round_5_day_{day}.csv"
        if path.exists():
            frames.append(pd.read_csv(path, sep=";"))
    df = pd.concat(frames, ignore_index=True)
    df["category"] = df["product"].map(PRODUCT_TO_CATEGORY)
    df = df[df["category"].notna() & df["category"].ne("PEBBLES")].copy()
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["bidv"] = df["bid_volume_1"].fillna(0)
    df["askv"] = df["ask_volume_1"].fillna(0)
    den = df["bidv"] + df["askv"]
    df["imbalance"] = np.where(den > 0, (df["bidv"] - df["askv"]) / den, 0.0)
    df["microprice_edge"] = np.where(den > 0, (df["ask_price_1"] * df["bidv"] + df["bid_price_1"] * df["askv"]) / den - df["mid_price"], 0.0)
    return df.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def pivot(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price").sort_index()


def safe_corr(a: pd.Series, b: pd.Series) -> float:
    tmp = pd.concat([a, b], axis=1).dropna()
    if len(tmp) < 50 or tmp.iloc[:, 0].std() == 0 or tmp.iloc[:, 1].std() == 0:
        return 0.0
    return float(tmp.iloc[:, 0].corr(tmp.iloc[:, 1]))


def signal_proxy(sig: pd.Series, fwd: pd.Series, spread: pd.Series, pct: float = 0.80) -> float:
    tmp = pd.concat([sig, fwd, spread], axis=1).dropna()
    if tmp.empty:
        return 0.0
    tmp.columns = ["sig", "fwd", "spread"]
    cutoff = tmp["sig"].abs().quantile(pct)
    take = tmp[tmp["sig"].abs() >= cutoff]
    if take.empty:
        return 0.0
    return float((np.sign(take["sig"]) * take["fwd"] * 10.0 - 0.35 * take["spread"]).sum())


def leave_one_fair(mid: pd.DataFrame, category: str, product: str) -> pd.Series:
    products = [p for p in CATEGORIES[category] if p in mid.columns]
    others = [p for p in products if p != product]
    xmap = SEM_X.get(category)
    if not xmap:
        return mid[others].mean(axis=1)
    xs = np.array([xmap[p] for p in others], dtype=float)
    x0 = xmap[product]
    fairs = []
    for _, row in mid[others].iterrows():
        ys = row.values.astype(float)
        ok = np.isfinite(ys)
        if ok.sum() < 2:
            fairs.append(np.nan)
            continue
        x, y = xs[ok], ys[ok]
        mx, my = x.mean(), y.mean()
        den = ((x - mx) ** 2).sum()
        slope = 0.0 if den <= 1e-9 else ((x - mx) * (y - my)).sum() / den
        fairs.append(my + slope * (x0 - mx))
    return pd.Series(fairs, index=mid.index)


def oracle_rows(full: pd.DataFrame, portal: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, df in [("full", full), ("portal", portal)]:
        mid = pivot(df)
        spread = df.groupby("product")["spread"].mean()
        for product in mid.columns:
            series = mid[product]
            fwd = series.groupby(level=0).shift(-1) - series
            h50 = series.groupby(level=0).shift(-50) - series
            gross = float(10 * fwd.abs().sum())
            spread_adj = float(10 * np.maximum(fwd.abs() - spread[product] / 2.0, 0).sum())
            h50_oracle = float(10 * h50.abs().sum(skipna=True))
            rows.append(
                {
                    "scope": label,
                    "product": product,
                    "category": PRODUCT_TO_CATEGORY[product],
                    "gross_one_step_oracle": gross,
                    "spread_adjusted_one_step_oracle": spread_adj,
                    "h50_oracle": h50_oracle,
                    "mean_spread": float(spread[product]),
                    "median_spread": float(df[df["product"] == product]["spread"].median()),
                    "mean_top_depth": float((df[df["product"] == product]["bidv"] + df[df["product"] == product]["askv"]).mean()),
                    "rows": int((df["product"] == product).sum()),
                }
            )
    wide = pd.DataFrame(rows)
    full_rows = wide[wide["scope"] == "full"].drop(columns=["scope"])
    portal_rows = wide[wide["scope"] == "portal"].drop(columns=["scope"])
    merged = full_rows.merge(portal_rows, on=["product", "category"], suffixes=("_full", "_portal"), how="left")
    merged["realistic_opportunity_score"] = (
        0.55 * merged["spread_adjusted_one_step_oracle_portal"].fillna(0)
        + 0.20 * merged["spread_adjusted_one_step_oracle_full"].fillna(0)
        + 0.15 * merged["h50_oracle_portal"].fillna(0)
        + 0.10 * merged["mean_top_depth_portal"].fillna(0) * 1000
    )
    return merged.sort_values("realistic_opportunity_score", ascending=False)


def edge_rows(full: pd.DataFrame, portal: pd.DataFrame, ranking: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, df in [("full", full), ("portal", portal)]:
        mid = pivot(df)
        spreads = {p: g.set_index(["day", "timestamp"])["spread"].reindex(mid.index) for p, g in df.groupby("product")}
        imbs = {p: g.set_index(["day", "timestamp"])["imbalance"].reindex(mid.index) for p, g in df.groupby("product")}
        micros = {p: g.set_index(["day", "timestamp"])["microprice_edge"].reindex(mid.index) for p, g in df.groupby("product")}
        fair_cache: dict[str, pd.Series] = {}
        for product in mid.columns:
            category = PRODUCT_TO_CATEGORY[product]
            fwd1 = mid[product].groupby(level=0).shift(-1) - mid[product]
            best = ("none", -1e18, 0.0, 0.0, "")
            candidates: list[tuple[str, pd.Series, pd.Series, str]] = []
            for h in HORIZONS:
                past = mid[product].groupby(level=0).diff(h)
                fwd = mid[product].groupby(level=0).shift(-h) - mid[product]
                candidates.append((f"{h}_tick_reversal", -past, fwd, "statistical/time-series"))
                candidates.append((f"{h}_tick_momentum", past, fwd, "statistical/time-series"))
            candidates.append(("imbalance", imbs[product], fwd1, "microstructure"))
            candidates.append(("microprice", micros[product], fwd1, "microstructure"))
            fair = leave_one_fair(mid, category, product)
            fair_cache[product] = fair
            candidates.append(("semantic_or_category_residual", -(mid[product] - fair), fwd1, "semantic/fair-value" if category in SEM_X else "category-mean"))
            for name, sig, fwd, model_type in candidates:
                proxy = signal_proxy(sig, fwd, spreads[product])
                corr = safe_corr(sig, fwd)
                if proxy > best[1]:
                    best = (name, proxy, corr, float(sig.abs().quantile(0.80)), model_type)
            rows.append(
                {
                    "scope": label,
                    "product": product,
                    "category": category,
                    "best_edge_family": best[0],
                    "best_edge_proxy": best[1],
                    "best_edge_corr": best[2],
                    "signal_threshold_proxy": best[3],
                    "model_type": best[4],
                    "residual_vol": float((mid[product] - fair_cache[product]).std(skipna=True)),
                }
            )
    edge = pd.DataFrame(rows)
    full_e = edge[edge["scope"] == "full"].drop(columns=["scope"])
    port_e = edge[edge["scope"] == "portal"].drop(columns=["scope"])
    out = full_e.merge(port_e, on=["product", "category"], suffixes=("_full", "_portal"), how="left")
    out = out.merge(ranking[["product", "realistic_opportunity_score", "spread_adjusted_one_step_oracle_portal", "spread_adjusted_one_step_oracle_full", "mean_spread_portal", "mean_top_depth_portal"]], on="product", how="left")
    out["probe_priority"] = (
        out["best_edge_proxy_portal"].clip(lower=0)
        + 0.08 * out["spread_adjusted_one_step_oracle_portal"].fillna(0)
        + 0.03 * out["spread_adjusted_one_step_oracle_full"].fillna(0)
        - 80 * out["mean_spread_portal"].fillna(0)
    )
    out["recommended_execution"] = np.where(out["best_edge_family_portal"].str.contains("reversal|momentum|residual", na=False), "passive-first", "taker-only-if-edge-large")
    out["probe_verdict"] = np.select(
        [
            (out["probe_priority"] > out["probe_priority"].quantile(0.85)) & (out["best_edge_proxy_portal"] > 0),
            (out["spread_adjusted_one_step_oracle_portal"] > out["spread_adjusted_one_step_oracle_portal"].quantile(0.80)) & (out["best_edge_proxy_portal"] > 0),
        ],
        ["standalone_probe", "research_probe"],
        default="defer",
    )
    return out.sort_values("probe_priority", ascending=False)


def write_reports(ranking: pd.DataFrame, edges: pd.DataFrame) -> None:
    ranking.to_csv(OUT / "non_pebbles_oracle_ranking.csv", index=False)
    edges.to_csv(OUT / "non_pebbles_edge_table.csv", index=False)
    top = ranking.head(15)
    edge_top = edges.head(15)
    cat = ranking.groupby("category").agg(
        portal_oracle=("spread_adjusted_one_step_oracle_portal", "sum"),
        full_oracle=("spread_adjusted_one_step_oracle_full", "sum"),
        score=("realistic_opportunity_score", "sum"),
        mean_spread=("mean_spread_portal", "mean"),
        depth=("mean_top_depth_portal", "mean"),
    ).sort_values("score", ascending=False)
    lines = ["# Non-PEBBLES Oracle Study", "", "PEBBLES excluded from all calculations in this sprint.", "", "## Category Ranking", ""]
    for category, row in cat.iterrows():
        lines.append(f"- `{category}`: portal executable oracle `{row.portal_oracle:.0f}`, full executable oracle `{row.full_oracle:.0f}`, opportunity score `{row.score:.0f}`, avg portal spread `{row.mean_spread:.1f}`, avg top depth `{row.depth:.1f}.")
    lines += ["", "## Top Product Opportunities", ""]
    for _, row in top.iterrows():
        lines.append(f"- `{row['product']}` ({row['category']}): portal oracle `{row.spread_adjusted_one_step_oracle_portal:.0f}`, full oracle `{row.spread_adjusted_one_step_oracle_full:.0f}`, h50 portal `{row.h50_oracle_portal:.0f}`, spread `{row.mean_spread_portal:.1f}`, score `{row.realistic_opportunity_score:.0f}`.")
    (OUT / "non_pebbles_oracle_study.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = ["# Non-PEBBLES Edge Discovery", "", "Top online edge candidates after portal-window signal proxies:", ""]
    for _, row in edge_top.iterrows():
        lines.append(
            f"- `{row['product']}` ({row['category']}): portal edge `{row.best_edge_family_portal}` proxy `{row.best_edge_proxy_portal:.0f}`, "
            f"full edge `{row.best_edge_family_full}` proxy `{row.best_edge_proxy_full:.0f}`, model `{row.model_type_portal}`, "
            f"verdict `{row.probe_verdict}`."
        )
    lines += [
        "",
        "## Rejections",
        "",
        "- High oracle alone is insufficient: many products have large hindsight capacity but only weak online capture.",
        "- MICROCHIP remains high-ceiling but the best online proxy is small relative to its oracle, so it should stay isolated.",
        "- ROBOT_DISHES remains special: oracle and ret-reversal signal are large, but previous visible-depth/passive probes did not translate. It needs a standalone execution probe, not integration.",
    ]
    (OUT / "non_pebbles_edge_discovery.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    probe = edges[edges["probe_verdict"].isin(["standalone_probe", "research_probe"])].head(10)
    lines = ["# Non-PEBBLES Probe Blueprint", "", "Probe only these non-PEBBLES ideas before any integration with candidate 16.", ""]
    score_path = OUT / "non_pebbles_probe_portal_scores.csv"
    if score_path.exists():
        scores = pd.read_csv(score_path)
        lines += ["## Fast Portal-Window Probes Already Run", ""]
        for _, score in scores.iterrows():
            lines.append(
                f"- `{score['Probe']}`: Kevin `{float(score['Portal Window Kevin']):.0f}`, "
                f"Xeeshan `{float(score['Portal Window Xeeshan']):.0f}`."
            )
        lines += [
            "",
            "Interpretation: the first short-horizon probes mostly failed, but the exact long-horizon breadth and MICROCHIP variants passed the portal-window threshold. Breadth is viable only when product-gated by the long-horizon signals; the earlier broad aggregation lost money.",
            "",
        ]
    full_path = OUT / "non_pebbles_promising_full_scores.csv"
    if full_path.exists():
        full_scores = pd.read_csv(full_path)
        lines += ["## Full Backtests For Promising Probes", ""]
        for _, score in full_scores.iterrows():
            lines.append(
                f"- `{score['Probe']}`: Kevin full `{float(score['Kevin Full']):.0f}`, "
                f"Xeeshan full `{float(score['Xeeshan Full']):.0f}`."
            )
        lines += [
            "",
            "Interpretation: the long-horizon breadth probe is now the first non-PEBBLES standalone probe with both strong portal-window replay and strong full-history PnL. It is worth turning into a formal candidate before any integration with candidate 16.",
            "",
        ]
    for _, row in probe.iterrows():
        enough = row.spread_adjusted_one_step_oracle_portal > 20000 and row.spread_adjusted_one_step_oracle_full > 200000
        lines.append(
            f"## `{row['product']}` / `{row['category']}`\n\n"
            f"- Edge to test: `{row.best_edge_family_portal}`.\n"
            f"- Execution: {row.recommended_execution}.\n"
            f"- Ceiling: portal oracle `{row.spread_adjusted_one_step_oracle_portal:.0f}`, full oracle `{row.spread_adjusted_one_step_oracle_full:.0f}`.\n"
            f"- Hindsight risk control: {'enough ceiling across portal and full data' if enough else 'probe only; ceiling/signal mix is weaker'}.\n"
            f"- Justification: portal proxy `{row.best_edge_proxy_portal:.0f}` and full proxy `{row.best_edge_proxy_full:.0f}` using online features only.\n"
            f"- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.\n"
        )
    lines.append("Do not integrate any of these into candidate 16 until a standalone portal probe passes.")
    (OUT / "non_pebbles_probe_blueprint.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    full = read_prices(ROUND)
    portal = read_prices(PORTAL)
    ranking = oracle_rows(full, portal)
    edges = edge_rows(full, portal, ranking)
    write_reports(ranking, edges)


if __name__ == "__main__":
    main()
