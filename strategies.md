# Tutorial Round

## Current Trader

Path:

- `TUTORIAL_ROUND/strategies/current_trader.py`

Purpose:

- active editable tutorial strategy
- local baseline for replay and tutorial Monte Carlo

High-level idea:

- tutorial-style market making on the two tutorial products
- intended as the current working baseline rather than a frozen historical submission

Notes:

- this file should represent the best current tutorial candidate
- if a new tutorial idea replaces it, archive the old one first

## Official Submission 21031

Path:

- `TUTORIAL_ROUND/21031/21031.py`

Status:

- historical official submission artifact

Notes:

- keep as a reference point only
- compare against later tutorial submissions for directional improvement

## Official Submission 21063

Path:

- `TUTORIAL_ROUND/21063/21063.py`

Status:

- historically important tutorial baseline

High-level idea:

- stable-product market making on the fixed-fair tutorial product
- more adaptive logic on the second tutorial product

Notes:

- this is one of the stronger tutorial references currently in the repo
- useful for understanding the early internal style of the project

## Official Submission 21074

Path:

- `TUTORIAL_ROUND/21074/21074.py`

Status:

- historical official submission artifact

Notes:

- keep for regression comparison and idea lineage

## Official Submission 21089

Path:

- `TUTORIAL_ROUND/21089/21089.py`

Status:

- historical official submission artifact

Notes:

- useful as another point on the tutorial evolution path

## Official Submission 21099

Path:

- `TUTORIAL_ROUND/21099/21099.py`

Status:

- historical official submission artifact

Notes:

- treat as reference, not active code

# Round 1

## Current Trader

Path:

- `ROUND1/strategies/current_trader.py`

Purpose:

- active editable Round 1 strategy
- primary file used by the local replay wrappers when no explicit strategy path is supplied

High-level idea:

- market making on `ASH_COATED_OSMIUM` around a stable fair value
- more adaptive microstructure-driven market making on `INTARIAN_PEPPER_ROOT`
- fair value adjusted using book shape, imbalance, short-horizon trend, and inventory-aware reservation pricing

Strengths:

- structured around clear microstructure signals rather than pure prediction
- compatible with all integrated local replay tools
- useful baseline for comparing fill-model sensitivity across replay engines

Risks:

- pepper behavior appears highly sensitive to simulator fill semantics
- local replay and official portal currently disagree materially on realized pepper performance

## scratch_alpha_01

Path:

- `ROUND1/scratch_alpha_01/trader.py`

Status:

- active scratch strategy under investigation

High-level idea:

- same broad family as the current Round 1 baseline
- dynamic market making on both products
- stronger structure and more aggression than the simplest fixed-fair approach

Important note:

- this strategy is effectively the same as the `184591` official submission artifact in the repo, aside from a trailing newline difference
- this makes it the main file to use when comparing portal results against local replay outputs

Known issue:

- official portal result is materially positive on the current evaluation window
- public local replay engines currently score it materially negative, especially on pepper

## Official Submission 167536

Path:

- `ROUND1/official_submissions/167536/167536.py`

Status:

- historical Round 1 official submission

High-level idea:

- stable-product market making on osmium
- trend-plus-anchor style fair value model on pepper

Known characteristics:

- earlier logic than the newer scratch/current Round 1 strategy family
- useful as a simpler Round 1 reference

Notes:

- this is a good checkpoint for comparing “simple robust baseline” versus “more adaptive microstructure model”

## Official Submission 184591

Path:

- `ROUND1/official_submissions/184591/184591.py`
- `ROUND1/official_submissions/184591/184591.log`
- `ROUND1/official_submissions/184591/184591.json`

Status:

- critical investigation artifact

High-level idea:

- same strategy family as `scratch_alpha_01`
- active market making in both products with adaptive fair and inventory-aware placement

Why it matters:

- this bundle is the main reference for official portal-versus-local replay mismatch analysis
- the official portal reports positive PnL on the evaluation window
- public local replay tools score the same strategy materially negative on the same window

Use:

- primary artifact for simulator-difference debugging
- upload candidate for visualizer comparison against local replay logs

## Official Submission 214011

Path:

- `ROUND1/official_submissions/214011/`
- `ROUND1/official_submissions/214011.zip`

Status:

- official submission artifact present in the repo

Notes:

- preserve as historical evidence
- detailed strategy characterization is still pending a dedicated read-through

## Research Baseline

Path:

- `ROUND1/research/analyze_round1.py`
- `ROUND1/research/outputs/`

Purpose:

- not a trader itself
- research and diagnostics for Round 1 data

What it is used for:

- spread analysis
- midpoint path inspection
- imbalance signal inspection
- pepper detrending and structural analysis

## Strategy Registry Conventions

When adding a new strategy to Round 1:

- give it a stable name
- record its file path
- describe the fair-value model
- describe the execution model
- describe the main risk
- note whether it is a scratch idea, active candidate, archived winner, or official artifact

# Round 2

## No Strategies Registered Yet

Round 2 strategy work has not been documented in this file yet.

# Round 3

## No Strategies Registered Yet

Round 3 strategy work has not been documented in this file yet.

# Round 4

## No Strategies Registered Yet

Round 4 strategy work has not been documented in this file yet.

# Round 5

## No Strategies Registered Yet

Round 5 strategy work has not been documented in this file yet.

# Round 6

## No Strategies Registered Yet

Round 6 strategy work has not been documented in this file yet.

# Round 7

## No Strategies Registered Yet

Round 7 strategy work has not been documented in this file yet.

# Round 8

## No Strategies Registered Yet

Round 8 strategy work has not been documented in this file yet.
