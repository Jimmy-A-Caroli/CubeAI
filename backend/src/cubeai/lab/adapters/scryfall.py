"""Exact-ID Scryfall metadata resolver with a small durable SQLite cache."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Protocol, cast
import urllib.error
import urllib.request
from uuid import UUID

from cubeai.lab.application.imports import CandidateResolution, ImportCandidate
from cubeai.lab.application.metadata import (
    MetadataDiagnostic,
    MetadataDiagnosticCode,
    MetadataResolution,
    MetadataResolutionOutcome,
    MetadataResolutionSnapshot,
    ResolvedPrinting,
    ScryfallFace,
)


COLLECTION_URL = "https://api.scryfall.com/cards/collection"
MAX_COLLECTION_IDENTIFIERS = 75
CACHE_FRESH_FOR = timedelta(hours=24)
MINIMUM_REQUEST_INTERVAL_SECONDS = 0.5
RATE_LIMIT_COOLDOWN_SECONDS = 30.0
RETRY_DELAY_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 10.0
RESPONSE_SCHEMA_VERSION = 1


class _Response(Protocol):
    status: int

    def read(self) -> bytes: ...


class _Opener(Protocol):
    def __call__(
        self, request: urllib.request.Request, timeout: float
    ) -> _Response: ...


def _default_opener(request: urllib.request.Request, timeout: float) -> _Response:
    return cast(_Response, urllib.request.urlopen(request, timeout=timeout))


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


def _normalise_uuid(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("printing reference must be a UUID string")
    return str(UUID(value))


def _format_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("cached fetched_at must be timezone-aware")
    return parsed.astimezone(UTC)


def _uri_pairs(value: object, field: str) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object when present")
    pairs: list[tuple[str, str]] = []
    for key, uri in value.items():
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(uri, str)
            or not uri.startswith("https://")
        ):
            raise ValueError(f"{field} must contain HTTPS URI values")
        pairs.append((key, uri))
    return tuple(sorted(pairs))


def _stored_uri_pairs(value: object, field: str) -> tuple[tuple[str, str], ...]:
    """Decode the JSON array form used by the durable cache payload."""
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array in a cached payload")
    pairs: list[tuple[str, str]] = []
    for pair in value:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or not isinstance(pair[0], str)
            or not pair[0].strip()
            or not isinstance(pair[1], str)
            or not pair[1].startswith("https://")
        ):
            raise ValueError(f"{field} must contain HTTPS name/URI pairs")
        pairs.append((pair[0], pair[1]))
    return tuple(pairs)


def _printing_to_json(printing: ResolvedPrinting) -> str:
    payload = {
        "provider": printing.provider,
        "printing_id": printing.printing_id,
        "oracle_id": printing.oracle_id,
        "name": printing.name,
        "set_code": printing.set_code,
        "collector_number": printing.collector_number,
        "language": printing.language,
        "layout": printing.layout,
        "faces": [
            {
                "name": face.name,
                "oracle_id": face.oracle_id,
                "image_uris": list(face.image_uris),
            }
            for face in printing.faces
        ],
        "image_uris": list(printing.image_uris),
        "original_reference": printing.original_reference,
        "fetched_at": printing.fetched_at,
        "response_schema_version": printing.response_schema_version,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _printing_from_json(payload: str) -> ResolvedPrinting:
    decoded = json.loads(payload)
    if not isinstance(decoded, Mapping):
        raise ValueError("cached printing payload must be an object")
    raw_faces = decoded.get("faces")
    if not isinstance(raw_faces, list):
        raise ValueError("cached printing faces must be an array")
    faces: list[ScryfallFace] = []
    for face in raw_faces:
        if not isinstance(face, Mapping):
            raise ValueError("cached printing face must be an object")
        faces.append(
            ScryfallFace(
                _require_text(face.get("name"), "face.name"),
                _optional_text(face.get("oracle_id"), "face.oracle_id"),
                _stored_uri_pairs(face.get("image_uris"), "face.image_uris"),
            )
        )
    schema_version = decoded.get("response_schema_version")
    if not isinstance(schema_version, int):
        raise ValueError("cached response_schema_version must be an integer")
    return ResolvedPrinting(
        _require_text(decoded.get("provider"), "provider"),
        _require_text(decoded.get("printing_id"), "printing_id"),
        _optional_text(decoded.get("oracle_id"), "oracle_id"),
        _require_text(decoded.get("name"), "name"),
        _require_text(decoded.get("set_code"), "set_code"),
        _require_text(decoded.get("collector_number"), "collector_number"),
        _require_text(decoded.get("language"), "language"),
        _require_text(decoded.get("layout"), "layout"),
        tuple(faces),
        _stored_uri_pairs(decoded.get("image_uris"), "image_uris"),
        _require_text(decoded.get("original_reference"), "original_reference"),
        _require_text(decoded.get("fetched_at"), "fetched_at"),
        schema_version,
    )


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field)


class SQLiteScryfallCache:
    """A single-table adapter cache keyed only by exact Scryfall printing ID."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scryfall_cache_records (
                    printing_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    response_schema_version INTEGER NOT NULL
                ) STRICT
                """
            )

    @property
    def path(self) -> Path:
        return self._path

    def get(self, printing_id: str) -> ResolvedPrinting | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM scryfall_cache_records WHERE printing_id = ?",
                (printing_id,),
            ).fetchone()
        if row is None:
            return None
        return _printing_from_json(cast(str, row[0]))

    def put(self, printing: ResolvedPrinting) -> None:
        if printing.provider != "scryfall":
            raise ValueError("the Scryfall cache only accepts Scryfall printings")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scryfall_cache_records (
                    printing_id, payload, fetched_at, response_schema_version
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(printing_id) DO UPDATE SET
                    payload = excluded.payload,
                    fetched_at = excluded.fetched_at,
                    response_schema_version = excluded.response_schema_version
                """,
                (
                    printing.printing_id,
                    _printing_to_json(printing),
                    printing.fetched_at,
                    printing.response_schema_version,
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)


