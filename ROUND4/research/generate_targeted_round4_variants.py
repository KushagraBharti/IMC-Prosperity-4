from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "ROUND4" / "strategies" / "round4_candidate_1_522830_base.py"
OUT = ROOT / "ROUND4" / "research" / "outputs" / "mini_experiments" / "generated_targeted_variants"


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f"Missing replacement target: {old!r}")
    return text.replace(old, new, 1)


def build(name: str, replacements: list[tuple[str, str]]) -> None:
    text = BASE.read_text(encoding="utf-8")
    for old, new in replacements:
        text = replace_once(text, old, new)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(text, encoding="utf-8")


def option_size(size: int) -> tuple[str, str]:
    return ("    OPTION_SIZE = 20", f"    OPTION_SIZE = {size}")


NO_HYDRO = [
    ("    HYDRO_MARK_FAIR_WEIGHT = 1.5", "    HYDRO_MARK_FAIR_WEIGHT = 0.0"),
    ("    HYDRO_PASSIVE_MARK_SIZE = 18", "    HYDRO_PASSIVE_MARK_SIZE = 0"),
]

HYDRO_FAIR_OFF = [
    ("    HYDRO_MARK_FAIR_WEIGHT = 1.5", "    HYDRO_MARK_FAIR_WEIGHT = 0.0"),
]

HYDRO_PASSIVE_OFF = [
    ("    HYDRO_PASSIVE_MARK_SIZE = 18", "    HYDRO_PASSIVE_MARK_SIZE = 0"),
]

VFE_CONSERVATIVE = [
    ("    VELVET_REL_TAKE_EDGE = 5.0", "    VELVET_REL_TAKE_EDGE = 5.5"),
    ("    VELVET_REL_TAKE_SIZE = 70", "    VELVET_REL_TAKE_SIZE = 50"),
]

FREE_BIDS_OFF = [
    ("    FREE_OPTION_BID_SIZE = 24", "    FREE_OPTION_BID_SIZE = 0"),
]

FREE_BIDS_SMALL = [
    ("    FREE_OPTION_BID_SIZE = 24", "    FREE_OPTION_BID_SIZE = 12"),
]

FREE_BIDS_LARGE = [
    ("    FREE_OPTION_BID_SIZE = 24", "    FREE_OPTION_BID_SIZE = 36"),
]

SAFER_EDGES = [
    (
        """    OPTION_EDGE = {
        4000: 10.00,
        4500: 2.00,
        5000: 1.50,
        5100: 0.50,
        5200: 7.00,
        5300: 3.00,
        5400: 1.00,
        5500: 3.00,
        6000: 0.50,
        6500: 0.50,
    }""",
        """    OPTION_EDGE = {
        4000: 10.00,
        4500: 2.50,
        5000: 2.00,
        5100: 1.00,
        5200: 7.50,
        5300: 3.50,
        5400: 1.50,
        5500: 3.50,
        6000: 1.00,
        6500: 1.00,
    }""",
    )
]

LOOSER_MID_EDGES = [
    (
        """    OPTION_EDGE = {
        4000: 10.00,
        4500: 2.00,
        5000: 1.50,
        5100: 0.50,
        5200: 7.00,
        5300: 3.00,
        5400: 1.00,
        5500: 3.00,
        6000: 0.50,
        6500: 0.50,
    }""",
        """    OPTION_EDGE = {
        4000: 10.00,
        4500: 2.00,
        5000: 1.25,
        5100: 0.25,
        5200: 6.00,
        5300: 2.50,
        5400: 0.75,
        5500: 2.50,
        6000: 0.50,
        6500: 0.50,
    }""",
    )
]


def main() -> None:
    specs = {
        "r4_target_option_size_9.py": [option_size(9)],
        "r4_target_option_size_9_nohydro.py": [option_size(9), *NO_HYDRO],
        "r4_target_option_size_9_hydro_fair_off.py": [option_size(9), *HYDRO_FAIR_OFF],
        "r4_target_option_size_9_hydro_passive_off.py": [option_size(9), *HYDRO_PASSIVE_OFF],
        "r4_target_option_size_9_free_bids_off.py": [option_size(9), *FREE_BIDS_OFF],
        "r4_target_option_size_9_safer_edges.py": [option_size(9), *SAFER_EDGES],
        "r4_target_option_size_10.py": [option_size(10)],
        "r4_target_option_size_11.py": [option_size(11)],
        "r4_target_option_size_10_nohydro.py": [option_size(10), *NO_HYDRO],
        "r4_target_option_size_10_hydro_fair_off.py": [option_size(10), *HYDRO_FAIR_OFF],
        "r4_target_option_size_10_hydro_passive_off.py": [option_size(10), *HYDRO_PASSIVE_OFF],
        "r4_target_option_size_10_vfe_conservative.py": [option_size(10), *VFE_CONSERVATIVE],
        "r4_target_option_size_10_nohydro_vfe_conservative.py": [option_size(10), *NO_HYDRO, *VFE_CONSERVATIVE],
        "r4_target_option_size_10_free_bids_off.py": [option_size(10), *FREE_BIDS_OFF],
        "r4_target_option_size_10_free_bids_small.py": [option_size(10), *FREE_BIDS_SMALL],
        "r4_target_option_size_10_free_bids_large.py": [option_size(10), *FREE_BIDS_LARGE],
        "r4_target_option_size_10_safer_edges.py": [option_size(10), *SAFER_EDGES],
        "r4_target_option_size_10_looser_mid_edges.py": [option_size(10), *LOOSER_MID_EDGES],
    }
    for name, replacements in specs.items():
        build(name, replacements)
    print(OUT)


if __name__ == "__main__":
    main()
