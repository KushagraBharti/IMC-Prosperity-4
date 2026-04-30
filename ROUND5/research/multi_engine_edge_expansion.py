from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import argparse
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROUND = ROOT / "ROUND5"
OUT = ROUND / "research" / "outputs"
ME_OUT = OUT / "multi_engine_edge_expansion"
PROBE_DIR = ROUND / "research" / "probes" / "multi_engine"
BT_DIR = OUT / "backtests" / "multi_engine_edge_expansion"
PORTAL_ROOT = OUT / "official_portal_windows" / "round5_candidate_1"

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


PROBES: dict[str, dict[str, tuple[Any, ...]]] = {
    "me_microchip_shape_breakout": {
        "MICROCHIP_SQUARE": ("breakout_low_reversal", 200, 0.75, 1.2),
        "MICROCHIP_TRIANGLE": ("rolling_mean_reversion", 100, 0.85, 1.0),
        "MICROCHIP_RECTANGLE": ("breakout_low_reversal", 200, 0.85, 0.9),
        "MICROCHIP_OVAL": ("breakout_low_reversal", 200, 0.85, 1.0),
    },
    "me_robot_specialists": {
        "ROBOT_DISHES": ("breakout_low_reversal", 100, 0.90, 1.1),
        "ROBOT_MOPPING": ("rolling_mean_reversion", 100, 0.85, 1.0),
        "ROBOT_LAUNDRY": ("breakout_low_reversal", 200, 0.95, 0.8),
        "ROBOT_IRONING": ("momentum", 100, 0.85, 1.0),
        "ROBOT_VACUUMING": ("breakout_low_reversal", 100, 1.0, 0.7),
    },
    "me_sleep_material_curve": {
        "SLEEP_POD_COTTON": ("vol_norm_momentum", 200, 0.90, 1.2),
        "SLEEP_POD_POLYESTER": ("breakout_low_reversal", 200, 0.90, 1.0),
        "SLEEP_POD_SUEDE": ("breakout_low_reversal", 200, 0.95, 0.8),
        "SLEEP_POD_LAMB_WOOL": ("breakout_low_reversal", 200, 0.95, 0.8),
        "SLEEP_POD_NYLON": ("rolling_mean_reversion", 100, 0.90, 0.8),
    },
    "me_panel_geometry": {
        "PANEL_4X4": ("momentum", 50, 0.80, 1.3),
        "PANEL_2X4": ("breakout_low_reversal", 200, 0.90, 0.9),
        "PANEL_2X2": ("breakout_low_reversal", 200, 1.0, 0.7),
        "PANEL_1X4": ("breakout_low_reversal", 200, 1.0, 0.6),
        "PANEL_1X2": ("breakout_low_reversal", 200, 1.0, 0.6),
    },
    "me_translator_colorways": {
        "TRANSLATOR_GRAPHITE_MIST": ("breakout_low_reversal", 100, 0.85, 1.0),
        "TRANSLATOR_VOID_BLUE": ("breakout_low_reversal", 100, 0.90, 0.9),
        "TRANSLATOR_ASTRO_BLACK": ("breakout_low_reversal", 100, 1.0, 0.6),
        "TRANSLATOR_SPACE_GRAY": ("breakout_high", 200, 1.0, 0.6),
        "TRANSLATOR_ECLIPSE_CHARCOAL": ("rolling_mean_reversion", 200, 1.0, 0.6),
    },
    "me_galaxy_trends": {
        "GALAXY_SOUNDS_PLANETARY_RINGS": ("breakout_low_reversal", 200, 0.85, 1.0),
        "GALAXY_SOUNDS_SOLAR_WINDS": ("rolling_mean_reversion", 200, 1.0, 0.6),
        "GALAXY_SOUNDS_DARK_MATTER": ("breakout_high", 200, 1.0, 0.6),
        "GALAXY_SOUNDS_BLACK_HOLES": ("rolling_mean_reversion", 200, 1.0, 0.6),
        "GALAXY_SOUNDS_SOLAR_FLAMES": ("rolling_mean_reversion", 200, 1.0, 0.6),
    },
    "me_uv_color_curve": {
        "UV_VISOR_ORANGE": ("momentum", 200, 0.85, 1.1),
        "UV_VISOR_RED": ("momentum", 200, 0.95, 0.8),
        "UV_VISOR_AMBER": ("breakout_low_reversal", 200, 0.95, 0.7),
        "UV_VISOR_YELLOW": ("breakout_low_reversal", 200, 1.0, 0.6),
        "UV_VISOR_MAGENTA": ("breakout_low_reversal", 200, 1.0, 0.6),
    },
    "me_oxygen_flavors": {
        "OXYGEN_SHAKE_GARLIC": ("reversal", 200, 0.85, 1.3),
        "OXYGEN_SHAKE_EVENING_BREATH": ("breakout_low_reversal", 200, 0.95, 0.8),
        "OXYGEN_SHAKE_MORNING_BREATH": ("breakout_high", 200, 1.0, 0.6),
        "OXYGEN_SHAKE_MINT": ("breakout_low_reversal", 200, 1.0, 0.6),
        "OXYGEN_SHAKE_CHOCOLATE": ("rolling_mean_reversion", 200, 1.0, 0.6),
    },
    "me_snackpack_specialists": {
        "SNACKPACK_RASPBERRY": ("breakout_low_reversal", 200, 1.0, 0.8),
        "SNACKPACK_STRAWBERRY": ("breakout_low_reversal", 200, 1.0, 0.8),
        "SNACKPACK_CHOCOLATE": ("rolling_mean_reversion", 200, 1.0, 0.6),
        "SNACKPACK_VANILLA": ("rolling_mean_reversion", 200, 1.0, 0.6),
        "SNACKPACK_PISTACHIO": ("breakout_low_reversal", 200, 1.0, 0.6),
    },
    "me_validated_addons": {
        "OXYGEN_SHAKE_GARLIC": ("reversal", 200, 0.85, 1.3),
        "PANEL_4X4": ("momentum", 50, 0.80, 1.3),
        "UV_VISOR_ORANGE": ("momentum", 200, 0.85, 1.1),
        "ROBOT_IRONING": ("momentum", 100, 0.85, 1.0),
        "MICROCHIP_OVAL": ("breakout_low_reversal", 200, 0.90, 0.9),
    },
    "me_microchip_taker_stress": {
        "MICROCHIP_SQUARE": ("breakout_low_reversal", 200, 0.95, 1.0, "hybrid"),
        "MICROCHIP_TRIANGLE": ("rolling_mean_reversion", 100, 0.95, 0.9, "hybrid"),
        "MICROCHIP_RECTANGLE": ("breakout_low_reversal", 200, 1.0, 0.8, "hybrid"),
    },
    "me_robot_dishes_execution": {
        "ROBOT_DISHES": ("reversal", 25, 0.90, 1.2, "hybrid"),
    },
    "me_robot_dishes_breakout": {
        "ROBOT_DISHES": ("breakout_low_reversal", 100, 1.0, 1.0, "hybrid"),
    },
    "me_translator_taker_stress": {
        "TRANSLATOR_GRAPHITE_MIST": ("breakout_low_reversal", 100, 1.0, 0.9, "hybrid"),
        "TRANSLATOR_VOID_BLUE": ("breakout_low_reversal", 100, 1.0, 0.8, "hybrid"),
        "TRANSLATOR_SPACE_GRAY": ("breakout_high", 200, 1.05, 0.7, "hybrid"),
    },
    "me_uv_portal_stress": {
        "UV_VISOR_ORANGE": ("momentum", 200, 0.80, 1.2, "hybrid"),
        "UV_VISOR_RED": ("momentum", 200, 0.90, 1.0, "hybrid"),
        "UV_VISOR_YELLOW": ("breakout_low_reversal", 200, 1.0, 0.7, "hybrid"),
    },
    "me_microchip_positive_ablation": {
        "MICROCHIP_SQUARE": ("breakout_low_reversal", 200, 0.75, 1.2),
        "MICROCHIP_RECTANGLE": ("breakout_low_reversal", 200, 0.85, 0.9),
        "MICROCHIP_OVAL": ("breakout_low_reversal", 200, 0.85, 1.0),
    },
    "me_robot_positive_ablation": {
        "ROBOT_DISHES": ("breakout_low_reversal", 100, 1.0, 0.7),
        "ROBOT_MOPPING": ("rolling_mean_reversion", 100, 0.85, 1.0),
        "ROBOT_LAUNDRY": ("breakout_low_reversal", 200, 0.95, 0.8),
        "ROBOT_IRONING": ("momentum", 100, 0.85, 1.0),
    },
    "me_sleep_positive_ablation": {
        "SLEEP_POD_COTTON": ("vol_norm_momentum", 200, 0.90, 1.2),
        "SLEEP_POD_LAMB_WOOL": ("breakout_low_reversal", 200, 0.95, 0.8),
        "SLEEP_POD_NYLON": ("rolling_mean_reversion", 100, 0.90, 0.8),
    },
    "me_panel_positive_ablation": {
        "PANEL_4X4": ("momentum", 50, 0.80, 1.3),
        "PANEL_1X2": ("breakout_low_reversal", 200, 1.0, 0.6),
        "PANEL_1X4": ("breakout_low_reversal", 200, 1.0, 0.6),
        "PANEL_2X2": ("breakout_low_reversal", 200, 1.0, 0.7),
    },
    "me_translator_positive_ablation": {
        "TRANSLATOR_SPACE_GRAY": ("breakout_high", 200, 1.0, 0.9, "hybrid"),
        "TRANSLATOR_ECLIPSE_CHARCOAL": ("rolling_mean_reversion", 200, 1.0, 0.7),
    },
    "me_galaxy_positive_ablation": {
        "GALAXY_SOUNDS_DARK_MATTER": ("breakout_high", 200, 1.0, 0.8),
        "GALAXY_SOUNDS_SOLAR_FLAMES": ("rolling_mean_reversion", 200, 1.0, 0.8),
        "GALAXY_SOUNDS_SOLAR_WINDS": ("rolling_mean_reversion", 200, 1.0, 0.7),
        "GALAXY_SOUNDS_PLANETARY_RINGS": ("breakout_low_reversal", 200, 0.85, 1.0),
    },
    "me_uv_positive_ablation": {
        "UV_VISOR_YELLOW": ("breakout_low_reversal", 200, 1.0, 0.7),
        "UV_VISOR_RED": ("momentum", 200, 0.95, 0.8),
        "UV_VISOR_ORANGE": ("momentum", 200, 0.85, 1.1),
    },
    "me_oxygen_positive_ablation": {
        "OXYGEN_SHAKE_MORNING_BREATH": ("breakout_high", 200, 1.0, 0.7),
        "OXYGEN_SHAKE_CHOCOLATE": ("rolling_mean_reversion", 200, 1.0, 0.7),
        "OXYGEN_SHAKE_GARLIC": ("reversal", 200, 0.85, 1.3),
        "OXYGEN_SHAKE_MINT": ("breakout_low_reversal", 200, 1.0, 0.6),
        "OXYGEN_SHAKE_EVENING_BREATH": ("breakout_low_reversal", 200, 0.95, 0.8),
    },
    "me_snackpack_positive_ablation": {
        "SNACKPACK_VANILLA": ("rolling_mean_reversion", 200, 1.0, 0.7),
        "SNACKPACK_CHOCOLATE": ("rolling_mean_reversion", 200, 1.0, 0.7),
        "SNACKPACK_RASPBERRY": ("breakout_low_reversal", 200, 1.0, 0.8),
        "SNACKPACK_PISTACHIO": ("breakout_low_reversal", 200, 1.0, 0.6),
    },
    "me_individual_galaxy_dark_matter": {
        "GALAXY_SOUNDS_DARK_MATTER": ("breakout_high", 200, 1.0, 1.0),
    },
    "me_individual_galaxy_solar_flames": {
        "GALAXY_SOUNDS_SOLAR_FLAMES": ("rolling_mean_reversion", 200, 1.0, 1.0),
    },
    "me_individual_galaxy_solar_winds": {
        "GALAXY_SOUNDS_SOLAR_WINDS": ("rolling_mean_reversion", 200, 1.0, 1.0),
    },
    "me_individual_translator_space_gray": {
        "TRANSLATOR_SPACE_GRAY": ("breakout_high", 200, 1.0, 1.0, "hybrid"),
    },
    "me_individual_translator_eclipse": {
        "TRANSLATOR_ECLIPSE_CHARCOAL": ("rolling_mean_reversion", 200, 1.0, 1.0),
    },
    "me_individual_oxygen_morning": {
        "OXYGEN_SHAKE_MORNING_BREATH": ("breakout_high", 200, 1.0, 1.0),
    },
    "me_individual_oxygen_chocolate": {
        "OXYGEN_SHAKE_CHOCOLATE": ("rolling_mean_reversion", 200, 1.0, 1.0),
    },
    "me_individual_oxygen_mint": {
        "OXYGEN_SHAKE_MINT": ("breakout_low_reversal", 200, 1.0, 1.0),
    },
    "me_individual_panel_1x2": {
        "PANEL_1X2": ("breakout_low_reversal", 200, 1.0, 1.0),
    },
    "me_individual_panel_1x4": {
        "PANEL_1X4": ("breakout_low_reversal", 200, 1.0, 1.0),
    },
    "me_individual_panel_2x2": {
        "PANEL_2X2": ("breakout_low_reversal", 200, 1.0, 1.0),
    },
    "me_individual_sleep_lamb_wool": {
        "SLEEP_POD_LAMB_WOOL": ("breakout_low_reversal", 200, 0.95, 1.0),
    },
    "me_individual_sleep_nylon": {
        "SLEEP_POD_NYLON": ("rolling_mean_reversion", 100, 0.90, 1.0),
    },
    "me_individual_microchip_square": {
        "MICROCHIP_SQUARE": ("breakout_low_reversal", 200, 0.75, 1.0),
    },
    "me_individual_microchip_rectangle": {
        "MICROCHIP_RECTANGLE": ("breakout_low_reversal", 200, 0.85, 1.0),
    },
    "me_individual_robot_dishes_basket_style": {
        "ROBOT_DISHES": ("breakout_low_reversal", 100, 1.0, 1.0),
    },
    "me_individual_robot_laundry": {
        "ROBOT_LAUNDRY": ("breakout_low_reversal", 200, 0.95, 1.0),
    },
    "me_individual_robot_mopping": {
        "ROBOT_MOPPING": ("rolling_mean_reversion", 100, 0.85, 1.0),
    },
    "me_individual_snackpack_chocolate": {
        "SNACKPACK_CHOCOLATE": ("rolling_mean_reversion", 200, 1.0, 1.0),
    },
    "me_individual_snackpack_raspberry": {
        "SNACKPACK_RASPBERRY": ("breakout_low_reversal", 200, 1.0, 1.0),
    },
}


