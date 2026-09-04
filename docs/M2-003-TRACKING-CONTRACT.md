# M2-003 local tracking and observation-stability contract

## Status and purpose

**M2-003 is COMPLETE.** This document records the smallest local-tracking
contract that preserves observation identity across restart, database restore,
and deterministic replay. It adds a local preference only; it does not redesign
draft persistence or add an analytics store.

The existing draft record is already sufficient to reconstruct factual draft
observations. M2-003 must add a separate local preference that can join those
facts; it must never amend, duplicate, or become input to the draft history.

```text
immutable allocation + ordered pick events
                 |
                 v
       DraftState -> observation / wheel projections
                 ^
                 |
  local tracking preference joins by exact draft-card instance
```

## Current factual reconstruction boundary

The SQLite draft record currently persists the following canonical inputs:

| Layer | Durable inputs that must remain intact | Why they matter |
|---|---|---|
| Immutable CubeVersion | version ID, content fingerprint, ordered distinct Cube memberships, and their printing/Oracle/source layers | Resolves the membership behind a draft-card instance without collapsing duplicates. |
| Draft initial record | draft ID, CubeVersion ID, geometry, seed, ordered packs, pack owners, and each `(draft_id, instance_id, cube_card_id)` allocation | Establishes the complete draft-local instance namespace and initial visible geometry. |
| Event history | append-only ordered `PickEvent` values: sequence, seat, pack, pick, chosen instance, actor origin/ID, strategy reference, and Bot provenance | Replays legal decisions and preserves provenance. |

`DraftState` active packs and pools, M2-001 decision observations, and M2-002
wheel facts are **deterministically derived** from those inputs. They must not
be stored as competing snapshots or caches for M2-003. Card names, image URLs,
printing IDs, Oracle IDs, and Cube membership IDs are display or identity
layers, but none substitutes for a draft-card instance target.

Existing rehydration already starts from the persisted allocation, replays the
ordered event prefix through the legal transition, and rejects a result that
does not exactly match the saved event. Existing CubeVersion and event-prefix
conflict checks remain mandatory prerequisites of this contract.

## Proposed tracking value and identity

A local marker identifies one exact card as seen by one seat in one draft:

```text
DraftTrackingTarget = (draft_id, observer_seat, card_instance_id)
```

`draft_id` plus `card_instance_id` is the exact `DraftCardInstance` namespace;
the observer seat is required because the same physical instance may be seen
by more than one seat. `cube_card_id` is verified through the allocation but
is deliberately not part of the marker key. Names, printings, and Oracle IDs
must never group, retarget, or deduplicate markers.

The M2-003 value is a binary local preference: the tuple is present when
tracked and absent when untracked. There is no score, tag, note, timestamp,
global user identity, recommendation, or automatic transfer to another draft.
The marker is not a PickEvent, annotation, Bot input, or analytical fact.

## Required operations and validation

The implementation should expose a transport-neutral application port with
the equivalent of `track`, `untrack`, and `list_tracked` for a draft/observer
seat. The frontend must use that port/API boundary; it must not make browser
storage an independent authority for tracked state.

Before a `track` write succeeds, the application layer must load the current
rehydrated `DraftState` and validate all of the following:

1. the draft exists and `observer_seat` is within its persisted geometry;
2. the allocation contains exactly one instance matching the supplied
   `(draft_id, card_instance_id)` and its membership exists in the persisted
   CubeVersion; and
3. the observer legitimately saw the instance: it is in that human seat's
   currently legal pack, or it occurs in a derived M2-001 `cards_seen` context
   for that seat.

Writes must be idempotent: tracking an already tracked target and untracking
an absent target produce the requested state without creating duplicate rows.
An invalid, cross-draft, cross-seat, or never-seen target must fail with a
diagnosable error and must not change the preference or draft history.

The initial UI may show the marker beside a card only where that card is
already visible through the seat-safe active-draft view or the allowed
post-draft observation view. A marker must not reveal allocation, an
opponent's current pack, another seat's live pool, or future events.

## Proposed durable representation

The approved implementation is a separate versioned SQLite `STRICT` table,
added by migration 2 and owned by the local-preference repository port:

