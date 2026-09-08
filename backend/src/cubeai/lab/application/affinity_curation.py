"""Human-curation helpers for exact-CubeVersion affinity artifacts.

This module deliberately produces no associations.  It turns a reviewed
CubeVersion into an empty, versioned starting artifact and a deterministic
coverage report; a human must add every future assignment explicitly.
"""

from __future__ import annotations

from typing import Any

from cubeai.lab.application.archetype_affinities import (
    ASSIGNMENT_ARTIFACT_SCHEMA_VERSION,
    ASSIGNMENT_ARTIFACT_TYPE,
)
from cubeai.lab.domain.archetypes import (
    ArchetypeAffinityAssignmentSet,
    assignment_coverage,
)
from cubeai.lab.domain.cube import CubeVersion


def empty_assignment_set(
    cube_version: CubeVersion, *, assignment_set_id: str
) -> ArchetypeAffinityAssignmentSet:
    """Create an all-UNKNOWN baseline without treating absence as ``NONE``."""

    return ArchetypeAffinityAssignmentSet(
        id=assignment_set_id,
        cube_version_id=cube_version.id,
        vocabulary_version="vintage-cube-archetypes-v0",
        assignments=(),
    )


def assignment_artifact_document(
    assignment_set: ArchetypeAffinityAssignmentSet,
) -> dict[str, object]:
    """Return the strict, reviewable production-artifact envelope."""

    return {
        "artifact_type": ASSIGNMENT_ARTIFACT_TYPE,
        "schema_version": ASSIGNMENT_ARTIFACT_SCHEMA_VERSION,
        "assignment_set": {
            "id": assignment_set.id,
            "cube_version_id": assignment_set.cube_version_id,
            "vocabulary_version": assignment_set.vocabulary_version,
            "assignments": [
                {
                    "target_id": item.target_id,
                    "identity_scope": item.identity_scope.value,
                    "archetype": item.archetype.value,
                    "support_level": item.support_level.value,
                    "provenance": item.provenance.value,
                    "review_status": item.review_status.value,
                    **({"note": item.note} if item.note is not None else {}),
                }
                for item in assignment_set.assignments
            ],
        },
    }


def coverage_report_document(
    assignment_set: ArchetypeAffinityAssignmentSet, cube_version: CubeVersion
) -> dict[str, Any]:
    """Serialize validation-backed coverage without exposing source card data."""

    coverage = assignment_coverage(assignment_set, cube_version)
    return {
        "assignment_set_id": assignment_set.id,
        "cube_version_id": cube_version.id,
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
            "total_memberships": coverage.total_memberships,
            "reviewed_memberships": coverage.reviewed_memberships,
            "unknown_unreviewed_memberships": coverage.unreviewed_memberships,
            "explicit_none_assignments": coverage.explicit_none_assignments,
            "reviewed_positive_memberships_by_archetype": {
                key.value: count for key, count in coverage.archetype_coverage
            },
            "multi_archetype_memberships": coverage.multi_archetype_memberships,
            "assignments_by_provenance": {
                key.value: count for key, count in coverage.provenance_counts
            },
            "ambiguous_reviewed_memberships": coverage.ambiguity_count,
        },
    }


def curation_worklist_document(cube_version: CubeVersion) -> dict[str, object]:
    """Make a local-only human worklist without proposing any affinity labels."""

    return {
        "cube_version_id": cube_version.id,
        "instructions": (
            "Choose only reviewed curator_defined or human_annotated conclusions. "
            "Leave a row absent from the assignment artifact when it is UNKNOWN; "
            "do not copy source tags or infer a label from card text."
        ),
        "memberships": [
            {
                "membership_id": card.id,
                "card_identity_id": (
                    card.printing.card_identity.id
                    if card.printing is not None
                    else None
                ),
                "card_name": (
                    card.printing.card_identity.name
                    if card.printing is not None
                    else None
                ),
                "recommended_identity_scope": (
                    "card_identity" if card.printing is not None else "cube_membership"
                ),
                "review_state": "unknown",
            }
            for card in cube_version.cards
        ],
    }
