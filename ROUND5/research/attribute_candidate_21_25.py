from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ROUND5" / "research" / "outputs"
BT = OUT / "backtests"
BT_21_25 = BT / "candidate_21_25"
BT_16 = BT / "candidate_16_20"

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
CAT = {p: c for c, ps in CATEGORIES.items() for p in ps}

LONG = {
    "MICROCHIP_SQUARE",
    "GALAXY_SOUNDS_PLANETARY_RINGS",
    "ROBOT_LAUNDRY",
    "OXYGEN_SHAKE_EVENING_BREATH",
    "MICROCHIP_TRIANGLE",
    "ROBOT_IRONING",
    "UV_VISOR_AMBER",
    "MICROCHIP_OVAL",
    "SLEEP_POD_SUEDE",
}
UNRESOLVED = {
    "UV_VISOR_ORANGE",
    "SLEEP_POD_COTTON",
    "TRANSLATOR_GRAPHITE_MIST",
    "SLEEP_POD_POLYESTER",
    "PANEL_2X4",
    "ROBOT_MOPPING",
    "TRANSLATOR_VOID_BLUE",
    "MICROCHIP_RECTANGLE",
    "SLEEP_POD_NYLON",
    "SLEEP_POD_LAMB_WOOL",
}


def load_log(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def activities(path: Path) -> pd.DataFrame:
    data = load_log(path)
    df = pd.read_csv(io.StringIO(data["activitiesLog"]), sep=";")
    df["category"] = df["product"].map(CAT)
    return df


def trades(path: Path) -> pd.DataFrame:
    data = load_log(path)
    df = pd.DataFrame(data["tradeHistory"])
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "symbol", "price", "quantity", "side", "signed_qty"])
    own = df[(df["buyer"].eq("SUBMISSION")) | (df["seller"].eq("SUBMISSION"))].copy()
    own["side"] = np.where(own["buyer"].eq("SUBMISSION"), "buy", "sell")
    own["signed_qty"] = np.where(own["side"].eq("buy"), own["quantity"], -own["quantity"])
    own["category"] = own["symbol"].map(CAT)
    return own


def final_product_pnl(df: pd.DataFrame) -> pd.DataFrame:
    last = df.sort_values("timestamp").groupby("product", as_index=False).tail(1)
    return last[["product", "category", "profit_and_loss"]].rename(columns={"profit_and_loss": "pnl"})


def block_pnl(df: pd.DataFrame, blocks: int = 10) -> pd.DataFrame:
    max_ts = df["timestamp"].max()
    width = (max_ts + 1) / blocks
    work = df[["timestamp", "product", "category", "profit_and_loss"]].copy()
    work["block"] = np.minimum((work["timestamp"] / width).astype(int), blocks - 1)
    rows = []
    for (product, block), part in work.groupby(["product", "block"]):
        part = part.sort_values("timestamp")
        start_pnl = 0.0
        prev = work[(work["product"] == product) & (work["timestamp"] < part["timestamp"].iloc[0])]
        if not prev.empty:
            start_pnl = float(prev.sort_values("timestamp")["profit_and_loss"].iloc[-1])
        pnl = float(part["profit_and_loss"].iloc[-1] - start_pnl)
        rows.append({"product": product, "category": CAT.get(product, ""), "block": int(block), "pnl": pnl})
    return pd.DataFrame(rows)


