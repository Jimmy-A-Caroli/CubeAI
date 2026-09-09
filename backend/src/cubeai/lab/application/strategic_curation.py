"""Local human-curation helpers for strategic-v1 artifacts.

These helpers create no strategic relationships.  They keep the compact active
assignment artifact distinct from source-assisted proposal evidence.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from cubeai.lab.application.metadata import MetadataResolutionSnapshot
from cubeai.lab.application.strategic_affinities import (
    STRATEGIC_ASSIGNMENT_ARTIFACT_SCHEMA_VERSION,
    STRATEGIC_ASSIGNMENT_ARTIFACT_TYPE,
)
from cubeai.lab.domain.archetypes import (
    AffinitySupportLevel,
    AssignmentIdentityScope,
    AssignmentReviewStatus,
)
from cubeai.lab.domain.cube import CubeVersion
from cubeai.lab.domain.strategic_vocabulary import (
    MacroPathKeyV1,
    PackageKeyV1,
    StrategicAffinityAssignment,
    StrategicAffinityAssignmentSet,
    StrategicTargetType,
    validate_strategic_assignment_set,
)


def empty_strategic_assignment_set(
    cube_version: CubeVersion, *, assignment_set_id: str
) -> StrategicAffinityAssignmentSet:
    """Create an all-UNKNOWN strategic baseline for one exact CubeVersion."""

    return StrategicAffinityAssignmentSet(
        id=assignment_set_id,
        cube_version_id=cube_version.id,
        vocabulary_version="vintage-cube-strategic-v1",
        assignments=(),
    )


def strategic_assignment_artifact_document(
    assignment_set: StrategicAffinityAssignmentSet,
) -> dict[str, object]:
    """Serialize reviewed/active assignments without source display data."""

    return {
        "artifact_type": STRATEGIC_ASSIGNMENT_ARTIFACT_TYPE,
        "schema_version": STRATEGIC_ASSIGNMENT_ARTIFACT_SCHEMA_VERSION,
        "assignment_set": {
            "id": assignment_set.id,
            "cube_version_id": assignment_set.cube_version_id,
            "vocabulary_version": assignment_set.vocabulary_version,
            "assignments": [
                {
                    "target_id": item.target_id,
                    "identity_scope": item.identity_scope.value,
                    "target_type": item.target_type.value,
                    "target": item.target.value,
                    "support_level": item.support_level.value,
                    "provenance": item.provenance.value,
                    "review_status": item.review_status.value,
                    **({"note": item.note} if item.note is not None else {}),
                }
                for item in assignment_set.assignments
            ],
        },
    }


def strategic_coverage_report_document(
    assignment_set: StrategicAffinityAssignmentSet, cube_version: CubeVersion
) -> dict[str, Any]:
    """Report strategic review state; absence remains UNKNOWN, never NONE."""

    validate_strategic_assignment_set(assignment_set, cube_version)
    by_membership: dict[str, list[StrategicAffinityAssignment]] = {
        card.id: [] for card in cube_version.cards
    }
    identities: dict[str, list[str]] = {}
    for card in cube_version.cards:
        if card.printing is not None:
            identities.setdefault(card.printing.card_identity.id, []).append(card.id)
    for assignment in assignment_set.assignments:
        membership_ids = (
            (assignment.target_id,)
            if assignment.identity_scope is AssignmentIdentityScope.CUBE_MEMBERSHIP
            else tuple(identities[assignment.target_id])
        )
        for membership_id in membership_ids:
            by_membership[membership_id].append(assignment)
    reviewed = {AssignmentReviewStatus.REVIEWED, AssignmentReviewStatus.ACTIVE}
    reviewed_memberships = sum(
        any(item.review_status in reviewed for item in assignments)
        for assignments in by_membership.values()
    )
    positives = [
        item
        for item in assignment_set.assignments
        if item.review_status in reviewed
        and item.support_level is not AffinitySupportLevel.NONE
    ]
    by_target = {
        target_type.value: {
            target.value: sum(
                item.target_type is target_type and item.target is target
                for item in positives
            )
            for target in (
                MacroPathKeyV1
                if target_type is StrategicTargetType.MACRO_PATH
                else PackageKeyV1
            )
        }
        for target_type in StrategicTargetType
    }
    return {
        "assignment_set_id": assignment_set.id,
        "cube_version_id": assignment_set.cube_version_id,
        "vocabulary_version": assignment_set.vocabulary_version,
        "membership_resolution": {
            "total": len(cube_version.cards),
            "resolved_card_identities": sum(
                card.printing is not None for card in cube_version.cards
            ),
            "unresolved_or_custom": sum(
                card.printing is None for card in cube_version.cards
            ),
        },
        "coverage": {
            "total_memberships": len(cube_version.cards),
            "reviewed_memberships": reviewed_memberships,
            "unknown_unreviewed_memberships": len(cube_version.cards)
            - reviewed_memberships,
            "explicit_none_assignments": sum(
                item.review_status in reviewed
                and item.support_level is AffinitySupportLevel.NONE
                for item in assignment_set.assignments
            ),
            "assignments_by_support_level": {
                level.value: sum(
                    item.review_status in reviewed and item.support_level is level
                    for item in assignment_set.assignments
                )
                for level in AffinitySupportLevel
            },
            "reviewed_positive_assignments_by_target": by_target,
            "macro_path_positive_assignments": sum(
                item.target_type is StrategicTargetType.MACRO_PATH for item in positives
            ),
            "package_positive_assignments": sum(
                item.target_type is StrategicTargetType.PACKAGE for item in positives
            ),
            "multi_target_memberships": sum(
                len(
                    {
                        (item.target_type, item.target)
                        for item in assignments
                        if item.review_status in reviewed
                        and item.support_level is not AffinitySupportLevel.NONE
                    }
                )
                > 1
                for assignments in by_membership.values()
            ),
            "assignments_by_provenance": dict(
                sorted(
                    Counter(
                        item.provenance.value for item in assignment_set.assignments
                    ).items()
                )
            ),
            "unresolved_review_conflicts": sum(
                any(
                    len(
                        {
                            item.support_level
                            for item in assignments
                            if item.review_status in reviewed
                            and item.target_type is target_type
                            and item.target is target
                        }
                    )
                    > 1
                    for target_type in StrategicTargetType
                    for target in (
                        MacroPathKeyV1
                        if target_type is StrategicTargetType.MACRO_PATH
                        else PackageKeyV1
                    )
                )
                for assignments in by_membership.values()
            ),
        },
    }


def strategic_curation_worklist_document(
    cube_version: CubeVersion, resolution: MetadataResolutionSnapshot
) -> dict[str, object]:
    """Create local review context from normalized metadata, never proposals."""

    by_membership = {
        item.candidate.membership_key: item for item in resolution.resolutions
    }
    memberships = []
    for card in cube_version.cards:
        item = by_membership.get(card.id)
        printing = item.printing if item is not None else None
        images = dict(printing.image_uris) if printing is not None else {}
        memberships.append(
            {
                "membership_id": card.id,
                "card_identity_id": card.printing.card_identity.id
                if card.printing
                else None,
                "card_name": card.printing.card_identity.name
                if card.printing
                else None,
                "image_url": images.get("normal") or next(iter(images.values()), None),
                "mana_value": printing.mana_value if printing is not None else None,
                "colors": list(printing.colors) if printing is not None else None,
                "type_line": printing.type_line if printing is not None else None,
                "recommended_identity_scope": "cube_membership",
                "review_state": "unknown",
            }
        )
    return {
        "cube_version_id": cube_version.id,
        "instructions": "Review proposals separately. Add only explicitly accepted curator_defined or human_annotated records to the strategic assignment artifact; absent relations remain UNKNOWN.",
        "memberships": memberships,
    }
