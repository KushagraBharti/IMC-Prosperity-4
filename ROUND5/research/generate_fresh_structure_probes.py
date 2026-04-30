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


LEAD_LAG_METHODS = r'''
    def run_lead_lag(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for product, cfg in self.LEAD_LAG_CONFIG.items():
            leader, lookback, threshold, weight, sign, style = cfg
            book = self.book(state, product)
            leader_book = self.book(state, leader)
            if not book or not leader_book:
                continue
            leader_hist = self.push(cache, "ll_" + leader, leader_book["mid"], max(260, lookback + 150))
            own_hist = self.push(cache, "llo_" + product, book["mid"], max(260, lookback + 150))
            if len(leader_hist) <= lookback + 5 or len(own_hist) <= 6:
                continue
            leader_move = (leader_hist[-1] - leader_hist[-1 - lookback]) / max(self.vol(leader_hist[-150:]), 1.0)
            own_short = (own_hist[-1] - own_hist[-6]) / max(self.vol(own_hist[-80:]), 1.0)
            signal = sign * leader_move - 0.18 * own_short
            signal += 0.05 * book["imb"]
            if abs(signal) >= threshold:
                scored.append((abs(signal) * weight, product, book, signal, threshold, style))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, signal, threshold, style in scored[: self.MAX_LEAD_LAG_PRODUCTS]:
            orders = self.trade_lead_lag(product, book, state.position.get(product, 0), signal, threshold, style)
            if orders:
                result[product] = orders

    def trade_lead_lag(self, product: str, book: dict, position: int, signal: float, threshold: float, style: str) -> List[Order]:
        intensity = min(1.0, max(0.0, (abs(signal) - threshold) / 1.6))
        target = int(round((self.LIMIT if signal > 0 else -self.LIMIT) * intensity))
        delta = target - position
        if delta > 0:
            price = book["ask"] if style == "hybrid" and abs(signal) > threshold + 1.1 else self.improve_bid(book)
            return self.ensure_limit(product, position, [Order(product, int(price), int(delta))])
        if delta < 0:
            price = book["bid"] if style == "hybrid" and abs(signal) > threshold + 1.1 else self.improve_ask(book)
            return self.ensure_limit(product, position, [Order(product, int(price), int(delta))])
        return []

'''


CURVE_METHODS = r'''
    def run_semantic_curves(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for group_name, spec in self.SEMANTIC_CURVES.items():
            products, x_map, product_cfg = spec
            books = {product: self.book(state, product) for product in products}
            if any(book is None for book in books.values()):
                continue
            mids = {product: books[product]["mid"] for product in products}
            for product in products:
                if product not in product_cfg:
                    continue
                peers = [p for p in products if p != product]
                fair = self.fit_predict([x_map[p] for p in peers], [mids[p] for p in peers], x_map[product])
                residual = mids[product] - fair
                hist = self.push(cache, "sc_" + product, residual, 260)
                if len(hist) < 70:
                    continue
                center = sum(hist[-220:]) / len(hist[-220:])
                sigma = self.std(hist[-160:], 4.0)
                z = (residual - center) / max(sigma, 1.0)
                threshold, weight, style = product_cfg[product]
                if abs(z) >= threshold:
                    scored.append((abs(z) * weight, product, books[product], z, threshold, sigma, style))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, z, threshold, sigma, style in scored[: self.MAX_SEMANTIC_CURVE_PRODUCTS]:
            orders = self.trade_semantic_curve(product, book, state.position.get(product, 0), z, threshold, sigma, style)
            if orders:
                result[product] = orders

    def trade_semantic_curve(self, product: str, book: dict, position: int, z: float, threshold: float, sigma: float, style: str) -> List[Order]:
        target = -self.LIMIT if z > 0 else self.LIMIT
        intensity = min(1.0, max(0.0, (abs(z) - threshold) / 1.7))
        delta = int(round(target * intensity)) - position
        if delta > 0:
            price = book["ask"] if style == "hybrid" and abs(z) > threshold + 1.2 and book["spread"] <= max(7, 0.35 * sigma) else self.improve_bid(book)
            return self.ensure_limit(product, position, [Order(product, int(price), int(delta))])
        if delta < 0:
            price = book["bid"] if style == "hybrid" and abs(z) > threshold + 1.2 and book["spread"] <= max(7, 0.35 * sigma) else self.improve_ask(book)
            return self.ensure_limit(product, position, [Order(product, int(price), int(delta))])
        return []

'''


