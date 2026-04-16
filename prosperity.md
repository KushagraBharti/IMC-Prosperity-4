# Prosperity

This document is the project-level reference for how `IMC Prosperity 4` works, what the competition is optimizing for, and how to think about the round structure.

## What Prosperity 4 Is

`Prosperity 4` is IMC's 2026 simulated trading challenge. It is a staged, team-based competition built around market microstructure rather than pure forecasting.

The event structure is:

- tutorial round before the main rounds
- five main competition rounds
- each round has:
  - one algorithmic challenge
  - one manual challenge
- the algorithmic and manual tracks are scored independently

The official schedule for `Prosperity 4` is:

- tutorial round: `March 16, 2026` to `April 13, 2026`
- main competition: `April 14, 2026` to `April 30, 2026`

Teams can have up to `5` members.

## Ranking And Prizes

Final ranking is based on simulated account balance.

If two teams tie on final balance, the earlier final algorithm submission ranks higher.

The prize pool is:

- `$50,000` overall
- plus a separate `$5,000` manual-trading prize

There is also an eligibility restriction:

- prior Top-10 participants from earlier Prosperity editions may participate again
- but teams containing them are ineligible for ranking, prizes, and recognition

## What The Competition Actually Tests

The official framing matters. IMC repeatedly presents Prosperity as:

- a simulated trading game
- a learning environment
- a team exercise in decision-making under time pressure
- a way to learn order books, liquidity, inventory, and risk

That implies a very specific meta:

- this is not mainly an ML leaderboard
- this is not a latency race
- this is not a pure time-series prediction contest

It is primarily a `microstructure and implementation competition`.

The strongest recurring themes are:

- fair value estimation
- market making
- inventory management
- exploiting visible liquidity
- identifying recurring bot behavior
- building tooling that speeds up iteration

## How Evaluation Works In Practice

The strongest public evidence from prior editions is that teams are evaluated independently against the Prosperity simulator and its built-in market/bot environment, then compared by resulting PnL.

That means your direct opponent is usually not another student live on the same order book.

Instead, your opponent is:

- the simulator design
- the order matching rules
- the bot ecology
- the hidden evaluation behavior

This matters because it changes what creates edge.

In a real market, many edges are about:

- queue position uncertainty
- adversarial other participants
- latency and race conditions

In Prosperity, the dominant edges are more often:

- fair value
- spread capture
- inventory-aware quoting
- cross-product mispricing
- options/conversion logic in later rounds
- bot pattern exploitation

## Canonical Strategy Families

Across public Prosperity repos and writeups from prior years, the same families show up repeatedly.

### Round-one style products

These usually involve:

- one stable product that behaves like fixed-fair market making
- one noisier or more structured product that rewards better microstructure modeling

Typical methods:

- fixed-fair quoting
- simple drift or mean-reversion overlays
- imbalance or wall-mid signals
- inventory-aware reservation price adjustments

### Statistical arbitrage / basket rounds

These usually involve:

- a basket or ETF-like product
- constituent products
- a spread between synthetic value and quoted market value

Typical methods:

- synthetic fair calculation
- divergence thresholds
- basket-versus-leg execution logic

### Derivatives rounds

These usually involve:

- options-like products
- implied volatility
- fair pricing versus market quotes

Typical methods:

- Black-Scholes style fair value
- smile fitting
- vol surface heuristics

### Conversion / location / fee rounds

These usually involve:

- cross-market conversion structure
- tariffs, fees, transport, or location frictions

Typical methods:

- conversion-adjusted fair value
- carry and fee accounting
- constrained arbitrage

### Informed-flow / trader-ID rounds

These usually involve:

- identifiable counterparties
- hidden informed bots
- copying or fading specific agents

Typical methods:

- counterparty tracking
- directional inference from observed named flow
- follow/avoid logic

## What Public Winners Repeatedly Say

The public postmortems from strong teams are unusually consistent.

The recurring lessons are:

- simple robust systems usually beat complicated fragile ones
- local backtesting and visualization are critical
- inventory mistakes are expensive
- overfitting is dangerous
- hardcoded behavior without fallback breaks when the simulator changes
- division of work and fast iteration matter a lot

