"""Normalize provider-resolution records into provider-neutral card facts."""

from cubeai.lab.application.metadata import ResolvedPrinting, ScryfallFace
from cubeai.lab.domain.card_facts import CardFaceFacts, CardFacts, CardLayout


class CardFactsNormalizationError(ValueError):
    """A resolved provider record cannot satisfy the accepted facts contract."""


_LAYOUTS = {
    "normal": CardLayout.SINGLE,
    "split": CardLayout.SPLIT,
    "adventure": CardLayout.ADVENTURE,
    "transform": CardLayout.TRANSFORM,
    "modal_dfc": CardLayout.MODAL_DFC,
}
_CARD_TYPES = frozenset(
    {
        "Artifact",
        "Battle",
        "Creature",
        "Enchantment",
        "Instant",
        "Land",
        "Planeswalker",
        "Sorcery",
        "Tribal",
    }
)


def card_facts_from_resolved_printing(
    printing: ResolvedPrinting, *, metadata_snapshot_id: str
) -> CardFacts:
    """Return facts only when the cached provider record is complete enough.

    `mana_value` is read from the provider's numeric semantic value already
    recorded by the adapter.  This function never parses mana-cost notation.
    """

    if not isinstance(printing, ResolvedPrinting):
        raise ValueError("printing must be a ResolvedPrinting")
    if not isinstance(metadata_snapshot_id, str) or not metadata_snapshot_id.strip():
        raise ValueError("metadata_snapshot_id must be a nonblank string")
    if printing.oracle_id is None:
        raise CardFactsNormalizationError(
            "resolved printing lacks the card identity required for CardFacts"
        )
    if printing.mana_value is None:
        raise CardFactsNormalizationError(
            "resolved printing lacks provider-supplied semantic mana_value"
        )
    if printing.type_line is None:
        raise CardFactsNormalizationError(
            "resolved printing lacks the type facts required for CardFacts"
        )
    try:
        layout = _LAYOUTS[printing.layout]
    except KeyError as error:
        raise CardFactsNormalizationError(
            f"unsupported provider layout for CardFacts: {printing.layout}"
        ) from error
    faces = tuple(_face_facts(face) for face in printing.faces)
    is_land, is_creature = _type_flags(printing.type_line)
    return CardFacts(
        printing_id=printing.printing_id,
        card_identity_id=printing.oracle_id,
        name=printing.name,
        layout=layout,
        mana_cost=printing.mana_cost,
        mana_value=printing.mana_value,
        colors=printing.colors,
        color_identity=printing.color_identity,
        type_line=printing.type_line,
        oracle_text=printing.oracle_text,
        power=printing.power,
        toughness=printing.toughness,
        loyalty=printing.loyalty,
        is_land=is_land,
        is_creature=is_creature,
        has_nonland_face=not is_land or any(not face.is_land for face in faces),
        faces=faces,
        metadata_snapshot_id=metadata_snapshot_id,
    )


def _face_facts(face: ScryfallFace) -> CardFaceFacts:
    if face.type_line is None or face.colors is None:
        raise CardFactsNormalizationError(
            f"face {face.name!r} lacks the type or colour facts required for CardFacts"
        )
    is_land, is_creature = _type_flags(face.type_line)
    return CardFaceFacts(
        name=face.name,
        mana_cost=face.mana_cost,
        colors=face.colors,
        type_line=face.type_line,
        oracle_text=face.oracle_text,
        power=face.power,
        toughness=face.toughness,
        loyalty=face.loyalty,
        is_land=is_land,
        is_creature=is_creature,
    )


def _type_flags(type_line: str) -> tuple[bool, bool]:
    type_words = set(type_line.partition("—")[0].split()) & _CARD_TYPES
    return "Land" in type_words, "Creature" in type_words
