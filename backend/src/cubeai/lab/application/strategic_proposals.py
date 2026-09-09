"""Strict boundary for source-assisted strategic proposals, never assignments."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import cast

from cubeai.lab.domain.archetypes import AffinitySupportLevel, AssignmentIdentityScope
from cubeai.lab.domain.cube import CubeVersion
from cubeai.lab.domain.strategic_vocabulary import (
    MacroPathKeyV1,
    PackageKeyV1,
    STRATEGIC_VOCABULARY_VERSION_V1,
    StrategicTargetType,
)


PROPOSAL_ARTIFACT_TYPE = "cubeai.strategic-affinity-proposal-set"


def _mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return cast(dict[str, object], value)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


@dataclass(frozen=True, slots=True)
class StrategicProposalSet:
    id: str
    cube_version_id: str
    vocabulary_version: str
    evidence_sources: tuple[dict[str, str], ...]
    proposals: tuple[dict[str, object], ...]


def proposal_set_from_artifact(document: object) -> StrategicProposalSet:
    envelope = _mapping(document, "artifact")
    if frozenset(envelope) != {"artifact_type", "schema_version", "proposal_set"}:
        raise ValueError("proposal artifact has missing or unknown keys")
    if (
        envelope["artifact_type"] != PROPOSAL_ARTIFACT_TYPE
        or envelope["schema_version"] != 1
    ):
        raise ValueError("proposal artifact type or schema is unsupported")
    values = _mapping(envelope["proposal_set"], "proposal_set")
    required = {
        "id",
        "cube_version_id",
        "vocabulary_version",
        "status",
        "proposed_by",
        "evidence_sources",
        "proposals",
    }
    if frozenset(values) != required:
        raise ValueError("proposal_set has missing or unknown keys")
    if values["status"] != "proposed":
        raise ValueError("proposal_set status must be proposed")
    _text(values["id"], "proposal_set.id")
    cube_version_id = _text(values["cube_version_id"], "proposal_set.cube_version_id")
    if values["vocabulary_version"] != STRATEGIC_VOCABULARY_VERSION_V1:
        raise ValueError("proposal_set has an unsupported vocabulary version")
    _text(values["proposed_by"], "proposal_set.proposed_by")
    sources = values["evidence_sources"]
    proposals = values["proposals"]
    if not isinstance(sources, list) or not isinstance(proposals, list):
        raise ValueError("proposal evidence_sources and proposals must be arrays")
    source_ids: set[str] = set()
    for source in sources:
        item = _mapping(source, "evidence_source")
        if frozenset(item) != {"id", "kind", "url", "published_on", "currentness"}:
            raise ValueError("evidence_source has missing or unknown keys")
        source_id = _text(item["id"], "evidence_source.id")
        if source_id in source_ids or not _text(
            item["url"], "evidence_source.url"
        ).startswith("https://"):
            raise ValueError("evidence_source id or URL is invalid")
        _text(item["kind"], "evidence_source.kind")
        _text(item["published_on"], "evidence_source.published_on")
        _text(item["currentness"], "evidence_source.currentness")
        source_ids.add(source_id)
    parsed: list[dict[str, object]] = []
    for proposal in proposals:
        item = _mapping(proposal, "proposal")
        required_proposal = {
            "target_id",
            "identity_scope",
            "target_type",
            "target",
            "support_level",
            "source_ids",
            "rationale",
        }
        if frozenset(item) != required_proposal:
            raise ValueError("proposal has missing, unknown, or active-assignment keys")
        _text(item["target_id"], "proposal.target_id")
        try:
            AssignmentIdentityScope(cast(str, item["identity_scope"]))
            target_type = StrategicTargetType(cast(str, item["target_type"]))
            (
                MacroPathKeyV1
                if target_type is StrategicTargetType.MACRO_PATH
                else PackageKeyV1
            )(cast(str, item["target"]))
            AffinitySupportLevel(cast(str, item["support_level"]))
        except (TypeError, ValueError) as error:
            raise ValueError(
                "proposal has an invalid strategic contract value"
            ) from error
        references = item["source_ids"]
        if (
            not isinstance(references, list)
            or not references
            or not set(references) <= source_ids
        ):
            raise ValueError("proposal source_ids must reference declared evidence")
        _text(item["rationale"], "proposal.rationale")
        parsed.append(item)
    return StrategicProposalSet(
        _text(values["id"], "proposal_set.id"),
        cube_version_id,
        STRATEGIC_VOCABULARY_VERSION_V1,
        tuple(cast(dict[str, str], item) for item in sources),
        tuple(parsed),
    )


def validate_proposal_set(
    proposal_set: StrategicProposalSet, cube_version: CubeVersion
) -> None:
    if proposal_set.cube_version_id != cube_version.id:
        raise ValueError("proposal set must bind to the exact CubeVersion")
    memberships = {card.id for card in cube_version.cards}
    identities = {
        card.printing.card_identity.id for card in cube_version.cards if card.printing
    }
    for proposal in proposal_set.proposals:
        valid = (
            memberships
            if proposal["identity_scope"] == "cube_membership"
            else identities
        )
        if proposal["target_id"] not in valid:
            raise ValueError("proposal target is absent from CubeVersion")


def load_proposal_set(path: Path) -> StrategicProposalSet:
    return proposal_set_from_artifact(json.loads(path.read_text(encoding="utf-8")))
