# Bot v1 Architecture Proposal: Contextual, Deterministic, Explainable

**Status: READY FOR HUMAN DECISION.** This is an implementation-ready
conceptual proposal only. It does not accept M2-004/M2-006, implement a Bot,
authorise external data, or alter Bot v0.

## Recommendation

Adopt **Option B: a deterministic, reviewed archetype-preference model with a
time-decaying openness prior** as the proposed `contextual-v1` baseline.

It retains CubeAI's owned static rating as raw power, represents several
Cube-version-specific archetype paths simultaneously, and scores legal
candidates through a short, versioned decomposition. It independently adapts
the explainable Saxe/madrury pattern and the Draft Omen rationale-ledger
pattern; it does not reuse their code, data, matrices, or weights.

This is the recommended smallest option that directly addresses Bot v0's defect: a card's
value can change with the current pool and draft stage. It does **not** model
table signals, direct card-pair synergy, curve optimisation, or ML.

## Current repository boundary and M2 dependency map

This proposal was checked against `main` at `5ea573b`. Bot v0 receives only the
current legal candidates and an Oracle-ID raw-rating artifact. Its durable
`PickEvent` records selected-card Bot provenance, while M2-001 reconstructs
pre-pick seat-visible pack/pool context; the completion-only Inspector exposes
that factual context and M2-011 stores human review separately. None currently
stores a candidate-level Bot score ledger.

```text
M1-018
  ├─ M2-001 observations ─┬─ M2-002 wheel facts
  │                       ├─ M2-003 local tracking
  │                       ├─ M2-009 factual metrics ── M2-010 analytics views (READY)
  │                       └─ M2-012 factual Inspector ── M2-011 human review
  └─ M2-004 CardFacts (BLOCKED; decision-ready proposal exists only on a research branch)

M1-007 ── M2-006 vocabulary (BLOCKED in canonical backlog; decision-ready proposal exists only on a research branch)
M2-004 + M2-006 ── M2-007 explainable draft-fit ── M2-008 full Inspector
```

M2-004 and M2-006 are therefore design prerequisites, not current production
inputs. M2-007's planned user-facing draft-fit score is a separate scope from
this Bot strategy proposal and must not be silently satisfied by it.

## Options considered

| Option | Description | Expected behavioral improvement | Cost / rights / failure mode |
|---|---|---|---|
| A. staged colour heuristic | raw rating + early/late colour commitment thresholds | avoids some colour whiplash | low cost but misses Cube archetypes; brittle hard thresholds; low rights risk |
| **B. multi-archetype preference** | raw rating + reviewed candidate affinity + pool-derived path distribution + decaying openness | can remain open in several Cube-relevant paths, then prefer supported candidates | moderate curated-vocabulary work; no external data required; can overfit bad labels/weights |
| C. learned contextual ranker | pack, pool, stage, possibly cube representation to learned ranker | potentially highest imitation | licensed Cube data and evaluation required; opaque explanations, distribution shift, greater reproducibility burden |

Choose **B** as a design judgement. A is less likely to express Cube-specific
paths; C is a separately licensed experimental track, not a credible first
production improvement without new evidence.

## Conceptual contract

### Permitted inputs

At one decision, `contextual-v1` may read only:

- acting seat's legal `DraftCardInstance`s in the current pack;
- acting seat's prior selected pool and completed own decisions;
- immutable CubeVersion, draft configuration, pack/pick position, and strategy
  configuration;
- a pinned CubeAI-owned raw-rating artifact;
- a pinned, accepted vocabulary/assignment version and its reviewed
  candidate-to-archetype affinity records.

It must not read another seat's pool or pack, unopened/future packs, allocation
seed as a preference input, later events, review annotations, outcomes, or
provider payloads. This must be enforced by a new typed, seat-local contextual
input assembled in the application layer; the present `BotVisibleState` is
intentionally insufficient because it carries legal candidates but no pool,
CubeVersion, or strategy configuration. The strategy must never receive
`DraftState`. M2-001/M2-002 are after-draft projections useful for lawful
historical replay, not proof of a live-input safety boundary.

### State and multiple paths

Let `A` be the finite archetypes for one exact CubeVersion/vocabulary version.
State is a non-negative vector `p[a]`, not `current_archetype`. Initially all
paths receive equal declared openness. Each previously selected card contributes
only its reviewed association `affinity[d,a]`; absent/unknown association is a
visible zero contribution, never a guessed tag. A vocabulary alone does not
provide these affinities: a separately approved assignment contract must define
owner/reviewer authority, association scope, coverage, ambiguity/conflict,
versioning, and whether any negative association is allowed.

```text
pool_support[a] = sum(affinity[d,a] for d in pool)
path_state[a,t] = normalize_or_preserve_scale(pool_support[a] + openness(t))
```

`openness(t)` is a declared monotone non-increasing schedule indexed only by
the completed-pick position. It prevents a small early pool from assigning all
weight to one path. It must be recorded as configuration/version evidence,
not learned silently. Its initial shape and scale require calibration; this
proposal deliberately fixes no coefficient. Before implementation, the new
issue must choose one score normalization, affinity scale/sign, schedule owner,
and calibration authority; no "equivalent" form may be substituted silently.

### Candidate scoring and tie-break

For candidate `c` in legal pack `P`:

```text
base(c)       = pinned raw-rating value, or its declared fallback
path_fit(c)   = sum(path_state[a,t] * affinity[c,a] for a in A)
score(c)      = base(c) + declared_path_weight * path_fit(c)
```

`declared_path_weight` is a versioned configuration value, not a hidden fitted
parameter. Rank by final score; exact numeric ties use the existing stable
`DraftCardInstance.id` tie-break. Do not introduce randomness in v1.