def strategy_template(config: dict[str, tuple[str, int, float, float]]) -> str:
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
    CONFIG = {config!r}
    MAX_ACTIVE = 10

    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {{}}
        scored = []
        for product, cfg in self.CONFIG.items():
            mode, lookback, threshold, weight = cfg[:4]
            style = cfg[4] if len(cfg) > 4 else "passive"
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, product, book["mid"], max(620, lookback + 180))
            if len(hist) <= lookback + 3:
                continue
            signal = self.signal(mode, hist, lookback)
            signal += 0.08 * book["imb"]
            score = abs(signal) / max(threshold, 0.01) * weight
            if abs(signal) >= threshold:
                scored.append((score, product, book, signal, threshold, weight, style))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _, product, book, signal, threshold, weight, style in scored[: self.MAX_ACTIVE]:
            result[product] = self.trade(product, book, state.position.get(product, 0), signal, threshold, weight, style)
        return result, 0, json.dumps(cache, separators=(",", ":"))

    def signal(self, mode: str, hist: List[float], lookback: int) -> float:
        vol = max(self.vol(hist[-160:]), 1.0)
        move = hist[-1] - hist[-1 - lookback]
        if mode == "momentum":
            return move / vol
        if mode == "reversal":
            return -move / vol
        if mode == "vol_norm_momentum":
            return move / vol
        if mode == "vol_norm_reversal":
            return -move / vol
        window = hist[-lookback:]
        mean = sum(window) / len(window)
        hi = max(window[:-1]) if len(window) > 1 else hist[-1]
        lo = min(window[:-1]) if len(window) > 1 else hist[-1]
        if mode == "rolling_mean_reversion":
            return -(hist[-1] - mean) / vol
        if mode == "breakout_high":
            return (hist[-1] - hi) / vol
        if mode == "breakout_low_reversal":
            return (lo - hist[-1]) / vol
        return move / vol

    def trade(self, product: str, book: dict, pos: int, signal: float, threshold: float, weight: float, style: str) -> List[Order]:
        strong = abs(signal) > threshold + 0.85
        base_qty = 10 if strong or weight >= 1.2 else 6
        if signal > 0 and pos < self.LIMIT:
            if style == "hybrid" and abs(signal) > threshold + 0.55:
                price = book["ask"]
            else:
                price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
            return [Order(product, price, min(base_qty, self.LIMIT - pos))]
        if signal < 0 and pos > -self.LIMIT:
            if style == "hybrid" and abs(signal) > threshold + 0.55:
                price = book["bid"]
            else:
                price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
            return [Order(product, price, -min(base_qty, self.LIMIT + pos))]
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


