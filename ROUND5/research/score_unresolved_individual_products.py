from __future__ import annotations

import csv
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ROUND5" / "research" / "outputs"
TMP = OUT / "backtests" / "unresolved_individual_tmp"
TMP.mkdir(parents=True, exist_ok=True)

CONFIG = {
    "TRANSLATOR_SPACE_GRAY": ("momentum", 100, 0.95),
    "GALAXY_SOUNDS_SOLAR_WINDS": ("momentum", 100, 0.95),
    "UV_VISOR_ORANGE": ("momentum", 100, 0.95),
    "GALAXY_SOUNDS_DARK_MATTER": ("reversal", 100, 1.00),
    "TRANSLATOR_ASTRO_BLACK": ("reversal", 100, 1.00),
    "MICROCHIP_RECTANGLE": ("momentum", 50, 1.00),
    "TRANSLATOR_VOID_BLUE": ("reversal", 100, 1.00),
    "SLEEP_POD_POLYESTER": ("reversal", 100, 1.00),
    "PANEL_2X4": ("momentum", 50, 1.00),
    "ROBOT_MOPPING": ("momentum", 50, 1.00),
    "SLEEP_POD_NYLON": ("reversal", 100, 1.05),
    "SLEEP_POD_LAMB_WOOL": ("momentum", 100, 1.05),
    "SLEEP_POD_COTTON": ("reversal", 100, 1.05),
    "TRANSLATOR_GRAPHITE_MIST": ("momentum", 100, 1.10),
}

TEMPLATE = r'''
from __future__ import annotations
import json, math
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
    PRODUCT = "__PRODUCT__"
    MODE = "__MODE__"
    LOOKBACK = __LOOKBACK__
    THRESHOLD = __THRESHOLD__
    def run(self, state: TradingState):
        cache = self.load_cache(state.traderData)
        result: Dict[str, List[Order]] = {}
        book = self.book(state, self.PRODUCT)
        if not book:
            return result, 0, json.dumps(cache, separators=(",", ":"))
        hist = self.push(cache, self.PRODUCT, book["mid"], 230)
        if len(hist) <= self.LOOKBACK + 2:
            result[self.PRODUCT] = []
            return result, 0, json.dumps(cache, separators=(",", ":"))
        signal = (hist[-1] - hist[-1 - self.LOOKBACK]) / max(self.vol(hist[-140:]), 1.0)
        if self.MODE == "reversal":
            signal = -signal
        signal += 0.08 * book["imb"]
        result[self.PRODUCT] = self.trade(book, state.position.get(self.PRODUCT, 0), signal)
        return result, 0, json.dumps(cache, separators=(",", ":"))
    def trade(self, book: dict, pos: int, signal: float) -> List[Order]:
        if abs(signal) < self.THRESHOLD:
            return []
        if signal > 0 and pos < self.LIMIT:
            price = min(book["bid"] + 1, book["ask"] - 1) if book["spread"] >= 3 else book["bid"]
            return [Order(self.PRODUCT, price, self.LIMIT - pos if signal > self.THRESHOLD + 0.9 else min(6, self.LIMIT - pos))]
        if signal < 0 and pos > -self.LIMIT:
            price = max(book["ask"] - 1, book["bid"] + 1) if book["spread"] >= 3 else book["ask"]
            return [Order(self.PRODUCT, price, -(self.LIMIT + pos if signal < -self.THRESHOLD - 0.9 else min(6, self.LIMIT + pos)))]
        return []
    def book(self, state: TradingState, product: str):
        d = state.order_depths.get(product)
        if not d or not d.buy_orders or not d.sell_orders:
            return None
        bid, ask = max(d.buy_orders), min(d.sell_orders)
        bv, av = max(0, d.buy_orders[bid]), max(0, -d.sell_orders[ask])
        total = bv + av
        return {"bid": bid, "ask": ask, "mid": (bid + ask) / 2.0, "spread": ask - bid, "imb": 0.0 if total == 0 else (bv - av) / total}
    def push(self, cache: dict, product: str, mid: float, keep: int) -> List[float]:
        hist = cache.get(product, [])
        if not isinstance(hist, list): hist = []
        hist.append(float(mid)); cache[product] = hist[-keep:]; return cache[product]
    def vol(self, hist: List[float]) -> float:
        if len(hist) < 3: return 1.0
        diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
        m = sum(diffs) / len(diffs)
        return max(1.0, math.sqrt(sum((x - m) ** 2 for x in diffs) / len(diffs)))
    def load_cache(self, raw: str) -> dict:
        try: return json.loads(raw) if raw else {}
        except Exception: return {}
'''


def parse_profit(path: Path, stdout: str) -> float | None:
    for text in (stdout, path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    return None


def write_strategy(product: str, mode: str, lookback: int, threshold: float) -> Path:
    path = TMP / f"probe_{product.lower()}.py"
    text = TEMPLATE.replace("__PRODUCT__", product).replace("__MODE__", mode).replace("__LOOKBACK__", str(lookback)).replace("__THRESHOLD__", str(threshold))
    path.write_text(text, encoding="utf-8")
    return path


def run_tool(tool: str, strategy_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    data_root = OUT / "official_portal_windows" / "round5_candidate_1"
    out_path = TMP / f"{strategy_path.stem}_{tool}_portal.log"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5-4", "--out", str(out_path), "--data", str(data_root), "--match-trades", "worse", "--no-vis", "--no-progress"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        cmd = [str(python), "-m", "prosperity4bt", str(strategy_path), "5-4", "--out", str(out_path), "--data", str(data_root), "--match-trades", "all", "--merge-pnl", "--no-progress"]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=180)
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or "")}


def fmt(value: Any) -> str:
    return "" if value is None else f"{float(value):.2f}"


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    rows = []
    raw = {}
    for product, (mode, lookback, threshold) in CONFIG.items():
        print(f"Individual portal probe {product}...")
        strategy = write_strategy(product, mode, lookback, threshold)
        raw[product] = {"kevin": run_tool("kevin", strategy, config), "xeeshan": run_tool("xeeshan", strategy, config)}
        rows.append({"Product": product, "Mode": mode, "Lookback": lookback, "Threshold": threshold, "Portal Window Kevin": fmt(raw[product]["kevin"]["profit"]), "Portal Window Xeeshan": fmt(raw[product]["xeeshan"]["profit"])})
    (OUT / "unresolved_individual_probe_raw.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    with (OUT / "unresolved_individual_probe_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Product", "Mode", "Lookback", "Threshold", "Portal Window Kevin", "Portal Window Xeeshan"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
