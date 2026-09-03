"""Offline contract tests for the bounded CubeCobra source adapter."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
import urllib.error
import urllib.request

import pytest

from cubeai.lab.adapters.cubecobra import CubeCobraSource
from cubeai.lab.application import (
    DiagnosticCode,
    ImportOutcome,
    SourceFieldState,
    SourceRequest,
)


FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "contracts" / "cubecobra"


class FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class FakeOpener:
    def __init__(self, events: list[FakeResponse | BaseException]) -> None:
        self.events = events
        self.calls: list[tuple[str, str | None, float]] = []

    def __call__(self, request: object, timeout: float) -> FakeResponse:
        assert isinstance(request, urllib.request.Request)
        full_url = request.full_url
        user_agent = request.get_header("User-agent")
        self.calls.append((full_url, user_agent, timeout))
        event = self.events.pop(0)
        if isinstance(event, BaseException):
            raise event
        return event


def _response_fixture(name: str) -> dict[str, object]:
    document = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return document["response_excerpt"]


def _body(payload: object) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _source(
    events: list[FakeResponse | BaseException], **kwargs: object
) -> tuple[CubeCobraSource, FakeOpener]:
    opener = FakeOpener(events)
    return (
        CubeCobraSource(
            opener=opener,
            clock=lambda: datetime(2026, 9, 3, 12, tzinfo=UTC),
            **kwargs,
        ),
        opener,
    )


def _codes(result: object) -> set[DiagnosticCode]:
    assert hasattr(result, "diagnostics")
    return {diagnostic.code for diagnostic in result.diagnostics}


def test_normal_fixture_maps_exact_identity_evidence_and_provenance() -> None:
    source, opener = _source(
        [FakeResponse(200, _body(_response_fixture("normal-public-mainboard.json")))],
        timeout=7.5,
        user_agent="CubeAI adapter test",
    )

    result = source.import_cube(SourceRequest("CubeCobra", "modovintage"))

    assert result.outcome is ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT
    assert result.snapshot is not None
    assert result.snapshot.snapshot_id == "5d2cb3f44153591614458e5d"
    assert result.snapshot.request_identifier == "modovintage"
    assert result.snapshot.returned_short_id == "modovintage"
    assert result.snapshot.retrieved_at == "2026-09-03T12:00:00+00:00"
    assert [(item.name, item.state) for item in result.snapshot.source_metadata] == [
        ("shortId", SourceFieldState.VALUE),
        ("cardCount", SourceFieldState.ABSENT),
        ("version", SourceFieldState.VALUE),
        ("dateLastUpdated", SourceFieldState.VALUE),
    ]
    candidate = result.candidates[0]
    assert candidate.membership_key == "5d2cb3f44153591614458e5d:0"
    assert candidate.provider_card_id == "6681b4a5-d848-4982-a4bf-e18e15b2c1b2"
    assert candidate.printing_hint == "6681b4a5-d848-4982-a4bf-e18e15b2c1b2"
    assert candidate.oracle_id == "4ec85850-f274-4c0c-9a03-0488267caa14"
    assert candidate.printing_hint != candidate.oracle_id
    assert candidate.tags == ()
    assert candidate.notes is None
    assert {item.name for item in candidate.source_metadata} >= {
        "board",
        "index",
        "details.set",
        "details.collector_number",
        "details.language",
        "tags",
        "notes",
        "status",
        "finish",
    }
    assert opener.calls == [
        (
            "https://cubecobra.com/cube/api/cubeJSON/modovintage",
            "CubeAI adapter test",
            7.5,
        )
    ]


def test_duplicate_fixture_conserves_each_array_occurrence() -> None:
    source, _ = _source(
        [FakeResponse(200, _body(_response_fixture("duplicate-mainboard.json")))]
    )

    result = source.import_cube(SourceRequest("cubecobra", "duplicate-cube"))

    assert result.outcome is ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT
    assert [candidate.position for candidate in result.candidates] == [0, 1]
    assert [candidate.membership_key for candidate in result.candidates] == [
        "6c078fb9-5559-4296-a57b-5d86ed19ae90:0",
        "6c078fb9-5559-4296-a57b-5d86ed19ae90:1",
    ]
    assert {candidate.printing_hint for candidate in result.candidates} == {
        "054f2276-2dd5-43da-bb26-c57c560861fe"
    }
    assert {candidate.oracle_id for candidate in result.candidates} == {
        "17039058-822d-409f-938c-b727a366ba63"
    }


def test_error_fixture_statuses_remain_distinct_and_are_not_retried() -> None:
    errors = json.loads((FIXTURES / "errors.json").read_text(encoding="utf-8"))
    cases = {case["status"]: case for case in errors["cases"]}
    source, opener = _source(
        [
            urllib.error.HTTPError(
                "https://cubecobra.com/cube/api/cubeJSON/missing",
                404,
                "not found",
                {},
                None,
            ),
            FakeResponse(400, cases[400]["body"].encode("utf-8")),
        ],
        retries=2,
    )

    inaccessible = source.import_cube(SourceRequest("cubecobra", "missing"))
    invalid = source.import_cube(SourceRequest("cubecobra", "bad-date"))

    assert inaccessible.outcome is ImportOutcome.SOURCE_INACCESSIBLE
    assert _codes(inaccessible) == {DiagnosticCode.SOURCE_INACCESSIBLE}
    assert invalid.outcome is ImportOutcome.SOURCE_REQUEST_INVALID
    assert _codes(invalid) == {DiagnosticCode.SOURCE_REQUEST_INVALID}
    assert len(opener.calls) == 2


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("", ImportOutcome.SOURCE_REQUEST_INVALID),
        (" https://cubecobra.com/cube/list ", ImportOutcome.SOURCE_REQUEST_INVALID),
        ("cube?date=1", ImportOutcome.SOURCE_REQUEST_INVALID),
    ],
)
def test_identifier_only_contract_rejects_empty_urls_and_queries(
    identifier: str, expected: ImportOutcome
) -> None:
    source, opener = _source([])

    result = source.import_cube(SourceRequest("cubecobra", identifier))

    assert result.outcome is expected
    assert _codes(result) == {DiagnosticCode.SOURCE_REQUEST_INVALID}
    assert opener.calls == []


@pytest.mark.parametrize(
    ("status", "outcome", "code", "expected_calls"),
    [
        (429, ImportOutcome.SOURCE_RATE_LIMITED, DiagnosticCode.SOURCE_RATE_LIMITED, 1),
        (500, ImportOutcome.SOURCE_UNAVAILABLE, DiagnosticCode.SOURCE_UNAVAILABLE, 2),
    ],
)
def test_rate_limits_are_never_retried_but_5xx_is_bounded(
    status: int, outcome: ImportOutcome, code: DiagnosticCode, expected_calls: int
) -> None:
    source, opener = _source(
        [FakeResponse(status, b"failure"), FakeResponse(status, b"failure")], retries=1
    )

    result = source.import_cube(SourceRequest("cubecobra", "cube"))

    assert result.outcome is outcome
    assert _codes(result) == {code}
    assert len(opener.calls) == expected_calls


def test_injected_retry_delay_is_used_only_for_retryable_failures() -> None:
    delays: list[float] = []
    source, _ = _source(
        [FakeResponse(500, b"failure"), FakeResponse(500, b"failure")],
        retries=1,
        retry_delay=0.25,
        sleeper=delays.append,
    )

    result = source.import_cube(SourceRequest("cubecobra", "cube"))

    assert result.outcome is ImportOutcome.SOURCE_UNAVAILABLE
    assert delays == [0.25]


def test_constructor_does_not_accept_an_alternative_remote_origin() -> None:
    with pytest.raises(TypeError):
        CubeCobraSource(base_url="https://example.invalid")  # type: ignore[call-arg]


def test_timeout_and_unexpected_provider_errors_cannot_escape_port_boundary() -> None:
    source, opener = _source(
        [TimeoutError(), RuntimeError("provider secret")], retries=1
    )

    result = source.import_cube(SourceRequest("cubecobra", "cube"))

    assert result.outcome is ImportOutcome.SOURCE_UNAVAILABLE
    assert _codes(result) == {DiagnosticCode.SOURCE_UNAVAILABLE}
    assert len(opener.calls) == 2
    assert "provider secret" not in result.diagnostics[0].message


def test_malformed_json_and_malformed_required_response_are_invalid_source() -> None:
    source, _ = _source([FakeResponse(200, b"not json")])
    malformed_json = source.import_cube(SourceRequest("cubecobra", "cube"))

    source, _ = _source([FakeResponse(200, _body({"id": "cube"}))])
    malformed_response = source.import_cube(SourceRequest("cubecobra", "cube"))

    assert malformed_json.outcome is ImportOutcome.INVALID_SOURCE
    assert malformed_response.outcome is ImportOutcome.INVALID_SOURCE
    assert _codes(malformed_json) == {DiagnosticCode.INVALID_SOURCE_RECORD}
    assert _codes(malformed_response) == {DiagnosticCode.INVALID_SOURCE_RECORD}


def test_supplementary_board_is_diagnosed_without_merging_it() -> None:
    payload = _response_fixture("normal-public-mainboard.json")
    payload["cards"]["maybeboard"] = [payload["cards"]["mainboard"][0]]
    source, _ = _source([FakeResponse(200, _body(payload))])

    result = source.import_cube(SourceRequest("cubecobra", "modovintage"))

    assert result.outcome is ImportOutcome.UNSUPPORTED
    assert len(result.candidates) == 1
    assert result.snapshot is not None
    assert result.snapshot.supplementary_boards[0].name == "maybeboard"
    assert result.snapshot.supplementary_boards[0].count == 1
    assert DiagnosticCode.UNSUPPORTED_NON_MAINBOARD in _codes(result)


@pytest.mark.parametrize(
    ("mutation", "voucher_value"),
    [
        ("missing_identity", None),
        ("voucher", ["provider-specific"]),
        ("voucher", []),
        ("voucher", None),
        ("voucher", "unexpected-shape"),
    ],
)
def test_unknown_custom_or_unresolved_shapes_fail_closed(
    mutation: str, voucher_value: object
) -> None:
    payload = _response_fixture("normal-public-mainboard.json")
    row = payload["cards"]["mainboard"][0]
    if mutation == "missing_identity":
        del row["details"]["scryfall_id"]
    elif mutation == "voucher":
        row["voucher_cards"] = voucher_value
    else:
        raise AssertionError(f"unexpected mutation: {mutation}")
    source, _ = _source([FakeResponse(200, _body(payload))])

    result = source.import_cube(SourceRequest("cubecobra", "modovintage"))

    assert result.outcome is ImportOutcome.UNKNOWN_SOURCE_SHAPE
    assert result.candidates == ()
    assert _codes(result) == {DiagnosticCode.UNKNOWN_SOURCE_SHAPE}


def test_custom_name_remains_allowed_optional_display_metadata() -> None:
    payload = _response_fixture("normal-public-mainboard.json")
    payload["cards"]["mainboard"][0]["custom_name"] = "Display override"
    source, _ = _source([FakeResponse(200, _body(payload))])

    result = source.import_cube(SourceRequest("cubecobra", "modovintage"))

    assert result.outcome is ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT
    assert result.candidates[0].custom_name == "Display override"


def test_card_count_mismatch_is_nonfatal_and_diagnostic() -> None:
    payload = _response_fixture("normal-public-mainboard.json")
    payload["cardCount"] = 2
    source, _ = _source([FakeResponse(200, _body(payload))])

    result = source.import_cube(SourceRequest("cubecobra", "modovintage"))

    assert result.outcome is ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT
    assert len(result.candidates) == 1
    assert DiagnosticCode.CARD_COUNT_MISMATCH in _codes(result)


@pytest.mark.parametrize(
    ("notes", "expected_state"),
    [
        (None, SourceFieldState.NULL),
        ("", SourceFieldState.EMPTY_STRING),
        ([], SourceFieldState.EMPTY_ARRAY),
        (["wrong-type-list"], SourceFieldState.MALFORMED),
    ],
)
def test_optional_notes_observation_preserves_empty_and_malformed_shapes(
    notes: object, expected_state: SourceFieldState
) -> None:
    payload = _response_fixture("normal-public-mainboard.json")
    payload["cards"]["mainboard"][0]["notes"] = notes
    source, _ = _source([FakeResponse(200, _body(payload))])

    result = source.import_cube(SourceRequest("cubecobra", "modovintage"))

    observation = next(
        item for item in result.candidates[0].source_metadata if item.name == "notes"
    )
    assert observation.state is expected_state


def test_optional_notes_absence_is_preserved_separately_from_null_and_empty() -> None:
    payload = _response_fixture("normal-public-mainboard.json")
    del payload["cards"]["mainboard"][0]["notes"]
    source, _ = _source([FakeResponse(200, _body(payload))])

    result = source.import_cube(SourceRequest("cubecobra", "modovintage"))

    observation = next(
        item for item in result.candidates[0].source_metadata if item.name == "notes"
    )
    assert observation.state is SourceFieldState.ABSENT


def test_unlisted_visibility_and_empty_mainboard_are_distinct_unsupported_outcomes() -> (
    None
):
    unlisted = _response_fixture("normal-public-mainboard.json")
    unlisted["visibility"] = "un"
    empty = _response_fixture("normal-public-mainboard.json")
    empty["cards"]["mainboard"] = []
    source, _ = _source(
        [FakeResponse(200, _body(unlisted)), FakeResponse(200, _body(empty))]
    )

    visibility = source.import_cube(SourceRequest("cubecobra", "unlisted"))
    mainboard = source.import_cube(SourceRequest("cubecobra", "empty"))

    assert visibility.outcome is ImportOutcome.UNSUPPORTED
    assert _codes(visibility) == {DiagnosticCode.UNSUPPORTED_VISIBILITY}
    assert mainboard.outcome is ImportOutcome.UNSUPPORTED
    assert _codes(mainboard) == {DiagnosticCode.EMPTY_MAINBOARD}


def test_optional_shape_diagnostics_preserve_the_supported_membership() -> None:
    payload = _response_fixture("normal-public-mainboard.json")
    payload["cardCount"] = "not-a-number"
    payload["cards"]["mainboard"][0]["tags"] = {"not": "a-list"}
    source, _ = _source([FakeResponse(200, _body(payload))])

    result = source.import_cube(SourceRequest("cubecobra", "modovintage"))

    assert result.outcome is ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT
    assert len(result.candidates) == 1
    assert _codes(result) == {DiagnosticCode.OPTIONAL_SOURCE_DATA_MALFORMED}
