"""Assemble immutable, provider-neutral CubeVersion snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from cubeai.lab.application.imports import (
    CandidateResolution,
    ImportOutcome,
    ImportResult,
    SourceSnapshotReference,
)
from cubeai.lab.application.metadata import (
    MetadataResolution,
    MetadataResolutionOutcome,
    MetadataResolutionSnapshot,
    ResolvedPrinting,
)
from cubeai.lab.domain.cube import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    ResolutionStatus,
    SourceReference,
)


class CubeVersionAssemblyOutcome(StrEnum):
    """Whether a source snapshot produced a version usable for validation."""

    USABLE = "usable"
    UNUSABLE = "unusable"
    NOT_ASSEMBLED = "not_assembled"


class CubeVersionAssemblyDiagnosticCode(StrEnum):
    """Provider-neutral reasons an assembly is not fully usable."""

    IMPORT_NOT_SUPPORTED = "import_not_supported"
    RESOLUTION_SNAPSHOT_MISMATCH = "resolution_snapshot_mismatch"
    UNRESOLVED_MEMBERSHIP = "unresolved_membership"
    CUSTOM_MEMBERSHIP = "custom_membership"
    INVALID_RESOLUTION = "invalid_resolution"


@dataclass(frozen=True, slots=True)
class CubeVersionAssemblyDiagnostic:
    code: CubeVersionAssemblyDiagnosticCode
    message: str
    source_snapshot: SourceSnapshotReference | None = None
    membership_key: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, CubeVersionAssemblyDiagnosticCode):
            raise ValueError("code must be a CubeVersionAssemblyDiagnosticCode")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a nonblank string")
        if self.source_snapshot is not None and not isinstance(
            self.source_snapshot, SourceSnapshotReference
        ):
            raise ValueError("source_snapshot must be a SourceSnapshotReference or None")
        if self.membership_key is not None and (
            not isinstance(self.membership_key, str) or not self.membership_key.strip()
        ):
            raise ValueError("membership_key must be a nonblank string or None")


@dataclass(frozen=True, slots=True)
class CubeVersionAssemblyResult:
    """A reviewable boundary result; an unusable version is never hidden."""

    outcome: CubeVersionAssemblyOutcome
    cube_version: CubeVersion | None
    diagnostics: tuple[CubeVersionAssemblyDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, CubeVersionAssemblyOutcome):
            raise ValueError("outcome must be a CubeVersionAssemblyOutcome")
        if self.cube_version is not None and not isinstance(
            self.cube_version, CubeVersion
        ):
            raise ValueError("cube_version must be a CubeVersion or None")
        diagnostics = tuple(self.diagnostics)
        if any(
            not isinstance(item, CubeVersionAssemblyDiagnostic) for item in diagnostics
        ):
            raise ValueError(
                "diagnostics must contain CubeVersionAssemblyDiagnostic values"
            )
        if self.outcome is CubeVersionAssemblyOutcome.NOT_ASSEMBLED:
            if self.cube_version is not None:
                raise ValueError("a not_assembled result cannot contain a CubeVersion")
        elif self.cube_version is None:
            raise ValueError("an assembled result requires a CubeVersion")
        object.__setattr__(self, "diagnostics", diagnostics)


_RESOLVED_OUTCOMES = frozenset(
    {
        MetadataResolutionOutcome.RESOLVED,
        MetadataResolutionOutcome.CACHED_FRESH,
        MetadataResolutionOutcome.CACHED_STALE,
    }
)
_SUPPORTED_IMPORT_OUTCOMES = frozenset(
    {
        ImportOutcome.SUPPORTED,
        ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT,
    }
)


def assemble_cube_version(
    import_result: ImportResult,
    resolution_snapshot: MetadataResolutionSnapshot,
    *,
    cube_id: str,
    cube_name: str,
) -> CubeVersionAssemblyResult:
    """Freeze one accepted import and resolution snapshot into a CubeVersion.

    The input source order is retained.  Resolution lookups may have been
    deduplicated remotely, but every source membership is assembled separately.
    """

    if not isinstance(import_result, ImportResult):
        raise ValueError("import_result must be an ImportResult")
    if not isinstance(resolution_snapshot, MetadataResolutionSnapshot):
        raise ValueError("resolution_snapshot must be a MetadataResolutionSnapshot")
    if import_result.outcome not in _SUPPORTED_IMPORT_OUTCOMES:
        return CubeVersionAssemblyResult(
            CubeVersionAssemblyOutcome.NOT_ASSEMBLED,
            None,
            (
                CubeVersionAssemblyDiagnostic(
                    CubeVersionAssemblyDiagnosticCode.IMPORT_NOT_SUPPORTED,
                    (
                        f"Import outcome {import_result.outcome.value} cannot assemble "
                        "a CubeVersion."
                    ),
                    import_result.snapshot,
                ),
            ),
        )
    if import_result.snapshot is None:
        raise ValueError("a supported ImportResult requires a source snapshot")

    resolutions = {
        item.candidate.membership_key: item for item in resolution_snapshot.resolutions
    }
    source_keys = tuple(
        candidate.membership_key for candidate in import_result.candidates
    )
    mismatched_candidate = next(
        (
            candidate
            for candidate in import_result.candidates
            if candidate.membership_key not in resolutions
            or resolutions[candidate.membership_key].candidate != candidate
        ),
        None,
    )
    if set(resolutions) != set(source_keys) or mismatched_candidate is not None:
        return CubeVersionAssemblyResult(
            CubeVersionAssemblyOutcome.NOT_ASSEMBLED,
            None,
            (
                CubeVersionAssemblyDiagnostic(
                    CubeVersionAssemblyDiagnosticCode.RESOLUTION_SNAPSHOT_MISMATCH,
                    "Resolution results must exactly match imported memberships.",
                    import_result.snapshot,
                    (
                        mismatched_candidate.membership_key
                        if mismatched_candidate is not None
                        else None
                    ),
                ),
            ),
        )

    cards: list[CubeCard] = []
    diagnostics: list[CubeVersionAssemblyDiagnostic] = []
    for candidate in import_result.candidates:
        resolution = resolutions[candidate.membership_key]
        card, diagnostic = _assemble_membership(candidate.source_snapshot, resolution)
        cards.append(card)
        if diagnostic is not None:
            diagnostics.append(diagnostic)

    source_reference = SourceReference(
        import_result.snapshot.source, import_result.snapshot.snapshot_id
    )
    cube = Cube(cube_id, cube_name, source_reference)
    fingerprint = _fingerprint(cube, cards, source_reference)
    version = CubeVersion(
        id=f"sha256:{fingerprint}",
        cube=cube,
        cards=tuple(cards),
        source_reference=source_reference,
        resolution_snapshot_id=resolution_snapshot.snapshot_id,
        content_fingerprint=fingerprint,
    )
    outcome = (
        CubeVersionAssemblyOutcome.USABLE
        if not diagnostics
        else CubeVersionAssemblyOutcome.UNUSABLE
    )
    return CubeVersionAssemblyResult(outcome, version, tuple(diagnostics))


def _assemble_membership(
    snapshot: SourceSnapshotReference, resolution: MetadataResolution
) -> tuple[CubeCard, CubeVersionAssemblyDiagnostic | None]:
    candidate = resolution.candidate
    reference = SourceReference(snapshot.source, candidate.membership_key)
    if (
        resolution.outcome in _RESOLVED_OUTCOMES
        and resolution.printing is not None
        and resolution.printing.oracle_id is not None
    ):
        card = _resolved_card(candidate.membership_key, reference, resolution.printing)
        return card, None

    if candidate.resolution is CandidateResolution.CUSTOM:
        code = CubeVersionAssemblyDiagnosticCode.CUSTOM_MEMBERSHIP
        status = ResolutionStatus.CUSTOM
        message = "Custom membership has no resolved printing identity."
    elif resolution.outcome is MetadataResolutionOutcome.CUSTOM_OR_UNRESOLVED:
        code = CubeVersionAssemblyDiagnosticCode.UNRESOLVED_MEMBERSHIP
        status = ResolutionStatus.UNRESOLVED
        message = "Membership has no exact resolved printing identity."
    else:
        code = CubeVersionAssemblyDiagnosticCode.INVALID_RESOLUTION
        status = ResolutionStatus.UNRESOLVED
        message = (
            "Resolved printing lacks card-level Oracle identity."
            if resolution.outcome in _RESOLVED_OUTCOMES
            else f"Membership resolution ended as {resolution.outcome.value}."
        )
    return (
        CubeCard(candidate.membership_key, status, source_reference=reference),
        CubeVersionAssemblyDiagnostic(
            code, message, snapshot, candidate.membership_key
        ),
    )


def _resolved_card(
    membership_key: str,
    membership_reference: SourceReference,
    printing: ResolvedPrinting,
) -> CubeCard:
    assert printing.oracle_id is not None
    identity = CardIdentity(
        id=printing.oracle_id,
        name=printing.name,
        resolution_status=ResolutionStatus.RESOLVED,
        oracle_id=printing.oracle_id,
        source_reference=SourceReference(printing.provider, printing.oracle_id),
    )
    card_printing = CardPrinting(
        id=printing.printing_id,
        card_identity=identity,
        source_reference=SourceReference(printing.provider, printing.printing_id),
    )
    return CubeCard(
        id=membership_key,
        resolution_status=ResolutionStatus.RESOLVED,
        printing=card_printing,
        source_reference=membership_reference,
    )


def _fingerprint(
    cube: Cube, cards: list[CubeCard], source_snapshot: SourceReference
) -> str:
    payload = {
        "cube": {"id": cube.id, "source": _reference_payload(cube.source_reference)},
        "source_snapshot": _reference_payload(source_snapshot),
        "memberships": [_card_payload(card) for card in cards],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _card_payload(card: CubeCard) -> dict[str, object]:
    printing = card.printing
    return {
        "id": card.id,
        "resolution_status": card.resolution_status.value,
        "source": _reference_payload(card.source_reference),
        "printing": None
        if printing is None
        else {
            "id": printing.id,
            "source": _reference_payload(printing.source_reference),
            "identity": {
                "id": printing.card_identity.id,
                "name": printing.card_identity.name,
                "oracle_id": printing.card_identity.oracle_id,
                "source": _reference_payload(printing.card_identity.source_reference),
            },
        },
    }


def _reference_payload(reference: SourceReference | None) -> dict[str, str] | None:
    if reference is None:
        return None
    return {"source": reference.source, "external_id": reference.external_id}
