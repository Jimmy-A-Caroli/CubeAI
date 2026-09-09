"""Typed local review of a fixed strategic proposal set.

This service never activates strategy data and never persists a browser draft.
It turns only explicit reviewer selections into a portable reviewed artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, cast

from cubeai.lab.application.metadata import CardMetadataLookup
from cubeai.lab.application.strategic_curation import (
    strategic_assignment_artifact_document,
    strategic_coverage_report_document,
)
from cubeai.lab.application.strategic_proposals import (
    StrategicProposalSet,
    validate_proposal_set,
)
from cubeai.lab.domain.archetypes import (
    AffinitySupportLevel,
    AssignmentIdentityScope,
    AssignmentProvenance,
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


class StrategicReviewError(ValueError):
    """A submitted curation decision conflicts with the fixed session."""


@dataclass(frozen=True, slots=True)
class StrategicReviewDecision:
    target_id: str
    identity_scope: str
    target_type: str
    target: str
    support_level: str

    def key(self) -> tuple[str, str, str, str]:
        return (self.target_id, self.identity_scope, self.target_type, self.target)


@dataclass(frozen=True, slots=True)
class StrategicReviewService:
    proposal_set: StrategicProposalSet

    def session_document(
        self, cube_version: CubeVersion, metadata_lookup: CardMetadataLookup | None
    ) -> dict[str, object]:
        self._validate_version(cube_version)
        cards = {card.id: card for card in cube_version.cards}
        sources = {item["id"]: item for item in self.proposal_set.evidence_sources}
        proposals = []
        for proposal in self.proposal_set.proposals:
            card = cards[str(proposal["target_id"])]
            printing = (
                metadata_lookup.lookup_printing(card.printing.id)
                if metadata_lookup is not None and card.printing is not None
                else None
            )
            proposals.append(
                {
                    "target_id": proposal["target_id"],
                    "identity_scope": proposal["identity_scope"],
                    "target_type": proposal["target_type"],
                    "target": proposal["target"],
                    "proposed_support_level": proposal["support_level"],
                    "rationale": proposal["rationale"],
                    "evidence_sources": [
                        sources[source_id]
                        for source_id in cast(list[str], proposal["source_ids"])
                    ],
                    "card": {
                        "name": (
                            printing.name
                            if printing is not None
                            else card.printing.card_identity.name
                            if card.printing is not None
                            else "Unresolved card"
                        ),
                        "image_url": self._image_url(printing),
                        "mana_value": (
                            printing.mana_value if printing is not None else None
                        ),
                        "colors": list(printing.colors) if printing is not None else [],
                        "type_line": printing.type_line
                        if printing is not None
                        else None,
                    },
                }
            )
        return {
            "proposal_set_id": self.proposal_set.id,
            "cube_version_id": cube_version.id,
            "vocabulary_version": self.proposal_set.vocabulary_version,
            "proposals": proposals,
        }

    def submit(
        self, cube_version: CubeVersion, decisions: tuple[StrategicReviewDecision, ...]
    ) -> dict[str, object]:
        self._validate_version(cube_version)
        proposal_by_key = {
            self._proposal_key(item): item for item in self.proposal_set.proposals
        }
        keys = tuple(decision.key() for decision in decisions)
        if len(keys) != len(set(keys)):
            raise StrategicReviewError("submitted decisions must not repeat a target")
        assignments = []
        for decision in decisions:
            proposal = proposal_by_key.get(decision.key())
            if proposal is None:
                raise StrategicReviewError(
                    "submitted decision is not in this proposal set"
                )
            try:
                target_type = StrategicTargetType(decision.target_type)
                target = (
                    MacroPathKeyV1(decision.target)
                    if target_type is StrategicTargetType.MACRO_PATH
                    else PackageKeyV1(decision.target)
                )
                assignments.append(
                    StrategicAffinityAssignment(
                        decision.target_id,
                        AssignmentIdentityScope(decision.identity_scope),
                        target_type,
                        target,
                        AffinitySupportLevel(decision.support_level),
                        AssignmentProvenance.HUMAN_ANNOTATED,
                        AssignmentReviewStatus.REVIEWED,
                    )
                )
            except ValueError as error:
                raise StrategicReviewError(
                    "submitted decision has an invalid value"
                ) from error
        digest = sha256(
            json.dumps(
                sorted(
                    (*decision.key(), decision.support_level) for decision in decisions
                ),
                separators=(",", ":"),
            ).encode()
        ).hexdigest()[:12]
        assignment_set = StrategicAffinityAssignmentSet(
            f"{self.proposal_set.id}-reviewed-{digest}",
            cube_version.id,
            self.proposal_set.vocabulary_version,
            tuple(assignments),
        )
        validate_strategic_assignment_set(assignment_set, cube_version)
        artifact = strategic_assignment_artifact_document(assignment_set)
        coverage = strategic_coverage_report_document(assignment_set, cube_version)
        return {
            "assignment_artifact": artifact,
            "coverage_report": coverage,
            "artifact_filename": f"{assignment_set.id}.json",
            "coverage_filename": f"{assignment_set.id}-coverage.json",
            "reviewed_count": len(assignments),
            "unknown_remaining": len(cube_version.cards)
            - len({item.target_id for item in assignments}),
        }

    def _validate_version(self, cube_version: CubeVersion) -> None:
        try:
            validate_proposal_set(self.proposal_set, cube_version)
        except ValueError as error:
            raise StrategicReviewError(str(error)) from error

    @staticmethod
    def _proposal_key(proposal: dict[str, object]) -> tuple[str, str, str, str]:
        return (
            str(proposal["target_id"]),
            str(proposal["identity_scope"]),
            str(proposal["target_type"]),
            str(proposal["target"]),
        )

    @staticmethod
    def _image_url(printing: Any) -> str | None:
        if printing is None:
            return None
        images = dict(printing.image_uris)
        return images.get("normal") or next(iter(images.values()), None)
