# Leaderboard Gap Notes

Top-100 official scores range from 77,336 to 453,994; median top-100 score is 134,438. Our best official score is 2,821 and best official-window replay is about 8,302.

This is not a parameter-tuning gap. To reach 100k with 10-lot fills requires roughly 10,000 one-tick/unit edges, 2,000 five-tick/unit edges, or 1,000 ten-tick/unit edges. The top score around 454k requires a repeated high-hit-rate source of edge, not sparse single-product z-score trades.

The leaderboard drawdowns are also revealing: many 100k-450k entries have max drawdown near 4k-10k and recovery factors above 15, with the top two above 100. That profile is closer to systematic spread/fair-value harvesting or a deterministic category relation than to noisy forecasting.

Duplicate clusters around 150k suggest a common discoverable public structure. The edge likely comes from a product/category formula, basket/factor residual, market-making/fill mechanism, or an online-detectable official-window regime that our generic screens missed.
