# Round 4 Fast Iteration Loop

## Objective

Maximize official Round 4 profit as fast as possible.

This is not a documentation project and not a production-engineering project. The loop should produce insight, code, backtests, portal candidates, and better profit. Documentation only exists to keep the current thesis, red flags, and next experiments clear.

Full rewrites are allowed when they are high ROI, but they are not the goal. Incremental changes are allowed when they create real edge or fix a proven leak. The goal is profit.

## Working Style

- Move fast: research, implement, backtest, decide.
- Treat this as an empirical trading-research loop, not a code-generation loop.
- Do not create extra `.md` files unless they replace hours of confusion.
- Keep the active thinking in this file or in generated run summaries.
- Prefer small, decisive experiments over polished writeups.
- If an experiment works, keep it and build on it.
- If it does not work, archive it or delete it.
- Do not perfect every detail before testing.
- Do not turn every observation into a new document.
- Do not over-trust local backtests when portal evidence disagrees.
- Do use gut/market structure when the backtester is clearly giving false-positive rankings.
- Do not make multiple unrelated strategy changes in one candidate unless it is explicitly a bundle test after the individual legs have been measured.
- Do not confuse "higher number" with "better strategy" until product attribution, fill behavior, and overfit risk are checked.

## Round 3 Lessons To Preserve

The Round 3 loop worked because it was strict, not because it was complicated. Preserve these mechanics:

- Keep a clean active strategy and generate temporary variants outside the active file.
- Change one thesis at a time unless testing a named bundle of already-validated legs.
- Validate with Kevin and Xeeshan before promotion.
- Use Rust only when final confidence matters and time permits; it is not part of fast loops.
- Use official/window feedback as evidence, but distinguish test-window fit from final hidden/full-fit robustness.
- Reject generated variants if the generator touched unintended constants, maps, products, or timestamp logic.
- Never promote a result from a broken sweep, even if the number is attractive.
- Prefer product-level and timestamp-block attribution over aggregate PnL when deciding why a candidate worked.
- Keep anti-overfit checks explicit: no replay tables, no official-log sequence matching, no fragile exact-window exits unless justified by market structure.
- Stop polishing weak ideas. Move to the next hypothesis once the evidence is clear.

## Required Inputs

Use these actively:

- `algo_guide.md`: platform mechanics and constraints.
- Round 4 prompt: Mark counterparties, live TTE, product limits.
- `522830.py` / current candidate code: starting point, not sacred.
- Official portal logs/results: highest-priority evidence.
- Local backtesters: fast filters, not final truth.

Important mechanics from `algo_guide.md` that we should exploit harder:

- `market_trades`: Mark buyer/seller IDs, bursts, product-specific behavior, cross-product signals.
- `own_trades`: passive fills, fill quality, adverse selection, whether bots take our quotes.
- `traderData`: compact state machine, product inventory age, recent fill quality, Mark memory.
- Passive orders: bots may trade against our resting quote before it is cancelled.
- Instant execution: if visible book liquidity is mispriced, we can take it immediately.
- Position limits: use full risk budget only where it earns profit.
- Full order book: spread, depth, imbalance, liquidity cliffs, not just best bid/ask.

## Source Of Truth And Freshness

Before each serious iteration block, refresh the state so the loop does not optimize stale candidates.

Required checks:

- List `ROUND4/strategies` and identify the current best candidate file.
- List `ROUND4/official_submissions` and extract any new official scores/logs.
- Read the latest generated summaries under `ROUND4/research/outputs/strategy_runs`.
- Update the active candidate table in this file if new candidates or official scores exist.
- If the candidate table is stale, do not use it for final decisions until refreshed.

Current known freshness issue:

- This plan lists candidates 1, 4, 6, 7, and 8, but `ROUND4/strategies` also contains candidates 9, 10, 11, and 12. The table must be refreshed before final selection.

## File Discipline

Use this layout consistently:

- Promotable strategies: `ROUND4/strategies`.
- Temporary generated variants: `ROUND4/research/strategy_experiments` or `ROUND4/research/outputs/strategy_runs`.
- Analysis scripts: `ROUND4/research`.
- Official bundles/logs: `ROUND4/official_submissions`.

