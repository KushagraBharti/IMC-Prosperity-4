from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "ROUND4" / "strategies" / "round4_candidate_9_vfe71900_5000_harvest.py"
OUT = ROOT / "ROUND4" / "research" / "strategy_experiments"


def replace_once(text: str, old: str, new: str, name: str) -> str:
    if old not in text:
        raise ValueError(f"{name}: missing {old!r}")
    return text.replace(old, new, 1)


def write_variant(name: str, replacements: list[tuple[str, str]]) -> None:
    text = BASE.read_text(encoding="utf-8")
    for old, new in replacements:
        text = replace_once(text, old, new, name)
    path = OUT / name
    path.write_text(text, encoding="utf-8")
    print(path)


def hydro_mark_replacements(*, weight: float, threshold: float, size: int, passive_threshold: float, passive_size: int, mark22: float) -> list[tuple[str, str]]:
    return [
        ("    HYDRO_MARK_FAIR_WEIGHT = 0.0", f"    HYDRO_MARK_FAIR_WEIGHT = {weight}"),
        ("    HYDRO_MARK_EXEC_THRESHOLD = 99.0", f"    HYDRO_MARK_EXEC_THRESHOLD = {threshold}"),
        ("    HYDRO_MARK_EXEC_SIZE = 0", f"    HYDRO_MARK_EXEC_SIZE = {size}"),
        ("    HYDRO_PASSIVE_MARK_THRESHOLD = 0.5", f"    HYDRO_PASSIVE_MARK_THRESHOLD = {passive_threshold}"),
        ("    HYDRO_PASSIVE_MARK_SIZE = 18", f"    HYDRO_PASSIVE_MARK_SIZE = {passive_size}"),
        ('        "Mark 22": 0.25,', f'        "Mark 22": {mark22},'),
    ]


def cooldown_replacements(reentry: int) -> list[tuple[str, str]]:
    return [
        ("    VELVET_EXIT_TIMESTAMP = 71_900", f"    VELVET_EXIT_TIMESTAMP = 71_900\n    VELVET_REENTRY_TIMESTAMP = {reentry}"),
        ('    TIMED_OPTION_EXIT = {"VEV_5000": 71_900}', f'    TIMED_OPTION_EXIT = {{"VEV_5000": 71_900}}\n    TIMED_OPTION_REENTRY = {{"VEV_5000": {reentry}}}'),
        ("                if timestamp >= self.VELVET_EXIT_TIMESTAMP:", "                if self.VELVET_EXIT_TIMESTAMP <= timestamp < self.VELVET_REENTRY_TIMESTAMP:"),
        ("            if timed_exit is not None and timestamp >= timed_exit:", "            if timed_exit is not None and timed_exit <= timestamp < self.TIMED_OPTION_REENTRY.get(symbol, 999_999):"),
    ]


def cooldown_pair_replacements(vfe_reentry: int, vev5000_reentry: int) -> list[tuple[str, str]]:
    return [
        ("    VELVET_EXIT_TIMESTAMP = 71_900", f"    VELVET_EXIT_TIMESTAMP = 71_900\n    VELVET_REENTRY_TIMESTAMP = {vfe_reentry}"),
        ('    TIMED_OPTION_EXIT = {"VEV_5000": 71_900}', f'    TIMED_OPTION_EXIT = {{"VEV_5000": 71_900}}\n    TIMED_OPTION_REENTRY = {{"VEV_5000": {vev5000_reentry}}}'),
        ("                if timestamp >= self.VELVET_EXIT_TIMESTAMP:", "                if self.VELVET_EXIT_TIMESTAMP <= timestamp < self.VELVET_REENTRY_TIMESTAMP:"),
        ("            if timed_exit is not None and timestamp >= timed_exit:", "            if timed_exit is not None and timed_exit <= timestamp < self.TIMED_OPTION_REENTRY.get(symbol, 999_999):"),
    ]


def passive_static_cover_replacements(start: int, symbols: tuple[str, ...], size: int) -> list[tuple[str, str]]:
    symbol_repr = "{" + ", ".join(f'"{symbol}"' for symbol in symbols) + "}"
    block = (
        f"    STATIC_PASSIVE_COVER_TIMESTAMP = {start}\n"
        f"    STATIC_PASSIVE_COVER_SET = {symbol_repr}\n"
        f"    STATIC_PASSIVE_COVER_SIZE = {size}"
    )
    code = (
        "            if timestamp >= self.STATIC_PASSIVE_COVER_TIMESTAMP and symbol in self.STATIC_PASSIVE_COVER_SET and position < 0:\n"
        "                cover_price = min(int(book[\"best_bid\"]) + 1, int(book[\"best_ask\"]) - 1)\n"
        "                if int(book[\"best_bid\"]) < cover_price < int(book[\"best_ask\"]):\n"
        "                    cover_qty = min(self.STATIC_PASSIVE_COVER_SIZE, -position, self.POSITION_LIMITS[symbol] - position)\n"
        "                    if cover_qty > 0:\n"
        "                        orders.append(Order(symbol, int(cover_price), int(cover_qty)))\n\n"
        "            if symbol in {\"VEV_6000\", \"VEV_6500\"} and position < self.POSITION_LIMITS[symbol]:"
    )
    return [
        ('    TIMED_OPTION_EXIT = {"VEV_5000": 71_900}', '    TIMED_OPTION_EXIT = {"VEV_5000": 71_900}\n' + block),
        ('            if symbol in {"VEV_6000", "VEV_6500"} and position < self.POSITION_LIMITS[symbol]:', code),
    ]


