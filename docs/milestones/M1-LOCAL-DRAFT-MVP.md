# M1 — Cube Import and Local Draft MVP

## Goal

A user supplies a supported CubeCobra URL or identifier, receives actionable validation, and completes a deterministic local eight-seat draft against seven raw-ranking bots.

## End-to-end slice

```text
CubeCobra contract research
  → source-preserving import
  → card identity and metadata resolution
  → immutable Cube version + validation
  → seeded pack allocation
  → draft state machine
  → Bot v0 strategy
  → persistence and API
  → import/validation/draft UI
  → reproducible acceptance scenario
```

## Exit criteria

- The supported CubeCobra contract and limitations are documented with sanitized fixtures.
- Oracle identity, printing, Cube membership, and draft instance are distinct.
- Duplicate entries and unresolved/custom cards receive explicit behavior.
- A configuration supports seat count, packs per seat, pack size, and seed; the UI initially defaults to 8/3/15.
- Allocation never duplicates a Cube-card instance unless the Cube version contains duplicate memberships.
- Packs rotate in alternating directions and every legal pick appears exactly once in one seat's pool.
- Bot v0 uses a versioned raw ranking with deterministic tie-breaking.
- Human and bot picks retain actor and strategy provenance.
- Draft state persists locally and survives a supported application restart.
- A focused UI completes the workflow without analytics or gameplay.
- A fixed fixture and seed reproduce packs, picks, and pools end to end.

The M1 draft UI is a functional, clean, intentionally simple visual foundation that can be reused by later inspection views. Current-pack, chosen-card, drafted-pool, seat, pack-number, and pick-number components should be structured as stable replayable views. This is a reuse constraint, not an M1 requirement for analytics, human annotation, advanced review, or visual polish.

## Detailed work packages

| ID | Outcome | Depends on | State |
|---|---|---|---|
| M1-001 | Research and freeze the supported CubeCobra import contract | M0-008 | COMPLETE |
| M1-002 | Model card identity, printing, Cube, version, and membership | M0-002 | COMPLETE |
| M1-003 | Define import candidates, diagnostics, and adapter port | M1-001, M1-002 | COMPLETE |
| M1-004 | Implement the CubeCobra read adapter against fixtures | M1-003 | COMPLETE |
| M1-005 | Research and define Scryfall metadata/cache policy | M0-009 | COMPLETE |
| M1-006 | Define metadata resolver port and Scryfall adapter | M1-002, M1-005 | COMPLETE |
| M1-007 | Assemble immutable Cube versions with diagnostics | M1-004, M1-006 | COMPLETE |
| M1-008 | Validate Cube contents and draft capacity | M1-007 | COMPLETE |
| M1-009 | Define draft configuration, instances, seats, packs, and picks | M1-002 | COMPLETE |
| M1-010 | Allocate deterministic packs | M1-008, M1-009 | COMPLETE |
| M1-011 | Implement draft state transitions and pack rotation | M1-010 | COMPLETE |
| M1-012 | Define bot strategy port and Bot v0 rating policy | M1-009 | COMPLETE — `70d621f`; reviewed CubeAI-owned artifact and strategy port |
| M1-013 | Execute deterministic bot turns | M1-011, M1-012 | COMPLETE — `543e8a6`; reviewed deterministic bot turns |
| M1-014 | Persist Cube versions and drafts in SQLite | M1-007, M1-013 | READY |
| M1-015 | Expose import, validation, draft command, and view APIs | M1-008, M1-013, M1-014 | BLOCKED |
| M1-016 | Build Cube import and validation UI | M1-015, M0-005 | BLOCKED |
| M1-017 | Build pack, pick, and drafted-pool UI | M1-015, M0-005 | BLOCKED |
| M1-018 | Verify end-to-end deterministic local draft | M1-016, M1-017 | BLOCKED |

Full issue definitions are in [the initial backlog](../issues/INITIAL_BACKLOG.md).

## Functional constraints

- The domain accepts configurable draft geometry even though the first UI targets standard eight-seat, three-pack, fifteen-card drafts.
- The same Cube membership cannot appear twice in allocated packs. Duplicate card names are valid when represented by distinct memberships.
- Source payloads and unresolved values never become domain truth without a visible resolution state.
- Draft views must be shaped so future multi-seat visibility can be enforced; M1 does not implement networking.
- Bot ratings are data with an explicit source and license, not magic constants scattered through code.

## Non-goals

Draft advice, cards-seen analysis, wheel detection, archetypes, deck building, ML, simulation batches, games, Forge, multiplayer, accounts, and hosting are excluded.
