# Candidate 6-10 Design Notes

This batch deliberately moved away from broad survivor baskets and toward concentrated official-positive legs. Candidate 2-style broad trading is rejected. Candidate 3 is used only after pruning the losing products.

- `round5_candidate_6.py`: `PEBBLES_XL` only. Full-limit rolling z-score reversion. Best robustness profile in this batch because full Kevin/Xeeshan are positive and portal replay improves over Candidates 1/4.
- `round5_candidate_7.py`: `PEBBLES_XL` plus gated `PEBBLES_L`. Higher official-window upside than Candidate 6, but negative full-history because `PEBBLES_L` remains unstable.
- `round5_candidate_8.py`: ROBOT-only repair of Candidate 4. Official-window positive and structurally distinct, but full-history profile is poor.
- `round5_candidate_9.py`: highest-upside PEBBLES/PANEL branch. Best portal-window replay by far, but full-history drawdown makes it a high-risk submission.
- `round5_candidate_10.py`: stricter `PEBBLES_XL` branch. More selective than Candidate 6; portal replay is stronger but full-history is slightly negative.

The batch is materially more aggressive than Candidates 1-5: it uses 5-10 lot orders, allows full +/-10 positions, crosses when signals are strong, and concentrates instead of diversifying into weak products.
