"""Bounded CubeCobra JSON adapter using the frozen public contract."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Protocol, cast

from cubeai.lab.application.imports import (
    CandidateResolution,
    CubeSource,
    DiagnosticCode,
    DiagnosticSeverity,
    ImportCandidate,
    ImportDiagnostic,
    ImportOutcome,
    ImportResult,
    SourceBoardObservation,
    SourceFieldObservation,
    SourceFieldState,
    SourceRequest,
    SourceSnapshotReference,
)


class _HttpResponse(Protocol):
    status: int

    def read(self) -> bytes: ...

    def __enter__(self) -> _HttpResponse: ...

    def __exit__(self, *args: object) -> None: ...


HttpOpener = Callable[[urllib.request.Request, float], _HttpResponse]
Clock = Callable[[], datetime]
Sleeper = Callable[[float], None]
CUBESCOBRA_ORIGIN = "https://cubecobra.com"


def _open_url(request: urllib.request.Request, timeout: float) -> _HttpResponse:
    return cast(_HttpResponse, urllib.request.urlopen(request, timeout=timeout))


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _no_sleep(_: float) -> None:
    """Default retries are immediate so the normal offline suite never waits."""


class CubeCobraSource(CubeSource):
    """Map exactly the frozen public cubeJSON subset to provider-neutral values."""

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        retries: int = 1,
        retry_delay: float = 0.0,
        user_agent: str = "CubeAI/0.1",
        opener: HttpOpener = _open_url,
        clock: Clock = _utc_now,
        sleeper: Sleeper = _no_sleep,
    ) -> None:
        if timeout <= 0 or not 0 <= retries <= 2 or retry_delay < 0:
            raise ValueError("invalid timeout, retries, or retry delay")
        if not user_agent.strip():
            raise ValueError("user_agent must be nonblank")
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        self._opener = opener
        self._clock = clock
        self._sleeper = sleeper

    @staticmethod
    def endpoint(identifier: str) -> str | None:
        """Validate an identifier only; page URL parsing is intentionally absent."""

        value = identifier.strip()
        if not value or any(char in value for char in "/\\?#"):
            return None
        return value

    def import_cube(self, request: SourceRequest) -> ImportResult:
        if request.source.lower() != "cubecobra":
            return self._failure(
                ImportOutcome.UNSUPPORTED,
                DiagnosticCode.UNSUPPORTED_SOURCE_CONTRACT,
                "the source is not CubeCobra",
            )
        identifier = self.endpoint(request.identifier)
        if identifier is None:
            return self._failure(
                ImportOutcome.SOURCE_REQUEST_INVALID,
                DiagnosticCode.SOURCE_REQUEST_INVALID,
                "CubeCobra input must be one nonempty identifier",
            )
        url = f"{CUBESCOBRA_ORIGIN}/cube/api/cubeJSON/{urllib.parse.quote(identifier)}"
        return self._request(identifier, url)

    def _request(self, identifier: str, url: str) -> ImportResult:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
        )
        for attempt in range(self.retries + 1):
            try:
                with self._opener(request, self.timeout) as response:
                    status = response.status
                    body = response.read()
            except urllib.error.HTTPError as error:
                status = error.code
                body = b""
            except TimeoutError, urllib.error.URLError, OSError:
                if attempt < self.retries:
                    self._retry()
                    continue
                return self._failure(
                    ImportOutcome.SOURCE_UNAVAILABLE,
                    DiagnosticCode.SOURCE_UNAVAILABLE,
                    "CubeCobra could not be reached",
                )
            except Exception:
                return self._failure(
                    ImportOutcome.SOURCE_UNAVAILABLE,
                    DiagnosticCode.SOURCE_UNAVAILABLE,
                    "CubeCobra request failed",
                )

            if not isinstance(status, int):
                return self._failure(
                    ImportOutcome.INVALID_SOURCE,
                    DiagnosticCode.INVALID_SOURCE_RECORD,
                    "CubeCobra response has an invalid HTTP status",
                )
            if status != 200:
                if status >= 500 and attempt < self.retries:
                    self._retry()
                    continue
                return self._http_failure(status)
            try:
                payload = json.loads(body)
            except TypeError, UnicodeDecodeError, json.JSONDecodeError:
                return self._failure(
                    ImportOutcome.INVALID_SOURCE,
                    DiagnosticCode.INVALID_SOURCE_RECORD,
                    "CubeCobra returned malformed JSON",
                )
            return self._map(payload, identifier, url)
        return self._failure(
            ImportOutcome.SOURCE_UNAVAILABLE,
            DiagnosticCode.SOURCE_UNAVAILABLE,
            "CubeCobra could not be reached",
        )

    def _retry(self) -> None:
        if self.retry_delay:
            self._sleeper(self.retry_delay)

    @staticmethod
    def _failure(
        outcome: ImportOutcome, code: DiagnosticCode, message: str
    ) -> ImportResult:
        return ImportResult(
            None,
            (),
            (ImportDiagnostic(code, DiagnosticSeverity.ERROR, message),),
            outcome,
        )

    def _http_failure(self, status: int) -> ImportResult:
        if status == 400:
            return self._failure(
                ImportOutcome.SOURCE_REQUEST_INVALID,
                DiagnosticCode.SOURCE_REQUEST_INVALID,
                "CubeCobra rejected the request",
            )
        if status == 404 or status in {401, 403}:
            return self._failure(
                ImportOutcome.SOURCE_INACCESSIBLE,
                DiagnosticCode.SOURCE_INACCESSIBLE,
                "CubeCobra source is inaccessible",
            )
        if status == 429:
            return self._failure(
                ImportOutcome.SOURCE_RATE_LIMITED,
                DiagnosticCode.SOURCE_RATE_LIMITED,
                "CubeCobra rate limited the request",
            )
        return self._failure(
            ImportOutcome.SOURCE_UNAVAILABLE,
            DiagnosticCode.SOURCE_UNAVAILABLE,
            "CubeCobra service is unavailable",
        )

    def _map(self, payload: object, identifier: str, url: str) -> ImportResult:
        if not isinstance(payload, dict):
            return self._failure(
                ImportOutcome.INVALID_SOURCE,
                DiagnosticCode.INVALID_SOURCE_RECORD,
                "CubeCobra response must be a JSON object",
            )
        response = cast(dict[str, object], payload)
        cube_id = self._required_text(response.get("id"))
        if cube_id is None:
            return self._failure(
                ImportOutcome.INVALID_SOURCE,
                DiagnosticCode.INVALID_SOURCE_RECORD,
                "CubeCobra response is missing a full id",
            )
        name = self._required_text(response.get("name"))
        if name is None:
            return self._failure(
                ImportOutcome.INVALID_SOURCE,
                DiagnosticCode.INVALID_SOURCE_RECORD,
                "CubeCobra response is missing a name",
            )
        visibility = response.get("visibility")
        if not isinstance(visibility, str) or not visibility.strip():
            return self._failure(
                ImportOutcome.INVALID_SOURCE,
                DiagnosticCode.INVALID_SOURCE_RECORD,
                "CubeCobra response is missing visibility",
            )
        if visibility != "pu":
            return self._failure(
                ImportOutcome.UNSUPPORTED,
                DiagnosticCode.UNSUPPORTED_VISIBILITY,
                "CubeCobra visibility is not public",
            )
        cards_value = response.get("cards")
        if not isinstance(cards_value, dict):
            return self._failure(
                ImportOutcome.INVALID_SOURCE,
                DiagnosticCode.INVALID_SOURCE_RECORD,
                "CubeCobra cards must be an object",
            )
        cards = cast(dict[str, object], cards_value)
        mainboard = cards.get("mainboard")
        if not isinstance(mainboard, list):
            return self._failure(
                ImportOutcome.INVALID_SOURCE,
                DiagnosticCode.INVALID_SOURCE_RECORD,
                "CubeCobra mainboard must be an array",
            )
        if not mainboard:
            return self._failure(
                ImportOutcome.UNSUPPORTED,
                DiagnosticCode.EMPTY_MAINBOARD,
                "CubeCobra mainboard is empty",
            )

        metadata = tuple(
            (
                self._observe_number(response, "cardCount")
                if key == "cardCount"
                else self._observe(response, key)
            )
            for key in ("shortId", "cardCount", "version", "dateLastUpdated")
        )
        supplementary = tuple(
            SourceBoardObservation(name, len(value))
            for name, value in cards.items()
            if name != "mainboard" and isinstance(value, list)
        )
        short_id = response.get("shortId")
        returned_short_id = self._required_text(short_id)
        snapshot = SourceSnapshotReference(
            "cubecobra",
            cube_id,
            self._clock().astimezone(UTC).isoformat(),
            url,
            identifier,
            returned_short_id,
            visibility,
            metadata,
            supplementary,
        )
        malformed_optionals = [
            field.name
            for field in metadata
            if field.state is SourceFieldState.MALFORMED
        ]
        diagnostics: list[ImportDiagnostic] = [
            ImportDiagnostic(
                DiagnosticCode.OPTIONAL_SOURCE_DATA_MALFORMED,
                DiagnosticSeverity.WARNING,
                f"optional CubeCobra field has an unsupported shape: {field}",
                snapshot,
            )
            for field in malformed_optionals
        ]
        card_count = next(field for field in metadata if field.name == "cardCount")
        if card_count.state is SourceFieldState.VALUE and card_count.value != len(
            mainboard
        ):
            diagnostics.append(
                ImportDiagnostic(
                    DiagnosticCode.CARD_COUNT_MISMATCH,
                    DiagnosticSeverity.WARNING,
                    "CubeCobra cardCount does not match mainboard length",
                    snapshot,
                )
            )
        candidates: list[ImportCandidate] = []
        optional_absent = any(
            field.state in {SourceFieldState.ABSENT, SourceFieldState.NULL}
            for field in metadata
        )
        for position, row_value in enumerate(mainboard):
            if not isinstance(row_value, dict):
                return self._row_failure(
                    snapshot, position, "mainboard row must be an object"
                )
            row = cast(dict[str, object], row_value)
            provider_card_id = self._required_text(row.get("cardID"))
            if provider_card_id is None:
                return self._row_failure(
                    snapshot, position, "mainboard row is missing cardID"
                )
            details_value = row.get("details")
            if not isinstance(details_value, dict):
                return self._unknown_row(
                    snapshot, position, "mainboard row has no identity details"
                )
            details = cast(dict[str, object], details_value)
            printing_id = self._required_text(details.get("scryfall_id"))
            oracle_id = self._required_text(details.get("oracle_id"))
            if printing_id is None or oracle_id is None:
                return self._unknown_row(
                    snapshot,
                    position,
                    "mainboard row is missing exact printing or Oracle evidence",
                )
            if self._is_custom_or_voucher(row):
                return self._unknown_row(
                    snapshot,
                    position,
                    "mainboard row has custom or voucher semantics",
                )
            row_metadata = self._row_metadata(row, details)
            malformed = [
                field.name
                for field in row_metadata
                if field.state is SourceFieldState.MALFORMED
            ]
            diagnostics.extend(
                ImportDiagnostic(
                    DiagnosticCode.OPTIONAL_SOURCE_DATA_MALFORMED,
                    DiagnosticSeverity.WARNING,
                    f"optional CubeCobra field has an unsupported shape: {field}",
                    snapshot,
                    f"{cube_id}:{position}",
                )
                for field in malformed
            )
            optional_absent = optional_absent or any(
                field.state in {SourceFieldState.ABSENT, SourceFieldState.NULL}
                for field in row_metadata
            )
            tags = self._tags_value(row_metadata)
            notes = self._text_value(row_metadata, "notes")
            custom_name = self._text_value(row_metadata, "custom_name")
            candidates.append(
                ImportCandidate(
                    f"{cube_id}:{position}",
                    snapshot,
                    position,
                    provider_card_id,
                    "mainboard",
                    tags,
                    notes,
                    printing_id,
                    oracle_id,
                    custom_name,
                    CandidateResolution.RESOLUTION_HINTED,
                    ("cardID", "details.scryfall_id", "details.oracle_id"),
                    row_metadata,
                )
            )
        nonempty_boards = tuple(board for board in supplementary if board.count > 0)
        if nonempty_boards:
            diagnostics.extend(
                ImportDiagnostic(
                    DiagnosticCode.UNSUPPORTED_NON_MAINBOARD,
                    DiagnosticSeverity.WARNING,
                    f"non-mainboard array is nonempty: {board.name} ({board.count})",
                    snapshot,
                )
                for board in nonempty_boards
            )
        if optional_absent:
            outcome = ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT
        else:
            outcome = ImportOutcome.SUPPORTED
        return ImportResult(snapshot, tuple(candidates), tuple(diagnostics), outcome)

    @staticmethod
    def _required_text(value: object) -> str | None:
        return value if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _observe(
        mapping: Mapping[str, object], key: str, name: str | None = None
    ) -> SourceFieldObservation:
        observation_name = name or key
        if key not in mapping:
            return SourceFieldObservation(observation_name, SourceFieldState.ABSENT)
        value = mapping[key]
        if value is None:
            return SourceFieldObservation(observation_name, SourceFieldState.NULL)
        if value == "":
            return SourceFieldObservation(
                observation_name, SourceFieldState.EMPTY_STRING
            )
        if isinstance(value, list) and not value:
            return SourceFieldObservation(
                observation_name, SourceFieldState.EMPTY_ARRAY
            )
        if isinstance(value, (str, int, float, bool)):
            return SourceFieldObservation(
                observation_name, SourceFieldState.VALUE, value
            )
        return SourceFieldObservation(observation_name, SourceFieldState.MALFORMED)

    @staticmethod
    def _observe_number(
        mapping: Mapping[str, object], name: str
    ) -> SourceFieldObservation:
        if name not in mapping:
            return SourceFieldObservation(name, SourceFieldState.ABSENT)
        value = mapping[name]
        if value is None:
            return SourceFieldObservation(name, SourceFieldState.NULL)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return SourceFieldObservation(name, SourceFieldState.VALUE, value)
        return SourceFieldObservation(name, SourceFieldState.MALFORMED)

    @classmethod
    def _row_metadata(
        cls, row: Mapping[str, object], details: Mapping[str, object]
    ) -> tuple[SourceFieldObservation, ...]:
        fields = [
            cls._observe(row, key)
            for key in (
                "board",
                "index",
                "notes",
                "status",
                "finish",
                "addedTmsp",
                "custom_name",
                "imgUrl",
                "imgBackUrl",
            )
        ]
        fields.extend(
            cls._observe(details, key, f"details.{key}")
            for key in ("set", "collector_number", "language")
        )
        if "tags" not in row:
            fields.append(SourceFieldObservation("tags", SourceFieldState.ABSENT))
        elif row["tags"] is None:
            fields.append(SourceFieldObservation("tags", SourceFieldState.NULL))
        elif isinstance(row["tags"], list) and not row["tags"]:
            fields.append(SourceFieldObservation("tags", SourceFieldState.EMPTY_ARRAY))
        elif isinstance(row["tags"], list) and all(
            isinstance(tag, str) for tag in row["tags"]
        ):
            fields.append(
                SourceFieldObservation(
                    "tags", SourceFieldState.VALUE, tuple(row["tags"])
                )
            )
        else:
            fields.append(SourceFieldObservation("tags", SourceFieldState.MALFORMED))
        return tuple(fields)

    @staticmethod
    def _is_custom_or_voucher(row: Mapping[str, object]) -> bool:
        return "voucher_cards" in row

    @staticmethod
    def _row_failure(
        snapshot: SourceSnapshotReference, position: int, message: str
    ) -> ImportResult:
        key = f"{snapshot.snapshot_id}:{position}"
        return ImportResult(
            snapshot,
            (),
            (
                ImportDiagnostic(
                    DiagnosticCode.INVALID_SOURCE_RECORD,
                    DiagnosticSeverity.ERROR,
                    message,
                    snapshot,
                    key,
                ),
            ),
            ImportOutcome.INVALID_SOURCE,
        )

    @staticmethod
    def _unknown_row(
        snapshot: SourceSnapshotReference, position: int, message: str
    ) -> ImportResult:
        key = f"{snapshot.snapshot_id}:{position}"
        return ImportResult(
            snapshot,
            (),
            (
                ImportDiagnostic(
                    DiagnosticCode.UNKNOWN_SOURCE_SHAPE,
                    DiagnosticSeverity.ERROR,
                    message,
                    snapshot,
                    key,
                ),
            ),
            ImportOutcome.UNKNOWN_SOURCE_SHAPE,
        )

    @staticmethod
    def _tags_value(metadata: tuple[SourceFieldObservation, ...]) -> tuple[str, ...]:
        field = next(item for item in metadata if item.name == "tags")
        return field.value if isinstance(field.value, tuple) else ()

    @staticmethod
    def _text_value(
        metadata: tuple[SourceFieldObservation, ...], name: str
    ) -> str | None:
        field = next(item for item in metadata if item.name == name)
        return field.value if isinstance(field.value, str) and field.value else None