Rules:

- Do not edit official submission files in place.
- Do not overwrite a known-good candidate without saving or being able to reconstruct the old one.
- Do not patch the active candidate until the variant has passed the promotion gate.
- If using regex or code generation, verify the diff before trusting the backtest. Round 3 had invalid sweeps from accidental constant edits; prevent that here.
- Keep strategy filenames descriptive enough to encode the hypothesis, not just `test.py`.

## Current Red Flags

These should steer experiments until fixed or disproven.

| Red flag | Evidence | Why it matters |
|---|---|---|
| Post-40k plateau | Algo reaches about 70k near 40k-41k, then mostly stalls. | Opening edge is harvested, then strategy stops creating enough new PnL. |
| Dead inventory | After 40k, baseline makes zero trades in `VEV_4000`, `VEV_5200`, `VEV_5300`, `VEV_5400`, `VEV_5500`. | Static inventory is marking to market instead of being actively managed. |
| Hydrogel broken | Our Hydrogel is about +232 official while another known result got about +2500. | We are missing a real product edge or should cut the product. |
| Backtester false positives | Candidate 2/3 ranked well locally but underperformed official. | Do not optimize blindly to local window scores. |
| `VEV_4000` sizing leak | Baseline ended -300 and made about 9,382; candidates ended -247 and made about 7,845. | Low-strike short sizing matters and must not be accidentally weakened. |
| Candidate 2/3 identical official fills | Hydrogel Mark toggles were not validated by portal. | Some local differences may not survive official execution. |

## Fast Workflow

1. Pick one high-ROI question.
2. Run the smallest research needed to answer it.
3. Implement one candidate or one controlled variant.
4. Backtest with the standard table.
5. Run product attribution and at least one fill/inventory sanity check.
6. Decide immediately: promote, mutate, archive, or delete.
7. Only write the conclusion if it changes what we test next.

Standard table format:

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |
|---|---:|---:|---:|---:|---:|
| `522830.py` | 363,494 | 364,966 | 76,040 | 76,040 | 75,988.86 |

Required extended table for serious candidates:

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official | Products Changed | Thesis | Verdict |
|---|---:|---:|---:|---:|---:|---|---|---|
| `candidate.py` | 0 | 0 | 0 | 0 | pending | `HYDROGEL_PACK` | example | promote/mutate/archive |

For product attribution, include at minimum:

| Strategy | Hydrogel | VFE | VEV4000 | VEV4500 | VEV5000 | VEV5100 | VEV5200 | VEV5300 | VEV5400 | VEV5500 | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|

For time-block attribution, include:

| Strategy | 0-20k | 20k-40k | 40k-60k | 60k-80k | 80k-end | Notes |
|---|---:|---:|---:|---:|---:|---|

The time-block table is mandatory for any change claiming to fix the post-40k plateau.

## Standard Validation Commands

Use the project wrappers when possible.

Full backtests:

```powershell
.\scripts\bt-kevin.ps1 round4 -Strategy ROUND4\strategies\candidate.py
.\scripts\bt-xeeshan.ps1 round4 -Strategy ROUND4\strategies\candidate.py
```

Window/official-like backtests:

```powershell
.\scripts\bt-portal-window.ps1 -Strategy ROUND4\strategies\candidate.py -Tool both -Label round4_candidate_window
```

If the Round 4 window wrapper or extracted official window is not available, create or refresh it before relying on window scores. Do not manually compare inconsistent windows.

Batch candidate scoring:

```powershell
python ROUND4\research\score_round4_candidates.py
```

Use scripts in `ROUND4\research` for attribution and official-log analysis:

```powershell
python ROUND4\research\compare_official_submissions.py
python ROUND4\research\analyze_official_plateau.py
python ROUND4\research\analyze_post40_mark_inventory.py
python ROUND4\research\round4_diagnostics.py
```

If a command fails or produces incomplete logs, treat the result as invalid until rerun cleanly.

## Promotion Gate

A candidate can be promoted only if it passes these checks.

Mandatory:

