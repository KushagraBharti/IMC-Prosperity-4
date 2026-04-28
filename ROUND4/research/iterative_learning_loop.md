# Round 4 Iterative Learning Loop

## Goal

Build a repeatable Round 4 research and strategy-improvement loop that starts from the proven Round 3 architecture, adapts it to the Round 4 time-to-expiry and counterparty-ID setting, and produces submission candidates with clear evidence.

Round 4 is not a restart. It is a Round 3 continuation with one major new information source:

- The traded products are the same Round 3 product family.
- The position limits are unchanged.
- Voucher time to expiry changes for the live round.
- Historical trades now expose named counterparties in `buyer` and `seller`.
- The manual challenge is separate and must be handled as a static derivatives portfolio problem.

The loop has two connected workstreams:

- Algorithmic: VFE, Hydrogel, and VEV strategy research with Mark counterparty signals.
- Manual: Aether Crystal portfolio valuation, risk analysis, and final order selection.

The final output should be more than a high backtest number. It should explain where the PnL comes from, which risks are being accepted, why a candidate should survive the portal better than a simulator-specific overfit, and what evidence supports the final submission.

## Starting Facts

Local Round 4 data capsule currently contains:

| File type | Count | Shape |
|---|---:|---|
| Price files | 3 | `prices_round_4_day_1.csv` through `prices_round_4_day_3.csv` |
| Trade files | 3 | `trades_round_4_day_1.csv` through `trades_round_4_day_3.csv` |
| Price rows | 360,000 | 120,000 rows per day, including header |
| Trade rows | 4,281 | Across all three days |
| Products | 12 | Hydrogel, VFE, and 10 VEV vouchers |
| Named Marks | 7 | `Mark 01`, `Mark 14`, `Mark 22`, `Mark 38`, `Mark 49`, `Mark 55`, `Mark 67` |

Product universe:

- `HYDROGEL_PACK`
- `VELVETFRUIT_EXTRACT`
- `VEV_4000`
- `VEV_4500`
- `VEV_5000`
- `VEV_5100`
- `VEV_5200`
- `VEV_5300`
- `VEV_5400`
- `VEV_5500`
- `VEV_6000`
- `VEV_6500`

Position limits:

| Product family | Limit |
|---|---:|
| `HYDROGEL_PACK` | 200 |
| `VELVETFRUIT_EXTRACT` | 200 |
| Each VEV voucher | 300 |

Important TTE facts:

- Historical Round 4 data says VEVs have TTE 7 Solvenarian days starting on day 1.
- That implies historical day 1, day 2, and day 3 should usually be modeled as roughly 7, 6, and 5 days remaining, decaying intraday.
- The live Round 4 prompt states `VEV_5000` has TTE 4 days.
- Live submission code should therefore use a live starting TTE of 4 days unless later portal evidence proves a different convention.

## Core Rule

All actual submission-strategy edits must stay in explicit Round 4 strategy branches.

Research files may generate diagnostics, tables, plots, temporary variants, and experiment outputs. They should not quietly become the submitted algorithm.

Recommended branch files:

| Branch | File | Starting point | Purpose |
|---|---|---|---|
| R4 522830 Baseline | `ROUND4/strategies/round4_522830_base.py` | Existing `522830.py` | Known strong official-tested baseline |
| R4 Base | `ROUND4/strategies/round4_base_r3_port.py` | Final Round 3 strategy or `522830.py`, depending on code comparison | Clean non-Mark baseline with Round 4 TTE calibration |
| R4 Mark Conservative | `ROUND4/strategies/round4_mark_conservative.py` | R4 Base or R4 522830 Baseline | Add only high-confidence Mark alpha with shrinkage and caps |
| R4 Mark Aggressive | `ROUND4/strategies/round4_mark_aggressive.py` | R4 Mark Conservative | Probe stronger Mark sizing, thresholds, and product-specific effects |
| R4 Current | `ROUND4/strategies/current_trader.py` | Best validated branch | Final active candidate only after evidence review |

Do not edit `current_trader.py` first. Promote into it after the branch has evidence.

## Evidence Hierarchy

Use evidence in this order:

1. Official portal result, if available.
2. Official bundle replay on extracted portal window, if available.
3. Agreement across local replay engines on full Round 4 data.
4. Agreement across day-held-out validation splits.
5. Product-level and fill-level diagnostics.
6. Raw total PnL from one local backtester.

The last item is useful, but it is never enough by itself.

## Pre-Loop Mini Workflow

Before starting the full multi-hour iterative loop, run a focused high-ROI discovery pass. The goal is to produce three serious algorithms for portal testing, not to immediately converge on one final strategy.

### Step 1: Learn and Run Many Mini Experiments

First, learn aggressively from the Round 4 data. Run as many small experiments as needed, prioritizing the highest expected information gain.

High-ROI experiments come first:

- TTE calibration.
- Round 3 baseline port.
- Mark counterparty scoring.
- Aggressor-aware Mark scoring.
- VFE Mark follow/fade tests.
- Hydrogel Mark pair tests.
- Voucher strike ablations.
- Delta-adjusted voucher residual tests.
- Manual Aether risk simulations.

Do not start by building a large complicated algorithm. The first job is to map the opportunity surface.

### Step 2: Build Three Algorithms

After the mini experiments, create exactly three portal candidates:

| Candidate | Source | Purpose |
|---|---|---|
| Algorithm 1 | Existing `522830.py` | Strong known baseline, cleaned or lightly improved only where evidence is obvious |
| Algorithm 2 | New idea branch | Conservative Mark-aware strategy with robust follow/fade logic |
| Algorithm 3 | New idea branch | Different strategic thesis, such as options-residual/strike-selection or Hydrogel/VFE regime specialization |

