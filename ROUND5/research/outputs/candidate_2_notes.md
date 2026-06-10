# Candidate 2 Notes

Edge hypothesis: products that survived nested train-two-days/test-one-day selection have robust simple reversion or momentum structure.

Products/categories traded: `ROBOT_LAUNDRY`, `TRANSLATOR_GRAPHITE_MIST`, `PEBBLES_L`, `TRANSLATOR_ASTRO_BLACK`, `ROBOT_IRONING`, `SLEEP_POD_SUEDE`, `MICROCHIP_OVAL`, `UV_VISOR_ORANGE`.

Hidden robustness rationale: product inclusion comes from nested validation, not raw in-sample ranking. Signals are normalized by online realized volatility.

Inventory controls: hard limit 10, max order size 1-2, inventory relief near +/-7 or +/-8.

Execution style: passive by default, only crosses when signal is unusually strong and spread is not wide versus volatility.

Likely failure modes: long-horizon signal timing may be hard to monetize in replay; selected products may share hidden regime risk.

Overfit risks: uses product-specific signal family from research, but thresholds are conservative and normalized rather than exact public-data levels.
