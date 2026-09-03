from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from cubeai.lab.application import (
    CandidateResolution,
    CubeSource,
    DiagnosticCode,
    DiagnosticSeverity,
    ImportCandidate,
    ImportDiagnostic,
    ImportResult,
    SourceRequest,
    SourceSnapshotReference,
)


def _snapshot() -> SourceSnapshotReference:
    return SourceSnapshotReference("test-provider", "snapshot-1", "2026-09-02")


def test_fake_provider_implements_provider_neutral_port() -> None:
    class FakeSource:
        def import_cube(self, request: SourceRequest) -> ImportResult:
            return ImportResult(
                _snapshot(), (ImportCandidate("member-1", _snapshot(), 0),)
            )

    source = cast(CubeSource, FakeSource())
    result = source.import_cube(SourceRequest("test-provider", "cube-1"))
    assert result.candidates[0].membership_key == "member-1"


def test_candidate_preserves_duplicate_memberships_and_source_evidence() -> None:
    snapshot = _snapshot()
    first = ImportCandidate(
        "member-1",
        snapshot,
        0,
        "provider-card",
        "mainboard",
        ("aggro",),
        "note",
        "set/1",
        raw_field_references=("cards.mainboard[0]",),
    )
    second = ImportCandidate(
        "member-2",
        snapshot,
        1,
        "provider-card",
        "mainboard",
        (),
        None,
        "set/1",
        resolution=CandidateResolution.CUSTOM,
    )
    result = ImportResult(snapshot, (first, second))
    assert len(result.candidates) == 2
    assert result.candidates[0].tags == ("aggro",)
    assert result.candidates[1].resolution is CandidateResolution.CUSTOM


@pytest.mark.parametrize("code", list(DiagnosticCode))
def test_diagnostic_codes_are_stable_enums(code: DiagnosticCode) -> None:
    diagnostic = ImportDiagnostic(code, DiagnosticSeverity.ERROR, "diagnostic")
    assert diagnostic.code.value in {
        "source_request_invalid",
        "source_inaccessible",
        "source_rate_limited",
        "source_unavailable",
        "unsupported_source_contract",
        "unsupported_visibility",
        "unsupported_non_mainboard",
        "empty_mainboard",
        "invalid_source_record",
        "unknown_source_shape",
        "optional_source_data_malformed",
    }


def test_malformed_candidate_and_result_are_rejected() -> None:
    snapshot = _snapshot()
    with pytest.raises(ValueError, match="position"):
        ImportCandidate("member-1", snapshot, -1)
    with pytest.raises(ValueError, match="membership_key values"):
        ImportResult(
            snapshot,
            (
                ImportCandidate("member-1", snapshot, 0),
                ImportCandidate("member-1", snapshot, 1),
            ),
        )


def test_import_values_are_frozen_and_provider_neutral() -> None:
    request = SourceRequest("provider", "cube")
    with pytest.raises(FrozenInstanceError):
        request.identifier = "other"  # type: ignore[misc]
    assert "CubeCobra" not in ImportCandidate.__module__
