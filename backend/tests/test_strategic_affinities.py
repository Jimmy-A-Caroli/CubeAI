"""Tests for the separate macro-path/package v1 contract."""

import json
from pathlib import Path

import pytest

from cubeai.lab.application.strategic_affinities import assignment_set_from_artifact
from cubeai.lab.application.strategic_curation import (
    empty_strategic_assignment_set,
    strategic_assignment_artifact_document,
    strategic_coverage_report_document,
)
from cubeai.lab.application.strategic_proposals import (
    proposal_set_from_artifact,
    validate_proposal_set,
)
from cubeai.lab.domain.archetypes import (
    AffinitySupportLevel,
    AssignmentIdentityScope,
    AssignmentProvenance,
    AssignmentReviewStatus,
)
from cubeai.lab.domain.strategic_vocabulary import (
    MacroPathKeyV1,
    PackageKeyV1,
    StrategicAffinityAssignment,
    StrategicAffinityAssignmentSet,
    StrategicTargetType,
)
from cubeai.lab.domain.cube import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    ResolutionStatus,
)


ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "artifacts"
    / "strategic-affinities"
    / "modovintage-strategic-affinities-v1.json"
)
SUCCESSOR_ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "artifacts"
    / "strategic-affinities"
    / "modovintage-strategic-affinities-v1-2026-09-09.json"
)
SUCCESSOR_COVERAGE = SUCCESSOR_ARTIFACT.with_name(
    "modovintage-strategic-affinities-v1-2026-09-09-coverage.json"
)
PROPOSALS = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "artifacts"
    / "strategic-affinity-proposals"
    / "modovintage-strategic-proposals-v1-2026-09-09.json"
)
RECOVERED_VERSION_ID = "sha256:17a9b63fd0a596760fa1205b24b93216e89e899811f7e4c105ea4e3ca3acac70"


def test_regenerated_baseline_is_empty_and_uses_successor_vocabulary() -> None:
    assignment_set = assignment_set_from_artifact(json.loads(ARTIFACT.read_text()))

    assert assignment_set.vocabulary_version == "vintage-cube-strategic-v1"
    assert assignment_set.assignments == ()


def test_successor_baseline_binds_only_the_recovered_version() -> None:
    assignment_set = assignment_set_from_artifact(
        json.loads(SUCCESSOR_ARTIFACT.read_text())
    )
    coverage = json.loads(SUCCESSOR_COVERAGE.read_text())

    assert assignment_set.cube_version_id == RECOVERED_VERSION_ID
    assert assignment_set.assignments == ()
    assert coverage["membership_resolution"] == {
        "total": 540,
        "resolved_card_identities": 540,
        "unresolved_or_custom": 0,
    }
    assert coverage["coverage"]["unknown_unreviewed_memberships"] == 540
    assert coverage["coverage"]["explicit_none_assignments"] == 0


def test_proposals_are_not_active_assignments() -> None:
    document = json.loads(PROPOSALS.read_text())
    proposal_set = document["proposal_set"]

    assert document["artifact_type"] == "cubeai.strategic-affinity-proposal-set"
    assert proposal_set["cube_version_id"] == RECOVERED_VERSION_ID
    assert proposal_set["status"] == "proposed"
    assert len(proposal_set["proposals"]) == 25
    assert all(
        "provenance" not in proposal and "review_status" not in proposal
        for proposal in proposal_set["proposals"]
    )
    with pytest.raises(ValueError, match="missing or unknown keys"):
        assignment_set_from_artifact(document)
    assert proposal_set_from_artifact(document).cube_version_id == RECOVERED_VERSION_ID


def test_proposal_parser_rejects_active_fields_and_unknown_evidence() -> None:
    document = json.loads(PROPOSALS.read_text())
    document["proposal_set"]["proposals"][0]["review_status"] = "active"

    with pytest.raises(ValueError, match="active-assignment keys"):
        proposal_set_from_artifact(document)

    document = json.loads(PROPOSALS.read_text())
    document["proposal_set"]["proposals"][0]["source_ids"] = ["not-declared"]

    with pytest.raises(ValueError, match="declared evidence"):
        proposal_set_from_artifact(document)


