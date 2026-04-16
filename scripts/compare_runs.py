from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def parse_activity_csv(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    reader = csv.DictReader(lines, delimiter=";")
    return list(reader)


def final_profit_by_product(rows: list[dict[str, str]]) -> dict[str, float]:
    if not rows:
        return {}
    last_timestamp = rows[-1]["timestamp"]
    result: dict[str, float] = {}
    for row in rows:
        if row["timestamp"] == last_timestamp:
            result[row["product"]] = float(row["profit_and_loss"])
    return result


def total_profit(rows: list[dict[str, str]]) -> float:
    return sum(final_profit_by_product(rows).values())


def parse_text_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    activities_marker = "Activities log:\n"
    trade_history_marker = "\n\n\n\n\nTrade History:\n"

    if activities_marker not in text:
        return {"path": str(path), "type": "unknown", "trade_count": 0}

    _, activity_tail = text.split(activities_marker, 1)
    if trade_history_marker in activity_tail:
        activity_csv, trade_blob = activity_tail.split(trade_history_marker, 1)
    else:
        activity_csv, trade_blob = activity_tail, "[]"

    activities = parse_activity_csv(activity_csv)
    trade_blob = trade_blob.strip()
    trades = []
    if trade_blob:
        try:
            trades = json.loads(trade_blob)
        except json.JSONDecodeError:
            trades = []

    return {
        "path": str(path),
        "type": "backtester_log",
        "activities": activities,
        "trade_count": len(trades),
        "profit_by_product": final_profit_by_product(activities),
        "total_profit": total_profit(activities),
    }


def parse_json_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "final_pnl_total" in payload and "final_pnl_by_product" in payload:
        return {
            "path": str(path),
            "type": "rust_metrics",
            "positions": {},
            "profit_by_product": {key: float(value) for key, value in (payload.get("final_pnl_by_product") or {}).items()},
            "total_profit": float(payload.get("final_pnl_total", 0.0)),
            "trade_count": int(payload.get("own_trade_count", 0)),
            "strategy": payload.get("trader_path"),
        }

    if "activitiesLog" in payload:
        activities = parse_activity_csv(payload["activitiesLog"])
        positions = {}
        for item in payload.get("positions", []) or []:
            positions[item["symbol"]] = item["quantity"]
        return {
            "path": str(path),
            "type": "official_json",
            "activities": activities,
            "positions": positions,
            "profit_by_product": final_profit_by_product(activities),
            "total_profit": float(payload.get("profit", total_profit(activities))),
            "trade_count": len(payload.get("tradeHistory", []) or []),
        }

    if "submissionId" in payload and "activitiesLog" in payload:
        activities = parse_activity_csv(payload["activitiesLog"])
        return {
            "path": str(path),
            "type": "official_log_json",
            "activities": activities,
            "positions": {},
            "profit_by_product": final_profit_by_product(activities),
            "total_profit": total_profit(activities),
            "trade_count": len(payload.get("tradeHistory", []) or []),
        }

    return {"path": str(path), "type": "json", "trade_count": 0}


def parse_any(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if path.is_dir():
        json_candidates = sorted(path.glob("*.json"))
        log_candidates = sorted(path.glob("*.log"))
        py_candidates = sorted(path.glob("*.py"))
        payload = {
            "path": str(path),
            "type": "directory",
            "strategy": str(py_candidates[0]) if py_candidates else None,
        }
        preferred_json = [candidate for candidate in json_candidates if candidate.name.lower() != "run.json"]
        if preferred_json:
            payload.update(parse_json_payload(preferred_json[0]))
        elif log_candidates:
            payload.update(parse_any(log_candidates[0]))
        elif json_candidates:
            payload.update(parse_json_payload(json_candidates[0]))
        return payload

    if path.suffix.lower() == ".json":
        return parse_json_payload(path)

    if path.suffix.lower() == ".log":
        text = path.read_text(encoding="utf-8")
        if text.lstrip().startswith("{"):
            return parse_json_payload(path)
        return parse_text_log(path)

    raise ValueError(f"Unsupported path: {path}")


def render_summary(label: str, payload: dict[str, Any]) -> list[str]:
    lines = [
        f"{label}: {payload.get('path')}",
        f"  type: {payload.get('type', 'unknown')}",
        f"  total profit: {payload.get('total_profit', 'n/a')}",
        f"  trade count: {payload.get('trade_count', 'n/a')}",
    ]
    strategy = payload.get("strategy")
    if strategy:
        lines.append(f"  strategy: {strategy}")
    positions = payload.get("positions") or {}
    if positions:
        lines.append(f"  positions: {positions}")
    profit_by_product = payload.get("profit_by_product") or {}
    if profit_by_product:
        lines.append(f"  profit by product: {profit_by_product}")
    return lines


def render_diff(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    lines = []
    left_total = float(left.get("total_profit", 0.0))
    right_total = float(right.get("total_profit", 0.0))
    lines.append(f"profit delta (right - left): {right_total - left_total}")

    keys = sorted(set((left.get("profit_by_product") or {}).keys()) | set((right.get("profit_by_product") or {}).keys()))
    if keys:
        lines.append("per-product deltas:")
        for key in keys:
            left_value = float((left.get("profit_by_product") or {}).get(key, 0.0))
            right_value = float((right.get("profit_by_product") or {}).get(key, 0.0))
            lines.append(f"  {key}: {right_value - left_value}")

    lines.append(f"trade count delta (right - left): {int(right.get('trade_count', 0)) - int(left.get('trade_count', 0))}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two Prosperity run artifacts.")
    parser.add_argument("left")
    parser.add_argument("right")
    args = parser.parse_args()

    left = parse_any(Path(args.left))
    right = parse_any(Path(args.right))

    print("\n".join(render_summary("LEFT", left)))
    print()
    print("\n".join(render_summary("RIGHT", right)))
    print()
    print("\n".join(render_diff(left, right)))


if __name__ == "__main__":
    main()
