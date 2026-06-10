# Model Diagnostics Note

Model diagnostics from this pass are stored as CSV tables rather than serialized model artifacts.

Key files:

- `../tables/microstructure_predictive_scores.csv`
- `../tables/microstructure_feature_importance.csv`
- `../tables/microstructure_signal_stability.csv`
- `../tables/regime_signal_performance.csv`
- `../tables/phase65_nonlinear_threshold_maps.csv`
- `../tables/phase65_garch_volatility_summary.csv`

No model object is intended for direct submission. Any strategy derived from these diagnostics must be re-expressed as lightweight platform-safe Python logic.