```text
draft_tracking(
  draft_id TEXT NOT NULL,
  observer_seat INTEGER NOT NULL,
  card_instance_id TEXT NOT NULL,
  PRIMARY KEY (draft_id, observer_seat, card_instance_id),
  FOREIGN KEY (draft_id) REFERENCES drafts(id)
)
```

The adapter must validate geometry, allocation membership, and seen evidence
through the rehydrated draft rather than denormalizing those values into this
table. Its write transaction must not weaken the existing immutable
CubeVersion, immutable initial payload, or append-only event-prefix guards.
If a stored marker cannot be resolved after loading a valid draft, the tracking
read must raise a dedicated local-preference persistence error; it must not
silently retarget by name or delete the marker. The immutable draft itself
remains resumable because the marker is not part of draft truth.

The caller-selected SQLite database path is the local preference scope. A
database restore recreates exactly the preferences contained in that backup;
it does not promise recovery of changes made after the backup. Browser-only
storage, cross-device synchronization, shared accounts, export/import of
preferences, and cloud backup are out of scope.

## Restart and replay guarantees

For an unchanged database, restart must produce the same allocation, event
history, `DraftCardInstance` identities, M2-001 observation identities, and
M2-002 wheel facts as before restart. A tracking marker must resolve to the
same `(draft_id, observer_seat, card_instance_id)` after restart, whether the
instance was picked, passed, removed from that seat's current pack, or later
returned.

For a restored database, the same guarantee applies to the exact backup
contents after required schema migrations. Re-importing a Cube, creating a new
draft from an equivalent CubeVersion, changing display metadata, or allocating
again with the same seed does **not** transfer markers: it creates a separate
draft-instance namespace.

Event replay may recompute observations and wheels, but neither projection may
read tracking markers or write them back into events. A future change to the
event or allocation persistence schema must preserve legal replay equivalence
through a migration or report an explicit persistence failure; it must not
silently reinterpret a tracked target.

## Required implementation tests

The eventual M2-003 implementation must add small synthetic, offline tests
for at least the following:

1. track/untrack idempotence and uniqueness for two distinct draft instances
   sharing a name, printing, or Oracle ID;
2. active-seat visibility validation, including rejection of a card from an
   unseen seat or a different draft;
3. persistence through repository reopen and application restart, with equal
   observation identifiers and wheel facts before and after restart;
4. restored-copy replay: the backup's tracked marker, observations, and wheels
   resolve identically after rehydration;
5. a tracked card that is picked, passed away, or returns as a wheel remains
   the same marker and does not mutate the derived fact; and
6. corruption/dangling-marker handling that is diagnosable without mutating
   the immutable draft record.

All fixtures remain CubeAI-authored, synthetic, fixed-order, and offline under
the fixture/test-data policy.

## Approved decisions and implementation surface

The approved owner is only the local human seat, currently seat 0. Bot-seat
histories never own a marker, even after completion. The caller-selected SQLite
database is the authoritative local preference store; browser storage is not a
second authority.

The transport surface is intentionally small and local:

- `GET /v1/drafts/{draft_id}/tracking` lists exact tracked instance IDs;
- `PUT /v1/drafts/{draft_id}/tracking/{card_instance_id}` tracks one visible
  local-human instance; and
- `DELETE /v1/drafts/{draft_id}/tracking/{card_instance_id}` untracks that
  same valid local-human instance.

CubeUI presents accessible Track/Untrack controls only beside cards already in
the local human's current legal pack or pool. It renders no technical IDs and
does not expose other seats' live information.

## Verification

The implementation uses synthetic, offline scenarios for duplicate logical
identities, active-seat visibility, idempotent removal, corruption reporting,
SQLite migration, application restart, rehydrated observations, and derived
wheels. Focused backend verification passed:

```powershell
uv --directory backend run --locked pytest -q tests/test_draft_tracking.py tests/test_sqlite_drafts.py tests/test_local_api.py tests/test_draft_observations.py tests/test_wheel_observations.py
```

Result: `38 passed`. The frontend regression verifies that tracking a duplicate
display-name card sends its exact instance ID and restores the visual marker.

No new ADR, provider, dependency, authentication model, or general persistence
redesign was required. Later M2 analytics and Inspector work remain separate.
