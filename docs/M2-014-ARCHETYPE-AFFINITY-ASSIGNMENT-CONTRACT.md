# M2-014 Archetype Affinity Assignment Contract

**Status:** APPROVED. The categorical v1 labels are `none`, `supports`, and
`strong`; `unknown` remains an unreviewed state rather than a serialized
affinity. Numeric weights remain outside this artifact in a future contextual
strategy configuration. The first exact-version baseline is recorded under
[`docs/artifacts/archetype-affinities/`](artifacts/archetype-affinities/),
with no active card associations until a curator or human review supplies one.

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

## Approved affinity scale

**Approved human-facing scale:** categorical `none`, `supports`, and `strong`.
It is legible in a review diff, avoids false decimal precision, and does not
force the future strategy to use a particular coefficient. `UNKNOWN` means no
reviewed association and is never serialized as an affinity. A card may have
multiple positive `supports`/`strong` associations. All v1 affinities are
non-negative: no anti-archetype category or weight is introduced.

The alternative is a small fixed numeric scale. It would make a future scoring
implementation superficially shorter, but would prematurely embed scoring
policy in curation and make reviewer disagreement appear more precise than the
evidence warrants. Initial affinities are non-negative only: no present
evidence requires an anti-archetype label, and negative consequences can be
introduced later as explicit, explainable features.

The numeric mapping, if any, belongs to a separately versioned contextual
strategy configuration and is not decided by this contract.

## Small human-curation workflow

Run `scripts/prepare_affinity_curation.py` through the locked environment with
the public identifier, a caller-local state directory, a caller-local worklist,
and intended artifact/report paths. It imports and freezes one CubeVersion,
writes the complete source-derived worklist only outside the repository, then
emits a compact empty assignment artifact and a coverage report for review.

The reviewer uses the local worklist to add only independently reviewed
`curator_defined` or `human_annotated` records to the artifact. A card remains
`UNKNOWN` when no conclusion is ready. The reviewer reruns the command/report
against the exact stored version after editing; no provider tags, Oracle text,
or generated suggestions enter the artifact.

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
