# M2-012 — Draft Inspector Foundation

## Status

**IMPLEMENTED — AWAITING HUMAN REVIEW.** This issue is a deliberately narrow
factual inspection surface, authorized separately from M2-010, M2-008, and
M2-011. It does not redefine M2-010 as an Inspector or advance human review
annotations.

## Goal

For one completed local draft, let a human inspect each recorded decision and
answer only these factual questions:

- what did this seat see;
- what had the seat already drafted;
- what did it choose;
- which legal alternatives were present;
- what Bot v0 evidence was recorded for a Bot choice; and
- which exact-instance seen-before-pick and wheel facts are available.

The user can navigate decisions chronologically. The UI initially opens the
first Bot decision when one exists, while preserving human decisions in the
same ordered record.

## Inputs and contract

The completion-gated `GET /v1/drafts/{draft_id}/inspector` projection consumes
only existing deterministic foundations:

- M2-001 `derive_draft_observations` for cards seen, selected card, pool
  before, event order, seat, and actor identity;
- M2-002 `derive_wheel_observations` for first-seen/returned wheel facts; and
- M2-009 `derive_draft_metrics` for the frozen exact-instance
  seen-before-pick count.

The response carries both one-based `round_number` / `pick_number` and an
explicitly labelled one-based `physical_pack_number`. The latter is technical
provenance, never a substitute for the draft round. Bot evidence is the
recorded strategy/version, selected rating, rating artifact/version, lookup
outcome, and tie-break reason. The Inspector does not recreate Bot reasoning
or calculate alternative scores that were not recorded.

The endpoint is available only after completion, uses no provider call or new
persistence, and does not expose active-draft hidden information. It is a
read-only projection over existing immutable state.

## Explicit exclusions

M2-012 does **not** implement draft-fit explanations, archetypes, color/curve
analysis, advice, alternative ratings, strategic scoring, predictions,
metrics dashboards, annotation creation, annotation storage, or training data.
An explanation of what another human thinks remains M2-011 and is unchanged.

M2-010 remains the separate, metrics-only analytics consumer. M2-008 remains
the blocked full Inspector that can add draft-fit/archetype-derived context
only after M2-007. M2-012 therefore depends on M2-001, M2-002, and M2-009,
not M2-007, because it consumes only their existing factual outputs.

## Verification boundary

The implementation adds API and browser regression coverage for completion
gating, chronological factual context, selected-card membership, explicit
round/physical-pack vocabulary, Bot v0 provenance, absence of alternative
scoring/annotations, and the human-readable Inspector workflow. Full
repository validation has passed:

- backend: `252 passed, 1 deselected`;
- frontend: four Vitest files / `19 passed`;
- backend Ruff format/check, strict mypy, and Import Linter passed;
- frontend format check, lint, typecheck, and production build passed; and
- backend source-distribution and wheel build passed on the authorized network
  retry required for Hatchling.

The Inspector-specific API test includes an exact-instance return scenario:
one card is seen, passed, absent, returned, and selected. It proves that the
endpoint carries M2-002 first-seen/returned facts and the M2-009
`seen_before_pick_count` of one. No live provider or external fixture is used.
