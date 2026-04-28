# Round 4 Research

Use this folder for Round 4 analysis scripts, notes, and generated research artifacts.

Suggested layout:

- keep reusable analysis scripts directly under `ROUND4\research\`
- write generated plots and summaries to `ROUND4\research\outputs\`
- keep one-off experiments in clearly named subfolders

Key planning docs:

- `../../algo_guide.md`: required platform-mechanics source for maximizing official profit; use it when designing structural rewrites and product engines.
- `iterative_learning_loop.md`: the single active Round 4 playbook for fast experiments, red flags, candidate handling, and next attacks.

Current direction:

- The goal is maximum official profit.
- Move fast: research, implement, backtest, decide.
- Full rewrites are allowed, but they are a tool, not the goal.
- Incremental fixes are allowed when they have clear ROI.
- Do not create extra markdown files unless they prevent real confusion.
- Use every relevant mechanism from `algo_guide.md`, especially `traderData`, `own_trades`, `market_trades`, passive fills, instantaneous execution, position-limit behavior, and full order-book information.
- Prioritize Hydrogel rebuild-or-cut, post-40k regime engines, product-role fixes, Mark mechanics, and passive-fill learning.
