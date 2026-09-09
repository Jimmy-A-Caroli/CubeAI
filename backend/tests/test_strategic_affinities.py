"""Tests for the separate macro-path/package v1 contract."""

import json
from pathlib import Path

import pytest

from cubeai.lab.application.strategic_affinities import assignment_set_from_artifact
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


ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "artifacts"
    / "strategic-affinities"
    / "modovintage-strategic-affinities-v1.json"
)


def test_regenerated_baseline_is_empty_and_uses_successor_vocabulary() -> None:
    assignment_set = assignment_set_from_artifact(json.loads(ARTIFACT.read_text()))

    assert assignment_set.vocabulary_version == "vintage-cube-strategic-v1"
    assert assignment_set.assignments == ()


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