This intentionally separates raw power from contextual fit. It does not claim
the final score is card power, expected wins, a human preference, or objective
quality.

### Explainability and frozen pick evidence

Every Bot v1 pick should preserve the full legal-candidate ledger at decision
time, including:

- strategy ID/version; feature/scoring configuration version; raw-rating
  artifact/version; vocabulary/assignment version; CubeVersion/configuration;
- legal candidate identity and order; raw rating/fallback outcome;
- the prior pool reference/snapshot identity and stage/opening schedule value;
- path-state vector and each candidate's reviewed affinity values;
- base, path-fit, final score, rank, selected flag, and deterministic tie-break;
- missing/unknown facts and terms explicitly not modelled.

This extends Bot v0 provenance; it never re-scores historical decisions using
today's taxonomy. Human annotations remain a separate provenance-bearing
observation and are not Bot input.

## What this improves and what it does not

Relative to static Bot v0, this should make a Bot prefer a somewhat weaker
candidate when its documented affinity matches several pool-supported paths,
while early openness preserves alternative paths. It should also make each such
choice inspectable as base-plus-context rather than unexplained behavior.

It does not establish that picks are stronger, more human-like, or better at
gameplay. It intentionally defers direct card-pair synergy, table-signal
inference, curve/mana/fixing adjustments, learned embeddings, training, and
simulation-scale performance conclusions.

## Evaluation plan

1. **Contract tests:** fixed synthetic Cube versions prove stable ranking,
   monotone opening behavior, exact legal-information boundary, unknown-tag
   fallback, duplicate-instance identity, and full explanation round-trip.
2. **One-step counterfactuals:** replay completed Bot v0 decision contexts;
   score the exact historical pool and legal pack with v0 and v1 side by side.
   This is valid only for that one decision; it does not claim that later picks
   would be the same after a different choice.
3. **Inspector-led calibration:** select changed/high-margin/low-margin cases;
   review with existing annotations. Compare assessment distribution, reason
   categories, and suggested-rating distribution only for the historically
   selected card to which an annotation is attached. Label small samples.
   Top-1/top-K agreement and a human rating of a changed v1 candidate require a
   separately approved counterfactual-review instrument; the current one-row
   annotation contract cannot measure them.
4. **Full counterfactual drafts:** run v0 and v1 from identical immutable Cube
   versions, configurations, and seed sets only after M4-style run identity is
   available. Different early choices create a different trajectory; never
   present this as historical replay.

Human review is calibration evidence, not training data. Do not freeze numeric
promotion thresholds before enough reviewed, representative decision contexts
exist.

## Promotion criteria and calibration procedure

`contextual-v1` must not replace v0 merely for being sophisticated. It must:

- be deterministic, complete legal drafts, preserve no-hidden-information
  boundaries, and emit a complete candidate ledger;
- retain Bot v0 unchanged and reproduce both versions from their pinned inputs;
- show reviewers enough changed and unchanged contexts to detect regressions in
  obvious raw-power picks;
- use a predeclared, stratified review set (early/mid/late picks, path-fit
  changes, high/low raw ratings, and unknown assignments);
- have a human-approved calibration target before any default switch, such as
  no material regression in review assessment and a demonstrated reduction in
  clearly unacceptable contextual misses. The threshold is a decision because
  current evidence does not justify a universal percentage.

## CubeAI implementation map

| Existing evidence/component | Proposed use | Missing before implementation |
|---|---|---|
| Bot v0 artifact and `RawRankingStrategyV0` | pinned raw-power prior and deterministic fallback/tie pattern | a new strategy, never mutation of v0 |
| immutable `PickEvent` / Bot provenance | versioned pick evidence | candidate-level explanation persistence contract |
| M2-001 observations | one-step context/replay evidence | no production signal input in v1 |
| M2-002 wheels | future, seat-visible experiment only | signal semantics/calibration |
| M2-009 metrics | factual population filters and later reporting | analytics views / comparison contract |
| Inspector + Human Review | explain/debrief/calibration | candidate-ledger Inspector projection; annotation aggregate proposal |
| M2-004 CardFacts proposal | future factual classifiers | human approval, fixtures, implementation |
| M2-006 vocabulary proposal | required reviewed affinities | human approval, assignment set, versioning, fixtures |

The present blocker is not a missing neural model. It is accepting and
implementing trustworthy, versioned Cube-specific facts/vocabulary and a
candidate-provenance contract. M2-004 and M2-006 remain blocked in the
canonical backlog; decision-ready proposals for both exist only on the current
research branch and have not been accepted. Bot v1 should therefore not begin
until an approved successor issue makes those dependencies explicit.

## Deferred experimental track (v1.1 or later)

- reviewed direct card-to-card synergy matrix;
- a strictly seat-visible table-signal/open-path model using M2-001/M2-002;
- curve, mana requirement, and fixing terms after M2-004/M2-005;
- learned contextual ranker/embeddings after a separate data-rights, evaluation,
  and reproducibility proposal;
- CubeCobraML-style models only as an experimental comparator, not a source of
  copied code/data/weights.

## Human decisions required

1. Accept or revise the M2-004 facts and M2-006 vocabulary/assignment decision
   gates before authorizing a Bot v1 issue.
2. Accept Option B as the architecture direction, including a versioned
   candidate-ledger rather than selected-score-only provenance.
3. Choose the calibration corpus/reviewer process and promotion threshold after
   a representative local review set exists; do not make annotations training
   data by default.

## Next action

**Approve or revise this Option B proposal and the prerequisite M2-004/M2-006
decision gates; do not begin Bot v1 implementation until then.**
