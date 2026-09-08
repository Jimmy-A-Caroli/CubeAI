# M2 — Draft Intelligence and Analytics

**Current checkpoint: observation, local tracking, factual metric calculation,
and Inspector-foundation implementation.** M2-001, M2-002, M2-003, and M2-009
are complete; M2-012 and M2-013 are complete and human-reviewed. Their
event-derived decision-observation, wheel, and local tracking contracts are recorded in
[`docs/M2-001-OBSERVATION-EVIDENCE.md`](../M2-001-OBSERVATION-EVIDENCE.md)
and [`docs/M2-002-WHEEL-EVIDENCE.md`](../M2-002-WHEEL-EVIDENCE.md), and
[`docs/M2-003-TRACKING-CONTRACT.md`](../M2-003-TRACKING-CONTRACT.md). The
implemented factual metrics contract and evidence are recorded in
[`docs/M2-DRAFT-POSITION-METRICS-CONTRACT.md`](../M2-DRAFT-POSITION-METRICS-CONTRACT.md)
and [`docs/M2-009-METRICS-EVIDENCE.md`](../M2-009-METRICS-EVIDENCE.md).
The Inspector Foundation contract is recorded in
[`docs/M2-012-DRAFT-INSPECTOR-FOUNDATION.md`](../M2-012-DRAFT-INSPECTOR-FOUNDATION.md).
The bounded all-Bot fast-draft contract is recorded in
[`docs/M2-013-FAST-DRAFT-EVIDENCE.md`](../M2-013-FAST-DRAFT-EVIDENCE.md).
M2-010 remains ready as a separate metrics-only analytics consumer. The closed
M2-006 `vintage-cube-archetypes-v0` vocabulary is accepted. Its separate
M2-014 affinity-assignment contract has an approved categorical scale and an
exact-version all-UNKNOWN curation baseline; it awaits reviewed card
associations. The remaining M2-004 projections/API/UI dependency also remains.
The CardFacts
foundation is implemented, including explicit partial/deferred face and layout
semantics, but it is not a mana-curve or color-distribution implementation.
Other later
M2 candidate issues remain blocked until their declared dependencies and
refinement are complete.

## Goal

Make a draft understandable during and after play while preserving the distinction between observation, heuristic advice, and empirical performance.

## Capability groups

### Event-derived history

- Derive every pack seen by a seat from immutable draft events.
- Display ordered pick history and pack contents at each decision.
- Detect cards that return to the same seat and define wheel semantics for configurable seat counts.
- Allow locally tracked cards without changing draft truth.

### Pool shape

- Mana-value curve with a documented treatment of lands, split/adventure/modal cards, and alternate costs.
- Color counts, color identity, castability-related mana requirements, and source counts as separate concepts.
- User-controlled inclusion/exclusion for likely sideboard cards before automatic deck construction exists.

### Archetypes and suggestions

- Versioned tags with source and confidence.
- Archetype support views based on explicit features.
- The accepted `vintage-cube-archetypes-v0` names roles and strategic paths;
  only a separately reviewed, exact-CubeVersion M2-014 assignment set may
  connect a membership or CardIdentity to a path. Provider tags remain inactive
  evidence, and unreviewed is not explicit `none`.
- Suggestions decomposed into power, color openness, curve, synergy, and current-pool fit.
- Explanations and uncertainty shown with every composite recommendation.

### Review and aggregates

- M2-012 **Draft Inspector Foundation**: a usable post-draft factual replay of cards seen, chosen card, prior pool, legal alternatives, exact-instance wheel/seen facts, and recorded Bot v0 evidence.
- M2-013 **Fast Draft**: one manually initiated eight-Bot v0 draft completed locally for factual Inspector review, not a batch simulation or quality claim.
- The later full **Draft Inspector** (M2-008): adds active strategy contributions, alternative scores, and derived color/curve/archetype context only after M2-007.
- Lightweight human review annotations remain a separate provenance-aware layer and never mutate draft truth.
- Initial average/median pick, last-pick, seen-to-pick, and wheel metrics.
- Filters for Cube version, human/bot origin, bot strategy/version, and time/run range.
- No win-rate claims before gameplay provides valid outcomes.

## Candidate issues

| ID | Outcome | Depends on | State |
|---|---|---|---|
| M2-001 | Define derived cards-seen and pick-history projections | M1-018 | COMPLETE |
| M2-002 | Define and test wheel detection | M2-001 | COMPLETE |
| M2-003 | Add local tracked-card behavior and UI | M2-001 | COMPLETE |
| M2-004 | Add mana curve and color-distribution projections | M1-018 | IN PROGRESS — CardFacts foundation complete; projections/API/UI remain |
| M2-005 | Define mana-requirement and source-count model | M2-004 | BLOCKED |
| M2-006 | Define versioned archetype/tag vocabulary | M1-007 | COMPLETE |
| M2-014 | Define archetype affinity assignment contract | M2-004, M2-006 | IN PROGRESS — scale approved; first exact-version baseline has zero reviewed associations |
| M2-007 | Add explainable draft-fit feature scores | M2-004, M2-006, M2-014 | BLOCKED |
| M2-008 | Build post-draft Draft Inspector and timeline review | M2-001, M2-007 | BLOCKED |
| M2-009 | Define provenance-aware pick metric schemas | M2-001 | COMPLETE |
| M2-010 | Build initial analytics views and filters | M2-009 | READY |
| M2-011 | Add lightweight human pick-review annotations | M2-012 | COMPLETE |
| M2-012 | Build factual Draft Inspector Foundation | M2-001, M2-002, M2-009 | COMPLETE |
| M2-013 | Add an inspectable eight-Bot fast draft | M1-013, M1-014, M1-015 | COMPLETE |

These issues require refinement after M1 establishes actual event and API schemas.

The Draft Inspector is a replay/inspection tool rather than a text-only timeline. M2 annotations may label a decision Reasonable, Debatable, or Bad, with optional reason categories (power, color commitment, curve, synergy, archetype fit, fixing, narrow payoff, or other) and a note. Each annotation identifies its author/source, Cube version, draft, seat, pick, strategy/version, and configuration. An annotation is a review observation, not objective ground truth or a training-data pipeline.

## Exit criteria

- All displayed history can be reproduced from persisted events.
- Wheel behavior is correct for supported configurations and duplicate cards.
- Mana and archetype metrics state their definitions and limitations.
- Recommendations expose contributing features instead of claiming unexplained authority.
- Analytics default to separated origins and clearly show active filters.

## Non-goals

Optimized bots, ML, automated deck construction, large simulation orchestration, or gameplay-derived performance are not M2 requirements.
