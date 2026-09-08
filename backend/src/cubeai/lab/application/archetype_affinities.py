"""Small JSON boundary for reviewed archetype-affinity assignment artifacts."""

import json
from pathlib import Path
from typing import cast

from cubeai.lab.domain.archetypes import (
    ArchetypeAffinityAssignment,
    ArchetypeAffinityAssignmentSet,
    ArchetypeKey,
    AssignmentIdentityScope,
    AssignmentProvenance,
    AssignmentReviewStatus,
    AffinitySupportLevel,
)


def _require_mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return cast(dict[str, object], value)


def _require_exact_keys(
    values: dict[str, object], required: frozenset[str], field: str
) -> None:
    actual = frozenset(values)
    if actual != required:
        raise ValueError(
            f"{field} keys must be {sorted(required)}; got {sorted(actual)}"
        )


def assignment_set_from_json_document(
    document: object,
) -> ArchetypeAffinityAssignmentSet:
    """Parse the intentionally small v1 artifact shape without provider input."""

    envelope = _require_mapping(document, "document")
    _require_exact_keys(
        envelope,
        frozenset(
            {
                "fixture_type",
                "schema_version",
                "purpose",
                "provenance",
                "assignment_set",
            }
        ),
        "document",
    )
    if envelope["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    values = _require_mapping(envelope["assignment_set"], "assignment_set")
    _require_exact_keys(
        values,
        frozenset({"id", "cube_version_id", "vocabulary_version", "assignments"}),
        "assignment_set",
    )
    raw_assignments = values["assignments"]
    if not isinstance(raw_assignments, list):
        raise ValueError("assignment_set.assignments must be an array")
    assignments = tuple(_assignment_from_json(item) for item in raw_assignments)
    return ArchetypeAffinityAssignmentSet(
        id=cast(str, values["id"]),
        cube_version_id=cast(str, values["cube_version_id"]),
        vocabulary_version=cast(str, values["vocabulary_version"]),
        assignments=assignments,
    )


def load_assignment_set(path: Path) -> ArchetypeAffinityAssignmentSet:
    """Load a local review artifact; callers still validate it against a CubeVersion."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"unable to read assignment artifact: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid assignment artifact JSON: {path}") from error
    return assignment_set_from_json_document(document)


def _assignment_from_json(value: object) -> ArchetypeAffinityAssignment:
    item = _require_mapping(value, "assignment")
    allowed = frozenset(
        {
            "target_id",
            "identity_scope",
            "archetype",
            "support_level",
            "provenance",
            "review_status",
            "note",
        }
    )
    required = allowed - {"note"}
    if not required.issubset(item) or not frozenset(item).issubset(allowed):
        raise ValueError("assignment has missing or unknown keys")
    try:
        return ArchetypeAffinityAssignment(
            target_id=cast(str, item["target_id"]),
            identity_scope=AssignmentIdentityScope(cast(str, item["identity_scope"])),
            archetype=ArchetypeKey(cast(str, item["archetype"])),
            support_level=AffinitySupportLevel(cast(str, item["support_level"])),
            provenance=AssignmentProvenance(cast(str, item["provenance"])),
            review_status=AssignmentReviewStatus(cast(str, item["review_status"])),
            note=cast(str | None, item.get("note")),
        )
    except (TypeError, ValueError) as error:
        raise ValueError("assignment has an invalid contract value") from error
