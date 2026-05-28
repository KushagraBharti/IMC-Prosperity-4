# IMC Prosperity 4 Research Archive

This repository is the full research archive and trading workbench for my IMC
Prosperity 4 competition run. It is not just a folder of final submissions. It
contains the strategy lineage, backtesting workflow, official feedback analysis,
candidate scorecards, round-by-round diagnostics, manual puzzle work, and the
lessons that mattered when local replay disagreed with the official engine.

## Outcome

- Finished in the top 6% worldwide.
- Built algorithmic strategies across all five rounds, from two-product market
  making to a 50-product final universe.
- Maintained separate analysis for algorithmic PnL, manual puzzle PnL, local
  replay PnL, portal-window PnL, official feedback PnL, and final-package PnL.
- Archived final/best official algorithmic artifacts totaling
  415,950.25341796825 displayed algorithmic PnL across the stored scorecard.

## Scorecard

| Round | Main products / scope | Archived algorithmic result | Manual result | Core lesson |
| --- | --- | ---: | ---: | --- |
| Round 1 | `ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT` | 89,306.8125 | 87,995.10 | Pepper drift dominated; Osmium was secondary mean-reversion/market making. |
| Round 2 | Same two products plus market-access fee | 81,359.0 raw / 80,708 displayed | 164,664 | Paying huge access fees was unnecessary once Pepper inventory could be reached. |
| Round 3 | `HYDROGEL_PACK`, `VELVETFRUIT_EXTRACT`, VEV vouchers | 76,114.025390625 | 78,715 | Selective VFE/voucher trading beat broad option-surface brute force. |
| Round 4 | Round 3 universe with new Mark/signal mechanics | 50,966.40673828125 | 2,826.16 | Regime transfer mattered more than clean local replay or earlier feedback-window PnL. |
| Round 5 | 50 products, position limit 10 each | 118,855.008789062 | Not the main archived edge | State-size control and fillability mattered as much as alpha discovery. |

## Repository Map

```text
.
├── main.py                         # Runs the multi-tool Prosperity workbench loop
├── repo.md                         # High-level repo orientation and active strategy paths
├── workflow.md                     # Daily workflow and tool usage notes
├── algo_guide.md                   # Platform mechanics and competition constraints
├── config/                         # Round metadata and default active round config
├── scripts/                        # PowerShell wrappers and official-window diagnostics
├── TUTORIAL_ROUND/                 # Tutorial round strategies/data
├── ROUND1/ ... ROUND5/             # Live round research, candidates, strategies, outputs
├── ROUND1-final/ ... ROUND4-final/ # Final report/submission packages for archived rounds
└── notes/                          # Setup notes, external tool locations, workflow notes
```

The most important files to read first are:

1. `repo.md`
2. `workflow.md`
3. `algo_guide.md`
4. The relevant `ROUND*/research/README.md`
5. The relevant `ROUND*-final/round*.md`
6. The archived official submission folders for the round being investigated

## Running The Workbench

The root runner coordinates the local replay stack:

```bash
python main.py --round round5 --skip-chris
```

With an explicit strategy:

```bash
python main.py --round round5 --strategy ROUND5/official_submissions/570579/570579.py --skip-chris
```

With specific days:

```bash
python main.py --round round3 --days 0 --strategy ROUND3-final/algo_submission/final-algo/486387.py --skip-chris
```

The runner executes:

- Xeeshan backtester
- Kevin backtester
- Rust backtester
- gsgill visualizer
- Kevin visualizer
- Chris Monte Carlo only for tutorial unless explicitly forced

Local replay is useful, but it is not truth by itself. The official engine,
portal feedback, final package logs, and state-size constraints are all part of
the real evaluation surface.

## Platform Mechanics That Mattered

### `Trader.run()`

Every strategy is built around the Prosperity `Trader.run()` contract:

```python
result, conversions, traderData = Trader().run(state)
```

The strategy has to reconstruct state from the incoming `TradingState`, submit
orders within position limits, and persist any memory through `traderData`.

### Stateless Runtime

The official runtime behaves like a stateless AWS Lambda environment. Anything
not returned through `traderData` cannot be trusted to persist. Local globals can
be convenient during development, but official strategy logic must assume a cold
process.

### Position Limits

Position limits are enforced on aggregate submitted orders, not just currently
filled inventory. A strategy can fail even when the current position is inside
the limit if its submitted order set could push the aggregate exposure out of
range.

### Fill Semantics

Immediate crossing orders can fill directly. Passive residual orders can be hit
by bots later in the tick, then auto-cancelled. This made fillability, quote
placement, and conservative inventory assumptions important in every round.

### Round 2 Market Access Fee

Round 2 added `bid()`, where higher bids bought more market access. The final
strategy used a conservative bid of 651 because the marginal value of extra
access was low once the Pepper accumulator could reliably reach the +80 target.

### `traderData` Size Cap

The official environment effectively capped `traderData` at 50,000 characters.
This became the decisive Round 5 engineering constraint. Strategies with
90k-130k characters of state looked excellent locally, then reset or degraded
officially. The repaired candidates used compact aliases, delta-encoded integer
histories, half-tick scaling, residual scaling, and cache trimming.

