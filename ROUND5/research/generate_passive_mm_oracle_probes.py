from __future__ import annotations

import importlib.util
import pprint
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = ROOT / "ROUND5" / "research" / "probes" / "150k_exec"
ROBUST_BASE = PROBE_DIR / "probe_c35_anchor_both_micro_uv_conservative.py"
PORTAL_BASE = PROBE_DIR / "probe_increment_vanilla_micro_uv_loose.py"


def load_trader(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module.Trader


def replace_assignment(text: str, name: str, value) -> str:
    rendered = pprint.pformat(value, width=120, sort_dicts=False)
    pattern = rf"(?m)^    {name} = .*$"
    if "\n" in rendered:
        pattern = rf"(?ms)^    {name} = .*?(?=^    [A-Z_]+ = |^    def )"
        rendered = f"    {name} = " + rendered.replace("\n", "\n    ") + "\n"
    else:
        rendered = f"    {name} = {rendered}"
    updated, count = re.subn(pattern, rendered, text, count=1)
    if count != 1:
        raise RuntimeError(f"Failed to replace {name}")
    return updated


PASSIVE_MM_METHODS = r'''
    def run_passive_mm(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        for product, cfg in self.PASSIVE_MM_CONFIG.items():
            mode, lookback, edge, size, inv_skew, min_spread = cfg
            book = self.book(state, product)
            if not book or book["spread"] < min_spread:
                continue
            hist = self.push(cache, "mm_" + product, book["mid"], max(260, lookback + 80))
            if len(hist) <= lookback + 3:
                continue
            pos = state.position.get(product, 0)
            fair = self.mm_fair(mode, hist, lookback)
            fair -= inv_skew * pos
            orders = self.trade_passive_mm(product, book, pos, fair, edge, int(size))
            if not orders:
                continue
            if self.PASSIVE_MM_OVERRIDE or product not in result:
                result[product] = orders

    def mm_fair(self, mode: str, hist: List[float], lookback: int) -> float:
        if mode == "rolling":
            w = hist[-lookback:]
            return sum(w) / len(w)
        if mode == "trend":
            return hist[-1] + 0.35 * (hist[-1] - hist[-1 - lookback])
        if mode == "revert":
            w = hist[-lookback:]
            return hist[-1] - 0.35 * (hist[-1] - sum(w) / len(w))
        return hist[-1]

    def trade_passive_mm(self, product: str, book: dict, position: int, fair: float, edge: float, size: int) -> List[Order]:
        orders: List[Order] = []
        bid_px = self.improve_bid(book)
        ask_px = self.improve_ask(book)
        bid_edge = fair - bid_px
        ask_edge = ask_px - fair
        if bid_edge >= edge and position < self.LIMIT:
            qty = min(size, self.LIMIT - position)
            if qty > 0:
                orders.append(Order(product, int(bid_px), int(qty)))
        if ask_edge >= edge and position > -self.LIMIT:
            qty = min(size, self.LIMIT + position)
            if qty > 0:
                orders.append(Order(product, int(ask_px), int(-qty)))
        return self.ensure_limit(product, position, orders)

'''


def write_probe(name: str, base_text: str, base_signal: dict, mm_config: dict, override: bool = False, remove_signals: set[str] | None = None) -> None:
    signal = dict(base_signal)
    for product in remove_signals or set():
        signal.pop(product, None)
    text = replace_assignment(base_text, "SIGNAL_CONFIG", signal)
    attrs = (
        f"    PASSIVE_MM_CONFIG = {pprint.pformat(mm_config, width=120, sort_dicts=False)}\n"
        f"    PASSIVE_MM_OVERRIDE = {bool(override)}\n"
    )
    text = text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    text = text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n        self.run_passive_mm(state, cache, result)\n", 1)
    text = text.replace("    def fit_predict", PASSIVE_MM_METHODS + "    def fit_predict", 1)
    text = text.replace("class Trader:", f"# Temporary passive-fill oracle probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def main() -> None:
    robust_text = ROBUST_BASE.read_text(encoding="utf-8")
    portal_text = PORTAL_BASE.read_text(encoding="utf-8")
    robust_cls = load_trader(ROBUST_BASE)
    portal_cls = load_trader(PORTAL_BASE)
    robust_sig = dict(robust_cls.SIGNAL_CONFIG)
    portal_sig = dict(portal_cls.SIGNAL_CONFIG)

    # Config tuple: mode, lookback, edge_floor, quote_size, inventory_skew, min_spread.
    panel_mm = {
        "PANEL_1X2": ("rolling", 120, 1.4, 4, 0.55, 3),
        "PANEL_1X4": ("rolling", 120, 1.4, 4, 0.55, 3),
        "PANEL_2X2": ("rolling", 120, 1.5, 4, 0.55, 3),
        "PANEL_2X4": ("rolling", 120, 1.3, 5, 0.50, 3),
        "PANEL_4X4": ("rolling", 120, 1.6, 4, 0.60, 3),
    }
    sleep_mm = {
        "SLEEP_POD_COTTON": ("rolling", 160, 1.5, 4, 0.55, 3),
        "SLEEP_POD_POLYESTER": ("rolling", 160, 1.4, 4, 0.50, 3),
        "SLEEP_POD_SUEDE": ("rolling", 160, 1.3, 5, 0.50, 3),
        "SLEEP_POD_LAMB_WOOL": ("rolling", 160, 1.4, 4, 0.55, 3),
        "SLEEP_POD_NYLON": ("rolling", 160, 1.5, 4, 0.55, 3),
    }
    trans_gal_mm = {
        "TRANSLATOR_GRAPHITE_MIST": ("rolling", 160, 1.5, 4, 0.55, 3),
        "TRANSLATOR_VOID_BLUE": ("rolling", 160, 1.5, 4, 0.55, 3),
        "TRANSLATOR_ASTRO_BLACK": ("rolling", 160, 1.4, 4, 0.50, 3),
        "TRANSLATOR_SPACE_GRAY": ("rolling", 160, 1.4, 5, 0.50, 3),
        "GALAXY_SOUNDS_PLANETARY_RINGS": ("rolling", 160, 1.5, 4, 0.55, 3),
        "GALAXY_SOUNDS_SOLAR_WINDS": ("rolling", 160, 1.5, 4, 0.55, 3),
        "GALAXY_SOUNDS_DARK_MATTER": ("rolling", 160, 1.5, 4, 0.55, 3),
        "GALAXY_SOUNDS_BLACK_HOLES": ("rolling", 160, 1.4, 4, 0.50, 3),
        "GALAXY_SOUNDS_SOLAR_FLAMES": ("rolling", 160, 1.5, 4, 0.55, 3),
    }
    oxygen_snack_mm = {
        "OXYGEN_SHAKE_MORNING_BREATH": ("rolling", 160, 1.4, 4, 0.50, 3),
        "OXYGEN_SHAKE_EVENING_BREATH": ("rolling", 160, 1.4, 4, 0.50, 3),
        "OXYGEN_SHAKE_MINT": ("rolling", 160, 1.4, 4, 0.50, 3),
        "OXYGEN_SHAKE_CHOCOLATE": ("rolling", 160, 1.4, 4, 0.50, 3),
        "OXYGEN_SHAKE_GARLIC": ("rolling", 160, 1.5, 4, 0.55, 3),
        "SNACKPACK_RASPBERRY": ("rolling", 160, 1.5, 3, 0.60, 3),
        "SNACKPACK_STRAWBERRY": ("rolling", 160, 1.5, 3, 0.60, 3),
        "SNACKPACK_CHOCOLATE": ("rolling", 160, 1.4, 3, 0.55, 3),
        "SNACKPACK_VANILLA": ("rolling", 160, 1.4, 3, 0.55, 3),
        "SNACKPACK_PISTACHIO": ("rolling", 160, 1.5, 3, 0.60, 3),
    }
    micro_mm = {
        "MICROCHIP_OVAL": ("rolling", 160, 1.5, 4, 0.55, 3),
        "MICROCHIP_SQUARE": ("rolling", 160, 1.5, 4, 0.55, 3),
        "MICROCHIP_RECTANGLE": ("rolling", 160, 1.5, 4, 0.55, 3),
        "MICROCHIP_CIRCLE": ("rolling", 160, 1.6, 3, 0.60, 3),
    }
    all_nonrobot = {**panel_mm, **sleep_mm, **trans_gal_mm, **oxygen_snack_mm, **micro_mm}
    sets = {
        "panel": panel_mm,
        "sleep": sleep_mm,
        "trans_gal": trans_gal_mm,
        "oxygen_snack": oxygen_snack_mm,
        "micro": micro_mm,
        "all_nonrobot": all_nonrobot,
    }

    for suffix, cfg in sets.items():
        products = set(cfg)
        write_probe(f"probe_mm_robust_skip_{suffix}", robust_text, robust_sig, cfg, False, set())
        write_probe(f"probe_mm_portal_skip_{suffix}", portal_text, portal_sig, cfg, False, set())
        write_probe(f"probe_mm_robust_replace_{suffix}", robust_text, robust_sig, cfg, True, products)
        write_probe(f"probe_mm_portal_replace_{suffix}", portal_text, portal_sig, cfg, True, products)

    print(f"Wrote passive MM probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
