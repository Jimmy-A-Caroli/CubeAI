"""Deterministically allocate a validated CubeVersion into draft packs."""

import random
from dataclasses import dataclass

from cubeai.lab.domain.cube import CubeVersion
from cubeai.lab.domain.draft import DraftCardInstance, DraftPack
from cubeai.lab.domain.validation import CubeValidationResult, validate_cube_version


@dataclass(frozen=True, slots=True)
class AllocatedPack:
    pack: DraftPack
    cards: tuple[DraftCardInstance, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.pack, DraftPack):
            raise ValueError("pack must be a DraftPack")
        cards = tuple(self.cards)
        if any(not isinstance(card, DraftCardInstance) for card in cards):
            raise ValueError("cards must contain DraftCardInstance values")
        if len({card.id for card in cards}) != len(cards):
            raise ValueError("cards must have unique draft-card instance IDs")
        if any(card.draft_id != self.pack.draft_id for card in cards):
            raise ValueError("cards must belong to the allocated pack draft")
        object.__setattr__(self, "cards", cards)


class InsufficientCubeCapacity(ValueError):
    """Cube capacity is below configured draft demand."""


def allocate_packs(
    draft_id: str, version: CubeVersion, validation: CubeValidationResult
) -> tuple[AllocatedPack, ...]:
    """Allocate each selected membership exactly once from source-order input.

    Validation fixes draft geometry and proves the selected memberships are
    usable. The recorded seed shuffles the immutable source-order sequence;
    excess memberships remain unallocated.
    """

    if not isinstance(version, CubeVersion):
        raise ValueError("version must be a CubeVersion")
    if not isinstance(validation, CubeValidationResult):
        raise ValueError("validation must be a CubeValidationResult")
    if validation.cube_version_id != version.id:
        raise ValueError("validation must belong to the supplied CubeVersion")
    if validation.cube_version_fingerprint != version.content_fingerprint:
        raise ValueError("validation must match the supplied CubeVersion snapshot")
    configuration = validation.configuration
    verified_validation = validate_cube_version(version, configuration)
    if verified_validation.usable_membership_count < configuration.card_count:
        raise InsufficientCubeCapacity("Cube has insufficient usable memberships")
    if not verified_validation.is_draftable:
        raise ValueError("CubeVersion validation contains blocking diagnostics")
    if validation != verified_validation:
        raise ValueError("validation must match the supplied CubeVersion")

    selected = list(version.cards)
    random.Random(configuration.seed).shuffle(selected)
    selected = selected[: configuration.card_count]
    allocated: list[AllocatedPack] = []
    for pack_number in range(configuration.seats * configuration.packs_per_seat):
        start = pack_number * configuration.pack_size
        cards = tuple(
            DraftCardInstance(
                f"{draft_id}:card:{pack_number}:{card_index}",
                draft_id,
                membership.id,
            )
            for card_index, membership in enumerate(
                selected[start : start + configuration.pack_size]
            )
        )
        allocated.append(
            AllocatedPack(
                DraftPack(draft_id, pack_number, pack_number % configuration.seats),
                cards,
            )
        )
    return tuple(allocated)
