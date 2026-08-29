# Analytics aggregation compute spike

## Question

Can a small, deterministic draft-event model compute the proposed draft
analytics in pure Python and in SQLite with identical results, and which work
is suitable for interactive calculation?

## Methodology

This is a non-production, standard-library-only experiment.  It consumes nested
sequences of deterministic `PickEvent` values from the existing draft engine
and synthetic `SyntheticCard` metadata.  The two implementations produce the
same normalized, sorted JSON-compatible rows for average and median pick,
first seen, last-pick rate, wheel rate, color and card utilization, tag
frequency, and co-occurrence.

The hand-auditable test fixture has two two-seat drafts and six cards.  It
asserts literal expected values against both backends.  Pick positions are
one-based within a pack.  `first_seen` is the earliest chronological sighting
in a draft, reported as its pick position.  The wheel definition is synthetic:
a card instance wheels when the same seat sees it again at least `seat_count`
picks after a prior observation.  It is not a proposed product definition.

Python uses dictionaries, sets, `statistics.median`, and pair combinations.
SQLite uses an in-memory normalized `cards`, `drafts`, `picks`, `seen`,
`pool_cards`, and `card_tags` schema.  It indexes card IDs, draft/seat,
draft/pick number, and the wheel lookup `(draft_id, seat, card_id, sequence)`.

Co-occurrence is deliberately bounded to pairs among the first twelve
chronological cards in a pool.  The measured pool has only three cards, so the
cap does not truncate this micro-workload; it still makes the implementation's
upper bound explicit.

## Environment and commands

Environment: CPython 3.14.0 on macOS 26.5.2 arm64.  No already-installed pandas
or Polars version was detected.  The measured workload intentionally uses one
seat × one pack × three cards, with 12 synthetic cards available, fixed seed
`20260828`, and the existing deterministic draft engine/bot0 chooser.  This
is the minimum legal workload that still exercises repeated visibility, the
synthetic wheel rule, pools, tags, and co-occurrence.  It is not a standard
eight-seat draft.

Primary command (the result JSON contains three repetitions):

```bash
python3 -m experiments.analytics --drafts 100 1000 10000 --seed 20260828 --repetitions 3 --output experiments/results/analytics.json
```

After the controller interrupted an earlier long matrix attempt, bounded
separate reruns provided visible wall-clock and reproducibility evidence:

```bash
/usr/bin/time -p python3 -m experiments.analytics --drafts 100 --seed 20260828 --repetitions 3 --output /tmp/analytics-100-rerun.json
/usr/bin/time -p python3 -m experiments.analytics --drafts 1000 --seed 20260828 --repetitions 3 --output /tmp/analytics-1000-rerun.json
/usr/bin/time -p perl -e 'alarm 180; exec @ARGV' python3 -m experiments.analytics --drafts 10000 --seed 20260828 --repetitions 1 --output /tmp/analytics-10000-rerun.json
```

Those shell runs took 0.19 s, 1.44 s, and 35.48 s respectively.  The last run
completed below its explicit 180-second cap.  Its Python and SQLite checksums
matched each other and the primary 10,000-draft checksum.  The first discarded
attempt used a substantially larger 4-seat × 2-pack × 5-card workload and did
not produce a result file before interruption; it is not evidence.  Code-path
inspection identified an unindexed per-draft wheel self-join, so the composite
`seen` index above was added before the recorded run.

## Measurements

Measured values below are the three-repetition means in
`experiments/results/analytics.json`. Peak traced aggregation allocations are
`tracemalloc` bytes captured only while each aggregation backend runs: tracing
starts after the synthetic event input is built, so these values exclude
pre-built input allocations and are not total process memory.

| Drafts | Events | Serialized input | Python mean / peak traced aggregation allocations | SQLite mean / peak traced aggregation allocations | SQLite DB | Checksum |
|---:|---:|---:|---:|---:|---:|---|
| 100 | 300 | 23,484 B | 0.0062 s / 67,248 B | 0.0080 s / 183,516 B | 86,016 B | `207c89ac…0107fae` |
| 1,000 | 3,000 | 234,815 B | 0.0492 s / 99,968 B | 0.3210 s / 1,555,738 B | 499,712 B | `d6b7a47d…a63f025` |
| 10,000 | 30,000 | 2,347,771 B | 0.5612 s / 542,240 B | 28.5279 s / 17,394,409 B | 4,673,536 B | `08486dc7…65761a1` |

Each row's full SHA-256 result checksum is recorded in the JSON, and the
Python and SQLite checksum is identical for every row.  SQLite size is page
count × page size (4,096 B): 21, 122, and 1,141 pages respectively.

## Observations

Pure Python remains below the two-second interactive threshold at 10,000
micro-drafts.  SQLite exceeds that threshold substantially at that size, even
though it completed the 180-second capped repeat.  The one-seat fixture is too
small to generalize those absolute times to a standard draft; the per-case
event and serialized-input counts are the useful scaling evidence.

The dominant SQLite cost is an inference from the measured gap and schema:
loading normalized rows and evaluating the synthetic wheel self-join over every
flattened `seen` observation dominate its work.  The composite lookup index
removes the earlier per-draft scan problem, but SQLite still performs more row
materialization and query work than the in-process dictionary aggregation.

## Limitations

This measures synthetic cards, deterministic choices, in-memory data, and a
very small draft configuration only.  It does not measure real card data,
production persistence, UI work, concurrent users, total resident memory, or
the eventual product meaning of these metrics.  `tracemalloc` excludes native
SQLite allocations and pre-built input allocations.  The synthetic wheel and co-occurrence definitions need a
future product issue and provenance-aware data model before adoption.

## Risks

Unrestricted card-card co-occurrence is quadratic in the number of candidate
cards per pool or deck.  A production design should bound it to cards sharing
a pool/deck, minimum-support pairs, or a limited candidate set; it must not
blindly aggregate all cards against all cards.  Mixing human, bot-generated,
and gameplay observations would also require explicit provenance rather than
using this experiment's homogeneous event stream.

## Recommendation

Keep simple pure-Python aggregation for small interactive synthetic workloads
and treat SQLite aggregation as precomputable or batch work once the event
volume approaches this spike's 10,000-case result.  Do not add pandas, Polars,
another analytics backend, production storage, or concurrency on this evidence.
Measure a representative multi-seat workload only when a future issue supplies
product metric definitions and a latency target.

## Roadmap/backlog impact

The spike supports retaining deterministic event provenance and a bounded
co-occurrence policy in later M1 analytics work.  It does not define a
production interface, alter the game protocol, make an issue ready, or change
the human-owned toolchain decision.
