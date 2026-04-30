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


def write_probe(name: str, base_text: str, signal_config: dict, max_signal_products: int = 40) -> None:
    text = replace_assignment(base_text, "SIGNAL_CONFIG", signal_config)
    text = replace_assignment(text, "MAX_SIGNAL_PRODUCTS", max_signal_products)
    text = text.replace("class Trader:", f"# Temporary fresh-edge pivot probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


CATEGORY_RESIDUAL_METHODS = r'''
    def run_category_residuals(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for group_name, group_products in self.FRESH_CATEGORY_GROUPS.items():
            books = {product: self.book(state, product) for product in group_products}
            if any(book is None for book in books.values()):
                continue
            mids = {product: books[product]["mid"] for product in group_products}
            for product in group_products:
                if product not in self.FRESH_CATEGORY_PRODUCTS or product in result:
                    continue
                peers = [mids[p] for p in group_products if p != product]
                if not peers:
                    continue
                fair = sum(peers) / len(peers)
                residual = mids[product] - fair
                hist = self.push(cache, "cat_" + product, residual, 260)
                if len(hist) < 70:
                    continue
                center = sum(hist[-220:]) / len(hist[-220:])
                sigma = self.std(hist[-160:], 4.0)
                z = (residual - center) / max(sigma, 1.0)
                threshold, weight, style = self.FRESH_CATEGORY_PRODUCTS[product]
                if abs(z) >= threshold:
                    scored.append((abs(z) * weight, product, books[product], z, threshold, sigma, style))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, z, threshold, sigma, style in scored[: self.MAX_FRESH_CATEGORY_PRODUCTS]:
            orders = self.trade_category_residual(product, book, state.position.get(product, 0), z, threshold, sigma, style)
            if orders:
                result[product] = orders

    def trade_category_residual(self, product: str, book: dict, position: int, z: float, threshold: float, sigma: float, style: str) -> List[Order]:
        # Positive residual = rich versus same-category peers, so sell.
        intensity = min(1.0, max(0.0, (abs(z) - threshold) / 1.8))
        target = int(round((-self.LIMIT if z > 0 else self.LIMIT) * intensity))
        delta = target - position
        if delta > 0:
            price = self.improve_bid(book)
            if style == "hybrid" and abs(z) > threshold + 1.25 and book["ask"] - price <= max(6, 0.35 * sigma):
                price = book["ask"]
            return self.ensure_limit(product, position, [Order(product, int(price), int(delta))])
        if delta < 0:
            price = self.improve_ask(book)
            if style == "hybrid" and abs(z) > threshold + 1.25 and price - book["bid"] <= max(6, 0.35 * sigma):
                price = book["bid"]
            return self.ensure_limit(product, position, [Order(product, int(price), int(delta))])
        return []

'''


def inject_category_residuals(base_text: str, groups: dict, products: dict, max_products: int = 7) -> str:
    attrs = (
        f"    FRESH_CATEGORY_GROUPS = {pprint.pformat(groups, width=120, sort_dicts=False)}\n"
        f"    FRESH_CATEGORY_PRODUCTS = {pprint.pformat(products, width=120, sort_dicts=False)}\n"
        f"    MAX_FRESH_CATEGORY_PRODUCTS = {max_products}\n"
    )
    text = base_text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    text = text.replace(
        "        self.run_signals(state, cache, result)\n",
        "        self.run_signals(state, cache, result)\n        self.run_category_residuals(state, cache, result)\n",
        1,
    )
    text = text.replace("    def book", CATEGORY_RESIDUAL_METHODS + "    def book", 1)
    return text


def write_residual_probe(name: str, base_text: str, signal_config: dict, groups: dict, products: dict, max_products: int = 7) -> None:
    text = inject_category_residuals(base_text, groups, products, max_products)
    write_probe(name, text, signal_config, 42)


def main() -> None:
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    robust_text = ROBUST_BASE.read_text(encoding="utf-8")
    portal_text = PORTAL_BASE.read_text(encoding="utf-8")
    robust_cls = load_trader(ROBUST_BASE)
    portal_cls = load_trader(PORTAL_BASE)
    robust_sig = dict(robust_cls.SIGNAL_CONFIG)
    portal_sig = dict(portal_cls.SIGNAL_CONFIG)

    # Fresh categories only: no new MICROCHIP/UV/anchor/ROBOT changes in this pivot batch.
    sleep_engine = {
        "SLEEP_POD_COTTON": ("momentum", 100, 0.90, 1.10, "passive"),
        "SLEEP_POD_POLYESTER": ("reversal", 100, 0.92, 1.05, "passive"),
        "SLEEP_POD_SUEDE": ("reversal", 100, 0.90, 1.10, "passive"),
        "SLEEP_POD_LAMB_WOOL": ("breakout_low_reversal", 500, 0.92, 0.95, "passive"),
        "SLEEP_POD_NYLON": ("rolling_mean_reversion", 200, 0.92, 0.85, "passive"),
    }

    panel_engine = {
        "PANEL_1X2": ("breakout_low_reversal", 200, 0.88, 0.95, "passive"),
        "PANEL_1X4": ("breakout_low_reversal", 200, 0.88, 0.95, "passive"),
        "PANEL_2X2": ("breakout_low_reversal", 200, 0.92, 0.85, "passive"),
        "PANEL_2X4": ("momentum", 100, 0.82, 1.15, "passive"),
        "PANEL_4X4": ("momentum", 50, 0.72, 1.45, "passive"),
    }

    trans_galaxy_engine = {
        "TRANSLATOR_GRAPHITE_MIST": ("momentum", 100, 1.02, 1.00, "passive"),
        "TRANSLATOR_VOID_BLUE": ("reversal", 100, 0.94, 0.95, "passive"),
        "TRANSLATOR_ASTRO_BLACK": ("momentum", 100, 0.94, 0.95, "passive"),
        "TRANSLATOR_SPACE_GRAY": ("breakout_high", 500, 0.86, 1.20, "passive"),
        "GALAXY_SOUNDS_PLANETARY_RINGS": ("breakout_low_reversal", 200, 0.78, 1.15, "passive"),
        "GALAXY_SOUNDS_DARK_MATTER": ("breakout_high", 200, 0.90, 0.95, "passive"),
        "GALAXY_SOUNDS_SOLAR_FLAMES": ("rolling_mean_reversion", 200, 0.90, 0.90, "passive"),
        "GALAXY_SOUNDS_SOLAR_WINDS": ("rolling_mean_reversion", 200, 0.96, 0.80, "passive"),
        "GALAXY_SOUNDS_BLACK_HOLES": ("reversal", 50, 0.92, 0.90, "passive"),
    }

    oxygen_snack_engine = {
        "OXYGEN_SHAKE_MORNING_BREATH": ("breakout_high", 200, 0.86, 1.05, "passive"),
        "OXYGEN_SHAKE_CHOCOLATE": ("rolling_mean_reversion", 200, 0.90, 0.95, "passive"),
        "OXYGEN_SHAKE_EVENING_BREATH": ("reversal", 100, 0.88, 0.95, "passive"),
        "OXYGEN_SHAKE_MINT": ("breakout_low_reversal", 500, 0.92, 0.85, "passive"),
        "OXYGEN_SHAKE_GARLIC": ("reversal", 200, 0.78, 1.35, "passive"),
        "SNACKPACK_STRAWBERRY": ("reversal", 200, 0.98, 0.80, "passive"),
        "SNACKPACK_RASPBERRY": ("reversal", 200, 1.00, 0.75, "passive"),
        "SNACKPACK_PISTACHIO": ("reversal", 200, 1.00, 0.65, "passive"),
        "SNACKPACK_CHOCOLATE": ("momentum", 200, 0.98, 0.70, "passive"),
        "SNACKPACK_VANILLA": ("momentum", 200, 1.02, 0.65, "passive"),
    }

    fresh_sets = {
        "sleep": sleep_engine,
        "panel": panel_engine,
        "translator_galaxy": trans_galaxy_engine,
        "oxygen_snack": oxygen_snack_engine,
        "sleep_panel": {**sleep_engine, **panel_engine},
        "trans_galaxy_panel": {**trans_galaxy_engine, **panel_engine},
        "all_fresh_no_robot_micro_uv": {**sleep_engine, **panel_engine, **trans_galaxy_engine, **oxygen_snack_engine},
    }

    for suffix, additions in fresh_sets.items():
        write_probe(f"probe_pivot_robust_{suffix}", robust_text, {**robust_sig, **additions}, 42)
        write_probe(f"probe_pivot_portal_{suffix}", portal_text, {**portal_sig, **additions}, 42)

    groups = {
        "SLEEP": ["SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON"],
        "PANEL": ["PANEL_1X2", "PANEL_1X4", "PANEL_2X2", "PANEL_2X4", "PANEL_4X4"],
        "TRANSLATOR": ["TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_SPACE_GRAY", "TRANSLATOR_ECLIPSE_CHARCOAL"],
        "GALAXY": ["GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_WINDS", "GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_SOLAR_FLAMES"],
        "OXYGEN": ["OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC"],
        "SNACK": ["SNACKPACK_RASPBERRY", "SNACKPACK_STRAWBERRY", "SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO"],
    }
    residual_sets = {
        "sleep_curve": (
            {"SLEEP": groups["SLEEP"]},
            {
                "SLEEP_POD_POLYESTER": (1.10, 0.95, "passive"),
                "SLEEP_POD_SUEDE": (1.05, 1.05, "passive"),
                "SLEEP_POD_LAMB_WOOL": (1.10, 0.85, "passive"),
                "SLEEP_POD_NYLON": (1.15, 0.75, "passive"),
            },
        ),
        "panel_curve": (
            {"PANEL": groups["PANEL"]},
            {
                "PANEL_1X2": (1.20, 0.75, "passive"),
                "PANEL_1X4": (1.15, 0.80, "passive"),
                "PANEL_2X2": (1.15, 0.85, "passive"),
                "PANEL_2X4": (1.05, 1.10, "hybrid"),
                "PANEL_4X4": (1.20, 0.80, "passive"),
            },
        ),
        "translator_galaxy_curve": (
            {"TRANSLATOR": groups["TRANSLATOR"], "GALAXY": groups["GALAXY"]},
            {
                "TRANSLATOR_ASTRO_BLACK": (1.10, 0.95, "passive"),
                "TRANSLATOR_SPACE_GRAY": (1.15, 0.90, "passive"),
                "TRANSLATOR_VOID_BLUE": (1.15, 0.80, "passive"),
                "GALAXY_SOUNDS_BLACK_HOLES": (1.10, 0.90, "passive"),
                "GALAXY_SOUNDS_SOLAR_WINDS": (1.15, 0.75, "passive"),
                "GALAXY_SOUNDS_SOLAR_FLAMES": (1.15, 0.75, "passive"),
            },
        ),
        "oxygen_snack_curve": (
            {"OXYGEN": groups["OXYGEN"], "SNACK": groups["SNACK"]},
            {
                "OXYGEN_SHAKE_MINT": (1.10, 0.85, "passive"),
                "OXYGEN_SHAKE_EVENING_BREATH": (1.10, 0.80, "passive"),
                "SNACKPACK_VANILLA": (1.05, 0.90, "passive"),
                "SNACKPACK_CHOCOLATE": (1.05, 0.90, "passive"),
                "SNACKPACK_RASPBERRY": (1.10, 0.75, "passive"),
                "SNACKPACK_PISTACHIO": (1.10, 0.65, "passive"),
            },
        ),
    }
    all_residual_groups = {k: v for item in residual_sets.values() for k, v in item[0].items()}
    all_residual_products = {k: v for item in residual_sets.values() for k, v in item[1].items()}

    for suffix, (group_cfg, product_cfg) in residual_sets.items():
        write_residual_probe(f"probe_pivot_robust_resid_{suffix}", robust_text, robust_sig, group_cfg, product_cfg, 6)
        write_residual_probe(f"probe_pivot_portal_resid_{suffix}", portal_text, portal_sig, group_cfg, product_cfg, 6)
    write_residual_probe("probe_pivot_robust_resid_all_fresh", robust_text, robust_sig, all_residual_groups, all_residual_products, 9)
    write_residual_probe("probe_pivot_portal_resid_all_fresh", portal_text, portal_sig, all_residual_groups, all_residual_products, 9)

    # Oracle-mimic product engines: use the marginal table's best fresh-category families directly.
    # This deliberately changes only non-MICROCHIP/non-UV/non-ROBOT/non-anchor products.
    panel_oracle = {
        "PANEL_1X2": ("momentum", 200, 0.88, 0.85, "passive"),
        "PANEL_1X4": ("momentum", 100, 0.78, 1.05, "passive"),
        "PANEL_2X2": ("momentum", 200, 0.90, 0.80, "passive"),
        "PANEL_2X4": ("momentum", 50, 0.76, 1.25, "passive"),
        "PANEL_4X4": ("momentum", 100, 0.76, 1.15, "passive"),
    }
    trans_galaxy_oracle = {
        "TRANSLATOR_GRAPHITE_MIST": ("momentum", 50, 0.94, 1.00, "passive"),
        "TRANSLATOR_VOID_BLUE": ("reversal", 50, 0.92, 0.95, "passive"),
        "TRANSLATOR_ASTRO_BLACK": ("momentum", 200, 0.92, 0.90, "passive"),
        "TRANSLATOR_SPACE_GRAY": ("momentum", 200, 0.72, 1.25, "passive"),
        "GALAXY_SOUNDS_PLANETARY_RINGS": ("momentum", 100, 0.72, 1.25, "passive"),
        "GALAXY_SOUNDS_DARK_MATTER": ("momentum", 50, 0.92, 0.95, "passive"),
        "GALAXY_SOUNDS_SOLAR_FLAMES": ("reversal", 200, 0.90, 0.95, "passive"),
        "GALAXY_SOUNDS_SOLAR_WINDS": ("momentum", 100, 0.96, 0.80, "passive"),
        "GALAXY_SOUNDS_BLACK_HOLES": ("reversal", 50, 0.92, 0.90, "passive"),
    }
    sleep_oxygen_oracle = {
        "SLEEP_POD_COTTON": ("momentum", 200, 0.84, 1.15, "passive"),
        "SLEEP_POD_POLYESTER": ("reversal", 200, 0.90, 1.05, "passive"),
        "SLEEP_POD_SUEDE": ("reversal", 100, 0.88, 1.10, "passive"),
        "SLEEP_POD_LAMB_WOOL": ("momentum", 200, 0.86, 1.00, "passive"),
        "SLEEP_POD_NYLON": ("reversal", 200, 0.90, 0.85, "passive"),
        "OXYGEN_SHAKE_MORNING_BREATH": ("momentum", 200, 0.88, 0.95, "passive"),
        "OXYGEN_SHAKE_EVENING_BREATH": ("reversal", 100, 0.88, 0.95, "passive"),
        "OXYGEN_SHAKE_MINT": ("reversal", 200, 0.92, 0.80, "passive"),
        "OXYGEN_SHAKE_CHOCOLATE": ("reversal", 200, 0.88, 0.95, "passive"),
        "OXYGEN_SHAKE_GARLIC": ("momentum", 100, 0.78, 1.20, "passive"),
    }
    snack_oracle = {
        "SNACKPACK_STRAWBERRY": ("reversal", 200, 0.92, 1.00, "passive"),
        "SNACKPACK_RASPBERRY": ("reversal", 200, 0.94, 0.90, "passive"),
        "SNACKPACK_PISTACHIO": ("reversal", 200, 0.94, 0.80, "passive"),
        "SNACKPACK_CHOCOLATE": ("momentum", 200, 0.92, 0.90, "passive"),
        "SNACKPACK_VANILLA": ("momentum", 200, 0.96, 0.80, "passive"),
    }
    oracle_sets = {
        "panel_oracle": panel_oracle,
        "trans_galaxy_oracle": trans_galaxy_oracle,
        "sleep_oxygen_oracle": sleep_oxygen_oracle,
        "snack_oracle": snack_oracle,
        "fresh_oracle_all": {**panel_oracle, **trans_galaxy_oracle, **sleep_oxygen_oracle, **snack_oracle},
    }
    for suffix, additions in oracle_sets.items():
        write_probe(f"probe_pivot_robust_{suffix}", robust_text, {**robust_sig, **additions}, 44)
        write_probe(f"probe_pivot_portal_{suffix}", portal_text, {**portal_sig, **additions}, 44)

    print(f"Wrote fresh-edge pivot probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
