# Candidate 16 Notes

Thesis: improve candidate 13 rather than replace it. The all-50 scanner still makes PEBBLES the only proven high-PnL category, so candidate 16 keeps all five PEBBLES but adds product-weighted edge gates and slightly less eager crossing.

Products traded: `PEBBLES_XS`, `PEBBLES_S`, `PEBBLES_M`, `PEBBLES_L`, `PEBBLES_XL`.

Evidence: candidate 13 scored about 101k full and 18.5k portal-window replay. Scanner also identified `PEBBLES_XL` and `PEBBLES_M` as the strongest PEBBLES product-level signals.

Execution: inside-spread passive fair-value market making; crosses only on larger residual dislocations.

Failure mode: if candidate 13's extra aggression was the source of edge, candidate 16 may undertrade.
