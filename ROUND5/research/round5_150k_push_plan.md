# Round 5 150k Push Plan

This is the active post-candidate-35/36 research plan.

Current phase update: the first ceiling-gap pass produced the required oracle/proxy map, but that map is not build-ready. The active next step is executable probe conversion using `round5_150k_executable_probe_plan.md`.

## Target

The immediate target is `150k+` official portal PnL.

Stretch target is `200k+`.

The target must be reached without:

- timestamp hardcoding,
- future leakage,
- official-log parsing inside a strategy,
- local file reads,
- unsupported imports,
- state-cap violations,
- pure portal-window memorization.

## Leaderboard Context

Current leaderboard read:

| Level | Approx Official Portal PnL | Meaning |
|---|---:|---|
| Top 100 cutoff | 114k | minimum competitive threshold |
| Strong range | 150k+ | roughly top-50 / high-97th percentile territory |
| Stretch range | 200k+ | roughly top-20 territory |
| Elite range | 300k-450k | likely another major structural edge |

Top entries combine high PnL with low drawdown and avg fill around `8-11`. That profile looks like repeated high-confidence edge extraction, not random broad trading.

## Current Strategy Truth

| Strategy | Portal | Full | Role |
|---|---:|---:|---|
| `round5_candidate_35.py` | 91.9k | 287.4k | current robust development base |
| `round5_candidate_36.py` | 105.5k | 36.7k | current portal-upside branch |
| `round5_candidate_34.py` | 105.9k | -49.8k | portal exploit / idea mine |
| `round5_candidate_33.py` | 85.9k | 244.7k | prior aggressive robust base |
| `round5_candidate_32.py` | 70.7k | 250.2k | prior clean robust base |

Candidate 35 is the best current base for robust development.

Candidate 36 is useful, but it is not robust enough to be the hidden-final base.

## Core Problem

We are not trying to add another `2k-5k`.

We need to identify the missing `40k-100k` official-window component.

The next step must fix meaningful undercaptures and investigate unused products directly. A final strategy should aim to trade at least `30` products only if those products have validated or gated executable edge.

The next phase must answer:

- where 35/36 leave large oracle capacity uncaptured,
- what products/categories can still add enough PnL to matter,
- which engines are underused or missing,
- which current engines crowd out stronger trades,
- whether there is another structural mechanism beyond PEBBLES and the 10,000-anchor family,
- whether passive market making/fill mechanics are underutilized.

## Required Oracle-Like Diagnostics

### 1. Taker Oracle

Estimate directional opportunity by product/category if future mid movement were known.

Purpose:

- identify products where crossing the spread could be justified,
- separate momentum/reversal potential from passive-only potential,
- locate high-capacity products ignored by 35/36.

Must include realistic top-of-book cost assumptions.

### 2. Passive Fill Oracle

Estimate opportunity from quoting at or improving the best bid/ask, then measuring forward markout.

Purpose:

- find market-making products,
- detect high-hit-rate passive edges,
- explain leaderboard-like low drawdown / high fill patterns.

This is mandatory because prior top scores look more like repeated fill-quality harvesting than generic forecasting.

### 3. Inventory-Constrained Oracle

Recompute opportunity under actual `±10` product position limits and liquidation assumptions.

Purpose:

- convert raw oracle capacity into realistic strategy capacity,
- identify products where oracle looks high but inventory traps make it unusable,
- rank products by executable capacity rather than hindsight fantasy.

### 4. Residual / Fair-Value Oracle

Search for synthetic fair-value relationships beyond PEBBLES.

Must cover:

- MICROCHIP,
- PANEL,
- SLEEP_POD,
- TRANSLATOR,
- GALAXY_SOUNDS,
- OXYGEN_SHAKE,
- UV_VISOR,
- SNACKPACK,
- ROBOT.

Purpose:

- discover category formulas, baskets, curves, anchors, and pair residuals,
- identify online-computable residual edges,
- distinguish traded products from anchor-only products.

### 5. Regime Oracle

Split opportunity by:

- spread,
- volatility,
- depth,
- imbalance,
- trend/reversal state,
- product/category state,
- timestamp block without exact timestamp hardcoding.

