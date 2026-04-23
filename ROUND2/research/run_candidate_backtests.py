from __future__ import annotations

import csv
import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "ROUND2" / "research" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STRATEGIES = [
    ROOT / "ROUND2" / "strategies" / "pepper_only_baseline.py",
    ROOT / "ROUND2" / "strategies" / "pepper_only_residual_harvest.py",
    ROOT / "ROUND2" / "strategies" / "pepper_only_adaptive.py",
    ROOT / "ROUND2" / "strategies" / "osmium_only_legacy.py",
    ROOT / "ROUND2" / "strategies" / "osmium_only_simple10002.py",
    ROOT / "ROUND2" / "strategies" / "osmium_only_adaptive.py",
]


def run_tool(script_name: str, strategy: Path) -> str:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ROOT / "scripts" / script_name),
        "-Strategy",
        str(strategy),
    ]
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def parse_xeeshan(stdout: str) -> tuple[float, float, float]:
    totals = re.findall(r"Total profit:\s*([0-9,.-]+)", stdout)
    total = float(totals[-1].replace(",", ""))
    osmium = sum(
        float(x.replace(",", ""))
        for x in re.findall(r"ASH_COATED_OSMIUM:\s*([0-9,.-]+)", stdout)
    )
    pepper = sum(
        float(x.replace(",", ""))
        for x in re.findall(r"INTARIAN_PEPPER_ROOT:\s*([0-9,.-]+)", stdout)
    )
    return total, osmium, pepper


def parse_kevin(stdout: str) -> tuple[float, float, float]:
    totals = re.findall(r"Total profit:\s*([0-9,.-]+)", stdout)
    total = float(totals[-1].replace(",", ""))
    osmium = sum(
        float(x.replace(",", ""))
        for x in re.findall(r"ASH_COATED_OSMIUM:\s*([0-9,.-]+)", stdout)
    )
    pepper = sum(
        float(x.replace(",", ""))
        for x in re.findall(r"INTARIAN_PEPPER_ROOT:\s*([0-9,.-]+)", stdout)
    )
    return total, osmium, pepper


def parse_rust(stdout: str) -> tuple[float, float, float, int]:
    total = float(re.search(r"TOTAL\s+-\s+\d+\s+(\d+)\s+([0-9.]+)", stdout).group(2))
    own_trades = int(re.search(r"TOTAL\s+-\s+\d+\s+(\d+)\s+[0-9.]+", stdout).group(1))
    osmium = float(re.search(r"ASH_COATED_OSMIUM\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+([0-9.]+)", stdout).group(1))
    pepper = float(re.search(r"INTARIAN_PEPPER_ROOT\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+([0-9.]+)", stdout).group(1))
    return total, osmium, pepper, own_trades


def main() -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_csv = OUTPUT_DIR / f"single_product_candidate_backtests_{timestamp}.csv"
    rows = []

    for strategy in STRATEGIES:
        print(f"Running {strategy.name}")
        x_stdout = run_tool("bt-xeeshan-round2.ps1", strategy)
        k_stdout = run_tool("bt-kevin-round2.ps1", strategy)
        r_stdout = run_tool("bt-rust-round2.ps1", strategy)

        x_total, x_osmium, x_pepper = parse_xeeshan(x_stdout)
        k_total, k_osmium, k_pepper = parse_kevin(k_stdout)
        r_total, r_osmium, r_pepper, r_trades = parse_rust(r_stdout)

        rows.append(
            {
                "name": strategy.stem,
                "path": str(strategy),
                "xeeshan_total": x_total,
                "xeeshan_osmium": x_osmium,
                "xeeshan_pepper": x_pepper,
                "kevin_total": k_total,
                "kevin_osmium": k_osmium,
                "kevin_pepper": k_pepper,
                "rust_total": r_total,
                "rust_osmium": r_osmium,
                "rust_pepper": r_pepper,
                "rust_own_trades": r_trades,
                "average": round((x_total + k_total + r_total) / 3.0, 2),
            }
        )

    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(out_csv)


if __name__ == "__main__":
    main()
