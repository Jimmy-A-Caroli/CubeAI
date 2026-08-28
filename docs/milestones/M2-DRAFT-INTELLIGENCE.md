# M2 — Draft Intelligence and Analytics

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
- Suggestions decomposed into power, color openness, curve, synergy, and current-pool fit.
- Explanations and uncertainty shown with every composite recommendation.

### Review and aggregates

- Timeline review of alternatives and signals available at each pick.
- Initial average/median pick, last-pick, seen-to-pick, and wheel metrics.
- Filters for Cube version, human/bot origin, bot strategy/version, and time/run range.
- No win-rate claims before gameplay provides valid outcomes.

## Candidate issues

| ID | Outcome | Depends on |
|---|---|---|
| M2-001 | Define derived cards-seen and pick-history projections | M1-018 |
| M2-002 | Define and test wheel detection | M2-001 |
| M2-003 | Add local tracked-card behavior and UI | M2-001 |
| M2-004 | Add mana curve and color-distribution projections | M1-018 |
| M2-005 | Define mana-requirement and source-count model | M2-004 |
| M2-006 | Define versioned archetype/tag vocabulary | M1-007 |
| M2-007 | Add explainable draft-fit feature scores | M2-004, M2-006 |
| M2-008 | Build post-draft timeline review | M2-001, M2-007 |
| M2-009 | Define provenance-aware pick metric schemas | M2-001 |
| M2-010 | Build initial analytics views and filters | M2-009 |

These issues require refinement after M1 establishes actual event and API schemas.

## Exit criteria

- All displayed history can be reproduced from persisted events.
- Wheel behavior is correct for supported configurations and duplicate cards.
- Mana and archetype metrics state their definitions and limitations.
- Recommendations expose contributing features instead of claiming unexplained authority.
- Analytics default to separated origins and clearly show active filters.

## Non-goals

Optimized bots, ML, automated deck construction, large simulation orchestration, or gameplay-derived performance are not M2 requirements.
