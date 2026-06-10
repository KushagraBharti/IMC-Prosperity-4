# Candidate 37-44 Recommendation

## Ranking

- Submit first for portal upside: `round5_candidate_37.py` (`123,425 / 123,435` portal, cap-identical). It is the best official-window candidate in this batch and full-validates at `158.8k / 158.5k`, so it is not the old fully toxic robot branch.
- Best robust development base: `round5_candidate_42.py` (`113,412` portal, `421.5k` full). It sacrifices portal score but is the strongest hidden-final/full-history branch found so far.
- Best balanced branch: `round5_candidate_39.py` (`121,436 / 121,446` portal, `254.4k / 254.5k` full). It is the cleanest compromise if we distrust the candidate 37 robot+anchor stack.
- Keep as references/ablations: `round5_candidate_38.py`, `40.py`, `41.py`, `43.py`, `44.py`.

## Interpretation

Candidate 37 proves careful handwritten integration helped: fresh breadth + robot extras + MICROCHIP_SQUARE anchor is additive on portal and much less full-toxic than the earlier robot-pair branch. Candidate 42 proves the robust path is not exhausted: panel/micro-anchor integration improved full-history from the old ~379k robust branch to ~421.5k.

## Next action

Submit `round5_candidate_37.py` if the immediate objective is official portal upside. Use `round5_candidate_42.py` as the next robust development base. Use `round5_candidate_39.py` as the balanced backup if official result for 37 underperforms replay.
