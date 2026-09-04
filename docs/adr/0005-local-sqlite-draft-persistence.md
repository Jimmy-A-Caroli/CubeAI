# ADR-0005: Use local SQLite snapshots and append-only draft histories

- **Status:** Accepted
- **Date:** 2026-09-03

## Context

M1-014 needs a small durable boundary for immutable Cube versions and active
drafts so a local application can resume after restart. The persistence layer
must preserve instance identity and human/Bot provenance without introducing
SQL models into the CubeLab domain or committing a human pick separately from
the resulting consecutive Bot turns.

ADR-0003 already accepts standard-library `sqlite3` with SQLite 3.37 or newer
as the available local persistence capability.

## Decision

Use an explicit CubeLab repository port with a standard-library SQLite adapter.
The adapter requires SQLite 3.37+ and uses `STRICT` tables with a small,
versioned migration ledger.

Persist a canonical immutable CubeVersion snapshot, immutable draft geometry
and allocation payload, and an append-only ordered pick-event payload. Existing
CubeVersion snapshots and draft initial payloads cannot change; a later write
may only retain the saved event prefix and append new legal events.

The repository transaction port loads a persisted draft and its CubeVersion,
applies one application transition, validates the result, and saves it under a
single SQLite `BEGIN IMMEDIATE` transaction. The M1 command service uses this
boundary for a human pick plus consecutive configured Bot turns.

## Consequences

- SQLite types, schema details, JSON payloads, and migrations stay in the
  adapter; CubeLab domain values remain framework- and storage-independent.
- Allocation memberships are checked against the persisted CubeVersion before
  a draft is saved; rehydration replays events through the existing legal
  transition function and retains actor, strategy, rating-artifact, and
  tie-break provenance.
- Re-importing equivalent immutable source/card content reuses the persisted
  snapshot rather than attempting to overwrite it. A local display-label
  change and a later resolution retrieval timestamp are not source content and
  cannot invalidate an existing draft; the first snapshot retains its original
  resolution provenance. A difference in immutable source content still
  reaches the repository's `PERSISTENCE_CONFLICT` guard.
- The database path is caller-selected local state. PostgreSQL, cloud backup,
  cross-device synchronization, analytics storage, and background migration
  services remain out of scope.
- A future schema change must be a new migration with restart and upgrade
  coverage. A persistence strategy change requires a new decision record.

## Revisit when

Revisit only when a demonstrated product need requires shared, remote, large
archive, or materially concurrent draft storage. Any replacement must preserve
the current identity, visibility, deterministic replay, and append-only event
requirements.
