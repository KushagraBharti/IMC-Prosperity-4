from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PRODUCT_ORDER = [
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Round 3 log diagnostics")
    parser.add_argument("--out", required=True, help="Output diagnostics directory")
    parser.add_argument(
        "--log",
        action="append",
        default=[],
        help="Named log in the form name=path. Can be repeated.",
    )
    parser.add_argument("--block-size", type=int, default=10_000)
    parser.add_argument("--markout", type=int, action="append", default=[100, 500, 1000, 5000, 10000])
    return parser.parse_args()


def read_bundle(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Some files may include non-JSON preamble in the future. Keep this permissive.
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(raw[start : end + 1])


def read_activities(bundle: dict) -> pd.DataFrame:
    activities = bundle.get("activitiesLog", "")
    if not activities:
        return pd.DataFrame()
    df = pd.read_csv(io.StringIO(activities), sep=";")
    numeric_cols = [c for c in df.columns if c not in {"product"}]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def read_trades(bundle: dict) -> pd.DataFrame:
    trades = bundle.get("tradeHistory", [])
    if not trades:
        return pd.DataFrame(columns=["timestamp", "symbol", "side", "price", "quantity", "signed_qty"])
    df = pd.DataFrame(trades)
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "symbol", "side", "price", "quantity", "signed_qty"])
    for col in ["timestamp", "price", "quantity"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    buy_mask = df.get("buyer", "").eq("SUBMISSION")
    sell_mask = df.get("seller", "").eq("SUBMISSION")
    df = df[buy_mask | sell_mask].copy()
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "symbol", "side", "price", "quantity", "signed_qty"])
    df["side"] = np.where(df["buyer"].eq("SUBMISSION"), "buy", "sell")
    df["signed_qty"] = np.where(df["side"].eq("buy"), df["quantity"], -df["quantity"])
    return df[["timestamp", "symbol", "side", "price", "quantity", "signed_qty"]]


def named_logs(log_args: Iterable[str]) -> list[tuple[str, Path]]:
    out = []
    for item in log_args:
        if "=" not in item:
            raise ValueError(f"--log must be name=path, got {item!r}")
        name, raw_path = item.split("=", 1)
        out.append((name, Path(raw_path)))
    return out


def product_pnl(run: str, activities: pd.DataFrame) -> pd.DataFrame:
    if activities.empty:
        return pd.DataFrame()
    rows = (
        activities.sort_values(["product", "timestamp"])
        .groupby("product", as_index=False)
        .tail(1)[["product", "profit_and_loss"]]
        .copy()
    )
    rows.insert(0, "run", run)
    rows = rows.rename(columns={"profit_and_loss": "final_pnl"})
    rows["product"] = pd.Categorical(rows["product"], PRODUCT_ORDER, ordered=True)
    return rows.sort_values(["run", "product"])


def timestamp_total_pnl(run: str, activities: pd.DataFrame) -> pd.DataFrame:
    if activities.empty:
        return pd.DataFrame()
    pivot = activities.pivot_table(
        index="timestamp",
        columns="product",
        values="profit_and_loss",
        aggfunc="last",
    ).sort_index()
    pivot = pivot.ffill().fillna(0.0)
    pivot["total_pnl"] = pivot.sum(axis=1)
    pivot.insert(0, "run", run)
    return pivot.reset_index()


