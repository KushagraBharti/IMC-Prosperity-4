# IMC Prosperity 4 Trading Research System

Competitive algorithmic trading research for IMC Prosperity 4, built around fast strategy iteration, replay validation, and a Rust-backed Monte Carlo backtester. The project treats the competition like a production research loop: diagnose market mechanics, encode compact strategy state, backtest candidate changes, promote only the variants that clear gates, and keep a visual audit trail of why a strategy did or did not survive.

The submitted team workflow had verified PnL for all five rounds down to decimal precision, plus a replay-fidelity investigation that identified three concrete sources of simulator/server divergence. The most expensive lesson was Round 4: a window-collapse change that looked like an `87k` improvement in backtest compressed to about `51k` live, which led to tighter promotion gates and a stronger bias toward replay stability over peak fitted PnL.

Highlights:

- Five-round IMC Prosperity strategy research with verified round PnLs and postmortems.
- Candidate promotion gates for moving changes from experiment to submission candidate.
- Round 4 research corpus with `1,517` backtest logs for window and parameter analysis.
- `traderData` compression using scale-10 and delta encoding to fit state into the exchange log limit.
- Rust Monte Carlo engine plus Python CLI and Vite dashboard for distribution-level strategy checks.
- Legacy historical replay compatibility for Prosperity CSV datasets.

## Technical Architecture

The repo has two layers: competition strategy research and reusable tooling.

The reusable toolchain centers on `prosperity4mcbt`, a Python CLI that loads a normal Prosperity `Trader.run(state)` implementation and runs it against a Rust simulator. Strategies keep the standard competition contract:

```python
class Trader:
    def run(self, state):
        return orders, conversions, trader_data
```

The Monte Carlo path handles order book generation, immediate crossing fills, resting order simulation, bot taker flow, cash/position accounting, mark-to-market PnL, path tracing, and dashboard bundle generation. Sessions run independently in parallel through Rayon on the Rust side, while the Python package owns the strategy bridge and output assembly.

The tutorial-round simulator is calibrated from `data/round0/`:

- `EMERALDS` uses a fixed fair value around `10000`.
- `TOMATOES` uses a zero-drift latent fair-value process calibrated from the tutorial CSVs.
- Bot quote placement, spread structure, one-sided inside quotes, taker timing, side mix, and size distributions are inferred from observed files rather than invented as generic noise.

The dashboard writes:

- `dashboard.json`
- `session_summary.csv`
- `run_summary.csv`
- `sample_paths/`
- `sessions/`

The visualizer is a local React/Vite app with Monte Carlo views for total/product PnL distributions, stability, profitability, best/worst sessions, and sampled path bands. The repo also retains the `prosperity3bt` replay CLI lineage for historical CSV playback.

### Research Practices Captured

- Replay fidelity is treated as a first-class research artifact, not an afterthought.
- Candidate strategies are promoted by gates, not by a single best backtest.
- The Round 4 `87k -> 51k` live gap is documented as a window-collapse overfitting lesson.
- Large-scale Round 4 sweeps produced `1,517` logs for regression and parameter-window review.
- `traderData` is encoded compactly with scale-10/delta state so live submissions can preserve enough memory without breaching the log cap.

## Setup And Run

Prerequisites:

- Python `3.9+`
- `uv`
- Rust / Cargo
- Node / npm

Install the backtester:

```bash
cd imc-prosperity-4/backtester
uv venv
uv sync
source .venv/bin/activate
uv pip install -e .
cd ..
```

On PowerShell, activate with:

```powershell
cd imc-prosperity-4\backtester
uv venv
uv sync
.\.venv\Scripts\Activate.ps1
uv pip install -e .
cd ..
```

Run the bundled starter as a smoke test:

```bash
source backtester/.venv/bin/activate
prosperity4mcbt example_trader.py --quick --out tmp/example/dashboard.json
```

Run your own trader:

```bash
source backtester/.venv/bin/activate
prosperity4mcbt your_trader.py --quick --out tmp/your_run/dashboard.json
prosperity4mcbt your_trader.py --out tmp/your_run/dashboard.json
prosperity4mcbt your_trader.py --heavy --out tmp/your_run/dashboard.json
```

CLI presets:

- default / `--quick`: `100` sessions, `10` saved sample sessions
- `--heavy`: `1000` sessions, `100` saved sample sessions
- manual override: `--sessions 3000 --sample-sessions 150`

Start the visualizer:

```bash
cd visualizer
npm install
npm run dev
```

Then run a backtest with visualization:

```bash
cd ..
source backtester/.venv/bin/activate
prosperity4mcbt your_trader.py --quick --vis --out tmp/your_run/dashboard.json
```

The common local URL is:

```text
http://127.0.0.1:5555/
```

Run historical replay instead of Monte Carlo:

```bash
source backtester/.venv/bin/activate
prosperity3bt your_trader.py 0 --data data
```

Build the visualizer:

```bash
cd visualizer
npm run build
```

## Repository Map

```text
imc-prosperity-4/
├── backtester/         # Python CLIs, strategy bridge, dashboard bundle builder
├── rust_simulator/     # Rust simulation engine
├── visualizer/         # React/Vite dashboard
├── calibration/        # market-structure reverse engineering notes/scripts
├── scripts/            # helper scripts and Python strategy worker
├── data/               # tutorial-round CSV data
├── example_trader.py   # official IMC starter trader template
├── starter.py          # simple example strategy
└── test_algo.py        # local test strategy
```

## Status

The Monte Carlo simulator is designed for strategy comparison, robustness testing, and research discipline. It is not a claim of exact official-market reconstruction. The historical replay path remains available when exact CSV playback is the right tool.

## Attribution

This project includes adapted components from Jasper van Merle's open-source IMC Prosperity 3 tooling:

- Backtester lineage: https://github.com/jmerle/imc-prosperity-3-backtester
- Visualizer lineage: https://github.com/jmerle/imc-prosperity-3-visualizer

The Rust simulator, Monte Carlo engine, dashboard data model, tutorial-round calibration work, and Monte Carlo visualizer route are original additions in this repo.
