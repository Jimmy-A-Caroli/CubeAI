# M2-002 wheel-detection evidence

## Decision

**M2-002 is COMPLETE.** CubeAI now derives first-return wheel facts from the
ordered M2-001 decision-observation projection. A wheel is an observed return,
not a signal, recommendation, quality judgment, or Bot adjustment.

## Formal semantics

For one seat and one specific `DraftCardInstance`, a first-return wheel exists
only when all of the following are true:

1. the seat legally saw the instance and did not choose it;
2. at a later decision for that same seat, the instance was absent, proving it
   left that seat's available pack; and
3. at a still later decision, that same seat legally saw the same instance
   again.

The projection emits at most one fact for each `(seat, DraftCardInstance)`
pair: its first verified return. This is the smallest result needed for the
M2-002 question, “did this instance return?”, and intentionally does not define
a wheel count or strategic significance for any further return in unusual
geometries.

Each `WheelObservation` contains the seat, exact draft identity and instance
ID, and first seen/returned event, pack, and pick positions. It consumes the
existing ordered observations and does not reimplement allocation/pass-direction
topology, replay draft events, write persistence, call providers, use a clock,
or use randomness.

## Identity and visibility

Wheel identity is the complete `DraftCardInstance` value: both draft ID and
draft-card instance ID. Names, Oracle IDs, printing IDs, and Cube membership
IDs are not grouping keys. Two instances that share a logical identity—or a
textual instance ID from separate drafts—cannot produce a false wheel merely
because a seat first saw one and later saw the other.

The derivation is an application-layer pure function and has no API or UI
surface in M2-002. Existing active-draft seat-safe views are unchanged.

## Verification

Focused deterministic scenarios cover:

- a two-seat, three-card pack where seat 0 saw
  `wheel-draft:card:0:2` at sequence 0 / pack 0 / pick 0 and saw the same
  instance return at sequence 4 / pack 0 / pick 2;
- alternating left/right rounds in a three-seat, two-pack, four-card geometry;
- selected and once-seen instances that must not wheel;
- duplicate logical identities represented by distinct draft instances;
- identical textual instance IDs belonging to different drafts;
- first-return-only behavior, seat isolation, determinism, immutability, and
  rejection of unordered input.

Validation passed on the implementation branch:

- `uv run --project backend pytest backend/tests/test_wheel_observations.py backend/tests/test_draft_observations.py backend/tests/test_draft_state.py -q` — 23 passed;
- `uv run --project backend ruff format --check backend/src backend/tests` — 54 files already formatted;
- `uv run --project backend ruff check backend/src backend/tests` — passed;
- `uv run --project backend mypy --strict backend/src` — 30 source files, no issues;
- `uv run lint-imports` from `backend/` — 51 files / 149 dependencies, one contract kept; and
- `uv run pytest -q` from `backend/` — 236 passed, 1 deselected.

Independent review caught and the final regression suite covers the full draft
identity requirement: a shared textual instance ID from a separate draft is not
a return.

## Scope boundary

M2-002 does not infer archetypes, colors, signals, pick quality, optimal picks,
or future Bot changes. It does not add a dashboard, Inspector, metric store,
external dataset, or persistence schema.
