# M2-009 — Provenance-aware Draft Metrics Evidence

## Status

**COMPLETE.** M2-009 implements the frozen
[Draft Position & Metrics Contract](M2-DRAFT-POSITION-METRICS-CONTRACT.md) as
a pure CubeLab application calculation. It adds neither a metric store nor an
HTTP/UI analytics view.

## Implemented boundary

`cubeai.lab.application.derive_draft_metrics(states, actor_scope)` accepts
immutable `DraftState` values and returns typed, deterministic results. It
only includes states whose status is `COMPLETED`. A calculation requires one
exact `CubeVersion` and one exact configuration tuple
`(seats, packs_per_seat, pack_size)`; it rejects a mixed completed population.
Incomplete states are excluded before that population is formed.

Every result carries a `MetricContext` containing:

- the exact CubeVersion and draft geometry;
- the explicit actor selector and completed draft IDs;
- the `completed-drafts-only` population selector; and
- calculation version `m2-009-v1` plus M2-001 observation and M2-002 wheel
  provenance identifiers.

The calculation is deterministic and uses no clock, provider, repository, or
persistence access. It replays existing M2-001 observations and consumes
existing M2-002 first-return wheel facts; it does not reconstruct either
projection independently.

## Scopes and values

Aggregate rows are keyed by exact Cube membership ID within the context's
CubeVersion. Different memberships remain different rows even where a future
source could describe them as the same card. The event facts in
seen-before-pick and wheel evidence retain the exact `DraftCardInstance`.

The caller must select exactly one of:

- `HumanActorScope()`: `HUMAN` at the local human seat 0;
- `BotActorScope(strategy_id, strategy_version)`: `BOT` with that exact
  recorded strategy pair; or
- `CombinedActorScope((...))`: an explicitly enumerated union of those
  selectors.

Rates expose integer numerator and denominator and an exact `Fraction` value.
Mean and median position expose their sample `n` and an exact `Fraction`.
When a rate denominator or position sample is zero, its value is `None`
(undefined), never an invented zero percent or zero pick position.

The implemented definitions are:

| Metric | Value / numerator | Denominator / sample |
|---|---|---|
| Mean and median pick | One-based selected pick positions | Selected membership events; `n` is retained |
| Pick rate | Selected membership instances | Legal M2-001 candidate appearances |
| First-pick rate | Selections at `pick_number == 0` | Candidate appearances at that position |
| Last-pick rate | Selections with one card available | Candidate appearances with one card available |
| Second-to-last rate | Selections with two cards available | Candidate appearances with two cards available |
| Seen-before-pick | Prior same-seat appearances for each selected exact instance | Selected exact-instance samples; `n` is retained |
| Wheel return rate | M2-002 first returns | Completed pass opportunities, aggregated to membership |

A completed pass opportunity is the first time a seat observes and does not
select an exact instance, followed by a later observation for that same seat
and pack round where the instance is absent. The first observation is a
seat/instance fact before actor filtering; filtering it differently would
silently redefine the approved denominator if a seat's recorded actor changes.
The numerator is only the corresponding M2-002 first return.

## Reference evidence

[`backend/tests/test_draft_metrics.py`](../backend/tests/test_draft_metrics.py)
uses deterministic, hand-checked draft histories to cover:

- pick, first, last, second-to-last, and wheel numerator/denominator facts;
- a wheel return, a completed pass that does not return, and a zero
  denominator reported as undefined;
- the standard `8 x 3 x 15` replay: human seat 0 has 45 picks, with each
  Pick 1–15 occurring in each of three rounds;
- a nonstandard `2 x 1 x 3` geometry, so late-position definitions are
  structural rather than hard-coded to 15-card packs;
- repeated appearances of one exact instance producing seen-before-pick
  counts of 0 and 2;
- distinct human, Bot strategy/version, and explicit combined populations;
- distinct CubeVersion rejection and exclusion of an incomplete history; and
- result-context provenance and distinct Cube-membership rows.

This evidence establishes semantic correctness for the defined factual
metrics. It does not establish strategic quality, card power, statistical
significance, source-wide comparisons, or a user-facing analytics product.

## Deterministic sanity replay

After the reference suite, a standalone deterministic `8 x 3 x 15` replay
with seed `20260907` completed successfully under CubeVersion
`sanity-cube-version`. Its local human scope produced 45 selected-instance
samples, positions 1–15 across rounds 1–3, 84 first-return facts, and 252
completed pass opportunities. This is an end-to-end smoke of calculation and
provenance plumbing only; it is deliberately synthetic and is not a
statistically meaningful card-performance sample.

## Explicit limitations and next boundary

M2-009 intentionally does not expose an API, persist metric snapshots, add
filters, charts, Draft Inspector behavior, Bot intelligence, archetypes, or
external data. Those consumers must preserve the result context and label
small or undefined samples. The directly unblocked follow-on is M2-010, which
can define a separate analytics consumer without changing these facts.