Then report all three to the user before the full loop begins. Each report must include:

- Strategy file path.
- Short thesis.
- Key changes.
- Risk profile.
- Product-level attribution.
- Backtest table in the required format.
- Known weaknesses.
- Why it deserves portal testing.

### Step 3: User Runs Portal

The user will run the three algorithms on the official portal.

After portal runs are complete, the user will put the official data bundles into:

```text
ROUND4/official_submissions/
```

Do not continue into the full iterative loop until the portal bundles are available, unless the user explicitly asks for more local-only research first.

### Step 4: Full Iterative Learning Loop

Once the official bundles are available, start the full iterative learning loop. This phase should be deep and persistent:

- Extract portal windows.
- Compare official versus local behavior.
- Diagnose first divergences.
- Iterate for hours if needed.
- Preserve accepted and rejected changes.
- Keep portal alignment as the main target.

The full loop starts after the three-candidate portal feedback, not before.

## Required Backtest Table Format

Every candidate summary must use this table format:

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |
|---|---:|---:|---:|---:|---:|
| `522830.py` | 363,494 | 364,966 | 76,040 | 76,040 | 75,988.86 |

Rules:

- Keep column names exactly as shown.
- Use comma-separated integer formatting for local backtests.
- Use official precision as reported by the portal.
- If official has not been run yet, write `pending`.
- If a local engine failed, write `failed` and explain below the table.
- Add product-level tables separately; do not alter this headline table.

Current known baseline:

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |
|---|---:|---:|---:|---:|---:|
| `522830.py` | 363,494 | 364,966 | 76,040 | 76,040 | 75,988.86 |

This is the benchmark every new Round 4 algorithm must beat or justify failing to beat.

## External Research Anchors

The Round 4 research should borrow ideas from market microstructure and option pricing, but only when they can be tested on the actual Prosperity data.

Relevant concepts:

- Trade direction classification: buyer/seller identity is useful, but it is not always the same as aggressor side. Compare trade price to the prevailing bid/mid/ask.
- Kyle lambda: estimate price impact per unit of signed Mark flow.
- Order-flow toxicity and VPIN: useful as inspiration for volume-bucket imbalance, but must beat simpler signed-flow metrics before entering strategy code.
- Prior Prosperity informed-trader patterns: named trader IDs can be stored in `traderData` as recent buy/sell timestamps or decayed alpha.
- Chooser, binary, and discrete barrier option pricing: useful for manual Aether only, not algorithmic VEV trading.

Reference links:

| Topic | Link |
|---|---|
| Prosperity 4 official site | `https://prosperity.imc.com/` |
| Prosperity visualizer data format | `https://imc-prosperity-visualizer.vercel.app/` |
| Xeeshan backtester matching note | `https://pypi.org/project/prosperity4btx/2.1.1/` |
| Prior Prosperity informed-trader implementation pattern | `https://github.com/TimoDiehm/imc-prosperity-3/blob/main/FrankfurtHedgehogs_polished.py` |
| Lee/Ready trade-direction paper summary | `https://ideas.repec.org/a/bla/jfinan/v46y1991i2p733-46.html` |
| Kyle lambda / informed trading model | `https://people.stern.nyu.edu/lpederse/courses/LAP/papers/Information%2CFundamental/Kyle85.pdf` |
| VPIN critique and benchmark warning | `https://www.sciencedirect.com/science/article/pii/S1386418113000189` |
| Chooser option pricing | `https://ryanoconnellfinance.com/chooser-options/` |
| Binary option valuation | `https://deripricing.gitbook.io/binary-option-valuation` |
| Discrete barrier option methods | `https://www.sciencedirect.com/science/article/pii/S0377042714003793` |

## Round 4 Data Splits

Round 4 has three historical days. The loop should avoid training every parameter on all days and then declaring victory.

Use these splits:

| Split | Train | Validate | Purpose |
|---|---|---|---|
| A | Day 1 and Day 2 | Day 3 | Main out-of-sample validation |
| B | Day 1 and Day 3 | Day 2 | Regime robustness check |
| C | Day 2 and Day 3 | Day 1 | Early-day robustness check |
| Full | Day 1, Day 2, Day 3 | None | Final full-data diagnostic only |

For Mark analysis, a signal is not trusted unless it is at least directionally coherent across two validation views or has a strong economic explanation.

## Iteration Cadence

Every iteration should produce a small evidence packet:

- Strategy file and commit/diff label.
- Parameter changes.
- Hypothesis being tested.
- Full-data local results.
- Day-split results.
- Product-level PnL.
- Inventory summary.
- Fill count and fill quality.
- Mark exposure summary.
- Why the result should generalize.
- Decision: accept, reject, hold for portal test, or archive.

An iteration should change exactly one concept at a time. A concept may include multiple code lines if they are one idea, for example:

- "Change live TTE from 5 to 4."
- "Add conservative VFE Mark alpha."
- "Drop `VEV_5500` again."
- "Raise `VEV_5000` edge threshold."
- "Make Hydrogel flattening more aggressive after inventory 130."

Avoid bundled changes such as:

- "Add Mark alpha, change option vols, change sizes, and modify Hydrogel quoting."

That kind of bundle cannot be interpreted.

## Phase 0: Reconstruct Round 3 Baseline

Purpose:

Make sure the Round 3 final strategy can be ported and run on Round 4 data before introducing Mark logic.

Tasks:

