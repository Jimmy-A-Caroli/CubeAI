# Simulation Data Volume Spike

## Question

For deterministic synthetic eight-seat drafts, how much space do normalized pick,
seen-card, pool, and per-draft metadata records occupy as compact NDJSON,
gzip-compressed NDJSON, and a compact normalized SQLite file? What linear
planning estimates follow for larger simulated batches without selecting a
production persistence design?

## Methodology

This non-production probe generated 1,000 deterministic synthetic drafts with
the committed experiment engine. Each draft has eight seats, three packs per
seat, and fifteen cards per pack (360 picks per draft). For every generated
draft it streamed compact UTF-8 NDJSON arrays for pick rows, seen-card rows,
pool-entry rows, and one per-draft metadata row. It populated the same
facts into a temporary normalized SQLite database.

The SQLite schema has `runs`, `drafts`, `picks`, `seen`, and `pool_entries`
tables. Its primary keys preserve logical row identity; it deliberately has no
query-specific secondary indexes. The probe commits and runs `VACUUM` before
measuring the main database file, so the result is a compact baseline rather
than an on-line operational database. The NDJSON payload was compressed with
`gzip.compress(..., compresslevel=6)`.

The single SQLite `runs` row is true run metadata. The one-per-draft compact
NDJSON `r` records mirror fields held by SQLite `drafts` rows; `r` is only the
fixed one-character record tag, while the measured component is named draft
metadata rather than run metadata.

## Environment and command

Measured on CPython 3.14.0, macOS 26.5.2 arm64:

```bash
python3 -m experiments.data_volume \
  --sample-drafts 1000 \
  --targets 1000 10000 100000 1000000 \
  --seed 20260828 \
  --output experiments/results/data-volume.json
```

## Measured facts

The 1,000-draft sample emitted 360,000 pick rows, 2,880,000 seen-card rows,
360,000 pool rows, and 1,000 per-draft metadata rows. These are measured row
counts, not estimates.

| Encoding or compact component | Measured bytes | Approx. MiB |
| --- | ---: | ---: |
| Pick-row NDJSON | 8,034,400 | 7.66 |
| Seen-row NDJSON | 56,188,591 | 53.59 |
| Pool-data NDJSON | 6,610,400 | 6.30 |
| Per-draft metadata NDJSON | 25,890 | 0.02 |
| Combined compact NDJSON | 70,859,281 | 67.58 |
| Gzip level-6 NDJSON | 12,173,922 | 11.61 |
| Compact normalized SQLite main file | 126,828,544 | 120.95 |

Seen-card rows dominate the compact NDJSON sample (about 79% of its bytes).
The gzip result is about 5.8 times smaller than compact NDJSON for this
synthetic, repetitive encoding. The measured SQLite main file is about 1.8
times compact NDJSON and about 10.4 times gzip NDJSON. These comparisons
describe this file shape only; they are not general database or compression
benchmarks.

## Projections

The table below is a **linear projection** from the 1,000-draft measurement.
It is not a new measurement and does not include growth from secondary indexes,
WAL/journal files, backups, free pages, schema changes, or a different data
distribution.

| Target drafts | Compact NDJSON | Gzip level-6 NDJSON | SQLite main file |
| ---: | ---: | ---: | ---: |
| 1,000 | 70,859,281 B (67.58 MiB) | 12,173,922 B (11.61 MiB) | 126,828,544 B (120.95 MiB) |
| 10,000 | 708,592,810 B (0.66 GiB) | 121,739,220 B (0.11 GiB) | 1,268,285,440 B (1.18 GiB) |
| 100,000 | 7,085,928,100 B (6.60 GiB) | 1,217,392,200 B (1.13 GiB) | 12,682,854,400 B (11.81 GiB) |
| 1,000,000 | 70,859,281,000 B (65.99 GiB) | 12,173,922,000 B (11.34 GiB) | 126,828,544,000 B (118.12 GiB) |

The JSON result retains the detailed projected pick, seen, pool, and metadata
byte estimates alongside these aggregate encodings. No Parquet dependency,
measurement, or numerical Parquet claim is made: this probe supplies no local
evidence for one.

## Documented behavior and assumptions

The probe deliberately uses the standard-library `gzip.compress` call at level
6 and SQLite's main database file after `VACUUM`; those are documented probe
behaviors, not a production-storage choice. The linear table assumes that the
observed row and byte rates per synthetic draft continue unchanged. It also
assumes the same fixed 8×3×15 geometry, compact record keys, SQLite page
configuration, and no query-specific indexes. Those assumptions are why the
table is labeled as projections rather than measurements.

## Operational interpretation

SQLite being large is not by itself a reason to replace it. A local file can
remain suitable when expected user disk space and backup time are acceptable,
the actual query set meets its latency targets, write pauses are tolerable, and
the maintenance workflow is understandable for the intended user. The measured
file is only a compact baseline; it answers none of those operational questions
by itself.

SQLite becomes operationally inconvenient when evidence shows that the needed
secondary indexes materially increase file size or insert cost, write
amplification causes unacceptable stalls, or representative queries miss their
latency budget. Backup and export matter separately: a large main file plus
active WAL/journal state needs a documented consistent-backup procedure, while
compact NDJSON/gzip exports may be easier to move but are less convenient for
interactive queries. `VACUUM` can recover free pages after substantial churn,
but it requires temporary free space and can be disruptive; the VACUUMed sample
therefore should not be treated as a steady-state operational size. A growing
set of special indexes, ad-hoc maintenance scripts, or export formats can also
make the simplest local persistence choice less maintainable even when raw
bytes fit comfortably on disk.

## Limitations and risks

- The cards, picks, and pools are synthetic and use an intentionally compact
  array encoding; real domain identities and diagnostics may change row size.
- The sample holds a fixed draft geometry and deterministic chooser; it does
  not establish production workload mix, concurrency, retention, or access
  patterns.
- Gzip efficiency depends on value repetition and ordering. The observed ratio
  must not be generalized to real Cube content without another measurement.
- The SQLite count excludes query-specific indexes, WAL/journal sidecars,
  backups, migration headroom, and file fragmentation between VACUUM runs.
- Linear projections preserve the measured per-draft rate but cannot predict
  nonlinear operational costs such as cache pressure, filesystem behavior, or
  long-running maintenance.

## Recommendation

Keep storage selection open. Retain the generated event/pool shape as a
reproducible planning datum and use the gzip NDJSON result as a compact export
reference, not as a persistence recommendation. Before an M1/M4 storage issue
chooses or rejects SQLite, measure representative schemas and query workloads
with the required indexes, write pattern, backup/export procedure, and
maintenance expectations. Do not infer a hard SQLite cutoff from these bytes.

## Roadmap and backlog impact

This spike does not change the proposed SQLite-first local architecture or
create a production persistence implementation. It supports keeping M1
persistence and M4 simulation storage behind replaceable boundaries, with a
future issue defining retention, indexes, query latency targets, and export /
backup behavior from product evidence.
