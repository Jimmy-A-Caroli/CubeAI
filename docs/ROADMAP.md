# CubeAI Roadmap

## Delivery strategy

The roadmap follows the product loop in dependency order. Each milestone must produce a demonstrable capability and evidence that sharpens the next milestone. Detail intentionally decreases with distance: M0 and M1 are execution-ready, M2 is moderately decomposed, M3–M5 describe capabilities and spikes, and M6–M9 remain skeletons.

## Dependency overview

```text
M0 Repository Foundation
  ↓
M1 Cube Import + Local Draft MVP
  ├──→ M2 Draft Intelligence + Analytics
  │       ↓
  │     M3 Improved Draft Bots
  │       ↓
  └────→ M4 Simulation Framework / CubeLab

M0 ─────────────────────────→ M5 Gameplay Engine Feasibility
                                  ↓ decision
                                M6 Local Playable Game
                                  ↓
                                M7 Game UI Refinement
                                  ↓
                                M8 Human Multiplayer
                                  ↓
                                M9 Public Platform / Deployment
```

CubeLab milestones do not depend on adopting Forge. M5 has no code dependency on M1–M4, but it is behind a product-priority gate until M1 succeeds, unless explicitly overridden by a human. The gate controls product sequencing rather than technical feasibility: after M0, M5 may be worked deliberately when that override is recorded, and it does not block M1–M4.

## M0 — Repository Foundation

**Outcome:** A contributor can clone the repository, run documented validation, understand component boundaries, and implement focused issues through a consistent workflow.

Capabilities include validated Python and frontend toolchains, domain and UI smoke tests, formatting/linting/type checking, CI, local orchestration, fixture policy, ADR and issue conventions, and dependency/license reporting. M0 must not implement drafting.

The M0 vertical smoke slice proves connectivity, not product functionality:

```text
backend GET /health → {"status": "ok"}
frontend status view → "Backend connected"
```

Its wording and schema may change during M0-001 when the toolchains and contracts are selected. The acceptance purpose is an end-to-end connectivity proof, not a product API or draft behavior.

**Success:** One supported setup path and one aggregate validation command work from a clean clone; CI runs the same checks; architecture-import boundaries have automated enforcement; agent-safe issues can be selected from explicit dependencies.

Detailed scope: [M0 milestone](milestones/M0-REPOSITORY-FOUNDATION.md).

## M1 — Cube Import + Local Draft MVP

**Outcome:** A local user imports a supported CubeCobra Cube, understands validation problems, and completes a seeded eight-seat draft against seven Bot v0 seats through CubeUI.

Capabilities include source-contract research, identity and Cube-version models, metadata resolution, validation, deterministic pack allocation, a draft state machine, alternating pack directions, pick provenance, raw-ranking bots, SQLite persistence, a small API, and a focused draft UI.

Explicit non-goals are ML, draft advice, advanced analytics, deck construction, gameplay, Forge, multiplayer, accounts, and hosted deployment.

**Success:** A documented fixture Cube and at least one supported public Cube complete end-to-end locally; replaying the fixture with the same inputs and seed produces the same packs, bot picks, and pools.

Detailed scope: [M1 milestone](milestones/M1-LOCAL-DRAFT-MVP.md).

## M2 — Draft Intelligence + Analytics

**Outcome:** A drafter can understand what was seen, what wheeled, how the pool developed, and the basic color/curve/archetype implications during and after a draft.

Capabilities include cards-seen history, wheel detection, tracking/wish cards, color and mana views, explicit archetype tags, review timelines, and provenance-aware initial aggregates. Advice must distinguish power, openness, synergy, and deck fit rather than present a single unexplained score.

**Success:** The UI derives analysis reproducibly from immutable draft events; a user can inspect why each metric exists and filter human versus bot data.

Detailed scope: [M2 milestone](milestones/M2-DRAFT-INTELLIGENCE.md).

## M3 — Improved Draft Bots

**Outcome:** Pluggable bot strategies improve progressively and can be benchmarked against fixed scenarios without claiming to model human behavior.

Proposed progression:

1. Externalized and versioned card ratings.
2. Color preference and commitment.
3. Curve and mana-requirement awareness.
4. Archetype and synergy features.
5. Named profiles and benchmark suites.

**Success:** Strategies are reproducible, explain their scored features, and are compared over fixed Cube versions and seed sets. ML remains out of scope until data quality and licensing justify a proposal.

## M4 — Simulation Framework / CubeLab

**Outcome:** Users run reproducible draft batches and obtain reports on pick position, last-pick rate, wheels, utilization, colors, archetypes, and deck coherence.

Major capabilities include a CLI or equivalent batch entry point, seed allocation, bounded parallel execution, resumable run records, metric definitions, exportable reports, and before/after Cube-version experiments. Human and simulated data remain separate dimensions.

**Success:** Repeating a run with the same Cube, bot versions, configuration, and seeds produces equivalent events and metrics; performance is measured before parallelism is complicated.

## M5 — Gameplay Engine Feasibility / Forge Spike

**Outcome:** A written, evidence-backed decision adopts Forge, rejects it, or defines a narrowly scoped follow-up.

The spike must answer:

- Can Forge initialize and run a game without its native UI?
- Can CubeAI enumerate legal actions and submit every required action/choice?
- Can it serialize player-specific state without leaking hidden information?
- Can state and event DTOs avoid exposing Forge classes?
- Can games be seeded, replayed, and diagnosed?
- What throughput, memory, startup, and concurrency characteristics matter locally?
- Can upgrades avoid a deep permanent fork?
- What GPL-3.0 obligations arise for process, distribution, linking, and modifications?

**Success:** A throwaway prototype and research report cover representative interactions, failure modes, performance evidence, and legal review needs. Production integration is explicitly outside the spike.

## M6 — Local Playable Game

**Outcome:** Using the selected engine architecture, a local human completes a correct game against AI if feasible.

Scope includes deck loading, player-safe game state, zones, stack, priority, legal actions, targets, combat, game completion, and a correctness-first UI. Refine this milestone only after M5.

## M7 — Game UI Refinement

**Outcome:** Core gameplay becomes efficient, legible, accessible, and reviewable.

Potential scope includes battlefield layout, card interaction, stack visualization, priority stops, auto-pass, logs, replay timeline, keyboard/accessibility support, and information-density settings.

## M8 — Human Multiplayer

**Outcome:** Known users can join direct local or remote sessions, reconnect, draft with mixed human/bot seats, and play without hidden-information leakage.

Potential scope includes session transport, reconnection, player authorization, draft rooms, direct challenges, and spectators. Public matchmaking remains out of scope.

## M9 — Public Platform / Deployment

**Outcome:** Only after the local application is useful, CubeAI can be operated responsibly as a hosted service.

Potential scope includes authentication, hosted persistence, deployment, observability, privacy, abuse prevention, backup/recovery, and measured scaling. This milestone intentionally has no implementation decomposition yet.

## Cross-cutting risks

- CubeCobra contracts and historical-data availability may change or lack guarantees.
- Custom cards and ambiguous printings complicate identity resolution.
- Scryfall usage, attribution, images, and bulk-data refresh need a responsible cache design.
- Draft rating/training datasets may be unavailable or incompatibly licensed.
- Self-play analytics can amplify bot assumptions if provenance is ignored.
- Forge may not expose a stable headless control surface, and GPL implications may constrain integration.
- Multiplayer makes state visibility and event ordering security requirements rather than UI details.

These risks are tracked as research issues in the [initial backlog](issues/INITIAL_BACKLOG.md).
