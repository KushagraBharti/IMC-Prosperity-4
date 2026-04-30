from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
OUTPUT_DIR = ROUND_DIR / "research" / "outputs"
BACKTEST_DIR = OUTPUT_DIR / "backtests" / "candidate_26_30"
STRATEGIES = [f"round5_candidate_{i}.py" for i in range(26, 31)]
ROLES = {
    "round5_candidate_26.py": "clean validated add-ons",
    "round5_candidate_27.py": "MICROCHIP specialist/info",
    "round5_candidate_28.py": "robust multi-engine",
    "round5_candidate_29.py": "portal-upside broad integration",
    "round5_candidate_30.py": "balanced competition portfolio",
}


def parse_profit(log_path: Path, stdout: str) -> float | None:
    for text in (stdout, log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    if log_path.exists():
        try:
            data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
            activities = data.get("activitiesLog", "")
            if activities:
                rows = list(csv.DictReader(io.StringIO(activities), delimiter=";"))
                if rows:
                    latest = rows[-50:]
                    return sum(float(row.get("profit_and_loss") or 0.0) for row in latest)
        except Exception:
            pass
    return None


def category(product: str) -> str:
    if product.startswith("PEBBLES_"):
        return "PEBBLES"
    if product.startswith("MICROCHIP_"):
        return "MICROCHIP"
    if product.startswith("SLEEP_POD_"):
        return "SLEEP_POD"
    if product.startswith("OXYGEN_SHAKE_"):
        return "OXYGEN_SHAKE"
    if product.startswith("GALAXY_SOUNDS_"):
        return "GALAXY_SOUNDS"
    if product.startswith("UV_VISOR_"):
        return "UV_VISOR"
    if product.startswith("ROBOT_"):
        return "ROBOT"
    if product.startswith("PANEL_"):
        return "PANEL"
    if product.startswith("TRANSLATOR_"):
        return "TRANSLATOR"
    if product.startswith("SNACKPACK_"):
        return "SNACKPACK"
    return product.split("_", 1)[0]


def final_product_pnl(log_path: Path) -> dict[str, float]:
    data = json.loads(log_path.read_text(encoding="utf-8", errors="ignore"))
    activities = data.get("activitiesLog", "")
    rows = list(csv.DictReader(io.StringIO(activities), delimiter=";"))
    latest: dict[str, float] = {}
    for row in rows:
        product = row.get("product")
        if product:
            latest[product] = float(row.get("profit_and_loss") or 0.0)
    return latest


def run_tool(tool: str, strategy_name: str, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    strategy_path = ROUND_DIR / "strategies" / strategy_name
    out_path = BACKTEST_DIR / f"{strategy_name.replace('.py', '')}_{tool}_portal_day4.log"
    stdout_path = BACKTEST_DIR / f"{strategy_name.replace('.py', '')}_{tool}_portal_day4_stdout.txt"
    portal_root = OUTPUT_DIR / "official_portal_windows" / "round5_candidate_1"
    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy_path),
            "5-4",
            "--out",
            str(out_path),
            "--data",
            str(portal_root),
            "--match-trades",
            "worse",
            "--no-vis",
            "--no-progress",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo)
    else:
        repo = Path(config["paths"]["xeeshanBacktesterRepo"])
        python = Path(config["envs"]["xeeshanVenv"]) / "Scripts" / "python.exe"
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy_path),
            "5-4",
            "--out",
            str(out_path),
            "--data",
            str(portal_root),
            "--match-trades",
            "all",
            "--merge-pnl",
            "--no-progress",
        ]
        env = os.environ.copy()
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=360)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {
        "returncode": proc.returncode,
        "profit": parse_profit(out_path, proc.stdout or ""),
        "log": str(out_path),
        "stdout": str(stdout_path),
        "stderr_tail": (proc.stderr or "")[-1500:],
    }


def fmt(value: Any) -> str:
    return "" if value is None else f"{float(value):.2f}"


