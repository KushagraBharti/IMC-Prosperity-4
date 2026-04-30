from __future__ import annotations

import ast
import csv
import io
import json
import os
import pprint
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
STRATEGY_DIR = ROUND_DIR / "strategies"
OUTPUT_DIR = ROUND_DIR / "research" / "outputs"
TEMP_DIR = ROUND_DIR / "research" / "temp_candidate_35_36_ablation"
BACKTEST_DIR = OUTPUT_DIR / "backtests" / "candidate_35_36_ablation"
PORTAL_ROOT = OUTPUT_DIR / "official_portal_windows" / "round5_candidate_1"
PRICE_FILE = PORTAL_ROOT / "round5" / "prices_round_5_day_4.csv"


@dataclass
class SimpleDepth:
    buy_orders: dict[int, int] = field(default_factory=dict)
    sell_orders: dict[int, int] = field(default_factory=dict)


@dataclass
class SimpleState:
    order_depths: dict[str, SimpleDepth]
    position: dict[str, int] = field(default_factory=dict)
    traderData: str = ""
    timestamp: int = 0


def class_attrs(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    attrs: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Trader":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    try:
                        attrs[stmt.targets[0].id] = ast.literal_eval(stmt.value)
                    except Exception:
                        pass
    return attrs


def replace_class_attr(text: str, name: str, value: Any) -> str:
    pattern = re.compile(rf"^    {re.escape(name)} = .*?(?=^    [A-Z_][A-Z0-9_]* = |^    def )", re.M | re.S)
    rendered = pprint.pformat(value, width=140, sort_dicts=False)
    rendered = "\n".join("    " + line if i == 0 else "    " + line for i, line in enumerate(rendered.splitlines()))
    replacement = f"    {name} = {rendered.strip()}\n"
    new, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace {name}")
    return new


def make_variant(base: int, name: str, updates: dict[str, Any]) -> Path:
    src = STRATEGY_DIR / f"round5_candidate_{base}.py"
    text = src.read_text(encoding="utf-8")
    attrs = class_attrs(src)
    for attr, value in updates.items():
        if isinstance(value, dict) and isinstance(attrs.get(attr), dict):
            merged = dict(attrs[attr])
            for key, item in value.items():
                if item is None:
                    merged.pop(key, None)
                else:
                    merged[key] = item
            value = merged
        text = replace_class_attr(text, attr, value)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    path = TEMP_DIR / f"{name}.py"
    path.write_text(text, encoding="utf-8")
    return path


def parse_profit(log_path: Path, stdout: str) -> float | None:
    for text in (stdout, log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    if log_path.exists():
        data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
        latest: dict[str, float] = {}
        for row in csv.DictReader(io.StringIO(data.get("activitiesLog", "")), delimiter=";"):
            product = row.get("product")
            if product:
                latest[product] = float(row.get("profit_and_loss") or 0.0)
        return sum(latest.values()) if latest else None
    return None


def run_kevin_portal(path: Path, label: str, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BACKTEST_DIR / f"{label}_kevin_portal.log"
    stdout_path = BACKTEST_DIR / f"{label}_kevin_portal_stdout.txt"
    repo = Path(config["paths"]["kevinBacktesterRepo"])
    python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
    cmd = [
        str(python),
        "-m",
        "prosperity4bt",
        str(path),
        "5-4",
        "--out",
        str(out_path),
        "--data",
        str(PORTAL_ROOT),
        "--match-trades",
        "worse",
        "--no-vis",
        "--no-progress",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=360)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {"returncode": proc.returncode, "profit": parse_profit(out_path, proc.stdout or ""), "log": str(out_path)}


def product_pnl(log_path: Path) -> dict[str, float]:
    data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
    latest: dict[str, float] = {}
    for row in csv.DictReader(io.StringIO(data.get("activitiesLog", "")), delimiter=";"):
        product = row.get("product")
        if product:
            latest[product] = float(row.get("profit_and_loss") or 0.0)
    return latest


def load_strategy(path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module.Trader()


def depth_from_row(row: dict[str, str]) -> SimpleDepth:
    depth = SimpleDepth()
    for i in range(1, 4):
        bp = row.get(f"bid_price_{i}") or ""
        bv = row.get(f"bid_volume_{i}") or ""
        ap = row.get(f"ask_price_{i}") or ""
        av = row.get(f"ask_volume_{i}") or ""
        if bp and bv:
            depth.buy_orders[int(float(bp))] = int(float(bv))
        if ap and av:
            depth.sell_orders[int(float(ap))] = -abs(int(float(av)))
    return depth


def measure_state(path: Path) -> int:
    trader = load_strategy(path)
    trader_data = ""
    max_len = 0
    rows_by_ts: dict[int, dict[str, SimpleDepth]] = {}
    with PRICE_FILE.open("r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            rows_by_ts.setdefault(int(row["timestamp"]), {})[row["product"]] = depth_from_row(row)
    for ts in sorted(rows_by_ts):
        _orders, _conv, trader_data = trader.run(SimpleState(order_depths=rows_by_ts[ts], traderData=trader_data, timestamp=ts))
        max_len = max(max_len, len(trader_data))
    return max_len


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))

    additions = {
        "UV_VISOR_AMBER": ("momentum", 150, 0.75, 0.70, "passive"),
        "ROBOT_LAUNDRY": ("momentum", 100, 1.25, 0.65, "passive"),
        "ROBOT_DISHES": ("momentum", 150, 0.75, 0.65, "passive"),
        "ROBOT_MOPPING": ("momentum", 50, 1.05, 0.75, "passive"),
        "PANEL_2X4": ("momentum", 150, 1.60, 0.55, "passive"),
        "MICROCHIP_TRIANGLE": ("reversal", 50, 0.98, 0.80, "passive"),
        "TRANSLATOR_GRAPHITE_MIST": ("momentum", 100, 1.10, 0.90, "passive"),
        "TRANSLATOR_VOID_BLUE": ("reversal", 100, 1.00, 0.80, "passive"),
        "SLEEP_POD_POLYESTER": ("reversal", 100, 1.00, 0.90, "passive"),
    }

    variants: list[tuple[str, Path, str]] = []
    variants.append(("base33", STRATEGY_DIR / "round5_candidate_33.py", "benchmark"))
    variants.append(("base34", STRATEGY_DIR / "round5_candidate_34.py", "benchmark"))
    variants.append(("probe_33_robot_uv", make_variant(33, "probe_33_robot_uv", {"SIGNAL_CONFIG": {k: additions[k] for k in ["UV_VISOR_AMBER", "ROBOT_LAUNDRY", "ROBOT_DISHES", "ROBOT_MOPPING"]}, "MAX_SIGNAL_PRODUCTS": 28}), "33 + robot/UV amber"))
    variants.append(("probe_33_trans_sleep", make_variant(33, "probe_33_trans_sleep", {"SIGNAL_CONFIG": {k: additions[k] for k in ["TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE", "SLEEP_POD_POLYESTER"]}, "MAX_SIGNAL_PRODUCTS": 27}), "33 + 34 signal branch"))
    variants.append(("probe_33_panel_micro", make_variant(33, "probe_33_panel_micro", {"SIGNAL_CONFIG": {k: additions[k] for k in ["PANEL_2X4", "MICROCHIP_TRIANGLE"]}, "MAX_SIGNAL_PRODUCTS": 26}), "33 + panel2x4/micro triangle"))
    variants.append(("probe_33_all_targeted", make_variant(33, "probe_33_all_targeted", {"SIGNAL_CONFIG": additions, "MAX_SIGNAL_PRODUCTS": 30}), "33 + all targeted 34/31 additions"))

    remove_high_toxic = {
        "SLEEP_POD_LAMB_WOOL": None,
        "MICROCHIP_RECTANGLE": None,
        "PEBBLES_XS": None,
        "PANEL_1X4": None,
        "PANEL_2X2": None,
        "OXYGEN_SHAKE_GARLIC": None,
        "UV_VISOR_MAGENTA": None,
        "SNACKPACK_CHOCOLATE": None,
        "SNACKPACK_VANILLA": None,
    }
    remove_snack_uv = {
        "UV_VISOR_MAGENTA": None,
        "SNACKPACK_CHOCOLATE": None,
        "SNACKPACK_VANILLA": None,
    }
    keep_lineage = {
        "TRANSLATOR_SPACE_GRAY": (220, 0.70, 0.80),
        "GALAXY_SOUNDS_PLANETARY_RINGS": (220, 2.00, 0.75),
        "UV_VISOR_AMBER": (150, 0.75, 0.70),
        "ROBOT_LAUNDRY": (100, 1.25, 0.65),
        "ROBOT_DISHES": (150, 0.75, 0.65),
        "PANEL_4X4": (220, 0.75, 0.60),
        "MICROCHIP_TRIANGLE": (150, 0.95, -0.60),
        "PANEL_2X4": (150, 1.60, 0.55),
    }
    variants.append(("probe_34_no_snack_uvmag", make_variant(34, "probe_34_no_snack_uvmag", {"MOMENTUM_EXTRAS": remove_snack_uv, "MAX_MOMENTUM_EXTRAS": 7}), "34 remove snack/uvmagenta extras"))
    variants.append(("probe_34_keep_lineage", make_variant(34, "probe_34_keep_lineage", {"MOMENTUM_EXTRAS": keep_lineage, "MAX_MOMENTUM_EXTRAS": 7}), "34 keep only 31-lineage momentum extras"))
    variants.append(("probe_34_remove_toxic", make_variant(34, "probe_34_remove_toxic", {"MOMENTUM_EXTRAS": remove_high_toxic, "MAX_MOMENTUM_EXTRAS": 7}), "34 remove likely full-toxic extras"))
    variants.append(("probe_34_no_anchor", make_variant(34, "probe_34_no_anchor", {"ANCHOR_PRODUCTS": set()}), "34 without anchor engine"))

    rows = []
    for label, path, note in variants:
        print(f"Portal probe {label}...", flush=True)
        result = run_kevin_portal(path, label, config)
        log_path = Path(result["log"])
        pnl = product_pnl(log_path) if log_path.exists() else {}
        rows.append(
            {
                "probe": label,
                "note": note,
                "portal_kevin": "" if result["profit"] is None else round(result["profit"], 2),
                "max_state": measure_state(path),
                "top_positive": "; ".join(f"{p}:{v:.0f}" for p, v in sorted(((p, v) for p, v in pnl.items() if v > 0), key=lambda x: x[1], reverse=True)[:8]),
                "top_negative": "; ".join(f"{p}:{v:.0f}" for p, v in sorted(((p, v) for p, v in pnl.items() if v < 0), key=lambda x: x[1])[:6]),
            }
        )
        print(f"  {label}: {rows[-1]['portal_kevin']} state {rows[-1]['max_state']}", flush=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / "candidate_35_36_ablation_probe_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Candidate 35-36 Ablation Probe Scores",
        "",
        "| Probe | Portal Kevin | Max State | Note |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['probe']}` | {row['portal_kevin']} | {row['max_state']} | {row['note']} |")
    (OUTPUT_DIR / "candidate_35_36_ablation_probe_scores.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
