from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / "ROUND5"
OUT = ROUND / "research" / "outputs"
PROBE_DIR = ROUND / "research" / "probes" / "exhaustive"
BT_DIR = OUT / "backtests" / "exhaustive_remaining_edges"
PORTAL_ROOT = OUT / "official_portal_windows" / "round5_candidate_1"
PORTAL_PRICES = PORTAL_ROOT / "round5"

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
PRODUCT_TO_CATEGORY = {p: c for c, ps in CATEGORIES.items() for p in ps}

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
    "PANEL": {"PANEL_1X2": 2.0, "PANEL_2X2": 4.0, "PANEL_1X4": 4.2, "PANEL_2X4": 8.0, "PANEL_4X4": 16.0},
    "UV_VISOR": {"UV_VISOR_RED": 1.0, "UV_VISOR_ORANGE": 2.0, "UV_VISOR_AMBER": 2.5, "UV_VISOR_YELLOW": 3.0, "UV_VISOR_MAGENTA": 5.0},
}
HORIZONS = [1, 2, 5, 10, 25, 50, 100, 200, 500]


@dataclass
class ProbeConfig:
    product: str
    mode: str
    lookback: int
    threshold: float


def read_prices(root: Path) -> pd.DataFrame:
    frames = []
    for day in [2, 3, 4]:
        path = root / f"prices_round_5_day_{day}.csv"
        if path.exists():
            frames.append(pd.read_csv(path, sep=";"))
    if not frames:
        raise FileNotFoundError(f"No Round 5 price files under {root}")
    df = pd.concat(frames, ignore_index=True)
    df["category"] = df["product"].map(PRODUCT_TO_CATEGORY)
    df = df[df["category"].notna()].copy()
    df["spread"] = df["ask_price_1"] - df["bid_price_1"]
    df["bidv"] = df["bid_volume_1"].fillna(0)
    df["askv"] = df["ask_volume_1"].fillna(0).abs()
    depth = df["bidv"] + df["askv"]
    df["imbalance"] = np.where(depth > 0, (df["bidv"] - df["askv"]) / depth, 0.0)
    df["microprice"] = np.where(depth > 0, (df["ask_price_1"] * df["bidv"] + df["bid_price_1"] * df["askv"]) / depth, df["mid_price"])
    df["microprice_edge"] = df["microprice"] - df["mid_price"]
    df["depth_imbalance"] = df["imbalance"] * np.log1p(depth)
    return df.sort_values(["day", "timestamp", "product"]).reset_index(drop=True)


def mid_pivot(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index=["day", "timestamp"], columns="product", values="mid_price").sort_index()


def safe_corr(a: pd.Series, b: pd.Series) -> float:
    tmp = pd.concat([a, b], axis=1).dropna()
    if len(tmp) < 50:
        return 0.0
    if tmp.iloc[:, 0].std() == 0 or tmp.iloc[:, 1].std() == 0:
        return 0.0
    return float(tmp.iloc[:, 0].corr(tmp.iloc[:, 1]))


def block_id(index: pd.MultiIndex, blocks: int = 10) -> pd.Series:
    ts = index.get_level_values("timestamp").astype(float)
    day = index.get_level_values("day")
    out = np.zeros(len(index), dtype=int)
    for d in sorted(set(day)):
        mask = np.asarray(day == d)
        vals = ts[mask]
        if len(vals) == 0:
            continue
        width = (vals.max() - vals.min() + 1.0) / blocks
        out[mask] = np.minimum(((vals - vals.min()) / max(width, 1.0)).astype(int), blocks - 1)
    return pd.Series(out, index=index)


def signal_proxy(sig: pd.Series, fwd: pd.Series, spread: pd.Series, pct: float, cost_mult: float) -> tuple[float, float, int, int, int]:
    tmp = pd.concat([sig, fwd, spread], axis=1).dropna()
    if tmp.empty:
        return 0.0, 0.0, 0, 0, 0
    tmp.columns = ["sig", "fwd", "spread"]
    cutoff = tmp["sig"].abs().quantile(pct)
    take = tmp[tmp["sig"].abs() >= max(cutoff, 1e-9)].copy()
    if take.empty:
        return 0.0, 0.0, 0, 0, 0
    pnl = np.sign(take["sig"]) * take["fwd"] * 10.0 - cost_mult * take["spread"].clip(lower=0)
    take["pnl"] = pnl
    day_scores = take.groupby(level="day")["pnl"].sum()
    bidir = int((take["sig"] > 0).any() and (take["sig"] < 0).any())
    return float(pnl.sum()), safe_corr(tmp["sig"], tmp["fwd"]), int((day_scores > 0).sum()), int(len(day_scores)), bidir