def parse_profit(log_path: Path, stdout: str) -> float | None:
    texts = [stdout]
    if log_path.exists():
        texts.append(log_path.read_text(encoding="utf-8", errors="ignore")[-20000:])
    for text in texts:
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    return None


def run_tool(tool: str, probe_path: Path, day_arg: str, data_root: Path, label: str, config: dict[str, Any]) -> dict[str, Any]:
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
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=360)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or ""), "log": str(out_path), "stdout": str(stdout_path)}


def final_product_pnl(log_path: Path) -> pd.DataFrame:
    if not log_path.exists():
        return pd.DataFrame(columns=["product", "pnl"])
    data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
    act = pd.read_csv(io.StringIO(data["activitiesLog"]), sep=";")
    last = act.sort_values("timestamp").groupby("product", as_index=False).tail(1)
    return last[["product", "profit_and_loss"]].rename(columns={"profit_and_loss": "pnl"})


def load_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    edge = pd.read_csv(OUT / "exhaustive_remaining_edge_table.csv")
    signals = pd.read_csv(OUT / "exhaustive_signal_family_results.csv")
    cls = pd.read_csv(OUT / "exhaustive_product_classification.csv")
    attr = pd.read_csv(OUT / "candidate_21_25_product_pnl.csv")
    return edge, signals, cls, attr


