# Deterministic draft-engine spike

## Question

Can a small standard-library draft loop deterministically allocate synthetic
card instances, alternate pack direction, retain complete seen-pack history,
and complete small through oversized draft configurations?

## Methodology

`experiments.draft_engine` shuffles integer card IDs with a local seeded RNG,
allocates packs, performs one synchronous pick per seat per round, and moves
each pack to `(seat + direction) % seats`. Directions alternate `+1, -1` by
pack. Each `PickEvent` records the pack number, pick number, seat, chosen ID,
and all IDs in the pack before removing the choice. A chooser receives visible
`SyntheticCard` values and the current pool, while the default remains the
deliberately mechanical largest-ID selection.

## Environment and command

Measured on CPython 3.14.0, macOS 26.5.2, arm64:

```bash
python3 -m experiments.draft_engine --seed 20260828 --repetitions 7 --output experiments/results/draft-engine.json
```

`time.perf_counter` measured each run and `tracemalloc` recorded each case's
peak Python-traced allocation.

## Observations

All fixed-seed test scenarios reproduced identical events. Conservation holds
for the 360-instance standard configuration, directions alternate, insufficient
card input is rejected, and an injected chooser can inspect card attributes
without changing the engine. The measured workload grows with event count; the
largest configuration has 720 picks per draft.

## Measurements

| Configuration | Events/draft | Mean seconds/draft | Drafts/second | Peak traced bytes |
| --- | ---: | ---: | ---: | ---: |
| 4 × 2 × 3 | 24 | 0.000972 | 1,029.0 | 12,344 |
| 8 × 3 × 15 | 360 | 0.008941 | 111.9 | 206,496 |
| 8 × 5 × 18 | 720 | 0.018945 | 52.8 | 314,992 |

The checksums and full measurements are in
[`experiments/results/draft-engine.json`](../../experiments/results/draft-engine.json).

## Limitations

The integer-card draft engine measures mechanics, not production serialization
or bots. It has no domain validation, persistence, clock, UI/API, game rules,
or human/bot provenance implementation. `tracemalloc` is not total process
memory, and short benchmark timings vary between machines and runs.

## Risks

The experiment's event and chooser contracts are deliberately lightweight and
must not be treated as production public APIs. A later production state machine
will need stronger validation, command errors, identities, and provenance while
preserving deterministic ordering and seen-pack semantics.

## Recommendation

Use the probe as a mechanics baseline for subsequent bot and analytics spikes.
Keep chooser injection and card-attribute visibility, but introduce production
draft interfaces only through an M1 issue after the Cube/domain identities are
defined.

## Roadmap/backlog impact

No M1 implementation issue is unblocked by this alone. The evidence supports
the roadmap's deterministic draft requirement and gives M3's bot baseline an
attribute-aware chooser seam. Future M1 work should add domain-level
conservation and replay tests with real draft-instance identities.
