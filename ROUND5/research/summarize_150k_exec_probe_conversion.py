from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ROUND5" / "research" / "outputs"
BT = OUT / "backtests"


PORTAL_RUNS = [
    BT / "c35_36_exec_probes_portal",
    BT / "c35_36_exec_probes_portal_clean2",
    BT / "c35_36_exec_probes_portal_remaining40k",
    BT / "c35_36_exec_probes_portal_remaining40k_isolation",
    BT / "c35_36_exec_probes_portal_remaining40k_followup",
    BT / "c35_36_exec_probes_portal_highroi_grid",
    BT / "c35_36_exec_probes_portal_anchor_near10000",
    BT / "c35_36_exec_probes_portal_increment_near10000_micro_uv",
    BT / "c35_36_exec_probes_portal_robust_micro_uv_grid",
    BT / "c35_36_exec_probes_portal_two_branch_robot",
    BT / "c35_36_exec_probes_portal_fresh_edge_pivot",
    BT / "c35_36_exec_probes_portal_fresh_category_residuals",
    BT / "c35_36_exec_probes_portal_fresh_oracle_mimic",
    BT / "c35_36_exec_probes_portal_fresh_structural",
    BT / "c35_36_exec_probes_portal_passive_mm_skip",
    BT / "c35_36_exec_probes_portal_passive_mm_replace",
    BT / "c35_36_exec_probes_portal_microstructure_fill",
    BT / "c35_36_exec_probes_portal_regime_gap",
    BT / "c35_36_exec_probes_portal_pebbles_fv",
    BT / "c35_36_exec_probes_portal_broad_anchor_passive",
]
FULL_RUNS = [
    BT / "c35_36_exec_probes_full_promising",
    BT / "c35_36_exec_probes_full_clean2",
    BT / "c35_36_exec_probes_full_remaining40k",
    BT / "c35_36_exec_probes_full_remaining40k_isolation",
    BT / "c35_36_exec_probes_full_remaining40k_followup",
    BT / "c35_36_exec_probes_full_highroi_grid",
    BT / "c35_36_exec_probes_full_increment_near10000_micro_uv",
    BT / "c35_36_exec_probes_full_robust_lower_portal",
    BT / "c35_36_exec_probes_full_robust_micro_uv_grid",
    BT / "c35_36_exec_probes_full_conservative_anchor_increment",
    BT / "c35_36_exec_probes_full_two_branch_robot",
    BT / "c35_36_exec_probes_full_fresh_pivot_best",
]


ALL_PRODUCTS = [
    "PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L", "PEBBLES_XL",
    "MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_SQUARE", "MICROCHIP_RECTANGLE", "MICROCHIP_TRIANGLE",
    "PANEL_1X2", "PANEL_1X4", "PANEL_2X2", "PANEL_2X4", "PANEL_4X4",
    "OXYGEN_SHAKE_MORNING_BREATH", "OXYGEN_SHAKE_EVENING_BREATH", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_GARLIC",
    "UV_VISOR_YELLOW", "UV_VISOR_AMBER", "UV_VISOR_ORANGE", "UV_VISOR_RED", "UV_VISOR_MAGENTA",
    "ROBOT_DISHES", "ROBOT_MOPPING", "ROBOT_LAUNDRY", "ROBOT_IRONING", "ROBOT_VACUUMING",
    "SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON",
    "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_VOID_BLUE", "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_SPACE_GRAY", "TRANSLATOR_ECLIPSE_CHARCOAL",
    "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_WINDS", "GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_SOLAR_FLAMES",
    "SNACKPACK_RASPBERRY", "SNACKPACK_STRAWBERRY", "SNACKPACK_CHOCOLATE", "SNACKPACK_VANILLA", "SNACKPACK_PISTACHIO",
]


