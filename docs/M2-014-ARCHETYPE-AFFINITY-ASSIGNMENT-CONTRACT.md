# M2-014 Archetype Affinity Assignment Contract

**Status:** READY FOR HUMAN DECISION on the proposed categorical affinity
scale; validation and coverage machinery are implemented but no real Cube
assignment set is accepted.

**Dependencies:** M2-004, M2-006

## Purpose and non-goals

An assignment set is the reviewed, versioned bridge from a Cube membership or
CardIdentity to an approved archetype path. It is not CardFacts, a role
assignment, a Bot coefficient, a human pick review, or an automatic tagger.
No Oracle-text, color, source-tag, rating, external matrix, or model inference
may create an active association.

This contract adds no contextual Bot behavior: no pool support, openness,
path-state, path-fit, score, selection, candidate ledger, signals, synergy,
curve, fixing, color commitment, or ML.

## Versioned JSON artifact

The human-reviewable artifact is a small, ordered JSON file. JSON matches the
repository's existing synthetic/contract fixtures, requires no dependency, and
keeps reviewed diffs deterministic. A future imported Cube may generate a
local worksheet from its exact `CubeVersion`, but no provider list or real
Vintage Cube assignment data is committed here.

Each artifact contains:

- immutable assignment-set `id`, `cube_version_id`, and `vocabulary_version`;
- records with `target_id`, explicit `identity_scope`, `archetype`,
  `support_level`, `provenance`, review status, and optional note;
- one record at most for one `(target_id, identity_scope, archetype)` tuple.

`identity_scope` is exactly `cube_membership` or `card_identity`. Validation
checks the exact `CubeVersion` and verifies each target exists in the declared
scope. A CardIdentity assignment may intentionally cover duplicate Cube
memberships; it does not turn those memberships into the same identity.

## Review, provenance, and missingness

The minimum review lifecycle is `proposed`, `reviewed`, and `active`.
`active` requires `curator_defined` or `human_annotated` provenance. Other
provenance categories are representable as evidence, but remain inactive.

`none` is an explicit reviewed conclusion for one target/archetype pair.
`unknown` / `unreviewed` is represented by no reviewed assignment for that
pair or membership. It is never serialized as `none`, and coverage reports it
separately. A future strategy may operationally use no contribution for an
unknown value, but its candidate ledger must preserve the difference from an
explicit `none` conclusion.

The validator permits overlapping CardIdentity and membership assignments so
that evidence remains visible. Coverage reports a membership as ambiguous when
reviewed records for the same archetype disagree on support level; it never
chooses an implicit precedence or creates an override.

## Affinity scale: one recommendation requiring approval

**Recommended human-facing scale:** categorical `none`, `supports`, and
`strong`. It is legible in a review diff, avoids false decimal precision, and
does not force the future strategy to use a particular coefficient. The
numeric mapping, if any, belongs to a separately versioned contextual strategy
configuration and is not decided by this contract.

The alternative is a small fixed numeric scale. It would make a future scoring
implementation superficially shorter, but would prematurely embed scoring
policy in curation and make reviewer disagreement appear more precise than the
evidence warrants. Initial affinities are non-negative only: no present
evidence requires an anti-archetype label, and negative consequences can be
introduced later as explicit, explainable features.

**Human decision required:** approve the categorical v0 support-level labels
and defer any numeric mapping to the contextual strategy configuration.

## Validation and coverage

`cubeai.lab.domain.archetypes` validates identity scope, exact CubeVersion
binding, known vocabulary keys, active-provenance policy, and duplicate record
keys. Its deterministic coverage report exposes:

- total, reviewed, and unreviewed memberships;
- explicit reviewed `none` records;
- reviewed non-`none` membership coverage for every archetype;
- multi-archetype memberships;
- source provenance counts; and
- overlapping reviewed-record disagreement counts.

Coverage reports curation state, not tag quality or a required minimum. The
synthetic fixture at
[`fixtures/synthetic/archetype-affinity-assignment-v0.json`](../fixtures/synthetic/archetype-affinity-assignment-v0.json)
demonstrates strong, multi-path, explicit-none, unreviewed, provenance,
exact-version, scope, and duplicate-membership behavior without asserting an
opinion about a real card.

## Future dependency chain

```text
M2-004 CardFacts ─┐
                  ├─> M2-014 assignment contract ─> reviewed assignment set
M2-006 vocabulary ┘                                      │
                                                         v
                                            contextual-v1 scoring contract
                                                         │
                                                         v
                                             contextual-v1 implementation
```

M2-007 is not redefined by this issue. Its existing draft-fit scope remains
blocked until its dependencies and the required contextual scoring contract
are ready. Bot v0 remains the unchanged reproducible baseline.
