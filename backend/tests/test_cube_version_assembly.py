"""Focused tests for the import-to-immutable-CubeVersion boundary."""

from dataclasses import FrozenInstanceError

import pytest

from cubeai.lab.application import (
    CandidateResolution,
    CubeVersionAssemblyDiagnosticCode,
    CubeVersionAssemblyOutcome,
    ImportCandidate,
    ImportOutcome,
    ImportResult,
    MetadataResolution,
    MetadataResolutionOutcome,
    MetadataResolutionSnapshot,
    ResolvedPrinting,
    SourceSnapshotReference,
    assemble_cube_version,
)
from cubeai.lab.domain import ResolutionStatus


def _source_snapshot() -> SourceSnapshotReference:
    return SourceSnapshotReference(
        "synthetic-source", "cube-snapshot-1", "2026-09-03T12:00:00+00:00"
    )


def _candidate(
    key: str,
    position: int,
    *,
    resolution: CandidateResolution = CandidateResolution.RESOLUTION_HINTED,
) -> ImportCandidate:
    return ImportCandidate(
        key,
        _source_snapshot(),
        position,
        printing_hint="printing-1",
        oracle_id="oracle-1",
        resolution=resolution,
    )


def _printing() -> ResolvedPrinting:
    return ResolvedPrinting(
        "scryfall",
        "printing-1",
        "oracle-1",
        "Synthetic Ember",
        "syn",
        "1",
        "en",
        "normal",
        (),
        (),
        "printing-1",
        "2026-09-03T12:00:00+00:00",
    )


def _assembled(*candidates: ImportCandidate):
    imported = ImportResult(_source_snapshot(), candidates)
    resolutions = tuple(
        MetadataResolution(
            candidate,
            MetadataResolutionOutcome.RESOLVED,
            _printing(),
            "scryfall:printing-1:record",
        )
        for candidate in candidates
    )
    return assemble_cube_version(
        imported,
        MetadataResolutionSnapshot(
            "resolution-snapshot-1", "2026-09-03T12:00:00+00:00", resolutions
        ),
        cube_id="cube-1",
        cube_name="Synthetic Cube",
    )


def test_assembly_preserves_order_duplicate_memberships_and_identity_scopes() -> None:
    result = _assembled(_candidate("membership-1", 0), _candidate("membership-2", 1))

    assert result.outcome is CubeVersionAssemblyOutcome.USABLE
    assert result.cube_version is not None
    assert [card.id for card in result.cube_version.cards] == [
        "membership-1",
        "membership-2",
    ]
    first, second = result.cube_version.cards
    assert first != second
    assert first.printing is not None and second.printing is not None
    assert first.printing.id == second.printing.id == "printing-1"
    assert first.printing.card_identity.oracle_id == "oracle-1"
    assert first.source_reference != first.printing.source_reference
    assert result.cube_version.source_reference is not None
    assert result.cube_version.source_reference.external_id == "cube-snapshot-1"
    assert result.cube_version.resolution_snapshot_id == "resolution-snapshot-1"


def test_assembly_is_structurally_immutable_and_detaches_input_collections() -> None:
    candidates = [_candidate("membership-1", 0)]
    result = _assembled(*candidates)
    candidates.append(_candidate("membership-2", 1))

    assert result.cube_version is not None
    assert tuple(card.id for card in result.cube_version.cards) == ("membership-1",)
    with pytest.raises(FrozenInstanceError):
        result.cube_version.cards = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        result.cube_version.cards.append(result.cube_version.cards[0])  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        object.__setattr__(result.cube_version, "unexpected", "mutable state")


def test_same_normalized_content_has_a_stable_fingerprint_and_changes_are_visible() -> (
    None
):
    first = _assembled(_candidate("membership-1", 0))
    same = _assembled(_candidate("membership-1", 0))
    changed = _assembled(_candidate("membership-2", 0))

    assert first.cube_version is not None
    assert same.cube_version is not None
    assert changed.cube_version is not None
    assert (
        first.cube_version.content_fingerprint == same.cube_version.content_fingerprint
    )
    assert first.cube_version == same.cube_version
    assert (
        first.cube_version.content_fingerprint
        != changed.cube_version.content_fingerprint
    )
    assert first.cube_version.id != changed.cube_version.id