def existing_profit(probe_stem: str, tool: str, label: str) -> float | str:
    log_path = BT_DIR / f"{probe_stem}_{tool}_{label}.log"
    stdout_path = BT_DIR / f"{probe_stem}_{tool}_{label}_stdout.txt"
    if not log_path.exists() and not stdout_path.exists():
        return ""
    stdout = stdout_path.read_text(encoding="utf-8", errors="ignore") if stdout_path.exists() else ""
    value = parse_profit(log_path, stdout)
    return "" if value is None else value


def existing_run_result(probe_stem: str, tool: str, label: str) -> dict[str, Any] | None:
    log_path = BT_DIR / f"{probe_stem}_{tool}_{label}.log"
    stdout_path = BT_DIR / f"{probe_stem}_{tool}_{label}_stdout.txt"
    if not log_path.exists() or not stdout_path.exists():
        return None
    stdout = stdout_path.read_text(encoding="utf-8", errors="ignore")
    return {"returncode": 0, "profit": parse_profit(log_path, stdout), "log": str(log_path), "stdout": str(stdout_path)}


def score_probes(run_full: bool = False) -> pd.DataFrame:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for name, probe_config in PROBES.items():
        path = PROBE_DIR / f"{name}.py"
        path.write_text(strategy_template(probe_config), encoding="utf-8")
        cached_kp = existing_run_result(path.stem, "kevin", "portal")
        cached_xp = existing_run_result(path.stem, "xeeshan", "portal")
        if cached_kp and cached_xp:
            kp, xp = cached_kp, cached_xp
            print(f"Using cached {name} portal...")
        else:
            print(f"Scoring {name} portal...")
            kp = run_tool("kevin", path, "5-4", PORTAL_ROOT, "portal", config)
            xp = run_tool("xeeshan", path, "5-4", PORTAL_ROOT, "portal", config)
        kfull: dict[str, Any] = {"profit": existing_profit(path.stem, "kevin", "full")}
        xfull: dict[str, Any] = {"profit": existing_profit(path.stem, "xeeshan", "full")}
        full_source = "existing_log" if kfull["profit"] != "" or xfull["profit"] != "" else ""
        try:
            portal_floor = min(float(kp["profit"]), float(xp["profit"]))
        except Exception:
            portal_floor = -1e18
        if run_full and portal_floor >= 5000 and (kfull["profit"] == "" or xfull["profit"] == ""):
            print(f"Scoring {name} full...")
            kfull = run_tool("kevin", path, "5", ROOT / "outputs" / "tool-data" / "kevin", "full", config)
            xfull = run_tool("xeeshan", path, "5", ROOT / "outputs" / "tool-data" / "xeeshan", "full", config)
            full_source = "new_full_run"
        pnl = final_product_pnl(Path(kp["log"]))
        product_pnls = ";".join(f"{r.product}:{float(r.pnl):.0f}" for r in pnl[pnl["product"].isin(probe_config)].itertuples())
        rows.append(
            {
                "probe": f"{name}.py",
                "products": ",".join(probe_config),
                "portal_kevin": kp["profit"],
                "portal_xeeshan": xp["profit"],
                "full_kevin": kfull["profit"],
                "full_xeeshan": xfull["profit"],
                "full_source": full_source,
                "product_count": len(probe_config),
                "portal_product_pnls": product_pnls,
                "probe_path": str(path),
                "kevin_portal_log": kp["log"],
            }
        )
    return pd.DataFrame(rows)