def test_proposals_require_exact_version_membership() -> None:
    document = json.loads(PROPOSALS.read_text())
    document["proposal_set"]["proposals"] = [
        {
            "target_id": "member-1",
            "identity_scope": "cube_membership",
            "target_type": "package",
            "target": "artifacts",
            "support_level": "supports",
            "source_ids": ["mtgo-vintage-cube-beginners-guide"],
            "rationale": "Synthetic validation only.",
        }
    ]
    proposal_set = proposal_set_from_artifact(document)

    validate_proposal_set(proposal_set, _recovered_version())
    wrong_version = CubeVersion(
        "other-version", _recovered_version().cube, _recovered_version().cards
    )
    with pytest.raises(ValueError, match="exact CubeVersion"):
        validate_proposal_set(proposal_set, wrong_version)
    document["proposal_set"]["proposals"][0]["target_id"] = "missing-member"
    proposal_set = proposal_set_from_artifact(document)

    with pytest.raises(ValueError, match="absent from CubeVersion"):
        validate_proposal_set(proposal_set, _recovered_version())


def test_macro_paths_and_packages_are_distinct_but_can_overlap() -> None:
    macro = StrategicAffinityAssignment(
        "member-1",
        AssignmentIdentityScope.CUBE_MEMBERSHIP,
        StrategicTargetType.MACRO_PATH,
        MacroPathKeyV1.CONTROL,
        AffinitySupportLevel.SUPPORTS,
        AssignmentProvenance.HUMAN_ANNOTATED,
        AssignmentReviewStatus.ACTIVE,
    )
    package = StrategicAffinityAssignment(
        "member-1",
        AssignmentIdentityScope.CUBE_MEMBERSHIP,
        StrategicTargetType.PACKAGE,
        PackageKeyV1.ARTIFACTS,
        AffinitySupportLevel.STRONG,
        AssignmentProvenance.CURATOR_DEFINED,
        AssignmentReviewStatus.ACTIVE,
    )
    assignment_set = StrategicAffinityAssignmentSet(
        "synthetic-v1",
        "synthetic-version",
        "vintage-cube-strategic-v1",
        (macro, package),
    )

    assert len(assignment_set.assignments) == 2


def test_target_type_rejects_wrong_vocabulary_namespace() -> None:
    with pytest.raises(ValueError, match="MacroPathKeyV1"):
        StrategicAffinityAssignment(
            "member-1",
            AssignmentIdentityScope.CUBE_MEMBERSHIP,
            StrategicTargetType.MACRO_PATH,
            PackageKeyV1.ARTIFACTS,
            AffinitySupportLevel.SUPPORTS,
            AssignmentProvenance.HUMAN_ANNOTATED,
            AssignmentReviewStatus.REVIEWED,
        )


def _recovered_version() -> CubeVersion:
    identity = CardIdentity(
        "oracle-1", "Synthetic Anchor", ResolutionStatus.RESOLVED, "oracle-1"
    )
    return CubeVersion(
        "sha256:17a9b63fd0a596760fa1205b24b93216e89e899811f7e4c105ea4e3ca3acac70",
        Cube("cubecobra:modovintage", "Synthetic Cube"),
        (
            CubeCard(
                "member-1",
                ResolutionStatus.RESOLVED,
                CardPrinting("printing-1", identity),
            ),
            CubeCard(
                "member-2",
                ResolutionStatus.RESOLVED,
                CardPrinting("printing-2", identity),
            ),
        ),
    )


def test_successor_baseline_keeps_all_memberships_unknown() -> None:
    version = _recovered_version()
    assignment_set = empty_strategic_assignment_set(
        version, assignment_set_id="modovintage-strategic-affinities-v1-2026-09-09"
    )

    assert assignment_set_from_artifact(
        strategic_assignment_artifact_document(assignment_set)
    ) == assignment_set
    report = strategic_coverage_report_document(assignment_set, version)

    assert report["cube_version_id"] == version.id
    assert report["membership_resolution"] == {
        "total": 2,
        "resolved_card_identities": 2,
        "unresolved_or_custom": 0,
    }
    assert report["coverage"]["reviewed_memberships"] == 0
    assert report["coverage"]["unknown_unreviewed_memberships"] == 2
    assert report["coverage"]["explicit_none_assignments"] == 0
