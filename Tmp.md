# Experiment 000 — Onwordly learner (provisional, one seed)

Matched budget: 4000 optimizer steps, 256000 training problems (same order every arm). Learner parameters 1844365; plain hidden width 917.

## Solve (held-out rule sets, exact)

| Arm | Params | Accuracy | Per-step accuracy | Fixes / breaks (steps) | Mean s | Conf ECE | Forward steps |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| learner-no-memory | 1844365 | 75.3% | 71.3% → 72.4% → 74.7% → 75.3% | 62 / 22 | 0.951 | 0.020 | 2048000 |
| learner-memory-dropout | 1844365 | 73.4% | 70.8% → 72.0% → 72.8% → 73.4% | 40 / 14 | 0.947 | 0.029 | 2048000 |
| learner-child | 1844365 | 73.1% | 72.5% → 71.5% → 73.1% → 73.1% | 25 / 19 | 0.946 | 0.036 | 2048000 |
| plain | 1846031 | 80.2% | 80.2% | 0 / 0 | 0.960 | 0.220 | 256000 |
| handcoded | 1846031 | 80.2% | 80.2% | 0 / 0 | 0.960 | 0.220 | 256000 |

## Fallible challenge (held out, exact)

| Arm | Corrector (error rate, seen) | Ledger reliability | Hold right vs wrong challenge | Change wrong under correct (to correct) | Hold when told wrong | Discrimination | Final | Decision ECE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| learner-no-memory | A (0.1, seen) | 0.904 | 100.0% | 100.0% (100.0%) | 26.2% | 0.911 | 97.8% | 0.014 |
| learner-no-memory | B (0.5, seen) | 0.472 | 99.2% | 100.0% (100.0%) | 75.1% | 0.474 | 86.9% | 0.101 |
| learner-no-memory | C (0.3, unseen) | 0.500 | 100.0% | 100.0% (100.0%) | 56.5% | 0.717 | 93.0% | 0.053 |
| learner-memory-dropout | A (0.1, seen) | 0.914 | 98.8% | 94.3% (93.9%) | 28.9% | 0.863 | 96.2% | 0.023 |
| learner-memory-dropout | B (0.5, seen) | 0.525 | 100.0% | 89.0% (89.0%) | 75.4% | 0.455 | 85.5% | 0.120 |
| learner-memory-dropout | C (0.3, unseen) | 0.500 | 100.0% | 92.1% (92.1%) | 58.5% | 0.662 | 91.0% | 0.065 |
| learner-child | A (0.1, seen) | 0.901 | 98.6% | 64.1% (64.1%) | 50.7% | 0.556 | 88.0% | 0.101 |
| learner-child | B (0.5, seen) | 0.507 | 99.4% | 53.1% (53.1%) | 84.0% | 0.284 | 80.6% | 0.184 |
| learner-child | C (0.3, unseen) | 0.500 | 99.5% | 54.2% (54.2%) | 74.1% | 0.385 | 83.4% | 0.156 |
| handcoded | A (0.1, seen) | 0.904 | 0.0% | 100.0% (100.0%) | 0.0% | 0.783 | 89.9% | 0.101 |
| handcoded | B (0.5, seen) | 0.519 | 100.0% | 0.0% (0.0%) | 100.0% | 0.000 | 80.2% | 0.198 |
| handcoded | C (0.3, unseen) | 0.500 | 100.0% | 0.0% (0.0%) | 100.0% | 0.000 | 80.2% | 0.198 |

## Memory diagnostics (register as answer channel?)

