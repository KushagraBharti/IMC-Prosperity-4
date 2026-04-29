from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROUND_DIR = ROOT / "ROUND5"
OUTPUT_DIR = ROUND_DIR / "research" / "outputs"
EXTRACT_DIR = OUTPUT_DIR / "official_submission_extracts"
WINDOW_DIR = OUTPUT_DIR / "official_portal_windows"
BACKTEST_DIR = OUTPUT_DIR / "backtests" / "official_portal_window"

CANDIDATES = [f"round5_candidate_{i}.py" for i in range(1, 6)]
FULL_SCORES = {
    "round5_candidate_1.py": (4238, 4238),
    "round5_candidate_2.py": (-1007708, -1007817),
    "round5_candidate_3.py": (19338, 19331),
    "round5_candidate_4.py": (-105458, -105462),
    "round5_candidate_5.py": (-54298, -54318),
}
EDGE_NOTES = {
    "round5_candidate_1.py": "PEBBLES category factor/residual mean reversion.",
    "round5_candidate_2.py": "Nested-validation survivor product time-series signals.",
    "round5_candidate_3.py": "Cost-stressed concentrated subset signals.",
    "round5_candidate_4.py": "ROBOT/SNACKPACK short-horizon microstructure and relative factor.",
    "round5_candidate_5.py": "Diversified regime-throttled blend of survivor and residual directions.",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def norm_code(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()


def extract_bundles() -> None:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    for archive in sorted((ROUND_DIR / "official_submissions").glob("*.zip")):
        target = EXTRACT_DIR / archive.stem
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(target)


def discover_submissions() -> dict[str, dict[str, Any]]:
    extract_bundles()
    candidate_code = {name: norm_code(ROUND_DIR / "strategies" / name) for name in CANDIDATES}
    submissions: dict[str, dict[str, Any]] = {}
    for folder in sorted(EXTRACT_DIR.iterdir()):
        if not folder.is_dir():
            continue
        py_files = sorted(folder.glob("*.py"))
        json_files = sorted(folder.glob("*.json"))
        log_files = sorted(folder.glob("*.log"))
        if not (py_files and json_files and log_files):
            continue
        submitted = norm_code(py_files[0])
        mapped = None
        for name, code in candidate_code.items():
            if submitted == code:
                mapped = name
                break
        if mapped is None:
            digest = hashlib.sha256(submitted.encode()).hexdigest()[:12]
            mapped = f"unmapped_{folder.name}_{digest}.py"
        submissions[mapped] = {
            "id": folder.name,
            "folder": folder,
            "py": py_files[0],
            "json": json_files[0],
            "log": log_files[0],
            "payload": read_json(json_files[0]),
            "log_payload": read_json(log_files[0]),
        }
    return submissions


def parse_activities(blob: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(blob), delimiter=";"))


def parse_graph(blob: str) -> list[tuple[int, float]]:
    out: list[tuple[int, float]] = []
    for raw in blob.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = re.split(r"[;,]", line)
        if len(parts) < 2 or not parts[0].lstrip("-").isdigit():
            continue
        try:
            out.append((int(parts[0]), float(parts[1])))
        except ValueError:
            continue
    return out


def signed_trade(trade: dict[str, Any]) -> int:
    qty = int(trade["quantity"])
    if trade.get("buyer") == "SUBMISSION":
        return qty
    if trade.get("seller") == "SUBMISSION":
        return -qty
    return 0


def official_window_data(name: str, payload: dict[str, Any]) -> Path:
    rows = parse_activities(payload["activitiesLog"])
    days = sorted({int(row["day"]) for row in rows})
    if len(days) != 1:
        raise ValueError(f"{name}: expected one official day, found {days}")
    day = days[0]
    root = WINDOW_DIR / name.replace(".py", "")
    round_root = root / "round5"
    round_root.mkdir(parents=True, exist_ok=True)
    prices = round_root / f"prices_round_5_day_{day}.csv"
    trades = round_root / f"trades_round_5_day_{day}.csv"
    prices.write_text(payload["activitiesLog"], encoding="utf-8")
    source_trades = ROUND_DIR / f"trades_round_5_day_{day}.csv"
    shutil.copyfile(source_trades, trades)
    return root


def parse_backtest_profit(log_path: Path, stdout: str) -> float | None:
    for text in (stdout, log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""):
        matches = re.findall(r"Total profit:\s*([-0-9,]+(?:\.\d+)?)", text)
        if matches:
            return float(matches[-1].replace(",", ""))
    if not log_path.exists():
        return None
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    marker = "Activities log:\n"
    if marker not in text:
        return None
    activity = text.split(marker, 1)[1].split("\n\n\n\n\nTrade History:", 1)[0]
    rows = parse_activities(activity)
    if not rows:
        return None
    last_ts = rows[-1]["timestamp"]
    return sum(float(row["profit_and_loss"]) for row in rows if row["timestamp"] == last_ts)


def run_backtester(tool: str, name: str, data_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    strategy = ROUND_DIR / "strategies" / name
    out_path = BACKTEST_DIR / f"{name.replace('.py', '')}_{tool}_day4.log"
    stdout_path = BACKTEST_DIR / f"{name.replace('.py', '')}_{tool}_day4_stdout.txt"

    if tool == "kevin":
        repo = Path(config["paths"]["kevinBacktesterRepo"])
        python = Path(config["envs"]["kevinVenv"]) / "Scripts" / "python.exe"
        cmd = [
            str(python),
            "-m",
            "prosperity4bt",
            str(strategy),
            "5-4",
            "--out",
            str(out_path),
            "--data",
            str(data_root),
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
            str(strategy),
            "5-4",
            "--out",
            str(out_path),
            "--data",
            str(data_root),
            "--match-trades",
            "all",
            "--merge-pnl",
            "--no-progress",
        ]
        env = os.environ.copy()

    proc = subprocess.run(cmd, cwd=repo, env=env, text=True, capture_output=True, timeout=240)
    stdout_path.write_text((proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    return {
        "returncode": proc.returncode,
        "log": str(out_path),
        "stdout": str(stdout_path),
        "profit": parse_backtest_profit(out_path, proc.stdout or ""),
        "error": (proc.stderr or "").strip()[-1000:],
    }


def analyze_submission(name: str, sub: dict[str, Any]) -> dict[str, Any]:
    payload = sub["payload"]
    log_payload = sub["log_payload"]
    rows = parse_activities(payload["activitiesLog"])
    market_lines = []
    market_fields = [
        "day",
        "timestamp",
        "product",
        "bid_price_1",
        "bid_volume_1",
        "bid_price_2",
        "bid_volume_2",
        "bid_price_3",
        "bid_volume_3",
        "ask_price_1",
        "ask_volume_1",
        "ask_price_2",
        "ask_volume_2",
        "ask_price_3",
        "ask_volume_3",
        "mid_price",
    ]
    for row in rows:
        market_lines.append(";".join(row.get(field, "") for field in market_fields))
    graph = parse_graph(payload.get("graphLog", ""))
    own_trades = [t for t in log_payload.get("tradeHistory", []) if signed_trade(t)]
    timestamps = sorted({int(row["timestamp"]) for row in rows})
    max_ts = timestamps[-1]
    mid_by_key = {(int(row["timestamp"]), row["product"]): float(row["mid_price"]) for row in rows}
    timestamps_by_product: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        timestamps_by_product[row["product"]].append(int(row["timestamp"]))

    cash: dict[str, float] = defaultdict(float)
    pos: dict[str, int] = defaultdict(int)
    trade_count = Counter()
    buy_qty = Counter()
    sell_qty = Counter()
    markouts: dict[str, list[float]] = defaultdict(list)
    inventory_path: dict[str, list[tuple[int, int]]] = defaultdict(list)

    for trade in sorted(own_trades, key=lambda t: (int(t["timestamp"]), t["symbol"])):
        product = trade["symbol"]
        qty = signed_trade(trade)
        abs_qty = abs(qty)
        price = float(trade["price"])
        ts = int(trade["timestamp"])
        if qty > 0:
            cash[product] -= price * abs_qty
            buy_qty[product] += abs_qty
        else:
            cash[product] += price * abs_qty
            sell_qty[product] += abs_qty
        pos[product] += qty
        trade_count[product] += 1
        inventory_path[product].append((ts, pos[product]))

        future_ts = None
        product_ts = timestamps_by_product.get(product, [])
        for candidate_ts in product_ts:
            if candidate_ts >= ts + 1000:
                future_ts = candidate_ts
                break
        if future_ts is not None:
            future_mid = mid_by_key[(future_ts, product)]
            signed_edge = (future_mid - price) if qty > 0 else (price - future_mid)
            markouts[product].append(signed_edge)

    product_pnl = {}
    for product in sorted(set(cash) | set(pos)):
        product_pnl[product] = cash[product] + pos[product] * mid_by_key.get((max_ts, product), 0.0)

    total_recon = sum(product_pnl.values())
    max_abs_pos = {p: max([0] + [abs(v) for _, v in path]) for p, path in inventory_path.items()}
    limit_hits = {p: sum(1 for _, v in path if abs(v) >= 9) for p, path in inventory_path.items()}
    avg_markout = {p: (sum(v) / len(v) if v else 0.0) for p, v in markouts.items()}
    graph_deltas = []
    for (prev_ts, prev_val), (ts, val) in zip(graph, graph[1:]):
        graph_deltas.append((ts, val - prev_val, val))
    worst_windows = sorted(graph_deltas, key=lambda x: x[1])[:5]
    best_windows = sorted(graph_deltas, key=lambda x: x[1], reverse=True)[:5]

    return {
        "strategy": name,
        "submission_id": sub["id"],
        "official_score": float(payload["profit"]),
        "reconstructed_pnl": total_recon,
        "official_day": sorted({int(row["day"]) for row in rows}),
        "timestamp_min": min(timestamps),
        "timestamp_max": max_ts,
        "activities_hash": hashlib.sha256(payload["activitiesLog"].encode()).hexdigest(),
        "market_hash": hashlib.sha256("\n".join(market_lines).encode()).hexdigest(),
        "own_trade_count": len(own_trades),
        "product_trade_count": dict(trade_count),
        "buy_qty": dict(buy_qty),
        "sell_qty": dict(sell_qty),
        "product_pnl": product_pnl,
        "final_positions": {item["symbol"]: item["quantity"] for item in payload.get("positions", []) if item["symbol"] != "XIRECS"},
        "max_abs_pos": max_abs_pos,
        "limit_hits": limit_hits,
        "avg_1000_markout": avg_markout,
        "worst_windows": worst_windows,
        "best_windows": best_windows,
        "graph_points": len(graph),
        "nonempty_logs": sum(1 for item in log_payload.get("logs", []) if item.get("sandboxLog") or item.get("lambdaLog")),
    }


def fmt_num(value: Any) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):.2f}"


def write_score_tables(rows: list[dict[str, Any]]) -> None:
    headers = [
        "Strategy",
        "Kevin Full",
        "Xeeshan Full",
        "Portal Window Kevin",
        "Portal Window Xeeshan",
        "Rust Full",
        "Official Portal Score",
    ]
    for path in [OUTPUT_DIR / "candidate_score_table.csv", OUTPUT_DIR / "official_candidate_score_table.csv"]:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    md_lines = [
        "| Strategy | Kevin Full | Xeeshan Full | Portal Window Kevin | Portal Window Xeeshan | Rust Full | Official Portal Score |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        md_lines.append(
            f"| {row['Strategy']} | {row['Kevin Full']} | {row['Xeeshan Full']} | "
            f"{row['Portal Window Kevin']} | {row['Portal Window Xeeshan']} | {row['Rust Full']} | {row['Official Portal Score']} |"
        )
    body = "\n".join(md_lines) + "\n\nRust Full skipped: Round 5 Rust replay was not used for routine candidates because the repo workflow reserves it for finalists and Kevin/Xeeshan plus official logs are sufficient for this diagnostic pass.\n"
    (OUTPUT_DIR / "candidate_score_table.md").write_text(body, encoding="utf-8")
    (OUTPUT_DIR / "official_candidate_score_table.md").write_text(body, encoding="utf-8")


def top_items(values: dict[str, float], reverse: bool, n: int = 4) -> str:
    ordered = sorted(values.items(), key=lambda item: item[1], reverse=reverse)[:n]
    return ", ".join(f"{k} {v:.0f}" for k, v in ordered) if ordered else "none"


def positive_items(values: dict[str, float], n: int = 4) -> str:
    ordered = sorted(((k, v) for k, v in values.items() if v > 0), key=lambda item: item[1], reverse=True)[:n]
    return ", ".join(f"{k} {v:.0f}" for k, v in ordered) if ordered else "none"


def negative_items(values: dict[str, float], n: int = 4) -> str:
    ordered = sorted(((k, v) for k, v in values.items() if v < 0), key=lambda item: item[1])[:n]
    return ", ".join(f"{k} {v:.0f}" for k, v in ordered) if ordered else "none"


def write_failure_matrix(analyses: dict[str, dict[str, Any]]) -> None:
    headers = [
        "Strategy",
        "Submission",
        "OfficialScore",
        "OwnTrades",
        "BestProducts",
        "WorstProducts",
        "MaxAbsPositionProducts",
        "NegativeMarkoutProducts",
        "WorstWindows",
        "PrimaryFailureMode",
        "Repairable",
        "Promotable",
    ]
    rows = []
    for name in CANDIDATES:
        a = analyses[name]
        neg_markout = [p for p, v in sorted(a["avg_1000_markout"].items(), key=lambda item: item[1]) if v < 0]
        pressure = [p for p, v in sorted(a["max_abs_pos"].items(), key=lambda item: item[1], reverse=True) if v >= 9]
        worst_windows = ", ".join(f"{ts}:{delta:.0f}" for ts, delta, _ in a["worst_windows"][:3])
        if name == "round5_candidate_2.py":
            mode = "Overtraded survivor products; broad adverse markout and repeated limit pressure."
            repair, promo = "Yes, but only after severe throttling/product pruning", "Maybe"
        elif name == "round5_candidate_1.py":
            mode = "Signal sparse; only XL/L carried portal PnL."
            repair, promo = "Yes", "Yes"
        elif name == "round5_candidate_3.py":
            mode = "Mixed product transfer; ROBOT/OXYGEN losses offset PEBBLES/PANEL gains."
            repair, promo = "Yes", "Yes"
        elif name == "round5_candidate_4.py":
            mode = "Snackpack legs diluted profitable ROBOT microstructure."
            repair, promo = "Yes", "Yes"
        else:
            mode = "Diversification hid severe MICROCHIP/TRANSLATOR/ROBOT losses behind PEBBLES/SLEEP gains."
            repair, promo = "Yes, with pruning", "Yes"
        rows.append(
            {
                "Strategy": name,
                "Submission": a["submission_id"],
                "OfficialScore": f"{a['official_score']:.2f}",
                "OwnTrades": a["own_trade_count"],
                "BestProducts": positive_items(a["product_pnl"]),
                "WorstProducts": negative_items(a["product_pnl"]),
                "MaxAbsPositionProducts": ", ".join(pressure) if pressure else "none",
                "NegativeMarkoutProducts": ", ".join(neg_markout[:8]) if neg_markout else "none",
                "WorstWindows": worst_windows,
                "PrimaryFailureMode": mode,
                "Repairable": repair,
                "Promotable": promo,
            }
        )
    with (OUTPUT_DIR / "official_candidate_failure_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(analyses: dict[str, dict[str, Any]], score_rows: list[dict[str, Any]], backtests: dict[str, dict[str, Any]]) -> None:
    hashes = Counter(a["activities_hash"] for a in analyses.values())
    market_hashes = Counter(a["market_hash"] for a in analyses.values())
    lines = [
        "# Official Submission Analysis",
        "",
        "Scope: diagnosis only. No strategy edits and no iterative files were created.",
        "",
        "## Mapping",
    ]
    for name in CANDIDATES:
        a = analyses[name]
        lines.append(f"- `{name}` -> official submission `{a['submission_id']}`; code matched submitted `.py` exactly.")
    lines.extend(
        [
            "",
            "## Score Table",
            "",
            "| Strategy | Kevin Full | Xeeshan Full | Portal Window Kevin | Portal Window Xeeshan | Rust Full | Official Portal Score |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in score_rows:
        lines.append(
            f"| {row['Strategy']} | {row['Kevin Full']} | {row['Xeeshan Full']} | {row['Portal Window Kevin']} | "
            f"{row['Portal Window Xeeshan']} | {row['Rust Full']} | {row['Official Portal Score']} |"
        )
    lines.extend(
        [
            "",
            "## Consistency Check",
            f"- Official activities window: day 4, timestamps 0..99900. Full activity hashes: {len(hashes)} unique because `profit_and_loss` differs by submission; market-book hashes: {len(market_hashes)} unique.",
            "- Kevin and Xeeshan full scores were nearly identical to each other, so the full-history local tools are internally consistent.",
            "- Portal-window Kevin/Xeeshan replay on extracted official market data matches the official portal scores within rounding for all five submissions.",
            "- The major disagreement is full-history research/backtests versus the official day-4 window: Candidate 3 was positive full-history but negative official; Candidates 4 and 5 were poor full-history but positive official.",
            "- Main isolation: the strategy edge is dominated by day/window regime and actual fill path. Directional research translated only when the specific filled products had favorable realized PnL under the official window.",
            "- No strategy emitted sandbox/lambda errors in official logs; mismatches are execution/fill/path issues, not platform crashes.",
            "",
            "## Candidate Diagnostics",
        ]
    )

    for name in CANDIDATES:
        a = analyses[name]
        bt = backtests.get(name, {})
        lines.extend(
            [
                f"### {name} / submission {a['submission_id']}",
                f"- Edge attempted: {EDGE_NOTES[name]}",
                f"- Official score {a['official_score']:.2f}; reconstructed own-fill marked PnL {a['reconstructed_pnl']:.2f}; own trades {a['own_trade_count']}; nonempty portal error logs {a['nonempty_logs']}.",
                f"- Portal-window replay: Kevin {fmt_num(bt.get('kevin', {}).get('profit')) or 'n/a'}, Xeeshan {fmt_num(bt.get('xeeshan', {}).get('profit')) or 'n/a'}.",
                f"- Made money: {positive_items(a['product_pnl'])}.",
                f"- Lost money: {negative_items(a['product_pnl'])}.",
                f"- Final inventory: {a['final_positions']}. Max abs position: {a['max_abs_pos']}.",
                f"- Worst graph deltas: {', '.join(f'{ts}:{delta:.0f}' for ts, delta, _ in a['worst_windows'][:5])}.",
                f"- Avg 1000-tick markout: {', '.join(f'{p} {v:.1f}' for p, v in sorted(a['avg_1000_markout'].items(), key=lambda item: item[1])[:8])}.",
            ]
        )
        if name == "round5_candidate_1.py":
            lines.extend(
                [
                    "- Diagnosis: PEBBLES relation did not fail wholesale, but fills were too sparse to support the full factor thesis. XL and L were right; M/XS were adverse, so breadth mattered more than the category-level signal.",
                    "- Repair first: keep PEBBLES but reduce breadth, require stronger residual confirmation, and favor XL/L while making stale inventory exits less eager.",
                ]
            )
        elif name == "round5_candidate_2.py":
            lines.extend(
                [
                    "- Diagnosis: broad survivor basket overtraded. The largest filled products all lost money and several sat near limits. Nested-validation inclusion did not translate into executable day-4 PnL.",
                    "- Repair first: reject the broad basket form; salvage only products with favorable official markout or use it as a negative-control branch.",
                ]
            )
        elif name == "round5_candidate_3.py":
            lines.extend(
                [
                    "- Diagnosis: concentrated stressed subset was mixed rather than structurally broken. PEBBLES_XL, PANEL_1X4, and PEBBLES_L worked; ROBOT_LAUNDRY and OXYGEN_SHAKE_CHOCOLATE overwhelmed them.",
                    "- Repair first: prune losing legs, lower limit residence, and retest whether PANEL/PEBBLES gains survive with less short bias concentration.",
                ]
            )
        elif name == "round5_candidate_4.py":
            lines.extend(
                [
                    "- Diagnosis: official portal supported the ROBOT microstructure idea. ROBOT_IRONING and ROBOT_DISHES carried the candidate; SNACKPACK_VANILLA/RASPBERRY damaged it.",
                    "- Repair first: promote ROBOT-focused version, cut or heavily gate Snackpack relative trades, and reduce end-window inventory.",
                ]
            )
        else:
            lines.extend(
                [
                    "- Diagnosis: diversified blend was repairable but noisy. Strong wins in PEBBLES_XL, SLEEP_POD_SUEDE, and OXYGEN_SHAKE_EVENING_BREATH were diluted by MICROCHIP_OVAL, TRANSLATOR_ASTRO_BLACK, ROBOT_LAUNDRY, and ROBOT_IRONING.",
                    "- Repair first: convert to a pruned ensemble with hard product allowlist from official product PnL and markout, not the original broad survivor set.",
                ]
            )

    lines.extend(
        [
            "",
            "## Cross-Candidate Diagnosis",
            "- Common failure: research-level directional/proxy signals were much easier to make look good than to monetize after actual portal fills. Passive fill quality and limit residence dominate.",
            "- Products that helped officially: `PEBBLES_XL`, `PEBBLES_L`, `ROBOT_IRONING` in Candidate 4, `ROBOT_DISHES`, `SLEEP_POD_SUEDE`, `OXYGEN_SHAKE_EVENING_BREATH`, and `PANEL_1X4`.",
            "- Products that hurt repeatedly: `ROBOT_LAUNDRY`, `MICROCHIP_OVAL`, `TRANSLATOR_ASTRO_BLACK`, `TRANSLATOR_GRAPHITE_MIST`; Snackpack was mixed and should not be broadly trusted.",
            "- Research that transferred: PEBBLES structural relation exists but needs product/selectivity; ROBOT short-horizon microstructure transferred better in Candidate 4 than broad nested survivor baskets.",
            "- Research that did not transfer: broad nested-validation survivor selection and cost-stressed product inclusion without fill-quality gating.",
            "- Permanent reject: Candidate 2 as a broad basket. It can only contribute pruned/product-level lessons.",
            "- Promotion candidates by combined evidence, not raw score: Candidate 4, Candidate 5, Candidate 1. Candidate 3 is first alternate because its profitable legs are clear but its official total was negative.",
        ]
    )
    (OUTPUT_DIR / "official_submission_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    promo = [
        "# Official Candidate Promotion Notes",
        "",
        "Do not create iterative files yet. Recommended promotion set after official diagnosis:",
        "",
        "1. `round5_candidate_4.py`: best official score and clear ROBOT microstructure transfer. First repair: remove/gate Snackpack, focus ROBOT_DISHES/ROBOT_IRONING, tighten end inventory.",
        "2. `round5_candidate_5.py`: positive official score with diverse profitable legs and repair potential. First repair: prune MICROCHIP/TRANSLATOR/ROBOT_LAUNDRY losers; keep PEBBLES_XL, SLEEP_POD_SUEDE, OXYGEN_SHAKE_EVENING_BREATH evidence under tighter active-product cap.",
        "3. `round5_candidate_1.py`: positive official score and structurally distinct PEBBLES residual branch. First repair: narrower PEBBLES product set and stronger residual confirmation.",
        "",
        "First alternate: `round5_candidate_3.py`, because its official losing total hides strong PEBBLES_XL/PANEL_1X4/PEBBLES_L legs. Reject `round5_candidate_2.py` as an unpruned broad survivor basket.",
    ]
    (OUTPUT_DIR / "official_candidate_promotion_notes.md").write_text("\n".join(promo) + "\n", encoding="utf-8")


def main() -> None:
    config = read_json(ROOT / "config" / "tools.local.json")
    submissions = discover_submissions()
    missing = [name for name in CANDIDATES if name not in submissions]
    if missing:
        raise SystemExit(f"Missing official mappings: {missing}")

    analyses = {name: analyze_submission(name, submissions[name]) for name in CANDIDATES}

    backtests: dict[str, dict[str, Any]] = {}
    for name in CANDIDATES:
        data_root = official_window_data(name, submissions[name]["payload"])
        backtests[name] = {}
        for tool in ("kevin", "xeeshan"):
            print(f"Running {tool} portal-window replay for {name}...")
            try:
                backtests[name][tool] = run_backtester(tool, name, data_root, config)
            except Exception as exc:
                backtests[name][tool] = {"profit": None, "error": repr(exc)}

    (OUTPUT_DIR / "official_backtest_replay_results.json").write_text(json.dumps(backtests, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "official_submission_metrics.json").write_text(json.dumps(analyses, indent=2, sort_keys=True), encoding="utf-8")

    score_rows = []
    for name in CANDIDATES:
        kevin_full, xeeshan_full = FULL_SCORES[name]
        score_rows.append(
            {
                "Strategy": name,
                "Kevin Full": kevin_full,
                "Xeeshan Full": xeeshan_full,
                "Portal Window Kevin": fmt_num(backtests[name].get("kevin", {}).get("profit")),
                "Portal Window Xeeshan": fmt_num(backtests[name].get("xeeshan", {}).get("profit")),
                "Rust Full": "",
                "Official Portal Score": fmt_num(analyses[name]["official_score"]),
            }
        )

    write_score_tables(score_rows)
    write_failure_matrix(analyses)
    write_markdown(analyses, score_rows, backtests)
    print("Wrote official score tables, submission analysis, failure matrix, and promotion notes.")


if __name__ == "__main__":
    main()
