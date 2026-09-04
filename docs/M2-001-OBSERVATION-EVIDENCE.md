# M2-001 observation-projection evidence

## Decision

**M2-001 is COMPLETE.** CubeAI now derives ordered post-draft decision
observations from a draft's immutable allocation and pick-event history. This
is an observation foundation, not an analytics platform, an Inspector UI, or a
Bot strategy change.

## Projection contract

`derive_draft_observations(state)` is a pure application-layer replay of a
`DraftState`. For each recorded pick, it reconstructs the legal current pack
and the acting seat's pool immediately before that pick. Each observation
contains:

- the ordered recorded event: sequence, seat, pack, pick, actor origin and
  actor identifier;
- the chosen `DraftCardInstance`;
- `cards_seen`, in the exact legal-pack order at that moment;
- `pool_before`, in that seat's prior pick-event order; and
- the recorded Bot provenance when and only when the actor is a Bot.

Replay starts from the immutable allocation and applies each original event
through the same legal transition function. It validates active-seat, pack,
pick-number, candidate membership, and final replay equivalence before
returning observations. It neither mutates persisted state nor queries a
provider, clock, random source, CubeCobra, or Scryfall.

Distinct `DraftCardInstance` and Cube membership identities remain distinct,
including memberships that later resolve to the same printing or Oracle card.
The completed-draft API additionally supplies draft-instance, Cube-membership,
printing, and Oracle identifiers so downstream analysis can preserve those
layers rather than infer them from names.

## API and information boundary

`GET /v1/drafts/{draft_id}/observations` exposes chronological decision
contexts only after draft completion. Before completion it returns the stable
`DRAFT_OBSERVATIONS_UNAVAILABLE` error and exposes no other-seat current packs,
private pools, future allocation, or future events.

The endpoint returns evidence rather than advice: cards seen, pool before,
chosen card, actor, and recorded Bot v0 strategy/artifact/rating/lookup/tie-break
provenance. A human event has no inferred strategy or reasoning.

## Scope and deferred work

No persistence schema, source adapter, metadata provider policy, Bot v0
behavior, UI Inspector, annotation system, metric, wheel calculation,
archetype, deck model, simulation batch, gameplay, authentication, or hosted
service was added. M2-002 onward remain blocked pending their declared
dependencies and refinement.

## Verification

On the implementation branch, the following commands passed:

```powershell
uv --directory backend run --locked pytest -q tests
uv --directory backend run --locked ruff format --check .
uv --directory backend run --locked ruff check .
uv --directory backend run --locked mypy --strict src
uv --directory backend run --locked lint-imports
uv --directory backend build

corepack npm --prefix frontend run format:check
corepack npm --prefix frontend run lint
corepack npm --prefix frontend run typecheck
corepack npm --prefix frontend test
corepack npm --prefix frontend run build
```

Results: backend `229 passed, 1 deselected`; frontend `4` Vitest files / `16`
tests passed; Ruff, strict mypy (29 source files), and the one Import Linter
contract passed; backend source distribution/wheel and frontend production
build completed. The backend build's sandboxed attempt could not reach PyPI for
Hatchling; the unmodified build passed on the authorized retry. `git diff
--check` also passed.

An independent focused review checked deterministic replay, duplicate identity,
actor/Bot provenance, information boundaries, layer separation, and needless
abstraction. It found and the implementation resolved two issues before final
validation: the observation now carries its chosen instance directly, and the
API regression proves that two memberships with the same printing/Oracle
identity remain distinct in both cards-seen and pick history.