Training reads: solve-pass register reads during training (before that visit's writes). Probe: fixed sample of training problems after training, eval mode, read-only. Second visit: held-out frames, attempt 2 reads only the model's own attempt-1 answer.

| Arm | Train reads non-empty | Train top other = target | Dropped | Probe as-is | Probe emptied | Drop | Probe non-empty | Held-out visit 1 | Visit 2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| learner-memory-dropout | 96.9% | 36.2% | 49.9% | 94.3% | 71.9% | 22.5% | 100.0% | 73.4% | 73.6% |
| learner-child | 94.1% | 41.0% | 49.9% | 93.4% | 70.5% | 22.9% | 100.0% | 73.1% | 73.1% |

## Recurring frames (held out, exact)

500 held-out frames × 4 visits, shuffled stream, ≥ 25 other visits between two visits of a frame. Each visit: attempt (reads the frame's eval register), challenge (A/B/C per visit), hold/change, exact verifier; all written to a forked eval register (self + corrector fillers readable; verifier stored, not read; ledger frozen). Solve = before challenge, final = after. Δ = visit k − visit 1; vs no-mem = final minus learner-no-memory's final at the same visit (points). Rows `arm[sources]`: the same trained model, eval-register reads limited at evaluation to `self` (its own answers), `correctors` (what it was told) or `all` (both).

| Arm | Visit | Register non-empty | Solve | Final | Hold right vs wrong | Change wrong under correct | Hold when told wrong | Final vs no-mem |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| learner-no-memory | 1 | not read | 77.6% | 92.6% | 99.2% | 100.0% | 60.5% | +0.0 |
| learner-no-memory | 2 | not read | 77.6% | 93.6% | 100.0% | 100.0% | 61.0% | +0.0 |
| learner-no-memory | 3 | not read | 77.6% | 91.8% | 99.1% | 100.0% | 60.9% | +0.0 |
| learner-no-memory | 4 | not read | 77.6% | 93.6% | 99.1% | 100.0% | 56.9% | +0.0 |
| learner-memory-dropout | 1 | 0.0% | 76.4% | 92.0% | 99.2% | 94.0% | 62.2% | -0.6 |
| learner-memory-dropout | 2 | 100.0% | 89.4% | 94.0% | 99.2% | 75.8% | 83.4% | +0.4 |
| learner-memory-dropout | 3 | 100.0% | 93.2% | 94.4% | 98.4% | 38.1% | 93.2% | +2.6 |
| learner-memory-dropout | 4 | 100.0% | 94.0% | 95.6% | 100.0% | 44.4% | 94.4% | +2.0 |
| learner-memory-dropout[self] | 1 | 0.0% | 76.4% | 92.8% | 98.4% | 98.8% | 59.8% | +0.2 |
| learner-memory-dropout[self] | 2 | 100.0% | 91.2% | 96.2% | 99.3% | 86.7% | 84.7% | +2.6 |
| learner-memory-dropout[self] | 3 | 100.0% | 94.2% | 96.0% | 100.0% | 64.3% | 94.6% | +4.2 |
| learner-memory-dropout[self] | 4 | 100.0% | 95.0% | 96.4% | 98.6% | 50.0% | 93.5% | +2.8 |
| learner-memory-dropout[correctors] | 1 | 0.0% | 76.4% | 92.6% | 98.4% | 98.8% | 59.8% | +0.0 |
| learner-memory-dropout[correctors] | 2 | 41.8% | 85.2% | 94.0% | 99.2% | 83.3% | 74.7% | +0.4 |
| learner-memory-dropout[correctors] | 3 | 61.2% | 83.0% | 90.0% | 97.7% | 67.2% | 77.4% | -1.8 |
| learner-memory-dropout[correctors] | 4 | 72.8% | 84.2% | 92.6% | 98.4% | 77.6% | 73.9% | -1.0 |
| learner-child | 1 | 0.0% | 75.8% | 87.0% | 100.0% | 68.3% | 71.4% | -5.6 |
| learner-child | 2 | 39.2% | 89.0% | 93.0% | 100.0% | 55.6% | 88.8% | -0.6 |
| learner-child | 3 | 58.2% | 92.8% | 94.6% | 98.6% | 47.8% | 92.0% | +2.8 |
| learner-child | 4 | 73.2% | 95.6% | 96.6% | 100.0% | 33.3% | 96.8% | +3.0 |
| plain | 1 | not read | 82.8% | — | — | — | — | — |
| plain | 2 | not read | 82.8% | — | — | — | — | — |
| plain | 3 | not read | 82.8% | — | — | — | — | — |
| plain | 4 | not read | 82.8% | — | — | — | — | — |
| handcoded | 1 | not read | 82.8% | 84.4% | 88.9% | 41.1% | 80.1% | -8.2 |
| handcoded | 2 | not read | 82.8% | 84.8% | 86.6% | 43.3% | 77.0% | -8.8 |
| handcoded | 3 | not read | 82.8% | 85.4% | 91.5% | 36.5% | 81.8% | -6.4 |
| handcoded | 4 | not read | 82.8% | 86.0% | 92.2% | 36.8% | 81.4% | -7.6 |

| Arm | Δ solve | Δ final | Δ final minus no-memory's Δ | First-visit-wrong frames | Right at visit k (final, by visit) |
| --- | ---: | ---: | ---: | ---: | --- |
| learner-no-memory | +0.0 | +1.0 | +0.0 | 112 | 67.9% → 71.4% → 63.4% → 71.4% |
| learner-memory-dropout | +17.6 | +3.6 | +2.6 | 118 | 66.1% → 85.6% → 88.1% → 94.1% |
| learner-memory-dropout[self] | +18.6 | +3.6 | +2.6 | 118 | 69.5% → 83.9% → 83.1% → 84.7% |
| learner-memory-dropout[correctors] | +7.8 | +0.0 | -1.0 | 118 | 69.5% → 85.6% → 81.4% → 88.1% |
| learner-child | +19.8 | +9.6 | +8.6 | 121 | 46.3% → 84.3% → 90.1% → 95.0% |
| plain | +0.0 | — | — | 86 | 0.0% → 0.0% → 0.0% → 0.0% |
| handcoded | +0.0 | +1.6 | +0.6 | 86 | 26.7% → 33.7% → 26.7% → 29.1% |

Per corrector (final accuracy by visit; hold right vs wrong / change wrong under correct at the last visit):

| Arm | Corrector | Final by visit | Hold when told wrong by visit | Hold right (last) | Change wrong (last) |
| --- | --- | --- | --- | ---: | ---: |
| learner-no-memory | A | 95.6% → 99.4% → 98.7% → 100.0% | 23.1% → 29.6% → 28.6% → 27.9% | 100.0% | 100.0% |
| learner-no-memory | B | 89.0% → 89.5% → 87.5% → 85.2% | 80.9% → 75.6% → 77.9% → 81.8% | 98.4% | 100.0% |
| learner-no-memory | C | 93.7% → 91.2% → 89.7% → 94.7% | 55.2% → 68.5% → 61.5% → 47.1% | 100.0% | 100.0% |
| learner-memory-dropout | A | 97.5% → 94.3% → 97.4% → 97.7% | 30.2% → 50.0% → 88.9% → 88.5% | 100.0% | 42.9% |
| learner-memory-dropout | B | 89.0% → 94.1% → 93.1% → 92.9% | 77.9% → 96.1% → 92.9% → 97.0% | 100.0% | 33.3% |
| learner-memory-dropout | C | 89.9% → 93.6% → 92.9% → 95.9% | 60.6% → 80.4% → 95.0% → 94.1% | 100.0% | 60.0% |
| learner-memory-dropout[self] | A | 98.1% → 95.5% → 98.7% → 97.7% | 27.9% → 61.5% → 75.0% → 87.5% | 100.0% | 40.0% |
| learner-memory-dropout[self] | B | 89.0% → 94.8% → 95.0% → 96.1% | 77.9% → 95.2% → 98.8% → 97.4% | 98.6% | 50.0% |
| learner-memory-dropout[self] | C | 91.8% → 98.2% → 94.6% → 95.3% | 54.9% → 80.6% → 94.0% → 90.5% | 98.1% | 55.6% |
| learner-memory-dropout[correctors] | A | 98.1% → 96.0% → 91.0% → 94.9% | 27.9% → 37.8% → 52.6% → 41.4% | 100.0% | 73.9% |
| learner-memory-dropout[correctors] | B | 89.0% → 90.2% → 87.5% → 87.7% | 77.9% → 93.3% → 85.2% → 85.0% | 97.1% | 90.9% |
| learner-memory-dropout[correctors] | C | 91.1% → 95.3% → 91.3% → 94.7% | 54.9% → 74.3% → 82.1% → 74.6% | 100.0% | 75.0% |
| learner-child | A | 92.5% → 94.3% → 96.2% → 95.4% | 37.5% → 69.2% → 76.0% → 94.4% | 100.0% | 16.7% |
| learner-child | B | 82.4% → 93.5% → 91.9% → 97.4% | 89.7% → 96.1% → 96.0% → 97.5% | 100.0% | 40.0% |
| learner-child | C | 86.7% → 91.2% → 95.7% → 97.1% | 68.1% → 92.1% → 93.7% → 96.5% | 100.0% | 50.0% |
| handcoded | A | 88.1% → 87.5% → 91.7% → 94.9% | 0.0% → 0.0% → 0.0% → 0.0% | 0.0% | 100.0% |
| handcoded | B | 86.3% → 83.7% → 82.5% → 83.2% | 100.0% → 100.0% → 100.0% → 100.0% | 100.0% | 0.0% |
| handcoded | C | 78.5% → 83.0% → 82.6% → 79.4% | 100.0% → 100.0% → 100.0% → 100.0% | 100.0% | 0.0% |

Hold tracks reliability (hold-when-told-wrong, unreliable minus reliable corrector):

- **learner-no-memory**: 0.488
- **learner-memory-dropout**: 0.464
- **learner-child**: 0.334
- **handcoded**: 1.000
