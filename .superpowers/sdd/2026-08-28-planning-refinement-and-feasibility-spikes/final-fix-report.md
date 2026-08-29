# Final fix report — Tasks 3–5

## Scope

This fix wave is limited to the Task 4 analytics aggregation and Task 5
simulation-storage research artifacts. No Task 6+ files were changed.

## Changes

- Renamed analytics result key `peak_tracemalloc_bytes` to
  `peak_traced_aggregation_bytes` and documented that tracing begins after the
  generated event input exists; it therefore covers Python allocations during
  aggregation only, not pre-built input, total process memory, or native SQLite
  allocations.
- Mechanically migrated the recorded analytics artifact to that key, retaining
  all six recorded byte values, elapsed samples, checksums, and database sizes.
  The 100/1,000/10,000 aggregation matrix was not rerun, so no timings were
  fabricated or replaced.
- Renamed the per-draft `StorageRows`/`StorageBytes` components and result JSON
  keys from `run_metadata` to `draft_metadata`. The report now distinguishes
  SQLite's one true `runs` row from the per-draft fields mirrored by `drafts`.
- Mechanically migrated the 1,000-draft storage artifact keys while retaining
  the measured byte totals and all linear projections. The raw compact NDJSON
  record tag remains the fixed one-character `r`; it is not the component name,
  so keeping it makes the existing compressed-byte measurement exactly
  applicable and avoids an unnecessary rerun.
- Added focused regression assertions for both names, both explanatory
  boundaries, and preserved recorded values.

## Files changed

- `experiments/analytics.py`
- `experiments/data_volume.py`
- `experiments/tests/test_analytics.py`
- `experiments/tests/test_data_volume.py`
- `experiments/results/analytics.json`
- `experiments/results/data-volume.json`
- `docs/research/analytics-compute-spike.md`
- `docs/research/simulation-data-volume.md`
- `.superpowers/sdd/2026-08-28-planning-refinement-and-feasibility-spikes/final-fix-report.md`

## Commands and output

Initial red test after adding the focused assertions:

```text
$ python3 -m unittest experiments.tests.test_analytics experiments.tests.test_data_volume -v
Ran 7 tests in 0.014s
FAILED (failures=1, errors=4)
```

The analytics failure was the expected absence of
`peak_traced_aggregation_bytes`; the storage errors were the expected absence
of `draft_metadata_rows` and `draft_metadata_bytes` in the old dataclasses.

Focused Task 4/5 verification after the fix:

```text
$ python3 -m unittest experiments.tests.test_analytics experiments.tests.test_data_volume -v
Ran 8 tests in 0.041s
OK
```

Full experiment suite:

```text
$ python3 -m unittest discover -s experiments/tests -v
Ran 20 tests in 1.989s
OK
```

Diff and scope checks:

```text
$ git diff --check
(no output; exit 0)

$ git diff --name-only
docs/research/analytics-compute-spike.md
docs/research/simulation-data-volume.md
experiments/analytics.py
experiments/data_volume.py
experiments/results/analytics.json
experiments/results/data-volume.json
experiments/tests/test_analytics.py
experiments/tests/test_data_volume.py
```

The scope search found legacy names only in negative regression assertions;
the final report was added afterward and is itself scoped evidence.

## Self-review

The diff changes terminology and explicitly documents the measurement boundary
without changing aggregation behavior, timing values, checksums, or storage
projection arithmetic. The new tests read the generated artifacts to guard the
key migrations and measured values directly. The raw compact-record tag was
deliberately retained because changing it would alter the measured compressed
payload rather than merely clarify the result schema.

## Concerns

These remain synthetic, non-production measurements. `tracemalloc` still does
not represent total process or native SQLite memory, and the storage sample
still does not measure indexes, WAL/journal sidecars, or operational workloads.
