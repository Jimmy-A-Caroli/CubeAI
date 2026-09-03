"""SQLite adapter for immutable Cube snapshots and append-only draft events."""

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path

from cubeai.lab.application.repositories import DraftTransaction
from cubeai.lab.domain.allocation import AllocatedPack
from cubeai.lab.domain.cube import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    ResolutionStatus,
    SourceReference,
)
from cubeai.lab.domain.draft import (
    ActorOrigin,
    BotDecisionProvenance,
    BotTieBreakReason,
    Draft,
    DraftCardInstance,
    DraftConfiguration,
    DraftPack,
    PickEvent,
    RatingLookupOutcome,
)
from cubeai.lab.domain.draft_state import (
    DraftState,
    DraftTransitionError,
    pick_card,
    start_draft,
)


class PersistenceError(ValueError):
    """A durable snapshot cannot be safely stored or rehydrated."""


class PersistenceConflict(PersistenceError):
    """An immutable snapshot or prior event history was changed."""


_MIGRATIONS: tuple[tuple[int, str], ...] = (
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        ) STRICT;
        CREATE TABLE IF NOT EXISTS cube_versions (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL
        ) STRICT;
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            cube_version_id TEXT NOT NULL,
            initial_payload TEXT NOT NULL,
            events_payload TEXT NOT NULL,
            FOREIGN KEY(cube_version_id) REFERENCES cube_versions(id)
        ) STRICT;
        """,
    ),
)


class SQLiteDraftRepository:
    """A local SQLite repository with a deliberately compact schema boundary."""

    def __init__(
        self,
        database_path: Path,
        *,
        before_commit: Callable[[], None] | None = None,
    ) -> None:
        if not isinstance(database_path, Path):
            raise ValueError("database_path must be a Path")
        if sqlite3.sqlite_version_info < (3, 37, 0):
            raise PersistenceError("SQLite 3.37 or newer is required for STRICT tables")
        self._path = database_path
        self._before_commit = before_commit
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            self._migrate(connection)

    def save_draft(self, cube_version: CubeVersion, state: DraftState) -> None:
        if not isinstance(cube_version, CubeVersion):
            raise ValueError("cube_version must be a CubeVersion")
        if not isinstance(state, DraftState):
            raise ValueError("state must be a DraftState")
        with self._connect() as connection:
            self._save_draft(connection, cube_version, state)

    def save_cube_version(self, cube_version: CubeVersion) -> None:
        """Store one immutable CubeVersion before a draft is configured."""

        if not isinstance(cube_version, CubeVersion):
            raise ValueError("cube_version must be a CubeVersion")
        with self._connect() as connection:
            self._store_cube_version(
                connection,
                cube_version.id,
                _encode(_cube_version_payload(cube_version)),
            )

    def transact(self, draft_id: str, transition: DraftTransaction) -> DraftState:
        """Load, transition, and persist one draft under one SQLite transaction."""

        if not isinstance(draft_id, str) or not draft_id.strip():
            raise ValueError("draft_id must be a nonblank string")
        if not callable(transition):
            raise ValueError("transition must be callable")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT cube_version_id FROM drafts WHERE id = ?", (draft_id,)
            ).fetchone()
            if row is None:
                raise PersistenceError("draft does not exist")
            state = self._load_draft(connection, draft_id)
            cube_version = self._load_cube_version(connection, row["cube_version_id"])
            if state is None or cube_version is None:
                raise PersistenceError("stored draft is missing its CubeVersion")
            updated = transition(state, cube_version)
            if not isinstance(updated, DraftState) or updated.draft.id != draft_id:
                raise PersistenceError("transaction must return the same DraftState")
            self._save_draft(connection, cube_version, updated)
            return updated

    def load_cube_version(self, cube_version_id: str) -> CubeVersion | None:
        if not isinstance(cube_version_id, str) or not cube_version_id.strip():
            raise ValueError("cube_version_id must be a nonblank string")
        with self._connect() as connection:
            return self._load_cube_version(connection, cube_version_id)

    def load_draft(self, draft_id: str) -> DraftState | None:
        if not isinstance(draft_id, str) or not draft_id.strip():
            raise ValueError("draft_id must be a nonblank string")
        with self._connect() as connection:
            return self._load_draft(connection, draft_id)

    @staticmethod
    def _load_cube_version(
        connection: sqlite3.Connection, cube_version_id: str
    ) -> CubeVersion | None:
        row = connection.execute(
            "SELECT payload FROM cube_versions WHERE id = ?", (cube_version_id,)
        ).fetchone()
        return (
            None if row is None else _cube_version_from_payload(_decode(row["payload"]))
        )

    @staticmethod
    def _load_draft(connection: sqlite3.Connection, draft_id: str) -> DraftState | None:
        row = connection.execute(
            "SELECT initial_payload, events_payload FROM drafts WHERE id = ?",
            (draft_id,),
        ).fetchone()
        if row is None:
            return None
        draft, allocation = _draft_initial_from_payload(_decode(row["initial_payload"]))
        try:
            state = start_draft(draft, allocation)
            for event in _decode_events(row["events_payload"]):
                state = pick_card(
                    state,
                    event.seat_number,
                    event.card_instance_id,
                    actor_origin=event.actor_origin,
                    actor_id=event.actor_id,
                    strategy_ref=event.strategy_ref,
                    bot_provenance=event.bot_provenance,
                )
                if state.pick_events[-1] != event:
                    raise PersistenceError(
                        "rehydrated event does not match stored event"
                    )
            return state
        except (ValueError, DraftTransitionError, KeyError, TypeError) as error:
            raise PersistenceError("stored draft cannot be rehydrated") from error

    def _save_draft(
        self,
        connection: sqlite3.Connection,
        cube_version: CubeVersion,
        state: DraftState,
    ) -> None:
        if state.draft.cube_version_id != cube_version.id:
            raise PersistenceError("cube_version must belong to the draft")
        cube_card_ids = {card.id for card in cube_version.cards}
        if any(
            card.cube_card_id not in cube_card_ids
            for allocated in state.allocation
            for card in allocated.cards
        ):
            raise PersistenceError("draft allocation must reference CubeVersion cards")
        cube_payload = _encode(_cube_version_payload(cube_version))
        initial_payload = _encode(_draft_initial_payload(state))
        events_payload = _encode(
            [_pick_event_payload(event) for event in state.pick_events]
        )
        self._store_cube_version(connection, cube_version.id, cube_payload)
        row = connection.execute(
            "SELECT cube_version_id, initial_payload, events_payload FROM drafts WHERE id = ?",
            (state.draft.id,),
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO drafts(id, cube_version_id, initial_payload, events_payload) "
                "VALUES (?, ?, ?, ?)",
                (state.draft.id, cube_version.id, initial_payload, events_payload),
            )
        else:
            if (
                row["cube_version_id"] != cube_version.id
                or row["initial_payload"] != initial_payload
            ):
                raise PersistenceConflict("draft initial state is immutable")
            existing_events = _decode_events(row["events_payload"])
            new_events = _decode_events(events_payload)
            if tuple(new_events[: len(existing_events)]) != tuple(existing_events):
                raise PersistenceConflict(
                    "draft events must retain their persisted prefix"
                )
            connection.execute(
                "UPDATE drafts SET events_payload = ? WHERE id = ?",
                (events_payload, state.draft.id),
            )
        if self._before_commit is not None:
            self._before_commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _migrate(connection: sqlite3.Connection) -> None:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL) STRICT"
        )
        for version, sql in _MIGRATIONS:
            applied = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone()
            if applied is None:
                connection.executescript(sql)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) "
                    "VALUES (?, datetime('now'))",
                    (version,),
                )

    @staticmethod
    def _store_cube_version(
        connection: sqlite3.Connection, cube_version_id: str, payload: str
    ) -> None:
        row = connection.execute(
            "SELECT payload FROM cube_versions WHERE id = ?", (cube_version_id,)
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO cube_versions(id, payload) VALUES (?, ?)",
                (cube_version_id, payload),
            )
        elif row["payload"] != payload:
            raise PersistenceConflict("CubeVersion snapshots are immutable")


def _encode(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _decode(value: str) -> dict[str, object] | list[object]:
    decoded = json.loads(value)
    if not isinstance(decoded, (dict, list)):
        raise PersistenceError("stored JSON has an unexpected shape")
    return decoded


def _reference_payload(reference: SourceReference | None) -> dict[str, str] | None:
    return (
        None
        if reference is None
        else {"source": reference.source, "external_id": reference.external_id}
    )


def _reference_from_payload(value: object) -> SourceReference | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise PersistenceError("source reference has an invalid shape")
    return SourceReference(_text(value, "source"), _text(value, "external_id"))


def _cube_version_payload(version: CubeVersion) -> dict[str, object]:
    return {
        "id": version.id,
        "cube": {
            "id": version.cube.id,
            "name": version.cube.name,
            "source": _reference_payload(version.cube.source_reference),
        },
        "source": _reference_payload(version.source_reference),
        "resolution_snapshot_id": version.resolution_snapshot_id,
        "content_fingerprint": version.content_fingerprint,
        "cards": [
            {
                "id": card.id,
                "resolution_status": card.resolution_status.value,
                "source": _reference_payload(card.source_reference),
                "printing": None
                if card.printing is None
                else {
                    "id": card.printing.id,
                    "source": _reference_payload(card.printing.source_reference),
                    "identity": {
                        "id": card.printing.card_identity.id,
                        "name": card.printing.card_identity.name,
                        "resolution_status": card.printing.card_identity.resolution_status.value,
                        "oracle_id": card.printing.card_identity.oracle_id,
                        "source": _reference_payload(
                            card.printing.card_identity.source_reference
                        ),
                    },
                },
            }
            for card in version.cards
        ],
    }


def _cube_version_from_payload(value: dict[str, object] | list[object]) -> CubeVersion:
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("cube"), dict)
        or not isinstance(value.get("cards"), list)
    ):
        raise PersistenceError("CubeVersion payload has an invalid shape")
    cube_payload = value["cube"]
    cards_payload = value["cards"]
    assert isinstance(cube_payload, dict)
    assert isinstance(cards_payload, list)
    cards: list[CubeCard] = []
    for card_payload in cards_payload:
        if not isinstance(card_payload, dict):
            raise PersistenceError("CubeCard payload has an invalid shape")
        printing_payload = card_payload.get("printing")
        printing: CardPrinting | None = None
        if printing_payload is not None:
            if not isinstance(printing_payload, dict) or not isinstance(
                printing_payload.get("identity"), dict
            ):
                raise PersistenceError("printing payload has an invalid shape")
            identity_payload = printing_payload["identity"]
            assert isinstance(identity_payload, dict)
            identity = CardIdentity(
                _text(identity_payload, "id"),
                _text(identity_payload, "name"),
                ResolutionStatus(_text(identity_payload, "resolution_status")),
                _optional_text(identity_payload.get("oracle_id")),
                _reference_from_payload(identity_payload.get("source")),
            )
            printing = CardPrinting(
                _text(printing_payload, "id"),
                identity,
                _reference_from_payload(printing_payload.get("source")),
            )
        cards.append(
            CubeCard(
                _text(card_payload, "id"),
                ResolutionStatus(_text(card_payload, "resolution_status")),
                printing,
                _reference_from_payload(card_payload.get("source")),
            )
        )
    return CubeVersion(
        _text(value, "id"),
        Cube(
            _text(cube_payload, "id"),
            _text(cube_payload, "name"),
            _reference_from_payload(cube_payload.get("source")),
        ),
        tuple(cards),
        _reference_from_payload(value.get("source")),
        _optional_text(value.get("resolution_snapshot_id")),
        _optional_text(value.get("content_fingerprint")),
    )


def _draft_initial_payload(state: DraftState) -> dict[str, object]:
    return {
        "draft": {
            "id": state.draft.id,
            "cube_version_id": state.draft.cube_version_id,
            "configuration": {
                "seats": state.draft.configuration.seats,
                "packs_per_seat": state.draft.configuration.packs_per_seat,
                "pack_size": state.draft.configuration.pack_size,
                "seed": state.draft.configuration.seed,
            },
        },
        "allocation": [
            {
                "pack_number": allocated.pack.pack_number,
                "owner_seat": allocated.pack.owner_seat,
                "cards": [
                    {"id": card.id, "cube_card_id": card.cube_card_id}
                    for card in allocated.cards
                ],
            }
            for allocated in state.allocation
        ],
    }


def _draft_initial_from_payload(
    value: dict[str, object] | list[object],
) -> tuple[Draft, tuple[AllocatedPack, ...]]:
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("draft"), dict)
        or not isinstance(value.get("allocation"), list)
    ):
        raise PersistenceError("draft payload has an invalid shape")
    draft_payload = value["draft"]
    allocation_payload = value["allocation"]
    assert isinstance(draft_payload, dict)
    assert isinstance(allocation_payload, list)
    configuration_payload = draft_payload.get("configuration")
    if not isinstance(configuration_payload, dict):
        raise PersistenceError("draft configuration has an invalid shape")
    draft = Draft(
        _text(draft_payload, "id"),
        _text(draft_payload, "cube_version_id"),
        DraftConfiguration(
            _integer(configuration_payload, "seats"),
            _integer(configuration_payload, "packs_per_seat"),
            _integer(configuration_payload, "pack_size"),
            _integer(configuration_payload, "seed"),
        ),
    )
    allocation: list[AllocatedPack] = []
    for item in allocation_payload:
        if not isinstance(item, dict) or not isinstance(item.get("cards"), list):
            raise PersistenceError("allocation payload has an invalid shape")
        pack = DraftPack(
            draft.id,
            _integer(item, "pack_number"),
            _integer(item, "owner_seat"),
        )
        cards = tuple(
            DraftCardInstance(_text(card, "id"), draft.id, _text(card, "cube_card_id"))
            for card in item["cards"]
            if isinstance(card, dict)
        )
        if len(cards) != len(item["cards"]):
            raise PersistenceError("allocation cards have an invalid shape")
        allocation.append(AllocatedPack(pack, cards))
    return draft, tuple(allocation)


def _pick_event_payload(event: PickEvent) -> dict[str, object]:
    provenance = event.bot_provenance
    return {
        "draft_id": event.draft_id,
        "sequence": event.sequence,
        "seat_number": event.seat_number,
        "pack_number": event.pack_number,
        "pick_number": event.pick_number,
        "card_instance_id": event.card_instance_id,
        "actor_origin": event.actor_origin.value,
        "actor_id": event.actor_id,
        "strategy_ref": event.strategy_ref,
        "bot_provenance": None
        if provenance is None
        else {
            "strategy_id": provenance.strategy_id,
            "strategy_version": provenance.strategy_version,
            "rating_artifact_id": provenance.rating_artifact_id,
            "rating_artifact_version": provenance.rating_artifact_version,
            "selected_rating": provenance.selected_rating,
            "rating_lookup_outcome": provenance.rating_lookup_outcome.value,
            "tie_break_reason": provenance.tie_break_reason.value,
        },
    }


def _decode_events(value: str) -> list[PickEvent]:
    payload = _decode(value)
    if not isinstance(payload, list):
        raise PersistenceError("events payload must be an array")
    events: list[PickEvent] = []
    for item in payload:
        if not isinstance(item, dict):
            raise PersistenceError("event payload has an invalid shape")
        provenance_payload = item.get("bot_provenance")
        provenance: BotDecisionProvenance | None = None
        if provenance_payload is not None:
            if not isinstance(provenance_payload, dict):
                raise PersistenceError("bot provenance has an invalid shape")
            rating = provenance_payload.get("selected_rating")
            if not isinstance(rating, (int, float)) or isinstance(rating, bool):
                raise PersistenceError("bot provenance rating has an invalid shape")
            provenance = BotDecisionProvenance(
                _text(provenance_payload, "strategy_id"),
                _text(provenance_payload, "strategy_version"),
                _text(provenance_payload, "rating_artifact_id"),
                _text(provenance_payload, "rating_artifact_version"),
                rating,
                RatingLookupOutcome(_text(provenance_payload, "rating_lookup_outcome")),
                BotTieBreakReason(_text(provenance_payload, "tie_break_reason")),
            )
        events.append(
            PickEvent(
                _text(item, "draft_id"),
                _integer(item, "sequence"),
                _integer(item, "seat_number"),
                _integer(item, "pack_number"),
                _integer(item, "pick_number"),
                _text(item, "card_instance_id"),
                ActorOrigin(_text(item, "actor_origin")),
                _text(item, "actor_id"),
                _optional_text(item.get("strategy_ref")),
                provenance,
            )
        )
    return events


def _text(value: dict[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise PersistenceError(f"{key} must be a nonblank string")
    return item


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise PersistenceError("optional text has an invalid shape")
    return value


def _integer(value: dict[str, object], key: str) -> int:
    item = value.get(key)
    if not isinstance(item, int) or isinstance(item, bool):
        raise PersistenceError(f"{key} must be an integer")
    return item