def rolling_std(series: pd.Series, window: int) -> pd.Series:
    return series.groupby(level="day").diff().groupby(level="day").rolling(window, min_periods=max(5, window // 4)).std().reset_index(level=0, drop=True).reindex(series.index)


def semantic_fair(mid: pd.DataFrame, category: str, product: str) -> pd.Series:
    products = [p for p in CATEGORIES[category] if p in mid.columns and p != product]
    if not products:
        return mid[product] * np.nan
    xmap = SEMANTIC_X.get(category)
    if not xmap or len(products) < 2:
        return mid[products].mean(axis=1)
    xs = np.array([xmap[p] for p in products], dtype=float)
    x0 = float(xmap[product])
    vals = mid[products]
    mask = np.isfinite(vals.values)
    count = mask.sum(axis=1).astype(float)
    y = np.where(mask, vals.values.astype(float), 0.0)
    x = np.where(mask, xs.reshape(1, -1), 0.0)
    valid = count >= 2
    mx = np.divide(x.sum(axis=1), count, out=np.full(len(vals), np.nan), where=count > 0)
    my = np.divide(y.sum(axis=1), count, out=np.full(len(vals), np.nan), where=count > 0)
    xc = np.where(mask, xs.reshape(1, -1) - mx.reshape(-1, 1), 0.0)
    yc = np.where(mask, vals.values.astype(float) - my.reshape(-1, 1), 0.0)
    den = (xc * xc).sum(axis=1)
    slope = np.divide((xc * yc).sum(axis=1), den, out=np.zeros(len(vals)), where=den > 1e-9)
    fair = my + slope * (x0 - mx)
    fair[~valid] = np.nan
    return pd.Series(fair, index=vals.index)


def pca_fair(mid: pd.DataFrame, category: str, product: str) -> pd.Series:
    products = [p for p in CATEGORIES[category] if p in mid.columns]
    if len(products) < 3 or product not in products:
        return mid[product] * np.nan
    # Research-only factor proxy. The earlier broad research already wrote full
    # PCA tables; here we need fast all-product coverage, so use the category
    # common factor as the online-safe one-factor residual proxy.
    return mid[[p for p in products if p != product]].mean(axis=1)


def candidate_signals(df: pd.DataFrame, mid: pd.DataFrame, product: str) -> list[tuple[str, str, int, pd.Series, pd.Series]]:
    category = PRODUCT_TO_CATEGORY[product]
    s = mid[product]
    rows = df[df["product"] == product].set_index(["day", "timestamp"]).reindex(mid.index)
    candidates: list[tuple[str, str, int, pd.Series, pd.Series]] = []
    for h in HORIZONS:
        past = s.groupby(level="day").diff(h)
        fwd = s.groupby(level="day").shift(-h) - s
        vol = rolling_std(s, min(max(h, 10), 200)).replace(0, np.nan)
        minp = 1 if h == 1 else max(2, min(h, 10))
        roll_mean = s.groupby(level="day").rolling(h, min_periods=minp).mean().reset_index(level=0, drop=True).reindex(s.index)
        roll_hi = s.groupby(level="day").rolling(h, min_periods=minp).max().reset_index(level=0, drop=True).reindex(s.index)
        roll_lo = s.groupby(level="day").rolling(h, min_periods=minp).min().reset_index(level=0, drop=True).reindex(s.index)
        candidates += [
            ("momentum", "statistical/time-series", h, past, fwd),
            ("reversal", "statistical/time-series", h, -past, fwd),
            ("vol_norm_momentum", "statistical/time-series", h, past / vol, fwd),
            ("vol_norm_reversal", "statistical/time-series", h, -past / vol, fwd),
            ("rolling_mean_reversion", "statistical/time-series", h, -(s - roll_mean), fwd),
            ("breakout_high", "breakout", h, s - roll_hi.shift(1), fwd),
            ("breakout_low_reversal", "breakout", h, roll_lo.shift(1) - s, fwd),
        ]
    fwd1 = s.groupby(level="day").shift(-1) - s
    products = [p for p in CATEGORIES[category] if p in mid.columns]
    cat_mean = mid[[p for p in products if p != product]].mean(axis=1)
    cat_median = mid[[p for p in products if p != product]].median(axis=1)
    fair = semantic_fair(mid, category, product)
    pca = pca_fair(mid, category, product)
    candidates += [
        ("category_mean_reversion", "category/basket", 1, -(s - cat_mean), fwd1),
        ("category_median_reversion", "category/basket", 1, -(s - cat_median), fwd1),
        ("semantic_curve_residual", "semantic/name-curve", 1, -(s - fair), fwd1),
        ("basket_residual", "category/basket", 1, -(s - cat_mean), fwd1),
        ("pca_factor_residual", "factor/research-only", 1, -(s - pca), fwd1),
        ("order_book_imbalance", "microstructure", 1, rows["imbalance"], fwd1),
        ("microprice_edge", "microstructure", 1, rows["microprice_edge"], fwd1),
        ("spread_depth_imbalance", "microstructure", 1, rows["depth_imbalance"], fwd1),
    ]
    for leader in products:
        if leader == product:
            continue
        leader_ret = mid[leader].groupby(level="day").diff(1)
        candidates.append((f"lead_lag_from:{leader}", "lead-lag", 1, leader_ret, fwd1))
    return candidates


def oracle(df: pd.DataFrame) -> pd.DataFrame:
    mid = mid_pivot(df)
    rows = []
    for product in mid.columns:
        s = mid[product]
        spread = df[df["product"] == product].set_index(["day", "timestamp"])["spread"].reindex(s.index)
        for h in [1, 10, 50, 100]:
            fwd = s.groupby(level="day").shift(-h) - s
            gross = 10.0 * fwd.abs().sum(skipna=True)
            spread_adj = 10.0 * np.maximum(fwd.abs() - spread / 2.0, 0).sum(skipna=True)
            rows.append({"product": product, "horizon": h, "gross_oracle": float(gross), "spread_adjusted_oracle": float(spread_adj)})
    return pd.DataFrame(rows)


def scan_scope(df: pd.DataFrame, scope: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    mid = mid_pivot(df)
    rows = []
    best_rows = []
    for product in PRODUCT_TO_CATEGORY:
        if product not in mid.columns:
            continue
        print(f"{scope}: scanning {product}", flush=True)
        spread = df[df["product"] == product].set_index(["day", "timestamp"])["spread"].reindex(mid.index)
        for family, model_type, horizon, sig, fwd in candidate_signals(df, mid, product):
            passive, corr, pos_days, day_count, bidir = signal_proxy(sig, fwd, spread, pct=0.82, cost_mult=0.25)
            taker, taker_corr, taker_days, _, _ = signal_proxy(sig, fwd, spread, pct=0.88, cost_mult=1.05)
            blocks = block_id(sig.index)
            tmp = pd.concat([sig, fwd, spread, blocks.rename("block")], axis=1).dropna()
            tmp.columns = ["sig", "fwd", "spread", "block"]
            if tmp.empty:
                pos_blocks = 0
                total_blocks = 0
            else:
                tmp["pnl"] = np.sign(tmp["sig"]) * tmp["fwd"] * 10.0 - 0.25 * tmp["spread"]
                strength = tmp["sig"].abs()
                tmp = tmp[strength >= max(strength.quantile(0.82), 1e-9)]
                by_block = tmp.groupby(["day", "block"])["pnl"].sum()
                pos_blocks = int((by_block > 0).sum())
                total_blocks = int(len(by_block))
            rows.append(
                {
                    "scope": scope,
                    "product": product,
                    "category": PRODUCT_TO_CATEGORY[product],
                    "signal_family": family,
                    "model_type": model_type,
                    "horizon": horizon,
                    "passive_proxy_pnl": passive,
                    "taker_proxy_pnl": taker,
                    "signal_corr": corr if abs(corr) >= abs(taker_corr) else taker_corr,
                    "positive_days": pos_days if passive >= taker else taker_days,
                    "day_count": day_count,
                    "positive_blocks": pos_blocks,
                    "block_count": total_blocks,
                    "bidirectional": bidir,
                }
            )
        product_rows = [r for r in rows if r["scope"] == scope and r["product"] == product]
        best = max(product_rows, key=lambda r: max(r["passive_proxy_pnl"], r["taker_proxy_pnl"]))
        best_rows.append(best | {"best_execution": "passive" if best["passive_proxy_pnl"] >= best["taker_proxy_pnl"] else "taker"})
    return pd.DataFrame(rows), pd.DataFrame(best_rows)


def load_candidate_product_pnl() -> pd.DataFrame:
    path = OUT / "candidate_21_25_product_pnl.csv"
    if not path.exists():
        return pd.DataFrame(columns=["product", "scope", "pnl", "strategy"])
    return pd.read_csv(path)


def load_existing_probe_scores() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for name in [
        "non_pebbles_probe_portal_scores.csv",
        "non_pebbles_promising_full_scores.csv",
        "unresolved_edge_probe_portal_scores.csv",
        "unresolved_promising_full_scores.csv",
        "unresolved_individual_probe_portal_scores.csv",
        "unresolved_individual_alt_probe_portal_scores.csv",
    ]:
        path = OUT / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            rows.append({"probe": row.iloc[0], "source_file": name, **{str(k): row[k] for k in df.columns[1:]}})
    return pd.DataFrame(rows)


def load_manual_product_status() -> dict[str, str]:
    path = OUT / "unresolved_products_edge_summary.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "Product" not in df.columns or "Edge Status" not in df.columns:
        return {}
    return {str(r["Product"]): str(r["Edge Status"]) for _, r in df.iterrows()}


def parse_profit(log_path: Path, stdout: str) -> float | None:
    texts = [stdout]
    if log_path.exists():
        texts.append(log_path.read_text(encoding="utf-8", errors="ignore")[-10000:])
    for text in texts:
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    return None


def probe_template(configs: list[ProbeConfig]) -> str:
    cfg = {c.product: (c.mode, c.lookback, c.threshold) for c in configs}
    return f'''from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List

try:
    from datamodel import Order, TradingState
except ImportError:
    @dataclass
    class Order:
        symbol: str
        price: int
        quantity: int

    @dataclass
    class TradingState:
        order_depths: Dict[str, object]
        position: Dict[str, int] = field(default_factory=dict)
        traderData: str = ""


class Trader:
    LIMIT = 10
    CONFIG = {cfg!r}

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {{}}
        scored = []
        for product, (mode, lookback, threshold) in self.CONFIG.items():
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"], max(620, lookback + 160))
            if len(hist) <= lookback + 2:
                continue
            signal = (hist[-1] - hist[-1 - lookback]) / max(self.vol(hist[-160:]), 1.0)
            if mode == "reversal":
                signal = -signal
            signal += 0.08 * book["imb"]
            if abs(signal) >= threshold:
                scored.append((abs(signal) / threshold, product, book, signal, threshold))
        scored.sort(reverse=True, key=lambda x: x[0])
        for _, product, book, signal, threshold in scored[:10]:
            result[product] = self.trade(product, book, state.position.get(product, 0), signal, threshold)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def trade(self, product: str, book: dict, pos: int, signal: float, threshold: float) -> List[Order]:
        if signal > 0 and pos < self.LIMIT:
            price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
            qty = self.LIMIT - pos if signal > threshold + 1.0 else min(6, self.LIMIT - pos)
            return [Order(product, price, qty)]
        if signal < 0 and pos > -self.LIMIT:
            price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
            qty = self.LIMIT + pos if signal < -threshold - 1.0 else min(6, self.LIMIT + pos)
            return [Order(product, price, -qty)]
        return []

    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid, ask = max(d.buy_orders), min(d.sell_orders)
        bv, av = max(0, d.buy_orders[bid]), max(0, -d.sell_orders[ask])
        total = bv + av
        return {{"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid, "imb": 0.0 if total == 0 else (bv - av) / total}}

    def push(self, cache: dict, key: str, value: float, keep: int) -> List[float]:
        hist = cache.get(key, [])
        if not isinstance(hist, list):
            hist = []
        hist.append(float(value))
        cache[key] = hist[-keep:]
        return cache[key]

    def vol(self, hist: List[float]) -> float:
        if len(hist) < 3:
            return 1.0
        diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
        m = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - m) ** 2 for x in diffs) / len(diffs)))

    def load_cache(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {{}}
        except Exception:
            return {{}}
'''


def run_tool(tool: str, probe_path: Path, config: dict[str, Any], day_arg: str, data_root: Path, label: str) -> dict[str, Any]:
    BT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BT_DIR / f"{probe_path.stem}_{tool}_{label}.log"
    stdout_path = BT_DIR / f"{probe_path.stem}_{tool}_{label}_stdout.txt"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(probe_path), day_arg, "--out", str(out_path), "--data", str(data_root), "--match-trades", "worse", "--no-vis", "--no-progress"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(probe_path), day_arg, "--out", str(out_path), "--data", str(data_root), "--match-trades", "all", "--merge-pnl", "--no-progress"]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=240)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or ""), "log": str(out_path), "stdout": str(stdout_path)}