def build_engine_table(edge: pd.DataFrame, signals: pd.DataFrame, cls: pd.DataFrame, attr: pd.DataFrame, probes: pd.DataFrame) -> pd.DataFrame:
    best_family = (
        signals.assign(score=lambda d: d[["passive_proxy_pnl", "taker_proxy_pnl"]].max(axis=1))
        .sort_values("score", ascending=False)
        .groupby(["scope", "product"], as_index=False)
        .head(1)
    )
    portal_best = best_family[best_family["scope"].eq("portal")].rename(columns={c: f"{c}_best_portal" for c in best_family.columns if c not in {"product"}})
    full_best = best_family[best_family["scope"].eq("full")].rename(columns={c: f"{c}_best_full" for c in best_family.columns if c not in {"product"}})
    attr_wide = attr.groupby(["product", "scope"]).agg(best_candidate_pnl=("pnl", "max"), worst_candidate_pnl=("pnl", "min")).reset_index()
    attr_wide = attr_wide.pivot(index="product", columns="scope", values=["best_candidate_pnl", "worst_candidate_pnl"]).reset_index()
    attr_wide.columns = ["_".join(str(x) for x in c if x) for c in attr_wide.columns]
    probe_product: dict[str, dict[str, Any]] = {}
    for _, row in probes.iterrows():
        for item in str(row.get("portal_product_pnls", "")).split(";"):
            if ":" not in item:
                continue
            product, val = item.split(":", 1)
            pnl = float(val)
            old = probe_product.get(product)
            full_for_product = row["full_kevin"] if int(row.get("product_count", 99) or 99) == 1 else ""
            if old is None or pnl > old["best_probe_product_pnl"]:
                probe_product[product] = {"best_probe": row["probe"], "best_probe_product_pnl": pnl, "probe_portal_kevin": row["portal_kevin"], "probe_full_kevin": full_for_product}
    prior_probe_path = OUT / "exhaustive_probe_score_table.csv"
    if prior_probe_path.exists():
        prior = pd.read_csv(prior_probe_path)
        for _, row in prior.dropna(subset=["product"]).iterrows():
            product = str(row["product"])
            try:
                pnl = min(float(row["kevin_portal"]), float(row["xeeshan_portal"]))
            except Exception:
                continue
            try:
                full = min(float(row.get("kevin_full", "")), float(row.get("xeeshan_full", "")))
            except Exception:
                full = ""
            old = probe_product.get(product)
            if old is None or pnl > old["best_probe_product_pnl"] or (pnl == old["best_probe_product_pnl"] and full != ""):
                probe_product[product] = {
                    "best_probe": str(row["probe"]),
                    "best_probe_product_pnl": pnl,
                    "probe_portal_kevin": row["kevin_portal"],
                    "probe_full_kevin": full,
                }
    probe_df = pd.DataFrame([{"product": p, **v} for p, v in probe_product.items()])
    table = (
        edge[["product", "category", "classification", "strategy_role", "portal_oracle_h1", "full_oracle_h1", "largest_gap"]]
        .merge(cls, on=["product", "category"], how="left", suffixes=("", "_old"))
        .merge(portal_best[["product", "signal_family_best_portal", "model_type_best_portal", "horizon_best_portal", "passive_proxy_pnl_best_portal", "taker_proxy_pnl_best_portal", "positive_days_best_portal", "positive_blocks_best_portal", "block_count_best_portal"]], on="product", how="left")
        .merge(full_best[["product", "signal_family_best_full", "model_type_best_full", "horizon_best_full", "passive_proxy_pnl_best_full", "taker_proxy_pnl_best_full", "positive_days_best_full"]], on="product", how="left")
        .merge(attr_wide, on="product", how="left")
        .merge(probe_df, on="product", how="left")
    )
    for col in ["best_candidate_pnl_portal", "best_candidate_pnl_full", "best_probe_product_pnl"]:
        if col not in table:
            table[col] = 0.0
        table[col] = pd.to_numeric(table[col], errors="coerce").fillna(0.0)
    table["oracle_capture_portal"] = table[["best_candidate_pnl_portal", "best_probe_product_pnl"]].max(axis=1).clip(lower=0) / table["portal_oracle_h1"].replace(0, pd.NA)
    table["engine_status"] = table.apply(engine_status, axis=1)
    table["best_engine"] = table.apply(best_engine_name, axis=1)
    table["engine_action"] = table.apply(engine_action, axis=1)
    table["failure_or_risk"] = table.apply(failure_reason, axis=1)
    table["candidate_26_30_role"] = table.apply(candidate_role, axis=1)
    return table.sort_values(["engine_status", "portal_oracle_h1"], ascending=[True, False])


