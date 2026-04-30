from __future__ import annotations

import csv
import json
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ROUND5" / "research" / "outputs"

BASE_PATH = ROOT / "ROUND5" / "research" / "score_unresolved_edge_probes.py"
spec = importlib.util.spec_from_file_location("base_unresolved_score", BASE_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)

PROBES = [
    "unresolved_probe_portal_best_all.py",
    "unresolved_probe_sleep.py",
    "unresolved_probe_micro_robot_panel.py",
]


def fmt(value):
    return "" if value is None else f"{float(value):.2f}"


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    probe_dir = ROOT / "ROUND5" / "research" / "probes"
    rows = []
    raw = {}
    for probe in PROBES:
        print(f"Full scoring {probe}...")
        path = probe_dir / probe
        raw[probe] = {
            "kevin_full": base.run_tool("kevin", path, "5", ROOT / "outputs" / "tool-data" / "kevin", "full", config),
            "xeeshan_full": base.run_tool("xeeshan", path, "5", ROOT / "outputs" / "tool-data" / "xeeshan", "full", config),
        }
        rows.append({"Probe": probe, "Kevin Full": fmt(raw[probe]["kevin_full"]["profit"]), "Xeeshan Full": fmt(raw[probe]["xeeshan_full"]["profit"])})
    (OUT / "unresolved_promising_full_raw.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    with (OUT / "unresolved_promising_full_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Probe", "Kevin Full", "Xeeshan Full"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