1. Copy the final Round 3 strategy into `round4_base_r3_port.py`.
2. Rename products only if necessary. The local Round 4 files still use `VEV_*`, so no product rename should be needed unless the portal datamodel differs.
3. Preserve `OrderBuilder`.
4. Preserve the dynamic Hydrogel fair.
5. Preserve the VFE fair based on anchor plus deep-voucher-implied values.
6. Preserve selective voucher trading.
7. Disable any Round 3-specific assumptions that are not valid in Round 4.
8. Run syntax checks before replay.

Acceptance criteria:

- Strategy runs without exceptions.
- No generated order can exceed product limits under the internal builder.
- No debug output is emitted in normal mode.
- Product list matches Round 4 products.

Reject or fix immediately if:

- The strategy silently skips VFE or all vouchers.
- It generates unsupported product names.
- It relies on Round 3-only TTE constants.
- It produces uncontrolled max-long exposure in every product without a clear reason.

## Phase 1: TTE and Option Model Calibration

Purpose:

Prevent the voucher model from trading against the wrong expiry.

Historical TTE convention to test:

```python
historical_tte_days = max(0.05, 8.0 - day - timestamp / 1_000_000.0)
```

This gives:

- Day 1 starts near 7.
- Day 2 starts near 6.
- Day 3 starts near 5.

Live TTE convention to test:

```python
live_tte_days = max(0.05, 4.0 - timestamp / 1_000_000.0)
```

Required diagnostics:

- Voucher mid minus Black-Scholes fair by strike, day, and timestamp block.
- Buy edge and sell edge distribution by strike.
- Edge hit rate for thresholds 0.5, 1.0, 1.5, 2.0, 5.0, and 8.0.
- Realized replay contribution by strike.
- Whether deep ITM options still imply useful VFE fair.
- Whether 5000/5100 remain the highest-quality strikes.
- Whether 5200/5300 still have realized edge.
- Whether 5400/5500 are still noisy or now useful with changed TTE.

Decision rules:

- Do not trade a voucher just because Black-Scholes says it is mispriced.
- Prefer strikes that show realized replay edge and stable markouts.
- Penalize strikes where edge appears only in one day or one simulator.
- Keep deep ITM vouchers as fair-value inputs even if they are not traded.
- Keep far OTM vouchers disabled unless there is clear evidence of executable edge.

## Phase 2: Base Strategy Validation

Purpose:

Establish the non-Mark baseline. Mark alpha is only valuable if it improves on a clean baseline.

Baseline candidates:

| Candidate | Description |
|---|---|
| `R3-final as-is` | Round 3 final logic with minimal changes |
| `R4 TTE fixed` | Same logic, historical/live TTE corrected |
| `R4 TTE + refit vols` | Correct TTE plus Round 4 volatility/table adjustment |
| `R4 TTE + voucher set sweep` | Correct TTE plus active strike selection |

Required output table:

| Strategy | Full total | Day 1 | Day 2 | Day 3 | Hydrogel | VFE | VEV total | Max drawdown | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|

Base acceptance criteria:

- Positive on at least two of three days.
- No single product hides catastrophic losses.
- VFE/voucher PnL has an economically explainable source.
- Hydrogel does not fail through uncontrolled inventory.
- Drawdown is understood, not ignored.

## Phase 3: Mark Counterparty Research

Purpose:

Separate informed flow from noise and pretense.

Trade sign convention:

```text
If Mark is buyer:
    signed flow = +quantity

If Mark is seller:
    signed flow = -quantity
```

For every `(mark, product)` pair, compute:

- Trade count.
- Total quantity.
- Net signed quantity.
- Buy count and sell count.
- Average trade price versus mid.
- Future mid return after trade.
- Signed future return.
- Markout PnL proxy.
- Stability by day.
- Stability by horizon.
- Whether the Mark is always paired with one counterparty.

Horizons:

- 100
- 500
- 1,000
- 5,000
- 10,000
- 25,000
- 50,000 if enough future data exists

Score:

```text
score(mark, product, horizon) =
    sum(sign * quantity * (future_mid - current_mid)) / sum(quantity)
```

Interpretation:

- Positive score: follow the Mark.
- Negative score: fade the Mark.
- Near zero: ignore.

Minimum evidence rules:

| Rule | Default |
|---|---:|
| Minimum events per `(mark, product)` | 20 |
| Minimum total quantity | 100 |
| Minimum days represented | 2 |
| Minimum absolute score for direct fair adjustment | Product-specific |
| Shrink small samples | Required |

For sparse voucher products, allow a lower event count only if the signal is aggregated by family and has a strong explanation.

### Additional Round 4 Mark Metrics

Add these metrics before choosing live Mark weights.

#### Aggressor Classification

Buyer/seller names tell us who was on each side, but not who demanded liquidity. Classify every trade relative to the prevailing book:

| Trade location | Buyer interpretation | Seller interpretation |
|---|---|---|
| Trade price at or above ask | Buyer likely aggressive | Seller likely passive |
| Trade price at or below bid | Buyer likely passive | Seller likely aggressive |
| Trade price inside spread | Ambiguous or negotiated | Ambiguous or negotiated |
| Trade price at mid | Use tick test fallback | Use tick test fallback |

Metric:

```text
mark_aggressor_score =
    count_aggressive_trades / count_total_trades
```

Use this to split Mark signals into:

- Mark as aggressive buyer.
- Mark as aggressive seller.
- Mark as passive buyer.
- Mark as passive seller.
- Mark inside-spread participant.

This matters because following an informed aggressive buyer is not the same as following a passive seller who happened to get lifted.

#### Mark Adverse Selection

For each `(mark, product, role, side)` bucket, compute post-trade markouts:

```text
markout_h =
    signed_qty * (future_mid[t + h] - trade_price)
```

Where signed quantity is positive when the Mark bought and negative when the Mark sold.

Track:

