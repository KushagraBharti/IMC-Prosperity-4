from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = ROOT / "ROUND5" / "research" / "probes" / "150k_exec"
ROBUST_BASE = PROBE_DIR / "probe_c35_anchor_both_micro_uv_conservative.py"
PORTAL_BASE = PROBE_DIR / "probe_increment_vanilla_micro_uv_loose.py"


ANCHOR_METHODS = r'''
    def run_product_anchor_edges(self, state: TradingState, result: Dict[str, List[Order]]) -> None:
        for product, cfg in self.PRODUCT_ANCHOR_CONFIG.items():
            anchor, edge, size, side, style = cfg
            depth = state.order_depths.get(product)
            if not depth or not depth.buy_orders or not depth.sell_orders:
                continue
            if product in result and not self.PRODUCT_ANCHOR_OVERRIDE:
                continue
            book = self.book(state, product)
            if not book:
                continue
            orders = self.trade_product_anchor(product, book, state.position.get(product, 0), anchor, edge, int(size), side, style)
            if orders:
                result[product] = orders

    def trade_product_anchor(self, product: str, book: dict, pos: int, anchor: float, edge: float, size: int, side: str, style: str) -> List[Order]:
        orders: List[Order] = []
        start = pos
        if side in ("sell_high", "two_sided") and book["mid"] - anchor >= edge and pos > -self.LIMIT:
            price = book["bid"] if style == "take" and book["bid"] - anchor >= edge + 2 else self.improve_ask(book)
            qty = min(size if book["mid"] - anchor < edge + 18 else self.LIMIT + pos, self.LIMIT + pos)
            if qty > 0:
                orders.append(Order(product, int(price), int(-qty)))
        if side in ("buy_low", "two_sided") and anchor - book["mid"] >= edge and pos < self.LIMIT:
            price = book["ask"] if style == "take" and anchor - book["ask"] >= edge + 2 else self.improve_bid(book)
            qty = min(size if anchor - book["mid"] < edge + 18 else self.LIMIT - pos, self.LIMIT - pos)
            if qty > 0:
                orders.append(Order(product, int(price), int(qty)))
        # Inventory release near anchor, so one-sided anchors do not carry stale exposure forever.
        if side == "sell_high" and pos < 0 and book["mid"] <= anchor + max(1.0, edge * 0.25):
            orders.append(Order(product, int(self.improve_bid(book)), int(min(-pos, size))))
        if side == "buy_low" and pos > 0 and book["mid"] >= anchor - max(1.0, edge * 0.25):
            orders.append(Order(product, int(self.improve_ask(book)), int(-min(pos, size))))
        return self.ensure_limit(product, start, orders)

'''


FILL_METHODS = r'''
    def run_one_sided_fill_edges(self, state: TradingState, cache: dict, result: Dict[str, List[Order]]) -> None:
        scored = []
        for product, cfg in self.ONE_SIDED_FILL_CONFIG.items():
            side, min_spread, imb_gate, size, release_ticks = cfg
            book = self.book(state, product)
            if not book:
                continue
            if product in result and not self.ONE_SIDED_FILL_OVERRIDE:
                continue
            hist = self.push(cache, "os_" + product, book["mid"], 120)
            if len(hist) < 20:
                continue
            # Favor one-sided quoting only when spread/imbalance are compatible with the passive-fill oracle.
            if book["spread"] < min_spread:
                continue
            if side == "bid" and book["imb"] < imb_gate:
                continue
            if side == "ask" and book["imb"] > -imb_gate:
                continue
            scored.append((abs(book["imb"]) * max(book["spread"], 1), product, book, side, int(size), float(release_ticks)))
        scored.sort(reverse=True, key=lambda row: row[0])
        for _score, product, book, side, size, release_ticks in scored[: self.MAX_ONE_SIDED_FILL_PRODUCTS]:
            orders = self.trade_one_sided_fill(product, book, state.position.get(product, 0), side, size, release_ticks)
            if orders:
                result[product] = orders

    def trade_one_sided_fill(self, product: str, book: dict, pos: int, side: str, size: int, release_ticks: float) -> List[Order]:
        orders: List[Order] = []
        start = pos
        if side == "bid":
            if pos < self.LIMIT:
                orders.append(Order(product, int(self.improve_bid(book)), int(min(size, self.LIMIT - pos))))
            if pos > 0:
                orders.append(Order(product, int(self.improve_ask(book)), int(-min(pos, max(1, size // 2)))))
        elif side == "ask":
            if pos > -self.LIMIT:
                orders.append(Order(product, int(self.improve_ask(book)), int(-min(size, self.LIMIT + pos))))
            if pos < 0:
                orders.append(Order(product, int(self.improve_bid(book)), int(min(-pos, max(1, size // 2)))))
        return self.ensure_limit(product, start, orders)

'''


