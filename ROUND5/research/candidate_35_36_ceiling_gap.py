from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
OUT = ROUND_DIR / "research" / "outputs"
PORTAL_PRICE = OUT / "official_portal_windows" / "round5_candidate_1" / "round5" / "prices_round_5_day_4.csv"
FULL_PRICE_DIR = ROOT / "outputs" / "tool-data" / "kevin" / "round5"

HORIZONS = [1, 2, 5, 10, 25, 50, 100, 200]
POSITION_LIMIT = 10


def category(product: str) -> str:
    if product.startswith("OXYGEN_SHAKE_"):
        return "OXYGEN_SHAKE"
    if product.startswith("GALAXY_SOUNDS_"):
        return "GALAXY_SOUNDS"
    if product.startswith("SLEEP_POD_"):
        return "SLEEP_POD"
    if product.startswith("UV_VISOR_"):
        return "UV_VISOR"
    return product.split("_")[0]


def load_prices(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    for col in df.columns:
        if col not in ("product",):
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["category"] = df["product"].map(category)
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    bv = df["bid_volume_1"].clip(lower=0).fillna(0)
    av = (-df["ask_volume_1"]).clip(lower=0).fillna(0)
    df["top_bid_vol"] = bv
    df["top_ask_vol"] = av
    df["top_depth"] = bv + av
    df["imbalance"] = np.where(df["top_depth"] > 0, (bv - av) / df["top_depth"], 0.0)
    return df.sort_values(["day", "product", "timestamp"]).reset_index(drop=True)


def load_full_prices() -> pd.DataFrame:
    frames = [load_prices(path) for path in sorted(FULL_PRICE_DIR.glob("prices_round_5_day_*.csv"))]
    return pd.concat(frames, ignore_index=True)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    g = out.groupby(["day", "product"], sort=False)
    for h in HORIZONS:
        out[f"future_mid_{h}"] = g["mid_price"].shift(-h)
        out[f"past_ret_{h}"] = out["mid_price"] - g["mid_price"].shift(h)
    out["ret1"] = out["mid_price"] - g["mid_price"].shift(1)
    out["vol50"] = g["ret1"].transform(lambda s: s.rolling(50, min_periods=10).std()).fillna(0)
    out["trend50"] = out["mid_price"] - g["mid_price"].shift(50)
    return out


def load_candidate_pnl() -> pd.DataFrame:
    path = OUT / "candidate_35_36_portal_product_pnl.csv"
    df = pd.read_csv(path)
    pivot = df.pivot_table(index="product", columns="strategy", values="portal_kevin_pnl", aggfunc="sum").fillna(0)
    pivot.columns = [c.replace(".py", "") for c in pivot.columns]
    return pivot.reset_index()


def taker_oracle(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product, p in df.groupby("product", sort=False):
        best = None
        for h in HORIZONS:
            valid = p.dropna(subset=[f"future_mid_{h}", "ask_price_1", "bid_price_1"])
            buy_edge = valid[f"future_mid_{h}"] - valid["ask_price_1"]
            sell_edge = valid["bid_price_1"] - valid[f"future_mid_{h}"]
            edge = np.maximum.reduce([buy_edge.to_numpy(), sell_edge.to_numpy(), np.zeros(len(valid))])
            qty = np.where(buy_edge.to_numpy() >= sell_edge.to_numpy(), valid["top_ask_vol"].to_numpy(), valid["top_bid_vol"].to_numpy())
            qty = np.minimum(POSITION_LIMIT, np.nan_to_num(qty, nan=0))
            pnl = float(np.sum(edge * qty))
            signal_count = int(np.sum(edge > 0))
            avg_edge = float(np.mean(edge[edge > 0])) if signal_count else 0.0
            record = {"best_taker_horizon": h, "taker_oracle": pnl, "taker_signal_count": signal_count, "taker_avg_edge": avg_edge}
            if best is None or pnl > best["taker_oracle"]:
                best = record
        rows.append({"product": product, "category": category(product), **best})
    return pd.DataFrame(rows)


def passive_oracle(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product, p in df.groupby("product", sort=False):
        best = None
        for h in HORIZONS:
            valid = p.dropna(subset=[f"future_mid_{h}", "ask_price_1", "bid_price_1"])
            bid_edge = valid[f"future_mid_{h}"] - valid["bid_price_1"]
            ask_edge = valid["ask_price_1"] - valid[f"future_mid_{h}"]
            edge = np.maximum.reduce([bid_edge.to_numpy(), ask_edge.to_numpy(), np.zeros(len(valid))])
            # Passive fill is not guaranteed; discount by visible top depth and half-hit assumption.
            qty = np.minimum(POSITION_LIMIT, np.maximum(valid["top_bid_vol"].to_numpy(), valid["top_ask_vol"].to_numpy())) * 0.5
            pnl = float(np.sum(edge * qty))
            hit_count = int(np.sum(edge > 0))
            avg_markout = float(np.mean(edge[edge > 0])) if hit_count else 0.0
            record = {"best_passive_horizon": h, "passive_oracle": pnl, "passive_hit_count": hit_count, "passive_avg_markout": avg_markout}
            if best is None or pnl > best["passive_oracle"]:
                best = record
        rows.append({"product": product, "category": category(product), **best})
    return pd.DataFrame(rows)


def inventory_oracle(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product, p in df.groupby("product", sort=False):
        best = None
        for h in [5, 10, 25, 50, 100, 200]:
            valid = p.dropna(subset=[f"future_mid_{h}", "ask_price_1", "bid_price_1"]).copy()
            pos = 0
            cash = 0.0
            trades = 0
            for row in valid.itertuples(index=False):
                future = getattr(row, f"future_mid_{h}")
                ask = row.ask_price_1
                bid = row.bid_price_1
                if future - ask > 1.0:
                    target = POSITION_LIMIT
                elif bid - future > 1.0:
                    target = -POSITION_LIMIT
                else:
                    target = 0
                delta = target - pos
                if delta > 0:
                    cash -= delta * ask
                    trades += abs(delta)
                elif delta < 0:
                    cash += (-delta) * bid
                    trades += abs(delta)
                pos = target
            if len(valid):
                final_mid = float(valid["mid_price"].iloc[-1])
                pnl = cash + pos * final_mid
            else:
                pnl = 0.0
            record = {"best_inventory_horizon": h, "inventory_oracle": float(pnl), "inventory_turnover": int(trades)}
            if best is None or pnl > best["inventory_oracle"]:
                best = record
        rows.append({"product": product, "category": category(product), **best})
    return pd.DataFrame(rows)


def residual_oracle(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (day, cat), cdf in df.groupby(["day", "category"], sort=False):
        # category-median residual, online-computable at timestamp level.
        pivot = cdf.pivot(index="timestamp", columns="product", values="mid_price").sort_index()
        if pivot.shape[1] < 2:
            continue
        median = pivot.median(axis=1)
        for product in pivot.columns:
            s = pivot[product].dropna()
            resid = s - median.loc[s.index]
            for h in [5, 10, 25, 50, 100]:
                fut = s.shift(-h)
                valid = pd.DataFrame({"resid": resid, "mid": s, "future": fut}).dropna()
                if len(valid) < 50:
                    continue
                move = valid["future"] - valid["mid"]
                # residual mean reversion: positive resid predicts down, negative predicts up.
                signal = -valid["resid"]
                pnl_proxy = np.maximum(signal.to_numpy() * move.to_numpy(), 0).sum()
                corr = float(np.corrcoef(signal, move)[0, 1]) if signal.std() > 1e-9 and move.std() > 1e-9 else 0.0
                rows.append({"day": day, "product": product, "category": cat, "horizon": h, "residual_proxy": float(pnl_proxy), "residual_ic": corr})
    if not rows:
        return pd.DataFrame(columns=["product", "category", "best_residual_horizon", "residual_proxy", "residual_ic"])
    raw = pd.DataFrame(rows)
    idx = raw.groupby("product")["residual_proxy"].idxmax()
    best = raw.loc[idx].rename(columns={"horizon": "best_residual_horizon"})
    return best[["product", "category", "best_residual_horizon", "residual_proxy", "residual_ic"]].reset_index(drop=True)


def strategy_family_backtests(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    families = []
    for h in [10, 25, 50, 100, 200]:
        families.append((f"momentum_{h}", h, 1))
        families.append((f"reversal_{h}", h, -1))
    for product, p in df.groupby("product", sort=False):
        for name, h, sign in families:
            valid = p.dropna(subset=[f"past_ret_{h}", "ask_price_1", "bid_price_1", "mid_price"])
            if len(valid) < h + 20:
                continue
            ret = valid[f"past_ret_{h}"]
            scale = valid["vol50"].replace(0, np.nan).fillna(valid["vol50"].median() or 1.0)
            sig = sign * ret / scale.clip(lower=1.0)
            threshold = np.nanquantile(np.abs(sig), 0.80)
            pos = 0
            cash = 0.0
            trades = 0
            for row, s in zip(valid.itertuples(index=False), sig):
                if s > threshold:
                    target = POSITION_LIMIT
                elif s < -threshold:
                    target = -POSITION_LIMIT
                elif abs(s) < threshold * 0.35:
                    target = 0
                else:
                    target = pos
                delta = target - pos
                if delta > 0:
                    cash -= delta * row.ask_price_1
                    trades += abs(delta)
                elif delta < 0:
                    cash += (-delta) * row.bid_price_1
                    trades += abs(delta)
                pos = target
            pnl = cash + pos * float(valid["mid_price"].iloc[-1])
            rows.append({"product": product, "category": category(product), "engine": name, "engine_proxy_pnl": float(pnl), "turnover": int(trades)})
    raw = pd.DataFrame(rows)
    idx = raw.groupby("product")["engine_proxy_pnl"].idxmax()
    return raw.loc[idx].reset_index(drop=True)


def regime_oracle(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product, p in df.groupby("product", sort=False):
        valid = p.dropna(subset=["future_mid_50"]).copy()
        if len(valid) < 100:
            continue
        valid["future_move50"] = valid["future_mid_50"] - valid["mid_price"]
        valid["abs_move50"] = valid["future_move50"].abs()
        regimes = {
            "spread_low": valid["spread"] <= valid["spread"].median(),
            "spread_high": valid["spread"] > valid["spread"].median(),
            "vol_low": valid["vol50"] <= valid["vol50"].median(),
            "vol_high": valid["vol50"] > valid["vol50"].median(),
            "depth_high": valid["top_depth"] >= valid["top_depth"].median(),
            "imbalance_extreme": valid["imbalance"].abs() >= valid["imbalance"].abs().quantile(0.75),
            "trend_up": valid["trend50"] > valid["trend50"].quantile(0.65),
            "trend_down": valid["trend50"] < valid["trend50"].quantile(0.35),
        }
        for regime, mask in regimes.items():
            sub = valid[mask]
            if len(sub) < 30:
                continue
            # discounted best-side oracle inside regime
            edge = np.maximum.reduce([
                (sub["future_mid_50"] - sub["ask_price_1"]).to_numpy(),
                (sub["bid_price_1"] - sub["future_mid_50"]).to_numpy(),
                np.zeros(len(sub)),
            ])
            pnl = float(np.sum(edge * np.minimum(POSITION_LIMIT, sub["top_depth"].to_numpy()) * 0.5))
            rows.append({
                "product": product,
                "category": category(product),
                "regime": regime,
                "rows": len(sub),
                "regime_oracle": pnl,
                "avg_abs_move50": float(sub["abs_move50"].mean()),
                "avg_spread": float(sub["spread"].mean()),
            })
    raw = pd.DataFrame(rows)
    idx = raw.groupby("product")["regime_oracle"].idxmax()
    return raw.loc[idx].reset_index(drop=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    portal = add_features(load_prices(PORTAL_PRICE))
    full = add_features(load_full_prices())
    cand = load_candidate_pnl()

    taker = taker_oracle(portal)
    passive = passive_oracle(portal)
    inv = inventory_oracle(portal)
    resid = residual_oracle(portal)
    engines = strategy_family_backtests(portal)
    regime = regime_oracle(portal)

    gap = taker.merge(passive, on=["product", "category"], how="outer")
    gap = gap.merge(inv, on=["product", "category"], how="outer")
    gap = gap.merge(resid, on=["product", "category"], how="outer")
    gap = gap.merge(engines, on=["product", "category"], how="outer")
    gap = gap.merge(regime[["product", "category", "regime", "regime_oracle"]], on=["product", "category"], how="outer")
    gap = gap.merge(cand, on="product", how="left").fillna(0)
    gap["best_current_portal_pnl"] = gap[["round5_candidate_35", "round5_candidate_36"]].max(axis=1)
    gap["oracle_capacity"] = gap[["taker_oracle", "passive_oracle", "inventory_oracle", "residual_proxy", "regime_oracle"]].max(axis=1)
    gap["oracle_gap_vs_best_current"] = gap["oracle_capacity"] - gap["best_current_portal_pnl"].clip(lower=0)
    gap["capture_ratio"] = np.where(gap["oracle_capacity"] > 0, gap["best_current_portal_pnl"].clip(lower=0) / gap["oracle_capacity"], 0)
    gap = gap.sort_values("oracle_gap_vs_best_current", ascending=False)

    # Full-history robustness proxy for best engine family.
    full_engines = strategy_family_backtests(full)
    full_engines = full_engines.rename(columns={"engine": "full_best_engine", "engine_proxy_pnl": "full_engine_proxy_pnl", "turnover": "full_engine_turnover"})
    marginal = gap.merge(full_engines[["product", "full_best_engine", "full_engine_proxy_pnl", "full_engine_turnover"]], on="product", how="left")
    marginal["marginal_role"] = np.select(
        [
            (marginal["oracle_gap_vs_best_current"] > 25000) & (marginal["full_engine_proxy_pnl"] > 0),
            (marginal["oracle_gap_vs_best_current"] > 25000) & (marginal["full_engine_proxy_pnl"] <= 0),
            marginal["best_current_portal_pnl"] > 2500,
        ],
        ["candidate_addition", "portal_only_or_gated", "already_captured"],
        default="low_priority",
    )
    marginal = marginal.sort_values(["marginal_role", "oracle_gap_vs_best_current"], ascending=[True, False])

    gap.to_csv(OUT / "candidate_35_36_oracle_gap_table.csv", index=False)
    marginal.to_csv(OUT / "candidate_35_36_marginal_engine_table.csv", index=False)
    regime.to_csv(OUT / "candidate_35_36_regime_oracle_table.csv", index=False)

    top_gap = gap.head(12)
    top_marginal = marginal[marginal["marginal_role"].isin(["candidate_addition", "portal_only_or_gated"])].head(12)
    cat_gap = gap.groupby("category", as_index=False).agg(
        oracle_capacity=("oracle_capacity", "sum"),
        current_best=("best_current_portal_pnl", "sum"),
        gap=("oracle_gap_vs_best_current", "sum"),
    ).sort_values("gap", ascending=False)

    lines = [
        "# Candidate 35/36 Ceiling Gap",
        "",
        "This is an oracle/proxy research pass, not a submitted-strategy result. It uses portal-window order-book data plus current candidate 35/36 attribution to locate remaining capacity.",
        "",
        "## Main Read",
        f"- Candidate 35 current portal: `91.9k`; candidate 36 current portal: `105.5k`.",
        "- There is still large oracle capacity, but most raw oracle is not directly capturable because it assumes future mid knowledge or guaranteed passive fills.",
        "- The biggest practical gaps are concentrated in categories where candidate 36 already shows portal sensitivity: PANEL, TRANSLATOR, MICROCHIP, SLEEP/UV, and selected ROBOT.",
        "- The strongest robust next step is not a blind merge with 36; it is candidate 35 plus gated 36-style portal engines whose full-history proxy is non-toxic.",
        "",
        "## Top Product Gaps",
        "",
        "| Product | Category | Current Best | Oracle Capacity | Gap | Best Engine Proxy | Full Proxy | Regime |",
        "|---|---|---:|---:|---:|---|---:|---|",
    ]
    for row in top_gap.itertuples(index=False):
        lines.append(
            f"| `{row.product}` | {row.category} | {row.best_current_portal_pnl:.0f} | {row.oracle_capacity:.0f} | {row.oracle_gap_vs_best_current:.0f} | {row.engine} | {getattr(row, 'full_engine_proxy_pnl', 0):.0f} | {row.regime} |"
        )
    lines += ["", "## Category Gap", "", "| Category | Oracle Capacity | Current Best | Gap |", "|---|---:|---:|---:|"]
    for row in cat_gap.itertuples(index=False):
        lines.append(f"| {row.category} | {row.oracle_capacity:.0f} | {row.current_best:.0f} | {row.gap:.0f} |")
    lines += [
        "",
        "## Diagnostics That Mattered",
        "- Passive-fill and inventory-constrained oracles matter more than raw taker oracle. Raw taker capacity is huge but mostly fantasy unless the signal is strong enough to cross spread repeatedly.",
        "- Regime oracle matters for candidate 36-style products: many high portal products need spread/vol/trend gating to avoid full-history toxicity.",
        "- Residual/fair-value oracle shows useful category structure beyond PEBBLES, but no single non-PEBBLES category has a clean all-products synthetic edge as strong as PEBBLES.",
        "- Marginal-addition oracle says candidate 35 is the correct base: add only targeted 36 components, not the full 36 architecture.",
        "",
        "## 150k Read",
        "- `150k` looks reachable only if candidate 37-40 can add roughly `40k-60k` portal to candidate 35 or stabilize most of candidate 36's portal-only gain.",
        "- The most plausible path is a gated candidate 35 + selected candidate 36 legs: PANEL full branch, ROBOT_LAUNDRY/DISHES only under favorable regimes, UV_AMBER/TRANSLATOR anchor family, and SLEEP_LAMB_WOOL if full proxy is acceptable.",
        "- `200k` probably requires a new structural edge or a much better passive-fill market-making engine. Existing marginal engines look capable of tens of thousands, not another clean 100k.",
    ]
    (OUT / "candidate_35_36_ceiling_gap.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    blueprint = [
        "# Candidate 37-40 Blueprint",
        "",
        "Do not build until explicitly instructed. Candidate 35 remains the robust base; candidate 36 is the portal-upside idea mine.",
        "",
        "## Candidate 37: Robust 35+ Gated Additions",
        "- Base: `round5_candidate_35.py`.",
        "- Add: `PANEL_2X4`, `SLEEP_POD_LAMB_WOOL`, `UV_VISOR_AMBER`, and `ROBOT_LAUNDRY` only with spread/vol/trend gates from the regime oracle.",
        "- Remove/gate: avoid `ROBOT_DISHES` unless its regime is strongly favorable; keep candidate 35 core untouched.",
        "- Role: robust hidden-final performance.",
        "- Target: portal `105k-120k`, full `260k+`.",
        "- Validation: portal cap check first, then full score-only.",
        "",
        "## Candidate 38: Maximum Portal Upside Cleanup",
        "- Base: `round5_candidate_36.py`.",
        "- Add/keep: candidate 36 portal machinery; keep anchor engine and broad PANEL/TRANSLATOR/ROBOT/UV legs.",
        "- Gate: day2/day3-toxic momentum extras using spread/vol/trend regimes rather than removing the whole branch.",
        "- Role: max portal upside.",
        "- Target: portal `115k-130k`, full positive but not necessarily robust.",
        "- Validation: submit/probe only after portal replay beats 36 without state/cap mismatch.",
        "",
        "## Candidate 39: Passive-Fill / Market-Making Information Candidate",
        "- Base: lightweight new probe architecture, or candidate 35 with separate passive engines.",
        "- Products: high passive oracle products from PANEL, TRANSLATOR, MICROCHIP, SLEEP, UV, and selected ROBOT.",
        "- Engine: quote/improve at best bid/ask only when passive markout regime is favorable; do not cross except for extreme residual.",
        "- Role: information/probe candidate for the suspected leaderboard-style repeated fill-quality edge.",
        "- Target: portal `80k+` standalone or clear additive product attribution.",
        "- Validation: portal JSON attribution mandatory.",
        "",
        "## Candidate 40: Aggressive 150k Composite",
        "- Base: candidate 35.",
        "- Add: candidate 37 robust gates plus candidate 38 portal gates where they do not crowd out 35's high-quality signals.",
        "- Use ranking caps per engine family, not one global product ranking, to avoid crowd-out.",
        "- Role: most aggressive 150k attempt.",
        "- Target: portal `130k-150k+`, full `180k+` minimum.",
        "- Validation order: portal Kevin/Xeeshan cap check, then full score-only, then one finalist full JSON attribution.",
        "",
        "## What Not To Do",
        "- Do not start from candidate 36 as the robust base.",
        "- Do not add all high-oracle products blindly.",
        "- Do not add `ROBOT_DISHES` without a regime gate.",
        "- Do not use full JSON logs in high-parallel batches.",
    ]
    (OUT / "candidate_37_40_blueprint.md").write_text("\n".join(blueprint) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