def vfe_mid_reentry_replacements(threshold: float) -> list[tuple[str, str]]:
    return [
        ("    VELVET_EXIT_TIMESTAMP = 71_900", f"    VELVET_EXIT_TIMESTAMP = 71_900\n    VELVET_REENTRY_MID_THRESHOLD = {threshold}"),
        (
            "                timestamp,\n            )",
            "                timestamp,\n                cache,\n            )",
        ),
        (
            "        timestamp: int,\n    ) -> Dict[str, List[Order]]:",
            "        timestamp: int,\n        cache: Dict[str, object],\n    ) -> Dict[str, List[Order]]:",
        ),
        (
            '            velvet_pos = state.position.get("VELVETFRUIT_EXTRACT", 0)',
            '            velvet_pos = state.position.get("VELVETFRUIT_EXTRACT", 0)\n            if timestamp >= self.VELVET_EXIT_TIMESTAMP and not cache.get("velvet_reentry", False):\n                if float(velvet_book["mid"]) <= self.VELVET_REENTRY_MID_THRESHOLD:\n                    cache["velvet_reentry"] = True',
        ),
        ("                if timestamp >= self.VELVET_EXIT_TIMESTAMP:", '                if timestamp >= self.VELVET_EXIT_TIMESTAMP and not cache.get("velvet_reentry", False):'),
        ("            if timed_exit is not None and timestamp >= timed_exit:", '            if timed_exit is not None and timestamp >= timed_exit and not cache.get("velvet_reentry", False):'),
    ]


def candidate15_base_replacements() -> list[tuple[str, str]]:
    return (
        cooldown_replacements(85_000)
        + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0)
        + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")]
    )


def vfe_order_uses_blended_replacements() -> list[tuple[str, str]]:
    return [
        (
            '                    results["VELVETFRUIT_EXTRACT"] = self.trade_velvet_relative(velvet_book, velvet_implied_fair, velvet_pos)',
            '                    results["VELVETFRUIT_EXTRACT"] = self.trade_velvet_relative(velvet_book, velvet_fair, velvet_pos)',
        )
    ]


def velvet_mark_weight_replacements(weight: float) -> list[tuple[str, str]]:
    return [("    VELVET_MARK_FAIR_WEIGHT = 0.25", f"    VELVET_MARK_FAIR_WEIGHT = {weight}")]


def velvet_relative_replacements(take_edge: float | None = None, take_size: int | None = None, passive_size: int | None = None) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    if take_edge is not None:
        replacements.append(("    VELVET_REL_TAKE_EDGE = 5.0", f"    VELVET_REL_TAKE_EDGE = {take_edge}"))
    if take_size is not None:
        replacements.append(("    VELVET_REL_TAKE_SIZE = 70", f"    VELVET_REL_TAKE_SIZE = {take_size}"))
    if passive_size is not None:
        replacements.append(("    VELVET_REL_PASSIVE_SIZE = 24", f"    VELVET_REL_PASSIVE_SIZE = {passive_size}"))
    return replacements


def option_mid_size_replacements(size_5000: int, size_5100: int) -> list[tuple[str, str]]:
    return [
        (
            "    OPTION_SIZE_BY_STRIKE = {5000: 9, 5100: 9}",
            f"    OPTION_SIZE_BY_STRIKE = {{5000: {size_5000}, 5100: {size_5100}}}",
        )
    ]


def option_mid_edge_replacements(edge_5000: float, edge_5100: float) -> list[tuple[str, str]]:
    return [
        ("        5000: 1.50,", f"        5000: {edge_5000:.2f},"),
        ("        5100: 0.50,", f"        5100: {edge_5100:.2f},"),
    ]


def option_mark_fair_replacements(scale: float) -> list[tuple[str, str]]:
    weights = (
        "    OPTION_MARK_FAIR_WEIGHT = " + str(scale) + "\n"
        "    OPTION_MARK_WEIGHTS_BY_SYMBOL = {\n"
        '        "VEV_5000": {"Mark 22": 0.8, "Mark 38": -0.8},\n'
        '        "VEV_5100": {"Mark 22": 0.8, "Mark 38": -0.8},\n'
        '        "VEV_5200": {"Mark 22": -1.0, "Mark 38": -0.6},\n'
        '        "VEV_5300": {"Mark 14": 1.0, "Mark 38": -0.6},\n'
        '        "VEV_5400": {"Mark 14": -1.0},\n'
        "    }"
    )
    return [
        ("    OPTION_MARK_SPOT_WEIGHT = 0.0", "    OPTION_MARK_SPOT_WEIGHT = 0.0\n" + weights),
        (
            "                timestamp,\n            )",
            "                timestamp,\n                state,\n                cache,\n            )",
        ),
        (
            "        timestamp: int,\n    ) -> Dict[str, List[Order]]:",
            "        timestamp: int,\n        state: TradingState,\n        cache: Dict[str, object],\n    ) -> Dict[str, List[Order]]:",
        ),
        (
            "            fair = self.black_scholes_call(spot_fair, strike, t_years, sigma)",
            "            fair = self.black_scholes_call(spot_fair, strike, t_years, sigma)\n"
            "            option_mark_weights = self.OPTION_MARK_WEIGHTS_BY_SYMBOL.get(symbol)\n"
            "            if option_mark_weights:\n"
            "                fair += self.OPTION_MARK_FAIR_WEIGHT * self.mark_flow_signal(cache, state, symbol, option_mark_weights, f\"{symbol}_mark_flow\")",
        ),
    ]


def weak_option_exit_replacements(timestamp: int, symbols: tuple[str, ...]) -> list[tuple[str, str]]:
    symbol_repr = "{" + ", ".join(f'"{symbol}"' for symbol in symbols) + "}"
    return [
        ("    WEAK_OPTION_EXIT_TIMESTAMP = 86_600", f"    WEAK_OPTION_EXIT_TIMESTAMP = {timestamp}"),
        ('    WEAK_OPTION_EXIT_SET = {"VEV_5200", "VEV_5300"}', f"    WEAK_OPTION_EXIT_SET = {symbol_repr}"),
    ]


