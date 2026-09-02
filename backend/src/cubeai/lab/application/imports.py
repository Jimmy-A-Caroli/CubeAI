"""Provider-neutral import candidates and source adapter port."""

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
    TRANSPORT_FAILURE = "transport_failure"
    UNSUPPORTED_SOURCE_CONTRACT = "unsupported_source_contract"
    INVALID_SOURCE_RECORD = "invalid_source_record"


class CandidateResolution(StrEnum):
    UNRESOLVED = "unresolved"
    CUSTOM = "custom"
    RESOLUTION_HINTED = "resolution_hinted"


@dataclass(frozen=True, slots=True)
class SourceRequest:
    source: str
    identifier: str

    def __post_init__(self) -> None:
        _require_text(self.source, "source")
        _require_text(self.identifier, "identifier")


@dataclass(frozen=True, slots=True)
class SourceSnapshotReference:
    source: str
    snapshot_id: str
    retrieved_at: str
    source_uri: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.source, "source")
        _require_text(self.snapshot_id, "snapshot_id")
        _require_text(self.retrieved_at, "retrieved_at")
        if self.source_uri is not None:
            _require_text(self.source_uri, "source_uri")


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
    custom_name: str | None = None
    resolution: CandidateResolution = CandidateResolution.UNRESOLVED
    raw_field_references: tuple[str, ...] = ()

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
            ("custom_name", self.custom_name),
        ):
            if value is not None:
                _require_text(value, field)
        if not isinstance(self.resolution, CandidateResolution):
            raise ValueError("resolution must be a CandidateResolution")
        tags = tuple(self.tags)
        references = tuple(self.raw_field_references)
        if any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise ValueError("tags must contain nonblank strings")
        if any(not isinstance(ref, str) or not ref.strip() for ref in references):
            raise ValueError("raw_field_references must contain nonblank strings")
        object.__setattr__(self, "tags", tags)
        object.__setattr__(self, "raw_field_references", references)


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
    snapshot: SourceSnapshotReference
    candidates: tuple[ImportCandidate, ...]
    diagnostics: tuple[ImportDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot, SourceSnapshotReference):
            raise ValueError("snapshot must be a SourceSnapshotReference")
        candidates = tuple(self.candidates)
        diagnostics = tuple(self.diagnostics)
        if any(candidate.source_snapshot != self.snapshot for candidate in candidates):
            raise ValueError("all candidates must reference the result snapshot")
        if len({candidate.membership_key for candidate in candidates}) != len(
            candidates
        ):
            raise ValueError(
                "membership_key values must be unique within an import result"
            )
        if any(not isinstance(item, ImportDiagnostic) for item in diagnostics):
            raise ValueError("diagnostics must contain ImportDiagnostic values")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "diagnostics", diagnostics)


class CubeSource(Protocol):
    """Application port implemented by provider-specific source adapters."""

    def import_cube(self, request: SourceRequest) -> ImportResult:
        """Return source-preserving candidates and diagnostics for a request."""
