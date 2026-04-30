from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ROUND5" / "research" / "outputs"
PROBE_DIR = ROOT / "ROUND5" / "research" / "probes" / "fill_capacity"
LOG_DIR = OUT / "backtests" / "candidate_37_44_finalists_portal_logs"
PRICE_FILE = OUT / "official_portal_windows" / "round5_candidate_1" / "round5" / "prices_round_5_day_4.csv"


def load_prices() -> dict[str, list[tuple[int, float]]]:
    prices: dict[str, list[tuple[int, float]]] = {}
    with PRICE_FILE.open("r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            product = row["product"]
            bid = float(row["bid_price_1"])
            ask = float(row["ask_price_1"])
            prices.setdefault(product, []).append((int(row["timestamp"]), (bid + ask) / 2.0))
    return prices


def future_mid(series: list[tuple[int, float]], timestamp: int, ticks: int) -> float | None:
    idx = timestamp // 100
    target = idx + ticks
    if target < 0 or target >= len(series):
        return None
    return series[target][1]


def portal_audit(strategy: str, tool: str = "kevin") -> list[dict[str, object]]:
    prices = load_prices()
    log_path = LOG_DIR / f"{strategy[:-3]}_{tool}_portal.log"
    data = json.loads(log_path.read_text(encoding="utf-8"))
    product_pnl: dict[str, float] = {}
    activities = data.get("activitiesLog", "")
    if activities:
        for row in csv.DictReader(activities.splitlines(), delimiter=";"):
            product = row.get("product")
            if product:
                product_pnl[product] = float(row.get("profit_and_loss") or 0.0)

    stats: dict[str, dict[str, object]] = {}
    for trade in data.get("tradeHistory", []) or []:
        if trade.get("buyer") != "SUBMISSION" and trade.get("seller") != "SUBMISSION":
            continue
        product = trade["symbol"]
        qty = int(trade["quantity"])
        sign = 1 if trade.get("buyer") == "SUBMISSION" else -1
        ts = int(trade["timestamp"])
        price = float(trade["price"])
        row = stats.setdefault(
            product,
            {
                "product": product,
                "fill_count": 0,
                "filled_qty": 0,
                "signed_pos": 0,
                "max_abs_pos": 0,
                "near_limit_events": 0,
                "markout_10_sum": 0.0,
                "markout_10_count": 0,
                "markout_50_sum": 0.0,
                "markout_50_count": 0,
                "adverse_50": 0,
            },
        )
        row["fill_count"] = int(row["fill_count"]) + 1
        row["filled_qty"] = int(row["filled_qty"]) + qty
        row["signed_pos"] = int(row["signed_pos"]) + sign * qty
        row["max_abs_pos"] = max(int(row["max_abs_pos"]), abs(int(row["signed_pos"])))
        if abs(int(row["signed_pos"])) >= 8:
            row["near_limit_events"] = int(row["near_limit_events"]) + 1
        series = prices.get(product, [])
        for horizon in (10, 50):
            fm = future_mid(series, ts, horizon)
            if fm is None:
                continue
            markout = sign * (fm - price)
            row[f"markout_{horizon}_sum"] = float(row[f"markout_{horizon}_sum"]) + markout * qty
            row[f"markout_{horizon}_count"] = int(row[f"markout_{horizon}_count"]) + qty
            if horizon == 50 and markout < 0:
                row["adverse_50"] = int(row["adverse_50"]) + qty

    rows = []
    for product, row in stats.items():
        filled = int(row["filled_qty"])
        pnl = product_pnl.get(product, 0.0)
        mark10_count = int(row["markout_10_count"])
        mark50_count = int(row["markout_50_count"])
        rows.append(
            {
                "strategy": strategy,
                "product": product,
                "portal_pnl": round(pnl, 2),
                "full_pnl_if_available": "",
                "fill_count": row["fill_count"],
                "filled_qty": filled,
                "avg_fill_size": round(filled / max(1, int(row["fill_count"])), 3),
                "avg_order_size_est": "",
                "max_position_utilization": row["max_abs_pos"],
                "near_limit_fill_events": row["near_limit_events"],
                "pnl_per_fill": round(pnl / max(1, int(row["fill_count"])), 3),
                "markout_10_per_unit": round(float(row["markout_10_sum"]) / max(1, mark10_count), 4),
                "markout_50_per_unit": round(float(row["markout_50_sum"]) / max(1, mark50_count), 4),
                "adverse_selection_rate_50": round(int(row["adverse_50"]) / max(1, mark50_count), 4),
                "scale_read": scale_read(pnl, filled, int(row["max_abs_pos"]), float(row["markout_50_sum"]) / max(1, mark50_count)),
            }
        )
    return sorted(rows, key=lambda r: float(r["portal_pnl"]), reverse=True)


def scale_read(pnl: float, filled: int, max_pos: int, mark50: float) -> str:
    if pnl > 2500 and max_pos < 8 and mark50 > 0:
        return "under_sized"
    if pnl > 1500 and mark50 > 0:
        return "scale_carefully"
    if pnl <= 0:
        return "remove_or_anchor_only"
    if mark50 < 0:
        return "keep_small_adverse"
    return "keep_small"


def write_audits() -> None:
    rows42 = portal_audit("round5_candidate_42.py")
    rows39 = portal_audit("round5_candidate_39.py")
    with (OUT / "candidate_42_product_fill_audit.csv").open("w", encoding="utf-8", newline="") as handle:
        headers = list(rows42[0].keys())
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows42)

    by42 = {r["product"]: r for r in rows42}
    by39 = {r["product"]: r for r in rows39}
    products = sorted(set(by42) | set(by39))
    comp = []
    for product in products:
        a = by42.get(product, {})
        b = by39.get(product, {})
        comp.append(
            {
                "product": product,
                "candidate42_portal_pnl": a.get("portal_pnl", 0),
                "candidate39_portal_pnl": b.get("portal_pnl", 0),
                "pnl_39_minus_42": round(float(b.get("portal_pnl", 0) or 0) - float(a.get("portal_pnl", 0) or 0), 2),
                "candidate42_avg_fill": a.get("avg_fill_size", ""),
                "candidate39_avg_fill": b.get("avg_fill_size", ""),
                "candidate42_max_pos": a.get("max_position_utilization", ""),
                "candidate39_max_pos": b.get("max_position_utilization", ""),
                "candidate42_markout_50": a.get("markout_50_per_unit", ""),
                "candidate39_markout_50": b.get("markout_50_per_unit", ""),
                "decision": compare_decision(a, b),
            }
        )
    with (OUT / "candidate_39_42_comparison_audit.csv").open("w", encoding="utf-8", newline="") as handle:
        headers = list(comp[0].keys())
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(comp)