- Mean markout.
- Median markout.
- Quantity-weighted markout.
- Hit rate.
- Worst decile.
- Day stability.
- Horizon with best markout.

Positive markout means the Mark's trade direction was good after execution. Negative markout means the Mark should potentially be faded.

#### Mark Kyle Lambda

Estimate price impact from signed Mark flow:

```text
future_mid_change = alpha + lambda * mark_signed_qty + error
```

Run this by:

- Mark.
- Product.
- Horizon.
- Day.
- Aggressor bucket.

Interpretation:

- Large positive lambda: Mark flow moves price in its direction.
- Negative lambda: Mark flow mean-reverts or is fadeable.
- Unstable lambda: do not use directly.

#### Mark Half-Life

For every signal, find the horizon where predictive value peaks:

```text
best_horizon = argmax_h abs(score(mark, product, h))
```

Then map best horizon to live decay:

| Best horizon | Suggested decay |
|---:|---:|
| 100 to 500 | 0.50 to 0.75 |
| 1,000 to 5,000 | 0.75 to 0.90 |
| 10,000 to 25,000 | 0.90 to 0.97 |
| 50,000+ | Treat as regime signal, not tick alpha |

#### Mark Stability Score

For each Mark signal, compute:

```text
stability =
    sign_agreement_rate_across_days * min_abs_day_score / max_abs_day_score
```

Reject signals with strong all-data score but poor day stability unless the goal is explicitly regime-specific.

#### Mark Pair Edge

Score full pairs:

```text
pair_score(buyer, seller, product, horizon)
```

Use this to determine whether the edge belongs to:

- Buyer identity.
- Seller identity.
- Specific pair interaction.
- Product regime triggered by that pair.

#### Mark Flow Persistence

Measure whether a Mark's flow clusters:

- Autocorrelation of signed flow.
- Probability next trade has same signed direction.
- Burst length.
- Time between same-Mark trades.
- Trade-size autocorrelation.

Persistent flow may be useful as inventory target adjustment. One-off informed prints may be better as short-lived fair-value bumps.

#### Mark Conflict With Base Model

Track cases where Mark alpha disagrees with the base model:

| Base signal | Mark signal | Experiment |
|---|---|---|
| Buy | Buy | Increase size or lower edge threshold |
| Buy | Sell | Reduce size or require extra edge |
| Sell | Sell | Increase size or lower edge threshold |
| Sell | Buy | Reduce size or require extra edge |
| Neutral | Strong Mark | Allow small exploratory trade |

The first Mark strategy should usually modify thresholds and sizes before it overrides the base fair outright.

Initial observed Mark structure:

| Mark | Early interpretation |
|---|---|
| `Mark 67` | Strong candidate follow signal in VFE |
| `Mark 49` | Strong candidate fade signal in VFE |
| `Mark 55` | Candidate VFE follow/fade depending on horizon and side details |
| `Mark 14` | Very active, product-specific, not safe to classify globally |
| `Mark 38` | Very active, especially paired against `Mark 14`; product-specific |
| `Mark 01` | Heavy voucher activity; may be structural rather than predictive |
| `Mark 22` | Heavy counterparty to `Mark 01`; may be structural rather than predictive |

These are hypotheses, not final rules.

## Phase 4: Mark Signal Families

Purpose:

Avoid one generic Mark alpha. Marks may mean different things in VFE, Hydrogel, and vouchers.

Build separate signal families.

### 4.1 VFE Directional Mark Signal

Questions:

- Does a Mark buying VFE predict VFE mid rising?
- Does a Mark selling VFE predict VFE mid falling?
- Is the signal immediate or delayed?
- Does the signal remain after controlling for current trend?
- Does it survive across days?

Candidate implementation:

```python
vfe_mark_alpha = decayed_sum(mark_weight[mark] * signed_qty)
vfe_fair_adjusted = vfe_model_fair + clip(vfe_mark_alpha, -cap, cap)
```

Initial caps:

- Conservative: 1.0 to 2.5 XIRECS.
- Moderate: 2.5 to 5.0 XIRECS.
- Aggressive: 5.0 to 8.0 XIRECS only after validation.

Acceptance criteria:

- Improves VFE without making voucher losses worse.
- Does not simply force max-long VFE in every regime.
- Improves at least one held-out day and does not materially break another.

### 4.2 Hydrogel Mark Signal

Questions:

- Are `Mark 14` and `Mark 38` informed, liquidity-motivated, or mean-reverting?
- Does Mark side predict Hydrogel mid, or does it predict reversion after an impact trade?
- Is Hydrogel Mark alpha redundant with book imbalance?

Candidate implementation:

```python
hydro_signal = dynamic_hydro_signal + mark_hydro_alpha
```

Do not apply Hydrogel Mark alpha directly to fair until it is proven. Hydrogel was regime-sensitive in Round 3.

Safer first use:

- Tighten buy threshold after informed buy flow.
- Tighten sell threshold after informed sell flow.
- Widen thresholds after adverse/fade flow.
- Increase flattening urgency if Mark flow conflicts with current inventory.

### 4.3 Voucher Direction Mark Signal

Questions:

- Does a voucher Mark predict the voucher's own future mid?
- Does a voucher Mark predict VFE movement?
- Does a voucher Mark predict option residual movement after delta adjustment?

For each option trade, compute:

```text
option_return = future_option_mid - option_mid
underlying_return = future_vfe_mid - vfe_mid
delta_adjusted_return = option_return - option_delta * underlying_return
```

Interpretation:

- Predicts underlying return: use as VFE spot alpha.
- Predicts delta-adjusted residual: use as option fair/residual alpha.
- Predicts neither: ignore.

Voucher Mark alpha should be smaller than VFE alpha:

