"""Strict JSON boundary for approved v1 strategic-affinity artifacts."""

import json
from pathlib import Path
from typing import cast

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


STRATEGIC_ASSIGNMENT_ARTIFACT_TYPE = "cubeai.strategic-affinity-assignment-set"
STRATEGIC_ASSIGNMENT_ARTIFACT_SCHEMA_VERSION = 1


def _mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return cast(dict[str, object], value)


def assignment_set_from_artifact(document: object) -> StrategicAffinityAssignmentSet:
    envelope = _mapping(document, "artifact")
    if frozenset(envelope) != frozenset(
        {"artifact_type", "schema_version", "assignment_set"}
    ):
        raise ValueError("artifact has missing or unknown keys")
    if envelope["artifact_type"] != STRATEGIC_ASSIGNMENT_ARTIFACT_TYPE:
        raise ValueError("artifact_type is not a strategic affinity artifact")
    if envelope["schema_version"] != STRATEGIC_ASSIGNMENT_ARTIFACT_SCHEMA_VERSION:
        raise ValueError("artifact schema_version is not supported")
    values = _mapping(envelope["assignment_set"], "assignment_set")
    if frozenset(values) != frozenset(
        {"id", "cube_version_id", "vocabulary_version", "assignments"}
    ):
        raise ValueError("assignment_set has missing or unknown keys")
    raw_assignments = values["assignments"]
    if not isinstance(raw_assignments, list):
        raise ValueError("assignment_set.assignments must be an array")
    return StrategicAffinityAssignmentSet(
        id=cast(str, values["id"]),
        cube_version_id=cast(str, values["cube_version_id"]),
        vocabulary_version=cast(str, values["vocabulary_version"]),
        assignments=tuple(_assignment(item) for item in raw_assignments),
    )


def load_assignment_set(path: Path) -> StrategicAffinityAssignmentSet:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"unable to load strategic affinity artifact: {path}"
        ) from error
    return assignment_set_from_artifact(document)


def _assignment(value: object) -> StrategicAffinityAssignment:
    item = _mapping(value, "assignment")
    allowed = frozenset(
        {
            "target_id",
            "identity_scope",
            "target_type",
            "target",
            "support_level",
            "provenance",
            "review_status",
            "note",
        }
    )
    if not (allowed - {"note"}).issubset(item) or not frozenset(item).issubset(allowed):
        raise ValueError("assignment has missing or unknown keys")
    try:
        target_type = StrategicTargetType(cast(str, item["target_type"]))
        target = (
            MacroPathKeyV1(cast(str, item["target"]))
            if target_type is StrategicTargetType.MACRO_PATH
            else PackageKeyV1(cast(str, item["target"]))
        )
        return StrategicAffinityAssignment(
            target_id=cast(str, item["target_id"]),
            identity_scope=AssignmentIdentityScope(cast(str, item["identity_scope"])),
            target_type=target_type,
            target=target,
            support_level=AffinitySupportLevel(cast(str, item["support_level"])),
            provenance=AssignmentProvenance(cast(str, item["provenance"])),
            review_status=AssignmentReviewStatus(cast(str, item["review_status"])),
            note=cast(str | None, item.get("note")),
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "assignment has an invalid strategic contract value"
        ) from error