@dataclass(frozen=True, slots=True)
class _CollectionLookup:
    printings: Mapping[str, ResolvedPrinting]
    not_found: frozenset[str]
    failure: MetadataResolutionOutcome | None = None


class ScryfallMetadataResolver:
    """Resolve only exact printing UUIDs through cache-first collection calls."""

    def __init__(
        self,
        cache: SQLiteScryfallCache,
        *,
        user_agent: str = "CubeAI/0.1 (https://example.invalid/cubeai)",
        opener: _Opener | None = None,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        _require_text(user_agent, "user_agent")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._cache = cache
        self._user_agent = user_agent
        self._opener = opener or _default_opener
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleeper = sleeper
        self._timeout = timeout
        self._last_request_at: datetime | None = None
        self._cooldown_until: datetime | None = None

    def resolve(
        self,
        candidates: tuple[ImportCandidate, ...],
        *,
        offline: bool = False,
    ) -> MetadataResolutionSnapshot:
        now = self._now()
        resolved: dict[str, MetadataResolution] = {}
        pending: dict[str, list[ImportCandidate]] = {}
        for candidate in candidates:
            reference = self._candidate_reference(candidate)
            if reference is None:
                resolved[candidate.membership_key] = MetadataResolution(
                    candidate, MetadataResolutionOutcome.CUSTOM_OR_UNRESOLVED
                )
                continue
            if isinstance(reference, MetadataResolutionOutcome):
                resolved[candidate.membership_key] = MetadataResolution(
                    candidate, reference
                )
                continue
            cached = self._cache.get(reference)
            if cached is not None:
                outcome = self._cache_outcome(cached, now)
                if outcome is MetadataResolutionOutcome.CACHED_FRESH or offline:
                    resolved[candidate.membership_key] = self._resolution(
                        candidate, outcome, cached
                    )
                    continue
            if offline:
                resolved[candidate.membership_key] = MetadataResolution(
                    candidate, MetadataResolutionOutcome.PROVIDER_UNAVAILABLE
                )
                continue
            pending.setdefault(reference, []).append(candidate)

        for references in _chunks(tuple(pending), MAX_COLLECTION_IDENTIFIERS):
            lookup = self._lookup(references)
            for reference in references:
                candidates_for_reference = pending[reference]
                if lookup.failure is not None:
                    for candidate in candidates_for_reference:
                        resolved[candidate.membership_key] = MetadataResolution(
                            candidate, lookup.failure
                        )
                elif reference in lookup.not_found:
                    for candidate in candidates_for_reference:
                        resolved[candidate.membership_key] = MetadataResolution(
                            candidate, MetadataResolutionOutcome.NOT_FOUND
                        )
                else:
                    printing = lookup.printings.get(reference)
                    if printing is None:
                        for candidate in candidates_for_reference:
                            resolved[candidate.membership_key] = MetadataResolution(
                                candidate,
                                MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE,
                            )
                    else:
                        self._cache.put(printing)
                        for candidate in candidates_for_reference:
                            resolved[candidate.membership_key] = self._resolution(
                                candidate, MetadataResolutionOutcome.RESOLVED, printing
                            )

        ordered = tuple(resolved[candidate.membership_key] for candidate in candidates)
        retrieved_at = _format_time(now)
        return MetadataResolutionSnapshot(
            _snapshot_id(retrieved_at, ordered), retrieved_at, ordered
        )

    def _candidate_reference(
        self, candidate: ImportCandidate
    ) -> str | MetadataResolutionOutcome | None:
        if candidate.resolution is CandidateResolution.CUSTOM:
            return None
        if candidate.printing_hint is None:
            return None
        try:
            return _normalise_uuid(candidate.printing_hint)
        except ValueError:
            return MetadataResolutionOutcome.INVALID_REFERENCE

    def _cache_outcome(
        self, printing: ResolvedPrinting, now: datetime
    ) -> MetadataResolutionOutcome:
        fetched_at = _parse_time(printing.fetched_at)
        age = now - fetched_at
        if timedelta() <= age < CACHE_FRESH_FOR:
            return MetadataResolutionOutcome.CACHED_FRESH
        return MetadataResolutionOutcome.CACHED_STALE

    def _resolution(
        self,
        candidate: ImportCandidate,
        outcome: MetadataResolutionOutcome,
        printing: ResolvedPrinting,
    ) -> MetadataResolution:
        diagnostics: list[MetadataDiagnostic] = []
        if (
            candidate.oracle_id is not None
            and candidate.oracle_id != printing.oracle_id
        ):
            diagnostics.append(
                MetadataDiagnostic(
                    MetadataDiagnosticCode.ORACLE_ID_MISMATCH,
                    "candidate Oracle identity does not match the exact printing record",
                )
            )
        candidate_face_oracles = {
            observation.value
            for observation in candidate.source_metadata
            if observation.name == "details.card_faces.oracle_id"
            and isinstance(observation.value, str)
        }
        printing_face_oracles = {
            face.oracle_id for face in printing.faces if face.oracle_id is not None
        }
        if candidate_face_oracles and candidate_face_oracles != printing_face_oracles:
            diagnostics.append(
                MetadataDiagnostic(
                    MetadataDiagnosticCode.FACE_ORACLE_ID_MISMATCH,
                    "candidate face Oracle identities do not match the exact printing record",
                )
            )
        cache_reference = (
            f"scryfall:{printing.printing_id}:{printing.fetched_at}:"
            f"v{printing.response_schema_version}"
        )
        return MetadataResolution(
            candidate, outcome, printing, cache_reference, tuple(diagnostics)
        )

    def _lookup(self, references: tuple[str, ...]) -> _CollectionLookup:
        payload = json.dumps(
            {"identifiers": [{"id": reference} for reference in references]},
            separators=(",", ":"),
        ).encode("utf-8")
        request = urllib.request.Request(
            COLLECTION_URL,
            data=payload,
            headers={
                "User-Agent": self._user_agent,
                "Accept": "application/json;q=0.9,*/*;q=0.8",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        document = self._request_json(request)
        if isinstance(document, MetadataResolutionOutcome):
            return _CollectionLookup({}, frozenset(), document)
        try:
            return _parse_collection(document, references, self._now())
        except TypeError, ValueError, json.JSONDecodeError:
            return _CollectionLookup(
                {}, frozenset(), MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE
            )

    def _request_json(
        self, request: urllib.request.Request
    ) -> Mapping[str, object] | MetadataResolutionOutcome:
        for attempt in range(2):
            self._wait_for_request_slot()
            try:
                response = self._opener(request, self._timeout)
                status = response.status
                body = response.read()
            except urllib.error.HTTPError as error:
                status = error.code
                body = b""
            except TimeoutError, urllib.error.URLError, OSError:
                if attempt == 0:
                    self._sleeper(RETRY_DELAY_SECONDS)
                    continue
                return MetadataResolutionOutcome.NETWORK_FAILURE
            except Exception:
                return MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE
            if type(status) is not int or not isinstance(body, bytes):
                return MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE
            if status == 429:
                self._cooldown_until = self._now() + timedelta(
                    seconds=RATE_LIMIT_COOLDOWN_SECONDS
                )
                return MetadataResolutionOutcome.PROVIDER_RATE_LIMITED
            if status >= 500:
                if attempt == 0:
                    self._sleeper(RETRY_DELAY_SECONDS)
                    continue
                return MetadataResolutionOutcome.PROVIDER_UNAVAILABLE
            if status != 200:
                return MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE
            try:
                document = json.loads(body.decode("utf-8"))
            except UnicodeDecodeError, json.JSONDecodeError:
                return MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE
            if not isinstance(document, Mapping):
                return MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE
            return document
        return MetadataResolutionOutcome.PROVIDER_UNAVAILABLE

    def _wait_for_request_slot(self) -> None:
        now = self._now()
        not_before = self._last_request_at
        if self._cooldown_until is not None and (
            not_before is None or self._cooldown_until > not_before
        ):
            not_before = self._cooldown_until
        if not_before is not None:
            elapsed = (now - not_before).total_seconds()
            required = (
                MINIMUM_REQUEST_INTERVAL_SECONDS
                if not_before is self._last_request_at
                else 0.0
            )
            if elapsed < required:
                self._sleeper(required - elapsed)
            elif elapsed < 0:
                self._sleeper(-elapsed)
        self._last_request_at = self._now()

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value.astimezone(UTC)


def _chunks(values: tuple[str, ...], size: int) -> tuple[tuple[str, ...], ...]:
    return tuple(values[index : index + size] for index in range(0, len(values), size))


def _parse_collection(
    document: Mapping[str, object], references: tuple[str, ...], fetched_at: datetime
) -> _CollectionLookup:
    data = document.get("data")
    not_found = document.get("not_found", [])
    if not isinstance(data, list) or not isinstance(not_found, list):
        raise ValueError("collection response needs data and not_found arrays")
    requested = set(references)
    printings: dict[str, ResolvedPrinting] = {}
    for row in data:
        if not isinstance(row, Mapping):
            raise ValueError("collection data entries must be objects")
        printing = _parse_printing(row, fetched_at)
        if printing.printing_id not in requested or printing.printing_id in printings:
            raise ValueError("collection response returned an unexpected printing ID")
        printings[printing.printing_id] = printing
    missing: set[str] = set()
    for row in not_found:
        if not isinstance(row, Mapping):
            raise ValueError("collection not_found entries must be objects")
        reference = _normalise_uuid(row.get("id"))
        if reference not in requested or reference in missing or reference in printings:
            raise ValueError("collection response returned an invalid not_found ID")
        missing.add(reference)
    if set(printings) | missing != requested:
        raise ValueError("collection response omitted a requested printing ID")
    return _CollectionLookup(printings, frozenset(missing))


def _parse_printing(
    row: Mapping[object, object], fetched_at: datetime
) -> ResolvedPrinting:
    raw_faces = row.get("card_faces", [])
    if not isinstance(raw_faces, list):
        raise ValueError("card_faces must be an array")
    faces: list[ScryfallFace] = []
    for raw_face in raw_faces:
        if not isinstance(raw_face, Mapping):
            raise ValueError("card face must be an object")
        faces.append(
            ScryfallFace(
                _require_text(raw_face.get("name"), "card_faces.name"),
                _optional_text(raw_face.get("oracle_id"), "card_faces.oracle_id"),
                _uri_pairs(raw_face.get("image_uris"), "card_faces.image_uris"),
            )
        )
    return ResolvedPrinting(
        "scryfall",
        _normalise_uuid(row.get("id")),
        _optional_text(row.get("oracle_id"), "oracle_id"),
        _require_text(row.get("name"), "name"),
        _require_text(row.get("set"), "set"),
        _require_text(row.get("collector_number"), "collector_number"),
        _require_text(row.get("lang"), "lang"),
        _require_text(row.get("layout"), "layout"),
        tuple(faces),
        _uri_pairs(row.get("image_uris"), "image_uris"),
        _normalise_uuid(row.get("id")),
        _format_time(fetched_at),
        RESPONSE_SCHEMA_VERSION,
    )


def _snapshot_id(retrieved_at: str, resolutions: tuple[MetadataResolution, ...]) -> str:
    payload = {
        "retrieved_at": retrieved_at,
        "resolutions": [
            {
                "membership_key": resolution.candidate.membership_key,
                "outcome": resolution.outcome.value,
                "printing_id": (
                    resolution.printing.printing_id if resolution.printing else None
                ),
                "cache_reference": resolution.cache_reference,
                "diagnostics": [
                    diagnostic.code.value for diagnostic in resolution.diagnostics
                ],
            }
            for resolution in resolutions
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"scryfall-resolution-v1:{hashlib.sha256(encoded).hexdigest()}"
