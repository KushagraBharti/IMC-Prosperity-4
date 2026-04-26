from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PRODUCTS = [
    "HYDROGEL_PACK",
    "VELVETFRUIT_EXTRACT",
    "VEV_4000",
    "VEV_4500",
    "VEV_5000",
    "VEV_5100",
    "VEV_5200",
    "VEV_5300",
    "VEV_5400",
    "VEV_5500",
    "VEV_6000",
    "VEV_6500",
]

ACTIVE_OPTIONS = ["VEV_5000", "VEV_5100", "VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500"]
STRIKES = {
    "VEV_4000": 4000,
    "VEV_4500": 4500,
    "VEV_5000": 5000,
    "VEV_5100": 5100,
    "VEV_5200": 5200,
    "VEV_5300": 5300,
    "VEV_5400": 5400,
    "VEV_5500": 5500,
    "VEV_6000": 6000,
    "VEV_6500": 6500,
}
SIGMA = {
    4000: 0.5244,
    4500: 0.3056,
    5000: 0.2419,
    5100: 0.24035,
    5200: 0.24215,
    5300: 0.24455,
    5400: 0.22960,
    5500: 0.24845,
    6000: 0.3775,
    6500: 0.5701,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deep Round 3 strategy and market diagnostics")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument(
        "--price",
        action="append",
        default=[],
        help="Named price CSV in the form source=path. Can be repeated.",
    )
    parser.add_argument(
        "--log",
        action="append",
        default=[],
        help="Named backtest log bundle in the form run=path. Can be repeated.",
    )
    parser.add_argument("--block-size", type=int, default=10_000)
    parser.add_argument("--markout", type=int, action="append", default=[100, 500, 1000, 5000, 10000, 25000])
    return parser.parse_args()


