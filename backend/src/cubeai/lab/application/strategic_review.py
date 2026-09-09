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
    initial_assignments: StrategicAffinityAssignmentSet | None = None

    def session_document(
        self, cube_version: CubeVersion, metadata_lookup: CardMetadataLookup | None
    ) -> dict[str, object]:
        self._validate_version(cube_version)
        sources = {item["id"]: item for item in self.proposal_set.evidence_sources}
        proposal_by_key = {
            self._proposal_key(proposal): proposal
            for proposal in self.proposal_set.proposals
        }
        current_by_key = {
            self._assignment_key(assignment): assignment
            for assignment in self._initial_assignments(cube_version)
        }
        membership_cards = []
        for card in cube_version.cards:
            printing = (
                metadata_lookup.lookup_printing(card.printing.id)
                if metadata_lookup is not None and card.printing is not None
                else None
            )
            relations = []
            for target_type, target in self._targets():
                key = (
                    card.id,
                    AssignmentIdentityScope.CUBE_MEMBERSHIP.value,
                    target_type.value,
                    target.value,
                )
                proposal = proposal_by_key.get(key)
                current = current_by_key.get(key)
                relations.append(
                    {
                        "target_id": card.id,
                        "identity_scope": AssignmentIdentityScope.CUBE_MEMBERSHIP.value,
                        "target_type": target_type.value,
                        "target": target.value,
                        "current_support_level": (
                            current.support_level.value if current is not None else None
                        ),
                        "proposed_support_level": (
                            proposal["support_level"] if proposal is not None else None
                        ),
                        "rationale": proposal["rationale"]
                        if proposal is not None
                        else None,
                        "evidence_sources": (
                            [
                                sources[source_id]
                                for source_id in cast(list[str], proposal["source_ids"])
                            ]
                            if proposal is not None
                            else []
                        ),
                    }
                )
            membership_cards.append(
                {
                    "target_id": card.id,
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
                    "relations": relations,
                }
            )
        return {
            "proposal_set_id": self.proposal_set.id,
            "cube_version_id": cube_version.id,
            "vocabulary_version": self.proposal_set.vocabulary_version,
            "target_cell_count": len(membership_cards) * len(self._targets()),
            "cards": membership_cards,
        }

    def submit(
        self, cube_version: CubeVersion, decisions: tuple[StrategicReviewDecision, ...]
    ) -> dict[str, object]:
        self._validate_version(cube_version)
        membership_ids = {card.id for card in cube_version.cards}
        keys = tuple(decision.key() for decision in decisions)
        if len(keys) != len(set(keys)):
            raise StrategicReviewError("submitted decisions must not repeat a target")
        assignments = []
        for decision in decisions:
            if (
                decision.target_id not in membership_ids
                or decision.identity_scope
                != AssignmentIdentityScope.CUBE_MEMBERSHIP.value
            ):
                raise StrategicReviewError(
                    "submitted decision target is not a cube membership"
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
            membership_ids = {card.id for card in cube_version.cards}
            if any(
                proposal["target_id"] not in membership_ids
                for proposal in self.proposal_set.proposals
            ):
                raise StrategicReviewError(
                    "proposal targets a membership absent from the current CubeVersion"
                )
        except ValueError as error:
            raise StrategicReviewError(str(error)) from error
        try:
            validate_strategic_assignment_set(
                StrategicAffinityAssignmentSet(
                    "initial-strategic-review",
                    cube_version.id,
                    self.proposal_set.vocabulary_version,
                    self._initial_assignments(cube_version),
                ),
                cube_version,
            )
        except ValueError as error:
            raise StrategicReviewError(str(error)) from error

    def _initial_assignments(
        self, cube_version: CubeVersion
    ) -> tuple[StrategicAffinityAssignment, ...]:
        if self.initial_assignments is None:
            return ()
        if self.initial_assignments.cube_version_id != cube_version.id:
            return self.initial_assignments.assignments
        return self.initial_assignments.assignments

    @staticmethod
    def _targets() -> tuple[
        tuple[StrategicTargetType, MacroPathKeyV1 | PackageKeyV1], ...
    ]:
        return tuple(
            (StrategicTargetType.MACRO_PATH, target) for target in MacroPathKeyV1
        ) + tuple((StrategicTargetType.PACKAGE, target) for target in PackageKeyV1)

    @staticmethod
    def _proposal_key(proposal: dict[str, object]) -> tuple[str, str, str, str]:
        return (
            str(proposal["target_id"]),
            str(proposal["identity_scope"]),
            str(proposal["target_type"]),
            str(proposal["target"]),
        )

    @staticmethod
    def _assignment_key(
        assignment: StrategicAffinityAssignment,
    ) -> tuple[str, str, str, str]:
        return (
            assignment.target_id,
            assignment.identity_scope.value,
            assignment.target_type.value,
            assignment.target.value,
        )

    @staticmethod
    def _image_url(printing: Any) -> str | None:
        if printing is None:
            return None
        images = dict(printing.image_uris)
        return images.get("normal") or next(iter(images.values()), None)
