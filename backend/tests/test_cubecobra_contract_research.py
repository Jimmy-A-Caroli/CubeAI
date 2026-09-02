"""Offline probes for the frozen CubeCobra contract, not an adapter."""

from __future__ import annotations

import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_FIXTURES = REPOSITORY_ROOT / "fixtures" / "contracts" / "cubecobra"
SYNTHETIC_CUSTOM = (
    REPOSITORY_ROOT / "fixtures" / "synthetic" / "duplicate-membership-unresolved-custom.json"
)


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((CONTRACT_FIXTURES / name).read_text(encoding="utf-8"))


def project_supported_mainboard(response: dict[str, object]) -> list[dict[str, object]]:
    """Small, test-only projection of the frozen supported source subset."""

    assert isinstance(response.get("id"), str) and response["id"].strip()
    assert isinstance(response.get("name"), str) and response["name"].strip()
    assert response.get("visibility") == "pu"

    cards = response.get("cards")
    assert isinstance(cards, dict)
    mainboard = cards.get("mainboard")
    assert isinstance(mainboard, list) and mainboard

    projected: list[dict[str, object]] = []
    for position, row in enumerate(mainboard):
        assert isinstance(row, dict)
        assert isinstance(row.get("cardID"), str) and row["cardID"]
        details = row.get("details")
        assert isinstance(details, dict)
        assert isinstance(details.get("scryfall_id"), str) and details["scryfall_id"]
        assert isinstance(details.get("oracle_id"), str) and details["oracle_id"]
        projected.append(
            {
                "position": position,
                "provider_card_id": row.get("cardID"),
                "printing_id": details["scryfall_id"],
                "oracle_id": details["oracle_id"],
            }
        )
    return projected


def test_provider_contract_excerpts_have_required_review_metadata() -> None:
    for name in ("normal-public-mainboard.json", "duplicate-mainboard.json"):
        fixture = load_fixture(name)
        provenance = fixture["provenance"]

        assert fixture["fixture_type"] == "sanitized-provider-contract"
        assert fixture["schema_version"] == 1
        assert isinstance(fixture["purpose"], str) and fixture["purpose"]
        assert isinstance(fixture["sanitization"], str) and fixture["sanitization"]
        assert isinstance(provenance, dict)
        assert provenance["provider"] == "CubeCobra"
        assert provenance["retrieved_at"] == "2026-09-02"
        assert isinstance(provenance["source_url"], str)
        assert isinstance(provenance["license_and_terms"], str)
        assert provenance["response_data_licensing"] == (
            "Not established. This minimal sanitized excerpt is retained only under "
            "CubeAI's approved conservative fixture policy; no broader reuse or "
            "licensing conclusion is made."
        )


def test_normal_excerpt_replays_required_shape_with_optional_card_count_absent() -> None:
    fixture = load_fixture("normal-public-mainboard.json")
    response = fixture["response_excerpt"]

    assert isinstance(response, dict)
    assert "cardCount" not in response
    row = response["cards"]["mainboard"][0]
    assert row["tags"] == []
    assert row["notes"] == ""
    memberships = project_supported_mainboard(response)

    assert len(memberships) == 1
    assert memberships[0]["printing_id"] != memberships[0]["oracle_id"]


def test_duplicate_excerpt_conserves_two_memberships_with_one_printing() -> None:
    fixture = load_fixture("duplicate-mainboard.json")
    response = fixture["response_excerpt"]

    assert isinstance(response, dict)
    assert all(
        row["tags"] is None and row["notes"] is None
        for row in response["cards"]["mainboard"]
    )
    memberships = project_supported_mainboard(response)

    assert [membership["position"] for membership in memberships] == [0, 1]
    assert len(memberships) == 2
    assert {membership["printing_id"] for membership in memberships} == {
        "054f2276-2dd5-43da-bb26-c57c560861fe"
    }
    assert {membership["oracle_id"] for membership in memberships} == {
        "17039058-822d-409f-938c-b727a366ba63"
    }


def test_error_excerpt_keeps_invalid_request_and_inaccessible_source_distinct() -> None:
    fixture = load_fixture("errors.json")
    provenance = fixture["provenance"]
    cases = fixture["cases"]

    assert isinstance(provenance, dict)
    assert fixture["fixture_type"] == "sanitized-provider-contract-errors"
    assert fixture["schema_version"] == 1
    assert isinstance(fixture["purpose"], str) and fixture["purpose"]
    assert isinstance(fixture["sanitization"], str) and fixture["sanitization"]
    assert len(provenance["source_urls"]) == 2
    assert provenance["response_data_licensing"] == (
        "Not established. This minimal sanitized excerpt is retained only under "
        "CubeAI's approved conservative fixture policy; no broader reuse or "
        "licensing conclusion is made."
    )
    assert isinstance(cases, list)
    by_status = {case["status"]: case for case in cases if isinstance(case, dict)}
    assert by_status[400]["request_category"] == "invalid-historical-date"
    assert by_status[404]["request_category"] == "missing-or-inaccessible-id"


def test_custom_unresolved_case_remains_synthetic_not_provider_evidence() -> None:
    fixture = json.loads(SYNTHETIC_CUSTOM.read_text(encoding="utf-8"))
    unresolved = fixture["memberships"][-1]

    assert fixture["fixture_type"] == "cubeai-synthetic"
    assert unresolved["resolution_status"] == "unresolved_custom"
    assert unresolved["printing_id"] is None
    assert unresolved["oracle_id"] is None