- Conservative cap: 0.25 to 1.00.
- Moderate cap: 1.00 to 2.50.
- Aggressive cap: 2.50 to 4.00 only with strong evidence.

### 4.4 Mark Pair Signal

Some trade pairs dominate the data:

- `Mark 01 -> Mark 22`
- `Mark 14 -> Mark 38`
- `Mark 38 -> Mark 14`
- `Mark 55 -> Mark 14`
- `Mark 14 -> Mark 55`

Research whether the pair itself matters beyond the buyer/seller names.

Pair diagnostics:

- Average future return by `(buyer, seller, product)`.
- Whether the same buyer has different predictive value against different sellers.
- Whether pair activity marks regime changes.
- Whether some pairs are internal/noise and should be ignored.

Do not add pair logic until single-Mark logic is understood.

## Phase 5: Mark Alpha Design

Purpose:

Convert Mark research into robust live code.

The submitted strategy only sees trades after they occur through `state.market_trades` and/or `state.own_trades`, depending on the datamodel feed. The Mark signal must therefore be online, persistent, and decayed.

State to store in `traderData`:

```json
{
  "mark_alpha": {
    "VELVETFRUIT_EXTRACT": 0.0,
    "HYDROGEL_PACK": 0.0,
    "VEV_5000": 0.0
  },
  "last_seen_trade_ids": {},
  "mark_flow": {},
  "diagnostic_counts": {}
}
```

Keep this compact. `traderData` size can become a hidden risk.

Recommended online update:

```python
alpha = decay * alpha + scale * mark_weight * signed_quantity
alpha = clip(alpha, -cap, cap)
```

Default decay grid:

| Decay | Interpretation |
|---:|---|
| 0.50 | Very short memory |
| 0.75 | Short memory |
| 0.90 | Medium memory |
| 0.97 | Long memory |

Default scale grid:

| Product | Conservative scale |
|---|---:|
| Hydrogel | 0.02 to 0.08 |
| VFE | 0.03 to 0.12 |
| VEV lower strikes | 0.005 to 0.04 |
| VEV middle strikes | 0.005 to 0.03 |
| VEV far strikes | 0.000 to 0.01 |

Apply shrinkage:

```text
effective_weight = raw_weight * n / (n + shrink_k)
```

Suggested `shrink_k`:

- 50 for VFE and Hydrogel.
- 20 for vouchers with sparse data.
- Higher if signal is unstable by day.

## Phase 6: Strategy Branches

Maintain three live branches during research.

### Branch A: Base

Purpose:

Clean non-Mark Round 4 baseline.

Contains:

- Correct TTE.
- Round 4 voucher parameters.
- No Mark alpha.
- Clean OrderBuilder.

Use this as the control in every comparison.

### Branch B: Conservative Mark

Purpose:

Add only robust Mark signals.

Contains:

- Mark alpha only for products with stable evidence.
- Small caps.
- Shrinkage.
- Minimum count guard.
- No pair logic unless very strong.
- No hardcoded timestamp behavior.

Expected role:

- Serious portal candidate.

### Branch C: Aggressive Mark

Purpose:

Probe ceiling and identify whether Mark signals are being underused.

Contains:

- Higher caps.
- More products.
- Optional pair logic.
- Optional threshold changes instead of direct fair adjustment.

Expected role:

- Research branch, not automatic submission candidate.

Promote from C to B only after the aggressive change is simplified and validated.

## Phase 7: Diagnostics To Build

Round 4 diagnostics should extend Round 3 diagnostics.

### Market Diagnostics

- Product mid path by day.
- Spread distribution by product.
- Top-of-book depth distribution by product.
- Imbalance distribution by product.
- Microprice deviation and future returns.
- Regime segmentation by timestamp block.
- Day-to-day drift and volatility.
- VFE versus deep voucher implied fair.
- Hydrogel dynamic fair residual.
- Voucher Black-Scholes residual by strike.
- Option edge by strike and block.

### Mark Diagnostics

- Mark activity table.
- Mark pair activity table.
- Mark signed flow by product.
- Mark signed flow by timestamp block.
- Mark score by horizon.
- Mark score by day.
- Mark score by product family.
- Mark score after controlling for trend.
- Mark score after controlling for spread and imbalance.
- Mark score after excluding tiny trades.
- Mark score after excluding pair-dominated trades.
- Mark flow autocorrelation.
- Mark buyer/seller asymmetry.
- Mark contribution to model decisions in backtest.

### Strategy Diagnostics

- Total PnL by engine.
- PnL by product.
- PnL by day.
- PnL by timestamp block.
- Drawdown by strategy and product.
- Own fills by product, side, and fill class.
- Entry edge to mid.
- Future markouts after own fills.
- Passive versus taker fill quality.
- Inventory path and limit pressure.
- Final inventory.
- Order count and cancellation/rejection symptoms.
- Difference between base and Mark branch decisions.
- Timestamps where Mark branch diverges from base.

### Options Diagnostics

- BS fair by strike.
- Delta by strike.
- Delta-adjusted residual.
- Net option delta.
- VFE plus option combined delta.
- Gamma concentration by strike.
- Theta exposure if useful.
- Voucher inventory by strike.
- Cross-strike relative value.
- Deep-voucher-implied VFE fair quality.
- Strike-specific overtrading.

### Portal Gap Diagnostics

If official bundle exists:

- Compare submitted code to local branch.
- Extract official window.
- Replay base and Mark branches on official window.
- Compare product PnL.
- Compare fills and first divergence.
- Compare Mark trades seen before divergence.
- Identify whether portal weakness is model, fill semantics, or data path.

### Required Metric Backlog

Build these metrics as reusable outputs, not one-off notebook cells.