CLASSIFICATION = {
    "PEBBLES_XS": ("gated_add", "Fair-value core trades it but portal PnL is negative; boost/taker variants hurt, so keep only in balanced FV core or information branch."),
    "PEBBLES_S": ("validated_add", "Strong PEBBLES fair-value leg; preserve current candidate 35 logic."),
    "PEBBLES_M": ("validated_add", "Positive in core; undercapture probes improved some variants but aggressive boost damaged full/portal balance."),
    "PEBBLES_L": ("validated_add", "Direct FV is weak, but dual-anchor execution converts it to positive portal and improves full; use anchor role, not FV overlay."),
    "PEBBLES_XL": ("validated_add", "Strongest PEBBLES FV leg; preserve core."),
    "MICROCHIP_CIRCLE": ("exclude", "Passive/hybrid probes were toxic or portal-only; high oracle not executable yet."),
    "MICROCHIP_OVAL": ("validated_add", "Stable positive base microchip leg."),
    "MICROCHIP_SQUARE": ("validated_add", "Stable positive base leg; hybrid retune was toxic, so preserve current config."),
    "MICROCHIP_RECTANGLE": ("validated_add", "Positive base leg; no stronger add-on found."),
    "MICROCHIP_TRIANGLE": ("gated_add", "Portal-upside hybrid adds about +4.2k, but full score drops materially; use only in portal/upside branch or with stronger gate."),
    "PANEL_1X2": ("validated_add", "Stable positive panel leg."),
    "PANEL_1X4": ("validated_add", "Stable positive panel leg."),
    "PANEL_2X2": ("validated_add", "Positive in candidate 35, but weaker than other panel legs."),
    "PANEL_2X4": ("validated_add", "Previously unused by 35; clean probes add about +1.8k portal and full stays strong."),
    "PANEL_4X4": ("validated_add", "Strong existing panel leg."),
    "OXYGEN_SHAKE_MORNING_BREATH": ("validated_add", "Stable positive existing OXYGEN leg."),
    "OXYGEN_SHAKE_EVENING_BREATH": ("gated_add", "Small positive in current 35; no larger robust conversion found."),
    "OXYGEN_SHAKE_MINT": ("gated_add", "Small positive only; keep low weight or use as conditional."),
    "OXYGEN_SHAKE_CHOCOLATE": ("validated_add", "Positive existing OXYGEN leg."),
    "OXYGEN_SHAKE_GARLIC": ("validated_add", "Strong existing OXYGEN leg."),
    "UV_VISOR_YELLOW": ("gated_add", "Small positive in 35 but full proxy fragile; keep only as current low-weight leg."),
    "UV_VISOR_AMBER": ("gated_add", "Portal-upside hybrid adds about +4.9k, but full score drops materially; use only in portal/upside branch or with stronger gate."),
    "UV_VISOR_ORANGE": ("validated_add", "Strong existing UV leg."),
    "UV_VISOR_RED": ("validated_add", "Positive existing UV leg."),
    "UV_VISOR_MAGENTA": ("exclude", "Tiny portal contribution in broad probes and negative full proxy; do not include robust branch."),
    "ROBOT_DISHES": ("gated_add", "Hybrid adds about +2.3k portal but crushes full score; likely execution/fill edge that needs a dedicated gate."),
    "ROBOT_MOPPING": ("gated_add", "Small/unstable; candidate 36 uses it but c35 add-on is not convincing."),
    "ROBOT_LAUNDRY": ("exclude", "Toxic in c35-compatible probes despite c36 portal positives; do not add to robust stack."),
    "ROBOT_IRONING": ("validated_add", "Stable existing robot leg."),
    "ROBOT_VACUUMING": ("validated_add", "Clean c35 stack converts it into +1.36k portal and full remains strong."),
    "SLEEP_POD_COTTON": ("validated_add", "Stable existing sleep leg."),
    "SLEEP_POD_POLYESTER": ("validated_add", "Stable existing sleep leg."),
    "SLEEP_POD_SUEDE": ("validated_add", "Previously unused; clean stack adds +1.88k portal and survives full validation."),
    "SLEEP_POD_LAMB_WOOL": ("validated_add", "Positive existing sleep leg."),
    "SLEEP_POD_NYLON": ("validated_add", "Positive existing sleep leg, lower edge."),
    "TRANSLATOR_GRAPHITE_MIST": ("validated_add", "Stable existing translator leg."),
    "TRANSLATOR_VOID_BLUE": ("validated_add", "Stable existing translator leg."),
    "TRANSLATOR_ASTRO_BLACK": ("validated_add", "Previously unused; clean stack adds +2.59k portal with strong full result."),
    "TRANSLATOR_SPACE_GRAY": ("validated_add", "Stable existing translator leg."),
    "TRANSLATOR_ECLIPSE_CHARCOAL": ("validated_add", "Signal version was negative, but 10k anchor execution adds about +5k portal; use anchor engine, not old signal."),
    "GALAXY_SOUNDS_PLANETARY_RINGS": ("validated_add", "Stable existing galaxy leg."),
    "GALAXY_SOUNDS_SOLAR_WINDS": ("validated_add", "Stable existing galaxy leg."),
    "GALAXY_SOUNDS_DARK_MATTER": ("validated_add", "Stable existing galaxy leg."),
    "GALAXY_SOUNDS_BLACK_HOLES": ("validated_add", "Previously unused; clean stack adds about +2.2k portal and full remains strong."),
    "GALAXY_SOUNDS_SOLAR_FLAMES": ("validated_add", "Stable existing galaxy leg."),
    "SNACKPACK_RASPBERRY": ("validated_add", "Clean stack converts it to +1.31k portal and full improves."),
    "SNACKPACK_STRAWBERRY": ("validated_add", "Clean stack converts it to +1.17k portal and full improves."),
    "SNACKPACK_CHOCOLATE": ("exclude", "Only tiny/zero portal result as direct/anchor add; do not carry except in information probes."),
    "SNACKPACK_VANILLA": ("gated_add", "Weak alone, but as a 10k anchor it helps the loose portal-upside branch reach 120.3k; not a robust default."),
    "SNACKPACK_PISTACHIO": ("validated_add", "Clean stack converts it to +0.54k portal and full improves; low weight only."),
}


