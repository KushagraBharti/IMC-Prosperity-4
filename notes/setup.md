# Prosperity Workbench Setup

This workspace keeps the trading repo separate from the open-source tooling clones:

- Project repo: `C:\Users\kushagra\OneDrive\Documents\CS Projects\IMC Trading Comp`
- Tool clones: `C:\Users\kushagra\OneDrive\Documents\CS Projects\prosperity-tools`

Cloned tools:

- `chris-monte-carlo`
  - source: `https://github.com/chrispyroberts/imc-prosperity-4`
- `kevin-backtester`
  - source: `https://github.com/kevin-fu1/imc-prosperity-4-backtester`
- `kevin-visualizer`
  - source: `https://github.com/kevin-fu1/imc-prosperity-4-visualizer`
- `xeeshan-backtester`
  - source: `https://github.com/Xeeshan85/imc-prosperity-4-backtester`
- `gsgill7-visualizer`
  - source: `https://github.com/gsgill7/prosperity-visualiser`

Bootstrap command:

```powershell
.\scripts\bootstrap-tools.ps1
```

What bootstrap does:

- creates isolated Python environments per backtester
- installs the replay backtester dependencies
- installs the visualizer dependencies
- creates mirrored round-data directories for tools that expect package-style resource layouts
- prepares Chris's Python environment and warns if Rust/Cargo is still missing

Round-local strategy layout:

- `ROUND1\strategies\current_trader.py`
- `ROUND1\strategies\archive\`
- `TUTORIAL_ROUND\strategies\current_trader.py`
- `TUTORIAL_ROUND\strategies\archive\`

Official output handling:

- Existing numeric submission folders at the round root are treated as legacy official bundles and remain supported.
- New manual imports can also be dropped into `ROUND1\official_submissions\` or `TUTORIAL_ROUND\official_submissions\`.

Outputs:

- replay runs: `outputs\backtests\`
- Monte Carlo runs: `outputs\stress\`
- visualizer handoff: `outputs\visualizer-inbox\`
- packaged submissions: `outputs\submissions\`
