from __future__ import annotations

import importlib.util
import pprint
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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


ANCHOR_METHODS = r'''
    def run_integrated_micro_anchor(self, state: TradingState, result: Dict[str, List[Order]]) -> None:
        product = "MICROCHIP_SQUARE"
        book = self.book(state, product)
        if not book:
            return
        orders = self.trade_integrated_micro_anchor(product, book, state.position.get(product, 0))
        if orders:
            result[product] = orders

    def trade_integrated_micro_anchor(self, product: str, book: dict, pos: int) -> List[Order]:
        anchor = 14250.0
        edge = self.MICRO_ANCHOR_EDGE
        size = self.MICRO_ANCHOR_SIZE
        orders: List[Order] = []
        start = pos
        # Portal oracle showed strongest one-sided sell-high behavior. Keep release gentle near anchor.
        if book["mid"] - anchor >= edge and pos > -self.LIMIT:
            price = book["bid"] if book["bid"] - anchor >= edge + self.MICRO_ANCHOR_TAKE_EXTRA else self.improve_ask(book)
            qty = self.LIMIT + pos if book["mid"] - anchor >= edge + 18 else min(size, self.LIMIT + pos)
            if qty > 0:
                orders.append(Order(product, int(price), int(-qty)))
        if pos < 0 and book["mid"] <= anchor + max(2.0, edge * 0.30):
            orders.append(Order(product, int(self.improve_bid(book)), int(min(-pos, max(2, size // 2)))))
        return self.ensure_limit(product, start, orders)

'''


def inject_micro_anchor(text: str, edge: float = 16.0, size: int = 10, take_extra: float = 2.0) -> str:
    attrs = (
        f"    MICRO_ANCHOR_EDGE = {edge}\n"
        f"    MICRO_ANCHOR_SIZE = {size}\n"
        f"    MICRO_ANCHOR_TAKE_EXTRA = {take_extra}\n"
    )
    text = text.replace("    def run(self, state: TradingState):\n", attrs + "    def run(self, state: TradingState):\n", 1)
    text = text.replace("        self.run_anchor(state, result)\n", "        self.run_anchor(state, result)\n        self.run_integrated_micro_anchor(state, result)\n", 1)
    text = text.replace("    def fit_predict", ANCHOR_METHODS + "    def fit_predict", 1)
    return text


def write(name: str, text: str) -> None:
    text = text.replace("class Trader:", f"# Hand-integrated mechanism probe: {name}\nclass Trader:", 1)
    (PROBE_DIR / f"{name}.py").write_text(text, encoding="utf-8")


def main() -> None:
    portal_base = PROBE_DIR / "probe_increment_vanilla_micro_uv_loose.py"
    portal_fresh = PROBE_DIR / "probe_pivot_portal_all_fresh_no_robot_micro_uv.py"
    portal_robot = PROBE_DIR / "probe_branch_portal_vanilla_micro_uv_robot_pair.py"
    robust_panel = PROBE_DIR / "probe_pivot_robust_panel.py"

    portal_base_text = portal_base.read_text(encoding="utf-8")
    fresh_text = portal_fresh.read_text(encoding="utf-8")
    robot_text = portal_robot.read_text(encoding="utf-8")
    robust_panel_text = robust_panel.read_text(encoding="utf-8")

    PortalBase = load_trader(portal_base)
    Fresh = load_trader(portal_fresh)
    Robot = load_trader(portal_robot)
    RobustPanel = load_trader(robust_panel)

    fresh_robot_cfg = dict(PortalBase.SIGNAL_CONFIG)
    fresh_robot_cfg.update(dict(Fresh.SIGNAL_CONFIG))
    fresh_robot_cfg.update(
        {
            "ROBOT_DISHES": ("momentum", 25, 1.42, 0.58, "hybrid"),
            "ROBOT_MOPPING": ("reversal", 25, 1.15, 0.38, "passive"),
        }
    )
    fresh_robot_text = replace_assignment(portal_base_text, "SIGNAL_CONFIG", fresh_robot_cfg)
    fresh_robot_text = replace_assignment(fresh_robot_text, "MAX_SIGNAL_PRODUCTS", 42)

    # Portal branch integrations.
    write("probe_hand_portal_fresh_micro_anchor", inject_micro_anchor(fresh_text, 16.0, 10, 2.0))
    write("probe_hand_portal_robot_micro_anchor", inject_micro_anchor(robot_text, 16.0, 10, 2.0))
    write("probe_hand_portal_fresh_robot", fresh_robot_text)
    write("probe_hand_portal_fresh_robot_micro_anchor", inject_micro_anchor(fresh_robot_text, 16.0, 10, 2.0))

    # Slightly less aggressive anchor versions to test whether integration loss is from crossing.
    write("probe_hand_portal_fresh_micro_anchor_passive", inject_micro_anchor(fresh_text, 10.0, 6, 99.0))
    write("probe_hand_portal_fresh_robot_micro_anchor_passive", inject_micro_anchor(fresh_robot_text, 10.0, 6, 99.0))

    # Robust branch integration: only the non-toxic PANEL lift plus MICROCHIP_SQUARE anchor.
    write("probe_hand_robust_panel_micro_anchor", inject_micro_anchor(robust_panel_text, 16.0, 10, 2.0))
    robust_panel_cfg = dict(RobustPanel.SIGNAL_CONFIG)
    robust_panel_cfg["MICROCHIP_SQUARE"] = ("breakout_low_reversal", 200, 0.86, 0.75, "passive")
    robust_clean = replace_assignment(robust_panel_text, "SIGNAL_CONFIG", robust_panel_cfg)
    write("probe_hand_robust_panel_micro_deweighted_anchor", inject_micro_anchor(robust_clean, 16.0, 10, 2.0))

    print("Wrote hand-integrated probes")


if __name__ == "__main__":
    main()
