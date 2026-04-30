from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
R5 = ROOT / "ROUND5"
OUT = R5 / "research" / "outputs"


HORIZONS = [1, 5, 10, 50, 100]
COEFS = [-3, -2, -1, 1, 2, 3]


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


def load_prices() -> pd.DataFrame:
    frames = []
    for day in (2, 3, 4):
        path = R5 / f"prices_round_5_day_{day}.csv"
        df = pd.read_csv(path, sep=";")
        df["day"] = day
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    for col in [
        "bid_price_1",
        "bid_volume_1",
        "ask_price_1",
        "ask_volume_1",
        "bid_price_2",
        "bid_volume_2",
        "ask_price_2",
        "ask_volume_2",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    total = df["bid_volume_1"].clip(lower=0).fillna(0) + (-df["ask_volume_1"]).clip(lower=0).fillna(0)
    df["imbalance"] = np.where(total > 0, (df["bid_volume_1"].clip(lower=0).fillna(0) - (-df["ask_volume_1"]).clip(lower=0).fillna(0)) / total, 0.0)
    df["cat"] = df["product"].map(category)
    return df


def pivot_mid(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price").sort_index()


def identity_search(mid: pd.DataFrame) -> pd.DataFrame:
    products = list(mid.columns)
    dev = mid - 10000.0
    ret = mid.groupby(level=0).diff(50)
    corr = ret.corr().fillna(0.0).abs()
    rows = []
    for target in products:
        target_cat = category(target)
        peers = [p for p in products if p != target and category(p) == target_cat]
        corr_peers = [p for p in corr[target].sort_values(ascending=False).index if p != target][:10]
        peers = list(dict.fromkeys(peers + corr_peers))
        y = dev[target].to_numpy(dtype=float)
        future_y = dev[target].groupby(level=0).shift(-50).to_numpy(dtype=float)
        for b in peers:
            x = dev[b].to_numpy(dtype=float)
            fx = dev[b].groupby(level=0).shift(-50).to_numpy(dtype=float)
            residual = y - x
            rows.append(score_identity(target, (b,), (1,), residual, future_y - fx, "spread"))
        for b, c in itertools.combinations(peers[:12], 2):
            xb = dev[b].to_numpy(dtype=float)
            xc = dev[c].to_numpy(dtype=float)
            fxb = dev[b].groupby(level=0).shift(-50).to_numpy(dtype=float)
            fxc = dev[c].groupby(level=0).shift(-50).to_numpy(dtype=float)
            for cb, cc in itertools.product(COEFS, repeat=2):
                if cb + cc == 0:
                    continue
                residual = y - (cb * xb + cc * xc)
                future_residual = future_y - (cb * fxb + cc * fxc)
                rows.append(score_identity(target, (b, c), (cb, cc), residual, future_residual, "small_int_dev"))
    out = pd.DataFrame(rows)
    out = out.replace([np.inf, -np.inf], np.nan).dropna(subset=["portal_reversion_proxy"])
    out = out.sort_values(["portal_reversion_proxy", "portal_resid_std"], ascending=[False, True])
    return out.head(1000)


def score_identity(target: str, peers: tuple[str, ...], coefs: tuple[int, ...], residual: np.ndarray, future_residual: np.ndarray, kind: str) -> dict:
    valid = np.isfinite(residual)
    if valid.sum() < 1000:
        return {}
    centered = residual - np.nanmedian(residual)
    std = float(np.nanstd(centered))
    if std < 1e-9:
        std = 1.0
    z = centered / std
    change = future_residual - residual
    # Reversion PnL: if residual rich, sell target/buy basket; profit if residual falls.
    pnl = -np.sign(z) * change
    mask = np.isfinite(pnl) & (np.abs(z) > 1.5)
    portal_mask = mask.copy()
    # day 4 is the official-window proxy.
    n_per_day = len(residual) // 3
    day4 = np.zeros_like(mask, dtype=bool)
    day4[-n_per_day:] = True
    day_scores = []
    for i in range(3):
        m = mask.copy()
        m[: i * n_per_day] = False
        m[(i + 1) * n_per_day :] = False
        day_scores.append(float(np.nansum(pnl[m])) if m.any() else 0.0)
    portal_mask &= day4
    return {
        "target": target,
        "category": category(target),
        "kind": kind,
        "peers": "|".join(peers),
        "coefs": "|".join(map(str, coefs)),
        "full_resid_std": round(std, 4),
        "portal_resid_std": round(float(np.nanstd(centered[day4])), 4),
        "full_reversion_proxy": round(float(np.nansum(pnl[mask])) if mask.any() else 0.0, 2),
        "portal_reversion_proxy": round(float(np.nansum(pnl[portal_mask])) if portal_mask.any() else 0.0, 2),
        "signal_count": int(mask.sum()),
        "portal_signal_count": int(portal_mask.sum()),
        "day2_proxy": round(day_scores[0], 2),
        "day3_proxy": round(day_scores[1], 2),
        "day4_proxy": round(day_scores[2], 2),
        "stability_min_day": round(min(day_scores), 2),
    }


def anchor_search(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    round_levels = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 10000]
    for product, g in df.groupby("product"):
        g = g.sort_values(["day", "timestamp"]).reset_index(drop=True)
        mid = g["mid_price"].to_numpy(float)
        anchors = {"median": float(np.nanmedian(mid)), "mean": float(np.nanmean(mid)), "10000": 10000.0}
        for base in round_levels:
            anchors[f"round_{base}"] = round(float(np.nanmedian(mid)) / base) * base
        for name, anchor in anchors.items():
            for h in HORIZONS:
                fwd = g.groupby("day")["mid_price"].shift(-h).to_numpy(float)
                dev = mid - anchor
                for side in ["two_sided", "buy_low", "sell_high"]:
                    if side == "buy_low":
                        mask = dev < -max(2.0, 0.35 * np.nanstd(dev))
                        pnl = fwd - mid
                    elif side == "sell_high":
                        mask = dev > max(2.0, 0.35 * np.nanstd(dev))
                        pnl = mid - fwd
                    else:
                        mask = np.abs(dev) > max(2.0, 0.35 * np.nanstd(dev))
                        pnl = -np.sign(dev) * (fwd - mid)
                    mask &= np.isfinite(pnl)
                    portal = mask & (g["day"].to_numpy() == 4)
                    if mask.sum() < 50:
                        continue
                    rows.append(
                        {
                            "product": product,
                            "category": category(product),
                            "anchor_type": name,
                            "anchor": round(anchor, 4),
                            "side": side,
                            "horizon": h,
                            "full_proxy": round(float(np.nansum(pnl[mask])), 2),
                            "portal_proxy": round(float(np.nansum(pnl[portal])), 2),
                            "avg_pnl": round(float(np.nanmean(pnl[mask])), 4),
                            "hit_rate": round(float((pnl[mask] > 0).mean()), 4),
                            "count": int(mask.sum()),
                            "portal_count": int(portal.sum()),
                        }
                    )
    return pd.DataFrame(rows).sort_values(["portal_proxy", "full_proxy"], ascending=False).head(1500)


def passive_fill_oracle(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product, g in df.groupby("product"):
        g = g.sort_values(["day", "timestamp"]).reset_index(drop=True)
        for h in HORIZONS:
            fwd = g.groupby("day")["mid_price"].shift(-h)
            for style in ["join", "improve"]:
                bid_quote = g["bid_price_1"].copy()
                ask_quote = g["ask_price_1"].copy()
                if style == "improve":
                    bid_quote = np.minimum(g["bid_price_1"] + 1, g["ask_price_1"] - 1)
                    ask_quote = np.maximum(g["ask_price_1"] - 1, g["bid_price_1"] + 1)
                buy_mark = fwd - bid_quote
                sell_mark = ask_quote - fwd
                for gate_name, gate in [
                    ("all", np.ones(len(g), dtype=bool)),
                    ("imb_buy", g["imbalance"].to_numpy() > 0.35),
                    ("imb_sell", g["imbalance"].to_numpy() < -0.35),
                    ("spread_low", g["spread"].to_numpy() <= g["spread"].median()),
                    ("spread_high", g["spread"].to_numpy() >= g["spread"].median()),
                ]:
                    for side, mark in [("bid", buy_mark), ("ask", sell_mark)]:
                        if gate_name == "imb_buy" and side != "bid":
                            continue
                        if gate_name == "imb_sell" and side != "ask":
                            continue
                        arr = mark.to_numpy(float)
                        mask = gate & np.isfinite(arr)
                        portal = mask & (g["day"].to_numpy() == 4)
                        if mask.sum() < 100:
                            continue
                        rows.append(
                            {
                                "product": product,
                                "category": category(product),
                                "style": style,
                                "side": side,
                                "gate": gate_name,
                                "horizon": h,
                                "avg_markout": round(float(np.nanmean(arr[mask])), 4),
                                "portal_avg_markout": round(float(np.nanmean(arr[portal])) if portal.any() else 0.0, 4),
                                "hit_rate": round(float((arr[mask] > 0).mean()), 4),
                                "portal_hit_rate": round(float((arr[portal] > 0).mean()) if portal.any() else 0.0, 4),
                                "count": int(mask.sum()),
                                "portal_count": int(portal.sum()),
                                "full_proxy": round(float(np.nansum(arr[mask])), 2),
                                "portal_proxy": round(float(np.nansum(arr[portal])) if portal.any() else 0.0, 2),
                                "avg_fill_target": round(float(np.nanmean(np.where(side == "bid", g["bid_volume_1"], -g["ask_volume_1"])[mask])), 2),
                            }
                        )
    return pd.DataFrame(rows).sort_values(["portal_proxy", "avg_markout"], ascending=False)


def leadlag_search(mid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    products = list(mid.columns)
    for lead in products:
        for lag in products:
            if lead == lag:
                continue
            related = category(lead) == category(lag)
            if not related:
                # Keep cross-category search tractable but still broad: test all products with same suffix-ish no, plus high-level top correlations.
                pass
            for look in [1, 5, 10, 50, 100, 200]:
                lead_move = mid[lead].groupby(level=0).diff(look)
                for horizon in [1, 5, 10, 50]:
                    fut = mid[lag].groupby(level=0).shift(-horizon) - mid[lag]
                    valid = lead_move.notna() & fut.notna()
                    if valid.sum() < 1000:
                        continue
                    x = lead_move[valid].to_numpy(float)
                    y = fut[valid].to_numpy(float)
                    sx = np.nanstd(x)
                    sy = np.nanstd(y)
                    if sx < 1e-9 or sy < 1e-9:
                        continue
                    ic = float(np.nanmean((x - np.nanmean(x)) * (y - np.nanmean(y))) / (sx * sy))
                    pred = np.sign(x)
                    pnl = pred * y
                    portal = valid.index.get_level_values("day")[valid] == 4
                    rows.append(
                        {
                            "lead": lead,
                            "lag": lag,
                            "lead_category": category(lead),
                            "lag_category": category(lag),
                            "same_category": related,
                            "lookback": look,
                            "horizon": horizon,
                            "ic": round(ic, 5),
                            "abs_ic": round(abs(ic), 5),
                            "full_proxy": round(float(np.nansum(pnl)), 2),
                            "portal_proxy": round(float(np.nansum(pnl[portal])), 2),
                            "count": int(valid.sum()),
                            "portal_count": int(portal.sum()),
                        }
                    )
    out = pd.DataFrame(rows)
    return out.sort_values(["portal_proxy", "abs_ic"], ascending=[False, False]).head(2500)


def write_summary(identity: pd.DataFrame, anchors: pd.DataFrame, passive: pd.DataFrame, leadlag: pd.DataFrame) -> None:
    best_identity = identity.head(10)
    best_anchor = anchors.head(10)
    best_passive = passive.head(10)
    best_leadlag = leadlag.head(10)
    lines = [
        "# Missing Mechanism Discovery Summary",
        "",
        "This sprint searched for mechanisms rather than another candidate-35/36 product tweak.",
        "",
        "## Best Mechanism Proxies",
        "",
        "### Identity / Basket",
        best_identity.to_markdown(index=False),
        "",
        "### Anchor",
        best_anchor.to_markdown(index=False),
        "",
        "### Passive Fill",
        best_passive.to_markdown(index=False),
        "",
        "### Lead-Lag",
        best_leadlag.to_markdown(index=False),
        "",
        "## Read",
        "",
        "- These tables are oracle/proxy diagnostics, not submitted strategy scores.",
        "- A mechanism is candidate-worthy only if portal proxy is strong, full proxy is not obviously toxic, counts are high, and the rule is online-computable.",
        "- The next step is to convert the strongest rows into executable probes only if they plausibly add at least `10k` to the active branches.",
    ]
    (OUT / "missing_mechanism_discovery_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_prices()
    mid = pivot_mid(df)
    print("identity")
    identity = identity_search(mid)
    identity.to_csv(OUT / "missing_mechanism_identity_search.csv", index=False)
    print("anchors")
    anchors = anchor_search(df)
    anchors.to_csv(OUT / "missing_mechanism_anchor_search.csv", index=False)
    print("passive")
    passive = passive_fill_oracle(df)
    passive.to_csv(OUT / "missing_mechanism_passive_fill_oracle.csv", index=False)
    print("leadlag")
    leadlag = leadlag_search(mid)
    leadlag.to_csv(OUT / "missing_mechanism_leadlag_search.csv", index=False)
    pd.DataFrame(columns=["strategy", "mechanism", "portal_kevin", "portal_xeeshan", "full_kevin", "full_xeeshan", "notes"]).to_csv(
        OUT / "missing_mechanism_probe_scores.csv", index=False
    )
    write_summary(identity, anchors, passive, leadlag)
    (OUT / "missing_mechanism_candidate_paths.md").write_text(
        "# Missing Mechanism Candidate Paths\n\n"
        "Executable probes have not been generated by this diagnostic script directly. Convert only rows with strong portal proxy, adequate sample count, and plausible full stability.\n",
        encoding="utf-8",
    )
    print("done")


if __name__ == "__main__":
    main()