| Metric | Product family | Purpose |
|---|---|---|
| `mark_aggressor_score` | All | Distinguish informed takers from passive counterparties |
| `mark_adverse_selection` | All | Determine whether Mark flow should be followed or faded |
| `mark_kyle_lambda` | All | Estimate price impact per unit signed Mark flow |
| `mark_pair_edge` | All | Detect pair-specific scripted behavior |
| `mark_half_life` | All | Choose live alpha decay |
| `mark_stability` | All | Reject one-day Mark overfits |
| `mark_flow_persistence` | All | Detect bursts and regime behavior |
| `toxicity_bucket` | All | Test volume-bucket imbalance against future volatility/returns |
| `decision_delta_vs_base` | Strategy | Explain exactly what Mark logic changed |
| `vfe_to_option_lead_lag` | VFE and VEV | Test whether VFE leads options or options lead VFE |
| `option_delta_adjusted_markout` | VEV | Separate option residual edge from underlying movement |
| `strike_edge_decay` | VEV | See whether option edge persists or mean-reverts |
| `deep_voucher_fair_error` | VFE | Validate `VEV_4000`/`VEV_4500` as VFE fair inputs |
| `inventory_pnl_attribution` | Strategy | Split PnL into realized spread, mark-to-market, and end inventory |
| `fill_toxicity_after_own_orders` | Strategy | Find where our fills are followed by adverse movement |
| `portal_window_sensitivity` | Strategy | Measure robustness to the extracted official window |

The highest-priority additions are:

1. `mark_aggressor_score`
2. `mark_adverse_selection`
3. `mark_stability`
4. `option_delta_adjusted_markout`
5. `decision_delta_vs_base`

These directly affect Round 4 strategy design.

## Mini Experiment Queue

Run many mini experiments before building the three portal candidates. Keep each experiment small and named.

### Highest ROI Experiments

| Experiment | Branch/output | Question | Expected decision |
|---|---|---|---|
| Aggressor-aware Mark leaderboard | `mark_diagnostics/aggressor_leaderboard.csv` | Are Mark buyer/seller labels enough, or do we need aggressor buckets? | Choose Mark weights by role |
| `Mark 67` VFE follow | Strategy branch | Does following `Mark 67` improve VFE without hurting vouchers? | Accept/reject VFE follow weight |
| `Mark 49` VFE fade | Strategy branch | Does fading `Mark 49` improve VFE? | Accept/reject VFE fade weight |
| `Mark 55` horizon test | Diagnostics and branch | Is `Mark 55` follow/fade horizon-dependent? | Choose decay or ignore |
| `Mark 14` vs `Mark 38` Hydrogel pair | Diagnostics and branch | Is the pair continuation or reversion? | Threshold adjustment or ignore |
| VFE Mark alpha into VEV spot | Strategy branch | Should VFE Mark alpha change option spot input? | Apply to options or VFE only |
| Voucher residual Mark alpha | Strategy branch | Do option Marks predict delta-adjusted residuals? | Add voucher fair bump or ignore |
| TTE sweep | Option diagnostics | Which historical TTE convention best explains observed voucher prices? | Lock historical/live TTE |
| Strike ablation | Strategy branch | Which VEV strikes actually make money? | Active voucher set |
| Deep-voucher fair weights | Strategy branch | How much should `VEV_4000`/`VEV_4500` influence VFE fair? | VFE fair weights |
| Mark conflict filter | Strategy branch | Should Mark alpha block trades against informed flow? | Size/threshold overlay |
| Endgame inventory flattening | Strategy branch | Does reducing final exposure improve window/official robustness? | Flatten policy |
| Passive quote toxicity | Diagnostics | Are passive fills adverse on Round 4? | Reduce passive quoting if toxic |
| Taker edge quality | Diagnostics | Which taker trades keep positive markout? | Product-specific take thresholds |
| Window-only robustness | Strategy branch | Does candidate survive the official-style window? | Portal candidate eligibility |

### Additional Mark Experiments

1. Remove tiny trades and recompute Mark scores.
2. Remove inside-spread trades and recompute Mark scores.
3. Score only aggressive trades.
4. Score only passive trades.
5. Score only repeated Mark bursts.
6. Score first trade in each Mark burst versus later trades.
7. Compare buyer identity versus seller identity versus pair identity.
8. Compute Mark score conditional on spread being wide or tight.
9. Compute Mark score conditional on book imbalance agreeing with trade direction.
10. Compute Mark score conditional on VFE trend regime.
11. Test Mark alpha as fair-value bump.
12. Test Mark alpha as edge-threshold modifier.
13. Test Mark alpha as size modifier only.
14. Test Mark alpha as inventory target modifier.
15. Test Mark alpha as a no-trade filter when it conflicts with base model.

### Additional Options Experiments

1. Refit volatility by strike using Round 4 historical TTE.
2. Refit volatility by day and compare stability.
3. Use market VFE mid versus model VFE fair as option spot.
4. Blend market spot and fair spot with weights from -0.25 to 1.50.
5. Test `VEV_5000` and `VEV_5100` only.
6. Test `VEV_5000`, `VEV_5100`, and `VEV_5200`.
7. Test `VEV_5000`, `VEV_5100`, and `VEV_5300`.
8. Test all `VEV_5000` through `VEV_5300`.
9. Add `VEV_5400` only if residual markout supports it.
10. Add `VEV_5500` only if realized replay supports it.
11. Test option edge thresholds by strike.
12. Test option sizes by strike.
13. Test delta-exposure caps.
14. Test no-voucher branch to isolate VFE/Hydrogel contribution.
15. Test VFE-only Mark alpha with vouchers disabled.

### Additional Hydrogel Experiments

