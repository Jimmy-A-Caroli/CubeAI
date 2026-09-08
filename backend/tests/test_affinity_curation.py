"""Tests for the intentional all-UNKNOWN curation starting point."""

from cubeai.lab.application.affinity_curation import (
    assignment_artifact_document,
    curation_worklist_document,
    coverage_report_document,
    empty_assignment_set,
)
from cubeai.lab.application.archetype_affinities import assignment_set_from_artifact
from cubeai.lab.domain.cube import Cube, CubeCard, CubeVersion, ResolutionStatus


def _version() -> CubeVersion:
    return CubeVersion(
        id="current-modovintage-version",
        cube=Cube("cubecobra:modovintage", "MTGO Vintage Cube"),
        cards=(
            CubeCard("membership-a", ResolutionStatus.UNRESOLVED),
            CubeCard("membership-b", ResolutionStatus.UNRESOLVED),
        ),
    )


def test_empty_assignment_set_is_a_valid_all_unknown_artifact() -> None:
    assignment_set = empty_assignment_set(
        _version(), assignment_set_id="modovintage-affinities-v1"
    )

    artifact = assignment_artifact_document(assignment_set)

    assert assignment_set_from_artifact(artifact) == assignment_set
    assert artifact["assignment_set"] == {
        "id": "modovintage-affinities-v1",
        "cube_version_id": "current-modovintage-version",
        "vocabulary_version": "vintage-cube-archetypes-v0",
        "assignments": [],
    }


def test_coverage_report_keeps_unknown_separate_from_none() -> None:
    assignment_set = empty_assignment_set(
        _version(), assignment_set_id="modovintage-affinities-v1"
    )

    report = coverage_report_document(assignment_set, _version())

    assert report["membership_resolution"] == {
        "total": 2,
        "resolved_card_identities": 0,
        "unresolved_or_custom": 2,
    }
    assert report["coverage"]["unknown_unreviewed_memberships"] == 2
    assert report["coverage"]["explicit_none_assignments"] == 0


def test_worklist_exposes_identity_choices_but_no_proposed_affinities() -> None:
    worklist = curation_worklist_document(_version())

    assert worklist["cube_version_id"] == "current-modovintage-version"
    assert worklist["memberships"] == [
        {
            "membership_id": "membership-a",
            "card_identity_id": None,
            "card_name": None,
            "recommended_identity_scope": "cube_membership",
            "review_state": "unknown",
        },
        {
            "membership_id": "membership-b",
            "card_identity_id": None,
            "card_name": None,
            "recommended_identity_scope": "cube_membership",
            "review_state": "unknown",
        },
    ]
