# Candidate 21-25 Recommendation

Submit order:

1. `round5_candidate_24.py` for highest official-window upside: portal replay `41760`, full `131k`.
2. `round5_candidate_23.py` for best robust integrated branch: portal replay `37240`, full `184k`.
3. `round5_candidate_25.py` as balanced integration: portal replay `38946`, full `157k`.

Standalone candidates:

- `round5_candidate_21.py` is a valid non-PEBBLES standalone candidate, but it is mainly useful as a component/control branch.
- `round5_candidate_22.py` is portal-strong but full-history weaker; submit only if testing official-window sensitivity.

For later iterative promotion, use:

1. `round5_candidate_23.py` as the main robust integrated base.
2. `round5_candidate_24.py` as the high-official-window integration branch.
3. `round5_candidate_16.py` or `round5_candidate_12.py` as the clean PEBBLES control branch.

Do not promote candidate 21 or 22 over integrated branches unless official portal results contradict local replay.
