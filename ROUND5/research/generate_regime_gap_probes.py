from __future__ import annotations

import importlib.util
import pprint
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


REGIME_METHODS = r'''
    def run_regime_gap_signals(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for product, cfg in self.REGIME_GAP_CONFIG.items():
            mode, lookback, threshold, weight, style, regime, gate = cfg
            book = self.book(state, product)
            if not book:
                continue
            if product in result and not self.REGIME_GAP_OVERRIDE:
                continue
            if not self.regime_ok(book, regime, gate):
                continue
            hist = self.push(cache, "rg_" + product, book["mid"], max(620, lookback + 180))
            if len(hist) <= lookback + 3:
                continue
            signal = self.signal(mode, hist, lookback)
            signal += 0.10 * book["imb"]
            if abs(signal) >= threshold:
                scored.append((abs(signal) / max(threshold, 0.01) * weight, product, book, signal, threshold, weight, style))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, signal, threshold, weight, style in scored[: self.MAX_REGIME_GAP_PRODUCTS]:
            orders = self.trade_signal(product, book, state.position.get(product, 0), signal, threshold, weight, style)
            if orders:
                result[product] = orders

    def regime_ok(self, book: dict, regime: str, gate: float) -> bool:
        if regime == "imbalance_extreme":
            return abs(book["imb"]) >= gate
        if regime == "imbalance_positive":
            return book["imb"] >= gate
        if regime == "imbalance_negative":
            return book["imb"] <= -gate
        if regime == "spread_low":
            return book["spread"] <= gate
        if regime == "spread_high":
            return book["spread"] >= gate
        return True

'''


def write_probe(name: str, base_text: str, config: dict, override: bool = False, max_products: int = 10) -> None:
    attrs = (
        f"    REGIME_GAP_CONFIG = {pprint.pformat(config, width=120, sort_dicts=False)}\n"
        f"    REGIME_GAP_OVERRIDE = {bool(override)}\n"
        f"    MAX_REGIME_GAP_PRODUCTS = {max_products}\n"
    )
    text = base_text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    text = text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n        self.run_regime_gap_signals(state, cache, result)\n", 1)
    text = text.replace("    def fit_predict", REGIME_METHODS + "    def fit_predict", 1)
    text = text.replace("class Trader:", f"# Temporary regime-gap probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def main() -> None:
    robust_text = ROBUST_BASE.read_text(encoding="utf-8")
    portal_text = PORTAL_BASE.read_text(encoding="utf-8")
    load_trader(ROBUST_BASE)
    load_trader(PORTAL_BASE)

    # Tuple: mode, lookback, threshold, weight, style, regime, gate.
    snack_imb = {
        "SNACKPACK_STRAWBERRY": ("reversal", 200, 0.90, 1.10, "passive", "imbalance_extreme", 0.42),
        "SNACKPACK_RASPBERRY": ("reversal", 200, 0.92, 0.95, "passive", "imbalance_extreme", 0.42),
        "SNACKPACK_PISTACHIO": ("reversal", 200, 0.94, 0.80, "passive", "imbalance_extreme", 0.42),
        "SNACKPACK_CHOCOLATE": ("momentum", 200, 0.92, 0.90, "passive", "spread_low", 10.0),
        "SNACKPACK_VANILLA": ("momentum", 200, 0.98, 0.70, "passive", "spread_low", 10.0),
    }
    uv_sleep_gal = {
        "UV_VISOR_MAGENTA": ("momentum", 50, 0.86, 1.00, "passive", "imbalance_extreme", 0.45),
        "UV_VISOR_YELLOW": ("reversal", 200, 0.88, 0.85, "passive", "spread_low", 11.0),
        "SLEEP_POD_SUEDE": ("reversal", 100, 0.84, 1.15, "passive", "spread_low", 11.0),
        "SLEEP_POD_POLYESTER": ("reversal", 200, 0.88, 1.00, "passive", "imbalance_extreme", 0.42),
        "SLEEP_POD_LAMB_WOOL": ("momentum", 200, 0.86, 0.95, "passive", "imbalance_extreme", 0.42),
        "GALAXY_SOUNDS_BLACK_HOLES": ("reversal", 50, 0.86, 1.00, "passive", "imbalance_extreme", 0.45),
        "GALAXY_SOUNDS_SOLAR_FLAMES": ("reversal", 200, 0.88, 0.90, "passive", "spread_low", 12.0),
    }
    oxygen_spread = {
        "OXYGEN_SHAKE_EVENING_BREATH": ("reversal", 100, 0.84, 1.00, "passive", "spread_low", 12.0),
        "OXYGEN_SHAKE_MINT": ("reversal", 200, 0.88, 0.90, "passive", "spread_low", 12.0),
        "OXYGEN_SHAKE_MORNING_BREATH": ("momentum", 200, 0.86, 0.95, "passive", "spread_low", 12.0),
        "OXYGEN_SHAKE_CHOCOLATE": ("reversal", 200, 0.86, 0.95, "passive", "imbalance_extreme", 0.42),
    }
    strict = {
        k: (v[0], v[1], v[2] + 0.12, max(0.45, v[3] * 0.85), v[4], v[5], v[6] + (0.12 if "imbalance" in v[5] else -2.0))
        for k, v in {**snack_imb, **uv_sleep_gal, **oxygen_spread}.items()
    }
    loose = {
        k: (v[0], v[1], max(0.70, v[2] - 0.08), v[3] * 1.10, v[4], v[5], max(0.30, v[6] - (0.08 if "imbalance" in v[5] else 0.0)))
        for k, v in {**snack_imb, **uv_sleep_gal, **oxygen_spread}.items()
    }
    sets = {
        "snack_regime": snack_imb,
        "uv_sleep_gal_regime": uv_sleep_gal,
        "oxygen_regime": oxygen_spread,
        "all_regime_strict": strict,
        "all_regime_loose": loose,
    }
    for suffix, cfg in sets.items():
        write_probe(f"probe_regime_robust_{suffix}", robust_text, cfg, False, 10)
        write_probe(f"probe_regime_portal_{suffix}", portal_text, cfg, False, 10)

    print(f"Wrote regime gap probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
