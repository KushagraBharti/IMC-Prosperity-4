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


MICRO_FILL_METHODS = r'''
    def run_micro_fill(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for product, cfg in self.MICRO_FILL_CONFIG.items():
            threshold, weight, size, min_spread, style = cfg
            book = self.book(state, product)
            if not book or book["spread"] < min_spread:
                continue
            # Smooth imbalance briefly; raw top-book imbalance is noisy but still online.
            hist = self.push(cache, "imb_" + product, book["imb"], 24)
            smooth = sum(hist[-8:]) / min(len(hist), 8)
            if abs(smooth) < threshold:
                continue
            score = abs(smooth) * weight * min(2.0, max(0.5, book["spread"] / 4.0))
            scored.append((score, product, book, smooth, threshold, int(size), style))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, imb, threshold, size, style in scored[: self.MAX_MICRO_FILL_PRODUCTS]:
            orders = self.trade_micro_fill(product, book, state.position.get(product, 0), imb, threshold, size, style)
            if orders:
                result[product] = orders

    def trade_micro_fill(self, product: str, book: dict, position: int, imb: float, threshold: float, size: int, style: str) -> List[Order]:
        # Positive imbalance means bid-side depth dominates; quote bid expecting favorable fill/markout.
        strong = abs(imb) > threshold + 0.22
        qty = 10 if strong else size
        if imb > 0 and position < self.LIMIT:
            price = self.improve_bid(book) if style == "improve" else book["bid"]
            return self.ensure_limit(product, position, [Order(product, int(price), int(min(qty, self.LIMIT - position)))])
        if imb < 0 and position > -self.LIMIT:
            price = self.improve_ask(book) if style == "improve" else book["ask"]
            return self.ensure_limit(product, position, [Order(product, int(price), int(-min(qty, self.LIMIT + position)))])
        return []

'''


def write_probe(name: str, base_text: str, base_signal: dict, config: dict, override: bool, remove_signals: set[str]) -> None:
    signal = dict(base_signal)
    for product in remove_signals:
        signal.pop(product, None)
    text = replace_assignment(base_text, "SIGNAL_CONFIG", signal)
    attrs = (
        f"    MICRO_FILL_CONFIG = {pprint.pformat(config, width=120, sort_dicts=False)}\n"
        f"    MAX_MICRO_FILL_PRODUCTS = 12\n"
    )
    text = text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    if override:
        text = text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n        self.run_micro_fill(state, cache, result)\n", 1)
    else:
        text = text.replace("        self.run_signals(state, cache, result)\n", "        self.run_micro_fill(state, cache, result)\n        self.run_signals(state, cache, result)\n", 1)
    text = text.replace("    def fit_predict", MICRO_FILL_METHODS + "    def fit_predict", 1)
    text = text.replace("class Trader:", f"# Temporary microstructure fill probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def main() -> None:
    robust_text = ROBUST_BASE.read_text(encoding="utf-8")
    portal_text = PORTAL_BASE.read_text(encoding="utf-8")
    robust_cls = load_trader(ROBUST_BASE)
    portal_cls = load_trader(PORTAL_BASE)
    robust_sig = dict(robust_cls.SIGNAL_CONFIG)
    portal_sig = dict(portal_cls.SIGNAL_CONFIG)

    # Config tuple: imbalance threshold, rank weight, passive size, min spread, style.
    broad = {
        "PANEL_1X2": (0.26, 0.80, 4, 3, "improve"),
        "PANEL_1X4": (0.26, 0.85, 4, 3, "improve"),
        "PANEL_2X2": (0.26, 0.80, 4, 3, "improve"),
        "PANEL_2X4": (0.24, 1.00, 5, 3, "improve"),
        "PANEL_4X4": (0.28, 0.90, 4, 3, "improve"),
        "SLEEP_POD_COTTON": (0.28, 0.85, 4, 3, "improve"),
        "SLEEP_POD_POLYESTER": (0.26, 0.90, 4, 3, "improve"),
        "SLEEP_POD_SUEDE": (0.24, 1.00, 5, 3, "improve"),
        "SLEEP_POD_LAMB_WOOL": (0.26, 0.90, 4, 3, "improve"),
        "SLEEP_POD_NYLON": (0.28, 0.80, 4, 3, "improve"),
        "TRANSLATOR_ASTRO_BLACK": (0.26, 0.95, 4, 3, "improve"),
        "TRANSLATOR_SPACE_GRAY": (0.24, 1.05, 5, 3, "improve"),
        "GALAXY_SOUNDS_BLACK_HOLES": (0.26, 0.95, 4, 3, "improve"),
        "GALAXY_SOUNDS_PLANETARY_RINGS": (0.28, 0.85, 4, 3, "improve"),
        "OXYGEN_SHAKE_GARLIC": (0.26, 1.00, 4, 3, "improve"),
        "OXYGEN_SHAKE_MINT": (0.26, 0.90, 4, 3, "improve"),
        "SNACKPACK_VANILLA": (0.24, 0.90, 4, 3, "improve"),
        "SNACKPACK_CHOCOLATE": (0.24, 0.90, 4, 3, "improve"),
    }
    panels_sleep = {k: v for k, v in broad.items() if k.startswith("PANEL_") or k.startswith("SLEEP_")}
    trans_gal_oxy_snack = {k: v for k, v in broad.items() if k not in panels_sleep}
    conservative = {k: (v[0] + 0.12, v[1], max(2, v[2] - 1), v[3], "join") for k, v in broad.items()}
    aggressive = {k: (max(0.18, v[0] - 0.08), v[1] * 1.1, min(8, v[2] + 2), v[3], "improve") for k, v in broad.items()}

    sets = {
        "fresh_broad": broad,
        "fresh_panel_sleep": panels_sleep,
        "fresh_trans_gal_oxy_snack": trans_gal_oxy_snack,
        "fresh_conservative_join": conservative,
        "fresh_aggressive": aggressive,
    }
    for suffix, cfg in sets.items():
        products = set(cfg)
        write_probe(f"probe_microfill_robust_override_{suffix}", robust_text, robust_sig, cfg, True, products)
        write_probe(f"probe_microfill_portal_override_{suffix}", portal_text, portal_sig, cfg, True, products)

    print(f"Wrote microstructure fill probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
