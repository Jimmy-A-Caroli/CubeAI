"""Card and Cube identity values for the CubeLab domain."""

from dataclasses import dataclass
from enum import Enum


def _require_nonblank_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a nonblank string")


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    CUSTOM = "custom"


@dataclass(frozen=True)
class SourceReference:
    source: str
    external_id: str

    def __post_init__(self) -> None:
        _require_nonblank_string(self.source, "source")
        _require_nonblank_string(self.external_id, "external_id")


@dataclass(frozen=True)
class CardIdentity:
    id: str
    name: str
    resolution_status: ResolutionStatus
    oracle_id: str | None = None
    source_reference: SourceReference | None = None

    def __post_init__(self) -> None:
        _require_nonblank_string(self.id, "id")
        if not isinstance(self.resolution_status, ResolutionStatus):
            raise ValueError("resolution_status must be a ResolutionStatus")
        if self.resolution_status is ResolutionStatus.RESOLVED:
            _require_nonblank_string(self.oracle_id, "oracle_id")
        elif self.oracle_id is not None:
            raise ValueError("oracle_id must be absent for a nonresolved identity")


@dataclass(frozen=True)
class CardPrinting:
    id: str
    card_identity: CardIdentity
    source_reference: SourceReference | None = None

    def __post_init__(self) -> None:
        _require_nonblank_string(self.id, "id")


@dataclass(frozen=True)
class Cube:
    id: str
    name: str
    source_reference: SourceReference | None = None

    def __post_init__(self) -> None:
        _require_nonblank_string(self.id, "id")


@dataclass(frozen=True)
class CubeCard:
    id: str
    resolution_status: ResolutionStatus
    printing: CardPrinting | None = None
    source_reference: SourceReference | None = None

    def __post_init__(self) -> None:
        _require_nonblank_string(self.id, "id")
        if not isinstance(self.resolution_status, ResolutionStatus):
            raise ValueError("resolution_status must be a ResolutionStatus")
        if self.resolution_status is ResolutionStatus.RESOLVED:
            if self.printing is None:
                raise ValueError("printing is required for a resolved CubeCard")
            if (
                self.printing.card_identity.resolution_status
                is not ResolutionStatus.RESOLVED
            ):
                raise ValueError(
                    "printing.card_identity.resolution_status must be resolved"
                )
        elif self.printing is not None:
            raise ValueError("printing must be absent for a nonresolved CubeCard")


@dataclass(frozen=True)
class CubeVersion:
    id: str
    cube: Cube
    cards: tuple[CubeCard, ...]
    source_reference: SourceReference | None = None

    def __post_init__(self) -> None:
        _require_nonblank_string(self.id, "id")
        cards = tuple(self.cards)
        object.__setattr__(self, "cards", cards)
        card_ids = [card.id for card in cards]
        if len(card_ids) != len(set(card_ids)):
            raise ValueError("duplicate CubeCard.id values are not allowed")
