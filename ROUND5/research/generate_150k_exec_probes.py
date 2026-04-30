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

    print(f"Wrote {len(list(PROBE_DIR.glob('probe_*.py')))} probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
