from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STRATEGY_DIR = ROOT / "ROUND4" / "strategies"
EXPERIMENT_DIR = ROOT / "ROUND4" / "research" / "strategy_experiments"


def write_variant(source: str, name: str, replacements: list[tuple[str, str]]) -> None:
    text = (STRATEGY_DIR / source).read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in text:
            raise ValueError(f"{old!r} not found for {name}")
        text = text.replace(old, new, 1)
    path = EXPERIMENT_DIR / name
    path.write_text(text, encoding="utf-8")
    print(path)


def main() -> None:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    c4 = "round4_candidate_4_vev4000_repair_mid9_hydrofairoff.py"
    c6 = "round4_candidate_6_hydro_more_mid9.py"
    c7 = "round4_candidate_7_exit_5200_5300_86600.py"

    write_variant(
        c7,
        "round4_exp_18_c7_hydro_exit60300.py",
        [("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300")],
    )
    write_variant(
        c7,
        "round4_exp_19_c7_hydro_exit60000.py",
        [("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_000")],
    )
    write_variant(
        c4,
        "round4_exp_20_c4_hydro_exit60300.py",
        [("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300")],
    )
    write_variant(
        c6,
        "round4_exp_21_c6_hydro_exit60300.py",
        [("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300")],
    )
    write_variant(
        c7,
        "round4_exp_22_c7_hydro_mark22_fade_exit60300.py",
        [
            ("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300"),
            ('"Mark 22": 0.25,', '"Mark 22": -1.0,'),
        ],
    )
    write_variant(
        c7,
        "round4_exp_23_c7_hydro_mark_exec_exit60300.py",
        [
            ("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300"),
            ("HYDRO_MARK_FAIR_WEIGHT = 0.0", "HYDRO_MARK_FAIR_WEIGHT = 1.0"),
            ("HYDRO_MARK_EXEC_THRESHOLD = 99.0", "HYDRO_MARK_EXEC_THRESHOLD = 1.2"),
            ("HYDRO_MARK_EXEC_SIZE = 0", "HYDRO_MARK_EXEC_SIZE = 32"),
            ("HYDRO_PASSIVE_MARK_THRESHOLD = 0.5", "HYDRO_PASSIVE_MARK_THRESHOLD = 0.2"),
            ('"Mark 22": 0.25,', '"Mark 22": -1.0,'),
        ],
    )
    write_variant(
        c7,
        "round4_exp_24_c7_hydro_no_mm_exit60300.py",
        [
            ("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300"),
            ("HYDRO_MM_ENABLED = True", "HYDRO_MM_ENABLED = False"),
        ],
    )
    write_variant(
        c7,
        "round4_exp_25_c7_mid15_hydro_exit60300.py",
        [
            ("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300"),
            ("OPTION_SIZE_BY_STRIKE = {5000: 9, 5100: 9}", "OPTION_SIZE_BY_STRIKE = {5000: 15, 5100: 15}"),
        ],
    )
    write_variant(
        c7,
        "round4_exp_26_c7_mid20_hydro_exit60300.py",
        [
            ("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300"),
            ("OPTION_SIZE_BY_STRIKE = {5000: 9, 5100: 9}", "OPTION_SIZE_BY_STRIKE = {5000: 20, 5100: 20}"),
        ],
    )
    write_variant(
        c7,
        "round4_exp_27_c7_5100size15_hydro_exit60300.py",
        [
            ("HYDRO_EXIT_TIMESTAMP = 999_999", "HYDRO_EXIT_TIMESTAMP = 60_300"),
            ("OPTION_SIZE_BY_STRIKE = {5000: 9, 5100: 9}", "OPTION_SIZE_BY_STRIKE = {5000: 9, 5100: 15}"),
        ],
    )


if __name__ == "__main__":
    main()
