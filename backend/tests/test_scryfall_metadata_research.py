"""Offline checks for M1-005 research examples, not a Scryfall adapter."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = (
    REPOSITORY_ROOT / "fixtures" / "synthetic" / "scryfall-metadata-examples.json"
)


def load_examples() -> dict[str, object]:
    decoded: object = json.loads(EXAMPLES.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("Scryfall metadata research examples must be a JSON object")

    examples: dict[str, object] = {}
    for key, value in decoded.items():
        if not isinstance(key, str):
            raise ValueError("Scryfall metadata research example keys must be strings")
        examples[key] = value
    return examples


def test_examples_are_cubeai_authored_synthetic_research_data() -> None:
    examples = load_examples()

    assert examples["fixture_type"] == "cubeai-synthetic"
    assert examples["schema_version"] == 1
    assert examples["provenance"] == {
        "source": "CubeAI-authored synthetic research test data",
        "license": "MIT",
    }


def test_collection_request_example_has_exact_identifier_envelope() -> None:
    examples = load_examples()
    request = examples["collection_request"]

    assert isinstance(request, dict)
    identifiers = request["identifiers"]
    assert isinstance(identifiers, list)
    assert 1 <= len(identifiers) <= 75
    assert all(isinstance(identifier, dict) for identifier in identifiers)
    assert all(set(identifier) == {"id"} for identifier in identifiers)
    assert len({identifier["id"] for identifier in identifiers}) == len(identifiers)
    for identifier in identifiers:
        UUID(identifier["id"])


def test_bulk_metadata_example_has_minimum_documented_shape() -> None:
    examples = load_examples()
    bulk_list = examples["bulk_list"]

    assert isinstance(bulk_list, dict)
    assert bulk_list["object"] == "list"
    assert bulk_list["has_more"] is False
    records = bulk_list["data"]
    assert isinstance(records, list) and len(records) == 1

    record = records[0]
    assert isinstance(record, dict)
    assert record["object"] == "bulk_data"
    UUID(record["id"])
    assert record["type"] == "default_cards"
    assert isinstance(record["compressed_size"], int)
    assert record["compressed_size"] >= 0
    datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
    for key in ("uri", "jsonl_download_uri"):
        parsed = urlparse(record[key])
        assert parsed.scheme == "https" and parsed.netloc
