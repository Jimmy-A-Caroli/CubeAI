"""Provider-neutral metadata-resolution values and port.

This boundary records a provider printing separately from a candidate's Cube
membership and any Oracle identity.  It deliberately does not create Cube
versions or decide whether an unresolved membership is acceptable.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from cubeai.lab.application.imports import ImportCandidate


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


class MetadataResolutionOutcome(StrEnum):
    """The complete, non-throwing outcome taxonomy for one membership."""

    RESOLVED = "resolved"
    CACHED_FRESH = "cached_fresh"
    CACHED_STALE = "cached_stale"
    INVALID_REFERENCE = "invalid_reference"
    NOT_FOUND = "not_found"
    CUSTOM_OR_UNRESOLVED = "custom_or_unresolved"
    PROVIDER_RATE_LIMITED = "provider_rate_limited"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    NETWORK_FAILURE = "network_failure"
    PROVIDER_CONTRACT_FAILURE = "provider_contract_failure"


class MetadataDiagnosticCode(StrEnum):
    ORACLE_ID_MISMATCH = "oracle_id_mismatch"
    FACE_ORACLE_ID_MISMATCH = "face_oracle_id_mismatch"


@dataclass(frozen=True, slots=True)
class MetadataDiagnostic:
    code: MetadataDiagnosticCode
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, MetadataDiagnosticCode):
            raise ValueError("code must be a MetadataDiagnosticCode")
        _require_text(self.message, "message")


@dataclass(frozen=True, slots=True)
class ScryfallFace:
    """The small face-level identity/display subset needed by the M1 policy."""

    name: str
    oracle_id: str | None
    image_uris: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        if self.oracle_id is not None:
            _require_text(self.oracle_id, "oracle_id")
        image_uris = tuple(self.image_uris)
        if any(
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(value, str)
            or not value.startswith("https://")
            for key, value in image_uris
        ):
            raise ValueError("image_uris must contain HTTPS name/URI pairs")
        object.__setattr__(self, "image_uris", image_uris)


@dataclass(frozen=True, slots=True)
class ResolvedPrinting:
    """A provider record, never a replacement Cube membership identity."""

    provider: str
    printing_id: str
    oracle_id: str | None
    name: str
    set_code: str
    collector_number: str
    language: str
    layout: str
    faces: tuple[ScryfallFace, ...]
    image_uris: tuple[tuple[str, str], ...]
    original_reference: str
    fetched_at: str
    response_schema_version: int = 1
    mana_cost: str | None = None
    type_line: str | None = None
    oracle_text: str | None = None
    power: str | None = None
    toughness: str | None = None
    loyalty: str | None = None

    def __post_init__(self) -> None:
        for field, value in (
            ("provider", self.provider),
            ("printing_id", self.printing_id),
            ("name", self.name),
            ("set_code", self.set_code),
            ("collector_number", self.collector_number),
            ("language", self.language),
            ("layout", self.layout),
            ("original_reference", self.original_reference),
            ("fetched_at", self.fetched_at),
        ):
            _require_text(value, field)
        if self.oracle_id is not None:
            _require_text(self.oracle_id, "oracle_id")
        for field in (
            "mana_cost",
            "type_line",
            "oracle_text",
            "power",
            "toughness",
            "loyalty",
        ):
            value = getattr(self, field)
            if value is not None:
                _require_text(value, field)
        faces = tuple(self.faces)
        images = tuple(self.image_uris)
        if any(not isinstance(face, ScryfallFace) for face in faces):
            raise ValueError("faces must contain ScryfallFace values")
        if any(
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(value, str)
            or not value.startswith("https://")
            for key, value in images
        ):
            raise ValueError("image_uris must contain HTTPS name/URI pairs")
        if (
            not isinstance(self.response_schema_version, int)
            or self.response_schema_version < 1
        ):
            raise ValueError("response_schema_version must be a positive integer")
        object.__setattr__(self, "faces", faces)
        object.__setattr__(self, "image_uris", images)


@dataclass(frozen=True, slots=True)
class MetadataResolution:
    """Resolution result for exactly one source membership occurrence."""

    candidate: ImportCandidate
    outcome: MetadataResolutionOutcome
    printing: ResolvedPrinting | None = None
    cache_reference: str | None = None
    diagnostics: tuple[MetadataDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, ImportCandidate):
            raise ValueError("candidate must be an ImportCandidate")
        if not isinstance(self.outcome, MetadataResolutionOutcome):
            raise ValueError("outcome must be a MetadataResolutionOutcome")
        if self.printing is not None and not isinstance(
            self.printing, ResolvedPrinting
        ):
            raise ValueError("printing must be a ResolvedPrinting or None")
        if self.cache_reference is not None:
            _require_text(self.cache_reference, "cache_reference")
        diagnostics = tuple(self.diagnostics)
        if any(not isinstance(item, MetadataDiagnostic) for item in diagnostics):
            raise ValueError("diagnostics must contain MetadataDiagnostic values")
        if (
            self.outcome
            in {
                MetadataResolutionOutcome.RESOLVED,
                MetadataResolutionOutcome.CACHED_FRESH,
                MetadataResolutionOutcome.CACHED_STALE,
            }
            and self.printing is None
        ):
            raise ValueError("a resolved outcome requires a printing")
        if self.printing is not None and self.cache_reference is None:
            raise ValueError("a printing requires a cache_reference")
        object.__setattr__(self, "diagnostics", diagnostics)


@dataclass(frozen=True, slots=True)
class MetadataResolutionSnapshot:
    """An immutable import-time record for later CubeVersion assembly."""

    snapshot_id: str
    retrieved_at: str
    resolutions: tuple[MetadataResolution, ...]

    def __post_init__(self) -> None:
        _require_text(self.snapshot_id, "snapshot_id")
        _require_text(self.retrieved_at, "retrieved_at")
        resolutions = tuple(self.resolutions)
        if any(not isinstance(item, MetadataResolution) for item in resolutions):
            raise ValueError("resolutions must contain MetadataResolution values")
        membership_keys = [item.candidate.membership_key for item in resolutions]
        if len(set(membership_keys)) != len(membership_keys):
            raise ValueError("resolutions must contain unique membership keys")
        object.__setattr__(self, "resolutions", resolutions)


class MetadataResolver(Protocol):
    """Application port for provider-neutral candidate resolution."""

    def resolve(
        self,
        candidates: tuple[ImportCandidate, ...],
        *,
        offline: bool = False,
    ) -> MetadataResolutionSnapshot:
        """Return one deterministic structured result for every candidate."""


@runtime_checkable
class CardMetadataLookup(Protocol):
    """Read the approved display subset for one already-resolved printing."""

    def lookup_printing(self, printing_id: str) -> ResolvedPrinting | None: ...