def write_probe(name: str, base_text: str, lead_lag: dict | None = None, curves: dict | None = None, max_ll: int = 8, max_curve: int = 6) -> None:
    text = base_text
    attrs = ""
    run_inserts = ""
    if lead_lag:
        attrs += f"    LEAD_LAG_CONFIG = {pprint.pformat(lead_lag, width=120, sort_dicts=False)}\n"
        attrs += f"    MAX_LEAD_LAG_PRODUCTS = {max_ll}\n"
        run_inserts += "        self.run_lead_lag(state, cache, result)\n"
    if curves:
        attrs += f"    SEMANTIC_CURVES = {pprint.pformat(curves, width=120, sort_dicts=False)}\n"
        attrs += f"    MAX_SEMANTIC_CURVE_PRODUCTS = {max_curve}\n"
        run_inserts += "        self.run_semantic_curves(state, cache, result)\n"
    text = text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    text = text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n" + run_inserts, 1)
    methods = ""
    if lead_lag:
        methods += LEAD_LAG_METHODS
    if curves:
        methods += CURVE_METHODS
    text = text.replace("    def book", methods + "    def book", 1)
    text = text.replace("class Trader:", f"# Temporary fresh structural probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def main() -> None:
    robust_text = ROBUST_BASE.read_text(encoding="utf-8")
    portal_text = PORTAL_BASE.read_text(encoding="utf-8")
    load_trader(ROBUST_BASE)
    load_trader(PORTAL_BASE)

    panel_ll = {
        "PANEL_1X2": ("PANEL_4X4", 100, 0.92, 0.80, 1.0, "passive"),
        "PANEL_1X4": ("PANEL_4X4", 100, 0.90, 0.90, 1.0, "passive"),
        "PANEL_2X2": ("PANEL_4X4", 100, 0.92, 0.85, 1.0, "passive"),
        "PANEL_2X4": ("PANEL_4X4", 100, 0.86, 1.15, 1.0, "passive"),
    }
    sleep_ll = {
        "SLEEP_POD_POLYESTER": ("SLEEP_POD_COTTON", 100, 0.92, 0.95, -1.0, "passive"),
        "SLEEP_POD_SUEDE": ("SLEEP_POD_COTTON", 100, 0.90, 1.05, -1.0, "passive"),
        "SLEEP_POD_LAMB_WOOL": ("SLEEP_POD_COTTON", 200, 0.90, 0.95, 1.0, "passive"),
        "SLEEP_POD_NYLON": ("SLEEP_POD_COTTON", 100, 0.92, 0.85, -1.0, "passive"),
    }
    trans_galaxy_ll = {
        "TRANSLATOR_GRAPHITE_MIST": ("TRANSLATOR_SPACE_GRAY", 200, 0.82, 1.00, 1.0, "passive"),
        "TRANSLATOR_VOID_BLUE": ("TRANSLATOR_SPACE_GRAY", 200, 0.86, 0.90, -1.0, "passive"),
        "TRANSLATOR_ASTRO_BLACK": ("TRANSLATOR_SPACE_GRAY", 200, 0.84, 0.95, 1.0, "passive"),
        "GALAXY_SOUNDS_SOLAR_WINDS": ("GALAXY_SOUNDS_PLANETARY_RINGS", 200, 0.86, 0.85, 1.0, "passive"),
        "GALAXY_SOUNDS_DARK_MATTER": ("GALAXY_SOUNDS_PLANETARY_RINGS", 100, 0.90, 0.90, 1.0, "passive"),
        "GALAXY_SOUNDS_BLACK_HOLES": ("GALAXY_SOUNDS_PLANETARY_RINGS", 100, 0.90, 0.90, -1.0, "passive"),
        "GALAXY_SOUNDS_SOLAR_FLAMES": ("GALAXY_SOUNDS_PLANETARY_RINGS", 200, 0.90, 0.85, -1.0, "passive"),
    }
    oxygen_snack_ll = {
        "OXYGEN_SHAKE_MORNING_BREATH": ("OXYGEN_SHAKE_GARLIC", 100, 0.86, 1.00, 1.0, "passive"),
        "OXYGEN_SHAKE_EVENING_BREATH": ("OXYGEN_SHAKE_GARLIC", 100, 0.90, 0.85, -1.0, "passive"),
        "OXYGEN_SHAKE_MINT": ("OXYGEN_SHAKE_GARLIC", 200, 0.90, 0.85, -1.0, "passive"),
        "OXYGEN_SHAKE_CHOCOLATE": ("OXYGEN_SHAKE_GARLIC", 200, 0.88, 0.90, -1.0, "passive"),
        "SNACKPACK_RASPBERRY": ("SNACKPACK_STRAWBERRY", 200, 0.90, 0.80, 1.0, "passive"),
        "SNACKPACK_CHOCOLATE": ("SNACKPACK_VANILLA", 200, 0.90, 0.80, 1.0, "passive"),
        "SNACKPACK_PISTACHIO": ("SNACKPACK_STRAWBERRY", 200, 0.92, 0.70, 1.0, "passive"),
    }
    panel_curve = {
        "PANEL": (
            ["PANEL_1X2", "PANEL_1X4", "PANEL_2X2", "PANEL_2X4", "PANEL_4X4"],
            {"PANEL_1X2": 2.0, "PANEL_1X4": 4.0, "PANEL_2X2": 4.2, "PANEL_2X4": 8.0, "PANEL_4X4": 16.0},
            {
                "PANEL_1X2": (1.15, 0.75, "passive"),
                "PANEL_1X4": (1.10, 0.85, "passive"),
                "PANEL_2X2": (1.10, 0.90, "passive"),
                "PANEL_2X4": (1.00, 1.15, "hybrid"),
                "PANEL_4X4": (1.20, 0.80, "passive"),
            },
        )
    }
    sleep_curve = {
        "SLEEP": (
            ["SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON"],
            {"SLEEP_POD_COTTON": 1.0, "SLEEP_POD_POLYESTER": 2.0, "SLEEP_POD_SUEDE": 3.0, "SLEEP_POD_LAMB_WOOL": 4.0, "SLEEP_POD_NYLON": 5.0},
            {
                "SLEEP_POD_POLYESTER": (1.10, 0.95, "passive"),
                "SLEEP_POD_SUEDE": (1.05, 1.05, "passive"),
                "SLEEP_POD_LAMB_WOOL": (1.10, 0.90, "passive"),
                "SLEEP_POD_NYLON": (1.15, 0.80, "passive"),
            },
        )
    }

    structural_sets = {
        "leadlag_panel": (panel_ll, None),
        "leadlag_sleep": (sleep_ll, None),
        "leadlag_trans_galaxy": (trans_galaxy_ll, None),
        "leadlag_oxygen_snack": (oxygen_snack_ll, None),
        "leadlag_all_fresh": ({**panel_ll, **sleep_ll, **trans_galaxy_ll, **oxygen_snack_ll}, None),
        "curve_panel": (None, panel_curve),
        "curve_sleep": (None, sleep_curve),
        "leadlag_curve_panel_sleep": ({**panel_ll, **sleep_ll}, {**panel_curve, **sleep_curve}),
    }

    for suffix, (ll_cfg, curve_cfg) in structural_sets.items():
        write_probe(f"probe_struct_robust_{suffix}", robust_text, ll_cfg, curve_cfg)
        write_probe(f"probe_struct_portal_{suffix}", portal_text, ll_cfg, curve_cfg)

    print(f"Wrote structural probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