def test_unresolved_and_custom_memberships_remain_visible_and_unusable() -> None:
    unresolved = _candidate("membership-1", 0)
    custom = _candidate("membership-2", 1, resolution=CandidateResolution.CUSTOM)
    imported = ImportResult(_source_snapshot(), (unresolved, custom))
    resolution_snapshot = MetadataResolutionSnapshot(
        "resolution-snapshot-1",
        "2026-09-03T12:00:00+00:00",
        (
            MetadataResolution(
                unresolved,
                MetadataResolutionOutcome.CUSTOM_OR_UNRESOLVED,
            ),
            MetadataResolution(
                custom,
                MetadataResolutionOutcome.CUSTOM_OR_UNRESOLVED,
            ),
        ),
    )

    result = assemble_cube_version(
        imported, resolution_snapshot, cube_id="cube-1", cube_name="Synthetic Cube"
    )

    assert result.outcome is CubeVersionAssemblyOutcome.UNUSABLE
    assert result.cube_version is not None
    assert [card.resolution_status for card in result.cube_version.cards] == [
        ResolutionStatus.UNRESOLVED,
        ResolutionStatus.CUSTOM,
    ]
    assert [(item.code, item.membership_key) for item in result.diagnostics] == [
        (CubeVersionAssemblyDiagnosticCode.UNRESOLVED_MEMBERSHIP, "membership-1"),
        (CubeVersionAssemblyDiagnosticCode.CUSTOM_MEMBERSHIP, "membership-2"),
    ]
    assert all(
        item.source_snapshot == _source_snapshot() for item in result.diagnostics
    )


def test_invalid_import_or_mismatched_resolution_cannot_create_a_partial_version() -> (
    None
):
    candidate = _candidate("membership-1", 0)
    unsupported = ImportResult(
        _source_snapshot(), (), outcome=ImportOutcome.UNSUPPORTED
    )
    empty_resolution = MetadataResolutionSnapshot(
        "resolution-snapshot-1", "2026-09-03T12:00:00+00:00", ()
    )
    unsupported_result = assemble_cube_version(
        unsupported, empty_resolution, cube_id="cube-1", cube_name="Synthetic Cube"
    )
    mismatch_result = assemble_cube_version(
        ImportResult(_source_snapshot(), (candidate,)),
        empty_resolution,
        cube_id="cube-1",
        cube_name="Synthetic Cube",
    )

    assert unsupported_result.outcome is CubeVersionAssemblyOutcome.NOT_ASSEMBLED
    assert unsupported_result.cube_version is None
    assert mismatch_result.outcome is CubeVersionAssemblyOutcome.NOT_ASSEMBLED
    assert mismatch_result.cube_version is None
    assert mismatch_result.diagnostics[0].code is (
        CubeVersionAssemblyDiagnosticCode.RESOLUTION_SNAPSHOT_MISMATCH
    )


def test_resolution_cannot_substitute_different_source_evidence_for_same_key() -> None:
    imported_custom = _candidate(
        "membership-1", 0, resolution=CandidateResolution.CUSTOM
    )
    substituted_resolved = _candidate("membership-1", 0)

    result = assemble_cube_version(
        ImportResult(_source_snapshot(), (imported_custom,)),
        MetadataResolutionSnapshot(
            "resolution-snapshot-1",
            "2026-09-03T12:00:00+00:00",
            (
                MetadataResolution(
                    substituted_resolved,
                    MetadataResolutionOutcome.RESOLVED,
                    _printing(),
                    "scryfall:printing-1:record",
                ),
            ),
        ),
        cube_id="cube-1",
        cube_name="Synthetic Cube",
    )

    assert result.outcome is CubeVersionAssemblyOutcome.NOT_ASSEMBLED
    assert result.cube_version is None
    assert result.diagnostics[0].code is (
        CubeVersionAssemblyDiagnosticCode.RESOLUTION_SNAPSHOT_MISMATCH
    )
    assert result.diagnostics[0].membership_key == "membership-1"


def test_resolved_printing_without_card_level_oracle_identity_is_not_usable() -> None:
    candidate = _candidate("membership-1", 0)
    missing_oracle = ResolvedPrinting(
        "scryfall",
        "printing-1",
        None,
        "Synthetic Split",
        "syn",
        "2",
        "en",
        "split",
        (),
        (),
        "printing-1",
        "2026-09-03T12:00:00+00:00",
    )

    result = assemble_cube_version(
        ImportResult(_source_snapshot(), (candidate,)),
        MetadataResolutionSnapshot(
            "resolution-snapshot-1",
            "2026-09-03T12:00:00+00:00",
            (
                MetadataResolution(
                    candidate,
                    MetadataResolutionOutcome.RESOLVED,
                    missing_oracle,
                    "scryfall:printing-1:record",
                ),
            ),
        ),
        cube_id="cube-1",
        cube_name="Synthetic Cube",
    )

    assert result.outcome is CubeVersionAssemblyOutcome.UNUSABLE
    assert result.cube_version is not None
    assert result.cube_version.cards[0].resolution_status is ResolutionStatus.UNRESOLVED
    assert (
        result.diagnostics[0].code
        is CubeVersionAssemblyDiagnosticCode.INVALID_RESOLUTION
    )