def hydro_weight_map_replacements(mark14: float, mark38: float, mark22: float) -> list[tuple[str, str]]:
    return [
        ('        "Mark 14": 1.0,', f'        "Mark 14": {mark14},'),
        ('        "Mark 38": -1.0,', f'        "Mark 38": {mark38},'),
        ('        "Mark 22": -2.0,', f'        "Mark 22": {mark22},'),
    ]


def hydro_exit_replacements(timestamp: int) -> list[tuple[str, str]]:
    return [("    HYDRO_EXIT_TIMESTAMP = 60_000", f"    HYDRO_EXIT_TIMESTAMP = {timestamp}")]


def late_option_exit_replacements(timestamp: int, symbols: tuple[str, ...]) -> list[tuple[str, str]]:
    symbol_repr = "{" + ", ".join(f'"{symbol}"' for symbol in symbols) + "}"
    constants = (
        f"    LATE_OPTION_EXIT_TIMESTAMP = {timestamp}\n"
        f"    LATE_OPTION_EXIT_SET = {symbol_repr}"
    )
    block = (
        "            if symbol in self.LATE_OPTION_EXIT_SET and timestamp >= self.LATE_OPTION_EXIT_TIMESTAMP:\n"
        "                if position < 0 and book[\"sell_orders\"]:\n"
        "                    close_price = int(book[\"sell_orders\"][-1][0])\n"
        "                    orders.append(Order(symbol, close_price, int(-position)))\n"
        "                elif position > 0 and book[\"buy_orders\"]:\n"
        "                    close_price = int(book[\"buy_orders\"][-1][0])\n"
        "                    orders.append(Order(symbol, close_price, int(-position)))\n"
        "                checked = self.ensure_within_hard_limit(symbol, original_position, orders)\n"
        "                if checked:\n"
        "                    results[symbol] = checked\n"
        "                continue\n\n"
        "            for ask_price, ask_volume in book[\"sell_orders\"]:"
    )
    return [
        ('    WEAK_OPTION_EXIT_SET = {"VEV_5200", "VEV_5300"}', '    WEAK_OPTION_EXIT_SET = {"VEV_5200", "VEV_5300"}\n' + constants),
        ('            for ask_price, ask_volume in book["sell_orders"]:', block),
    ]


def late_call_accum_replacements(timestamp: int, targets: dict[str, int], size: int, min_edge: float) -> list[tuple[str, str]]:
    target_repr = "{" + ", ".join(f'"{symbol}": {target}' for symbol, target in targets.items()) + "}"
    constants = (
        f"    LATE_CALL_ACCUM_TIMESTAMP = {timestamp}\n"
        f"    LATE_CALL_ACCUM_TARGETS = {target_repr}\n"
        f"    LATE_CALL_ACCUM_SIZE = {size}\n"
        f"    LATE_CALL_ACCUM_MIN_EDGE = {min_edge}"
    )
    block = (
        "            late_call_target = self.LATE_CALL_ACCUM_TARGETS.get(symbol)\n"
        "            if late_call_target is not None and timestamp >= self.LATE_CALL_ACCUM_TIMESTAMP and position < late_call_target:\n"
        "                for ask_price, ask_volume in book[\"sell_orders\"][:1]:\n"
        "                    if fair_adj - ask_price >= self.LATE_CALL_ACCUM_MIN_EDGE:\n"
        "                        qty = min(self.LATE_CALL_ACCUM_SIZE, late_call_target - position, max(0, -int(ask_volume)))\n"
        "                        if qty > 0:\n"
        "                            orders.append(Order(symbol, int(ask_price), int(qty)))\n"
        "                            position += qty\n\n"
        "            if symbol in {\"VEV_6000\", \"VEV_6500\"} and position < self.POSITION_LIMITS[symbol]:"
    )
    return [
        ("    OPTION_MARK_SPOT_WEIGHT = 0.0", "    OPTION_MARK_SPOT_WEIGHT = 0.0\n" + constants),
        ('            if symbol in {"VEV_6000", "VEV_6500"} and position < self.POSITION_LIMITS[symbol]:', block),
    ]


def option_delta_penalty_replacements(value: float) -> list[tuple[str, str]]:
    return [("    OPTION_DELTA_PENALTY = 0.0", f"    OPTION_DELTA_PENALTY = {value}")]