- It has a clear thesis before testing.
- It changes one identifiable product/engine, or it is a named bundle of already-measured legs.
- Full Kevin and Full Xeeshan both improve, or the candidate has a strong official/window reason and the full-data loss is explicitly accepted.
- Product attribution explains the aggregate gain.
- Inventory paths are valid and do not rely on accidental unliquidated exposure unless that exposure is the intentional economic thesis.
- The candidate does not weaken a known critical leg, especially `VEV_4000` short sizing, without compensating evidence.
- No accidental generator damage: verify product lists, strike maps, sigmas, edge maps, size maps, and timestamp constants.
- No platform-risk changes: no file I/O, no imports unavailable on platform, no excessive logs, no runtime-heavy logic.

Default numeric gates:

- For routine promotion: at least `+1000` on both Full Kevin and Full Xeeshan, or at least `+500` official/window with no full-data regression.
- For high-risk structural changes: at least `+3000` on both Full Kevin and Full Xeeshan, plus product attribution that makes economic sense.
- For portal/window-only promotion: official/window result must be large enough to justify final-hidden risk, and the overfit analysis must be explicit.
- For tiny fixes below `+500`: only promote if it removes risk, fixes an obvious leak, or enables a larger follow-up experiment.

Reject or archive if:

- It helps only one simulator.
- It improves aggregate PnL by shifting losses into an untrusted mark-to-market artifact.
- It only works on one narrow timestamp window without a structural explanation.
- It changes many products and the attribution cannot explain which leg worked.
- It worsens the current biggest red flag, such as the post-40k plateau, while improving an early block.

## Anti-Overfit And Hardcoding Rules

Allowed:

- Time regimes tied to observed market structure, such as post-repricing behavior after an opening adjustment, if validated across more than one day/window.
- Product-specific parameters derived from stable roles, e.g. low-strike static short vs active middle-strike engine.
- Mark-specific behavior when the Mark identity has measured predictive value out of sample or across comparable windows.
- Inventory aging and risk decay when product attribution shows stale inventory gives back.

Risky but sometimes acceptable:

- Timestamp thresholds around observed regime changes like 38k-42k. These require time-block attribution and at least one robustness check with nearby thresholds.
- Official-window tuned exits. These must be labeled as portal-window candidates, not final-hidden candidates, unless the market-structure thesis is strong.

Not allowed:

- Replay tables keyed by exact timestamp and product.
- Logic keyed to official submission IDs, exact log sequences, or exact historical trade order.
- Exact-window exits with no market-structure explanation.
- Any code that reads local files, writes files, or depends on research artifacts at runtime.
- Blind constants copied from official logs without a product-level thesis.

For every candidate, explicitly answer:

- Is this structural or window-specific?
- Which product earns the gain?
- Which inventory/risk exposure changed?
- Does the same idea survive nearby parameter values?
- Would this still make sense on a hidden full simulation?

## Priority Order

### 1. Hydrogel Rebuild Or Cut

Hydrogel is the clearest underperformer. Do not just nudge thresholds.

Fast experiments:

- Pure market maker with wider/narrower passive quotes.
- Mark-follow Hydrogel using only strongest Mark signals.
- Mark-fade Hydrogel using bad Marks.
- Trend/momentum Hydrogel from recent mid moves and order-book pressure.
- Mean-reversion Hydrogel around local fair.
- Passive-fill learner using `own_trades` markouts.
- No-Hydrogel control.
- Aggressive Hydrogel inventory use up to the limit when signal is strong.

Decision:

- If we can get Hydrogel above roughly +1500 local/official proxy without hurting other products, keep rebuilding.
- If repeated focused tests fail, cut or minimize Hydrogel and spend time elsewhere.
- Do not accept Hydrogel changes that only improve early marks while increasing post-40k giveback.
- Hydrogel candidates must include passive fill quality or Mark signal attribution if they use passive quotes or Mark logic.

### 2. Post-40k Plateau Engine

The current algo captures early repricing, then sits. Build a second-phase regime.

Fast experiments:

- Hard regime switch after 38k-42k.
- Reallocate risk from dead static vouchers into active `VEV_5000`/`VEV_5100`.
- Allow re-entry after stale inventory exits.
- Late-session Mark-only entries.
- Late-session passive quote probing on active strikes.
- Time-based inventory decay only for products proven to give back.
- Keep `VEV_4000` short sizing intact unless evidence says otherwise.