def category(product: str) -> str:
    if product.startswith("OXYGEN_SHAKE_"):
        return "OXYGEN_SHAKE"
    if product.startswith("GALAXY_SOUNDS_"):
        return "GALAXY_SOUNDS"
    if product.startswith("SLEEP_POD_"):
        return "SLEEP_POD"
    if product.startswith("UV_VISOR_"):
        return "UV_VISOR"
    return product.split("_")[0]


def read_summaries() -> pd.DataFrame:
    frames = []
    for run in PORTAL_RUNS + FULL_RUNS:
        path = run / "summary.csv"
        if path.exists():
            frame = pd.read_csv(path)
            frame["run"] = run.name
            frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def pivot_scores(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy, group in summary.groupby("strategy"):
        row = {"Strategy": strategy}
        for tool in ("kevin", "xeeshan"):
            raw_portal = group[(group.tool == tool) & (group.suite == "portal") & (group.capped == False)]  # noqa: E712
            cap_portal = group[(group.tool == tool) & (group.suite == "portal") & (group.capped == True)]  # noqa: E712
            full = group[(group.tool == tool) & (group.suite == "full") & (group.capped == False)]  # noqa: E712
            if not raw_portal.empty:
                row[f"Portal {tool.title()}"] = int(raw_portal.iloc[-1].profit)
            if not cap_portal.empty:
                row[f"Portal {tool.title()} 50k Cap"] = int(cap_portal.iloc[-1].profit)
            if not full.empty:
                row[f"Full {tool.title()}"] = int(full.iloc[-1].profit)
        portal_group = group[(group.suite == "portal") & (group.capped == False)]  # noqa: E712
        trades = portal_group.trade_count.dropna().max()
        avg_fill = portal_group.avg_fill_quantity.dropna().max()
        row["Trades"] = 0 if pd.isna(trades) else int(trades)
        row["Avg Fill"] = 0.0 if pd.isna(avg_fill) else round(float(avg_fill), 2)
        rows.append(row)
    out = pd.DataFrame(rows).sort_values(["Portal Kevin", "Full Kevin"], ascending=[False, False], na_position="last")
    return out


def read_product_pnl() -> pd.DataFrame:
    frames = []
    for run in PORTAL_RUNS:
        path = run / "product_pnl.csv"
        if path.exists():
            frame = pd.read_csv(path)
            frame["run"] = run.name
            frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def best_probe_pnl(product_pnl: pd.DataFrame) -> dict[str, tuple[str, float]]:
    df = product_pnl[(product_pnl.tool == "kevin") & (product_pnl.capped == False)]  # noqa: E712
    result = {}
    for product, group in df.groupby("product"):
        best = group.sort_values("pnl", ascending=False).iloc[0]
        result[product] = (best.strategy, float(best.pnl))
    return result


def current_pnl() -> dict[str, float]:
    path = OUT / "candidate_35_36_portal_product_pnl.csv"
    frame = pd.read_csv(path)
    frame = frame[frame["strategy"] == "round5_candidate_35.py"]
    return {row["product"]: float(row["portal_kevin_pnl"]) for _, row in frame.iterrows()}


def oracle_table() -> pd.DataFrame:
    path = OUT / "candidate_35_36_marginal_engine_table.csv"
    return pd.read_csv(path)


def write_probe_tables(score_table: pd.DataFrame) -> None:
    score_table.to_csv(OUT / "candidate_35_36_probe_score_table.csv", index=False)
    lines = ["# Candidate 35/36 Executable Probe Score Table", ""]
    lines.append(score_table.fillna("").to_markdown(index=False))
    lines.append("")
    (OUT / "candidate_35_36_probe_score_table.md").write_text("\n".join(lines), encoding="utf-8")


def write_coverage(product_pnl: pd.DataFrame) -> pd.DataFrame:
    base = current_pnl()
    best = best_probe_pnl(product_pnl)
    oracle = oracle_table().set_index("product")
    rows = []
    for product in ALL_PRODUCTS:
        cls, note = CLASSIFICATION[product]
        best_strategy, best_pnl = best.get(product, ("", 0.0))
        base_pnl = base.get(product, 0.0)
        oracle_capacity = float(oracle.loc[product, "raw_oracle_units_not_pnl"]) if product in oracle.index else 0.0
        practical = float(oracle.loc[product, "practical_engine_proxy"]) if product in oracle.index else 0.0
        rows.append(
            {
                "product": product,
                "category": category(product),
                "candidate35_portal_pnl": base_pnl,
                "best_probe_portal_pnl": best_pnl,
                "best_probe": best_strategy,
                "classification": cls,
                "oracle_capacity_units": oracle_capacity,
                "practical_engine_proxy": practical,
                "coverage_role": (
                    "active_trade"
                    if cls in {"validated_add", "gated_add"}
                    else "exclude"
                ),
                "notes": note,
            }
        )
    coverage = pd.DataFrame(rows)
    coverage.to_csv(OUT / "candidate_35_36_product_coverage_plan.csv", index=False)
    unused = coverage[coverage["candidate35_portal_pnl"].abs() < 1e-9].copy()
    unused.to_csv(OUT / "candidate_35_36_unused_product_table.csv", index=False)
    return coverage


def write_undercapture(coverage: pd.DataFrame) -> None:
    focus = [
        "PEBBLES_M", "PEBBLES_XS", "PEBBLES_L", "MICROCHIP_SQUARE", "MICROCHIP_CIRCLE",
        "MICROCHIP_TRIANGLE", "PANEL_2X4", "ROBOT_DISHES", "ROBOT_LAUNDRY",
        "ROBOT_VACUUMING", "SLEEP_POD_SUEDE", "UV_VISOR_MAGENTA", "SNACKPACK_STRAWBERRY",
        "SNACKPACK_RASPBERRY", "SNACKPACK_PISTACHIO", "GALAXY_SOUNDS_BLACK_HOLES",
        "TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL",
    ]
    rows = []
    cov = coverage.set_index("product")
    fix = {
        "PEBBLES_M": "Keep current FV core; mild boost did not produce a superior robust repair.",
        "PEBBLES_XS": "Do not boost; all aggressive repairs either hurt portal or full.",
        "PEBBLES_L": "Do not add direct overlay; anchor/FV role only.",
        "MICROCHIP_SQUARE": "Preserve current config; hybrid retune was toxic.",
        "MICROCHIP_CIRCLE": "Reject for now; passive/hybrid failed despite oracle.",
        "MICROCHIP_TRIANGLE": "Candidate 36 portal-only/gated; not robust add-on to 35 yet.",
        "PANEL_2X4": "Validated add via clean stack.",
        "ROBOT_DISHES": "Hybrid portal signal exists, but not enough/additive; information branch only.",
        "ROBOT_LAUNDRY": "Reject in c35 stack; toxic.",
        "ROBOT_VACUUMING": "Validated low-weight add via clean stack.",
        "SLEEP_POD_SUEDE": "Validated add via clean stack.",
        "UV_VISOR_MAGENTA": "Reject; tiny portal and bad full proxy.",
        "SNACKPACK_STRAWBERRY": "Validated low-weight add via clean stack.",
        "SNACKPACK_RASPBERRY": "Validated low-weight add via clean stack.",
        "SNACKPACK_PISTACHIO": "Validated low-weight add via clean stack.",
        "GALAXY_SOUNDS_BLACK_HOLES": "Validated add via clean stack.",
        "TRANSLATOR_ASTRO_BLACK": "Validated add via clean stack.",
        "TRANSLATOR_ECLIPSE_CHARCOAL": "Validated only through 10k anchor execution; replace negative old signal.",
    }
    for product in focus:
        row = cov.loc[product]
        rows.append(
            {
                "product": product,
                "category": row["category"],
                "candidate35_portal_pnl": row["candidate35_portal_pnl"],
                "best_probe_portal_pnl": row["best_probe_portal_pnl"],
                "best_probe": row["best_probe"],
                "classification": row["classification"],
                "decision": fix[product],
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "candidate_35_36_undercapture_fix_table.csv", index=False)


def write_summary(score_table: pd.DataFrame, coverage: pd.DataFrame) -> None:
    best = score_table.iloc[0]
    validated = coverage[coverage.classification == "validated_add"]
    gated = coverage[coverage.classification == "gated_add"]
    excluded = coverage[coverage.classification == "exclude"]
    text = f"""# Candidate 35/36 Executable Probe Conversion

This phase converted the 150k ceiling-gap map into executable probes. It did not create candidates 37-40.

## Main Results

- Best portal probe: `{best['Strategy']}` at `{int(best['Portal Kevin']):,}` Kevin / `{int(best['Portal Xeeshan']):,}` Xeeshan, with capped replay matching.
- Best full-validated robust branch: `probe_c35_anchor_both_micro_uv_conservative.py` at `111,868` portal and `379,278`/`379,319` full.
- Best pure full score among conservative-anchor probes: `probe_increment_snackpack_micro_uv_conservative.py` at `111,490`/`111,500` portal and `379,776`/`379,726` full; it improves full slightly but gives up portal versus the robust branch.
- Best intermediate blend: `probe_grid_robust_micro_uv_uv_hybrid_micro_passive.py` at `116,408` portal and `332,888`/`332,928` full.
- Best portal/full upside branch before robot toxicity: `probe_increment_vanilla_micro_uv_loose.py` at `120,300`/`120,310` portal and `263,754`/`263,918` full.
- Best fresh-category pivot add-on: `probe_pivot_portal_all_fresh_no_robot_micro_uv.py` at `121,436`/`121,446` portal and `254,379`/`254,543` full; it is a small portal lift, not an independent 10k mechanism.
- Best robust fresh-category add-on: `probe_pivot_robust_panel.py` at `112,884` portal and `371,384`/`371,426` full; it improves portal but gives up about `8k` full versus the robust branch.
- Highest raw portal branch: `probe_branch_portal_vanilla_micro_uv_robot_pair.py` at `121,620`/`121,630` portal, but full collapses to `114,755`/`114,557`; use as official-window information, not robust base.
- Candidate 36 remains below the best new portal probe (`105.5k` vs `120.0k`) and far weaker on full history.
- No executable probe reached `150k`; the gap is reduced from roughly `40k` to roughly `30k`, but still real.

## What Was Actually Fixed

- `TRANSLATOR_ECLIPSE_CHARCOAL`: old signal was negative, but the candidate-36-style `10,000` anchor engine adds about `+5k` portal and keeps full strong.
- `PEBBLES_L`: direct fair-value overlay remains weak, but adding it to the `10,000` anchor engine adds another `+1.2k` portal and improves full.
- `TRANSLATOR_ASTRO_BLACK`: previously unused; clean stack adds `+2.6k` portal.
- `GALAXY_SOUNDS_BLACK_HOLES`: previously unused; clean stack adds `+2.2k` portal.
- `SLEEP_POD_SUEDE`: previously unused; clean stack adds `+1.9k` portal.
- `PANEL_2X4`: converted into a real add-on at about `+1.8k` portal.
- `ROBOT_VACUUMING`: low-weight reversal add-on contributes about `+1.4k` portal.
- `SNACKPACK_STRAWBERRY/RASPBERRY/PISTACHIO`: small but real low-weight additions in the clean stack, and full history improves.
- `MICROCHIP_TRIANGLE` and `UV_VISOR_AMBER`: together move portal from `110.97k` to `120.03k`; individually they are `113.98k` and `114.68k`. Both are portal-upside/gated, not robust defaults, because full drops to about `305k-308k` alone and `266k` together.

## Rejected Or Still Conditional

- `PEBBLES_M/XS`: oracle undercapture is real, but direct boost/taker repairs did not improve the robust base. Keep the current fair-value core; do not force an overlay yet.
- `MICROCHIP_CIRCLE`: high oracle but toxic in executable probes.
- `MICROCHIP_TRIANGLE`: useful as portal-upside, not robust default.
- `ROBOT_LAUNDRY`: toxic when grafted into candidate 35.
- `ROBOT_DISHES`: hybrid can make portal PnL and lifted the raw portal branch to `121.6k`, but full drops as low as `114k`; this is official-window-fragile until a better regime/fill gate is found.
- `UV_VISOR_MAGENTA`: tiny portal contribution and poor full proxy; exclude.
- `SNACKPACK_CHOCOLATE`: no usable executable edge. `SNACKPACK_VANILLA` is not a standalone edge, but remains conditional as a 10k-anchor add-on in the portal-upside branch.

## Highest-ROI Next Profit Actions

The phase should not be treated as merely documentation-complete. Four unresolved mechanisms still justify focused work before candidate construction if the goal remains `150k+`:

1. `MICROCHIP_TRIANGLE + UV_VISOR_AMBER` portal gate: already adds about `+8.4k` portal over the conservative robust branch, but costs roughly `115k` full-history PnL when run loose.
2. `ROBOT_DISHES` execution/fill gate: adds about `+1.3k` over the best portal-upside branch when paired with `ROBOT_MOPPING`, but full-history toxicity means the current trigger is too broad.
3. Candidate-36 PANEL/TRANSLATOR/ROBOT machinery: broad transplants failed, but product attribution shows sizeable portal-positive pieces; the next probe should transplant those mechanics one family at a time, not all together.
4. Anchor/fair-value expansion: `TRANSLATOR_ECLIPSE_CHARCOAL` and `PEBBLES_L` proved anchor execution can convert weak signals into robust PnL. Other anchor-like products should be tested only with explicit cap/full validation.

Fresh-category pivot result: SLEEP, PANEL, TRANSLATOR/GALAXY, OXYGEN/SNACKPACK signal retunes and category residual engines did not reveal a new `10k-40k` mechanism. PANEL/fresh-signal additions add roughly `+1k` portal but reduce full-history robustness; category residuals and oracle-mimic overrides generally hurt. This suggests the remaining 150k gap is not explained by simple undertraded fresh-category momentum/reversal or same-category residuals.

Post-pivot high-ROI exhaustion:

- Lead-lag and semantic/name curves across PANEL, SLEEP, TRANSLATOR/GALAXY, and OXYGEN/SNACKPACK were rejected; all tested variants underperformed both active bases.
- Passive fill / rolling-fair market making did not convert the passive oracle. Skip variants were baseline; replacement variants degraded heavily.
- Microstructure imbalance/fill quoting was rejected; replacing fresh-category engines with imbalance quoting cut portal to roughly `71k-104k`.
- Regime-gated practical-gap probes produced baseline/no lift, so the simple spread/imbalance gates did not unlock the high-oracle products.
- PEBBLES quadratic/spline-like fair-value variants were rejected; current linear leave-one-out FV remains materially better.
- Broad `10,000` anchor families were rejected; the anchor edge appears narrow (`TRANSLATOR_ECLIPSE_CHARCOAL`, `PEBBLES_L`, and conditional `SNACKPACK_VANILLA` in portal branch), not a universal product rule.

## Coverage Read

- Validated direct/active products: `{len(validated)}`.
- Conditional/gated products: `{len(gated)}`.
- Excluded products: `{len(excluded)}`.
- A 30+ product strategy is now justified if it uses the clean stack architecture. The validated/gated set is broad enough, but products must keep separate engines; a generic all-product scanner is still wrong.

## 150k Read

`150k` is closer but not proven. The best executable conversion moved the portal benchmark from candidate 35's `91.9k` and candidate 36's `105.5k` to `121.6k`; the best robust-full branch is `111.9k` portal with `379k` full. A fresh-category pivot, structural lead-lag/curve search, passive-fill search, regime-gated search, PEBBLES formula search, and broad-anchor search all failed to find an independent high-ROI mechanism. The remaining official-window gap is still roughly `28k`; based on current executable evidence, it is not reachable through the tested oracle-list families.

`200k` still likely requires another structural/execution edge, most likely passive/fill quality or a better candidate-36-style portal engine.
"""
    (OUT / "candidate_35_36_executable_probe_summary.md").write_text(text, encoding="utf-8")


def write_blueprint() -> None:
    text = """# Candidate 37-40 Blueprint

Do not build until explicitly instructed. This blueprint supersedes the prior oracle-only version and is based on executable probes.

## Ceiling Read

- `150k` is not yet proven reachable from the converted executable probes. The best robust-full branch is `probe_c35_anchor_both_micro_uv_conservative.py` at about `111.9k` portal and `379k` full; the best balanced portal-upside branch is `probe_increment_vanilla_micro_uv_loose.py` at about `120.3k` portal and `264k` full; the highest raw portal branch is `probe_branch_portal_vanilla_micro_uv_robot_pair.py` at about `121.6k` portal but only `115k` full.
- The remaining path to `150k` requires another additive `30k` mechanism beyond the clean/anchor stack. The tested candidates for that mechanism were rejected: broad candidate-36 family grafts, fresh-category retunes, category residuals, lead-lag/semantic curves, passive fill, microstructure imbalance quoting, regime-gated add-ons, PEBBLES quadratic FV, and broad 10,000 anchors.
- `200k` is blocked by the absence of a new high-capacity executable structure. Current known add-ons are mostly 0.5k-9k product fixes; reaching 200k likely needs an untested market-quality/execution edge not represented by the current Kevin/Xeeshan oracle proxies, or a genuinely new category formula not found by the current curve/residual probes.
- A 30+ product strategy is justified only under the clean-stack classification: `validated_add` products can trade directly, `gated_add` products need explicit branch/gate logic, and excluded products should stay out even if their oracle score is high.

## Candidate 37: Robust Clean Stack

- Base: `round5_candidate_35.py`.
- Add: `PANEL_2X4`, `SLEEP_POD_SUEDE`, `GALAXY_SOUNDS_BLACK_HOLES`, `TRANSLATOR_ASTRO_BLACK`, `ROBOT_VACUUMING`, low-weight `SNACKPACK_STRAWBERRY/RASPBERRY/PISTACHIO`.
- Preserve: candidate 35 PEBBLES core and existing validated signal set.
- Avoid: `MICROCHIP_CIRCLE`, `ROBOT_LAUNDRY`, `UV_VISOR_MAGENTA`, `SNACKPACK_CHOCOLATE/VANILLA`.
- Expected: about `104k-106k` portal and `350k+` full if implemented like `probe_c35_stack_clean.py`.
- Role: best robust hidden-final development base.

## Candidate 38: Robust-Full Branch

- Base: candidate 37 architecture plus candidate-36-style `10,000` anchor execution for `TRANSLATOR_ECLIPSE_CHARCOAL` and `PEBBLES_L`.
- Add conservative passive `MICROCHIP_TRIANGLE` and `UV_VISOR_AMBER` gates exactly like `probe_c35_anchor_both_micro_uv_conservative.py`.
- Expected: about `111.9k` portal and `379k+` full if implementation matches the probe.
- Role: first official submission candidate from this phase.

## Candidate 39: Portal-Upside Branch

- Base: candidate 38 architecture, but use the loose MICROCHIP/UV gate plus `SNACKPACK_VANILLA` anchor like `probe_increment_vanilla_micro_uv_loose.py`.
- Purpose: maximize official-window upside while preserving state safety and avoiding candidate-36's broad full-history toxicity.
- Known evidence: `120,300`/`120,310` portal with full still positive around `264k`, but materially weaker than the robust-full branch.
- Optional information variant: add the tight `ROBOT_DISHES`/`ROBOT_MOPPING` pair to reach `121.6k` portal, but only as an official-window stress test because full falls to about `115k`.
- Role: official-window/upside branch and idea mine, not hidden-final base unless later full score improves.

## Candidate 40: Aggressive 150k Composite

- Base: candidate 38 and candidate 39 as separate lineages, not a blind merge.
- Add only engines that do not crowd out the clean stack:
  - candidate-36 PANEL/TRANSLATOR/ROBOT machinery if ablated additive,
  - a dedicated passive/fill engine for `ROBOT_DISHES` only if it beats the current `121.6k` raw portal branch without destroying full history,
  - a separate MICROCHIP_TRIANGLE portal gate if it does not damage `MICROCHIP_SQUARE`.
- First aggressive version should try to add a new mechanism to the portal-upside branch without importing the full-history damage into the robust-full branch.
- Explicitly keep per-engine ranking caps so weak add-ons cannot crowd out PEBBLES/PANEL/GALAXY/SLEEP/SNACKPACK validated legs.
- Expected: must beat `120.0k` portal before full validation; otherwise it is not a real 150k-push improvement.
- Role: aggressive 150k attempt.

## Validation Order

1. Portal Kevin/Xeeshan with cap check.
2. Product/category attribution on portal JSON logs.
3. Full Kevin/Xeeshan score-only for any probe above `105k` portal or any robust branch above candidate 35.
4. Only after official results, decide whether to promote candidate 38 or candidate 40.
"""
    (OUT / "candidate_37_40_blueprint.md").write_text(text, encoding="utf-8")


def main() -> None:
    summary = read_summaries()
    score_table = pivot_scores(summary)
    write_probe_tables(score_table)
    product_pnl = read_product_pnl()
    coverage = write_coverage(product_pnl)
    write_undercapture(coverage)
    write_summary(score_table, coverage)
    write_blueprint()
    print("Wrote executable probe conversion outputs")


if __name__ == "__main__":
    main()
