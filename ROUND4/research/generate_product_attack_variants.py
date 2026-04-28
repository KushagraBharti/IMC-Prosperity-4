from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "ROUND4" / "strategies" / "round4_candidate_1_522830_base.py"
OUT = ROOT / "ROUND4" / "strategies"


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f"Missing replacement target: {old!r}")
    return text.replace(old, new, 1)


def with_option_size_map(text: str, mapping: dict[int, int], default_size: int = 20) -> str:
    map_repr = "{" + ", ".join(f"{strike}: {size}" for strike, size in sorted(mapping.items())) + "}"
    text = replace_once(
        text,
        "    OPTION_SIZE = 20\n",
        f"    OPTION_SIZE = {default_size}\n    OPTION_SIZE_BY_STRIKE = {map_repr}\n",
    )
    old = "                    qty = self.OPTION_SIZE if edge < edge_threshold + 2.0 else 2 * self.OPTION_SIZE"
    new = (
        "                    base_size = self.OPTION_SIZE_BY_STRIKE.get(strike, self.OPTION_SIZE)\n"
        "                    qty = base_size if edge < edge_threshold + 2.0 else 2 * base_size"
    )
    text = text.replace(old, new)
    return text


def patch_common(text: str, replacements: list[tuple[str, str]]) -> str:
    for old, new in replacements:
        text = replace_once(text, old, new)
    return text


def write_variant(name: str, *, option_map: dict[int, int] | None = None, default_size: int = 20, replacements: list[tuple[str, str]] | None = None) -> None:
    text = BASE.read_text(encoding="utf-8")
    if option_map is not None:
        text = with_option_size_map(text, option_map, default_size=default_size)
    if replacements:
        text = patch_common(text, replacements)
    (OUT / name).write_text(text, encoding="utf-8")


MID_ACTIVE_9 = {5000: 9, 5100: 9}
MID_ACTIVE_9_WITH_4500 = {4500: 12, 5000: 9, 5100: 9}
STATIC_SHORT_FORCE = {4000: 24, 4500: 20, 5000: 9, 5100: 9, 5200: 20, 5300: 20, 5400: 20, 5500: 20}