1. Static fair baseline.
2. Dynamic fair baseline.
3. Dynamic fair plus Mark threshold adjustment.
4. Dynamic fair plus Mark size adjustment.
5. Dynamic fair plus Mark conflict filter.
6. Stronger flattening above inventory 100, 120, 140, and 160.
7. Endgame flattening at final 250k, 150k, 100k, and 50k timestamps.
8. Passive quote size sweep.
9. Taker edge sweep.
10. Imbalance weight sweep.
11. Trend weight sweep.
12. Disable Hydrogel if it hurts window score.

### Additional VFE Experiments

1. VFE take edge sweep.
2. VFE size sweep.
3. VFE passive size sweep.
4. VFE skew sweep.
5. VFE deep-voucher fair weight sweep.
6. VFE Mark fair bump.
7. VFE Mark threshold modifier.
8. VFE Mark size modifier.
9. VFE Mark conflict filter.
10. VFE endgame flattening.
11. VFE inventory target instead of symmetric market making.
12. VFE-only branch with vouchers disabled.

### Manual Aether Experiments

1. EV-max portfolio.
2. Variance-capped portfolio.
3. 5% CVaR-optimized portfolio.
4. Probability-of-negative-PnL minimized portfolio.
5. Remove binary short and compare distribution.
6. Remove KO long and compare distribution.
7. Add `AC_45_P` hedge and compare distribution.
8. Add `AC_35_P` hedge and compare distribution.
9. Include tiny `AC_60_C` short edge and test if it is worth noise.
10. Simulate official-style 100-path averages across at least 50,000 batches.

### Experiment Naming

Use stable labels:

```text
r4_mini_001_tte_sweep
r4_mini_002_mark_aggressor
r4_mini_003_mark67_vfe_follow
r4_mini_004_mark49_vfe_fade
r4_mini_005_hydro_mark14_38_pair
```

Every mini experiment should produce either:

- An accepted strategy change.
- A rejected-change entry.
- A diagnostic table that informs the three-candidate build.

## Phase 8: Acceptance Gates

A change can be accepted only if it passes all applicable gates.

### Gate 1: Mechanical Safety

- Syntax valid.
- No unsupported imports.
- No debug prints in serious candidate.
- `traderData` stays compact.
- Product limits enforced by construction.
- No empty product result omission if the engine expects product keys.
- No hidden dependence on files or local paths.

### Gate 2: Economic Coherence

- The change has a clear market explanation.
- It does not rely only on one simulator quirk.
- It does not generate PnL from unexplained end inventory unless that is the thesis.
- It does not trade a product solely because of surface-model richness.

### Gate 3: Backtest Robustness

- Improves or preserves full-data score.
- Improves or preserves at least two day-split validations.
- Does not introduce a catastrophic product loss.
- Does not worsen drawdown beyond the expected PnL improvement.
- Does not depend on one tiny sample Mark.

### Gate 4: Mark-Specific Robustness

- Mark signal has enough events or is heavily shrunk.
- Mark effect is not just a proxy for a single day.
- Mark effect is product-specific.
- Follow/fade classification is stable by horizon or intentionally horizon-specific.
- Live implementation cannot double-count the same trade repeatedly.

### Gate 5: Submission Readiness

- Candidate is simpler than the research branch where possible.
- Parameters are documented.
- Logs are clean.
- Strategy file is archived before replacement.
- Expected failure modes are known.

## Phase 9: Rejected-Change Discipline

Every rejected change should still be logged. Rejections are useful because they stop repeated rediscovery.

Track:

| Change | Branch | Result | Why rejected | Can revisit if |
|---|---|---:|---|---|

Common rejection reasons:

- Improves one day but breaks two.
- Improves full data but worsens held-out day.
- Improves total only through one fragile product.
- Increases drawdown too much.
- Uses a Mark with too few trades.
- Duplicates existing model signal without adding value.
- Relies on passive fills that may not survive portal.
- Makes strategy too complex for the gain.

## Phase 10: Manual Aether Loop

The manual challenge is standalone. Do not mix it with algorithmic VEV logic.

Known model:

- Underlying: `AETHER_CRYSTAL`.
- Initial spot near 50.
- GBM with zero risk-neutral drift.
- Annualized volatility: 251%.
- Trading days per year: 252.
- Steps per day: 4.
- Two weeks: 10 trading days, 40 steps.
- Three weeks: 15 trading days, 60 steps.
- Barrier checks are discrete only.
- Contract size: 3000.
- Official score uses average PnL over 100 simulations.

Manual valuation tasks:

1. Reprice all vanillas analytically.
2. Reprice binary put analytically.
3. Reprice chooser by Monte Carlo with the exact discrete grid.
4. Reprice knock-out put by Monte Carlo with the exact discrete grid.
5. Compute bid/ask edge for buying and selling each instrument.
6. Build max-edge portfolio.
7. Simulate PnL distribution under many random seeds.
8. Simulate official-style 100-path average distributions.
9. Inspect tail risk and probability of negative score.
10. Decide whether to include EV-positive but high-variance legs.

Preliminary model-backed portfolio:

| Action | Volume | Instrument | Reason |
|---|---:|---|---|
| Buy | 50 | `AC_50_P_2` | Underpriced 2-week ATM put |
| Buy | 50 | `AC_50_C_2` | Underpriced 2-week ATM call |
| Sell | 50 | `AC_50_CO` | Chooser appears overpriced |
| Sell | 50 | `AC_40_BP` | Binary put appears overpriced |
| Buy | 500 | `AC_45_KO` | Knock-out put appears underpriced |

Manual risk warning:

This portfolio has positive expected value under the stated model, but high realized variance because official scoring uses only 100 simulations. The final manual decision should optimize expected value subject to acceptable probability of a bad finite-sample outcome.

