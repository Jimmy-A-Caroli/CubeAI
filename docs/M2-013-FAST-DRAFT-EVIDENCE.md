# M2-013 — Fast Draft Evidence

## Outcome

CubeAI can create one fully completed, deterministic local draft with exactly
eight Bot v0 seats through `POST /v1/drafts/fast`. The normal human-seat draft
path remains unchanged.

## Contract

- The command accepts the existing immutable CubeVersion and explicit draft
  geometry/seed, but rejects any geometry other than eight seats.
- All eight seats use the existing Raw Ranking Bot v0 strategy. Each resulting
  `PickEvent` therefore keeps its normal Bot actor origin, strategy reference,
  rating artifact/version, chosen rating, lookup outcome, and deterministic
  tie-break evidence.
- Allocation and every Bot choice complete before SQLite receives the draft.
  A command failure cannot persist an incomplete fast draft.
- The API derives `mode: all_bot` from immutable event provenance. It is a
  display label, not a new persisted draft identity or simulation-run model.
- The completed draft is available through the existing completion-only review,
  observation, tracking, and Draft Inspector projections. Inspector remains
  factual: it exposes what every Bot saw, had drafted, chose, and recorded
  evidence for the choice; it does not call the choice good, score alternatives,
  or infer strategy beyond that evidence.

## Explicit boundaries

This is one manually initiated local draft for human inspection. It does not
introduce batch execution, scheduled runs, a `SimulationRun` identity, metrics
aggregation, bot benchmarking, strategic explanation, or an objective claim
that Bot v0 drafts well. It is deliberately not M4 simulation work.

## Verification

- `backend`: focused local API tests prove all eight decisions are Bot-origin,
  retain Raw Ranking provenance, and reload identically after SQLite restart.
- `frontend`: import/validation test proves the Fast draft action creates an
  immediately completed `all_bot` draft and hands it to the completed-draft
  workspace/Inspector flow.
