"""M2-004 tests for normalized provider-neutral CardFacts."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import json
from pathlib import Path

import pytest

from cubeai.lab.adapters.scryfall import _parse_printing
from cubeai.lab.adapters.scryfall import SQLiteScryfallCache
from cubeai.lab.application.card_facts import (
    CardFactsNormalizationError,
    card_facts_from_resolved_printing,
)
from cubeai.lab.application.metadata import ResolvedPrinting
from cubeai.lab.domain.card_facts import CardLayout


FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "contracts"
    / "scryfall"
    / "card-facts-layouts.json"
)
FETCHED_AT = datetime(2026, 9, 8, 12, tzinfo=UTC)
SNAPSHOT_ID = "scryfall-resolution-v1:synthetic"


def _printing(case: str) -> ResolvedPrinting:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return _parse_printing(document["cases"][case], FETCHED_AT)


@pytest.mark.parametrize(
    ("case", "layout"),
    [
        ("multicolor_spell", CardLayout.SINGLE),
        ("colorless_artifact", CardLayout.SINGLE),
        ("colored_mana_land", CardLayout.SINGLE),
        ("transform", CardLayout.TRANSFORM),
        ("modal_dfc", CardLayout.MODAL_DFC),
        ("adventure", CardLayout.ADVENTURE),
        ("split", CardLayout.SPLIT),
    ],
)
def test_normalizes_reviewed_layouts_without_provider_objects(
    case: str, layout: CardLayout
) -> None:
    facts = card_facts_from_resolved_printing(
        _printing(case), metadata_snapshot_id=SNAPSHOT_ID
    )

    assert facts.layout is layout
    assert facts.metadata_snapshot_id == SNAPSHOT_ID
    assert facts.printing_id
    assert facts.card_identity_id
    assert not hasattr(facts, "provider")


def test_mana_value_uses_provider_numeric_semantics_not_mana_cost_parsing() -> None:
    printing = _printing("multicolor_spell")
    changed = replace(printing, mana_cost="not mana notation", mana_value=7)

    facts = card_facts_from_resolved_printing(changed, metadata_snapshot_id=SNAPSHOT_ID)

    assert facts.mana_cost == "not mana notation"
    assert facts.mana_value == 7


def test_land_color_and_mana_production_are_not_conflated() -> None:
    facts = card_facts_from_resolved_printing(
        _printing("colored_mana_land"), metadata_snapshot_id=SNAPSHOT_ID
    )

    assert facts.is_land is True
    assert facts.has_nonland_face is False
    assert facts.colors == ()
    assert facts.color_identity == ("U",)


def test_modal_faces_are_ordered_and_overlap_is_explicit() -> None:
    facts = card_facts_from_resolved_printing(
        _printing("modal_dfc"), metadata_snapshot_id=SNAPSHOT_ID
    )

    assert facts.is_land is False
    assert facts.has_nonland_face is True
    assert [(face.name, face.is_land) for face in facts.faces] == [
        ("Synthetic Path", False),
        ("Synthetic Field", True),
    ]
    assert not hasattr(facts.faces[0], "mana_value")


def test_unknown_layout_is_visible_not_guessed() -> None:
    with pytest.raises(
        CardFactsNormalizationError, match="unsupported provider layout"
    ):
        card_facts_from_resolved_printing(
            _printing("prepare"), metadata_snapshot_id=SNAPSHOT_ID
        )


def test_cache_round_trips_mana_value_and_complete_face_facts(tmp_path: Path) -> None:
    cache = SQLiteScryfallCache(tmp_path / "scryfall-cache.sqlite3")
    printing = _printing("modal_dfc")

    cache.put(printing)

    assert cache.get(printing.printing_id) == printing
