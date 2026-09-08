"""Contract tests for reviewed, non-scoring archetype-affinity artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cubeai.lab.application.archetype_affinities import (
    assignment_set_from_json_document,
    load_assignment_set,
)
from cubeai.lab.domain.archetypes import (
    ArchetypeAffinityAssignment,
    ArchetypeAffinityAssignmentSet,
    ArchetypeKey,
    AssignmentIdentityScope,
    AssignmentProvenance,
    AssignmentReviewStatus,
    AffinitySupportLevel,
    assignment_coverage,
    validate_assignment_set,
)
from cubeai.lab.domain.cube import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    ResolutionStatus,
)


FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "synthetic"
    / "archetype-affinity-assignment-v0.json"
)


def _membership(membership_id: str, identity_id: str) -> CubeCard:
    return CubeCard(
        id=membership_id,
        resolution_status=ResolutionStatus.RESOLVED,
        printing=CardPrinting(
            id=f"printing:{membership_id}",
            card_identity=CardIdentity(
                id=identity_id,
                name=f"Synthetic {identity_id}",
                resolution_status=ResolutionStatus.RESOLVED,
                oracle_id=f"oracle:{identity_id}",
            ),
        ),
    )


def _cube_version() -> CubeVersion:
    return CubeVersion(
        id="synthetic-cube-version-1",
        cube=Cube(id="synthetic-cube", name="Synthetic Cube"),
        cards=(
            _membership("membership-strong", "identity-strong"),
            _membership("membership-shared-a", "identity-shared"),
            _membership("membership-shared-b", "identity-shared"),
            _membership("membership-none", "identity-none"),
            _membership("membership-unreviewed", "identity-unreviewed"),
        ),
    )


def test_synthetic_assignment_artifact_validates_scope_version_and_coverage() -> None:
    assignment_set = load_assignment_set(FIXTURE)
    coverage = assignment_coverage(assignment_set, _cube_version())

    assert assignment_set.vocabulary_version == "vintage-cube-archetypes-v0"
    assert (coverage.total_memberships, coverage.reviewed_memberships) == (5, 4)
    assert coverage.unreviewed_memberships == 1
    assert coverage.explicit_none_assignments == 1
    assert dict(coverage.archetype_coverage) == {
        ArchetypeKey.AGGRO: 0,
        ArchetypeKey.CONTROL: 0,
        ArchetypeKey.MIDRANGE: 0,
        ArchetypeKey.REANIMATOR: 1,
        ArchetypeKey.ARTIFACTS: 2,
        ArchetypeKey.RAMP: 2,
    }
    assert coverage.multi_archetype_memberships == 2
    assert dict(coverage.provenance_counts) == {
        AssignmentProvenance.SOURCE_PROVIDED: 1,
        AssignmentProvenance.CURATOR_DEFINED: 2,
        AssignmentProvenance.HUMAN_ANNOTATED: 2,
        AssignmentProvenance.RULE_DERIVED: 0,
        AssignmentProvenance.MODEL_INFERRED: 0,
    }
    assert coverage.ambiguity_count == 0


def test_unknown_is_absence_of_a_reviewed_assignment_not_explicit_none() -> None:
    assignment_set = ArchetypeAffinityAssignmentSet(
        id="empty-review",
        cube_version_id="synthetic-cube-version-1",
        vocabulary_version="vintage-cube-archetypes-v0",
        assignments=(),
    )

    coverage = assignment_coverage(assignment_set, _cube_version())

    assert coverage.reviewed_memberships == 0
    assert coverage.unreviewed_memberships == 5
    assert coverage.explicit_none_assignments == 0


def test_active_assignment_rejects_inactive_provenance() -> None:
    with pytest.raises(ValueError, match="active assignments require"):
        ArchetypeAffinityAssignment(
            target_id="membership-strong",
            identity_scope=AssignmentIdentityScope.CUBE_MEMBERSHIP,
            archetype=ArchetypeKey.REANIMATOR,
            support_level=AffinitySupportLevel.STRONG,
            provenance=AssignmentProvenance.SOURCE_PROVIDED,
            review_status=AssignmentReviewStatus.ACTIVE,
        )


def test_validation_rejects_wrong_version_and_wrong_identity_scope() -> None:
    wrong_version = ArchetypeAffinityAssignmentSet(
        id="wrong-version",
        cube_version_id="another-version",
        vocabulary_version="vintage-cube-archetypes-v0",
        assignments=(),
    )
    with pytest.raises(ValueError, match="exact CubeVersion"):
        validate_assignment_set(wrong_version, _cube_version())

    wrong_scope = ArchetypeAffinityAssignmentSet(
        id="wrong-scope",
        cube_version_id="synthetic-cube-version-1",
        vocabulary_version="vintage-cube-archetypes-v0",
        assignments=(
            ArchetypeAffinityAssignment(
                target_id="membership-strong",
                identity_scope=AssignmentIdentityScope.CARD_IDENTITY,
                archetype=ArchetypeKey.REANIMATOR,
                support_level=AffinitySupportLevel.SUPPORTS,
                provenance=AssignmentProvenance.HUMAN_ANNOTATED,
                review_status=AssignmentReviewStatus.REVIEWED,
            ),
        ),
    )
    with pytest.raises(ValueError, match="card_identity target"):
        validate_assignment_set(wrong_scope, _cube_version())


def test_duplicate_records_and_reviewed_conflicts_remain_diagnosable() -> None:
    first = ArchetypeAffinityAssignment(
        target_id="membership-strong",
        identity_scope=AssignmentIdentityScope.CUBE_MEMBERSHIP,
        archetype=ArchetypeKey.REANIMATOR,
        support_level=AffinitySupportLevel.SUPPORTS,
        provenance=AssignmentProvenance.HUMAN_ANNOTATED,
        review_status=AssignmentReviewStatus.REVIEWED,
    )
    with pytest.raises(ValueError, match="must not repeat"):
        ArchetypeAffinityAssignmentSet(
            id="duplicate",
            cube_version_id="synthetic-cube-version-1",
            vocabulary_version="vintage-cube-archetypes-v0",
            assignments=(first, first),
        )

    conflict = ArchetypeAffinityAssignmentSet(
        id="overlap",
        cube_version_id="synthetic-cube-version-1",
        vocabulary_version="vintage-cube-archetypes-v0",
        assignments=(
            first,
            ArchetypeAffinityAssignment(
                target_id="identity-strong",
                identity_scope=AssignmentIdentityScope.CARD_IDENTITY,
                archetype=ArchetypeKey.REANIMATOR,
                support_level=AffinitySupportLevel.NONE,
                provenance=AssignmentProvenance.CURATOR_DEFINED,
                review_status=AssignmentReviewStatus.REVIEWED,
            ),
        ),
    )
    assert assignment_coverage(conflict, _cube_version()).ambiguity_count == 1


def test_json_loader_rejects_unknown_keys_and_malformed_json(tmp_path: Path) -> None:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["unexpected"] = True
    with pytest.raises(ValueError, match="document keys"):
        assignment_set_from_json_document(document)

    path = tmp_path / "invalid.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid assignment artifact JSON"):
        load_assignment_set(path)