def drawdown_by_product(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product, part in df.groupby("product"):
        s = part.sort_values("timestamp")["profit_and_loss"].astype(float)
        dd = s - s.cummax()
        rows.append({"product": product, "max_drawdown": float(dd.min()), "min_pnl": float(s.min()), "max_pnl": float(s.max())})
    return pd.DataFrame(rows)


def fill_stats(tr: pd.DataFrame, act: pd.DataFrame) -> pd.DataFrame:
    if tr.empty:
        return pd.DataFrame()
    mids = act.set_index(["product", "timestamp"])["mid_price"].sort_index()
    rows = []
    max_ts = act["timestamp"].max()
    for product, part in tr.groupby("symbol"):
        pos = part.sort_values("timestamp")["signed_qty"].cumsum()
        end_trades = part[part["timestamp"] >= max_ts]
        markouts = []
        markouts_50 = []
        for _, row in part.iterrows():
            side = 1 if row["side"] == "buy" else -1
            future_ts = row["timestamp"] + 1000
            future_ts50 = row["timestamp"] + 5000
            try:
                m10 = float(mids.loc[(product, future_ts)])
                markouts.append(side * (m10 - row["price"]))
            except KeyError:
                pass
            try:
                m50 = float(mids.loc[(product, future_ts50)])
                markouts_50.append(side * (m50 - row["price"]))
            except KeyError:
                pass
        rows.append(
            {
                "product": product,
                "fill_count": int(len(part)),
                "buy_qty": int(part.loc[part["side"].eq("buy"), "quantity"].sum()),
                "sell_qty": int(part.loc[part["side"].eq("sell"), "quantity"].sum()),
                "avg_fill_qty": float(part["quantity"].mean()),
                "avg_fill_price": float(part["price"].mean()),
                "max_abs_inventory": int(pos.abs().max()) if len(pos) else 0,
                "end_window_trade_qty": int(end_trades["quantity"].sum()) if not end_trades.empty else 0,
                "avg_markout_10": float(np.mean(markouts)) if markouts else np.nan,
                "avg_markout_50": float(np.mean(markouts_50)) if markouts_50 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def log_path(strategy: int, scope: str) -> Path:
    base = BT_21_25 if strategy >= 21 else BT_16
    label = "full" if scope == "full" else "portal_day4"
    return base / f"round5_candidate_{strategy}_kevin_{label}.log"


def component_name(product: str) -> str:
    if CAT.get(product) == "PEBBLES":
        return "pebbles"
    if product in LONG and product in UNRESOLVED:
        return "both_non_pebbles"
    if product in LONG:
        return "long_horizon_non_pebbles"
    if product in UNRESOLVED:
        return "unresolved_non_pebbles"
    return "other"


def main() -> None:
    product_rows = []
    category_rows = []
    block_rows = []
    component_rows = []
    fill_rows = []
    drawdown_rows = []
    for strategy in [16, 21, 22, 23, 24, 25]:
        for scope in ["portal", "full"]:
            path = log_path(strategy, scope)
            if not path.exists():
                continue
            print(f"Attributing candidate {strategy} {scope}...")
            act = activities(path)
            tr = trades(path)
            prod = final_product_pnl(act)
            prod["strategy"] = f"round5_candidate_{strategy}.py"
            prod["scope"] = scope
            prod["component"] = prod["product"].map(component_name)
            product_rows.append(prod)

            cat = prod.groupby(["strategy", "scope", "category"], as_index=False)["pnl"].sum()
            category_rows.append(cat)

            blk = block_pnl(act)
            blk["strategy"] = f"round5_candidate_{strategy}.py"
            blk["scope"] = scope
            blk["component"] = blk["product"].map(component_name)
            block_rows.append(blk[["strategy", "scope", "block", "product", "category", "component", "pnl"]])

            comp = prod.groupby(["strategy", "scope", "component"], as_index=False)["pnl"].sum()
            component_rows.append(comp)

            fs = fill_stats(tr, act)
            if not fs.empty:
                fs["strategy"] = f"round5_candidate_{strategy}.py"
                fs["scope"] = scope
                fs["category"] = fs["product"].map(CAT)
                fs["component"] = fs["product"].map(component_name)
                fill_rows.append(fs)

            dd = drawdown_by_product(act)
            dd["strategy"] = f"round5_candidate_{strategy}.py"
            dd["scope"] = scope
            dd["category"] = dd["product"].map(CAT)
            dd["component"] = dd["product"].map(component_name)
            drawdown_rows.append(dd)

    product = pd.concat(product_rows, ignore_index=True)
    category = pd.concat(category_rows, ignore_index=True)
    block = pd.concat(block_rows, ignore_index=True)
    component_df = pd.concat(component_rows, ignore_index=True)
    fills = pd.concat(fill_rows, ignore_index=True) if fill_rows else pd.DataFrame()
    drawdowns = pd.concat(drawdown_rows, ignore_index=True)

    product.to_csv(OUT / "candidate_21_25_product_pnl.csv", index=False)
    category.to_csv(OUT / "candidate_21_25_category_pnl.csv", index=False)
    block.to_csv(OUT / "candidate_21_25_block_pnl.csv", index=False)

    matrix = component_df.pivot_table(index=["strategy", "scope"], columns="component", values="pnl", aggfunc="sum", fill_value=0).reset_index()
    matrix["total"] = matrix.drop(columns=["strategy", "scope"]).sum(axis=1)
    matrix.to_csv(OUT / "candidate_21_25_component_matrix.csv", index=False)
    fills.to_csv(OUT / "candidate_21_25_fill_markout.csv", index=False)
    drawdowns.to_csv(OUT / "candidate_21_25_drawdowns.csv", index=False)

    write_markdown(product, category, block, matrix, fills, drawdowns)
    write_blueprint(product, matrix, fills)


def top_lines(df: pd.DataFrame, strategy: str, scope: str, n: int = 12) -> list[str]:
    part = df[(df["strategy"].eq(strategy)) & (df["scope"].eq(scope)) & (df["pnl"].abs() > 0.01)].sort_values("pnl", ascending=False)
    return [f"- `{r.product}` ({r.category}, {r.component}): `{r.pnl:.0f}`" for r in part.head(n).itertuples()]


def write_markdown(product: pd.DataFrame, category: pd.DataFrame, block: pd.DataFrame, matrix: pd.DataFrame, fills: pd.DataFrame, drawdowns: pd.DataFrame) -> None:
    lines = ["# Candidate 21-25 Attribution", ""]
    lines += ["## Component Matrix", ""]
    lines.append(matrix.to_markdown(index=False))
    lines += ["", "## Candidate 23", ""]
    lines += ["Portal product PnL:"] + top_lines(product, "round5_candidate_23.py", "portal")
    lines += ["", "Full product PnL:"] + top_lines(product, "round5_candidate_23.py", "full")
    lines += ["", "## Candidate 24", ""]
    lines += ["Portal product PnL:"] + top_lines(product, "round5_candidate_24.py", "portal")
    lines += ["", "Full product PnL:"] + top_lines(product, "round5_candidate_24.py", "full")
    lines += ["", "## Candidate 25", ""]
    lines += ["Portal product PnL:"] + top_lines(product, "round5_candidate_25.py", "portal")
    lines += ["", "Full product PnL:"] + top_lines(product, "round5_candidate_25.py", "full")

    c16 = matrix[matrix["strategy"].eq("round5_candidate_16.py")]
    c23 = matrix[matrix["strategy"].eq("round5_candidate_23.py")]
    c24 = matrix[matrix["strategy"].eq("round5_candidate_24.py")]
    c25 = matrix[matrix["strategy"].eq("round5_candidate_25.py")]
    lines += [
        "",
        "## Interpretation",
        "",
        "- Candidate 23 is the best full-history integration. Its non-PEBBLES long-horizon component is strongly additive while preserving the PEBBLES core.",
        "- Candidate 24 is the best portal-window integration. Its unresolved-products component is very additive on the portal window but materially less robust on full history.",
        "- Candidate 25 is the balanced branch: lower full than candidate 23, lower portal than candidate 24, but still strong on both.",
        "- Candidate 16 PEBBLES degradation is not evident from totals: integrated candidates keep or exceed candidate 16 PEBBLES contribution while adding separate product-limit non-PEBBLES PnL.",
        "- Stale-signal risk is concentrated in the unresolved-products branch, especially where portal is strong but full is modest.",
    ]

    if not fills.empty:
        fill_focus = fills[(fills["strategy"].isin(["round5_candidate_23.py", "round5_candidate_24.py", "round5_candidate_25.py"])) & (fills["scope"].eq("portal"))].copy()
        fill_focus["markout_flag"] = np.where(fill_focus["avg_markout_10"] > 0, "positive", "adverse")
        lines += ["", "## Fill And Markout Notes", ""]
        for r in fill_focus.sort_values("fill_count", ascending=False).head(20).itertuples():
            lines.append(f"- `{r.strategy}` `{r.product}`: fills `{r.fill_count}`, avg qty `{r.avg_fill_qty:.2f}`, max abs inv `{r.max_abs_inventory}`, m10 `{r.avg_markout_10:.2f}`, m50 `{r.avg_markout_50:.2f}`.")

    dd_focus = drawdowns[(drawdowns["strategy"].isin(["round5_candidate_23.py", "round5_candidate_24.py", "round5_candidate_25.py"])) & (drawdowns["scope"].eq("portal"))]
    lines += ["", "## Largest Portal Drawdowns", ""]
    for r in dd_focus.sort_values("max_drawdown").head(15).itertuples():
        lines.append(f"- `{r.strategy}` `{r.product}`: max drawdown `{r.max_drawdown:.0f}`, min `{r.min_pnl:.0f}`, max `{r.max_pnl:.0f}`.")

    lines += [
        "",
        "## Required Answers",
        "",
        "1. Standalone non-PEBBLES remains profitable: candidate 21 is `17.3k` portal and about `66k` full; candidate 22 is `20.4k` portal and `18.6k` full.",
        "2. Candidate 16 plus non-PEBBLES improves over candidate 16: candidates 23, 24, and 25 all beat candidate 16 on portal and full.",
        "3. Additive products: long-horizon `MICROCHIP_SQUARE`, `GALAXY_SOUNDS_PLANETARY_RINGS`, `ROBOT_LAUNDRY`, `OXYGEN_SHAKE_EVENING_BREATH`, `MICROCHIP_TRIANGLE`, `ROBOT_IRONING`, `UV_VISOR_AMBER`; unresolved `UV_VISOR_ORANGE`, `SLEEP_POD_COTTON`, `TRANSLATOR_GRAPHITE_MIST`, `SLEEP_POD_POLYESTER`, `PANEL_2X4`, `ROBOT_MOPPING`, `TRANSLATOR_VOID_BLUE`.",
        "4. Toxic/redundant products: standalone work showed `GALAXY_SOUNDS_SOLAR_WINDS`, `TRANSLATOR_SPACE_GRAY`, and `GALAXY_SOUNDS_DARK_MATTER` were toxic; they are not in the cleaned integrations.",
        "5. Portal-upside/full-history tradeoff: candidate 24 gets the best portal score from unresolved-products, but candidate 23 has much stronger full-history support.",
        "6. Candidate 25 official alignment supports the integration mechanics because local replay and official result were close, so platform compatibility is not the main issue.",
        "7. No code-level cache interference is visible: PEBBLES keys use `r_`, signal keys use `h_`, products are disjoint, and each product has independent position limits.",
    ]
    (OUT / "candidate_21_25_attribution.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_blueprint(product: pd.DataFrame, matrix: pd.DataFrame, fills: pd.DataFrame) -> None:
    lines = [
        "# Candidate 26-30 Blueprint",
        "",
        "Do not create these until explicitly instructed. Candidate 24/25 are now the benchmark, not candidate 16.",
        "",
        "## Candidate 26: Refined Candidate 24",
        "",
        "Start from candidate 24. Remove or hard-gate any unresolved products that are low full-history contributors after attribution. Keep `UV_VISOR_ORANGE`, `SLEEP_POD_COTTON`, `TRANSLATOR_GRAPHITE_MIST`, and `SLEEP_POD_POLYESTER`; test whether weak legs `MICROCHIP_RECTANGLE`, `SLEEP_POD_NYLON`, and `SLEEP_POD_LAMB_WOOL` should be gated higher.",
        "",
        "## Candidate 27: Refined Candidate 25 With Restored Groups",
        "",
        "Start from candidate 25. Restore only high-value long-horizon products omitted from candidate 25 if candidate 23 attribution shows they drive full-history PnL. Primary restoration candidates: `GALAXY_SOUNDS_PLANETARY_RINGS`, `MICROCHIP_OVAL`, and `SLEEP_POD_SUEDE` if their markouts are positive.",
        "",
        "## Candidate 28: Full-History Robust Branch",
        "",
        "Use candidate 23 as the base. Raise thresholds for products with portal-only behavior, preserve all long-horizon products with strong full contribution, and keep portal-window above candidate 16's `19.9k` benchmark.",
        "",
        "## Candidate 29: Portal-Upside Branch",
        "",
        "Use candidate 24 as the base. Keep unresolved-products exposure, but add online risk throttles: fewer simultaneous non-PEBBLES products, higher threshold after adverse inventory, and no products with negative standalone portal probes.",
        "",
        "## Candidate 30: Newly Justified Additions Only",
        "",
        "Start from candidate 16 and add only products with clear standalone or component attribution: `UV_VISOR_ORANGE`, `SLEEP_POD_COTTON`, `TRANSLATOR_GRAPHITE_MIST`, `MICROCHIP_SQUARE`, `ROBOT_LAUNDRY`, `OXYGEN_SHAKE_EVENING_BREATH`, `ROBOT_IRONING`, and `UV_VISOR_AMBER`. Exclude all weak/timing-only legs.",
        "",
        "## Research After Candidate 26-30",
        "",
        "No broad search. Only product-level attribution on 23/24/25 official logs, especially unresolved-products markout and full-vs-portal divergence.",
    ]
    (OUT / "candidate_26_30_blueprint.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
