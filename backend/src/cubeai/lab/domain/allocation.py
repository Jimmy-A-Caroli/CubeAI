"""Deterministic initial pack allocation."""
import random
from dataclasses import dataclass
from cubeai.lab.domain.cube import CubeVersion
from cubeai.lab.domain.draft import DraftCardInstance, DraftConfiguration, DraftPack

@dataclass(frozen=True, slots=True)
class AllocatedPack:
    pack: DraftPack
    cards: tuple[DraftCardInstance, ...]

class InsufficientCubeCapacity(ValueError):
    """Cube capacity is below configured draft demand."""

def allocate_packs(draft_id: str, version: CubeVersion, configuration: DraftConfiguration) -> tuple[AllocatedPack, ...]:
    if len(version.cards) < configuration.card_count:
        raise InsufficientCubeCapacity("Cube has insufficient memberships")
    shuffled = list(version.cards)
    random.Random(configuration.seed).shuffle(shuffled)
    result = []
    for pack_number in range(configuration.seats * configuration.packs_per_seat):
        start = pack_number * configuration.pack_size
        cards = tuple(DraftCardInstance(f"{draft_id}:card:{pack_number}:{i}", draft_id, card.id) for i, card in enumerate(shuffled[start:start + configuration.pack_size]))
        result.append(AllocatedPack(DraftPack(draft_id, pack_number, pack_number % configuration.seats), cards))
    return tuple(result)
