from __future__ import annotations

import csv
import json
from pathlib import Path

from score_candidates_31_33_state_repair import (
    OUTPUT_DIR,
    ROUND_DIR,
    STRATEGY_DIR,
    diagnose_raw_568593,
    fmt,
    make_truncation_copy,
    measure_state_size,
    run_tool,
)


ROOT = Path(__file__).resolve().parents[2]


def load_existing_rows() -> list[dict[str, str]]:
    path = OUTPUT_DIR / "candidate_31_33_score_table.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_four_row_outputs(rows: list[dict[str, str]], raw_diag: dict) -> None:
    headers = [
        "Strategy",
        "Base",
        "Portal Kevin Uncapped",
        "Portal Xeeshan Uncapped",
        "Portal Kevin 50k Cap",
        "Portal Xeeshan 50k Cap",
        "Max traderData Length",
        "Official-Safe?",
    ]
    with (OUTPUT_DIR / "candidate_31_34_score_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "| Strategy | Base | Portal Kevin Uncapped | Portal Xeeshan Uncapped | Portal Kevin 50k Cap | Portal Xeeshan 50k Cap | Max traderData Length | Official-Safe? |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['Strategy']} | {row['Base']} | {row['Portal Kevin Uncapped']} | {row['Portal Xeeshan Uncapped']} | {row['Portal Kevin 50k Cap']} | {row['Portal Xeeshan 50k Cap']} | {row['Max traderData Length']} | {row['Official-Safe?']} |"
        )
    (OUTPUT_DIR / "candidate_31_34_score_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    with (OUTPUT_DIR / "candidate_31_34_state_size_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Strategy", "Base", "Max traderData Length"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"Strategy": row["Strategy"], "Base": row["Base"], "Max traderData Length": row["Max traderData Length"]})

    mismatch = abs((raw_diag["kevin_uncapped"]["profit"] or 0) - (raw_diag["kevin_capped"]["profit"] or 0))
    notes = [
        "# Candidate 31-34 State-Safe Table",
        "",
        "## 568593 Diagnosis",
        f"- Raw official submission max state: `{raw_diag['state_size']['max_len']}`.",
        f"- Raw uncapped Kevin/Xeeshan: `{fmt(raw_diag['kevin_uncapped']['profit'])}` / `{fmt(raw_diag['xeeshan_uncapped']['profit'])}`.",
        f"- Raw forced-50k Kevin/Xeeshan: `{fmt(raw_diag['kevin_capped']['profit'])}` / `{fmt(raw_diag['xeeshan_capped']['profit'])}`.",
        f"- Verdict: {'state cap is the problem' if mismatch > 100 else 'state cap is not the problem'}.",
        "",
        "## Candidate 34 Repair",
        "- `round5_candidate_34.py` is `568593.py` with the same compact state serializer used for candidates 31-33.",
        "- Trading logic was not intentionally changed.",
        "- Submit priority among these four should be based on capped portal replay.",
    ]
    (OUTPUT_DIR / "candidate_31_34_state_repair_notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    strategy = "round5_candidate_34.py"
    raw_diag = diagnose_raw_568593(config)
    strategy_path = STRATEGY_DIR / strategy
    capped_path = make_truncation_copy(strategy)
    size = measure_state_size(strategy_path)
    print(f"Scoring repaired {strategy} only...", flush=True)
    repaired = {
        "kevin_uncapped": run_tool("kevin", strategy_path, "portal_uncapped", config),
        "xeeshan_uncapped": run_tool("xeeshan", strategy_path, "portal_uncapped", config),
        "kevin_capped": run_tool("kevin", capped_path, "portal_50kcap", config),
        "xeeshan_capped": run_tool("xeeshan", capped_path, "portal_50kcap", config),
        "state_size": size,
    }
    (OUTPUT_DIR / "candidate_34_raw_backtests.json").write_text(json.dumps({"raw_568593": raw_diag, strategy: repaired}, indent=2), encoding="utf-8")

    rows = [row for row in load_existing_rows() if row["Strategy"] != strategy]
    ku = repaired["kevin_uncapped"]["profit"]
    xu = repaired["xeeshan_uncapped"]["profit"]
    kc = repaired["kevin_capped"]["profit"]
    xc = repaired["xeeshan_capped"]["profit"]
    rows.append(
        {
            "Strategy": strategy,
            "Base": "568593.py",
            "Portal Kevin Uncapped": fmt(ku),
            "Portal Xeeshan Uncapped": fmt(xu),
            "Portal Kevin 50k Cap": fmt(kc),
            "Portal Xeeshan 50k Cap": fmt(xc),
            "Max traderData Length": str(size["max_len"]),
            "Official-Safe?": "yes" if size["max_len"] < 45000 and abs((ku or 0) - (kc or 0)) <= 5 and abs((xu or 0) - (xc or 0)) <= 5 else "check",
        }
    )
    write_four_row_outputs(rows, raw_diag)
    print(f"Done. {strategy}: max state {size['max_len']}, Kevin {fmt(ku)} / cap {fmt(kc)}", flush=True)


if __name__ == "__main__":
    main()