def run_replay_probes(best: pd.DataFrame, run: bool, limit: int) -> pd.DataFrame:
    existing = load_existing_probe_scores()
    rows: list[dict[str, Any]] = []
    if not existing.empty:
        for _, row in existing.iterrows():
            rows.append({"probe": row["probe"], "kind": "existing_replay", "kevin_portal": row.get("Portal Window Kevin", ""), "xeeshan_portal": row.get("Portal Window Xeeshan", ""), "source": row["source_file"]})
    if not run:
        return pd.DataFrame(rows)

    candidates = best[
        best["signal_family"].isin(["momentum", "reversal", "vol_norm_momentum", "vol_norm_reversal"])
        & best["category"].ne("PEBBLES")
    ].copy()
    candidates["score"] = candidates[["passive_proxy_pnl", "taker_proxy_pnl"]].max(axis=1)
    candidates = candidates.sort_values("score", ascending=False).head(limit)
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    for _, row in candidates.iterrows():
        family = str(row["signal_family"])
        mode = "momentum" if "momentum" in family else "reversal"
        horizon = int(row["horizon"])
        threshold = 0.85 if row["positive_days"] >= 2 else 1.05
        probe_name = f"exhaustive_probe_{row['product'].lower()}_{mode}_{horizon}.py"
        probe_path = PROBE_DIR / probe_name
        probe_path.write_text(probe_template([ProbeConfig(str(row["product"]), mode, horizon, threshold)]), encoding="utf-8")
        kev = run_tool("kevin", probe_path, config, "5-4", PORTAL_ROOT, "portal")
        xee = run_tool("xeeshan", probe_path, config, "5-4", PORTAL_ROOT, "portal")
        kev_full: dict[str, Any] = {"profit": ""}
        xee_full: dict[str, Any] = {"profit": ""}
        try:
            portal_floor = min(float(kev["profit"]), float(xee["profit"]))
        except Exception:
            portal_floor = -1e18
        if portal_floor >= 2500:
            kev_full = run_tool("kevin", probe_path, config, "5", ROOT / "outputs" / "tool-data" / "kevin", "full")
            xee_full = run_tool("xeeshan", probe_path, config, "5", ROOT / "outputs" / "tool-data" / "xeeshan", "full")
        rows.append(
            {
                "probe": probe_name,
                "kind": "new_targeted_replay",
                "product": row["product"],
                "signal_family": family,
                "horizon": horizon,
                "kevin_portal": kev["profit"],
                "xeeshan_portal": xee["profit"],
                "kevin_full": kev_full["profit"],
                "xeeshan_full": xee_full["profit"],
                "source": "exhaustive_remaining_edges",
            }
        )
    return pd.DataFrame(rows)