def engine_status(row: pd.Series) -> str:
    best_probe = float(row.get("best_probe_product_pnl", 0.0))
    best_portal = float(row.get("best_candidate_pnl_portal", 0.0))
    best_full = float(row.get("best_candidate_pnl_full", 0.0))
    if row["category"] == "PEBBLES":
        return "engine_validated"
    if best_probe >= 2500 and (best_full > 0 or str(row.get("probe_full_kevin", "")).strip() not in {"", "nan"} and float(row.get("probe_full_kevin", 0) or 0) > 0):
        return "engine_validated"
    if best_portal >= 2500 and best_full > 0:
        return "engine_validated"
    if best_portal > 500 or best_probe > 500 or best_full > 2500:
        return "engine_conditional"
    if row["strategy_role"] == "signal/anchor-only":
        return "engine_anchor_only"
    return "engine_not_found_yet"


def best_engine_name(row: pd.Series) -> str:
    if row["category"] == "PEBBLES":
        return "pebbles_synthetic_fair_value_mm"
    if pd.notna(row.get("best_probe")):
        return str(row["best_probe"]).replace(".py", "")
    return f"{row.get('signal_family_best_portal', 'unknown')}_h{row.get('horizon_best_portal', '')}"


def engine_action(row: pd.Series) -> str:
    status = row["engine_status"]
    if status == "engine_validated":
        return "include as independent product/category engine; push size when signal clears threshold"
    if status == "engine_conditional":
        return "gate by product-specific threshold/regime; include only in exploratory candidate or with small cap"
    if status == "engine_anchor_only":
        return "use as anchor/signal only; do not trade standalone"
    return "exclude from candidates 26-30 unless a new specialized engine is discovered"


def failure_reason(row: pd.Series) -> str:
    if row["engine_status"] == "engine_validated":
        return "validated by existing integrated attribution or new portal/full replay"
    if row["engine_status"] == "engine_conditional":
        if float(row.get("best_candidate_pnl_full", 0.0)) <= 0:
            return "portal-positive or proxy-positive but weak full-history support"
        return "positive but too small/fragile for standalone confidence"
    if row["engine_status"] == "engine_anchor_only":
        return "prior probes too weak; potential use as category/semantic anchor"
    return "tested momentum/reversal/breakout/mean-reversion/category/factor/lead-lag/microstructure families; no executable replay support"


def candidate_role(row: pd.Series) -> str:
    p = row["product"]
    if row["category"] == "PEBBLES":
        return "all candidates: core PEBBLES engine"
    if p in {"OXYGEN_SHAKE_GARLIC", "PANEL_4X4"}:
        return "new engine for candidate 26/30"
    if row["engine_status"] == "engine_validated":
        return "preserve/add in clean multi-engine branch"
    if p in {"MICROCHIP_SQUARE", "MICROCHIP_TRIANGLE", "MICROCHIP_RECTANGLE", "UV_VISOR_RED", "TRANSLATOR_GRAPHITE_MIST", "SLEEP_POD_POLYESTER", "ROBOT_MOPPING"}:
        return "exploratory high-upside gated engine"
    if row["engine_status"] == "engine_conditional":
        return "only in aggressive exploratory branch"
    return "exclude"