Decision:

- A plateau fix must create new post-40k PnL, not only trim giveback.
- Run the time-block table for every plateau candidate.
- Test nearby thresholds around any proposed switch point, e.g. 38k, 40k, 42k, before calling it robust.
- If a plateau candidate reduces early PnL but creates later PnL, compare total and risk-adjusted inventory behavior before rejecting it.

### 3. Mark Mechanics

Round 4's new mechanic is Mark identity. Use it as more than a small fair-value bump.

Fast experiments:

- Mark leaderboard by product and horizon.
- Mark pair model: buyer/seller pair may matter more than one side alone.
- Mark burst model: first trade, repeated trade, exhaustion.
- Mark conditional on spread/depth/time/inventory.
- Cross-product Mark signal: VFE Mark flow predicting vouchers, voucher flow predicting VFE.
- Mark-based no-trade filter when base model is contradicted.
- Mark-specific passive quote baiting.
- Mark-informed stale inventory exits, but only if it beats naive exits.

Decision:

- If direct Mark crossing loses, do not keep forcing it.
- Try Mark as filter, sizing input, passive-quote trigger, and regime trigger.
- Mark models must be evaluated by Mark identity, product, side, and horizon.
- A Mark signal is not real until it improves either fill quality, directional markout, or inventory exit timing.

### 4. Voucher Product Roles

Stop treating every voucher as the same trade.

Known roles so far:

- `VEV_4000`: low-strike static short; preserve max short unless strong evidence changes it.
- `VEV_4500`: likely static short contributor.
- `VEV_5000` / `VEV_5100`: active late-session PnL engines.
- `VEV_5200` / `VEV_5300`: stale post-40k shorts; possible exit/re-entry candidates.
- `VEV_5400` / `VEV_5500`: low contribution; test whether they deserve risk.
- `VEV_6000` / `VEV_6500`: likely ignore unless Mark/liquidity says otherwise.

Fast experiments:

- Per-strike thresholds, sizes, and time regimes.
- Different exit rules per strike.
- Re-entry rules for `VEV_5200`/`VEV_5300`.
- Active middle-strike engine independent of static low-strike book.
- Delta/residual model: separate underlying direction from option mispricing.

Voucher promotion checks:

- Preserve `VEV_4000` and `VEV_4500` roles unless the candidate explicitly tests those roles.
- For `VEV_5000` and `VEV_5100`, report active fills and post-40k PnL separately.
- For `VEV_5200` and `VEV_5300`, report stale-inventory giveback and re-entry quality.
- For `VEV_5400` and `VEV_5500`, require evidence that they earn their risk budget.

### 5. VFE Anchor And Option Surface

VFE and vouchers are linked. If the fair model is stale after 40k, all decisions degrade.

Fast experiments:

- Refit VFE anchor by time regime.
- Use only reliable strikes to imply VFE.
- Use Mark flow to adjust VFE fair.
- Check whether `VEV_5000`/`VEV_5100` late PnL is underlying direction, vol/surface, or execution.

Surface promotion checks:

- Check whether gains come from better VFE fair, better option residual, or just larger directional exposure.
- Compare market VFE mid, implied VFE from low strikes, and final fair used by the strategy.
- Do not change option surface and execution sizing in the same first-pass candidate.

## Candidate Handling

Keep actual testable candidates in `ROUND4/strategies`.

Keep rejected or diagnostic one-offs in `ROUND4/research/strategy_experiments`.

Do not promote a candidate just because it has a nice local number. Promote it when the product attribution makes sense and it has a plausible path to official improvement.

Candidate states:

- `baseline`: preserved reference strategy.
- `probe`: temporary candidate for learning; not intended to submit.
- `diagnostic`: deliberately isolates one product or one mechanic.
- `promotable`: passed Kevin/Xeeshan plus attribution gates.
- `portal-only`: useful for official-window scoring but not trusted for final hidden scoring.
- `rejected`: failed validation or lacks thesis.

Every candidate should have one of those states in the run summary.

