from __future__ import annotations

import csv
import json
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ROUND5" / "research" / "outputs"

BASE_PATH = ROOT / "ROUND5" / "research" / "score_unresolved_individual_products.py"
spec = importlib.util.spec_from_file_location("base_unresolved_individual", BASE_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

CONFIG = {
    "TRANSLATOR_SPACE_GRAY": ("reversal", 100, 0.95),
    "GALAXY_SOUNDS_SOLAR_WINDS": ("momentum", 100, 0.95),
    "UV_VISOR_ORANGE": ("reversal", 100, 0.95),
    "GALAXY_SOUNDS_DARK_MATTER": ("reversal", 100, 0.95),
    "TRANSLATOR_ASTRO_BLACK": ("reversal", 50, 0.95),
    "MICROCHIP_RECTANGLE": ("reversal", 100, 0.95),
    "TRANSLATOR_VOID_BLUE": ("reversal", 50, 0.95),
    "SLEEP_POD_POLYESTER": ("reversal", 100, 0.95),
    "PANEL_2X4": ("momentum", 50, 0.95),
    "ROBOT_MOPPING": ("momentum", 100, 0.95),
    "SLEEP_POD_NYLON": ("momentum", 100, 0.95),
    "SLEEP_POD_LAMB_WOOL": ("momentum", 50, 0.95),
    "SLEEP_POD_COTTON": ("momentum", 100, 0.95),
    "TRANSLATOR_GRAPHITE_MIST": ("reversal", 100, 0.95),
}


def fmt(value):
    return "" if value is None else f"{float(value):.2f}"


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    rows = []
    raw = {}
    for product, (mode, lookback, threshold) in CONFIG.items():
        print(f"Alt individual portal probe {product}...")
        strategy = base.write_strategy(product, mode, lookback, threshold)
        raw[product] = {"kevin": base.run_tool("kevin", strategy, config), "xeeshan": base.run_tool("xeeshan", strategy, config)}
        rows.append({"Product": product, "Mode": mode, "Lookback": lookback, "Threshold": threshold, "Portal Window Kevin": fmt(raw[product]["kevin"]["profit"]), "Portal Window Xeeshan": fmt(raw[product]["xeeshan"]["profit"])})
    (OUT / "unresolved_individual_alt_probe_raw.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    with (OUT / "unresolved_individual_alt_probe_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Product", "Mode", "Lookback", "Threshold", "Portal Window Kevin", "Portal Window Xeeshan"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