def block_pnl(run: str, activities: pd.DataFrame, block_size: int) -> pd.DataFrame:
    if activities.empty:
        return pd.DataFrame()
    df = activities.sort_values(["product", "timestamp"]).copy()
    df["prev_pnl"] = df.groupby("product")["profit_and_loss"].shift(1).fillna(0.0)
    df["pnl_delta"] = df["profit_and_loss"] - df["prev_pnl"]
    df["block"] = (df["timestamp"] // block_size).astype(int)
    out = df.groupby(["block", "product"], as_index=False)["pnl_delta"].sum()
    out.insert(0, "run", run)
    out["product"] = pd.Categorical(out["product"], PRODUCT_ORDER, ordered=True)
    return out.sort_values(["run", "block", "product"])


def fill_summary(run: str, trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = (
        trades.groupby(["symbol", "side"], as_index=False)
        .agg(
            fills=("quantity", "count"),
            quantity=("quantity", "sum"),
            avg_price=("price", "mean"),
            first_ts=("timestamp", "min"),
            last_ts=("timestamp", "max"),
        )
        .rename(columns={"symbol": "product"})
    )
    rows.insert(0, "run", run)
    rows["product"] = pd.Categorical(rows["product"], PRODUCT_ORDER, ordered=True)
    return rows.sort_values(["run", "product", "side"])


def inventory_summary(run: str, trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    for product, product_trades in trades.sort_values("timestamp").groupby("symbol"):
        inv = product_trades["signed_qty"].cumsum()
        rows.append(
            {
                "run": run,
                "product": product,
                "min_inventory": float(inv.min()),
                "max_inventory": float(inv.max()),
                "end_inventory": float(inv.iloc[-1]),
                "turnover": float(product_trades["quantity"].sum()),
                "fill_count": int(len(product_trades)),
            }
        )
    out = pd.DataFrame(rows)
    out["product"] = pd.Categorical(out["product"], PRODUCT_ORDER, ordered=True)
    return out.sort_values(["run", "product"])


def inventory_path(run: str, trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    pieces = []
    for product, product_trades in trades.sort_values("timestamp").groupby("symbol"):
        path = product_trades[["timestamp", "signed_qty"]].copy()
        path["inventory"] = path["signed_qty"].cumsum()
        path["run"] = run
        path["product"] = product
        pieces.append(path[["run", "timestamp", "product", "inventory"]])
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def markouts(run: str, activities: pd.DataFrame, trades: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    if activities.empty or trades.empty:
        return pd.DataFrame()
    mid_lookup = {
        product: grp.set_index("timestamp")["mid_price"].sort_index()
        for product, grp in activities.groupby("product")
    }
    rows = []
    for trade in trades.itertuples(index=False):
        mids = mid_lookup.get(trade.symbol)
        if mids is None:
            continue
        try:
            mid_now = float(mids.loc[trade.timestamp])
        except KeyError:
            continue
        direction = 1.0 if trade.side == "buy" else -1.0
        row = {
            "run": run,
            "timestamp": int(trade.timestamp),
            "product": trade.symbol,
            "side": trade.side,
            "price": float(trade.price),
            "quantity": float(trade.quantity),
            "edge_to_mid": direction * (mid_now - float(trade.price)) * float(trade.quantity),
        }
        for horizon in horizons:
            target_ts = int(trade.timestamp) + horizon
            if target_ts in mids.index:
                future_mid = float(mids.loc[target_ts])
                row[f"markout_{horizon}"] = direction * (future_mid - float(trade.price)) * float(trade.quantity)
            else:
                row[f"markout_{horizon}"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def save_plots(out_dir: Path, product_pnls: pd.DataFrame, block_pnls: pd.DataFrame, inventories: pd.DataFrame) -> None:
    if not product_pnls.empty:
        pivot = product_pnls.pivot_table(index="product", columns="run", values="final_pnl", aggfunc="sum")
        pivot = pivot.reindex(PRODUCT_ORDER).dropna(how="all")
        ax = pivot.plot(kind="bar", figsize=(14, 7), title="Final PnL by Product")
        ax.set_ylabel("PnL")
        plt.tight_layout()
        plt.savefig(out_dir / "product_pnl.png", dpi=160)
        plt.close()

    if not block_pnls.empty:
        for run, grp in block_pnls.groupby("run"):
            pivot = grp.pivot_table(index="block", columns="product", values="pnl_delta", aggfunc="sum").fillna(0.0)
            pivot = pivot[[c for c in PRODUCT_ORDER if c in pivot.columns]]
            ax = pivot.plot(kind="bar", stacked=True, figsize=(14, 7), title=f"Block PnL: {run}")
            ax.set_ylabel("PnL delta")
            plt.tight_layout()
            safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(run))
            plt.savefig(out_dir / f"block_pnl_{safe}.png", dpi=160)
            plt.close()

    if not inventories.empty:
        for run, grp in inventories.groupby("run"):
            fig, ax = plt.subplots(figsize=(14, 7))
            for product, product_grp in grp.groupby("product"):
                if product_grp.empty:
                    continue
                ax.step(product_grp["timestamp"], product_grp["inventory"], where="post", label=str(product), alpha=0.8)
            ax.set_title(f"Inventory Path: {run}")
            ax.set_xlabel("Timestamp")
            ax.set_ylabel("Inventory")
            ax.legend(loc="best", fontsize=8)
            plt.tight_layout()
            safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(run))
            plt.savefig(out_dir / f"inventory_{safe}.png", dpi=160)
            plt.close()


def write_summary_md(
    out_dir: Path,
    product_pnls: pd.DataFrame,
    fills: pd.DataFrame,
    inventories: pd.DataFrame,
    markout_summary: pd.DataFrame,
) -> None:
    lines = ["# Round 3 Diagnostics", ""]
    if not product_pnls.empty:
        total = product_pnls.groupby("run")["final_pnl"].sum().sort_values(ascending=False)
        lines += ["## Total PnL", "", total.to_markdown(), ""]
        lines += ["## Product PnL", "", product_pnls.pivot_table(index="product", columns="run", values="final_pnl", aggfunc="sum").to_markdown(), ""]
    if not inventories.empty:
        lines += ["## Inventory Summary", "", inventories.to_markdown(index=False), ""]
    if not fills.empty:
        lines += ["## Fill Summary", "", fills.to_markdown(index=False), ""]
    if not markout_summary.empty:
        lines += ["## Markout Summary", "", markout_summary.to_markdown(index=False), ""]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    product_pnls = []
    totals = []
    blocks = []
    fills = []
    inventories = []
    inventory_paths = []
    all_markouts = []

    for run, path in named_logs(args.log):
        bundle = read_bundle(path)
        activities = read_activities(bundle)
        trades = read_trades(bundle)

        product_pnls.append(product_pnl(run, activities))
        totals.append(timestamp_total_pnl(run, activities))
        blocks.append(block_pnl(run, activities, args.block_size))
        fills.append(fill_summary(run, trades))
        inventories.append(inventory_summary(run, trades))
        inventory_paths.append(inventory_path(run, trades))
        all_markouts.append(markouts(run, activities, trades, args.markout))

    product_pnls_df = pd.concat([x for x in product_pnls if not x.empty], ignore_index=True)
    totals_df = pd.concat([x for x in totals if not x.empty], ignore_index=True)
    blocks_df = pd.concat([x for x in blocks if not x.empty], ignore_index=True)
    fills_df = pd.concat([x for x in fills if not x.empty], ignore_index=True) if fills else pd.DataFrame()
    inventories_df = pd.concat([x for x in inventories if not x.empty], ignore_index=True) if inventories else pd.DataFrame()
    inventory_paths_df = pd.concat([x for x in inventory_paths if not x.empty], ignore_index=True) if inventory_paths else pd.DataFrame()
    markouts_df = pd.concat([x for x in all_markouts if not x.empty], ignore_index=True) if all_markouts else pd.DataFrame()

    markout_cols = [c for c in markouts_df.columns if c.startswith("markout_")]
    if not markouts_df.empty:
        markout_summary = (
            markouts_df.groupby(["run", "product", "side"], as_index=False)
            .agg(
                fills=("quantity", "count"),
                quantity=("quantity", "sum"),
                edge_to_mid=("edge_to_mid", "sum"),
                **{col: (col, "sum") for col in markout_cols},
            )
            .sort_values(["run", "product", "side"])
        )
    else:
        markout_summary = pd.DataFrame()

    product_pnls_df.to_csv(out_dir / "product_pnl.csv", index=False)
    totals_df.to_csv(out_dir / "timestamp_total_pnl.csv", index=False)
    blocks_df.to_csv(out_dir / "block_pnl.csv", index=False)
    fills_df.to_csv(out_dir / "fill_summary.csv", index=False)
    inventories_df.to_csv(out_dir / "inventory_summary.csv", index=False)
    inventory_paths_df.to_csv(out_dir / "inventory_path.csv", index=False)
    markouts_df.to_csv(out_dir / "markouts.csv", index=False)
    markout_summary.to_csv(out_dir / "markout_summary.csv", index=False)

    save_plots(out_dir, product_pnls_df, blocks_df, inventory_paths_df)
    write_summary_md(out_dir, product_pnls_df, fills_df, inventories_df, markout_summary)
    print(out_dir)


if __name__ == "__main__":
    main()