Current active candidates:

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |
|---|---:|---:|---:|---:|---:|
| `round4_candidate_1_522830_base.py` | 363,494 | 364,966 | 76,040 | 76,040 | 75,988.86 |
| `round4_candidate_4_vev4000_repair_mid9_hydrofairoff.py` | 377,844 | 379,622 | 76,936 | 76,936 | pending |
| `round4_candidate_6_hydro_more_mid9.py` | 382,820 | 384,080 | 76,660 | 76,660 | pending |
| `round4_candidate_7_exit_5200_5300_86600.py` | 379,184 | 380,962 | 77,938 | 77,938 | pending |
| `round4_candidate_8_late_mark_passive_cover.py` | 378,784 | 380,720 | 76,930 | 76,930 | pending |

Known candidate-table freshness issue:

- `ROUND4/strategies` also contains `round4_candidate_9_vfe71900_5000_harvest.py`, `round4_candidate_10_vfe71900_harvest_only.py`, `round4_candidate_11_5000_harvest_only.py`, and `round4_candidate_12_markhydro_vfe5000_harvest_probe.py`. Refresh this table before using it for final decisions.

Interpretation:

- Candidate 4 is the clean repair/control.
- Candidate 6 is a Hydrogel-capacity diagnostic, not a solved Hydrogel strategy.
- Candidate 7 is giveback control, not a true plateau fix.
- Candidate 8 is a safe Mark/passive diagnostic, not a max-profit thesis.

## Decision Rules

- Official result beats everything.
- If official and local disagree, investigate the exact fills, product attribution, and whether the official score is test-window feedback or final-hidden evidence.
- If a product is not earning its risk budget, rebuild it or cut it.
- If a change only adds a few hundred and has no thesis, deprioritize it.
- If a change can unlock thousands, test it even if it requires messy code.
- If an experiment is obviously bad, stop polishing it.
- If a result is surprising, run one quick confirmation, then move.
- If two candidates are close, choose the one with lower overfit risk, simpler mechanics, and cleaner product attribution.
- If a candidate wins portal/window but loses full robustness, label it portal-only unless final scoring is confirmed to match the window.
- If a candidate wins full robustness but loses portal/window, keep it alive for hidden/full final scoring.
- When time is short, stop sweeping and run final Kevin/Xeeshan plus official/window on the best current file.

## What Not To Do

- Do not create a new markdown file for every thought.
- Do not spend time making research artifacts pretty.
- Do not keep tuning a dead idea because it is already implemented.
- Do not call full rewrites the goal. They are a tool.
- Do not ignore small fixes if they have clear ROI.
- Do not assume the current architecture is correct.
- Do not assume the current architecture is wrong without testing.
- Do not promote from an interrupted run.
- Do not promote from a sweep whose generated files were not diff-checked.
- Do not let a portal-window score seduce us into final-hidden overfit.
- Do not hide losing products inside aggregate score.
- Do not keep stale candidate tables.

## Next Attack

Start with Hydrogel and post-40k plateau because they are the biggest visible leaks.

Immediate experiments:

1. Hydrogel pure MM / Mark-follow / Mark-fade / no-Hydrogel controls.
2. Post-40k `VEV_5000`/`VEV_5100` active engine variants.
3. `VEV_5200`/`VEV_5300` exit plus re-entry variants.
4. Mark filter and passive quote tests, not only direct stale-inventory crossing.
5. Product attribution after every candidate.

## Final Selection Checklist

Before submission, produce one final table:

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official Best Seen | Overfit Risk | Submit? |
|---|---:|---:|---:|---:|---:|---|---|

Then answer:

- Which file exactly should be submitted?
- Is it current and saved under `ROUND4/strategies`?
- Did it pass Kevin and Xeeshan cleanly?
- Is Rust needed or skipped for speed?
- Does the candidate rely on portal-window timing?
- What are the top three product PnL contributors?
- What is the biggest known risk?
- If official final is hidden/full, is this still the best candidate?

If time is under 10 minutes:

- Stop exploratory sweeps.
- Kill stale background runs.
- Run Kevin, Xeeshan, and official/window for the current best only.
- Do not make unvalidated edits after the final validation.
- Submit the validated file, not a nearby untested variant.