Purpose:

- find conditional edges,
- upgrade previously weak products into gated engines,
- reduce candidate 36-style full-history toxicity.

### 6. Marginal-Addition Oracle

Evaluate candidate 35 and 36 as current portfolios and ask:

- which product/engine would add PnL if added now,
- which product/engine interferes with existing ranking/capacity,
- which current engine crowds out a better one,
- where position/capacity is underused.

This is the most important diagnostic for candidates 37-40.

### 7. Engine-Family Search

For every meaningful oracle gap, test product/category engines:

- momentum,
- reversal,
- breakout,
- rolling mean reversion,
- category median reversion,
- synthetic fair-value residual,
- pair residual,
- passive market making,
- taker trigger,
- imbalance/microprice,
- volatility/spread/depth gated versions,
- multi-engine hybrids.

## Execution Rules

Use `ROUND5/research/round5_backtester.py`.

Portal-heavy batches:

```powershell
python ROUND5/research/round5_backtester.py <strategies> --tools kevin xeeshan --suites portal --cap-check --jobs 10 --state portal --name <name>
```

Full score-only batches:

```powershell
python ROUND5/research/round5_backtester.py <strategies> --tools kevin xeeshan --suites full --jobs 8 --state none --name <name>
```

Mixed finalist validation:

```powershell
python ROUND5/research/round5_backtester.py <strategies> --tools kevin xeeshan --suites portal full --cap-check --jobs 8 --state portal --name <name>
```

Do not use `--full-logs` in high-parallel mode.

Use full JSON logs only for finalist attribution.

## Research Standard

Do not stop after one probe.

Do not accept a tiny gain unless it reveals a mechanism.

Do not exclude high-oracle products after one generic failed signal.

Do not force product variety without edge.

Every high-capacity product needs either:

- a validated engine,
- a conditional/gated role,
- an anchor/signal-only role,
- or a defensible reason it is not currently capturable.

## Ceiling-Gap Outputs

Create:

- `ROUND5/research/outputs/candidate_35_36_ceiling_gap.md`
- `ROUND5/research/outputs/candidate_35_36_oracle_gap_table.csv`
- `ROUND5/research/outputs/candidate_35_36_marginal_engine_table.csv`
- `ROUND5/research/outputs/candidate_35_36_regime_oracle_table.csv`
- `ROUND5/research/outputs/candidate_37_40_blueprint.md`

Stop after the research outputs and candidate 37-40 blueprint unless explicitly told to create candidates.

## Post Ceiling-Gap Requirement

After the ceiling-gap outputs exist, do not immediately build candidates 37-40.

First execute `round5_150k_executable_probe_plan.md` and `worker_prompt_150k_executable_probe_conversion.md`.

Reason:

- oracle/proxy rows identify where money might exist,
- executable probes prove whether a product/engine actually works in the backtester,
- candidate 37-40 should be built from proven add-ons, not from proxy tables alone.

Mandatory executable probe themes:

- PEBBLES undercapture: `PEBBLES_M`, `PEBBLES_XS`, `PEBBLES_L`,
- MICROCHIP/PANEL: `MICROCHIP_SQUARE`, `MICROCHIP_CIRCLE`, `MICROCHIP_TRIANGLE`, `PANEL_2X4`, `PANEL_4X4`,
- ROBOT passive/fill: `ROBOT_DISHES`, `ROBOT_LAUNDRY`, `ROBOT_VACUUMING`,
- SLEEP/UV/SNACKPACK conditional products,
- remaining high-gap/unused GALAXY, OXYGEN, TRANSLATOR products,
- candidate 35 marginal stack probes.

## Candidate 37-40 Blueprint Requirements

The blueprint must specify:

- which candidate targets maximum portal upside,
- which candidate targets robust hidden-final performance,
- which candidate is an information/probe candidate,
- which candidate is the most aggressive 150k attempt,
- base strategy for each candidate,
- engines/products to add,
- engines/products to remove,
- engines/products to gate,
- expected portal target,
- full-history risk,
- validation order.