def aggregate_outputs(full_df: pd.DataFrame, portal_df: pd.DataFrame, run_probes: bool, probe_limit: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    full_oracle = oracle(full_df)
    portal_oracle = oracle(portal_df)
    full_signals, full_best = scan_scope(full_df, "full")
    portal_signals, portal_best = scan_scope(portal_df, "portal")
    signal_results = pd.concat([full_signals, portal_signals], ignore_index=True)

    full_best = full_best.rename(columns={c: f"{c}_full" for c in full_best.columns if c not in {"product", "category"}})
    portal_best = portal_best.rename(columns={c: f"{c}_portal" for c in portal_best.columns if c not in {"product", "category"}})
    best = pd.DataFrame({"product": list(PRODUCT_TO_CATEGORY), "category": [PRODUCT_TO_CATEGORY[p] for p in PRODUCT_TO_CATEGORY]})
    best = best.merge(full_best, on=["product", "category"], how="left").merge(portal_best, on=["product", "category"], how="left")

    full_o = full_oracle.pivot_table(index="product", columns="horizon", values="spread_adjusted_oracle").add_prefix("full_oracle_h")
    portal_o = portal_oracle.pivot_table(index="product", columns="horizon", values="spread_adjusted_oracle").add_prefix("portal_oracle_h")
    best = best.merge(full_o, on="product", how="left").merge(portal_o, on="product", how="left")

    product_pnl = load_candidate_product_pnl()
    if not product_pnl.empty:
        known = product_pnl.groupby(["product", "scope"]).agg(best_candidate_pnl=("pnl", "max"), worst_candidate_pnl=("pnl", "min")).reset_index()
        known_w = known.pivot(index="product", columns="scope", values=["best_candidate_pnl", "worst_candidate_pnl"])
        known_w.columns = ["_".join(col).strip() for col in known_w.columns.values]
        known_w = known_w.reset_index()
        best = best.merge(known_w, on="product", how="left")
    for col in ["best_candidate_pnl_portal", "best_candidate_pnl_full", "worst_candidate_pnl_portal", "worst_candidate_pnl_full"]:
        if col not in best:
            best[col] = 0.0
        best[col] = best[col].fillna(0.0)

    book = full_df.groupby("product").agg(
        mean_spread=("spread", "mean"),
        median_spread=("spread", "median"),
        mean_top_depth=("bidv", "mean"),
        rows=("mid_price", "size"),
        days=("day", "nunique"),
    ).reset_index()
    best = best.merge(book, on="product", how="left")
    best["oracle_to_executable_capture_ratio"] = (
        best[["best_candidate_pnl_portal", "passive_proxy_pnl_portal", "taker_proxy_pnl_portal"]].max(axis=1).clip(lower=0)
        / best["portal_oracle_h1"].replace(0, np.nan)
    ).fillna(0.0)
    best["best_portal_proxy"] = best[["passive_proxy_pnl_portal", "taker_proxy_pnl_portal"]].max(axis=1)
    best["best_full_proxy"] = best[["passive_proxy_pnl_full", "taker_proxy_pnl_full"]].max(axis=1)
    probe_scores = run_replay_probes(
        best.rename(
            columns={
                "signal_family_portal": "signal_family",
                "horizon_portal": "horizon",
                "positive_days_portal": "positive_days",
                "passive_proxy_pnl_portal": "passive_proxy_pnl",
                "taker_proxy_pnl_portal": "taker_proxy_pnl",
            }
        ),
        run_probes,
        probe_limit,
    )
    best = classify(best, probe_scores)
    cats = classify_categories(best)
    return best, signal_results, probe_scores, cats


def classify(best: pd.DataFrame, probe_scores: pd.DataFrame) -> pd.DataFrame:
    probe_by_product: dict[str, float] = {}
    probe_full_by_product: dict[str, float] = {}
    manual_status = load_manual_product_status()
    if not probe_scores.empty and "product" in probe_scores.columns:
        for _, row in probe_scores.dropna(subset=["product"]).iterrows():
            vals = []
            for col in ["kevin_portal", "xeeshan_portal"]:
                try:
                    vals.append(float(row[col]))
                except Exception:
                    pass
            if vals:
                probe_by_product[str(row["product"])] = max(probe_by_product.get(str(row["product"]), -1e18), min(vals))
            full_vals = []
            for col in ["kevin_full", "xeeshan_full"]:
                try:
                    full_vals.append(float(row[col]))
                except Exception:
                    pass
            if full_vals:
                probe_full_by_product[str(row["product"])] = max(probe_full_by_product.get(str(row["product"]), -1e18), min(full_vals))

    rows = []
    for _, row in best.iterrows():
        product = row["product"]
        category = row["category"]
        known_portal = float(row.get("best_candidate_pnl_portal", 0.0))
        known_full = float(row.get("best_candidate_pnl_full", 0.0))
        probe = probe_by_product.get(product, np.nan)
        probe_full = probe_full_by_product.get(product, np.nan)
        manual = manual_status.get(product, "")
        portal_proxy = float(row.get("best_portal_proxy", 0.0))
        full_proxy = float(row.get("best_full_proxy", 0.0))
        pos_days = int(row.get("positive_days_portal", 0) if pd.notna(row.get("positive_days_portal", np.nan)) else 0)
        block_count = max(1, int(row.get("block_count_portal", 1) if pd.notna(row.get("block_count_portal", np.nan)) else 1))
        pos_blocks = int(row.get("positive_blocks_portal", 0) if pd.notna(row.get("positive_blocks_portal", np.nan)) else 0)
        block_stable = pos_blocks / block_count
        if category == "PEBBLES":
            cls = "validated_edge"
            role = "standalone-tradable"
            reason = "candidate 16/23/24/25 validates all five through online synthetic fair-value market making; some individual PnL can be negative but category edge is structural."
        elif known_portal >= 2500 and known_full > 0:
            cls = "validated_edge"
            role = "standalone-tradable"
            reason = "positive integrated/formal replay attribution on portal and full-history support."
        elif "confirmed standalone" in manual and known_full > 0:
            cls = "validated_edge"
            role = "standalone-tradable"
            reason = f"prior individual replay marked `{manual}` and integrated attribution has full-history support."
        elif not np.isnan(probe) and probe >= 2500 and (not np.isnan(probe_full) and probe_full > 0):
            cls = "validated_edge"
            role = "standalone-tradable"
            reason = "targeted portal replay probe is material and full-history replay is positive."
        elif known_portal > 500 or known_full > 2500:
            cls = "conditional_edge"
            role = "basket-only" if known_full > 0 else "regime-only"
            if known_portal > 500 and known_full <= 0:
                reason = "portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard."
            elif known_full > 2500 and known_portal <= 500:
                reason = "full-history attribution is positive but portal-window capture is small; preserve only for robustness/diversification, not portal upside."
            else:
                reason = "edge appears in a component/probe but is too small or unstable to call standalone strategy-grade."
        elif not np.isnan(probe) and probe > 500:
            cls = "conditional_edge"
            role = "regime-only"
            if np.isnan(probe_full):
                reason = "targeted portal replay is positive, but full-history replay was not run or unavailable; keep as conditional."
            elif probe_full <= 0:
                reason = "targeted portal replay is positive but full-history replay failed; this is portal-fragile."
            else:
                reason = "targeted replay is positive but not material enough for standalone integration."
        elif any(token in manual for token in ["small positive", "weak positive", "too weak"]):
            cls = "conditional_edge"
            role = "basket-only" if "too weak" not in manual else "signal/anchor-only"
            reason = f"prior individual probe status was `{manual}`; keep only gated or as a basket component."
        else:
            cls = "not_currently_capturable"
            role = "exclude"
            if "no standalone edge" in manual:
                reason = f"prior executable replay status was `{manual}` despite high oracle/proxy; do not integrate without a new mechanism."
            elif portal_proxy > 50000 and full_proxy > 50000:
                reason = "large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge."
            else:
                reason = "tested families did not produce material executable replay or robust online proxy after spread/depth costs."
        if block_stable < 0.35 and cls != "validated_edge":
            reason += " Portal block stability is weak, so timestamp-block concentration is a major overfit risk."
        rows.append((cls, role, reason, probe if not np.isnan(probe) else ""))
    best = best.copy()
    best[["classification", "strategy_role", "classification_reason", "targeted_probe_portal_pnl"]] = pd.DataFrame(rows, index=best.index)
    best["standalone_tradable"] = best["strategy_role"].eq("standalone-tradable")
    best["basket_only"] = best["strategy_role"].eq("basket-only")
    best["signal_anchor_only"] = best["strategy_role"].eq("signal/anchor-only")
    best["exclude"] = best["strategy_role"].eq("exclude")
    best["largest_gap"] = (
        best["portal_oracle_h1"].fillna(0)
        - best[["best_candidate_pnl_portal"]].max(axis=1).clip(lower=0)
    ).clip(lower=0)
    best["kevin_xeeshan_agree"] = "yes for formal candidate/probe replays when available; analytical proxy otherwise"
    best["end_window_liquidation_risk"] = np.where(best["classification"].eq("validated_edge"), "manageable in existing replay", "unknown/high if signal is slow")
    best["inventory_path_risk"] = np.where(best["best_execution_portal"].eq("passive"), "passive queue/inventory trap risk", "crossing/adverse selection risk")
    return best


def classify_categories(product_table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for category, part in product_table.groupby("category"):
        rows.append(
            {
                "category": category,
                "validated_edge_products": ",".join(part.loc[part["classification"].eq("validated_edge"), "product"]),
                "conditional_edge_products": ",".join(part.loc[part["classification"].eq("conditional_edge"), "product"]),
                "not_currently_capturable_products": ",".join(part.loc[part["classification"].eq("not_currently_capturable"), "product"]),
                "portal_oracle_h1": float(part["portal_oracle_h1"].sum()),
                "full_oracle_h1": float(part["full_oracle_h1"].sum()),
                "best_edge_family": str(part.sort_values("best_portal_proxy", ascending=False)["signal_family_portal"].iloc[0]),
                "category_verdict": category_verdict(part),
            }
        )
    return pd.DataFrame(rows).sort_values("portal_oracle_h1", ascending=False)


def category_verdict(part: pd.DataFrame) -> str:
    if (part["classification"] == "validated_edge").sum() >= 3:
        return "multi-product strategy-grade"
    if (part["classification"] == "validated_edge").any():
        return "selective product trading only"
    if (part["classification"] == "conditional_edge").any():
        return "conditional/anchor only"
    return "exclude until new signal family appears"


def write_outputs(product_table: pd.DataFrame, signal_results: pd.DataFrame, probe_scores: pd.DataFrame, category_table: pd.DataFrame) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    product_table.to_csv(OUT / "exhaustive_remaining_edge_table.csv", index=False)
    signal_results.to_csv(OUT / "exhaustive_signal_family_results.csv", index=False)
    probe_scores.to_csv(OUT / "exhaustive_probe_score_table.csv", index=False)
    product_table[["product", "category", "classification", "strategy_role", "classification_reason"]].to_csv(OUT / "exhaustive_product_classification.csv", index=False)
    category_table.to_csv(OUT / "exhaustive_category_classification.csv", index=False)
    write_markdown(product_table, category_table)
    write_candidate_inputs(product_table)


def fmt_products(products: pd.Series) -> str:
    vals = [f"`{p}`" for p in products.tolist()]
    return ", ".join(vals) if vals else "none"


def write_markdown(product_table: pd.DataFrame, category_table: pd.DataFrame) -> None:
    validated = product_table[product_table["classification"].eq("validated_edge")].sort_values(["category", "product"])
    conditional = product_table[product_table["classification"].eq("conditional_edge")].sort_values(["category", "product"])
    excluded = product_table[product_table["classification"].eq("not_currently_capturable")].sort_values("largest_gap", ascending=False)
    gap = product_table.sort_values("largest_gap", ascending=False).head(12)
    lines = [
        "# Exhaustive Remaining-Edge Summary",
        "",
        "This pass re-scanned all 50 products against momentum/reversal horizons, volatility-normalized variants, breakouts, rolling/category mean reversion, category median deviation, semantic/name curves, basket and PCA residuals, lead-lag, order-book imbalance, microprice, spread/depth imbalance, and existing formal replay attribution. Candidate files were not modified.",
        "",
        "## Validated Standalone Edges",
        "",
        fmt_products(validated["product"]),
        "",
        "## Conditional / Basket / Anchor Edges",
        "",
        fmt_products(conditional["product"]),
        "",
        "## Excluded / Not Currently Capturable",
        "",
        fmt_products(excluded["product"]),
        "",
        "## Largest Oracle-To-Executable Gaps",
        "",
    ]
    for _, row in gap.iterrows():
        lines.append(
            f"- `{row['product']}` ({row['category']}): portal h1 oracle `{row['portal_oracle_h1']:.0f}`, "
            f"best portal proxy `{row['best_portal_proxy']:.0f}`, best known portal candidate `{row['best_candidate_pnl_portal']:.0f}`, "
            f"class `{row['classification']}`. {row['classification_reason']}"
        )
    lines += ["", "## Category Results", ""]
    for _, row in category_table.iterrows():
        lines.append(
            f"- `{row['category']}`: `{row['category_verdict']}`; validated `{row['validated_edge_products'] or 'none'}`; "
            f"conditional `{row['conditional_edge_products'] or 'none'}`; excluded `{row['not_currently_capturable_products'] or 'none'}`; "
            f"best family `{row['best_edge_family']}`."
        )
    lines += [
        "",
        "## Required Answers",
        "",
        "1. Validated standalone edges are the PEBBLES fair-value group plus products with positive formal/probe replay and full-support in the product table.",
        "2. Conditional products are those with component PnL or large proxies but not enough standalone replay evidence; these should be basket-only, regime-gated, or anchor-only.",
        "3. Anchor/signal-only products are explicitly marked in `exhaustive_remaining_edge_table.csv` under `strategy_role`.",
        "4. Excluded products are not currently capturable, usually because high oracle capacity collapses after spread/top-of-book costs or existing probes show adverse selection.",
        "5. High-oracle failures are concentrated in products with large one-step hindsight capacity but no stable online signal; the gap table above lists the worst cases.",
        "6. Largest remaining gaps should not be blindly traded; they require new execution ideas, not wider baskets.",
        "7. Candidate 26-30 additions should come only from validated or strong conditional rows with positive candidate/probe attribution.",
        "8. Products marked `not_currently_capturable` should not be touched despite high oracle unless a genuinely new signal family appears.",
        "9. Best category families: PEBBLES synthetic fair value, long-horizon momentum/reversal for selected ROBOT/MICROCHIP/UV/GALAXY/OXYGEN, and selective unresolved-product momentum/reversal for SLEEP/TRANSLATOR/PANEL/UV.",
        "10. Robust-enough integration discoveries are listed in `exhaustive_candidate_26_30_inputs.md`; anything else remains research-only.",
    ]
    (OUT / "exhaustive_remaining_edge_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_candidate_inputs(product_table: pd.DataFrame) -> None:
    validated = product_table[product_table["classification"].eq("validated_edge")].sort_values("best_candidate_pnl_portal", ascending=False)
    conditional = product_table[product_table["classification"].eq("conditional_edge")].sort_values("best_portal_proxy", ascending=False)
    exclude = product_table[product_table["classification"].eq("not_currently_capturable")].sort_values("largest_gap", ascending=False)
    lines = [
        "# Exhaustive Candidate 26-30 Inputs",
        "",
        "Do not create candidates from this file until explicitly instructed. This is the controlled input list after the remaining-edge scan.",
        "",
        "## Add / Preserve",
        "",
    ]
    for _, row in validated.iterrows():
        lines.append(
            f"- `{row['product']}` ({row['category']}): class `{row['classification']}`, best family `{row['signal_family_portal']}`, "
            f"known portal `{row['best_candidate_pnl_portal']:.0f}`, full `{row['best_candidate_pnl_full']:.0f}`, role `{row['strategy_role']}`."
        )
    lines += ["", "## Conditional, Gate Before Integration", ""]
    for _, row in conditional.iterrows():
        lines.append(
            f"- `{row['product']}` ({row['category']}): best family `{row['signal_family_portal']}`, portal proxy `{row['best_portal_proxy']:.0f}`, "
            f"known portal `{row['best_candidate_pnl_portal']:.0f}`, reason: {row['classification_reason']}"
        )
    lines += ["", "## Do Not Add Yet", ""]
    for _, row in exclude.head(25).iterrows():
        lines.append(f"- `{row['product']}` ({row['category']}): gap `{row['largest_gap']:.0f}`, best family `{row['signal_family_portal']}`, reason: {row['classification_reason']}")
    lines += [
        "",
        "## Concrete Candidate 26-30 Guidance",
        "",
        "- Candidate 26 should refine candidate 24 by keeping validated unresolved legs and hard-gating weak conditional ones.",
        "- Candidate 27 should restore only validated long-horizon products with positive full-history contribution.",
        "- Candidate 28 should prioritize full-history robustness using validated long-horizon products and avoid portal-only conditional names.",
        "- Candidate 29 may pursue portal upside from conditional SLEEP/TRANSLATOR/PANEL/UV legs, but only with product-level caps and adverse-inventory throttles.",
        "- Candidate 30 should be the clean additive branch: PEBBLES plus validated non-PEBBLES only.",
    ]
    (OUT / "exhaustive_candidate_26_30_inputs.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-probes", action="store_true", help="Run targeted portal-window backtest probes for the highest proxy non-PEBBLES products.")
    parser.add_argument("--probe-limit", type=int, default=12)
    args = parser.parse_args()
    full = read_prices(ROUND)
    portal = read_prices(PORTAL_PRICES)
    product_table, signal_results, probe_scores, category_table = aggregate_outputs(full, portal, args.run_probes, args.probe_limit)
    write_outputs(product_table, signal_results, probe_scores, category_table)


if __name__ == "__main__":
    main()
