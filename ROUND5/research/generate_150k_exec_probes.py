from __future__ import annotations

import importlib.util
import pprint
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRATEGY_DIR = ROOT / "ROUND5" / "strategies"
PROBE_DIR = ROOT / "ROUND5" / "research" / "probes" / "150k_exec"


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


def replace_literal(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing literal: {old}")
    return text.replace(old, new, 1)


def write_probe(name: str, base_text: str, changes: dict, replacements: list[tuple[str, str]] | None = None) -> None:
    text = base_text
    for key, value in changes.items():
        text = replace_assignment(text, key, value)
    for old, new in replacements or []:
        text = replace_literal(text, old, new)
    text = text.replace("class Trader:", f"# Temporary executable 150k probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def inject_extra_engines(text: str, extra_groups: dict, extra_products: dict, momentum_extras: dict, max_momentum: int = 5) -> str:
    attrs = (
        f"    EXTRA_GROUPS = {pprint.pformat(extra_groups, width=120, sort_dicts=False)}\n"
        f"    EXTRA_PRODUCTS = {pprint.pformat(extra_products, width=120, sort_dicts=False)}\n"
        f"    MOMENTUM_EXTRAS = {pprint.pformat(momentum_extras, width=120, sort_dicts=False)}\n"
        f"    MAX_MOMENTUM_EXTRAS = {max_momentum}\n"
    )
    text = text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    text = text.replace(
        "        self.run_signals(state, cache, result)\n",
        "        self.run_signals(state, cache, result)\n        self.run_extra_relative(state, cache, result)\n        self.run_momentum_extras(state, cache, result)\n",
        1,
    )
    return text.replace("    def book", EXTRA_ENGINE_METHODS + "    def book", 1)


ANCHOR_METHODS = r'''
    def run_anchor(self, state: TradingState, result: Dict[str, List[Order]]) -> None:
        for product in self.ANCHOR_PRODUCTS:
            depth = state.order_depths.get(product)
            if not depth or not depth.buy_orders or not depth.sell_orders:
                continue
            orders = self.trade_anchor(product, depth, state.position.get(product, 0))
            if orders:
                result[product] = orders

    def trade_anchor(self, product: str, depth, position: int) -> List[Order]:
        orders: List[Order] = []
        start = position
        for ask_price, ask_volume in sorted(depth.sell_orders.items())[:2]:
            if position >= self.LIMIT:
                break
            if self.ANCHOR - ask_price >= 2:
                quantity = min(self.LIMIT - position, max(0, -int(ask_volume)))
                if quantity:
                    orders.append(Order(product, int(ask_price), int(quantity)))
                    position += quantity
        for bid_price, bid_volume in sorted(depth.buy_orders.items(), reverse=True)[:2]:
            if position <= -self.LIMIT:
                break
            if bid_price - self.ANCHOR >= 2:
                quantity = min(self.LIMIT + position, max(0, int(bid_volume)))
                if quantity:
                    orders.append(Order(product, int(bid_price), int(-quantity)))
                    position -= quantity
        bid = max(depth.buy_orders)
        ask = min(depth.sell_orders)
        if bid + 1 < ask:
            if position < self.LIMIT:
                orders.append(Order(product, int(min(bid + 1, self.ANCHOR - 2)), int(min(3, self.LIMIT - position))))
            if position > -self.LIMIT:
                orders.append(Order(product, int(max(ask - 1, self.ANCHOR + 2)), int(-min(3, self.LIMIT + position))))
        return self.ensure_limit(product, start, orders)

    def ensure_limit(self, product: str, position: int, orders: List[Order]) -> List[Order]:
        checked: List[Order] = []
        for order in orders:
            quantity = int(order.quantity)
            if quantity > 0:
                quantity = min(quantity, self.LIMIT - position)
            elif quantity < 0:
                quantity = -min(-quantity, self.LIMIT + position)
            if quantity:
                checked.append(Order(product, int(order.price), int(quantity)))
                position += quantity
        return checked

'''


EXTRA_ENGINE_METHODS = r'''
    def run_extra_relative(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for group_products in self.EXTRA_GROUPS.values():
            books = {product: self.book(state, product) for product in group_products}
            if any(book is None for book in books.values()):
                continue
            mids = {product: books[product]["mid"] for product in group_products}
            group_mid = sum(mids.values()) / len(mids)
            for product in group_products:
                if product not in self.EXTRA_PRODUCTS or product in result:
                    continue
                threshold, weight = self.EXTRA_PRODUCTS[product]
                residual = mids[product] - group_mid
                hist = self.push(cache, "xrel_" + product, residual, 220)
                if len(hist) < 45:
                    continue
                center_window = hist[-180:]
                center = sum(center_window) / len(center_window)
                sigma = self.std(hist[-120:], 4.0)
                z = (residual - center) / max(sigma, 1.0)
                if abs(z) >= threshold:
                    scored.append((abs(z) * weight, product, books[product], z, sigma))

        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, z, sigma in scored[:5]:
            orders = self.trade_extra_relative(product, book, state.position.get(product, 0), z, sigma)
            if orders:
                result[product] = orders

    def trade_extra_relative(self, product: str, book: dict, position: int, z: float, sigma: float) -> List[Order]:
        start = position
        intensity = min(1.0, max(0.0, (abs(z) - 1.05) / 2.1))
        target = int(round((-self.LIMIT if z > 0 else self.LIMIT) * intensity))
        delta = target - position
        if delta > 0:
            price = self.improve_bid(book)
            if abs(z) > 3.0 and book["ask"] - price <= max(7, 0.40 * sigma):
                price = book["ask"]
            return self.ensure_limit(product, start, [Order(product, int(price), int(delta))])
        if delta < 0:
            price = self.improve_ask(book)
            if abs(z) > 3.0 and price - book["bid"] <= max(7, 0.40 * sigma):
                price = book["bid"]
            return self.ensure_limit(product, start, [Order(product, int(price), int(delta))])
        return []

    def run_momentum_extras(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for product, (lookback, threshold, signed_weight) in self.MOMENTUM_EXTRAS.items():
            if product in result:
                continue
            book = self.book(state, product)
            if not book:
                continue
            hist = self.push(cache, "mom_" + product, book["mid"], max(260, lookback + 140))
            if len(hist) <= lookback + 5:
                continue
            raw = (hist[-1] - hist[-1 - lookback]) / max(self.vol(hist[-140:]), 1.0)
            signal = raw if signed_weight > 0 else -raw
            if abs(signal) >= threshold:
                scored.append((abs(signal) * abs(signed_weight), product, book, signal, threshold))

        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, signal, threshold in scored[: self.MAX_MOMENTUM_EXTRAS]:
            orders = self.trade_momentum_extra(product, book, state.position.get(product, 0), signal, threshold)
            if orders:
                result[product] = orders

    def trade_momentum_extra(self, product: str, book: dict, position: int, signal: float, threshold: float) -> List[Order]:
        start = position
        intensity = min(1.0, max(0.0, (abs(signal) - threshold) / 1.3))
        target = int(round((self.LIMIT if signal > 0 else -self.LIMIT) * intensity))
        delta = target - position
        if delta > 0:
            price = book["ask"] if abs(signal) > threshold + 1.3 else self.improve_bid(book)
            return self.ensure_limit(product, start, [Order(product, int(price), int(delta))])
        if delta < 0:
            price = book["bid"] if abs(signal) > threshold + 1.3 else self.improve_ask(book)
            return self.ensure_limit(product, start, [Order(product, int(price), int(delta))])
        return []

'''


def main() -> None:
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    c35_path = STRATEGY_DIR / "round5_candidate_35.py"
    c36_path = STRATEGY_DIR / "round5_candidate_36.py"
    c35_text = c35_path.read_text(encoding="utf-8")
    c36_text = c36_path.read_text(encoding="utf-8")
    C35 = load_trader(c35_path)
    C36 = load_trader(c36_path)

    c35_sig = dict(C35.SIGNAL_CONFIG)
    c35_boost = dict(C35.PEB_BOOST)

    # 1. PEBBLES undercapture repairs: M/L/XS get stronger passive quoting or more taker reach.
    write_probe(
        "probe_peb_mlx_boost_passive",
        c35_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.35, "PEBBLES_L": 1.25, "PEBBLES_XS": 1.15},
            "PEB_AGGRESSION": 1.15,
            "PEB_ALLOW_TAKE": 0,
        },
    )
    write_probe(
        "probe_peb_mlx_boost_taker",
        c35_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.35, "PEBBLES_L": 1.25, "PEBBLES_XS": 1.15},
            "PEB_AGGRESSION": 1.22,
            "PEB_ALLOW_TAKE": 1,
        },
        [
            ("abs(book[\"mid\"] - fair) > max(10.5, 1.85 * rvol)", "abs(book[\"mid\"] - fair) > max(8.0, 1.45 * rvol)"),
            ("edge_floor + 5.8", "edge_floor + 4.2"),
        ],
    )
    write_probe(
        "probe_peb_lxs_signal_overlay",
        c35_text,
        {
            "SIGNAL_CONFIG": {
                **c35_sig,
                "PEBBLES_L": ("reversal", 50, 0.88, 1.05, "passive"),
                "PEBBLES_XS": ("momentum", 100, 0.92, 0.90, "passive"),
                "PEBBLES_M": ("reversal", 200, 0.82, 1.25, "passive"),
            },
            "MAX_SIGNAL_PRODUCTS": 30,
        },
    )

    # 2. MICROCHIP/PANEL conversions: add missing high-gap legs via passive and hybrid variants.
    micro_panel = {
        **c35_sig,
        "MICROCHIP_CIRCLE": ("reversal", 100, 0.92, 0.95, "passive"),
        "MICROCHIP_TRIANGLE": ("reversal", 50, 0.92, 0.95, "passive"),
        "PANEL_2X4": ("momentum", 50, 0.84, 1.00, "passive"),
    }
    write_probe("probe_micro_panel_passive", c35_text, {"SIGNAL_CONFIG": micro_panel, "MAX_SIGNAL_PRODUCTS": 30})
    micro_panel_hybrid = dict(micro_panel)
    micro_panel_hybrid.update(
        {
            "MICROCHIP_SQUARE": ("momentum", 200, 0.92, 1.10, "hybrid"),
            "MICROCHIP_CIRCLE": ("reversal", 100, 0.88, 1.05, "hybrid"),
            "PANEL_2X4": ("momentum", 100, 0.82, 1.10, "hybrid"),
        }
    )
    write_probe("probe_micro_panel_hybrid", c35_text, {"SIGNAL_CONFIG": micro_panel_hybrid, "MAX_SIGNAL_PRODUCTS": 30})

    # 3. ROBOT fill/reversal probes.
    robot_passive = {
        **c35_sig,
        "ROBOT_DISHES": ("momentum", 25, 0.88, 1.05, "passive"),
        "ROBOT_LAUNDRY": ("reversal", 200, 0.92, 1.00, "passive"),
        "ROBOT_VACUUMING": ("reversal", 200, 0.94, 0.85, "passive"),
        "ROBOT_MOPPING": ("reversal", 25, 0.98, 0.75, "passive"),
    }
    write_probe("probe_robot_passive", c35_text, {"SIGNAL_CONFIG": robot_passive, "MAX_SIGNAL_PRODUCTS": 31})
    robot_hybrid = dict(robot_passive)
    robot_hybrid.update(
        {
            "ROBOT_DISHES": ("momentum", 25, 0.82, 1.20, "hybrid"),
            "ROBOT_LAUNDRY": ("reversal", 200, 0.88, 1.05, "hybrid"),
        }
    )
    write_probe("probe_robot_hybrid", c35_text, {"SIGNAL_CONFIG": robot_hybrid, "MAX_SIGNAL_PRODUCTS": 31})

    # 4. SLEEP/UV/SNACKPACK conditional conversion.
    sleep_uv_snack = {
        **c35_sig,
        "SLEEP_POD_SUEDE": ("reversal", 100, 0.92, 1.05, "passive"),
        "UV_VISOR_MAGENTA": ("momentum", 50, 0.94, 0.90, "passive"),
        "UV_VISOR_AMBER": ("momentum", 150, 0.86, 0.85, "passive"),
        "SNACKPACK_STRAWBERRY": ("reversal", 200, 1.02, 0.70, "passive"),
        "SNACKPACK_RASPBERRY": ("reversal", 200, 1.04, 0.65, "passive"),
        "SNACKPACK_CHOCOLATE": ("momentum", 200, 1.02, 0.60, "passive"),
        "SNACKPACK_PISTACHIO": ("reversal", 200, 1.04, 0.55, "passive"),
        "SNACKPACK_VANILLA": ("momentum", 200, 1.08, 0.50, "passive"),
    }
    write_probe("probe_sleep_uv_snack", c35_text, {"SIGNAL_CONFIG": sleep_uv_snack, "MAX_SIGNAL_PRODUCTS": 34})

    # 5. Remaining high-gap/unused products.
    remaining = {
        **c35_sig,
        "GALAXY_SOUNDS_BLACK_HOLES": ("reversal", 50, 0.98, 0.75, "passive"),
        "OXYGEN_SHAKE_EVENING_BREATH": ("reversal", 100, 0.92, 0.85, "passive"),
        "OXYGEN_SHAKE_MINT": ("breakout_low_reversal", 500, 0.98, 0.70, "passive"),
        "TRANSLATOR_ASTRO_BLACK": ("momentum", 100, 1.00, 0.70, "passive"),
        "TRANSLATOR_SPACE_GRAY": ("momentum", 220, 0.86, 0.90, "passive"),
        "TRANSLATOR_ECLIPSE_CHARCOAL": ("rolling_mean_reversion", 500, 0.90, 1.00, "passive"),
    }
    write_probe("probe_remaining_unused", c35_text, {"SIGNAL_CONFIG": remaining, "MAX_SIGNAL_PRODUCTS": 33})

    # 6. Candidate 35 marginal stacks.
    stack_robust = {
        **c35_sig,
        "PEBBLES_M": ("reversal", 200, 0.82, 1.20, "passive"),
        "SLEEP_POD_SUEDE": ("reversal", 100, 0.96, 0.90, "passive"),
        "MICROCHIP_CIRCLE": ("reversal", 100, 0.96, 0.85, "passive"),
        "PANEL_2X4": ("momentum", 100, 0.88, 0.85, "passive"),
        "ROBOT_LAUNDRY": ("reversal", 200, 0.96, 0.80, "passive"),
    }
    write_probe(
        "probe_c35_stack_robust",
        c35_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.24, "PEBBLES_L": 1.12, "PEBBLES_XS": 1.05},
            "PEB_AGGRESSION": 1.10,
            "SIGNAL_CONFIG": stack_robust,
            "MAX_SIGNAL_PRODUCTS": 32,
        },
    )
    stack_broad = {
        **stack_robust,
        "UV_VISOR_MAGENTA": ("momentum", 50, 0.98, 0.70, "passive"),
        "UV_VISOR_AMBER": ("momentum", 150, 0.90, 0.75, "passive"),
        "GALAXY_SOUNDS_BLACK_HOLES": ("reversal", 50, 1.00, 0.65, "passive"),
        "SNACKPACK_STRAWBERRY": ("reversal", 200, 1.08, 0.55, "passive"),
        "ROBOT_VACUUMING": ("reversal", 200, 0.98, 0.60, "passive"),
    }
    write_probe(
        "probe_c35_stack_broad_gated",
        c35_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.24, "PEBBLES_L": 1.12, "PEBBLES_XS": 1.05},
            "PEB_AGGRESSION": 1.10,
            "SIGNAL_CONFIG": stack_broad,
            "MAX_SIGNAL_PRODUCTS": 35,
        },
    )

    # 7. Candidate 36 cleanup variants, useful as portal-upside controls.
    c36_mom = dict(C36.MOMENTUM_EXTRAS)
    c36_mom_no_robot = {k: v for k, v in c36_mom.items() if not k.startswith("ROBOT_")}
    write_probe("probe_c36_no_robot_extras", c36_text, {"MOMENTUM_EXTRAS": c36_mom_no_robot})
    c36_mom_more_peb = dict(c36_mom)
    c36_mom_more_peb.update({"PEBBLES_L": (120, 0.85, 0.65), "PEBBLES_M": (180, 0.75, -0.65)})
    write_probe(
        "probe_c36_more_pebbles",
        c36_text,
        {
            "TRADED_PEBBLES": {"PEBBLES_S", "PEBBLES_M", "PEBBLES_XL", "PEBBLES_L", "PEBBLES_XS"},
            "PEB_BOOST": {"PEBBLES_XL": 1.15, "PEBBLES_M": 1.08, "PEBBLES_S": 1.12, "PEBBLES_L": 1.00, "PEBBLES_XS": 0.92},
            "MOMENTUM_EXTRAS": c36_mom_more_peb,
            "MAX_MOMENTUM_EXTRAS": 8,
        },
    )

    # 8. Second-pass cleaned stacks: keep only first-pass executable positives, then test anchor add-on.
    clean_stack = {
        **c35_sig,
        "PANEL_2X4": ("momentum", 50, 0.86, 1.00, "passive"),
        "SLEEP_POD_SUEDE": ("reversal", 100, 0.94, 1.00, "passive"),
        "GALAXY_SOUNDS_BLACK_HOLES": ("reversal", 50, 0.98, 0.75, "passive"),
        "TRANSLATOR_ASTRO_BLACK": ("momentum", 100, 1.00, 0.75, "passive"),
        "SNACKPACK_STRAWBERRY": ("reversal", 200, 1.08, 0.60, "passive"),
        "SNACKPACK_RASPBERRY": ("reversal", 200, 1.08, 0.55, "passive"),
        "SNACKPACK_PISTACHIO": ("reversal", 200, 1.08, 0.50, "passive"),
        "ROBOT_VACUUMING": ("reversal", 200, 1.02, 0.55, "passive"),
    }
    write_probe(
        "probe_c35_stack_clean",
        c35_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": clean_stack,
            "MAX_SIGNAL_PRODUCTS": 36,
        },
    )

    clean_no_snack = {k: v for k, v in clean_stack.items() if not k.startswith("SNACKPACK_")}
    write_probe(
        "probe_c35_stack_clean_no_snack",
        c35_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": clean_no_snack,
            "MAX_SIGNAL_PRODUCTS": 33,
        },
    )

    anchor_sig = {k: v for k, v in clean_stack.items() if k != "TRANSLATOR_ECLIPSE_CHARCOAL"}
    anchor_text = c35_text
    anchor_text = replace_assignment(anchor_text, "ANCHOR", 10000) if "    ANCHOR =" in anchor_text else anchor_text.replace("    LIMIT = 10\n", "    LIMIT = 10\n    ANCHOR = 10000\n", 1)
    anchor_text = anchor_text.replace("    PEBBLES = ", "    ANCHOR_PRODUCTS = {'TRANSLATOR_ECLIPSE_CHARCOAL'}\n    PEBBLES = ", 1)
    anchor_text = anchor_text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n        self.run_anchor(state, result)\n", 1)
    anchor_text = anchor_text.replace("    def run_pebbles", ANCHOR_METHODS + "    def run_pebbles", 1)
    write_probe(
        "probe_c35_stack_clean_anchor",
        anchor_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": anchor_sig,
            "MAX_SIGNAL_PRODUCTS": 36,
        },
    )

    anchor_only_sig = {k: v for k, v in c35_sig.items() if k != "TRANSLATOR_ECLIPSE_CHARCOAL"}
    anchor_only_text = c35_text
    anchor_only_text = anchor_only_text.replace("    LIMIT = 10\n", "    LIMIT = 10\n    ANCHOR = 10000\n", 1)
    anchor_only_text = anchor_only_text.replace("    PEBBLES = ", "    ANCHOR_PRODUCTS = {'TRANSLATOR_ECLIPSE_CHARCOAL'}\n    PEBBLES = ", 1)
    anchor_only_text = anchor_only_text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n        self.run_anchor(state, result)\n", 1)
    anchor_only_text = anchor_only_text.replace("    def run_pebbles", ANCHOR_METHODS + "    def run_pebbles", 1)
    write_probe("probe_c35_anchor_only", anchor_only_text, {"SIGNAL_CONFIG": anchor_only_sig, "MAX_SIGNAL_PRODUCTS": 27})

    # 9. Focused "remaining 40k" probes after executable conversion checkpoint.
    anchor_both_text = c35_text
    anchor_both_text = anchor_both_text.replace("    LIMIT = 10\n", "    LIMIT = 10\n    ANCHOR = 10000\n", 1)
    anchor_both_text = anchor_both_text.replace("    PEBBLES = ", "    ANCHOR_PRODUCTS = {'TRANSLATOR_ECLIPSE_CHARCOAL', 'PEBBLES_L'}\n    PEBBLES = ", 1)
    anchor_both_text = anchor_both_text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n        self.run_anchor(state, result)\n", 1)
    anchor_both_text = anchor_both_text.replace("    def run_pebbles", ANCHOR_METHODS + "    def run_pebbles", 1)
    write_probe(
        "probe_c35_stack_clean_anchor_both",
        anchor_both_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": anchor_sig,
            "MAX_SIGNAL_PRODUCTS": 36,
        },
    )

    robot_dishes_stack = {
        **anchor_sig,
        "ROBOT_DISHES": ("momentum", 25, 0.82, 1.20, "hybrid"),
        "ROBOT_MOPPING": ("reversal", 25, 1.02, 0.45, "passive"),
    }
    robot_dishes_text = anchor_text
    write_probe(
        "probe_c35_stack_anchor_robot_dishes",
        robot_dishes_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": robot_dishes_stack,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    micro_uv_stack = {
        **anchor_sig,
        "MICROCHIP_TRIANGLE": ("reversal", 150, 0.95, 0.60, "hybrid"),
        "UV_VISOR_AMBER": ("momentum", 150, 0.75, 0.70, "hybrid"),
    }
    write_probe(
        "probe_c35_stack_anchor_microtri_uvamber",
        anchor_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": micro_uv_stack,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    microtri_only_stack = {
        **anchor_sig,
        "MICROCHIP_TRIANGLE": ("reversal", 150, 0.95, 0.60, "hybrid"),
    }
    write_probe(
        "probe_c35_stack_anchor_microtri_only",
        anchor_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": microtri_only_stack,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    uvamber_only_stack = {
        **anchor_sig,
        "UV_VISOR_AMBER": ("momentum", 150, 0.75, 0.70, "hybrid"),
    }
    write_probe(
        "probe_c35_stack_anchor_uvamber_only",
        anchor_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": uvamber_only_stack,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    write_probe(
        "probe_c35_stack_anchor_both_microtri_uvamber",
        anchor_both_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": micro_uv_stack,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    # 10. Focused follow-up: try to keep the 120k portal mechanism while reducing full-history damage.
    conservative_micro_uv = {
        **anchor_sig,
        "MICROCHIP_TRIANGLE": ("reversal", 150, 1.15, 0.48, "passive"),
        "UV_VISOR_AMBER": ("momentum", 150, 0.98, 0.52, "passive"),
    }
    write_probe(
        "probe_c35_anchor_both_micro_uv_conservative",
        anchor_both_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": conservative_micro_uv,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    medium_micro_uv = {
        **anchor_sig,
        "MICROCHIP_TRIANGLE": ("reversal", 150, 1.05, 0.55, "hybrid"),
        "UV_VISOR_AMBER": ("momentum", 150, 0.88, 0.62, "hybrid"),
    }
    write_probe(
        "probe_c35_anchor_both_micro_uv_medium",
        anchor_both_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": medium_micro_uv,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    robot_dishes_tight = {
        **anchor_sig,
        "ROBOT_DISHES": ("momentum", 25, 1.18, 0.85, "passive"),
    }
    write_probe(
        "probe_c35_anchor_both_robot_dishes_tight",
        anchor_both_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": robot_dishes_tight,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    robot_dishes_very_tight = {
        **anchor_sig,
        "ROBOT_DISHES": ("momentum", 25, 1.38, 0.72, "hybrid"),
    }
    write_probe(
        "probe_c35_anchor_both_robot_dishes_very_tight",
        anchor_both_text,
        {
            "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
            "PEB_AGGRESSION": 1.08,
            "SIGNAL_CONFIG": robot_dishes_very_tight,
            "MAX_SIGNAL_PRODUCTS": 37,
        },
    )

    def anchor_probe_text(products: set[str]) -> str:
        text = c35_text
        text = text.replace("    LIMIT = 10\n", "    LIMIT = 10\n    ANCHOR = 10000\n", 1)
        text = text.replace("    PEBBLES = ", f"    ANCHOR_PRODUCTS = {products!r}\n    PEBBLES = ", 1)
        text = text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n        self.run_anchor(state, result)\n", 1)
        return text.replace("    def run_pebbles", ANCHOR_METHODS + "    def run_pebbles", 1)

    write_probe(
        "probe_c35_anchor_translator_family",
        anchor_probe_text({"TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_SPACE_GRAY", "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE"}),
        {"SIGNAL_CONFIG": anchor_sig, "MAX_SIGNAL_PRODUCTS": 36},
    )
    write_probe(
        "probe_c35_anchor_pebbles_family",
        anchor_probe_text({"PEBBLES_L", "PEBBLES_M", "PEBBLES_XS"}),
        {"SIGNAL_CONFIG": anchor_sig, "MAX_SIGNAL_PRODUCTS": 36},
    )
    write_probe(
        "probe_c35_anchor_all_reasonable",
        anchor_probe_text({"TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_SPACE_GRAY", "PEBBLES_L", "PEBBLES_M"}),
        {"SIGNAL_CONFIG": anchor_sig, "MAX_SIGNAL_PRODUCTS": 36},
    )

    write_probe(
        "probe_c35_anchor_snackpack_near10000",
        anchor_probe_text({"TRANSLATOR_ECLIPSE_CHARCOAL", "PEBBLES_L", "SNACKPACK_VANILLA", "SNACKPACK_RASPBERRY", "SNACKPACK_CHOCOLATE"}),
        {"SIGNAL_CONFIG": anchor_sig, "MAX_SIGNAL_PRODUCTS": 36},
    )
    write_probe(
        "probe_c35_anchor_space_nylon",
        anchor_probe_text({"TRANSLATOR_ECLIPSE_CHARCOAL", "PEBBLES_L", "TRANSLATOR_SPACE_GRAY", "SLEEP_POD_NYLON"}),
        {"SIGNAL_CONFIG": anchor_sig, "MAX_SIGNAL_PRODUCTS": 36},
    )
    write_probe(
        "probe_c35_anchor_vanilla_only",
        anchor_probe_text({"TRANSLATOR_ECLIPSE_CHARCOAL", "PEBBLES_L", "SNACKPACK_VANILLA"}),
        {"SIGNAL_CONFIG": anchor_sig, "MAX_SIGNAL_PRODUCTS": 36},
    )
    write_probe(
        "probe_c35_anchor_near10000_all",
        anchor_probe_text({"TRANSLATOR_ECLIPSE_CHARCOAL", "PEBBLES_L", "SNACKPACK_VANILLA", "SNACKPACK_RASPBERRY", "SNACKPACK_CHOCOLATE", "TRANSLATOR_SPACE_GRAY", "SLEEP_POD_NYLON"}),
        {"SIGNAL_CONFIG": anchor_sig, "MAX_SIGNAL_PRODUCTS": 36},
    )

    # 13. Incremental near-10k anchor products on top of the strongest MICROCHIP/UV portal branches.
    def anchor_plus_micro_uv_probe(name: str, anchors: set[str], cfg: dict) -> None:
        write_probe(
            name,
            anchor_probe_text(anchors),
            {
                "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
                "PEB_AGGRESSION": 1.08,
                "SIGNAL_CONFIG": cfg,
                "MAX_SIGNAL_PRODUCTS": 37,
            },
        )

    micro_uv_loose_cfg = {
        **anchor_sig,
        "MICROCHIP_TRIANGLE": ("reversal", 150, 0.82, 0.70, "hybrid"),
        "UV_VISOR_AMBER": ("momentum", 150, 0.70, 0.76, "hybrid"),
    }
    uv_only_loose_cfg = {
        **anchor_sig,
        "UV_VISOR_AMBER": ("momentum", 150, 0.70, 0.76, "hybrid"),
    }
    micro_only_loose_cfg = {
        **anchor_sig,
        "MICROCHIP_TRIANGLE": ("reversal", 150, 0.82, 0.70, "hybrid"),
    }
    base_anchors = {"TRANSLATOR_ECLIPSE_CHARCOAL", "PEBBLES_L"}
    anchor_plus_micro_uv_probe("probe_increment_vanilla_micro_uv_loose", base_anchors | {"SNACKPACK_VANILLA"}, micro_uv_loose_cfg)
    anchor_plus_micro_uv_probe("probe_increment_snackpack_micro_uv_loose", base_anchors | {"SNACKPACK_VANILLA", "SNACKPACK_RASPBERRY", "SNACKPACK_CHOCOLATE"}, micro_uv_loose_cfg)
    anchor_plus_micro_uv_probe("probe_increment_near10000_micro_uv_loose", base_anchors | {"SNACKPACK_VANILLA", "SNACKPACK_RASPBERRY", "SNACKPACK_CHOCOLATE", "TRANSLATOR_SPACE_GRAY", "SLEEP_POD_NYLON"}, micro_uv_loose_cfg)
    anchor_plus_micro_uv_probe("probe_increment_vanilla_uv_only", base_anchors | {"SNACKPACK_VANILLA"}, uv_only_loose_cfg)
    anchor_plus_micro_uv_probe("probe_increment_snackpack_uv_only", base_anchors | {"SNACKPACK_VANILLA", "SNACKPACK_RASPBERRY", "SNACKPACK_CHOCOLATE"}, uv_only_loose_cfg)
    anchor_plus_micro_uv_probe("probe_increment_space_nylon_uv_only", base_anchors | {"TRANSLATOR_SPACE_GRAY", "SLEEP_POD_NYLON"}, uv_only_loose_cfg)
    anchor_plus_micro_uv_probe("probe_increment_vanilla_micro_only", base_anchors | {"SNACKPACK_VANILLA"}, micro_only_loose_cfg)
    micro_uv_conservative_cfg = {
        **anchor_sig,
        "MICROCHIP_TRIANGLE": ("reversal", 150, 1.15, 0.48, "passive"),
        "UV_VISOR_AMBER": ("momentum", 150, 0.98, 0.52, "passive"),
    }
    anchor_plus_micro_uv_probe("probe_increment_snackpack_micro_uv_conservative", base_anchors | {"SNACKPACK_VANILLA", "SNACKPACK_RASPBERRY", "SNACKPACK_CHOCOLATE"}, micro_uv_conservative_cfg)
    anchor_plus_micro_uv_probe("probe_increment_vanilla_micro_uv_conservative", base_anchors | {"SNACKPACK_VANILLA"}, micro_uv_conservative_cfg)

    # 14. Two-branch focused probes: keep developing the robust-full and portal-upside lineages separately.
    # These are portal-first because ROBOT_DISHES has repeatedly shown official-window upside but severe full toxicity.
    portal_robot_vtight_cfg = {
        **micro_uv_loose_cfg,
        "ROBOT_DISHES": ("momentum", 25, 1.38, 0.72, "hybrid"),
    }
    anchor_plus_micro_uv_probe("probe_branch_portal_vanilla_micro_uv_robot_vtight", base_anchors | {"SNACKPACK_VANILLA"}, portal_robot_vtight_cfg)

    portal_robot_passive_cfg = {
        **micro_uv_loose_cfg,
        "ROBOT_DISHES": ("momentum", 25, 1.55, 0.56, "passive"),
    }
    anchor_plus_micro_uv_probe("probe_branch_portal_vanilla_micro_uv_robot_passive", base_anchors | {"SNACKPACK_VANILLA"}, portal_robot_passive_cfg)

    portal_robot_pair_cfg = {
        **micro_uv_loose_cfg,
        "ROBOT_DISHES": ("momentum", 25, 1.42, 0.58, "hybrid"),
        "ROBOT_MOPPING": ("reversal", 25, 1.15, 0.38, "passive"),
    }
    anchor_plus_micro_uv_probe("probe_branch_portal_vanilla_micro_uv_robot_pair", base_anchors | {"SNACKPACK_VANILLA"}, portal_robot_pair_cfg)

    robust_robot_vtight_cfg = {
        **micro_uv_conservative_cfg,
        "ROBOT_DISHES": ("momentum", 25, 1.45, 0.46, "passive"),
    }
    anchor_plus_micro_uv_probe("probe_branch_robust_conservative_robot_vtight", base_anchors, robust_robot_vtight_cfg)

    robust_robot_pair_cfg = {
        **micro_uv_conservative_cfg,
        "ROBOT_DISHES": ("momentum", 25, 1.60, 0.38, "passive"),
        "ROBOT_MOPPING": ("reversal", 25, 1.22, 0.30, "passive"),
    }
    anchor_plus_micro_uv_probe("probe_branch_robust_conservative_robot_pair", base_anchors, robust_robot_pair_cfg)

    # 15. Candidate-36 machinery as family grafts onto the two active lineages.
    # Broad c36 transplants failed; these isolate whether category-relative or momentum-extra mechanics are additive.
    c36_extra_groups = dict(C36.EXTRA_GROUPS)
    c36_extra_products = dict(C36.EXTRA_PRODUCTS)
    c36_momentum = dict(C36.MOMENTUM_EXTRAS)

    def family_momentum(prefixes: tuple[str, ...]) -> dict:
        return {k: v for k, v in c36_momentum.items() if k.startswith(prefixes)}

    def family_extra(products: set[str]) -> dict:
        return {k: v for k, v in c36_extra_products.items() if k in products}

    def extra_probe(name: str, anchors: set[str], signal_cfg: dict, extra_products: dict, momentum_extras: dict, max_mom: int = 5) -> None:
        text = inject_extra_engines(anchor_probe_text(anchors), c36_extra_groups, extra_products, momentum_extras, max_mom)
        write_probe(
            name,
            text,
            {
                "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
                "PEB_AGGRESSION": 1.08,
                "SIGNAL_CONFIG": signal_cfg,
                "MAX_SIGNAL_PRODUCTS": 37,
            },
        )

    portal_anchors = base_anchors | {"SNACKPACK_VANILLA"}
    robust_anchors = base_anchors
    extra_probe(
        "probe_branch_portal_c36_panel_momentum",
        portal_anchors,
        micro_uv_loose_cfg,
        {},
        family_momentum(("PANEL_",)),
        4,
    )
    extra_probe(
        "probe_branch_portal_c36_trans_gal_momentum",
        portal_anchors,
        micro_uv_loose_cfg,
        {},
        family_momentum(("TRANSLATOR_", "GALAXY_")),
        4,
    )
    extra_probe(
        "probe_branch_portal_c36_extra_relative",
        portal_anchors,
        micro_uv_loose_cfg,
        c36_extra_products,
        {},
        0,
    )
    extra_probe(
        "probe_branch_portal_c36_all_nonrobot",
        portal_anchors,
        micro_uv_loose_cfg,
        c36_extra_products,
        {k: v for k, v in c36_momentum.items() if not k.startswith("ROBOT_")},
        6,
    )
    extra_probe(
        "probe_branch_robust_c36_panel_momentum",
        robust_anchors,
        micro_uv_conservative_cfg,
        {},
        family_momentum(("PANEL_",)),
        4,
    )
    extra_probe(
        "probe_branch_robust_c36_trans_gal_momentum",
        robust_anchors,
        micro_uv_conservative_cfg,
        {},
        family_momentum(("TRANSLATOR_", "GALAXY_")),
        4,
    )
    extra_probe(
        "probe_branch_robust_c36_extra_relative",
        robust_anchors,
        micro_uv_conservative_cfg,
        c36_extra_products,
        {},
        0,
    )
    extra_probe(
        "probe_branch_robust_c36_all_nonrobot",
        robust_anchors,
        micro_uv_conservative_cfg,
        c36_extra_products,
        {k: v for k, v in c36_momentum.items() if not k.startswith("ROBOT_")},
        6,
    )

    # 11. High-ROI grid: keep dual-anchor base, sweep only the two portal-upside gates that moved the needle.
    micro_uv_variants = {
        "loose": (0.82, 0.70, "hybrid", 0.70, 0.76, "hybrid"),
        "micro_loose_uv_med": (0.82, 0.70, "hybrid", 0.88, 0.62, "hybrid"),
        "micro_med_uv_loose": (1.05, 0.55, "hybrid", 0.70, 0.76, "hybrid"),
        "passive_loose": (0.82, 0.70, "passive", 0.70, 0.76, "passive"),
        "uv_only_loose": (9.99, 0.0, "passive", 0.70, 0.76, "hybrid"),
        "micro_only_loose": (0.82, 0.70, "hybrid", 9.99, 0.0, "passive"),
    }
    for suffix, (m_thr, m_w, m_style, u_thr, u_w, u_style) in micro_uv_variants.items():
        cfg = dict(anchor_sig)
        if m_w > 0:
            cfg["MICROCHIP_TRIANGLE"] = ("reversal", 150, m_thr, m_w, m_style)
        if u_w > 0:
            cfg["UV_VISOR_AMBER"] = ("momentum", 150, u_thr, u_w, u_style)
        write_probe(
            f"probe_grid_micro_uv_{suffix}",
            anchor_both_text,
            {
                "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
                "PEB_AGGRESSION": 1.08,
                "SIGNAL_CONFIG": cfg,
                "MAX_SIGNAL_PRODUCTS": 37,
            },
        )

    robust_micro_uv_variants = {
        "conservative_hybrid": (1.15, 0.48, "hybrid", 0.98, 0.52, "hybrid"),
        "passive_medium": (1.05, 0.55, "passive", 0.88, 0.62, "passive"),
        "uv_hybrid_micro_passive": (1.15, 0.48, "passive", 0.70, 0.76, "hybrid"),
        "micro_hybrid_uv_passive": (0.82, 0.70, "hybrid", 0.98, 0.52, "passive"),
        "uv_only_medium": (9.99, 0.0, "passive", 0.88, 0.62, "hybrid"),
    }
    for suffix, (m_thr, m_w, m_style, u_thr, u_w, u_style) in robust_micro_uv_variants.items():
        cfg = dict(anchor_sig)
        if m_w > 0:
            cfg["MICROCHIP_TRIANGLE"] = ("reversal", 150, m_thr, m_w, m_style)
        if u_w > 0:
            cfg["UV_VISOR_AMBER"] = ("momentum", 150, u_thr, u_w, u_style)
        write_probe(
            f"probe_grid_robust_micro_uv_{suffix}",
            anchor_both_text,
            {
                "PEB_BOOST": {**c35_boost, "PEBBLES_M": 1.18, "PEBBLES_L": 1.08, "PEBBLES_XS": 1.02},
                "PEB_AGGRESSION": 1.08,
                "SIGNAL_CONFIG": cfg,
                "MAX_SIGNAL_PRODUCTS": 37,
            },
        )

    # 12. Candidate-36 family-specific transplant probes. These are information probes for bigger mechanisms.
    c36_no_micro = dict(C36.MOMENTUM_EXTRAS)
    c36_no_micro = {k: v for k, v in c36_no_micro.items() if not k.startswith("MICROCHIP_")}
    write_probe("probe_c36_no_micro_extras", c36_text, {"MOMENTUM_EXTRAS": c36_no_micro, "MAX_MOMENTUM_EXTRAS": 7})

    c36_no_uv = dict(C36.MOMENTUM_EXTRAS)
    c36_no_uv = {k: v for k, v in c36_no_uv.items() if not k.startswith("UV_VISOR_")}
    write_probe("probe_c36_no_uv_extras", c36_text, {"MOMENTUM_EXTRAS": c36_no_uv, "MAX_MOMENTUM_EXTRAS": 7})

    c36_no_panel = dict(C36.MOMENTUM_EXTRAS)
    c36_no_panel = {k: v for k, v in c36_no_panel.items() if not k.startswith("PANEL_")}
    write_probe("probe_c36_no_panel_extras", c36_text, {"MOMENTUM_EXTRAS": c36_no_panel, "MAX_MOMENTUM_EXTRAS": 7})


    c36_clean_signals = {
        product: (cfg[0], cfg[1], cfg[2], cfg[3])
        for product, cfg in clean_stack.items()
    }
    write_probe(
        "probe_c36_plus_c35_clean_signals",
        c36_text,
        {
            "SIGNAL_CONFIG": c36_clean_signals,
            "MAX_SIGNAL_PRODUCTS": 28,
            "MAX_MOMENTUM_EXTRAS": 7,
        },
    )

    c36_focus_signals = dict(C36.SIGNAL_CONFIG)
    for product in [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "PANEL_2X4",
        "SLEEP_POD_SUEDE",
        "TRANSLATOR_ASTRO_BLACK",
    ]:
        cfg = clean_stack.get(product)
        if cfg:
            c36_focus_signals[product] = (cfg[0], cfg[1], cfg[2], cfg[3])
    write_probe(
        "probe_c36_focus_gap_signals",
        c36_text,
        {
            "SIGNAL_CONFIG": c36_focus_signals,
            "MAX_SIGNAL_PRODUCTS": 14,
            "MAX_MOMENTUM_EXTRAS": 7,
        },
    )

    print(f"Wrote {len(list(PROBE_DIR.glob('probe_*.py')))} probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