## Research Principles

### 1. Local Replay Is A Tool, Not A Verdict

Several strategies looked strong in local full replay but failed under official
feedback windows or final package evaluation. A candidate was not trusted unless
it had:

- local full replay
- portal-window replay
- official feedback comparison when available
- product/time attribution
- inventory path inspection
- drawdown review
- state-size checks
- a concrete transfer-risk explanation

### 2. Product Attribution Beats Aggregate PnL

Aggregate PnL hid weak products. Round 4 made this obvious: strong VFE/voucher
contributions masked Hydrogel losses, stale voucher exposure, and drawdown risk.
Every serious candidate needed product-level PnL and time-block attribution.

### 3. Execution Quality Is Alpha

The best signal is still weak if it cannot fill, fills too late, or leaves toxic
inventory. The strongest strategies treated spread crossing, passive placement,
inventory skew, fill certainty, and time exits as part of the alpha model.

### 4. Official Constraints Are Part Of The Game

The Round 5 state-cap issue was not an implementation footnote. It changed the
leaderboard behavior. A strategy that cannot fit inside official runtime limits
is not a strategy; it is a local-only artifact.

### 5. Manual And Algorithmic Work Should Stay Separate

Manual puzzle PnL and algorithmic trading PnL were both valuable, but combining
them too early makes research analysis noisy. This repo keeps the two streams
conceptually separate.

## Round 1: Two-Product Market Making And Drift Capture

### Products

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

### Research Findings

`ASH_COATED_OSMIUM` behaved like a stationary product centered near 10,000. The
useful signals were fair-value deviation, book imbalance, and careful inventory
management. It was a market-making problem more than a trend-following problem.

`INTARIAN_PEPPER_ROOT` had an almost deterministic upward drift of roughly 0.001
per timestamp, with day-level anchors near 10,000, 11,000, and 12,000. That made
early accumulation and carry more important than small passive edge capture.

### Final Algorithmic Result

- Algorithmic PnL: 89,306.8125
- Final inventory: Pepper +80, Osmium +78
- Main contributor: Pepper carry
- Secondary contributor: Osmium specialist logic

### Manual Result

- Bought 9,999 `DRYLAND_FLAX`
- Bought 19,999 `EMBER_MUSHROOM`
- Manual PnL: 87,995.10
- Manual rank: 1st for the round

### Lesson

When one product has a structural carry edge, the strategy should be built around
capturing that edge reliably. Passive quote optimization is secondary if it
risks missing the core inventory target.

## Round 2: Market Access Fee

### New Mechanic

Round 2 introduced a market-access-fee bid. Higher bids received more quote
access, but the fee directly reduced displayed PnL.

### Final Algorithmic Result

- Raw algorithmic PnL: 81,359.0
- Displayed algorithmic PnL after fee: 80,708
- Market access fee bid: 651
- Final inventory: Pepper +80, Osmium +80

### Manual Result

- Final allocation: 18% Research / 57% Scale / 25% Speed
- Manual PnL: 164,664

### Lesson

The fee decision had to be priced like a marginal execution upgrade. Paying more
for access only made sense if it improved fills enough to offset the fee. In
practice, the disciplined Pepper accumulator did not need an aggressive fee.

## Round 3: Underlying, Vouchers, And Selectivity

### Products

- `HYDROGEL_PACK`
- `VELVETFRUIT_EXTRACT`
- VEV vouchers from 4000 to 6500 strikes

### Strategy Components

- dynamic Hydrogel fair-value estimation
- VFE fair-value inference from underlying and voucher signals
- Black-Scholes-style voucher pricing
- strike-specific volatility assumptions
- expiry-aware pricing
- inventory skew
- product-specific take and quote thresholds
- portal-window versus full-replay comparison

### Final Algorithmic Result

- Algorithmic PnL: 76,114.025390625
- Manual PnL: 78,715
- Major realized contributors: `VEV_5000`, `VELVETFRUIT_EXTRACT`, `VEV_5100`,
  `VEV_5200`, `HYDROGEL_PACK`, `VEV_5300`

### Accepted Changes

- dynamic Hydrogel fair
- selective VFE sizing
- focused 5000-5300 voucher exposure
- reduced option inventory/delta dampening where it damaged fills

### Rejected Changes

- broad option-surface brute force
- raw 5500 addition
- over-aggressive VFE sizing
- static Hydrogel overlays
- changes that improved local PnL without portal-window support

### Lesson

The best option strategy was not "trade every theoretical mispricing." It was
selective replay-informed exposure to strikes and products that actually filled
and transferred.

## Round 4: Regime Transfer And Attribution Discipline

Round 4 was the clearest warning that high official-feedback PnL can still be
fragile. The exact same 830-line strategy scored 87,114.392 in earlier official
feedback and only 50,966.40673828125 in the final package.

### Research Focus

