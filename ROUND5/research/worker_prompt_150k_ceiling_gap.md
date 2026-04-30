# Worker Prompt: Round 5 Candidate 35/36 Ceiling-Gap Push

Status: this prompt has already been executed.

Do not rerun this proxy/oracle-only phase unless explicitly asked. The active next prompt is:

- `ROUND5/research/worker_prompt_150k_executable_probe_conversion.md`

The ceiling-gap outputs are now a map. The next phase must convert those gaps into executable temporary probes before candidates 37-40 are built.

Proceed to the Round 5 `150k+` ceiling-gap and marginal-edge expansion phase.

Do not start the iterative loop.
Do not create `round5_iterative_*.py`.
Do not blindly mutate candidates.
Do not create candidates 37-40 yet.
Stop after research outputs and the candidate 37-40 blueprint unless explicitly told to build strategies.

## Read First

Read these files before running anything:

- `ROUND5/research/README.md`
- `ROUND5/research/round5_150k_push_plan.md`
- `ROUND5/research/round5_backtester.py`
- `ROUND5/research/round5_backtester_usage.md`
- `ROUND5/research/outputs/candidate_35_36_score_table.md`
- `ROUND5/research/outputs/candidate_35_36_score_table.csv`
- `ROUND5/research/outputs/candidate_35_36_ablation_summary.md`
- `ROUND5/research/outputs/candidate_35_36_design_notes.md`
- `ROUND5/research/outputs/candidate_35_36_recommendation.md`
- `ROUND5/research/outputs/candidate_31_34_reset_review.md`
- `ROUND5/research/outputs/candidate_31_34_current_checkpoint.md`
- `ROUND5/strategies/round5_candidate_35.py`
- `ROUND5/strategies/round5_candidate_36.py`

## Current Truth

Candidate 35 is the current robust development base:

- portal: about `91.9k`
- full: about `287.4k`

Candidate 36 is the current portal-upside branch:

- portal: about `105.5k`
- full: about `36.7k`

Candidate 34 remains the highest historical portal branch:

- portal: about `105.9k`
- full: about `-49.8k`

Candidate 32/33 remain important references:

- candidate 32: `70.7k` portal, `250.2k` full
- candidate 33: `85.9k` portal, `244.7k` full

## Leaderboard Target

The current leaderboard proves there is still major progress available:

- Top 100 cutoff is about `114k`.
- `150k+` is the immediate strong target.
- `200k+` is the stretch target.
- Top entries are `300k-450k`, likely using another major structural/execution edge.

Do not treat `105k` as good enough.

The current goal is to discover the missing `40k-100k` official-window component.

## Main Objective

Understand why candidates 35/36 are not yet near `150k-200k`, then identify what candidate 37-40 should be.

Answer:

- Which products/categories still have large oracle capacity not captured by 35/36?
- Which edge families could capture that capacity?
- Which product-specific engines can be added without damaging full-history robustness?
- Which current engines in 35/36 are crowding out better opportunities?
- Which products should trade more aggressively?
- Which products should be gated, removed, or converted to signal-only?
- What new strategy designs should become candidates 37-40?

## Mandatory Oracle-Like Diagnostics

Run all of these. Add additional diagnostics if the data suggests them.

1. Taker oracle
   - Estimate directional opportunity per product if future mid movement were known.
   - Include realistic spread/top-of-book costs.
   - Identify where crossing can be justified.

2. Passive fill oracle
   - Estimate bid/ask/improved-quote opportunity and forward markout.
   - Include fill feasibility.
   - This is mandatory because leaderboard profiles look like repeated high-confidence fill-quality harvesting.

3. Inventory-constrained oracle
   - Apply `±10` position limits and liquidation assumptions.
   - Rank realistic executable capacity, not fantasy oracle capacity.

4. Residual/fair-value oracle
   - Search synthetic fair-value relationships for all non-PEBBLES categories:
     MICROCHIP, PANEL, SLEEP_POD, TRANSLATOR, GALAXY_SOUNDS, OXYGEN_SHAKE, UV_VISOR, SNACKPACK, ROBOT.
   - Find online-computable category formulas, pair residuals, anchors, baskets, and curves.

5. Regime oracle
   - Split edge by spread, volatility, depth, imbalance, trend/reversal state, category state, and timestamp block.
   - Do not hardcode exact timestamps.
   - Find conditional engines that can upgrade weak products.

6. Marginal-addition oracle
   - Treat candidates 35/36 as current portfolios.
   - Find which products/engines add PnL versus interfere.
   - Detect ranking/capacity crowd-out.
   - This is the most important diagnostic.

7. Engine-family search
   - For meaningful oracle gaps, test:
     momentum, reversal, breakout, rolling mean reversion, category median reversion, synthetic FV residual, pair residual, passive MM, taker trigger, imbalance/microprice, volatility/spread/depth gated versions, and multi-engine hybrids.

## Use The Harness Aggressively

Use `ROUND5/research/round5_backtester.py`.

Portal-heavy probes:

```powershell
python ROUND5/research/round5_backtester.py <strategy_files> --tools kevin xeeshan --suites portal --cap-check --jobs 10 --state portal --name <experiment_name>
```

Full score-only validation:

```powershell
python ROUND5/research/round5_backtester.py <strategy_files> --tools kevin xeeshan --suites full --jobs 8 --state none --name <experiment_name>
```

Mixed finalist validation:

```powershell
python ROUND5/research/round5_backtester.py <strategy_files> --tools kevin xeeshan --suites portal full --cap-check --jobs 8 --state portal --name <experiment_name>
```

Avoid `--full-logs` in high-parallel mode.

Use full JSON logs only for one finalist if attribution requires it.

## Standards

Be aggressive.

Do not stop after a shallow oracle.
Do not stop after the first probe.
Do not accept `+2k` unless it reveals a reusable mechanism.
Do not exclude high-oracle products after one generic failed test.
Do not trade products just for variety.
Do not optimize only for day-4/portal if full-history collapses.
Do not use timestamp hardcoding, future leakage, local file reads, unsupported imports, or official-log parsing inside strategies.

Every high-capacity product must end with one of:

- validated engine,
- conditional/gated engine,
- anchor/signal-only role,
- not-currently-capturable with a specific reason.

## Required Outputs

Create:

- `ROUND5/research/outputs/candidate_35_36_ceiling_gap.md`
- `ROUND5/research/outputs/candidate_35_36_oracle_gap_table.csv`
- `ROUND5/research/outputs/candidate_35_36_marginal_engine_table.csv`
- `ROUND5/research/outputs/candidate_35_36_regime_oracle_table.csv`
- `ROUND5/research/outputs/candidate_37_40_blueprint.md`

The final blueprint must specify:

- what candidates 37-40 should be,
- which base each should use,
- what engines/products should be added,
- what engines/products should be removed,
- what engines/products should be gated,
- which candidate targets max portal upside,
- which candidate targets robust hidden-final performance,
- which candidate is an information/probe candidate,
- which candidate is the most aggressive `150k+` attempt,
- what score target validates each.

Final report should answer:

1. What uncaptured PnL sources were found.
2. What oracle diagnostics mattered most.
3. Which product/category has the best chance to add `40k+`.
4. Whether `150k` appears reachable with candidate 37-40.
5. Whether `200k` likely requires a new structural edge.
6. The exact candidate 37-40 plan.