def velvet_final_exit_replacements(timestamp: int) -> list[tuple[str, str]]:
    return [
        ("    VELVET_REENTRY_TIMESTAMP = 80000", f"    VELVET_REENTRY_TIMESTAMP = 80000\n    VELVET_FINAL_EXIT_TIMESTAMP = {timestamp}"),
        (
            "                if self.VELVET_EXIT_TIMESTAMP <= timestamp < self.VELVET_REENTRY_TIMESTAMP:",
            "                if self.VELVET_EXIT_TIMESTAMP <= timestamp < self.VELVET_REENTRY_TIMESTAMP or timestamp >= self.VELVET_FINAL_EXIT_TIMESTAMP:",
        ),
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    write_variant(
        "round4_exp_220_hydro_mark_lock.py",
        hydro_mark_replacements(weight=1.0, threshold=1.2, size=32, passive_threshold=0.2, passive_size=18, mark22=-1.0),
    )
    write_variant(
        "round4_exp_221_hydro_mark_lock_strong.py",
        hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0),
    )
    write_variant(
        "round4_exp_222_hydro_tighter_active.py",
        [
            ("    HYDRO_SIGNAL_THRESHOLD = 1.1", "    HYDRO_SIGNAL_THRESHOLD = 0.6"),
            ("    HYDRO_TAKE_EDGE = 16.0", "    HYDRO_TAKE_EDGE = 10.0"),
            ("    HYDRO_MAKER_EDGE = 4.0", "    HYDRO_MAKER_EDGE = 2.0"),
            ("    HYDRO_QUOTE_SIZE = 72", "    HYDRO_QUOTE_SIZE = 96"),
            ("    HYDRO_TAKE_SIZE = 80", "    HYDRO_TAKE_SIZE = 120"),
            ("    HYDRO_MM_EDGE = 1.5", "    HYDRO_MM_EDGE = 1.0"),
            ("    HYDRO_MM_SIZE = 24", "    HYDRO_MM_SIZE = 48"),
        ],
    )
    write_variant(
        "round4_exp_223_hydro_tighter_nomaker.py",
        [
            ("    HYDRO_SIGNAL_THRESHOLD = 1.1", "    HYDRO_SIGNAL_THRESHOLD = 0.6"),
            ("    HYDRO_TAKE_EDGE = 16.0", "    HYDRO_TAKE_EDGE = 8.0"),
            ("    HYDRO_MAKER_EDGE = 4.0", "    HYDRO_MAKER_EDGE = 2.0"),
            ("    HYDRO_QUOTE_SIZE = 72", "    HYDRO_QUOTE_SIZE = 96"),
            ("    HYDRO_TAKE_SIZE = 80", "    HYDRO_TAKE_SIZE = 120"),
            ("    HYDRO_MM_ENABLED = True", "    HYDRO_MM_ENABLED = False"),
        ],
    )
    write_variant(
        "round4_exp_224_hydro_mark_after40_lock.py",
        hydro_mark_replacements(weight=1.0, threshold=1.0, size=40, passive_threshold=0.2, passive_size=24, mark22=-1.0)
        + [
            (
                '        hydro_mark_signal = self.mark_flow_signal(cache, state, "HYDROGEL_PACK", self.HYDRO_MARK_WEIGHTS, "hydro_mark_flow")',
                '        hydro_mark_signal = self.mark_flow_signal(cache, state, "HYDROGEL_PACK", self.HYDRO_MARK_WEIGHTS, "hydro_mark_flow")\n        if timestamp < 40_000:\n            hydro_mark_signal = 0.0',
            )
        ],
    )

    for reentry in (78_000, 80_000, 82_000, 85_000):
        write_variant(
            f"round4_exp_{225 + (reentry - 78_000) // 2_000}_cooldown_reentry_{reentry}.py",
            cooldown_replacements(reentry),
        )

    write_variant(
        "round4_exp_229_cooldown80000_5100size15.py",
        cooldown_replacements(80_000)
        + [
            ("    OPTION_SIZE_BY_STRIKE = {5000: 9, 5100: 9}", "    OPTION_SIZE_BY_STRIKE = {5000: 9, 5100: 15}"),
        ],
    )
    write_variant(
        "round4_exp_230_cooldown80000_hydro_mark_lock.py",
        cooldown_replacements(80_000)
        + hydro_mark_replacements(weight=1.0, threshold=1.2, size=32, passive_threshold=0.2, passive_size=18, mark22=-1.0),
    )
    for idx, reentry in enumerate((86_000, 88_000, 90_000, 92_000, 95_000), start=231):
        write_variant(
            f"round4_exp_{idx}_cooldown_reentry_{reentry}.py",
            cooldown_replacements(reentry),
        )
    idx = 240
    for vfe_reentry in (80_000, 85_000, 90_000):
        for vev_reentry in (80_000, 85_000, 90_000):
            if vfe_reentry == vev_reentry:
                continue
            write_variant(
                f"round4_exp_{idx}_cooldown_vfe{vfe_reentry}_vev5000_{vev_reentry}.py",
                cooldown_pair_replacements(vfe_reentry, vev_reentry),
            )
            idx += 1

    write_variant(
        "round4_exp_250_cooldown80000_hydro_mark_strong.py",
        cooldown_replacements(80_000)
        + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0),
    )
    write_variant(
        "round4_exp_251_cooldown85000_hydro_mark_strong.py",
        cooldown_replacements(85_000)
        + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0),
    )
    write_variant(
        "round4_exp_252_cooldown80000_hydro_mark_strong_exit60000.py",
        cooldown_replacements(80_000)
        + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0)
        + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")],
    )
    write_variant(
        "round4_exp_253_cooldown85000_hydro_mark_strong_exit60000.py",
        cooldown_replacements(85_000)
        + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0)
        + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")],
    )
    write_variant(
        "round4_exp_254_hydro_mark_strong_exit60000.py",
        hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0)
        + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")],
    )
    write_variant(
        "round4_exp_260_cooldown85000_staticcover_4000_4500_87300.py",
        cooldown_replacements(85_000)
        + passive_static_cover_replacements(87_300, ("VEV_4000", "VEV_4500"), 36),
    )
    write_variant(
        "round4_exp_261_cooldown85000_staticcover_4000_4500_85000.py",
        cooldown_replacements(85_000)
        + passive_static_cover_replacements(85_000, ("VEV_4000", "VEV_4500"), 36),
    )
    write_variant(
        "round4_exp_262_cooldown85000_staticcover_5200_5300_86400.py",
        cooldown_replacements(85_000)
        + passive_static_cover_replacements(86_400, ("VEV_5200", "VEV_5300"), 36),
    )
    write_variant(
        "round4_exp_263_cooldown85000_staticcover_broad_86400.py",
        cooldown_replacements(85_000)
        + passive_static_cover_replacements(86_400, ("VEV_4000", "VEV_4500", "VEV_5200", "VEV_5300"), 36),
    )
    for idx, threshold in enumerate((5246.0, 5248.0, 5250.0, 5252.0), start=270):
        write_variant(
            f"round4_exp_{idx}_vfe_mid_reentry_{int(threshold)}.py",
            vfe_mid_reentry_replacements(threshold),
        )
    write_variant(
        "round4_exp_274_vfe_mid5248_hydro_mark_strong.py",
        vfe_mid_reentry_replacements(5248.0)
        + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0)
        + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")],
    )

    c15 = candidate15_base_replacements()
    write_variant("round4_exp_280_c15_vfe_blended_orders.py", c15 + vfe_order_uses_blended_replacements())
    write_variant("round4_exp_281_c15_vfe_blended_mark05.py", c15 + vfe_order_uses_blended_replacements() + velvet_mark_weight_replacements(0.5))
    write_variant("round4_exp_282_c15_vfe_blended_mark10.py", c15 + vfe_order_uses_blended_replacements() + velvet_mark_weight_replacements(1.0))
    write_variant("round4_exp_283_c15_option_mark_fair10.py", c15 + option_mark_fair_replacements(1.0))
    write_variant("round4_exp_284_c15_option_mark_fair20.py", c15 + option_mark_fair_replacements(2.0))
    write_variant("round4_exp_285_c15_blended_option_mark10.py", c15 + vfe_order_uses_blended_replacements() + option_mark_fair_replacements(1.0))
    write_variant("round4_exp_286_c15_vfe_blended_take35.py", c15 + vfe_order_uses_blended_replacements() + velvet_relative_replacements(take_edge=3.5))
    write_variant("round4_exp_287_c15_vfe_blended_size120.py", c15 + vfe_order_uses_blended_replacements() + velvet_relative_replacements(take_size=120, passive_size=36))
    write_variant("round4_exp_288_c15_mid_sizes_12_12.py", c15 + option_mid_size_replacements(12, 12))
    write_variant("round4_exp_289_c15_mid_sizes_9_15.py", c15 + option_mid_size_replacements(9, 15))
    write_variant("round4_exp_290_c15_mid_sizes_15_15.py", c15 + option_mid_size_replacements(15, 15))
    write_variant("round4_exp_291_c15_mid_edges_1_025.py", c15 + option_mid_edge_replacements(1.0, 0.25))
    write_variant("round4_exp_292_c15_blended_mid_sizes_9_15.py", c15 + vfe_order_uses_blended_replacements() + option_mid_size_replacements(9, 15))
    write_variant("round4_exp_293_c15_blended_mid_edges_1_025.py", c15 + vfe_order_uses_blended_replacements() + option_mid_edge_replacements(1.0, 0.25))
    write_variant("round4_exp_294_c15_vfe_blended_mark05_optionmark10.py", c15 + vfe_order_uses_blended_replacements() + velvet_mark_weight_replacements(0.5) + option_mark_fair_replacements(1.0))

    write_variant("round4_exp_295_c15_option_mark_fair025.py", c15 + option_mark_fair_replacements(0.25))
    write_variant("round4_exp_296_c15_option_mark_fair050.py", c15 + option_mark_fair_replacements(0.5))
    write_variant("round4_exp_297_c15_option_mark_fair075.py", c15 + option_mark_fair_replacements(0.75))
    write_variant("round4_exp_298_c15_optionmark050_edges_1_025.py", c15 + option_mark_fair_replacements(0.5) + option_mid_edge_replacements(1.0, 0.25))
    write_variant("round4_exp_299_c15_optionmark025_edges_125_025.py", c15 + option_mark_fair_replacements(0.25) + option_mid_edge_replacements(1.25, 0.25))
    write_variant("round4_exp_300_c15_edges_125_025.py", c15 + option_mid_edge_replacements(1.25, 0.25))
    write_variant("round4_exp_301_c15_edges_150_025.py", c15 + option_mid_edge_replacements(1.5, 0.25))
    write_variant("round4_exp_302_c15_edges_125_050.py", c15 + option_mid_edge_replacements(1.25, 0.5))

    write_variant("round4_exp_303_c15_weak_exit_84000.py", c15 + weak_option_exit_replacements(84_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_304_c15_weak_exit_85000.py", c15 + weak_option_exit_replacements(85_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_305_c15_weak_exit_86000.py", c15 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_306_c15_weak_exit_87300.py", c15 + weak_option_exit_replacements(87_300, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_307_c15_weak_exit_90000.py", c15 + weak_option_exit_replacements(90_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_308_c15_weak_exit_5200_5300_5400.py", c15 + weak_option_exit_replacements(86_400, ("VEV_5200", "VEV_5300", "VEV_5400")))
    write_variant("round4_exp_309_c15_weak_exit_5200_5300_5400_5500.py", c15 + weak_option_exit_replacements(86_400, ("VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500")))
    write_variant("round4_exp_310_c15_no_weak_exit.py", c15 + weak_option_exit_replacements(999_999, ()))

    write_variant("round4_exp_311_c15_hydro_mark22_only.py", c15 + hydro_weight_map_replacements(0.0, 0.0, -2.0))
    write_variant("round4_exp_312_c15_hydro_mark22_stronger.py", c15 + hydro_weight_map_replacements(0.0, 0.0, -3.0))
    write_variant("round4_exp_313_c15_hydro_mark22_plus14.py", c15 + hydro_weight_map_replacements(1.0, 0.0, -2.0))
    write_variant("round4_exp_314_c15_hydro_short_horizon_weights.py", c15 + hydro_weight_map_replacements(1.2, -1.0, -2.5))
    write_variant("round4_exp_315_c15_hydro_exit58000.py", c15 + hydro_exit_replacements(58_000))
    write_variant("round4_exp_316_c15_hydro_exit60300.py", c15 + hydro_exit_replacements(60_300))
    write_variant("round4_exp_317_c15_hydro_exit62000.py", c15 + hydro_exit_replacements(62_000))
    write_variant("round4_exp_318_c15_hydro_exit65000.py", c15 + hydro_exit_replacements(65_000))

    hydro_plus14 = hydro_weight_map_replacements(1.0, 0.0, -2.0)
    write_variant("round4_exp_319_c15_hydro_plus14_weak86000.py", c15 + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_320_c15_hydro_plus14_optionmark025_edges_125_025.py", c15 + hydro_plus14 + option_mark_fair_replacements(0.25) + option_mid_edge_replacements(1.25, 0.25))
    write_variant("round4_exp_321_c15_hydro_plus14_weak86000_edges_125_025.py", c15 + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")) + option_mid_edge_replacements(1.25, 0.25))
    write_variant("round4_exp_322_c15_hydro_plus14_weak86000_optionmark025.py", c15 + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")) + option_mark_fair_replacements(0.25))
    write_variant("round4_exp_323_c15_hydro_plus14_weak86000_optionmark025_edges.py", c15 + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")) + option_mark_fair_replacements(0.25) + option_mid_edge_replacements(1.25, 0.25))
    write_variant("round4_exp_324_c15_hydro_plus14_weak87300.py", c15 + hydro_plus14 + weak_option_exit_replacements(87_300, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_325_c15_hydro_plus14_edges_125_025.py", c15 + hydro_plus14 + option_mid_edge_replacements(1.25, 0.25))
    write_variant("round4_exp_326_c15_hydro_plus14_optionmark025.py", c15 + hydro_plus14 + option_mark_fair_replacements(0.25))

    write_variant("round4_exp_327_c15_hydro_mark14_05.py", c15 + hydro_weight_map_replacements(0.5, 0.0, -2.0))
    write_variant("round4_exp_328_c15_hydro_mark14_15.py", c15 + hydro_weight_map_replacements(1.5, 0.0, -2.0))
    write_variant("round4_exp_329_c15_hydro_mark14_20.py", c15 + hydro_weight_map_replacements(2.0, 0.0, -2.0))
    write_variant("round4_exp_330_c15_hydro_mark22_minus15.py", c15 + hydro_weight_map_replacements(1.0, 0.0, -1.5))
    write_variant("round4_exp_331_c15_hydro_mark22_minus25.py", c15 + hydro_weight_map_replacements(1.0, 0.0, -2.5))

    base_plus14_weak = c15 + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300"))
    write_variant("round4_exp_332_c15_plus14_weak86000_lateexit_4000_4500_85200.py", base_plus14_weak + late_option_exit_replacements(85_200, ("VEV_4000", "VEV_4500")))
    write_variant("round4_exp_333_c15_plus14_weak86000_lateexit_4000_4500_86600.py", base_plus14_weak + late_option_exit_replacements(86_600, ("VEV_4000", "VEV_4500")))
    write_variant("round4_exp_334_c15_plus14_weak86000_lateexit_4000_4500_90000.py", base_plus14_weak + late_option_exit_replacements(90_000, ("VEV_4000", "VEV_4500")))
    write_variant("round4_exp_335_c15_plus14_weak86000_lateexit_4000_4500_92400.py", base_plus14_weak + late_option_exit_replacements(92_400, ("VEV_4000", "VEV_4500")))
    write_variant("round4_exp_336_c15_plus14_weak86000_lateexit_deep_far_85200.py", base_plus14_weak + late_option_exit_replacements(85_200, ("VEV_4000", "VEV_4500", "VEV_5400", "VEV_5500")))
    write_variant("round4_exp_337_c15_plus14_weak86000_lateexit_deep_far_90000.py", base_plus14_weak + late_option_exit_replacements(90_000, ("VEV_4000", "VEV_4500", "VEV_5400", "VEV_5500")))
    write_variant("round4_exp_338_c15_plus14_weak86000_lateexit_4000_90000.py", base_plus14_weak + late_option_exit_replacements(90_000, ("VEV_4000",)))
    write_variant("round4_exp_339_c15_plus14_weak86000_lateexit_4500_90000.py", base_plus14_weak + late_option_exit_replacements(90_000, ("VEV_4500",)))
    write_variant("round4_exp_340_c15_plus14_weak86000_lateexit_5400_5500_90000.py", base_plus14_weak + late_option_exit_replacements(90_000, ("VEV_5400", "VEV_5500")))
    write_variant("round4_exp_341_c15_plus14_weak86000_lateexit_all_90000.py", base_plus14_weak + late_option_exit_replacements(90_000, ("VEV_4000", "VEV_4500", "VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500")))

    write_variant("round4_exp_342_c15_reentry83000_plus14_weak86000.py", cooldown_replacements(83_000) + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0) + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")] + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_343_c15_reentry84000_plus14_weak86000.py", cooldown_replacements(84_000) + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0) + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")] + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_344_c15_reentry86000_plus14_weak86000.py", cooldown_replacements(86_000) + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0) + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")] + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_345_c15_reentry87000_plus14_weak86000.py", cooldown_replacements(87_000) + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0) + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")] + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_346_c15_vfe85000_vev5000_80000_plus14_weak86000.py", cooldown_pair_replacements(85_000, 80_000) + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0) + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")] + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_347_c15_vfe83000_vev5000_85000_plus14_weak86000.py", cooldown_pair_replacements(83_000, 85_000) + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0) + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")] + hydro_plus14 + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))

    write_variant("round4_exp_348_c15_plus14_weak86000_passivecover_4000_4500_85200_s36.py", base_plus14_weak + passive_static_cover_replacements(85_200, ("VEV_4000", "VEV_4500"), 36))
    write_variant("round4_exp_349_c15_plus14_weak86000_passivecover_4000_4500_86600_s36.py", base_plus14_weak + passive_static_cover_replacements(86_600, ("VEV_4000", "VEV_4500"), 36))
    write_variant("round4_exp_350_c15_plus14_weak86000_passivecover_4000_4500_90000_s36.py", base_plus14_weak + passive_static_cover_replacements(90_000, ("VEV_4000", "VEV_4500"), 36))
    write_variant("round4_exp_351_c15_plus14_weak86000_passivecover_4000_4500_90000_s12.py", base_plus14_weak + passive_static_cover_replacements(90_000, ("VEV_4000", "VEV_4500"), 12))
    write_variant("round4_exp_352_c15_plus14_weak86000_passivecover_4000_4500_90000_s72.py", base_plus14_weak + passive_static_cover_replacements(90_000, ("VEV_4000", "VEV_4500"), 72))
    write_variant("round4_exp_353_c15_plus14_weak86000_passivecover_5400_5500_90000_s36.py", base_plus14_weak + passive_static_cover_replacements(90_000, ("VEV_5400", "VEV_5500"), 36))
    write_variant("round4_exp_354_c15_plus14_weak86000_passivecover_deep_far_90000_s36.py", base_plus14_weak + passive_static_cover_replacements(90_000, ("VEV_4000", "VEV_4500", "VEV_5400", "VEV_5500"), 36))

    idx = 355
    for mark14, mark22 in (
        (0.00, -1.50),
        (0.00, -2.00),
        (0.25, -1.50),
        (0.25, -2.00),
        (0.50, -1.50),
        (0.50, -2.00),
        (0.75, -1.50),
        (0.75, -2.00),
        (1.00, -1.50),
        (1.00, -2.50),
        (1.25, -1.50),
        (1.25, -2.00),
        (1.50, -1.50),
        (1.50, -2.00),
    ):
        write_variant(
            f"round4_exp_{idx}_c15_plus14_weak86000_hydro_m14_{str(mark14).replace('.', 'p')}_m22_{str(abs(mark22)).replace('.', 'p')}.py",
            c15 + hydro_weight_map_replacements(mark14, 0.0, mark22) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")),
        )
        idx += 1

    for threshold, size, fair_weight in (
        (0.60, 48, 1.5),
        (1.00, 48, 1.5),
        (1.20, 48, 1.5),
        (0.80, 36, 1.5),
        (0.80, 60, 1.5),
        (0.80, 48, 1.0),
        (0.80, 48, 2.0),
    ):
        write_variant(
            f"round4_exp_{idx}_c15_plus14_weak86000_hydro_exec_t{str(threshold).replace('.', 'p')}_s{size}_fw{str(fair_weight).replace('.', 'p')}.py",
            c15
            + hydro_weight_map_replacements(1.0, 0.0, -2.0)
            + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300"))
            + [
                ("    HYDRO_MARK_EXEC_THRESHOLD = 0.8", f"    HYDRO_MARK_EXEC_THRESHOLD = {threshold}"),
                ("    HYDRO_MARK_EXEC_SIZE = 48", f"    HYDRO_MARK_EXEC_SIZE = {size}"),
                ("    HYDRO_MARK_FAIR_WEIGHT = 1.5", f"    HYDRO_MARK_FAIR_WEIGHT = {fair_weight}"),
            ],
        )
        idx += 1

    reentry80_hydro = (
        cooldown_replacements(80_000)
        + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0)
        + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")]
    )
    write_variant("round4_exp_376_reentry80000_plus14_weak86000.py", reentry80_hydro + hydro_weight_map_replacements(1.0, 0.0, -2.0) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_377_reentry80000_hydro075_weak86000.py", reentry80_hydro + hydro_weight_map_replacements(0.75, 0.0, -1.5) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_378_reentry80000_hydro025_weak86000.py", reentry80_hydro + hydro_weight_map_replacements(0.25, 0.0, -1.5) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_379_reentry80000_weak86000.py", cooldown_replacements(80_000) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")))
    write_variant("round4_exp_380_reentry80000_plus14.py", reentry80_hydro + hydro_weight_map_replacements(1.0, 0.0, -2.0))
    write_variant("round4_exp_381_reentry80000_hydro075.py", reentry80_hydro + hydro_weight_map_replacements(0.75, 0.0, -1.5))
    write_variant("round4_exp_382_reentry80000_hydro025.py", reentry80_hydro + hydro_weight_map_replacements(0.25, 0.0, -1.5))

    for exp_id, mark14 in (
        (383, 0.40),
        (384, 0.50),
        (385, 0.60),
        (386, 0.70),
        (387, 0.85),
    ):
        write_variant(
            f"round4_exp_{exp_id}_reentry80000_hydro_m14_{str(mark14).replace('.', 'p')}_weak86000.py",
            reentry80_hydro + hydro_weight_map_replacements(mark14, 0.0, -1.5) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")),
        )
    for exp_id, reentry, mark14 in (
        (388, 78_000, 0.75),
        (389, 82_000, 0.75),
        (390, 84_000, 0.75),
        (391, 78_000, 0.25),
        (392, 82_000, 0.25),
        (393, 84_000, 0.25),
    ):
        base = (
            cooldown_replacements(reentry)
            + hydro_mark_replacements(weight=1.5, threshold=0.8, size=48, passive_threshold=0.15, passive_size=36, mark22=-2.0)
            + [("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 60_000")]
        )
        write_variant(
            f"round4_exp_{exp_id}_reentry{reentry}_hydro_m14_{str(mark14).replace('.', 'p')}_weak86000.py",
            base + hydro_weight_map_replacements(mark14, 0.0, -1.5) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300")),
        )

    structural_base = reentry80_hydro + hydro_weight_map_replacements(0.75, 0.0, -1.5) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300"))
    write_variant("round4_exp_394_reentry80000_hydro075_weak86000_edges_125_025.py", structural_base + option_mid_edge_replacements(1.25, 0.25))
    write_variant("round4_exp_395_reentry80000_hydro075_weak86000_edges_150_025.py", structural_base + option_mid_edge_replacements(1.50, 0.25))
    write_variant("round4_exp_396_reentry80000_hydro075_weak86000_edges_125_000.py", structural_base + option_mid_edge_replacements(1.25, 0.00))
    write_variant("round4_exp_397_reentry80000_hydro075_weak86000_size_9_15.py", structural_base + option_mid_size_replacements(9, 15))
    write_variant("round4_exp_398_reentry80000_hydro075_weak86000_size_9_20.py", structural_base + option_mid_size_replacements(9, 20))
    write_variant("round4_exp_399_reentry80000_hydro075_weak86000_size_12_15.py", structural_base + option_mid_size_replacements(12, 15))
    write_variant("round4_exp_400_reentry80000_hydro075_weak86000_edges_size.py", structural_base + option_mid_edge_replacements(1.25, 0.25) + option_mid_size_replacements(9, 15))
    write_variant("round4_exp_401_reentry80000_hydro075_weak86000_late5100_85000_edge0.py", structural_base + late_call_accum_replacements(85_000, {"VEV_5100": 300}, 24, 0.0))
    write_variant("round4_exp_402_reentry80000_hydro075_weak86000_late5100_90000_edge0.py", structural_base + late_call_accum_replacements(90_000, {"VEV_5100": 300}, 24, 0.0))
    write_variant("round4_exp_403_reentry80000_hydro075_weak86000_late5100_90000_edgem1.py", structural_base + late_call_accum_replacements(90_000, {"VEV_5100": 300}, 24, -1.0))
    write_variant("round4_exp_404_reentry80000_hydro075_weak86000_late5100_5200_90000_edge0.py", structural_base + late_call_accum_replacements(90_000, {"VEV_5100": 300, "VEV_5200": 150}, 24, 0.0))
    write_variant("round4_exp_405_reentry80000_hydro075_weak86000_delta_penalty_0005.py", structural_base + option_delta_penalty_replacements(0.005))
    write_variant("round4_exp_406_reentry80000_hydro075_weak86000_delta_penalty_001.py", structural_base + option_delta_penalty_replacements(0.01))
    write_variant("round4_exp_407_reentry80000_hydro075_weak86000_delta_penalty_neg0005.py", structural_base + option_delta_penalty_replacements(-0.005))

    write_variant("round4_exp_408_reentry80000_hydro075_weak86000_exit_5000_5100_92400.py", structural_base + late_option_exit_replacements(92_400, ("VEV_5000", "VEV_5100")))
    write_variant("round4_exp_409_reentry80000_hydro075_weak86000_exit_5000_5100_95500.py", structural_base + late_option_exit_replacements(95_500, ("VEV_5000", "VEV_5100")))
    write_variant("round4_exp_410_reentry80000_hydro075_weak86000_exit_vfe_92400.py", structural_base + velvet_final_exit_replacements(92_400))
    write_variant("round4_exp_411_reentry80000_hydro075_weak86000_exit_vfe_95500.py", structural_base + velvet_final_exit_replacements(95_500))
    write_variant("round4_exp_412_reentry80000_hydro075_weak86000_exit_vfe_5000_5100_92400.py", structural_base + velvet_final_exit_replacements(92_400) + late_option_exit_replacements(92_400, ("VEV_5000", "VEV_5100")))
    write_variant("round4_exp_413_reentry80000_hydro075_weak86000_exit_vfe_5000_5100_95500.py", structural_base + velvet_final_exit_replacements(95_500) + late_option_exit_replacements(95_500, ("VEV_5000", "VEV_5100")))
    write_variant("round4_exp_414_reentry80000_hydro075_weak86000_exit_vfe95500_5000_5100_92400.py", structural_base + velvet_final_exit_replacements(95_500) + late_option_exit_replacements(92_400, ("VEV_5000", "VEV_5100")))
    write_variant("round4_exp_415_reentry80000_hydro075_weak86000_exit_vfe95500_5100_92400_5000_95500.py", structural_base + velvet_final_exit_replacements(95_500) + late_option_exit_replacements(92_400, ("VEV_5100",)))

    high_window_base = reentry80_hydro + hydro_weight_map_replacements(0.25, 0.0, -1.5) + weak_option_exit_replacements(86_000, ("VEV_5200", "VEV_5300"))
    for exp_id, lock_ts in (
        (416, 91_800),
        (417, 92_400),
        (418, 93_000),
        (419, 93_600),
    ):
        write_variant(
            f"round4_exp_{exp_id}_reentry80000_hydro025_profitlock_{lock_ts}.py",
            high_window_base + velvet_final_exit_replacements(lock_ts) + late_option_exit_replacements(lock_ts, ("VEV_5000", "VEV_5100")),
        )
    for exp_id, lock_ts in (
        (420, 91_800),
        (421, 93_000),
        (422, 93_600),
        (423, 94_200),
    ):
        write_variant(
            f"round4_exp_{exp_id}_reentry80000_hydro075_profitlock_{lock_ts}.py",
            structural_base + velvet_final_exit_replacements(lock_ts) + late_option_exit_replacements(lock_ts, ("VEV_5000", "VEV_5100")),
        )


if __name__ == "__main__":
    main()