- Mark-driven signal mechanics
- VFE/voucher role audits
- Hydrogel failure analysis
- post-40k plateau diagnostics
- product/time attribution
- drawdown analysis
- candidate promotion gates
- portal-window-only versus robust improvement labels

### Final Algorithmic Result

- Algorithmic PnL: 50,966.40673828125
- Manual PnL: 2,826.16

### Final Diagnostics

Useful contributors remained in VFE and selected vouchers, but Hydrogel,
`VEV_5200`, `VEV_5300`, and drawdown control were not good enough. The final
outcome showed that candidate promotion needed stricter attribution gates.

### Lesson

Clean logs and high feedback-window PnL are insufficient. A strategy has to
survive regime transfer, product-level attribution, and drawdown inspection.

## Round 5: 50 Products, State Compression, And Fillability

### Product Universe

Round 5 scaled to 50 products with position limit 10 each across:

- Galaxy Sounds
- Sleep Pods
- Microchips
- Pebbles
- Robots
- UV Visors
- Translators
- Panels
- Oxygen Shakes
- Snack Packs

### Data Validation

The research verified:

- all 50 expected products were present
- no unexpected products were present
- price files had 17 columns
- trade files had 7 columns
- buyer/seller fields were mostly blank in sampled trade rows

That pushed the strategy work toward price action, synthetic fair value,
residual baskets, anchors, category-relative value, and fillability instead of
counterparty analysis.

### Alpha Families

Round 5 candidates used combinations of:

- PEBBLES synthetic fair value
- PEBBLES and TRANSLATOR anchors
- MICROCHIP relative value
- PANEL relative value
- UV momentum/reversal
- SLEEP momentum/reversal
- OXYGEN relative value
- ROBOT momentum
- GALAXY momentum
- product-specific passive and taker logic
- state-limited history and residual caches

### State-Cap Diagnosis

The most important Round 5 bug was local/official state mismatch. Local replay
initially allowed oversized `traderData`; official evaluation did not. This made
some candidates appear much stronger locally than they were officially.

Examples:

- candidate 29 and candidate 30 carried state near or above 90k-130k characters
- official behavior matched forced-50k-cap replay far more closely than uncapped replay
- repaired candidates dropped state size into safer ranges using compact encodings

### Candidate Tradeoffs

| Candidate | Portal-window behavior | Full-run behavior | Interpretation |
| --- | ---: | ---: | --- |
| 35 | ~91.9k | ~287k | Strong balanced branch. |
| 36 | ~105.5k | much weaker full robustness | Higher portal upside, more fragile. |
| 42 | ~111k-113k | ~421k | Best full-run robustness branch. |
| 49 | ~126k | ~201k | High portal upside without total collapse. |
| 50 | ~128k | negative full behavior | Pure portal-window gamble; too fragile. |

### Best Stored Official Round 5 Submission

- Official algorithmic PnL: 118,855.008789062
- Strong contributors included:
  - `PEBBLES_S`
  - `PEBBLES_XL`
  - `MICROCHIP_OVAL`
  - `TRANSLATOR_SPACE_GRAY`
  - `SLEEP_COTTON`
  - `PANEL_4X4`
  - `MICROCHIP_SQUARE`
  - `UV_AMBER`
  - `ROBOT_LAUNDRY`
  - `GALAXY_PLANETARY`

### Lesson

Round 5 was less about finding one huge signal and more about balancing many
small edges under state, fill, and transfer constraints. A strategy needed alpha,
but it also needed to fit into the official runtime and fill in the evaluated
window.

## Technical Patterns That Repeated

### Fair Value Models

- static fair values for stationary products
- smoothed dynamic fair values
- book imbalance corrections
- deviation and trend terms
- synthetic fair values from related products
- category-relative fair values
- anchor-product normalization

### Execution Models

- spread-aware taking
- passive quoting
- inventory skew
- time exits
- product-specific quote sizes
- fillability checks
- avoiding dead inventory
- conservative position-limit accounting

### Option/Voucher Models

- Black-Scholes-style pricing
- strike-specific volatility
- time-to-expiry decay
- underlying-implied fair values
- selective strike participation
- inventory and exposure controls

### Diagnostics

- official-window extraction
- fill-sequence comparison
- product-level PnL attribution
- time-block PnL attribution
- inventory paths
- drawdown tracking
- state-size audits
- full-run versus portal-window comparison

## What I Would Do Differently

1. Add state-size enforcement from the first day of Round 5 instead of diagnosing
   it after official mismatches appeared.
2. Promote candidates only after product-level attribution, not just aggregate
   PnL.
3. Keep a stricter separation between robust full-run branches and portal-window
   upside branches.
4. Build fillability and inventory decay metrics earlier.
5. Treat same-code feedback/final divergence as a first-class risk signal, not
   just a surprising result.

## The Core Learning

In a constrained trading competition, alpha is not enough. The winning unit is
the entire system: data validation, simulator fidelity, execution mechanics,
state serialization, risk control, candidate discipline, and official-feedback
interpretation. If any one of those pieces is wrong, a strong backtest can become
a weak official submission.
