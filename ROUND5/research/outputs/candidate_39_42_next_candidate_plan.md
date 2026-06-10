# Candidate 39/42 Next Candidate Plan

Do not make candidate 45+ blindly. If proceeding, create candidate-42-derived files only:

1. Robust base upgrade: start from candidate 42 and remove active trading in `PEBBLES_XS` while retaining it as fair-value input. Expected: `115.4k` portal / `424.6k` full.
2. Balanced upgrade: candidate 42 + skip `PEBBLES_XS` + selective MICRO/UV settings from candidate 39. Expected: `123.4k` portal / `310.8k` full.
3. Portal-upside 42 branch: balanced upgrade + panel hybrid. Expected: `126.2k` portal / `200.8k` full. Use for official-window upside only, not robust hidden-final base.
4. Do not use taker exits. Do not broad-cross categories. Do not treat qty size increases as a fix.

Recommended next candidate order if creating files later:

- First: balanced upgrade (`probe_c42_transplant_micro_uv_from39_skipxs.py`).
- Second: robust base upgrade (`probe_c42_pure_skip_pebxs.py`).
- Third: portal-upside panel hybrid (`probe_c42_microuv_skipxs_panelhybrid.py`) only if we want official-window upside risk.
