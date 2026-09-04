"""Offline checks for the committed fixture policy's smallest synthetic example."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = REPOSITORY_ROOT / "fixtures"
SYNTHETIC_FIXTURE = (
    FIXTURES_ROOT / "synthetic" / "duplicate-membership-unresolved-custom.json"
)
SCRYFALL_CONTRACT_FIXTURE = (
    FIXTURES_ROOT / "contracts" / "scryfall" / "exact-collection.json"
)
SECRET_PATTERN = re.compile(
    r'(?i)"?(?:api[_-]?key|authorization|bearer|password|secret|token)"?\s*[:=]'
)


def load_synthetic_fixture() -> dict[str, object]:
    return json.loads(SYNTHETIC_FIXTURE.read_text(encoding="utf-8"))


def test_synthetic_fixture_declares_its_purpose_and_provenance() -> None:
    fixture = load_synthetic_fixture()

    assert fixture["fixture_type"] == "cubeai-synthetic"
    assert fixture["schema_version"] == 1
    assert fixture["purpose"] == "duplicate memberships and unresolved/custom identity"
    assert fixture["provenance"] == {
        "source": "CubeAI-authored synthetic test data",
        "license": "MIT",
    }


def test_synthetic_fixture_preserves_duplicate_and_unresolved_custom_cases() -> None:
    fixture = load_synthetic_fixture()
    memberships = fixture["memberships"]

    assert isinstance(memberships, list)
    assert len(memberships) == 3
    assert len({membership["id"] for membership in memberships}) == len(memberships)

    printing_counts = Counter(
        membership["printing_id"]
        for membership in memberships
        if membership["printing_id"] is not None
    )
    assert printing_counts == {"synthetic-printing-ember": 2}

    unresolved_custom = memberships[-1]
    assert unresolved_custom["resolution_status"] == "unresolved_custom"
    assert unresolved_custom["printing_id"] is None
    assert unresolved_custom["oracle_id"] is None


def test_scryfall_contract_fixture_is_synthetic_licensed_and_parser_shaped() -> None:
    fixture = json.loads(SCRYFALL_CONTRACT_FIXTURE.read_text(encoding="utf-8"))

    assert fixture["fixture_type"] == "cubeai-synthetic-contract"
    assert fixture["schema_version"] == 1
    assert fixture["purpose"] == "exact Scryfall collection response parsing"
    assert fixture["provenance"] == {
        "source": "CubeAI-authored synthetic test data",
        "license": "MIT",
        "provider_data": "none",
    }
    assert set(fixture["response"]) == {"data", "not_found"}
    assert fixture["response"]["not_found"] == []
    assert set(fixture["response"]["data"][0]) == {
        "id",
        "oracle_id",
        "name",
        "set",
        "collector_number",
        "lang",
        "layout",
        "mana_cost",
        "type_line",
        "oracle_text",
        "colors",
        "color_identity",
        "image_uris",
    }


def test_committed_json_fixtures_contain_no_secret_markers() -> None:
    for fixture_path in FIXTURES_ROOT.rglob("*.json"):
        assert not SECRET_PATTERN.search(fixture_path.read_text(encoding="utf-8")), (
            fixture_path
        )


def test_secret_pattern_catches_quoted_json_secret_keys() -> None:
    assert SECRET_PATTERN.search('"api_key": "synthetic-value"')
    assert SECRET_PATTERN.search('"authorization": "synthetic-value"')