Manual outputs to save:

- `ROUND4/research/outputs/aether_fair_values.csv`
- `ROUND4/research/outputs/aether_portfolio_candidates.csv`
- `ROUND4/research/outputs/aether_official_100_path_distribution.csv`
- `ROUND4/research/outputs/aether_final_recommendation.md`

## Phase 11: Experiment Output Structure

Use stable output folders:

```text
ROUND4/research/outputs/
  market_diagnostics/
  mark_diagnostics/
  option_diagnostics/
  mini_experiments/
  strategy_runs/
  manual_aether/
  candidate_packets/
```

Each candidate packet should include:

```text
candidate_packets/
  round4_candidate_<label>/
    strategy.py
    summary.md
    results.csv
    product_pnl.csv
    day_split.csv
    inventory_summary.csv
    mark_exposure.csv
    fill_markouts.csv
    accepted_changes.md
    rejected_changes.md
```

## Phase 12: Final Candidate Selection

Final candidate should be chosen by this priority:

1. Best official portal result, if tested.
2. Best official-window proxy with clean product attribution.
3. Best conservative Mark branch that beats base on validation.
4. Best base branch if Mark alpha proves unstable.
5. Never choose the aggressive branch solely because it has the highest full-data local score.

Required final notes:

- Why this strategy is better than the Round 3 port.
- Which Marks are followed or faded.
- Which Marks are ignored and why.
- Which voucher strikes are traded and why.
- Which product carries the most risk.
- Expected portal mismatch risk.
- Manual portfolio and risk rationale.

## Stop Condition

Continue iterating until one of these is true:

- Conservative Mark branch clearly dominates base and aggressive branch does not add robust value.
- Mark alpha fails validation and base branch is the best reliable candidate.
- Portal feedback identifies a different failure mode that requires a new loop.
- Further changes are tiny, simulator-specific, or economically unjustified.

Do not stop just because one local run improves.

Do stop when every additional change is either:

- Overfit to one day.
- Overfit to one replay engine.
- Too dependent on passive fill generosity.
- Based on weak Mark sample size.
- Increasing drawdown more than it increases expected PnL.
- Too complex to trust under portal uncertainty.

## Working Checklist

Use this checklist during actual implementation.

### Setup

- [ ] Locate and preserve existing `522830.py`.
- [ ] Create `round4_522830_base.py`.
- [ ] Create `round4_base_r3_port.py`.
- [ ] Create `round4_mark_conservative.py`.
- [ ] Create `round4_mark_aggressive.py`.
- [ ] Keep `current_trader.py` as placeholder until promotion.
- [ ] Add Round 4 diagnostics scripts.
- [ ] Confirm product names and limits.

### Baseline

- [ ] Port Round 3 final strategy.
- [ ] Correct historical TTE.
- [ ] Correct live TTE.
- [ ] Run full-data baseline.
- [ ] Run day-split baseline.
- [ ] Save product PnL and inventory.

### Mark Research

- [ ] Build Mark activity table.
- [ ] Build aggressor-aware Mark table.
- [ ] Build Mark pair table.
- [ ] Compute Mark score by product and horizon.
- [ ] Compute Mark score by day.
- [ ] Compute Mark Kyle lambda.
- [ ] Compute Mark half-life.
- [ ] Compute Mark stability score.
- [ ] Compute option delta-adjusted Mark score.
- [ ] Compute Mark conflict-with-base metrics.
- [ ] Choose follow/fade/ignore labels.
- [ ] Document confidence and shrinkage.

### Mini Experiments

- [ ] Run TTE sweep.
- [ ] Run aggressor-aware Mark leaderboard.
- [ ] Run `Mark 67` VFE follow experiment.
- [ ] Run `Mark 49` VFE fade experiment.
- [ ] Run `Mark 14`/`Mark 38` Hydrogel pair experiment.
- [ ] Run VFE Mark alpha into VEV spot experiment.
- [ ] Run voucher residual Mark alpha experiment.
- [ ] Run strike ablation.
- [ ] Run deep-voucher fair weight sweep.
- [ ] Run endgame inventory flattening experiment.
- [ ] Record accepted/rejected mini experiment results.

### Three Portal Candidates

- [ ] Build Algorithm 1 from `522830.py`.
- [ ] Build Algorithm 2 from conservative Mark-aware idea.
- [ ] Build Algorithm 3 from a distinct new strategy thesis.
- [ ] Run Full Kevin and Full Xeeshan.
- [ ] Run Window Kevin and Window Xeeshan.
- [ ] Present all three with the required table format.
- [ ] Wait for user portal results before full iterative loop.

### Strategy Integration

- [ ] Add conservative VFE Mark alpha.
- [ ] Test VFE Mark alpha.
- [ ] Add Hydrogel threshold/flattening Mark logic only if supported.
- [ ] Test Hydrogel Mark logic.
- [ ] Add voucher residual Mark alpha only if supported.
- [ ] Test voucher Mark alpha.
- [ ] Compare base versus Mark branches.

### Manual

- [ ] Reproduce vanilla fair values.
- [ ] Reproduce chooser fair.
- [ ] Reproduce binary fair.
- [ ] Reproduce knock-out fair.
- [ ] Build candidate portfolios.
- [ ] Simulate 100-path official-style distributions.
- [ ] Pick final manual order set.

### Final

- [ ] Promote best branch to `current_trader.py`.
- [ ] Archive alternatives.
- [ ] Package candidate.
- [ ] Save evidence packet.
- [ ] Record accepted/rejected changes.
- [ ] Submit portal candidate.
- [ ] If official bundle returns, compare official versus local.
