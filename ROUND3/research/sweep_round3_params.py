from __future__ import annotations

import argparse
import csv
import itertools
import re
import subprocess
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Temporary Round 3 parameter sweep")
    parser.add_argument("--base", default="ROUND3/strategies/round3_iterative_2.py")
    parser.add_argument("--out-root", default="outputs/experiments")
    parser.add_argument(
        "--mode",
        choices=[
            "vfe",
            "vfe_passive",
            "options",
            "option_deep",
            "option_sigma",
            "option_spot",
            "option_pair",
            "option_size_matrix",
            "option_size_fine",
            "option_size_ultra",
        ],
        default="vfe",
    )
    parser.add_argument("--limit", type=int, default=0, help="Optional max variants")
    return parser.parse_args()


def replace_assignment(text: str, name: str, value: str) -> str:
    pattern = rf"^(\s*{re.escape(name)}\s*=\s*).*$"
    updated, count = re.subn(pattern, rf"\g<1>{value}", text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Could not replace assignment {name}")
    return updated


def replace_first_existing_assignment(text: str, names: list[str], value: str) -> str:
    last_error: Exception | None = None
    for name in names:
        try:
            return replace_assignment(text, name, value)
        except ValueError as exc:
            last_error = exc
    raise ValueError(f"Could not replace any assignment from {names}") from last_error


def replace_active_vouchers(text: str, vouchers: list[str]) -> str:
    value = "[" + ", ".join(repr(v) for v in vouchers) + "]"
    return replace_assignment(text, "ACTIVE_VOUCHERS", value)


def replace_option_edge(text: str, strike: int, value: float) -> str:
    block_match = re.search(r"OPTION_EDGE\s*=\s*\{(?P<body>.*?)^\s*\}", text, flags=re.MULTILINE | re.DOTALL)
    if not block_match:
        raise ValueError("Could not find OPTION_EDGE block")
    body = block_match.group("body")
    pattern = rf"^(\s*{strike}\s*:\s*)[-0-9.]+(,\s*)$"
    updated_body, count = re.subn(pattern, rf"\g<1>{value:.2f}\2", body, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Could not replace OPTION_EDGE for {strike}")
    return text[: block_match.start("body")] + updated_body + text[block_match.end("body") :]


def replace_sigma(text: str, strike: int, value: float) -> str:
    for block_name in ["SIGMA", "STRIKE_VOL"]:
        block_match = re.search(rf"{block_name}\s*=\s*\{{(?P<body>.*?)^\s*\}}", text, flags=re.MULTILINE | re.DOTALL)
        if not block_match:
            continue
        body = block_match.group("body")
        pattern = rf"^(\s*{strike}\s*:\s*)[-0-9.]+(,\s*)$"
        updated_body, count = re.subn(pattern, rf"\g<1>{value:.5g}\2", body, count=1, flags=re.MULTILINE)
        if count == 1:
            return text[: block_match.start("body")] + updated_body + text[block_match.end("body") :]
    raise ValueError(f"Could not replace sigma for {strike}")


def vfe_variants() -> list[dict[str, object]]:
    edges = [4.25, 4.5, 4.75, 5.0, 5.25, 5.5, 5.75, 6.0]
    skews = [0.0, 0.001, 0.0025, 0.005]
    sizes = [40, 50, 60, 70, 80, 90, 110]
    rows = []
    for edge, skew, size in itertools.product(edges, skews, sizes):
        rows.append({"edge": edge, "skew": skew, "size": size, "passive": 24})
    return rows


def option_variants() -> list[dict[str, object]]:
    # Keep the discovered VFE settings fixed and probe voucher structure only.
    rows: list[dict[str, object]] = []
    voucher_sets = [
        ["VEV_5000", "VEV_5100", "VEV_5200", "VEV_5300"],
        ["VEV_5000", "VEV_5100", "VEV_5200"],
        ["VEV_5000", "VEV_5100", "VEV_5300"],
        ["VEV_5000", "VEV_5100"],
    ]
    edge_5200 = [0.50, 0.75, 1.00, 1.50]
    edge_5300 = [1.00, 1.25, 1.50, 2.00]
    for vouchers in voucher_sets:
        for e5200 in edge_5200:
            for e5300 in edge_5300:
                rows.append({"vouchers": vouchers, "edge_5200": e5200, "edge_5300": e5300})
    return rows


def vfe_passive_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for edge, skew, size, passive in itertools.product(
        [4.75, 5.0, 5.25],
        [0.001, 0.0025, 0.005],
        [60, 70, 90],
        [0, 12, 24, 36, 48, 72],
    ):
        rows.append({"edge": edge, "skew": skew, "size": size, "passive": passive})
    return rows


def option_deep_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    voucher_sets = [
        ["VEV_5000"],
        ["VEV_5100"],
        ["VEV_5000", "VEV_5100"],
        ["VEV_5000", "VEV_5100", "VEV_5200"],
        ["VEV_5000", "VEV_5100", "VEV_5300"],
        ["VEV_5000", "VEV_5100", "VEV_5400"],
        ["VEV_5000", "VEV_5100", "VEV_5500"],
    ]
    for vouchers, edge, size, inv_skew in itertools.product(
        voucher_sets,
        [0.25, 0.50, 0.75, 1.00],
        [25, 50, 75, 100],
        [0.0, 0.001],
    ):
        rows.append({"vouchers": vouchers, "edge": edge, "size": size, "inv_skew": inv_skew})
    return rows


def option_sigma_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    sigma_grid = [0.2425, 0.245, 0.2475, 0.25, 0.2525, 0.255, 0.2575]
    for sigma_5000, sigma_5100, edge, size in itertools.product(
        sigma_grid,
        sigma_grid,
        [0.90, 1.00, 1.10],
        [25, 50],
    ):
        rows.append(
            {
                "sigma_5000": sigma_5000,
                "sigma_5100": sigma_5100,
                "edge": edge,
                "size": size,
            }
        )
    return rows


def option_spot_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spot_fair_weight, edge, size in itertools.product(
        [-0.25, 0.0, 0.25, 0.50, 0.75, 1.0, 1.25, 1.50],
        [0.90, 1.00, 1.10, 1.20, 1.30],
        [20, 25, 35, 50],
    ):
        rows.append({"spot_fair_weight": spot_fair_weight, "edge": edge, "size": size})
    return rows


def option_pair_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for edge_5000, edge_5100, size in itertools.product(
        [1.05, 1.15, 1.25, 1.30, 1.35, 1.45, 1.60],
        [1.05, 1.15, 1.25, 1.30, 1.35, 1.45, 1.60],
        [15, 20, 25, 35],
    ):
        rows.append({"edge_5000": edge_5000, "edge_5100": edge_5100, "size": size})
    return rows


def option_size_matrix_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for size_5000, size_5100, size_5300, edge_5300 in itertools.product(
        [10, 15, 25, 35],
        [10, 15, 25, 35],
        [0, 5, 15],
        [1.25, 2.00, 3.00],
    ):
        rows.append(
            {
                "size_5000": size_5000,
                "size_5100": size_5100,
                "size_5300": size_5300,
                "edge_5300": edge_5300,
            }
        )
    return rows


def option_size_fine_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for size_5000, size_5100, size_5300 in itertools.product(
        [5, 8, 10, 12],
        [12, 15, 18, 20],
        [3, 5, 7, 10],
    ):
        rows.append(
            {
                "size_5000": size_5000,
                "size_5100": size_5100,
                "size_5300": size_5300,
                "edge_5300": 1.25,
            }
        )
    return rows


def option_size_ultra_variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for size_5000, size_5100, size_5300 in itertools.product(
        [6, 7, 8, 9],
        [10, 11, 12, 13, 14],
        [1, 2, 3, 4],
    ):
        rows.append(
            {
                "size_5000": size_5000,
                "size_5100": size_5100,
                "size_5300": size_5300,
                "edge_5300": 1.25,
            }
        )
    return rows


def replace_option_size_by_strike(text: str, strike: int, value: int) -> str:
    block_match = re.search(r"OPTION_SIZE_BY_STRIKE\s*=\s*\{(?P<body>.*?)^\s*\}", text, flags=re.MULTILINE | re.DOTALL)
    if not block_match:
        raise ValueError("Could not find OPTION_SIZE_BY_STRIKE block")
    body = block_match.group("body")
    pattern = rf"^(\s*{strike}\s*:\s*)[-0-9]+(,\s*)$"
    updated_body, count = re.subn(pattern, rf"\g<1>{value}\2", body, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Could not replace OPTION_SIZE_BY_STRIKE for {strike}")
    return text[: block_match.start("body")] + updated_body + text[block_match.end("body") :]


def replace_option_spot_source(text: str, fair_weight: float) -> str:
    old = """        s = self.vfe_fair(state)
        if s is None:
            od = state.order_depths.get(VFE)
            s = mid_price(od) if od is not None else None
        if s is None:
            return
"""
    new = f"""        fair_s = self.vfe_fair(state)
        od_vfe = state.order_depths.get(VFE)
        market_s = mid_price(od_vfe) if od_vfe is not None else None
        if fair_s is None:
            s = market_s
        elif market_s is None:
            s = fair_s
        else:
            s = {fair_weight:.6g} * fair_s + (1.0 - {fair_weight:.6g}) * market_s
        if s is None:
            return
"""
    if old not in text:
        raise ValueError("Could not find option spot source block")
    return text.replace(old, new, 1)


def build_variant(base_text: str, mode: str, params: dict[str, object]) -> str:
    text = base_text
    if mode in {"vfe", "vfe_passive"}:
        text = replace_first_existing_assignment(text, ["VFE_TAKE_EDGE", "VELVET_REL_TAKE_EDGE"], str(params["edge"]))
        text = replace_first_existing_assignment(text, ["VFE_SKEW", "VELVET_REL_SKEW"], str(params["skew"]))
        text = replace_first_existing_assignment(text, ["VFE_TAKE_SIZE", "VELVET_REL_TAKE_SIZE"], str(params["size"]))
        text = replace_first_existing_assignment(text, ["VFE_PASSIVE_SIZE", "VELVET_REL_PASSIVE_SIZE"], str(params["passive"]))
    elif mode == "options":
        text = replace_active_vouchers(text, params["vouchers"])  # type: ignore[arg-type]
        text = replace_option_edge(text, 5200, float(params["edge_5200"]))
        text = replace_option_edge(text, 5300, float(params["edge_5300"]))
    elif mode == "option_deep":
        text = replace_active_vouchers(text, params["vouchers"])  # type: ignore[arg-type]
        text = replace_option_edge(text, 5000, float(params["edge"]))
        text = replace_option_edge(text, 5100, float(params["edge"]))
        text = replace_first_existing_assignment(text, ["OPTION_SIZE"], str(params["size"]))
        text = replace_first_existing_assignment(text, ["OPTION_INV_SKEW"], str(params["inv_skew"]))
    elif mode == "option_sigma":
        text = replace_sigma(text, 5000, float(params["sigma_5000"]))
        text = replace_sigma(text, 5100, float(params["sigma_5100"]))
        text = replace_option_edge(text, 5000, float(params["edge"]))
        text = replace_option_edge(text, 5100, float(params["edge"]))
        text = replace_first_existing_assignment(text, ["OPTION_SIZE"], str(params["size"]))
    elif mode == "option_spot":
        text = replace_option_spot_source(text, float(params["spot_fair_weight"]))
        text = replace_option_edge(text, 5000, float(params["edge"]))
        text = replace_option_edge(text, 5100, float(params["edge"]))
        text = replace_first_existing_assignment(text, ["OPTION_SIZE"], str(params["size"]))
    elif mode == "option_pair":
        text = replace_option_edge(text, 5000, float(params["edge_5000"]))
        text = replace_option_edge(text, 5100, float(params["edge_5100"]))
        text = replace_first_existing_assignment(text, ["OPTION_SIZE"], str(params["size"]))
    elif mode in {"option_size_matrix", "option_size_fine", "option_size_ultra"}:
        text = replace_option_size_by_strike(text, 5000, int(params["size_5000"]))
        text = replace_option_size_by_strike(text, 5100, int(params["size_5100"]))
        text = replace_option_size_by_strike(text, 5300, int(params["size_5300"]))
        text = replace_option_edge(text, 5300, float(params["edge_5300"]))
    return text


def run_portal(strategy_path: Path, label: str, project_root: Path) -> dict[str, object]:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(project_root / "scripts" / "bt-portal-window.ps1"),
        "-Strategy",
        str(strategy_path),
        "-Tool",
        "both",
        "-Label",
        label,
    ]
    completed = subprocess.run(cmd, cwd=project_root, text=True, capture_output=True)
    row: dict[str, object] = {
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "kevin": "",
        "xeeshan": "",
        "batch_dir": "",
    }
    if completed.returncode != 0:
        return row
    for line in completed.stdout.splitlines():
        if "Saved portal-window batch to " in line:
            row["batch_dir"] = line.split("Saved portal-window batch to ", 1)[1].strip()
    batch_dir = Path(str(row["batch_dir"]))
    summary = batch_dir / "summary.csv"
    if summary.exists():
        with summary.open(newline="", encoding="utf-8") as f:
            for record in csv.DictReader(f):
                tool = record.get("Tool", "").lower()
                if tool in {"kevin", "xeeshan"}:
                    row[tool] = record.get("PortalWindowTotal", "")
    return row


def main() -> None:
    args = parse_args()
    project_root = Path.cwd()
    base_path = project_root / args.base
    base_text = base_path.read_text(encoding="utf-8")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = project_root / args.out_root / f"round3_{args.mode}_sweep_{stamp}"
    strategy_dir = out_dir / "strategies"
    strategy_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "vfe":
        variants = vfe_variants()
    elif args.mode == "vfe_passive":
        variants = vfe_passive_variants()
    elif args.mode == "options":
        variants = option_variants()
    elif args.mode == "option_deep":
        variants = option_deep_variants()
    elif args.mode == "option_sigma":
        variants = option_sigma_variants()
    elif args.mode == "option_spot":
        variants = option_spot_variants()
    elif args.mode == "option_pair":
        variants = option_pair_variants()
    elif args.mode == "option_size_matrix":
        variants = option_size_matrix_variants()
    elif args.mode == "option_size_fine":
        variants = option_size_fine_variants()
    else:
        variants = option_size_ultra_variants()
    if args.limit > 0:
        variants = variants[: args.limit]

    results = []
    for idx, params in enumerate(variants, start=1):
        name = f"{args.mode}_{idx:03d}"
        strategy_path = strategy_dir / f"{name}.py"
        strategy_path.write_text(build_variant(base_text, args.mode, params), encoding="utf-8")
        label = f"round3_{args.mode}_sweep_{stamp}_{idx:03d}"
        run = run_portal(strategy_path, label, project_root)
        record = {"variant": name, **params, **run}
        results.append(record)
        print(record, flush=True)

    results_path = out_dir / "results.csv"
    keys = sorted({key for row in results for key in row})
    with results_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(results_path)


if __name__ == "__main__":
    main()