def parse_named_path(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError(f"Expected name=path, got {raw!r}")
    name, path = raw.split("=", 1)
    return name, Path(path)


def read_bundle(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                return json.loads(line)
    raise ValueError(f"Could not parse JSON bundle from {path}")


def parse_activities(raw: str) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    df = pd.read_csv(io.StringIO(raw), sep=";")
    return normalize_price_frame(df)


def normalize_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if col != "product":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "day" not in df.columns:
        df["day"] = 0
    return df


def read_prices(path: Path) -> pd.DataFrame:
    return normalize_price_frame(pd.read_csv(path, sep=";"))


def add_book_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bid_vol = df["bid_volume_1"].fillna(0.0)
    ask_vol = df["ask_volume_1"].fillna(0.0)
    denom = bid_vol + ask_vol
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["imbalance"] = np.where(denom > 0, (bid_vol - ask_vol) / denom, 0.0)
    df["microprice"] = np.where(
        denom > 0,
        (df["ask_price_1"] * bid_vol + df["bid_price_1"] * ask_vol) / denom,
        df["mid_price"],
    )
    df["micro_dev"] = df["microprice"] - df["mid_price"]
    bid_cols = ["bid_price_1", "bid_price_2", "bid_price_3"]
    ask_cols = ["ask_price_1", "ask_price_2", "ask_price_3"]
    df["book_center_3"] = df[bid_cols + ask_cols].mean(axis=1)
    df["book_center_3_dev"] = df["book_center_3"] - df["mid_price"]
    df["block"] = (df["timestamp"] // 10_000).astype(int)
    return df


def own_fills(bundle: dict) -> pd.DataFrame:
    rows = []
    for trade in bundle.get("tradeHistory", []) or []:
        buyer = trade.get("buyer", "")
        seller = trade.get("seller", "")
        if buyer != "SUBMISSION" and seller != "SUBMISSION":
            continue
        side = "buy" if buyer == "SUBMISSION" else "sell"
        rows.append(
            {
                "timestamp": int(trade["timestamp"]),
                "product": trade.get("symbol"),
                "side": side,
                "price": float(trade["price"]),
                "quantity": float(trade["quantity"]),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["timestamp", "product", "side", "price", "quantity"])
    return pd.DataFrame(rows)


def pnl_by_product(run: str, activities: pd.DataFrame, block_size: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if activities.empty:
        empty = pd.DataFrame()
        return empty, empty, empty
    df = activities.sort_values(["product", "timestamp"]).copy()
    df["run"] = run
    product = (
        df.groupby("product", as_index=False)
        .agg(final_pnl=("profit_and_loss", "last"), max_pnl=("profit_and_loss", "max"), min_pnl=("profit_and_loss", "min"))
    )
    product["run"] = run
    df["pnl_delta"] = df.groupby("product")["profit_and_loss"].diff().fillna(df["profit_and_loss"])
    df["block"] = (df["timestamp"] // block_size).astype(int)
    block = df.groupby(["run", "product", "block"], as_index=False).agg(
        pnl_delta=("pnl_delta", "sum"),
        pnl_start=("profit_and_loss", "first"),
        pnl_end=("profit_and_loss", "last"),
        mid_start=("mid_price", "first"),
        mid_end=("mid_price", "last"),
    )
    block["mid_change"] = block["mid_end"] - block["mid_start"]
    worst = (
        df.sort_values(["product", "timestamp"])
        .assign(next_pnl=lambda x: x.groupby("product")["profit_and_loss"].shift(-1))
        .assign(pnl_step=lambda x: x["next_pnl"] - x["profit_and_loss"])
        .dropna(subset=["pnl_step"])
        .sort_values("pnl_step")
        .groupby("product", as_index=False)
        .head(10)
    )
    worst["run"] = run
    return product, block, worst


def classify_fill(row: pd.Series) -> str:
    bid = row.get("bid_price_1")
    ask = row.get("ask_price_1")
    price = row["price"]
    side = row["side"]
    if pd.isna(bid) or pd.isna(ask):
        return "unknown"
    if side == "buy":
        if price >= ask:
            return "taker"
        if price <= bid:
            return "passive"
        return "inside"
    if price <= bid:
        return "taker"
    if price >= ask:
        return "passive"
    return "inside"


def fill_markouts(run: str, fills: pd.DataFrame, books: pd.DataFrame, horizons: Iterable[int]) -> pd.DataFrame:
    if fills.empty or books.empty:
        return pd.DataFrame()
    base_cols = [
        "day",
        "timestamp",
        "product",
        "bid_price_1",
        "ask_price_1",
        "bid_volume_1",
        "ask_volume_1",
        "mid_price",
        "spread",
        "imbalance",
        "micro_dev",
        "block",
    ]
    book_cols = [c for c in base_cols if c in books.columns]
    merged = fills.merge(books[book_cols], on=["timestamp", "product"], how="left")
    merged["run"] = run
    merged["fill_class"] = merged.apply(classify_fill, axis=1)
    merged["entry_edge_to_mid"] = np.where(
        merged["side"] == "buy",
        merged["mid_price"] - merged["price"],
        merged["price"] - merged["mid_price"],
    )
    merged["signed_qty"] = np.where(merged["side"] == "buy", merged["quantity"], -merged["quantity"])

    future_source = books[["timestamp", "product", "mid_price"]].copy()
    for horizon in horizons:
        future = future_source.copy()
        future["timestamp"] = future["timestamp"] - horizon
        future = future.rename(columns={"mid_price": f"future_mid_{horizon}"})
        merged = merged.merge(future, on=["timestamp", "product"], how="left")
        col = f"future_mid_{horizon}"
        merged[f"markout_{horizon}"] = np.where(
            merged["side"] == "buy",
            merged[col] - merged["price"],
            merged["price"] - merged[col],
        )
        merged[f"markout_pnl_{horizon}"] = merged[f"markout_{horizon}"] * merged["quantity"]
    return merged


def summarize_fills(markouts: pd.DataFrame, horizons: Iterable[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if markouts.empty:
        return pd.DataFrame(), pd.DataFrame()
    agg_spec = {
        "fills": ("quantity", "count"),
        "quantity": ("quantity", "sum"),
        "avg_price": ("price", "mean"),
        "entry_edge_pnl": ("entry_edge_to_mid", lambda x: float(np.sum(x * markouts.loc[x.index, "quantity"]))),
        "first_ts": ("timestamp", "min"),
        "last_ts": ("timestamp", "max"),
    }
    for horizon in horizons:
        agg_spec[f"markout_pnl_{horizon}"] = (f"markout_pnl_{horizon}", "sum")
        agg_spec[f"avg_markout_{horizon}"] = (f"markout_{horizon}", "mean")
    by_class = (
        markouts.groupby(["run", "product", "side", "fill_class"], as_index=False)
        .agg(**agg_spec)
        .sort_values(["run", "product", "side", "fill_class"])
    )
    by_block = (
        markouts.groupby(["run", "product", "block", "side", "fill_class"], as_index=False)
        .agg(fills=("quantity", "count"), quantity=("quantity", "sum"), avg_price=("price", "mean"))
        .sort_values(["run", "product", "block", "side", "fill_class"])
    )
    return by_class, by_block


def inventory_path(run: str, fills: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if fills.empty:
        return pd.DataFrame(), pd.DataFrame()
    df = fills.sort_values(["product", "timestamp"]).copy()
    df["signed_qty"] = np.where(df["side"] == "buy", df["quantity"], -df["quantity"])
    df["inventory"] = df.groupby("product")["signed_qty"].cumsum()
    df["run"] = run
    summary = df.groupby(["run", "product"], as_index=False).agg(
        min_inventory=("inventory", "min"),
        max_inventory=("inventory", "max"),
        end_inventory=("inventory", "last"),
        turnover=("quantity", "sum"),
        fill_count=("quantity", "count"),
    )
    return df, summary


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


def add_hydro_alpha(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source, source_df in df[df["product"] == "HYDROGEL_PACK"].groupby("source"):
        for day, g in source_df.sort_values("timestamp").groupby("day"):
            anchor = 9991.0
            history: list[float] = []
            for _, row in g.iterrows():
                mid = float(row["mid_price"])
                anchor = 0.95 * anchor + 0.05 * mid
                history.append(mid)
                history = history[-48:]
                long_avg = sum(history[-20:]) / min(len(history), 20)
                short_avg = sum(history[-5:]) / min(len(history), 5)
                fair = anchor + 10.5 * float(row["imbalance"]) + 0.04 * (long_avg - mid) + 0.03 * (short_avg - long_avg)
                out = row.to_dict()
                out["source"] = source
                out["fair_model"] = fair
                out["signal"] = fair - mid
                rows.append(out)
    return pd.DataFrame(rows)


def add_vfe_alpha(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source, source_df in df.groupby("source"):
        vfe = source_df[source_df["product"] == "VELVETFRUIT_EXTRACT"].copy()
        v4000 = source_df[source_df["product"] == "VEV_4000"][["day", "timestamp", "mid_price"]].rename(columns={"mid_price": "m4000"})
        v4500 = source_df[source_df["product"] == "VEV_4500"][["day", "timestamp", "mid_price"]].rename(columns={"mid_price": "m4500"})
        merged = vfe.merge(v4000, on=["day", "timestamp"], how="left").merge(v4500, on=["day", "timestamp"], how="left")
        implied_num = (merged["m4000"] + 4000.0) * 0.25 + (merged["m4500"] + 4500.0) * 0.35
        implied_den = np.where(merged[["m4000", "m4500"]].notna().all(axis=1), 0.60, np.nan)
        merged["deep_implied"] = implied_num / implied_den
        merged["fair_model"] = 0.55 * 5260.0 + 0.45 * merged["deep_implied"]
        merged["signal"] = merged["fair_model"] - merged["mid_price"]
        merged["source"] = source
        rows.append(merged)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def alpha_deciles(alpha: pd.DataFrame, horizons: Iterable[int], name: str) -> pd.DataFrame:
    if alpha.empty:
        return pd.DataFrame()
    frames = []
    alpha = alpha.sort_values(["source", "day", "timestamp"]).copy()
    for horizon in horizons:
        col = f"future_mid_{horizon}"
        shifted = alpha[["source", "day", "timestamp", "mid_price"]].copy()
        shifted["timestamp"] = shifted["timestamp"] - horizon
        shifted = shifted.rename(columns={"mid_price": col})
        sample = alpha.merge(shifted, on=["source", "day", "timestamp"], how="left")
        sample[f"ret_{horizon}"] = sample[col] - sample["mid_price"]
        sample = sample.dropna(subset=["signal", f"ret_{horizon}"])
        if sample.empty:
            continue
        for source, g in sample.groupby("source"):
            try:
                g = g.copy()
                g["signal_decile"] = pd.qcut(g["signal"], 10, labels=False, duplicates="drop")
            except ValueError:
                continue
            dec = g.groupby("signal_decile", as_index=False).agg(
                n=("signal", "size"),
                signal_mean=("signal", "mean"),
                future_ret_mean=(f"ret_{horizon}", "mean"),
                future_ret_median=(f"ret_{horizon}", "median"),
                hit_rate=(f"ret_{horizon}", lambda x: float((np.sign(g.loc[x.index, "signal"]) == np.sign(x)).mean())),
            )
            dec["source"] = source
            dec["horizon"] = horizon
            dec["model"] = name
            frames.append(dec)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def option_edges(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source, source_df in df.groupby("source"):
        vfe = source_df[source_df["product"] == "VELVETFRUIT_EXTRACT"][["day", "timestamp", "mid_price"]].rename(columns={"mid_price": "spot"})
        for product in ACTIVE_OPTIONS:
            opt = source_df[source_df["product"] == product].copy()
            if opt.empty:
                continue
            strike = STRIKES[product]
            merged = opt.merge(vfe, on=["day", "timestamp"], how="inner")
            if source == "full":
                tte_days = np.maximum(0.05, 8.0 - merged["day"] - merged["timestamp"] / 1_000_000.0)
            else:
                tte_days = np.maximum(0.05, 5.0 - merged["timestamp"] / 1_000_000.0)
            merged["bs"] = [bs_call(s, strike, t / 365.0, SIGMA[strike]) for s, t in zip(merged["spot"], tte_days)]
            merged["buy_edge"] = merged["bs"] - merged["ask_price_1"]
            merged["sell_edge"] = merged["bid_price_1"] - merged["bs"]
            merged["block"] = (merged["timestamp"] // 10_000).astype(int)
            for block, g in merged.groupby("block"):
                rows.append(
                    {
                        "source": source,
                        "product": product,
                        "strike": strike,
                        "block": int(block),
                        "n": len(g),
                        "mid_minus_bs_mean": float((g["mid_price"] - g["bs"]).mean()),
                        "buy_edge_gt_0_5": float((g["buy_edge"] > 0.5).mean()),
                        "sell_edge_gt_0_5": float((g["sell_edge"] > 0.5).mean()),
                        "buy_edge_gt_1": float((g["buy_edge"] > 1.0).mean()),
                        "sell_edge_gt_1": float((g["sell_edge"] > 1.0).mean()),
                        "buy_edge_p95": float(g["buy_edge"].quantile(0.95)),
                        "sell_edge_p95": float(g["sell_edge"].quantile(0.95)),
                    }
                )
    return pd.DataFrame(rows)


def save_plots(out_dir: Path, block_pnl: pd.DataFrame, inventory: pd.DataFrame, fills: pd.DataFrame, alpha: pd.DataFrame) -> None:
    if not block_pnl.empty:
        for run, g in block_pnl.groupby("run"):
            pivot = g.pivot_table(index="block", columns="product", values="pnl_delta", aggfunc="sum").fillna(0.0)
            ax = pivot.plot(kind="bar", stacked=True, figsize=(14, 6), title=f"Block PnL: {run}")
            ax.set_ylabel("PnL delta")
            plt.tight_layout()
            plt.savefig(out_dir / f"block_pnl_{run}.png", dpi=160)
            plt.close()
    if not inventory.empty:
        for run, g in inventory.groupby("run"):
            fig, ax = plt.subplots(figsize=(14, 6))
            for product in ["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_5000", "VEV_5100"]:
                p = g[g["product"] == product]
                if not p.empty:
                    ax.step(p["timestamp"], p["inventory"], where="post", label=product)
            ax.set_title(f"Inventory Path: {run}")
            ax.legend()
            plt.tight_layout()
            plt.savefig(out_dir / f"inventory_{run}.png", dpi=160)
            plt.close()
    if not fills.empty:
        class_counts = fills.groupby(["run", "product", "fill_class"], as_index=False)["quantity"].sum()
        for run, g in class_counts.groupby("run"):
            pivot = g.pivot_table(index="product", columns="fill_class", values="quantity", aggfunc="sum").fillna(0.0)
            ax = pivot.plot(kind="bar", stacked=True, figsize=(13, 5), title=f"Fill Quantity by Class: {run}")
            ax.set_ylabel("quantity")
            plt.tight_layout()
            plt.savefig(out_dir / f"fill_class_{run}.png", dpi=160)
            plt.close()
    if not alpha.empty:
        for source, g in alpha.groupby("source"):
            fig, ax = plt.subplots(figsize=(11, 5))
            for model, m in g[g["horizon"] == 1000].groupby("model"):
                ax.plot(m["signal_decile"], m["future_ret_mean"], marker="o", label=model)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.set_title(f"Signal Decile vs 1000-step Future Return: {source}")
            ax.set_xlabel("signal decile")
            ax.set_ylabel("future return")
            ax.legend()
            plt.tight_layout()
            plt.savefig(out_dir / f"alpha_deciles_{source}.png", dpi=160)
            plt.close()


def write_summary(
    out_dir: Path,
    product_pnl: pd.DataFrame,
    block_pnl: pd.DataFrame,
    fill_class: pd.DataFrame,
    inventory_summary: pd.DataFrame,
    alpha: pd.DataFrame,
    option_edge: pd.DataFrame,
    worst_steps: pd.DataFrame,
) -> None:
    lines = ["# Deep Round 3 Diagnostics", ""]
    if not product_pnl.empty:
        lines += ["## Product PnL", "", product_pnl.pivot_table(index="product", columns="run", values="final_pnl", aggfunc="sum").to_markdown(), ""]
    if not inventory_summary.empty:
        lines += ["## Inventory Summary", "", inventory_summary.to_markdown(index=False), ""]
    if not fill_class.empty:
        important = fill_class[fill_class["product"].isin(["HYDROGEL_PACK", "VELVETFRUIT_EXTRACT", "VEV_5000", "VEV_5100", "VEV_5200", "VEV_5300", "VEV_5400"])]
        lines += ["## Fill Class Summary", "", important.to_markdown(index=False), ""]
    if not block_pnl.empty:
        lines += ["## Worst Product Blocks", ""]
        worst_blocks = block_pnl.sort_values("pnl_delta").head(40)
        lines += [worst_blocks.to_markdown(index=False), ""]
    if not worst_steps.empty:
        lines += ["## Worst Single-Step PnL Drops", "", worst_steps.head(60).to_markdown(index=False), ""]
    if not alpha.empty:
        lines += ["## Alpha Deciles", ""]
        rows = []
        for (source, model, horizon), g in alpha.groupby(["source", "model", "horizon"]):
            lo = g.loc[g["signal_decile"].idxmin()]
            hi = g.loc[g["signal_decile"].idxmax()]
            rows.append(
                {
                    "source": source,
                    "model": model,
                    "horizon": horizon,
                    "low_signal_ret": lo["future_ret_mean"],
                    "high_signal_ret": hi["future_ret_mean"],
                    "spread": hi["future_ret_mean"] - lo["future_ret_mean"],
                    "high_hit_rate": hi["hit_rate"],
                    "low_hit_rate": lo["hit_rate"],
                }
            )
        lines += [pd.DataFrame(rows).sort_values(["source", "model", "horizon"]).to_markdown(index=False), ""]
    if not option_edge.empty:
        lines += ["## Option Edge by Block", ""]
        opt = option_edge[
            (option_edge["source"] == "portal")
            & (option_edge[["buy_edge_gt_1", "sell_edge_gt_1"]].max(axis=1) > 0.02)
        ]
        lines += [opt.to_markdown(index=False), ""]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    horizons = list(dict.fromkeys(args.markout))

    price_sources = []
    for raw in args.price:
        source, path = parse_named_path(raw)
        frame = add_book_features(read_prices(path))
        frame["source"] = source
        price_sources.append(frame)
    market = pd.concat(price_sources, ignore_index=True) if price_sources else pd.DataFrame()
    market.to_csv(out_dir / "market_features.csv", index=False)

    product_frames = []
    block_frames = []
    worst_frames = []
    markout_frames = []
    fill_class_frames = []
    fill_block_frames = []
    inventory_frames = []
    inventory_summary_frames = []

    for raw in args.log:
        run, path = parse_named_path(raw)
        bundle = read_bundle(path)
        activities = add_book_features(parse_activities(bundle.get("activitiesLog", "")))
        fills = own_fills(bundle)
        product, block, worst = pnl_by_product(run, activities, args.block_size)
        product_frames.append(product)
        block_frames.append(block)
        worst_frames.append(worst)
        fill_marks = fill_markouts(run, fills, activities, horizons)
        by_class, by_block = summarize_fills(fill_marks, horizons)
        inv, inv_summary = inventory_path(run, fills)
        markout_frames.append(fill_marks)
        fill_class_frames.append(by_class)
        fill_block_frames.append(by_block)
        inventory_frames.append(inv)
        inventory_summary_frames.append(inv_summary)

    product_pnl = pd.concat([x for x in product_frames if not x.empty], ignore_index=True) if product_frames else pd.DataFrame()
    block_pnl = pd.concat([x for x in block_frames if not x.empty], ignore_index=True) if block_frames else pd.DataFrame()
    worst_steps = pd.concat([x for x in worst_frames if not x.empty], ignore_index=True) if worst_frames else pd.DataFrame()
    markouts = pd.concat([x for x in markout_frames if not x.empty], ignore_index=True) if markout_frames else pd.DataFrame()
    fill_class = pd.concat([x for x in fill_class_frames if not x.empty], ignore_index=True) if fill_class_frames else pd.DataFrame()
    fill_block = pd.concat([x for x in fill_block_frames if not x.empty], ignore_index=True) if fill_block_frames else pd.DataFrame()
    inventory = pd.concat([x for x in inventory_frames if not x.empty], ignore_index=True) if inventory_frames else pd.DataFrame()
    inventory_summary = pd.concat([x for x in inventory_summary_frames if not x.empty], ignore_index=True) if inventory_summary_frames else pd.DataFrame()

    hydro_alpha = add_hydro_alpha(market) if not market.empty else pd.DataFrame()
    vfe_alpha = add_vfe_alpha(market) if not market.empty else pd.DataFrame()
    alpha = pd.concat(
        [
            alpha_deciles(hydro_alpha, [100, 500, 1000, 5000, 10000], "hydro_dynamic"),
            alpha_deciles(vfe_alpha, [100, 500, 1000, 5000, 10000], "vfe_deep_implied"),
        ],
        ignore_index=True,
    )
    option_edge = option_edges(market) if not market.empty else pd.DataFrame()

    product_pnl.to_csv(out_dir / "product_pnl.csv", index=False)
    block_pnl.to_csv(out_dir / "block_pnl.csv", index=False)
    worst_steps.to_csv(out_dir / "worst_pnl_steps.csv", index=False)
    markouts.to_csv(out_dir / "fill_markouts.csv", index=False)
    fill_class.to_csv(out_dir / "fill_class_summary.csv", index=False)
    fill_block.to_csv(out_dir / "fill_block_summary.csv", index=False)
    inventory.to_csv(out_dir / "inventory_path.csv", index=False)
    inventory_summary.to_csv(out_dir / "inventory_summary.csv", index=False)
    hydro_alpha.to_csv(out_dir / "hydro_alpha_series.csv", index=False)
    vfe_alpha.to_csv(out_dir / "vfe_alpha_series.csv", index=False)
    alpha.to_csv(out_dir / "alpha_deciles.csv", index=False)
    option_edge.to_csv(out_dir / "option_edge_by_block.csv", index=False)

    save_plots(out_dir, block_pnl, inventory, markouts, alpha)
    write_summary(out_dir, product_pnl, block_pnl, fill_class, inventory_summary, alpha, option_edge, worst_steps)
    print(out_dir)


if __name__ == "__main__":
    main()
