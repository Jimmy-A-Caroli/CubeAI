# Synthetic Cube data-footprint probe

## Question

What retained in-memory size does a small, normalized synthetic Cube model use
at the Cube sizes relevant to early local draft experiments?

## Methodology

The non-production `experiments.data_footprint` module constructs seeded,
standard-library `SyntheticCard` tuples and estimates retained size recursively
with `sys.getsizeof`. The estimator de-duplicates object identities and visits
dataclass fields, mappings, and iterable members. It also measures one complete
8-seat, 3-pack, 15-card integer draft result.

## Environment and command

Measured on CPython 3.14.0, macOS 26.5.2, arm64, with five repetitions per
case:

```bash
python3 -m experiments.data_footprint --seed 20260828 --output experiments/results/data-footprint.json
```

## Observations

The synthetic cube estimate grows near-linearly as card count increases. The
per-card estimate falls slightly at larger sizes because shared values such as
tags and short strings are counted once. The complete standard draft result is
larger than the 360-card synthetic cube because each event retains the complete
pack view seen before every pick.

## Measurements

| Case | Retained bytes | Derived value | Mean elapsed seconds |
| --- | ---: | ---: | ---: |
| 90 synthetic cards | 17,372 | 193.0 bytes/card | 0.001031 |
| 180 synthetic cards | 34,292 | 190.5 bytes/card | 0.001631 |
| 360 synthetic cards | 68,132 | 189.3 bytes/card | 0.004191 |
| 540 synthetic cards | 101,972 | 188.8 bytes/card | 0.004554 |
| 720 synthetic cards | 135,812 | 188.6 bytes/card | 0.009185 |
| 1,080 synthetic cards | 203,492 | 188.4 bytes/card | 0.013584 |
| Standard 8 × 3 × 15 draft result | 82,816 | 230.0 bytes/event | 0.006891 |

The complete machine-readable result is
[`experiments/results/data-footprint.json`](../../experiments/results/data-footprint.json).

## Limitations

Python retained size is runtime-specific. This `sys.getsizeof` traversal omits
interpreter and allocator overhead and is not a disk, database, JSON, or
wire-format measurement. The synthetic model deliberately excludes imported
Cube metadata, printing identity, custom cards, tags beyond a single synthetic
tag, and provenance.

## Risks

Using these figures as a production capacity estimate would understate the cost
of domain objects, event provenance, persistence indexes, serialization, and
runtime services. The CPython 3.14 result should not be compared directly with
another Python implementation or language runtime.

## Recommendation

Use these values only as an early local-experiment baseline. Measure actual
domain objects and serialized/persisted records after M1 defines their stable
data model; retain the complete `seen_card_ids` event requirement in those
measurements because it has material footprint consequences.

## Roadmap/backlog impact

No milestone or architecture change is indicated. The result supports keeping
the M1 deterministic draft work local-first and calls for a later M1/M2
measurement against real, provenance-preserving domain structures before any
storage strategy is selected.
