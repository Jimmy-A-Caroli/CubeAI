"""Approved v1 Vintage Cube macro-path and package affinity values.

This is intentionally separate from the immutable v0 flat-archetype contract.
It defines no score, card classification, or provider-derived assignment.
"""

from dataclasses import dataclass
from enum import StrEnum

from cubeai.lab.domain.archetypes import (
    ACTIVE_PROVENANCE,
    AffinitySupportLevel,
    AssignmentIdentityScope,
    AssignmentProvenance,
    AssignmentReviewStatus,
)
from cubeai.lab.domain.cube import CubeVersion


class StrategicTargetType(StrEnum):
    MACRO_PATH = "macro_path"
    PACKAGE = "package"


class MacroPathKeyV1(StrEnum):
    AGGRO = "aggro"
    CONTROL = "control"
    MIDRANGE_VALUE = "midrange_value"
    BIG_MANA = "big_mana"


class PackageKeyV1(StrEnum):
    REANIMATOR = "reanimator"
    ARTIFACTS = "artifacts"
    CHEAT_CREATURES = "cheat_creatures"
    LANDS_DEPTHS = "lands_depths"


STRATEGIC_VOCABULARY_VERSION_V1 = "vintage-cube-strategic-v1"


def _require_text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")


@dataclass(frozen=True, slots=True)
class StrategicAffinityAssignment:
    target_id: str
    identity_scope: AssignmentIdentityScope
    target_type: StrategicTargetType
    target: MacroPathKeyV1 | PackageKeyV1
    support_level: AffinitySupportLevel
    provenance: AssignmentProvenance
    review_status: AssignmentReviewStatus
    note: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.target_id, "target_id")
        if not isinstance(self.identity_scope, AssignmentIdentityScope):
            raise ValueError("identity_scope must be an AssignmentIdentityScope")
        if not isinstance(self.target_type, StrategicTargetType):
            raise ValueError("target_type must be a StrategicTargetType")
        expected = (
            MacroPathKeyV1
            if self.target_type is StrategicTargetType.MACRO_PATH
            else PackageKeyV1
        )
        if not isinstance(self.target, expected):
            raise ValueError(f"target must be a {expected.__name__} for target_type")
        for field, expected_type in (
            ("support_level", AffinitySupportLevel),
            ("provenance", AssignmentProvenance),
            ("review_status", AssignmentReviewStatus),
        ):
            if not isinstance(getattr(self, field), expected_type):
                raise ValueError(f"{field} must be a {expected_type.__name__}")
        if self.note is not None and (
            not isinstance(self.note, str) or len(self.note) > 2000
        ):
            raise ValueError("note must be at most 2000 characters")
        if (
            self.review_status is AssignmentReviewStatus.ACTIVE
            and self.provenance not in ACTIVE_PROVENANCE
        ):
            raise ValueError("active assignments require curator or human provenance")


@dataclass(frozen=True, slots=True)
class StrategicAffinityAssignmentSet:
    id: str
    cube_version_id: str
    vocabulary_version: str
    assignments: tuple[StrategicAffinityAssignment, ...]

    def __post_init__(self) -> None:
        for field in ("id", "cube_version_id", "vocabulary_version"):
            _require_text(getattr(self, field), field)
        if self.vocabulary_version != STRATEGIC_VOCABULARY_VERSION_V1:
            raise ValueError(
                "assignment set vocabulary_version must be "
                f"{STRATEGIC_VOCABULARY_VERSION_V1!r}"
            )
        assignments = tuple(self.assignments)
        if any(
            not isinstance(item, StrategicAffinityAssignment) for item in assignments
        ):
            raise ValueError(
                "assignments must contain StrategicAffinityAssignment values"
            )
        keys = tuple(
            (item.target_id, item.identity_scope, item.target_type, item.target)
            for item in assignments
        )
        if len(keys) != len(set(keys)):
            raise ValueError("assignments must not repeat a target tuple")
        object.__setattr__(self, "assignments", assignments)


def validate_strategic_assignment_set(
    assignment_set: StrategicAffinityAssignmentSet, cube_version: CubeVersion
) -> None:
    """Validate an explicit v1 assignment set against its exact CubeVersion."""

    if assignment_set.cube_version_id != cube_version.id:
        raise ValueError("assignment set must bind to the exact CubeVersion")
    membership_ids = {card.id for card in cube_version.cards}
    identity_ids = {
        card.printing.card_identity.id
        for card in cube_version.cards
        if card.printing is not None
    }
    for assignment in assignment_set.assignments:
        valid_ids = (
            membership_ids
            if assignment.identity_scope is AssignmentIdentityScope.CUBE_MEMBERSHIP
            else identity_ids
        )
        if assignment.target_id not in valid_ids:
            raise ValueError(
                f"{assignment.identity_scope.value} target is absent from CubeVersion: "
                f"{assignment.target_id}"
            )
