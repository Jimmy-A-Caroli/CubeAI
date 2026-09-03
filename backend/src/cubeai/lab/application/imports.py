"""Provider-neutral import candidates, outcomes, and source adapter port."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DiagnosticCode(StrEnum):
    SOURCE_REQUEST_INVALID = "source_request_invalid"
    SOURCE_INACCESSIBLE = "source_inaccessible"
    SOURCE_RATE_LIMITED = "source_rate_limited"
    SOURCE_UNAVAILABLE = "source_unavailable"
    UNSUPPORTED_SOURCE_CONTRACT = "unsupported_source_contract"
    UNSUPPORTED_VISIBILITY = "unsupported_visibility"
    UNSUPPORTED_NON_MAINBOARD = "unsupported_non_mainboard"
    EMPTY_MAINBOARD = "empty_mainboard"
    INVALID_SOURCE_RECORD = "invalid_source_record"
    UNKNOWN_SOURCE_SHAPE = "unknown_source_shape"
    OPTIONAL_SOURCE_DATA_MALFORMED = "optional_source_data_malformed"


class ImportOutcome(StrEnum):
    SUPPORTED = "supported"
    SUPPORTED_WITH_OPTIONAL_DATA_ABSENT = "supported_with_optional_data_absent"
    UNSUPPORTED = "unsupported"
    INVALID_SOURCE = "invalid_source"
    UNKNOWN_SOURCE_SHAPE = "unknown_source_shape"
    SOURCE_REQUEST_INVALID = "source_request_invalid"
    SOURCE_INACCESSIBLE = "source_inaccessible"
    SOURCE_RATE_LIMITED = "source_rate_limited"
    SOURCE_UNAVAILABLE = "source_unavailable"


class CandidateResolution(StrEnum):
    UNRESOLVED = "unresolved"
    CUSTOM = "custom"
    RESOLUTION_HINTED = "resolution_hinted"


class SourceFieldState(StrEnum):
    ABSENT = "absent"
    NULL = "null"
    VALUE = "value"
    MALFORMED = "malformed"


SourceFieldValue = str | int | float | bool | tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceFieldObservation:
    """A provider observation without carrying provider payload types inward."""

    name: str
    state: SourceFieldState
    value: SourceFieldValue | None = None

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        if not isinstance(self.state, SourceFieldState):
            raise ValueError("state must be a SourceFieldState")
        if self.state is SourceFieldState.VALUE and self.value is None:
            raise ValueError("a value observation requires a value")
        if self.state is not SourceFieldState.VALUE and self.value is not None:
            raise ValueError("only a value observation may carry a value")


@dataclass(frozen=True, slots=True)
class SourceBoardObservation:
    """A non-mainboard array recorded for diagnostics and source provenance."""

    name: str
    count: int

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        if not isinstance(self.count, int) or self.count < 0:
            raise ValueError("count must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class SourceRequest:
    source: str
    identifier: str

    def __post_init__(self) -> None:
        _require_text(self.source, "source")
        if not isinstance(self.identifier, str):
            raise ValueError("identifier must be a string")


@dataclass(frozen=True, slots=True)
class SourceSnapshotReference:
    source: str
    snapshot_id: str
    retrieved_at: str
    source_uri: str | None = None
    request_identifier: str | None = None
    returned_short_id: str | None = None
    visibility: str | None = None
    source_metadata: tuple[SourceFieldObservation, ...] = ()
    supplementary_boards: tuple[SourceBoardObservation, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.source, "source")
        _require_text(self.snapshot_id, "snapshot_id")
        _require_text(self.retrieved_at, "retrieved_at")
        for field, value in (
            ("source_uri", self.source_uri),
            ("request_identifier", self.request_identifier),
            ("returned_short_id", self.returned_short_id),
            ("visibility", self.visibility),
        ):
            if value is not None:
                _require_text(value, field)
        metadata = tuple(self.source_metadata)
        boards = tuple(self.supplementary_boards)
        if any(not isinstance(item, SourceFieldObservation) for item in metadata):
            raise ValueError(
                "source_metadata must contain SourceFieldObservation values"
            )
        if any(not isinstance(item, SourceBoardObservation) for item in boards):
            raise ValueError(
                "supplementary_boards must contain SourceBoardObservation values"
            )
        object.__setattr__(self, "source_metadata", metadata)
        object.__setattr__(self, "supplementary_boards", boards)


@dataclass(frozen=True, slots=True)
class ImportCandidate:
    membership_key: str
    source_snapshot: SourceSnapshotReference
    position: int
    provider_card_id: str | None = None
    board: str | None = None
    tags: tuple[str, ...] = ()
    notes: str | None = None
    printing_hint: str | None = None
    oracle_id: str | None = None
    custom_name: str | None = None
    resolution: CandidateResolution = CandidateResolution.UNRESOLVED
    raw_field_references: tuple[str, ...] = ()
    source_metadata: tuple[SourceFieldObservation, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.membership_key, "membership_key")
        if not isinstance(self.source_snapshot, SourceSnapshotReference):
            raise ValueError("source_snapshot must be a SourceSnapshotReference")
        if not isinstance(self.position, int) or self.position < 0:
            raise ValueError("position must be a nonnegative integer")
        for field, value in (
            ("provider_card_id", self.provider_card_id),
            ("board", self.board),
            ("notes", self.notes),
            ("printing_hint", self.printing_hint),
            ("oracle_id", self.oracle_id),
            ("custom_name", self.custom_name),
        ):
            if value is not None:
                _require_text(value, field)
        if not isinstance(self.resolution, CandidateResolution):
            raise ValueError("resolution must be a CandidateResolution")
        tags = tuple(self.tags)
        references = tuple(self.raw_field_references)
        metadata = tuple(self.source_metadata)
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise ValueError("tags must contain nonblank strings")
        if any(not isinstance(ref, str) or not ref.strip() for ref in references):
            raise ValueError("raw_field_references must contain nonblank strings")
        if any(not isinstance(item, SourceFieldObservation) for item in metadata):
            raise ValueError(
                "source_metadata must contain SourceFieldObservation values"
            )
        object.__setattr__(self, "tags", tags)
        object.__setattr__(self, "raw_field_references", references)
        object.__setattr__(self, "source_metadata", metadata)


@dataclass(frozen=True, slots=True)
class ImportDiagnostic:
    code: DiagnosticCode
    severity: DiagnosticSeverity
    message: str
    source_snapshot: SourceSnapshotReference | None = None
    membership_key: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, DiagnosticCode):
            raise ValueError("code must be a DiagnosticCode")
        if not isinstance(self.severity, DiagnosticSeverity):
            raise ValueError("severity must be a DiagnosticSeverity")
        _require_text(self.message, "message")
        if self.membership_key is not None:
            _require_text(self.membership_key, "membership_key")


@dataclass(frozen=True, slots=True)
class ImportResult:
    """A structured port result; adapters never leak provider exceptions."""

    snapshot: SourceSnapshotReference | None
    candidates: tuple[ImportCandidate, ...]
    diagnostics: tuple[ImportDiagnostic, ...] = ()
    outcome: ImportOutcome = ImportOutcome.SUPPORTED

    def __post_init__(self) -> None:
        if self.snapshot is not None and not isinstance(
            self.snapshot, SourceSnapshotReference
        ):
            raise ValueError("snapshot must be a SourceSnapshotReference or None")
        if not isinstance(self.outcome, ImportOutcome):
            raise ValueError("outcome must be an ImportOutcome")
        candidates = tuple(self.candidates)
        diagnostics = tuple(self.diagnostics)
        if self.snapshot is None and candidates:
            raise ValueError("candidates require a source snapshot")
        if self.snapshot is not None and any(
            candidate.source_snapshot != self.snapshot for candidate in candidates
        ):
            raise ValueError("all candidates must reference the result snapshot")
        if len({candidate.membership_key for candidate in candidates}) != len(
            candidates
        ):
            raise ValueError(
                "membership_key values must be unique within an import result"
            )
        if any(not isinstance(item, ImportDiagnostic) for item in diagnostics):
            raise ValueError("diagnostics must contain ImportDiagnostic values")
        if (
            self.outcome
            in {
                ImportOutcome.SUPPORTED,
                ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT,
            }
            and self.snapshot is None
        ):
            raise ValueError("a supported result requires a source snapshot")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "diagnostics", diagnostics)


class CubeSource(Protocol):
    """Application port implemented by provider-specific source adapters."""

    def import_cube(self, request: SourceRequest) -> ImportResult:
        """Return source-preserving candidates, diagnostics, and an outcome."""