def main() -> None:
    # VEV_4000 repair: preserve baseline clip size for static shorts, reduce only the active middle strikes.
    write_variant(
        "round4_exp_01_mid9_static20.py",
        option_map=MID_ACTIVE_9,
        default_size=20,
    )
    write_variant(
        "round4_exp_02_mid9_static20_hydrofairoff.py",
        option_map=MID_ACTIVE_9,
        default_size=20,
        replacements=[("    HYDRO_MARK_FAIR_WEIGHT = 1.5", "    HYDRO_MARK_FAIR_WEIGHT = 0.0")],
    )
    write_variant(
        "round4_exp_03_staticforce_mid9.py",
        option_map=STATIC_SHORT_FORCE,
        default_size=20,
    )

    # Late-session active-product management probes. These intentionally target the plateau/giveback zone.
    write_variant(
        "round4_exp_04_mid9_exit_5000_5100_85200.py",
        option_map=MID_ACTIVE_9,
        default_size=20,
        replacements=[
            ("    WEAK_OPTION_EXIT_TIMESTAMP = 999_999", "    WEAK_OPTION_EXIT_TIMESTAMP = 85_200"),
            ("    WEAK_OPTION_EXIT_SET = set()", '    WEAK_OPTION_EXIT_SET = {"VEV_5000", "VEV_5100"}'),
        ],
    )
    write_variant(
        "round4_exp_05_mid9_exit_5000_5100_90000.py",
        option_map=MID_ACTIVE_9,
        default_size=20,
        replacements=[
            ("    WEAK_OPTION_EXIT_TIMESTAMP = 999_999", "    WEAK_OPTION_EXIT_TIMESTAMP = 90_000"),
            ("    WEAK_OPTION_EXIT_SET = set()", '    WEAK_OPTION_EXIT_SET = {"VEV_5000", "VEV_5100"}'),
        ],
    )
    write_variant(
        "round4_exp_09_mid9_hydrofairoff_exit_4000_4500_43000.py",
        option_map=MID_ACTIVE_9,
        default_size=20,
        replacements=[
            ("    HYDRO_MARK_FAIR_WEIGHT = 1.5", "    HYDRO_MARK_FAIR_WEIGHT = 0.0"),
            ("    WEAK_OPTION_EXIT_TIMESTAMP = 999_999", "    WEAK_OPTION_EXIT_TIMESTAMP = 43_000"),
            ("    WEAK_OPTION_EXIT_SET = set()", '    WEAK_OPTION_EXIT_SET = {"VEV_4000", "VEV_4500"}'),
        ],
    )
    write_variant(
        "round4_exp_10_mid9_hydrofairoff_exit_static_86600.py",
        option_map=MID_ACTIVE_9,
        default_size=20,
        replacements=[
            ("    HYDRO_MARK_FAIR_WEIGHT = 1.5", "    HYDRO_MARK_FAIR_WEIGHT = 0.0"),
            ("    WEAK_OPTION_EXIT_TIMESTAMP = 999_999", "    WEAK_OPTION_EXIT_TIMESTAMP = 86_600"),
            ("    WEAK_OPTION_EXIT_SET = set()", '    WEAK_OPTION_EXIT_SET = {"VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500"}'),
        ],
    )
    write_variant(
        "round4_exp_11_mid9_hydrofairoff_exit_all_static_86600.py",
        option_map=MID_ACTIVE_9,
        default_size=20,
        replacements=[
            ("    HYDRO_MARK_FAIR_WEIGHT = 1.5", "    HYDRO_MARK_FAIR_WEIGHT = 0.0"),
            ("    WEAK_OPTION_EXIT_TIMESTAMP = 999_999", "    WEAK_OPTION_EXIT_TIMESTAMP = 86_600"),
            ("    WEAK_OPTION_EXIT_SET = set()", '    WEAK_OPTION_EXIT_SET = {"VEV_4000", "VEV_4500", "VEV_5200", "VEV_5300", "VEV_5400", "VEV_5500"}'),
        ],
    )

    # Hydrogel isolation probes.
    write_variant(
        "round4_exp_06_nohydro.py",
        replacements=[("    TRADE_START_TIMESTAMP = 0", "    TRADE_START_TIMESTAMP = 999_999")],
    )
    write_variant(
        "round4_exp_07_hydro_late_flatten_40000.py",
        replacements=[("    HYDRO_EXIT_TIMESTAMP = 999_999", "    HYDRO_EXIT_TIMESTAMP = 40_000")],
    )
    write_variant(
        "round4_exp_08_hydro_more_passive_mark38.py",
        replacements=[
            ("    HYDRO_MARK_FAIR_WEIGHT = 1.5", "    HYDRO_MARK_FAIR_WEIGHT = 0.0"),
            ("    HYDRO_TAKE_EDGE = 16.0", "    HYDRO_TAKE_EDGE = 10.0"),
            ("    HYDRO_MAKER_EDGE = 4.0", "    HYDRO_MAKER_EDGE = 2.0"),
            ("    HYDRO_QUOTE_SIZE = 72", "    HYDRO_QUOTE_SIZE = 96"),
            ("    HYDRO_TAKE_SIZE = 80", "    HYDRO_TAKE_SIZE = 120"),
            ("    HYDRO_PASSIVE_MARK_THRESHOLD = 0.5", "    HYDRO_PASSIVE_MARK_THRESHOLD = 0.2"),
            ("    HYDRO_PASSIVE_MARK_EDGE = 2.0", "    HYDRO_PASSIVE_MARK_EDGE = 1.0"),
            ("    HYDRO_PASSIVE_MARK_SIZE = 18", "    HYDRO_PASSIVE_MARK_SIZE = 48"),
            ("    HYDRO_MM_EDGE = 1.5", "    HYDRO_MM_EDGE = 1.0"),
            ("    HYDRO_MM_SIZE = 24", "    HYDRO_MM_SIZE = 48"),
        ],
    )
    write_variant(
        "round4_exp_12_mid9_static20_hydromore.py",
        option_map=MID_ACTIVE_9,
        default_size=20,
        replacements=[
            ("    HYDRO_MARK_FAIR_WEIGHT = 1.5", "    HYDRO_MARK_FAIR_WEIGHT = 0.0"),
            ("    HYDRO_TAKE_EDGE = 16.0", "    HYDRO_TAKE_EDGE = 10.0"),
            ("    HYDRO_MAKER_EDGE = 4.0", "    HYDRO_MAKER_EDGE = 2.0"),
            ("    HYDRO_QUOTE_SIZE = 72", "    HYDRO_QUOTE_SIZE = 96"),
            ("    HYDRO_TAKE_SIZE = 80", "    HYDRO_TAKE_SIZE = 120"),
            ("    HYDRO_PASSIVE_MARK_THRESHOLD = 0.5", "    HYDRO_PASSIVE_MARK_THRESHOLD = 0.2"),
            ("    HYDRO_PASSIVE_MARK_EDGE = 2.0", "    HYDRO_PASSIVE_MARK_EDGE = 1.0"),
            ("    HYDRO_PASSIVE_MARK_SIZE = 18", "    HYDRO_PASSIVE_MARK_SIZE = 48"),
            ("    HYDRO_MM_EDGE = 1.5", "    HYDRO_MM_EDGE = 1.0"),
            ("    HYDRO_MM_SIZE = 24", "    HYDRO_MM_SIZE = 48"),
        ],
    )
    print(OUT)


if __name__ == "__main__":
    main()