def compare_decision(a: dict[str, object], b: dict[str, object]) -> str:
    p42 = float(a.get("portal_pnl", 0) or 0)
    p39 = float(b.get("portal_pnl", 0) or 0)
    m42 = float(a.get("markout_50_per_unit", 0) or 0)
    if p39 - p42 > 800:
        return "transplant_candidate39_aggression"
    if p42 > 2500 and m42 > 0:
        return "scale_candidate42"
    if p42 <= 0:
        return "remove_or_signal_only"
    return "hold"


def replace_signal_config(text: str, config_literal: str) -> str:
    return re.sub(r"SIGNAL_CONFIG = \{.*?\n    MAX_SIGNAL_PRODUCTS", f"SIGNAL_CONFIG = {config_literal}\n    MAX_SIGNAL_PRODUCTS", text, flags=re.S)


def main() -> None:
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    write_audits()
    c42 = (ROOT / "ROUND5" / "strategies" / "round5_candidate_42.py").read_text(encoding="utf-8")
    c39 = (ROOT / "ROUND5" / "strategies" / "round5_candidate_39.py").read_text(encoding="utf-8")
    cfg39 = re.search(r"SIGNAL_CONFIG = (\{.*?\})\n    MAX_SIGNAL_PRODUCTS", c39, flags=re.S).group(1)

    probes: dict[str, str] = {}
    probes["probe_c42_qty10_all.py"] = c42.replace(
        "base_qty = 10 if strong or weight >= 1.2 else 6",
        "base_qty = 10",
    )
    probes["probe_c42_qty10_anchor10.py"] = probes["probe_c42_qty10_all.py"].replace(
        "int(min(3, self.LIMIT - position))",
        "int(min(10, self.LIMIT - position))",
    ).replace(
        "int(-min(3, self.LIMIT + position))",
        "int(-min(10, self.LIMIT + position))",
    )
    probes["probe_c42_threshold_92.py"] = c42.replace(
        "threshold = threshold + spread_penalty",
        "threshold = threshold * 0.92 + spread_penalty",
    )
    probes["probe_c42_threshold_85.py"] = c42.replace(
        "threshold = threshold + spread_penalty",
        "threshold = threshold * 0.85 + spread_penalty",
    )
    probes["probe_c42_top_hybrid.py"] = c42.replace(
        "style = cfg[4] if len(cfg) > 4 else \"passive\"",
        "style = cfg[4] if len(cfg) > 4 else \"passive\"\n            if product in self.TOP_HYBRID:\n                style = \"hybrid\"",
    ).replace(
        "MICRO_ANCHOR_TAKE_EXTRA = 2.0",
        "MICRO_ANCHOR_TAKE_EXTRA = 2.0\n    TOP_HYBRID = {'PANEL_4X4','PANEL_1X2','PANEL_1X4','MICROCHIP_OVAL','MICROCHIP_SQUARE','MICROCHIP_TRIANGLE','UV_VISOR_ORANGE','UV_VISOR_AMBER','GALAXY_SOUNDS_PLANETARY_RINGS','OXYGEN_SHAKE_GARLIC','OXYGEN_SHAKE_MORNING_BREATH'}",
    )
    probes["probe_c42_threshold_92_qty10.py"] = probes["probe_c42_threshold_92.py"].replace(
        "base_qty = 10 if strong or weight >= 1.2 else 6",
        "base_qty = 10",
    )
    probes["probe_c42_candidate39_config_micro_anchor.py"] = replace_signal_config(c42, cfg39)
    probes["probe_c42_candidate39_config_anchor10.py"] = probes["probe_c42_candidate39_config_micro_anchor.py"].replace(
        "int(min(3, self.LIMIT - position))",
        "int(min(10, self.LIMIT - position))",
    ).replace(
        "int(-min(3, self.LIMIT + position))",
        "int(-min(10, self.LIMIT + position))",
    )
    probes["probe_c42_peb_more_aggressive.py"] = c42.replace(
        "PEB_AGGRESSION = 1.08",
        "PEB_AGGRESSION = 1.32",
    ).replace(
        "qty = self.LIMIT - pos if buy_edge > edge_floor + 3.0 else min(8, self.LIMIT - pos)",
        "qty = self.LIMIT - pos",
    ).replace(
        "qty = self.LIMIT + pos if sell_edge > edge_floor + 3.0 else min(8, self.LIMIT + pos)",
        "qty = self.LIMIT + pos",
    )
    probes["probe_c42_scale_top_weights.py"] = c42
    for product in ["PANEL_4X4", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "UV_VISOR_ORANGE", "GALAXY_SOUNDS_PLANETARY_RINGS", "OXYGEN_SHAKE_GARLIC", "SLEEP_POD_COTTON", "TRANSLATOR_ECLIPSE_CHARCOAL"]:
        probes["probe_c42_scale_top_weights.py"] = re.sub(
            rf"('{product}': \('[^']+', \d+, )([0-9.]+)(, )([0-9.]+)(, '[^']+'\))",
            lambda m: m.group(1) + str(round(float(m.group(2)) * 0.92, 4)) + m.group(3) + str(round(float(m.group(4)) * 1.18, 4)) + m.group(5),
            probes["probe_c42_scale_top_weights.py"],
        )

    for name, text in probes.items():
        (PROBE_DIR / name).write_text(text, encoding="utf-8")
    print(f"wrote {len(probes)} probes to {PROBE_DIR}")


if __name__ == "__main__":
    main()
