"""Synthetic structures used only by the non-production experiments."""

from dataclasses import dataclass
import random


@dataclass(frozen=True, slots=True)
class SyntheticCard:
    card_id: int
    rating: float
    color: str
    mana_value: int
    archetype_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PickEvent:
    pack_number: int
    pick_number: int
    seat: int
    card_id: int
    seen_card_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DraftResult:
    events: tuple[PickEvent, ...]
    pools: tuple[tuple[int, ...], ...]
    pack_directions: tuple[int, ...]
    complete: bool


def make_cards(count: int, seed: int) -> tuple[SyntheticCard, ...]:
    """Build a seeded synthetic cube with no external card data."""
    rng = random.Random(seed)
    colors = "WUBRG"
    tags = ("aggro", "control", "artifacts", "graveyard")
    return tuple(
        SyntheticCard(i, rng.random() * 5, colors[i % 5], 1 + i % 7, (tags[i % 4],))
        for i in range(count)
    )
