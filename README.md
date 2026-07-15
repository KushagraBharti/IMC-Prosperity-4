# IMC Prosperity 4 Trading System

Finished **top 6% worldwide among 18,803 teams** in IMC Prosperity 4 by building market-making, statistical-arbitrage, and options-pricing strategies across five rounds of a global algorithmic trading competition.

The project combines competition code with a complete quantitative-research workflow: fair-value modeling, Black-Scholes voucher pricing, hindsight-oracle research, historical replay, Monte Carlo simulation, candidate promotion gates, and round-by-round postmortems.

## Product and highlights

The goal was not simply to produce one trader file. The repository became a research system for finding, testing, rejecting, and promoting trading edges under changing market mechanics.

Highlights include:

- Top 6% worldwide across 18,803 teams.
- Five rounds of live algorithmic and manual trading.
- Fair-value market making with inventory-aware quoting.
- Drift and carry strategies for directional products.
- Black-Scholes pricing and delta modeling for voucher options.
- Statistical arbitrage across a 50-product final-round universe.
- Hindsight-oracle research for locating the products and regimes where exploitable edge existed.
- Replay-fidelity tooling for diagnosing differences between local backtests and official evaluation.
- Compact `traderData` serialization that preserved state under the competition’s strict payload limit.

The central lesson was robustness: a strategy that dominates one feedback window can collapse when the evaluation regime changes. Candidate promotion therefore depended on transfer across multiple windows and replay conditions, not a single peak backtest.

## How the trading system works

### Competition contract

Each strategy implements the standard Prosperity interface:

```python
class Trader:
    def run(self, state):
        return orders, conversions, trader_data
```

On each timestamp, the trader receives:

- Current order books
- Existing positions
- Recent trades
- Conversion observations
- Counterparty information where available
- Persisted strategy state through `traderData`

It returns orders, conversions, and an updated serialized state.

### Research loop

Each round follows the same operating cycle:

1. Inspect the new products and market mechanics.
2. Measure price behavior, spreads, correlations, and inventory constraints.
3. Form a pricing or signal hypothesis.
4. Implement an isolated candidate.
5. Replay it across the portal window and broader historical data.
6. Compare product-level PnL, drawdown, fills, and failure modes.
7. Promote only candidates that survive multiple evaluation windows.
8. Archive the submitted code and official result for later diagnosis.

### Round-by-round strategy

#### Round 1 — Market making and directional carry

The first round centered on `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.

**ASH_COATED_OSMIUM** behaved like a stationary product suitable for fair-value market making. The strategy estimated a stable fair, monitored top-of-book imbalance, and shifted reservation prices according to inventory. The trader bought below fair, sold above fair, and became more conservative as exposure grew.

**INTARIAN_PEPPER_ROOT** exhibited a directional premium. Rather than forcing symmetric market making onto a trending product, the strategy treated it as a drift-and-carry opportunity and accumulated long exposure when the modeled forward edge justified it.

#### Round 2 — Mechanism design and expected value

Round 2 carried forward the core trading logic while adding the Market Access Fee decision.

The access bid was modeled as an expected-value problem:

```text
expected trading value
− access cost
− uncertainty buffer
```

This separated the value of entering a market from the strategies used once access was obtained.

#### Round 3 — Black-Scholes voucher pricing

Round 3 introduced vouchers behaving like options on `VELVETFRUIT_EXTRACT`.

The strategy:

- Estimated the underlying fair value.
- Priced vouchers with Black-Scholes.
- Used an error-function approximation for the normal CDF.
- Modeled strike-specific volatility.
- Updated time to expiry as the round progressed.
- Computed delta for directional exposure.
- Participated selectively where market prices diverged from theoretical value.

The strategy focused on the strikes where pricing errors were large enough to survive spread and execution risk.

#### Round 4 — Counterparty signals and anti-overfitting

Round 4 expanded the system with:

- Counterparty-flow signals
- Timed exits and re-entry rules
- Product-level PnL locks
- Volatility-smile diagnostics
- Portal-window versus full-history comparisons

Counterparty behavior associated with recurring bots was treated as a signal, but only after testing whether it transferred beyond the visible feedback window.

This round produced the clearest overfitting lesson: a large portal-window improvement compressed sharply under final evaluation. From that point forward, transfer risk became a first-class promotion criterion.

#### Round 5 — Fifty-product statistical arbitrage

The final round expanded to 50 products across 10 categories.

The system combined:

- Synthetic fair values for related product families
- Size-weighted component models for `PEBBLES`
- Category anchors
- Per-product momentum and reversal signals
- Category-relative residuals
- Rolling z-scores
- Signal-to-position conversion under position limits
- Product and category PnL attribution

Rather than treating each symbol independently, the strategy modeled products relative to their family and anchor. Deviations from the expected category structure became statistical-arbitrage opportunities.

### Hindsight-oracle research

The hindsight oracle used future prices to calculate an upper bound on realizable opportunity by product and category. It was never used as a live strategy.

Its purpose was diagnostic:

- Determine where meaningful edge actually existed.
- Compare portal-executable and full-history opportunity.
- Identify products worth further research.
- Study which observable signals preceded profitable moves.
- Avoid spending time optimizing markets with little attainable edge.

### Replay, simulation, and state engineering

The repository contains historical replay engines and a Rust-backed Monte Carlo simulator.

The simulator handles:

- Synthetic order-book generation
- Immediate crossing fills
- Resting-order fills
- Bot taker flow
- Position and cash accounting
- Mark-to-market PnL
- Parallel simulation through Rayon
- Session traces and dashboard bundles

Replay-fidelity analysis identified three major sources of local-versus-official divergence:

- Different evaluation windows
- Different within-tick matching behavior
- Passive fill sensitivity inside the spread

Persistent state was compressed with scaled integer encoding and delta-encoded histories before being trimmed against a fixed payload budget.

### Technologies and external dependencies

- **Strategy research:** Python, NumPy, pandas, orjson
- **Backtesting:** Python replay CLIs and historical Prosperity data
- **Simulation:** Rust, Rayon, serde, rand
- **Dashboard:** React, TypeScript, Vite
- **Tooling:** uv, Cargo, npm
- **External data:** Official IMC Prosperity logs, market data, and datamodel contracts

### Repository structure

```text
imc-prosperity-4/
├── ROUND1/ and ROUND1-final/   # Round 1 experiments and official artifacts
├── ROUND2/ and ROUND2-final/   # Round 2 research and submission
├── ROUND3/ and ROUND3-final/   # Voucher and options research
├── ROUND4/ and ROUND4-final/   # Flow signals and transfer analysis
├── ROUND5/                     # Fifty-product statistical-arbitrage system
├── backtester/                 # Python replay and Monte Carlo CLI
├── rust_simulator/             # Parallel Rust market simulator
├── visualizer/                 # React/Vite research dashboard
├── calibration/                # Market-structure calibration work
├── data/                       # Competition datasets
└── scripts/                    # Research and automation utilities
```

## Quick start

Requirements: Python 3.9+, `uv`, Rust/Cargo, and Node.js.

```powershell
cd backtester
uv venv
uv sync
.\.venv\Scripts\Activate.ps1
uv pip install -e .
cd ..
```

Run a smoke backtest:

```powershell
prosperity4mcbt example_trader.py --quick --out tmp/example/dashboard.json
```

Start the dashboard:

```powershell
cd visualizer
npm install
npm run dev
```

Run historical replay:

```powershell
prosperity3bt example_trader.py 0 --data data
```