def write_probe(name: str, base_text: str, anchor_cfg: dict | None = None, fill_cfg: dict | None = None, anchor_override: bool = True, fill_override: bool = False) -> None:
    text = base_text
    attrs = ""
    inserts = ""
    if anchor_cfg:
        attrs += f"    PRODUCT_ANCHOR_CONFIG = {anchor_cfg!r}\n"
        attrs += f"    PRODUCT_ANCHOR_OVERRIDE = {bool(anchor_override)}\n"
        inserts += "        self.run_product_anchor_edges(state, result)\n"
    if fill_cfg:
        attrs += f"    ONE_SIDED_FILL_CONFIG = {fill_cfg!r}\n"
        attrs += f"    ONE_SIDED_FILL_OVERRIDE = {bool(fill_override)}\n"
        attrs += "    MAX_ONE_SIDED_FILL_PRODUCTS = 8\n"
        inserts += "        self.run_one_sided_fill_edges(state, cache, result)\n"
    text = text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    text = text.replace("        self.run_signals(state, cache, result)\n", "        self.run_signals(state, cache, result)\n" + inserts, 1)
    methods = ""
    if anchor_cfg:
        methods += ANCHOR_METHODS
    if fill_cfg:
        methods += FILL_METHODS
    text = text.replace("    def fit_predict", methods + "    def fit_predict", 1)
    text = text.replace("class Trader:", f"# Temporary missing-mechanism executable probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def main() -> None:
    robust = ROBUST_BASE.read_text(encoding="utf-8")
    portal = PORTAL_BASE.read_text(encoding="utf-8")

    # From missing_mechanism_anchor_search.csv top rows.
    micro_square_sell = {"MICROCHIP_SQUARE": (14250.0, 8.0, 6, "sell_high", "passive")}
    micro_square_two = {"MICROCHIP_SQUARE": (14250.0, 10.0, 5, "two_sided", "passive")}
    micro_square_take = {"MICROCHIP_SQUARE": (14250.0, 16.0, 10, "sell_high", "take")}

    # From passive-fill oracle top nontrivial products. Config: side, min_spread, imbalance gate, size, release ticks.
    fill_best = {
        "PEBBLES_XL": ("bid", 3, 0.05, 4, 4.0),
        "OXYGEN_SHAKE_GARLIC": ("bid", 3, 0.05, 4, 4.0),
        "UV_VISOR_YELLOW": ("ask", 3, 0.05, 4, 4.0),
        "MICROCHIP_SQUARE": ("ask", 3, 0.05, 5, 4.0),
    }
    fill_no_peb = {k: v for k, v in fill_best.items() if not k.startswith("PEBBLES_")}
    fill_strict = {
        "OXYGEN_SHAKE_GARLIC": ("bid", 5, 0.35, 4, 4.0),
        "UV_VISOR_YELLOW": ("ask", 5, 0.35, 4, 4.0),
        "MICROCHIP_SQUARE": ("ask", 5, 0.25, 5, 4.0),
    }

    for base_name, text in [("robust", robust), ("portal", portal)]:
        write_probe(f"probe_missing_{base_name}_micro_square_anchor_sell", text, micro_square_sell, None, True)
        write_probe(f"probe_missing_{base_name}_micro_square_anchor_two", text, micro_square_two, None, True)
        write_probe(f"probe_missing_{base_name}_micro_square_anchor_take", text, micro_square_take, None, True)
        write_probe(f"probe_missing_{base_name}_passive_fill_best", text, None, fill_best, False, True)
        write_probe(f"probe_missing_{base_name}_passive_fill_no_peb", text, None, fill_no_peb, False, True)
        write_probe(f"probe_missing_{base_name}_passive_fill_strict", text, None, fill_strict, False, True)
        write_probe(f"probe_missing_{base_name}_micro_anchor_plus_fill", text, micro_square_sell, fill_no_peb, True, True)

    print(f"Wrote missing-mechanism probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