That means the operational edge is not only the strategy itself. It is also:

- better logs
- better visual inspection
- faster resubmission
- cleaner experiments

## The Data You See

At the replay level, the two core datasets are:

- `prices_*.csv`
- `trades_*.csv`

The price files contain the visible state of the book at each timestamp:

- bid levels
- ask levels
- displayed depth
- midpoint
- running PnL field in official-style outputs

The trade files contain realized trades:

- timestamp
- symbol
- price
- quantity
- buyer / seller identifiers when available in that round

Conceptually:

- the order book is displayed liquidity
- the trade tape is realized flow

Strong Prosperity strategies usually reason about both together.

## Manual Rounds

Manual rounds are separate from algorithmic rounds and often matter less for total leaderboard position than the algorithmic game, but they still matter.

Historically, manual rounds are usually discrete EV problems such as:

- auctions
- reserve-price reasoning
- probability
- game theory
- optimization
- news or narrative interpretation

The right posture is:

- do not ignore manual
- do not let manual consume the main algorithm research pipeline

## Product Limits And Constraints

Position limits are product-specific and must be respected by the simulator.

For the early Prosperity 4 products that matter in this repo, the public tooling consensus is:

- `EMERALDS`: `80`
- `TOMATOES`: `80`
- `INTARIAN_PEPPER_ROOT`: `80`
- `ASH_COATED_OSMIUM`: `80`

Public backtesters generally enforce these limits before matching.

The details of that enforcement can differ slightly between tools, which is part of why exact portal reproduction is difficult.

## Why Public Backtesters Matter

The public Prosperity 4 tooling ecosystem is not just convenience. It is the practical workbench for the competition.

Current important tool categories are:

- replay backtesters
- visualizers
- Monte Carlo or generative stress tools
- log comparison utilities

In this repo, the main integrated tools are:

- `Xeeshan` replay backtester
- `Kevin` replay backtester
- `GeyzsoN` Rust replay backtester
- `gsgill7` visualizer
- `Kevin` visualizer
- `Chris` Monte Carlo backtester

Note: Public backtesters aren't super accurate and shouldn't be treated as ground truth.

## What Local Backtesters Are Good For

Local backtesters are useful, but only if they are used correctly.

They are good for:

- fast iteration
- structural debugging
- comparing product splits
- spotting overtrading
- spotting inventory blowups
- checking if an idea is fragile across simulators

They are bad for:

- exact portal score prediction
- trusting passive-fill-heavy edges too literally
- assuming one simulator's fill model is the truth

The right mental model is:

- local replay is an instrument
- the official portal is the judge

## Current Known Mismatch: Official Portal Versus Public Replays

This repo has already observed a meaningful mismatch between official portal output and public local backtesters for at least one Round 1 strategy.

The most important findings are:

- official bundles may represent only the portal's current evaluation window rather than a full local-style replay
- even when local replay is truncated to match the same official window, the portal and public replayers can still disagree materially
- that disagreement is especially likely for strategies that rely on passive inside-spread fills and subtle within-tick matching behavior

That means:

- the exact portal simulator is not fully reproduced by current public tools
- local replay should be used for direction, diagnostics, and robustness checks
- official submission results should be treated as truth

## Recommended Competition Workflow

The best working workflow is:

1. build a robust strategy idea
2. test it locally on multiple replay engines
3. inspect logs visually
4. submit serious candidates to the official portal
5. keep only ideas that survive both local and portal checks

In practice, that means:

- avoid strategies that only work under one simulator
- distrust ideas that depend on tiny passive-fill assumptions
- prefer edges that still make sense under more pessimistic fills

## What “Winning” Usually Looks Like

The historically strongest teams do not usually win by deploying the fanciest model.

They usually win by combining:

- strong microstructure intuition
- simple reliable fair-value logic
- disciplined inventory control
- bot or structural exploitation where available
- strong tooling
- fast iteration

That is the correct frame for the competition.

Prosperity rewards:

- clear thinking
- adaptation
- robust execution

more than it rewards cosmetic model complexity.