def write_score_table(rows: list[dict[str, str]]) -> None:
    headers = ["Strategy", "Portal Window Kevin", "Portal Window Xeeshan", "Role", "Official Portal Score"]
    with (OUTPUT_DIR / "candidate_26_30_score_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    lines = ["| Strategy | Portal Window Kevin | Portal Window Xeeshan | Role | Official Portal Score |", "|---|---:|---:|---|---:|"]
    for row in rows:
        lines.append(f"| {row['Strategy']} | {row['Portal Window Kevin']} | {row['Portal Window Xeeshan']} | {row['Role']} | {row['Official Portal Score']} |")
    lines.append("")
    lines.append("Full backtests and Rust were intentionally skipped for this phase.")
    (OUTPUT_DIR / "candidate_26_30_score_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_attribution(raw: dict[str, dict[str, Any]]) -> None:
    product_rows: list[dict[str, Any]] = []
    category_rows: list[dict[str, Any]] = []
    lines = ["# Candidate 26-30 Portal Attribution", ""]
    for strategy, runs in raw.items():
        kevin_log = Path(runs["kevin_portal"]["log"])
        pnls = final_product_pnl(kevin_log)
        cats: dict[str, float] = {}
        for product, pnl in pnls.items():
            product_rows.append({"strategy": strategy, "product": product, "category": category(product), "portal_pnl": pnl})
            cats[category(product)] = cats.get(category(product), 0.0) + pnl
        for cat, pnl in sorted(cats.items()):
            category_rows.append({"strategy": strategy, "category": cat, "portal_pnl": pnl})

        traded = {p: v for p, v in pnls.items() if abs(v) > 0.01}
        positives = sorted(((p, v) for p, v in traded.items() if v > 0), key=lambda x: x[1], reverse=True)[:12]
        negatives = sorted(((p, v) for p, v in traded.items() if v < 0), key=lambda x: x[1])[:8]
        pebbles = sum(v for p, v in pnls.items() if category(p) == "PEBBLES")
        non_pebbles = sum(v for p, v in pnls.items() if category(p) != "PEBBLES")
        lines.extend(
            [
                f"## {strategy}",
                f"- Total Kevin portal: {fmt(runs['kevin_portal']['profit'])}; Xeeshan portal: {fmt(runs['xeeshan_portal']['profit'])}.",
                f"- PEBBLES PnL: {pebbles:.2f}; non-PEBBLES PnL: {non_pebbles:.2f}.",
                "- Top positive products: " + "; ".join(f"`{p}` {v:.0f}" for p, v in positives),
                "- Top negative products: " + ("; ".join(f"`{p}` {v:.0f}" for p, v in negatives) if negatives else "none material"),
                "",
            ]
        )

    with (OUTPUT_DIR / "candidate_26_30_product_pnl.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["strategy", "product", "category", "portal_pnl"])
        writer.writeheader()
        writer.writerows(product_rows)
    with (OUTPUT_DIR / "candidate_26_30_category_pnl.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["strategy", "category", "portal_pnl"])
        writer.writeheader()
        writer.writerows(category_rows)
    (OUTPUT_DIR / "candidate_26_30_portal_attribution.md").write_text("\n".join(lines), encoding="utf-8")


def write_recommendation(rows: list[dict[str, str]], raw: dict[str, dict[str, Any]]) -> None:
    ordered = sorted(rows, key=lambda r: float(r["Portal Window Kevin"]), reverse=True)
    best = ordered[0]
    lines = [
        "# Candidate 26-30 Recommendation",
        "",
        f"- Best local portal replay: `{best['Strategy']}` at Kevin `{best['Portal Window Kevin']}` / Xeeshan `{best['Portal Window Xeeshan']}`.",
        "- Candidate 24 benchmark was about `41.8k` portal; candidate 25 was about `38.9k` portal.",
        "- Submit order should prioritize candidates that beat or materially diversify from candidate 24/25.",
        "",
        "## Submit Priority",
    ]
    for i, row in enumerate(ordered, start=1):
        status = "beats candidate 24 benchmark" if float(row["Portal Window Kevin"]) > 41800 else "below candidate 24 benchmark"
        lines.append(f"{i}. `{row['Strategy']}`: {row['Role']}, Kevin `{row['Portal Window Kevin']}`, {status}.")
    lines.extend(
        [
            "",
            "## Notes",
            "- Scores are portal-window only by instruction; full robustness remains unknown for 26-30.",
            "- Use product attribution before official submission if a broad candidate wins only by one fragile category.",
        ]
    )
    (OUTPUT_DIR / "candidate_26_30_recommendation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    config = json.loads((ROOT / "config" / "tools.local.json").read_text(encoding="utf-8"))
    raw: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, str]] = []
    for strategy in STRATEGIES:
        print(f"Portal replay {strategy}...")
        raw[strategy] = {
            "kevin_portal": run_tool("kevin", strategy, config),
            "xeeshan_portal": run_tool("xeeshan", strategy, config),
        }
        rows.append(
            {
                "Strategy": strategy,
                "Portal Window Kevin": fmt(raw[strategy]["kevin_portal"]["profit"]),
                "Portal Window Xeeshan": fmt(raw[strategy]["xeeshan_portal"]["profit"]),
                "Role": ROLES[strategy],
                "Official Portal Score": "pending",
            }
        )
    (OUTPUT_DIR / "candidate_26_30_raw_backtests.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    write_score_table(rows)
    write_attribution(raw)
    write_recommendation(rows, raw)


if __name__ == "__main__":
    main()
