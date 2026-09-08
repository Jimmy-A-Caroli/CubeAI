"""Provider-neutral factual card values used by future CubeLab consumers."""

from dataclasses import dataclass
from enum import StrEnum


_COLOURS = frozenset({"W", "U", "B", "R", "G"})


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


def _validate_colours(value: tuple[str, ...], field: str) -> tuple[str, ...]:
    colours = tuple(value)
    if any(colour not in _COLOURS for colour in colours) or len(colours) != len(
        set(colours)
    ):
        raise ValueError(f"{field} must contain distinct WUBRG colour codes")
    return colours


class CardLayout(StrEnum):
    """Closed structural layouts with reviewed normalized semantics."""

    SINGLE = "single"
    SPLIT = "split"
    ADVENTURE = "adventure"
    TRANSFORM = "transform"
    MODAL_DFC = "modal_dfc"


@dataclass(frozen=True, slots=True)
class CardFaceFacts:
    """Facts for one ordered face; face mana value is intentionally absent."""

    name: str
    mana_cost: str | None
    colors: tuple[str, ...]
    type_line: str
    oracle_text: str | None
    power: str | None
    toughness: str | None
    loyalty: str | None
    is_land: bool
    is_creature: bool

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        _require_text(self.type_line, "type_line")
        for field in ("mana_cost", "oracle_text", "power", "toughness", "loyalty"):
            value = getattr(self, field)
            if value is not None:
                _require_text(value, field)
        object.__setattr__(self, "colors", _validate_colours(self.colors, "colors"))
        for field in ("is_land", "is_creature"):
            if not isinstance(getattr(self, field), bool):
                raise ValueError(f"{field} must be a boolean")


@dataclass(frozen=True, slots=True)
class CardFacts:
    """Immutable facts for one printing and its distinct rules identity.

    This records no provider name or raw payload.  It deliberately does not
    infer mana production, castability, card roles, or strategy meaning.
    """

    printing_id: str
    card_identity_id: str
    name: str
    layout: CardLayout
    mana_cost: str | None
    mana_value: int
    colors: tuple[str, ...]
    color_identity: tuple[str, ...]
    type_line: str
    oracle_text: str | None
    power: str | None
    toughness: str | None
    loyalty: str | None
    is_land: bool
    is_creature: bool
    has_nonland_face: bool
    faces: tuple[CardFaceFacts, ...]
    metadata_snapshot_id: str

    def __post_init__(self) -> None:
        for field in (
            "printing_id",
            "card_identity_id",
            "name",
            "type_line",
            "metadata_snapshot_id",
        ):
            _require_text(getattr(self, field), field)
        if not isinstance(self.layout, CardLayout):
            raise ValueError("layout must be a CardLayout")
        if type(self.mana_value) is not int or self.mana_value < 0:
            raise ValueError("mana_value must be a non-negative integer")
        for field in ("mana_cost", "oracle_text", "power", "toughness", "loyalty"):
            value = getattr(self, field)
            if value is not None:
                _require_text(value, field)
        object.__setattr__(self, "colors", _validate_colours(self.colors, "colors"))
        object.__setattr__(
            self,
            "color_identity",
            _validate_colours(self.color_identity, "color_identity"),
        )
        for field in ("is_land", "is_creature", "has_nonland_face"):
            if not isinstance(getattr(self, field), bool):
                raise ValueError(f"{field} must be a boolean")
        faces = tuple(self.faces)
        if any(not isinstance(face, CardFaceFacts) for face in faces):
            raise ValueError("faces must contain CardFaceFacts values")
        object.__setattr__(self, "faces", faces)
