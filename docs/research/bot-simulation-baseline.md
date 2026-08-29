# Heuristic bot simulation baseline

## Question

Do three transparent heuristic bot levels make a sequential, standard eight-seat
draft simulation computationally material at 100, 1,000, and 10,000 drafts?

## Methodology

The non-production experiment uses the deterministic synthetic-card generator
and the existing integer-card draft engine. Each draft is 8 seats × 3 packs ×
15 cards (360 picks), with fixed seed `20260828`. Each strategy uses the same
seed sequence and runs three sequential repetitions for each batch size.

`bot0` chooses raw rating. `bot1` adds `0.75 * pool_color_share`; `bot2`
also adds `0.35` for mana value at most three when normalized pool curve share
exceeds `0.45`. Equal scores choose the lowest card ID. The injected chooser
receives pool IDs, so this isolated model reconstructs pool color and mana
attributes from the documented deterministic generator convention. It does not
represent a future production bot interface.

The experiment starts `tracemalloc` for each repetition, records elapsed wall
time with `time.perf_counter`, and checks the ten-minute limit after each draft
in a 10,000-draft batch. After a redundant full-matrix repeat was ruled
anomalously slow by the controller and terminated, one bounded 100-draft
repeat per strategy compared only stable strategy, seed, draft-count, and
checksum fields.

## Environment and command

Primary command:

```bash
python3 -m experiments.bot_simulation --drafts 100 1000 10000 --strategies bot0 bot1 bot2 --seed 20260828 --repetitions 3 --output experiments/results/bot-simulation.json
```

Bounded repeat command:

```bash
python3 -m experiments.bot_simulation --drafts 100 --strategies bot0 bot1 bot2 --seed 20260828 --repetitions 1 --output /tmp/bot-simulation-repeat-100.json
```

Environment: CPython 3.14.0 on macOS 26.5.2 arm64, with 10 logical CPUs
reported by `os.cpu_count()`. The sandbox denied the macOS CPU-model query, so
no CPU model is reported. This was one sequential Python process; wall time is
the useful scheduling/latency measure here, and no separate process-CPU-time
sample was captured. Python bytecode execution is therefore effectively
single-core for these chooser loops, although the host has additional logical
CPUs.

## Observations

All primary cases completed all three repetitions. No 10,000-draft repetition
approached the ten-minute stop threshold: the slowest was bot2 at 78.43 seconds.
The raw-rating strategy is about three times faster than the two pool-aware
strategies. The additional curve calculation adds a modest cost beyond color
fit.

The bounded rerun matched the three 100-draft stable tuples of strategy, seed,
draft count, and checksum. Timing and traced allocation peaks naturally varied
and were excluded from that comparison. The controller terminated the redundant
full-matrix repeat after anomalous runtime, so it is not used as evidence.

## Measurements

Measured primary-run values; elapsed ranges are the three repetition samples.

| Strategy | Drafts | Mean wall time | Drafts/s | Repetition range | Peak traced memory | Checksum |
|---|---:|---:|---:|---:|---:|---:|
| bot0 | 100 | 0.293 s | 341.0 | 0.252–0.367 s | 212,764 B | 7788792921317202750 |
| bot0 | 1,000 | 2.492 s | 401.2 | 2.469–2.526 s | 130,596 B | 11943675501771462790 |
| bot0 | 10,000 | 25.329 s | 394.8 | 24.756–25.990 s | 130,564 B | 5511054195656919338 |
| bot1 | 100 | 0.675 s | 148.2 | 0.660–0.703 s | 131,028 B | 17648810157792754756 |
| bot1 | 1,000 | 6.697 s | 149.3 | 6.605–6.863 s | 130,620 B | 158585835923404106 |
| bot1 | 10,000 | 67.475 s | 148.2 | 66.545–68.651 s | 130,588 B | 8838557780695726458 |
| bot2 | 100 | 0.759 s | 131.7 | 0.742–0.793 s | 130,980 B | 6708021895044125410 |
| bot2 | 1,000 | 7.547 s | 132.5 | 7.469–7.688 s | 130,620 B | 17969312738145488384 |
| bot2 | 10,000 | 76.652 s | 130.5 | 75.612–78.433 s | 130,652 B | 3143057243534818870 |

The peak is the maximum per-repetition `tracemalloc` value and excludes the
synthetic card tuple created before tracing, interpreter baseline, and total
process memory. Bounded stable-field comparison passed for all three 100-draft
strategy cases.

## Limitations

This measures synthetic integer-card mechanics, transparent scoring, and Python
allocation tracing only. It does not measure real Cube-card parsing, rules text,
archetype evaluation, persistence, serialization, analytics, UI work, bot
quality, or total resident memory. Reconstructed pool attributes are valid only
for this generator's fixed ID convention. The timings are specific to this
machine, CPython release, and tracing configuration. The redundant full-matrix
repeat was controller-aborted after anomalous runtime, so only the bounded
100-draft repeat independently verifies stable fields.

## Risks

Treating this as production capacity would be misleading: realistic card and
strategy data can change both CPU and memory costs. Pool-aware scoring scans the
small synthetic pool for each candidate by design; a future production strategy
needs separately justified data structures and measurements. Running large
simulation matrices alongside interactive local use may still compete for CPU.

## Recommendation

Keep the baseline sequential and transparent. Parallel execution is not
justified for this spike: even the slowest 10,000-draft batch completes in under
79 seconds per repetition and stays well below the stated stop rule. Revisit
parallelism only after a realistic, separately measured workload makes the
latency or throughput requirement concrete; do not optimize this experimental
loop by adding opaque caching or multiprocessing.

## Roadmap/backlog impact

The evidence supports M1's planned basic-bot draft exploration and later
reproducible simulation batches without an immediate parallel-execution work
item. Preserve fixed seeds, strategy identifiers, and provenance when a future
production issue defines the actual bot boundary. This result does not make any
M0/M1 issue ready or change the human-owned toolchain decision.
