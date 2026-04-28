# Round 4 Fast Iteration Loop

## Objective

Maximize official Round 4 profit as fast as possible.

This is not a documentation project and not a production-engineering project. The loop should produce insight, code, backtests, portal candidates, and better profit. Documentation only exists to keep the current thesis, red flags, and next experiments clear.

Full rewrites are allowed when they are high ROI, but they are not the goal. Incremental changes are allowed when they create real edge or fix a proven leak. The goal is profit.

## Working Style

- Move fast: research, implement, backtest, decide.
- Do not create extra `.md` files unless they replace hours of confusion.
- Keep the active thinking in this file or in generated run summaries.
- Prefer small, decisive experiments over polished writeups.
- If an experiment works, keep it and build on it.
- If it does not work, archive it or delete it.
- Do not perfect every detail before testing.
- Do not turn every observation into a new document.
- Do not over-trust local backtests when portal evidence disagrees.
- Do use gut/market structure when the backtester is clearly giving false-positive rankings.

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
5. Decide immediately: promote, mutate, archive, or delete.
6. Only write the conclusion if it changes what we test next.

Standard table format:

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |
|---|---:|---:|---:|---:|---:|
| `522830.py` | 363,494 | 364,966 | 76,040 | 76,040 | 75,988.86 |

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

### 5. VFE Anchor And Option Surface

VFE and vouchers are linked. If the fair model is stale after 40k, all decisions degrade.

Fast experiments:

- Refit VFE anchor by time regime.
- Use only reliable strikes to imply VFE.
- Use Mark flow to adjust VFE fair.
- Check whether `VEV_5000`/`VEV_5100` late PnL is underlying direction, vol/surface, or execution.

## Candidate Handling

Keep actual testable candidates in `ROUND4/strategies`.

Keep rejected or diagnostic one-offs in `ROUND4/research/strategy_experiments`.

Do not promote a candidate just because it has a nice local number. Promote it when the product attribution makes sense and it has a plausible path to official improvement.

Current active candidates:

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |
|---|---:|---:|---:|---:|---:|
| `round4_candidate_1_522830_base.py` | 363,494 | 364,966 | 76,040 | 76,040 | 75,988.86 |
| `round4_candidate_4_vev4000_repair_mid9_hydrofairoff.py` | 377,844 | 379,622 | 76,936 | 76,936 | pending |
| `round4_candidate_6_hydro_more_mid9.py` | 382,820 | 384,080 | 76,660 | 76,660 | pending |
| `round4_candidate_7_exit_5200_5300_86600.py` | 379,184 | 380,962 | 77,938 | 77,938 | pending |
| `round4_candidate_8_late_mark_passive_cover.py` | 378,784 | 380,720 | 76,930 | 76,930 | pending |

Interpretation:

- Candidate 4 is the clean repair/control.
- Candidate 6 is a Hydrogel-capacity diagnostic, not a solved Hydrogel strategy.
- Candidate 7 is giveback control, not a true plateau fix.
- Candidate 8 is a safe Mark/passive diagnostic, not a max-profit thesis.

## Decision Rules

- Official result beats everything.
- If official and local disagree, investigate the exact fills and product attribution.
- If a product is not earning its risk budget, rebuild it or cut it.
- If a change only adds a few hundred and has no thesis, deprioritize it.
- If a change can unlock thousands, test it even if it requires messy code.
- If an experiment is obviously bad, stop polishing it.
- If a result is surprising, run one quick confirmation, then move.

## What Not To Do

- Do not create a new markdown file for every thought.
- Do not spend time making research artifacts pretty.
- Do not keep tuning a dead idea because it is already implemented.
- Do not call full rewrites the goal. They are a tool.
- Do not ignore small fixes if they have clear ROI.
- Do not assume the current architecture is correct.
- Do not assume the current architecture is wrong without testing.

## Next Attack

Start with Hydrogel and post-40k plateau because they are the biggest visible leaks.

Immediate experiments:

1. Hydrogel pure MM / Mark-follow / Mark-fade / no-Hydrogel controls.
2. Post-40k `VEV_5000`/`VEV_5100` active engine variants.
3. `VEV_5200`/`VEV_5300` exit plus re-entry variants.
4. Mark filter and passive quote tests, not only direct stale-inventory crossing.
5. Product attribution after every candidate.
