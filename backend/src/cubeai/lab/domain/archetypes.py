"""Reviewed archetype vocabulary and affinity-assignment contract values.

These values deliberately do not score a draft or infer a card's purpose.  They
make a human-curated, CubeVersion-bound assignment set validate and reportable.
"""

from dataclasses import dataclass
from enum import StrEnum

from cubeai.lab.domain.cube import CubeVersion


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


class RoleKey(StrEnum):
    THREAT = "threat"
    REMOVAL = "removal"
    SWEEPER = "sweeper"
    SPELL_COUNTER = "spell_counter"
    CARD_ADVANTAGE = "card_advantage"
    CARD_SELECTION = "card_selection"
    HAND_DISRUPTION = "hand_disruption"
    MANA_ACCELERATION = "mana_acceleration"
    FIXING = "fixing"
    REANIMATION_ENABLER = "reanimation_enabler"
    REANIMATION_PAYOFF = "reanimation_payoff"
    ARTIFACT_ENABLER = "artifact_enabler"
    ARTIFACT_PAYOFF = "artifact_payoff"


class ArchetypeKey(StrEnum):
    AGGRO = "aggro"
    CONTROL = "control"
    MIDRANGE = "midrange"
    REANIMATOR = "reanimator"
    ARTIFACTS = "artifacts"
    RAMP = "ramp"


class AssignmentIdentityScope(StrEnum):
    CUBE_MEMBERSHIP = "cube_membership"
    CARD_IDENTITY = "card_identity"


class AssignmentProvenance(StrEnum):
    SOURCE_PROVIDED = "source_provided"
    CURATOR_DEFINED = "curator_defined"
    HUMAN_ANNOTATED = "human_annotated"
    RULE_DERIVED = "rule_derived"
    MODEL_INFERRED = "model_inferred"


class AssignmentReviewStatus(StrEnum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    ACTIVE = "active"


class AffinitySupportLevel(StrEnum):
    """Human-readable association categories, without a scoring mapping."""

    NONE = "none"
    SUPPORTS = "supports"
    STRONG = "strong"


ACTIVE_PROVENANCE = frozenset(
    (AssignmentProvenance.CURATOR_DEFINED, AssignmentProvenance.HUMAN_ANNOTATED)
)
VOCABULARY_VERSION_V0 = "vintage-cube-archetypes-v0"


@dataclass(frozen=True, slots=True)
class ArchetypeAffinityAssignment:
    target_id: str
    identity_scope: AssignmentIdentityScope
    archetype: ArchetypeKey
    support_level: AffinitySupportLevel
    provenance: AssignmentProvenance
    review_status: AssignmentReviewStatus
    note: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.target_id, "target_id")
        for field, expected_type in (
            ("identity_scope", AssignmentIdentityScope),
            ("archetype", ArchetypeKey),
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
class ArchetypeAffinityAssignmentSet:
    id: str
    cube_version_id: str
    vocabulary_version: str
    assignments: tuple[ArchetypeAffinityAssignment, ...]

    def __post_init__(self) -> None:
        for field in ("id", "cube_version_id", "vocabulary_version"):
            _require_text(getattr(self, field), field)
        assignments = tuple(self.assignments)
        if any(
            not isinstance(item, ArchetypeAffinityAssignment) for item in assignments
        ):
            raise ValueError(
                "assignments must contain ArchetypeAffinityAssignment values"
            )
        keys = tuple(
            (item.target_id, item.identity_scope, item.archetype)
            for item in assignments
        )
        if len(keys) != len(set(keys)):
            raise ValueError(
                "assignments must not repeat a target, scope, and archetype"
            )
        object.__setattr__(self, "assignments", assignments)


@dataclass(frozen=True, slots=True)
class AssignmentCoverage:
    total_memberships: int
    reviewed_memberships: int
    unreviewed_memberships: int
    explicit_none_assignments: int
    archetype_coverage: tuple[tuple[ArchetypeKey, int], ...]
    multi_archetype_memberships: int
    provenance_counts: tuple[tuple[AssignmentProvenance, int], ...]
    ambiguity_count: int


def validate_assignment_set(
    assignment_set: ArchetypeAffinityAssignmentSet, cube_version: CubeVersion
) -> None:
    """Reject assignments that cannot be interpreted against this exact version."""

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


def assignment_coverage(
    assignment_set: ArchetypeAffinityAssignmentSet, cube_version: CubeVersion
) -> AssignmentCoverage:
    """Report explicit review coverage without treating unassigned as NONE."""

    validate_assignment_set(assignment_set, cube_version)
    by_membership: dict[str, list[ArchetypeAffinityAssignment]] = {
        card.id: [] for card in cube_version.cards
    }
    identity_to_memberships: dict[str, list[str]] = {}
    for card in cube_version.cards:
        if card.printing is not None:
            identity_to_memberships.setdefault(
                card.printing.card_identity.id, []
            ).append(card.id)
    for assignment in assignment_set.assignments:
        target_memberships = (
            (assignment.target_id,)
            if assignment.identity_scope is AssignmentIdentityScope.CUBE_MEMBERSHIP
            else tuple(identity_to_memberships[assignment.target_id])
        )
        for membership_id in target_memberships:
            by_membership[membership_id].append(assignment)

    reviewed_statuses = {
        AssignmentReviewStatus.REVIEWED,
        AssignmentReviewStatus.ACTIVE,
    }
    reviewed_memberships = sum(
        any(item.review_status in reviewed_statuses for item in assignments)
        for assignments in by_membership.values()
    )
    archetype_coverage = tuple(
        (
            archetype,
            sum(
                any(
                    item.archetype is archetype
                    and item.review_status in reviewed_statuses
                    and item.support_level is not AffinitySupportLevel.NONE
                    for item in assignments
                )
                for assignments in by_membership.values()
            ),
        )
        for archetype in ArchetypeKey
    )
    provenance_counts = tuple(
        (
            provenance,
            sum(item.provenance is provenance for item in assignment_set.assignments),
        )
        for provenance in AssignmentProvenance
    )
    ambiguity_count = sum(
        any(
            len(
                {
                    item.support_level
                    for item in assignments
                    if item.archetype is archetype
                    and item.review_status in reviewed_statuses
                }
            )
            > 1
            for archetype in ArchetypeKey
        )
        for assignments in by_membership.values()
    )
    return AssignmentCoverage(
        total_memberships=len(cube_version.cards),
        reviewed_memberships=reviewed_memberships,
        unreviewed_memberships=len(cube_version.cards) - reviewed_memberships,
        explicit_none_assignments=sum(
            item.support_level is AffinitySupportLevel.NONE
            and item.review_status in reviewed_statuses
            for item in assignment_set.assignments
        ),
        archetype_coverage=archetype_coverage,
        multi_archetype_memberships=sum(
            len(
                {
                    item.archetype
                    for item in assignments
                    if item.review_status in reviewed_statuses
                    and item.support_level is not AffinitySupportLevel.NONE
                }
            )
            > 1
            for assignments in by_membership.values()
        ),
        provenance_counts=provenance_counts,
        ambiguity_count=ambiguity_count,
    )
