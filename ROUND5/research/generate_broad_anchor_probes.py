from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = ROOT / "ROUND5" / "research" / "probes" / "150k_exec"
ROBUST_BASE = PROBE_DIR / "probe_c35_anchor_both_micro_uv_conservative.py"
PORTAL_BASE = PROBE_DIR / "probe_increment_vanilla_micro_uv_loose.py"


ANCHOR_METHODS = r'''
    def run_broad_anchor(self, state: TradingState, result: Dict[str, List[Order]]) -> None:
        for product in self.BROAD_ANCHOR_PRODUCTS:
            depth = state.order_depths.get(product)
            if not depth or not depth.buy_orders or not depth.sell_orders:
                continue
            orders = self.trade_broad_anchor(product, depth, state.position.get(product, 0))
            if orders and (self.BROAD_ANCHOR_OVERRIDE or product not in result):
                result[product] = orders

    def trade_broad_anchor(self, product: str, depth, position: int) -> List[Order]:
        orders: List[Order] = []
        start = position
        for ask_price, ask_volume in sorted(depth.sell_orders.items())[:2]:
            if position >= self.LIMIT:
                break
            if self.BROAD_ANCHOR - ask_price >= self.BROAD_ANCHOR_TAKE_EDGE:
                quantity = min(self.LIMIT - position, max(0, -int(ask_volume)))
                if quantity:
                    orders.append(Order(product, int(ask_price), int(quantity)))
                    position += quantity
        for bid_price, bid_volume in sorted(depth.buy_orders.items(), reverse=True)[:2]:
            if position <= -self.LIMIT:
                break
            if bid_price - self.BROAD_ANCHOR >= self.BROAD_ANCHOR_TAKE_EDGE:
                quantity = min(self.LIMIT + position, max(0, int(bid_volume)))
                if quantity:
                    orders.append(Order(product, int(bid_price), int(-quantity)))
                    position -= quantity
        bid = max(depth.buy_orders)
        ask = min(depth.sell_orders)
        if ask - bid >= self.BROAD_ANCHOR_MIN_SPREAD:
            if position < self.LIMIT and self.BROAD_ANCHOR - (bid + 1) >= self.BROAD_ANCHOR_PASSIVE_EDGE:
                orders.append(Order(product, int(bid + 1), int(min(self.BROAD_ANCHOR_SIZE, self.LIMIT - position))))
            if position > -self.LIMIT and (ask - 1) - self.BROAD_ANCHOR >= self.BROAD_ANCHOR_PASSIVE_EDGE:
                orders.append(Order(product, int(ask - 1), int(-min(self.BROAD_ANCHOR_SIZE, self.LIMIT + position))))
        return self.ensure_limit(product, start, orders)

'''


def write_probe(name: str, base_text: str, products: set[str], override: bool, take_edge: int, passive_edge: int, size: int, min_spread: int) -> None:
    attrs = (
        f"    BROAD_ANCHOR = 10000\n"
        f"    BROAD_ANCHOR_PRODUCTS = {products!r}\n"
        f"    BROAD_ANCHOR_OVERRIDE = {bool(override)}\n"
        f"    BROAD_ANCHOR_TAKE_EDGE = {take_edge}\n"
        f"    BROAD_ANCHOR_PASSIVE_EDGE = {passive_edge}\n"
        f"    BROAD_ANCHOR_SIZE = {size}\n"
        f"    BROAD_ANCHOR_MIN_SPREAD = {min_spread}\n"
    )
    text = base_text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    text = text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n        self.run_broad_anchor(state, result)\n", 1)
    text = text.replace("    def run_anchor", ANCHOR_METHODS + "    def run_anchor", 1) if "    def run_anchor" in text else text.replace("    def run_pebbles", ANCHOR_METHODS + "    def run_pebbles", 1)
    text = text.replace("class Trader:", f"# Temporary broad 10000-anchor probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def main() -> None:
    robust_text = ROBUST_BASE.read_text(encoding="utf-8")
    portal_text = PORTAL_BASE.read_text(encoding="utf-8")

    translator_sleep_snack = {
        "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_SPACE_GRAY",
        "SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON",
        "SNACKPACK_RASPBERRY", "SNACKPACK_STRAWBERRY", "SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO",
    }
    galaxy_oxygen_panel = {
        "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_WINDS", "GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_SOLAR_FLAMES",
        "OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC",
        "PANEL_1X2", "PANEL_1X4", "PANEL_2X2", "PANEL_2X4", "PANEL_4X4",
    }
    uv_micro_robot = {
        "UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA",
        "MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE",
        "ROBOT_MOPPING", "ROBOT_LAUNDRY", "ROBOT_IRONING", "ROBOT_VACUUMING",
    }
    all_reasonable = translator_sleep_snack | galaxy_oxygen_panel | uv_micro_robot
    sets = {
        "translator_sleep_snack": translator_sleep_snack,
        "galaxy_oxygen_panel": galaxy_oxygen_panel,
        "uv_micro_robot": uv_micro_robot,
        "all_reasonable": all_reasonable,
    }
    for suffix, products in sets.items():
        for base_name, text in [("robust", robust_text), ("portal", portal_text)]:
            write_probe(f"probe_anchor_{base_name}_{suffix}_passive", text, products, False, 12, 3, 3, 3)
            write_probe(f"probe_anchor_{base_name}_{suffix}_override", text, products, True, 10, 2, 5, 3)

    print(f"Wrote broad anchor probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