def write_outputs(engine_table: pd.DataFrame, probes: pd.DataFrame, signals: pd.DataFrame) -> None:
    ME_OUT.mkdir(parents=True, exist_ok=True)
    engine_table.to_csv(ME_OUT / "multi_engine_product_engine_table.csv", index=False)
    probes.to_csv(ME_OUT / "multi_engine_probe_score_table.csv", index=False)
    oracle = engine_table[
        [
            "product",
            "category",
            "engine_status",
            "portal_oracle_h1",
            "full_oracle_h1",
            "best_candidate_pnl_portal",
            "best_candidate_pnl_full",
            "best_probe_product_pnl",
            "oracle_capture_portal",
            "largest_gap",
        ]
    ].sort_values("portal_oracle_h1", ascending=False)
    oracle.to_csv(ME_OUT / "multi_engine_oracle_capture_table.csv", index=False)
    signals.to_csv(ME_OUT / "multi_engine_engine_family_results.csv", index=False)
    write_summary(engine_table, probes)
    write_category_plan(engine_table)
    write_candidate_plan(engine_table, probes)


def write_summary(table: pd.DataFrame, probes: pd.DataFrame) -> None:
    counts = table["engine_status"].value_counts().to_dict()
    lines = [
        "# Multi-Engine Edge Expansion Summary",
        "",
        "This phase tested product/category-specific engines before final integration. It did not create candidates 26-30, did not create iterative files, and did not modify candidates 23/24/25.",
        "",
        "## Status Counts",
        "",
    ]
    for key in ["engine_validated", "engine_conditional", "engine_anchor_only", "engine_not_found_yet"]:
        lines.append(f"- `{key}`: `{counts.get(key, 0)}`")
    lines += ["", "## New Probe Results", ""]
    for _, row in probes.sort_values("portal_kevin", ascending=False).iterrows():
        lines.append(
            f"- `{row['probe']}`: portal K/X `{row['portal_kevin']}` / `{row['portal_xeeshan']}`, "
            f"full K/X `{row['full_kevin']}` / `{row['full_xeeshan']}`, product PnL `{row['portal_product_pnls']}`."
        )
    lines += ["", "## Validated Engines", ""]
    for _, row in table[table["engine_status"].eq("engine_validated")].sort_values("portal_oracle_h1", ascending=False).iterrows():
        lines.append(
            f"- `{row['product']}` ({row['category']}): `{row['best_engine']}`, portal oracle `{row['portal_oracle_h1']:.0f}`, "
            f"known/probe portal `{max(row['best_candidate_pnl_portal'], row['best_probe_product_pnl']):.0f}`, role `{row['candidate_26_30_role']}`."
        )
    lines += ["", "## High-Potential Still Weak", ""]
    weak = table[table["engine_status"].isin(["engine_conditional", "engine_not_found_yet"])].sort_values("portal_oracle_h1", ascending=False).head(18)
    for _, row in weak.iterrows():
        lines.append(
            f"- `{row['product']}` ({row['category']}): status `{row['engine_status']}`, portal oracle `{row['portal_oracle_h1']:.0f}`, "
            f"engine `{row['best_engine']}`, risk `{row['failure_or_risk']}`."
        )
    lines += [
        "",
        "## Main Conclusion",
        "",
        "The next candidate batch should be multi-engine. The clean additions are `OXYGEN_SHAKE_GARLIC` and `PANEL_4X4`; the highest-upside but fragile engines remain MICROCHIP shape names, selected SLEEP/TRANSLATOR/ROBOT legs, and UV red/orange. SNACKPACK still has no executable engine.",
    ]
    (ME_OUT / "multi_engine_edge_expansion_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_category_plan(table: pd.DataFrame) -> None:
    lines = ["# Multi-Engine Category Plan", ""]
    for category, part in table.groupby("category"):
        val = part[part["engine_status"].eq("engine_validated")]["product"].tolist()
        cond = part[part["engine_status"].eq("engine_conditional")]["product"].tolist()
        missing = part[part["engine_status"].eq("engine_not_found_yet")]["product"].tolist()
        lines.append(f"## {category}")
        lines.append("")
        lines.append(f"- Validated engines: {', '.join(f'`{p}`' for p in val) or 'none'}.")
        lines.append(f"- Conditional engines: {', '.join(f'`{p}`' for p in cond) or 'none'}.")
        lines.append(f"- Exclude/missing: {', '.join(f'`{p}`' for p in missing) or 'none'}.")
        best = part.sort_values("portal_oracle_h1", ascending=False).iloc[0]
        lines.append(f"- Category plan: strongest potential is `{best['product']}` with portal oracle `{best['portal_oracle_h1']:.0f}`; use `{best['best_engine']}` only if status is not missing.")
        lines.append("")
    (ME_OUT / "multi_engine_category_plan.md").write_text("\n".join(lines), encoding="utf-8")


def write_candidate_plan(table: pd.DataFrame, probes: pd.DataFrame) -> None:
    lines = [
        "# Multi-Engine Candidate 26-30 Plan",
        "",
        "Do not create these files until explicitly instructed. These are intended as competition-grade multi-engine candidates, not parameter tweaks.",
        "",
        "## Candidate 26: Clean New Validated Additions",
        "",
        "- Base: candidate 25 architecture.",
        "- Include: PEBBLES core, `UV_VISOR_ORANGE`, `ROBOT_IRONING`, `MICROCHIP_OVAL`, `OXYGEN_SHAKE_GARLIC`, `PANEL_4X4`, and existing `SLEEP_POD_COTTON` only with the safer candidate 25 style rather than the standalone 200-tick probe.",
        "- Gate/exclude: do not include portal-fragile `UV_VISOR_RED` yet.",
        "- Expected impact: add roughly `+9k` to `+12k` portal before interactions if OXYGEN/PANEL do not conflict; full should improve because OXYGEN full replay was strong and PANEL full was mildly positive.",
        "- Validation: portal replay must beat candidate 25 and full must stay above `156k`.",
        "",
        "## Candidate 27: High-Upside MICROCHIP Specialist",
        "",
        "- Base: candidate 23/25 hybrid.",
        "- Include MICROCHIP-specific engines for `SQUARE`, `TRIANGLE`, `RECTANGLE`, `OVAL` with separate shape/breakout/reversion thresholds and product caps.",
        "- Treat `MICROCHIP_CIRCLE` as anchor/exclude, not a traded leg.",
        "- Expected impact: highest oracle upside, but portal-fragile; this is the aggressive learning branch.",
        "- Validation: product attribution must show MICROCHIP positive both portal and full; kill if `SQUARE` repeats negative full-history attribution.",
        "",
        "## Candidate 28: Robust Full-History Multi-Engine",
        "",
        "- Base: candidate 23.",
        "- Include full-history-positive engines: PEBBLES, `GALAXY_SOUNDS_PLANETARY_RINGS`, `ROBOT_IRONING`, `OXYGEN_SHAKE_EVENING_BREATH`, `MICROCHIP_TRIANGLE`, `SLEEP_POD_SUEDE`, `UV_VISOR_AMBER`, plus new `OXYGEN_SHAKE_GARLIC`.",
        "- Exclude portal-only fragile legs unless separately gated.",
        "- Expected impact: best hidden-final robustness; portal may trail candidate 24 but should exceed candidate 16.",
        "- Validation: full replay above candidate 23 and portal above `37k`.",
        "",
        "## Candidate 29: Portal-Upside Multi-Engine",
        "",
        "- Base: candidate 24.",
        "- Include unresolved portal engines plus new `PANEL_4X4`, `OXYGEN_SHAKE_GARLIC`, and optionally `UV_VISOR_RED` with hard adverse/full-history gate.",
        "- Include `TRANSLATOR_GRAPHITE_MIST`, `SLEEP_POD_POLYESTER`, `PANEL_2X4`, `ROBOT_MOPPING`, `TRANSLATOR_VOID_BLUE` as independent engines, not one shared basket.",
        "- Expected impact: highest portal-window upside; highest overfit risk.",
        "- Validation: portal replay must beat `41.8k`; full must not collapse below `120k`.",
        "",
        "## Candidate 30: Full Multi-Engine Portfolio",
        "",
        "- Base: candidate 25.",
        "- Include every validated engine and only the conditional engines with positive attribution or strong markout: `MICROCHIP_TRIANGLE`, `GALAXY_SOUNDS_PLANETARY_RINGS`, `SLEEP_POD_POLYESTER`, `TRANSLATOR_VOID_BLUE`, `ROBOT_MOPPING`, `UV_VISOR_AMBER`.",
        "- Exclude current missing products, especially `ROBOT_DISHES`, `SNACKPACK_*`, weak PANEL small sizes, and toxic GALAXY/TRANSLATOR names.",
        "- Expected impact: balanced attempt to move from ~39k portal toward 50k+ while preserving full-history.",
        "- Validation: beat candidate 25 on portal and full, with product attribution not dependent on one fragile product.",
        "",
        "## Engines To Exclude Until New Evidence",
        "",
    ]
    exclude = table[table["engine_status"].eq("engine_not_found_yet")]["product"].tolist()
    lines.append(", ".join(f"`{p}`" for p in exclude))
    lines += [
        "",
        "## Exact Next Validation",
        "",
        "For each candidate, run Kevin/Xeeshan portal replay first, then full replay for candidates above candidate 25 portal or with new high-upside engines. Attribute product PnL after every run before official submission.",
    ]
    (ME_OUT / "multi_engine_candidate_26_30_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-full", action="store_true", help="Run new full Kevin/Xeeshan backtests for very strong portal probes.")
    args = parser.parse_args()
    ME_OUT.mkdir(parents=True, exist_ok=True)
    edge, signals, cls, attr = load_tables()
    probes = score_probes(run_full=args.run_full)
    engine_table = build_engine_table(edge, signals, cls, attr, probes)
    write_outputs(engine_table, probes, signals)


if __name__ == "__main__":
    main()
