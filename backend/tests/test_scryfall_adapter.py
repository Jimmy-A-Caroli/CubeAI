"""Offline contract tests for exact-ID Scryfall metadata resolution."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import urllib.error
import urllib.request

import pytest

from cubeai.lab.adapters.scryfall import (
    CACHE_FRESH_FOR,
    MAX_COLLECTION_IDENTIFIERS,
    RATE_LIMIT_COOLDOWN_SECONDS,
    SQLiteScryfallCache,
    ScryfallMetadataResolver,
)
from cubeai.lab.application import (
    CandidateResolution,
    ImportCandidate,
    MetadataDiagnosticCode,
    MetadataResolutionOutcome,
    SourceSnapshotReference,
)


FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "contracts"
    / "scryfall"
    / "exact-collection.json"
)
PRINTING_ID = "11111111-1111-4111-8111-111111111111"
ORACLE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class FakeResponse:
    def __init__(self, status: object, body: object) -> None:
        self.status = status
        self._body = body

    def read(self) -> object:
        return self._body


class FakeOpener:
    def __init__(self, events: list[FakeResponse | BaseException]) -> None:
        self.events = events
        self.calls: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> FakeResponse:
        assert timeout == 10.0
        self.calls.append(request)
        event = self.events.pop(0)
        if isinstance(event, BaseException):
            raise event
        return event


class Clock:
    def __init__(self, value: datetime) -> None:
        self.value = value
        self.delays: list[float] = []

    def now(self) -> datetime:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.delays.append(seconds)
        self.value += timedelta(seconds=seconds)


def _fixture_document() -> dict[str, object]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return document["response"]


def _body(document: object) -> bytes:
    return json.dumps(document).encode("utf-8")


def _candidate(
    membership_key: str = "membership-1",
    *,
    printing_id: str | None = PRINTING_ID,
    oracle_id: str | None = ORACLE_ID,
    resolution: CandidateResolution = CandidateResolution.UNRESOLVED,
) -> ImportCandidate:
    snapshot = SourceSnapshotReference("synthetic-source", "source-1", "2026-09-03")
    return ImportCandidate(
        membership_key,
        snapshot,
        0,
        printing_hint=printing_id,
        oracle_id=oracle_id,
        resolution=resolution,
    )


def _resolver(
    tmp_path: Path,
    events: list[FakeResponse | BaseException],
    *,
    clock: Clock | None = None,
) -> tuple[ScryfallMetadataResolver, FakeOpener, Clock]:
    current_clock = clock or Clock(datetime(2026, 9, 3, 12, tzinfo=UTC))
    opener = FakeOpener(events)
    resolver = ScryfallMetadataResolver(
        SQLiteScryfallCache(tmp_path / "scryfall-cache.sqlite3"),
        user_agent="CubeAI test (https://example.invalid/contact)",
        opener=opener,
        clock=current_clock.now,
        sleeper=current_clock.sleep,
    )
    return resolver, opener, current_clock


def test_exact_collection_contract_maps_printing_and_preserves_identity_layers(
    tmp_path: Path,
) -> None:
    resolver, opener, _ = _resolver(
        tmp_path, [FakeResponse(200, _body(_fixture_document()))]
    )

    snapshot = resolver.resolve((_candidate("membership-A"),))

    result = snapshot.resolutions[0]
    assert result.outcome is MetadataResolutionOutcome.RESOLVED
    assert result.candidate.membership_key == "membership-A"
    assert result.printing is not None
    assert result.printing.printing_id == PRINTING_ID
    assert result.printing.oracle_id == ORACLE_ID
    assert result.printing.provider == "scryfall"
    assert result.printing.name == "Synthetic Ember"
    assert result.printing.set_code == "syn"
    assert result.printing.collector_number == "1"
    assert result.printing.language == "en"
    assert result.printing.layout == "normal"
    assert result.printing.image_uris == (
        ("normal", "https://images.example.invalid/synthetic-ember.jpg"),
    )
    assert (
        result.cache_reference == f"scryfall:{PRINTING_ID}:2026-09-03T12:00:00+00:00:v1"
    )
    assert snapshot.snapshot_id.startswith("scryfall-resolution-v1:")
    request = opener.calls[0]
    assert request.full_url == "https://api.scryfall.com/cards/collection"
    assert (
        request.get_header("User-agent")
        == "CubeAI test (https://example.invalid/contact)"
    )
    assert request.get_header("Accept") == "application/json;q=0.9,*/*;q=0.8"
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data or b"{}") == {"identifiers": [{"id": PRINTING_ID}]}


def test_cache_is_durable_fresh_and_stale_offline_without_network(
    tmp_path: Path,
) -> None:
    resolver, opener, clock = _resolver(
        tmp_path, [FakeResponse(200, _body(_fixture_document()))]
    )
    first = resolver.resolve((_candidate(),))
    assert first.resolutions[0].outcome is MetadataResolutionOutcome.RESOLVED
    assert len(opener.calls) == 1

    reopened, offline_opener, _ = _resolver(tmp_path, [], clock=clock)
    fresh = reopened.resolve((_candidate(),))
    assert fresh.resolutions[0].outcome is MetadataResolutionOutcome.CACHED_FRESH
    assert offline_opener.calls == []

    clock.value += CACHE_FRESH_FOR + timedelta(seconds=1)
    stale = reopened.resolve((_candidate(),), offline=True)
    assert stale.resolutions[0].outcome is MetadataResolutionOutcome.CACHED_STALE
    assert offline_opener.calls == []


def test_stale_online_record_refreshes_and_offline_miss_is_explicit(
    tmp_path: Path,
) -> None:
    clock = Clock(datetime(2026, 9, 3, 12, tzinfo=UTC))
    resolver, _, _ = _resolver(
        tmp_path, [FakeResponse(200, _body(_fixture_document()))], clock=clock
    )
    resolver.resolve((_candidate(),))
    clock.value += CACHE_FRESH_FOR + timedelta(seconds=1)
    refreshed, opener, _ = _resolver(
        tmp_path, [FakeResponse(200, _body(_fixture_document()))], clock=clock
    )

    result = refreshed.resolve((_candidate(),))
    missed = refreshed.resolve(
        (_candidate("missing", printing_id="22222222-2222-4222-8222-222222222222"),),
        offline=True,
    )

    assert result.resolutions[0].outcome is MetadataResolutionOutcome.RESOLVED
    assert len(opener.calls) == 1
    assert (
        missed.resolutions[0].outcome is MetadataResolutionOutcome.PROVIDER_UNAVAILABLE
    )


def test_duplicate_memberships_deduplicate_network_lookup_without_merging_memberships(
    tmp_path: Path,
) -> None:
    resolver, opener, _ = _resolver(
        tmp_path, [FakeResponse(200, _body(_fixture_document()))]
    )

    snapshot = resolver.resolve((_candidate("member-1"), _candidate("member-2")))

    assert [result.candidate.membership_key for result in snapshot.resolutions] == [
        "member-1",
        "member-2",
    ]
    assert [
        result.printing.printing_id
        for result in snapshot.resolutions
        if result.printing
    ] == [
        PRINTING_ID,
        PRINTING_ID,
    ]
    assert len(opener.calls) == 1


def test_exact_printing_oracle_mismatch_is_diagnostic_not_identity_substitution(
    tmp_path: Path,
) -> None:
    resolver, _, _ = _resolver(
        tmp_path, [FakeResponse(200, _body(_fixture_document()))]
    )

    result = resolver.resolve(
        (_candidate(oracle_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),)
    ).resolutions[0]

    assert result.outcome is MetadataResolutionOutcome.RESOLVED
    assert result.printing is not None and result.printing.oracle_id == ORACLE_ID
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        MetadataDiagnosticCode.ORACLE_ID_MISMATCH
    ]


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (
            _candidate(printing_id="not-a-uuid"),
            MetadataResolutionOutcome.INVALID_REFERENCE,
        ),
        (_candidate(printing_id=None), MetadataResolutionOutcome.CUSTOM_OR_UNRESOLVED),
        (
            _candidate(printing_id=None, resolution=CandidateResolution.CUSTOM),
            MetadataResolutionOutcome.CUSTOM_OR_UNRESOLVED,
        ),
    ],
)
def test_invalid_missing_and_custom_inputs_never_trigger_fallback_lookup(
    tmp_path: Path, candidate: ImportCandidate, expected: MetadataResolutionOutcome
) -> None:
    resolver, opener, _ = _resolver(tmp_path, [])

    result = resolver.resolve((candidate,)).resolutions[0]

    assert result.outcome is expected
    assert opener.calls == []


def test_collection_not_found_remains_explicit_and_does_not_fallback(
    tmp_path: Path,
) -> None:
    response = {"data": [], "not_found": [{"id": PRINTING_ID}]}
    resolver, _, _ = _resolver(tmp_path, [FakeResponse(200, _body(response))])

    result = resolver.resolve((_candidate(),)).resolutions[0]

    assert result.outcome is MetadataResolutionOutcome.NOT_FOUND
    assert result.printing is None


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse("200", _body(_fixture_document())),
        FakeResponse(200, "not bytes"),
    ],
)
def test_malformed_response_status_or_body_is_a_structured_contract_failure(
    tmp_path: Path, response: FakeResponse
) -> None:
    resolver, _, _ = _resolver(tmp_path, [response])

    result = resolver.resolve((_candidate(),)).resolutions[0]

    assert result.outcome is MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE


@pytest.mark.parametrize(
    ("events", "expected", "calls"),
    [
        (
            [FakeResponse(400, b"bad")],
            MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE,
            1,
        ),
        (
            [FakeResponse(404, b"missing")],
            MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE,
            1,
        ),
        (
            [FakeResponse(429, b"slow")],
            MetadataResolutionOutcome.PROVIDER_RATE_LIMITED,
            1,
        ),
        (
            [FakeResponse(500, b"failure"), FakeResponse(500, b"failure")],
            MetadataResolutionOutcome.PROVIDER_UNAVAILABLE,
            2,
        ),
        (
            [urllib.error.URLError("offline"), urllib.error.URLError("offline")],
            MetadataResolutionOutcome.NETWORK_FAILURE,
            2,
        ),
        (
            [RuntimeError("provider secret")],
            MetadataResolutionOutcome.PROVIDER_CONTRACT_FAILURE,
            1,
        ),
    ],
)
def test_provider_failures_are_structured_and_exceptions_do_not_escape(
    tmp_path: Path,
    events: list[FakeResponse | BaseException],
    expected: MetadataResolutionOutcome,
    calls: int,
) -> None:
    resolver, opener, _ = _resolver(tmp_path, events)

    result = resolver.resolve((_candidate(),)).resolutions[0]

    assert result.outcome is expected
    assert len(opener.calls) == calls


def test_collection_batching_pacing_and_retry_limits_are_deterministic(
    tmp_path: Path,
) -> None:
    identifiers = [
        f"{index:08x}-1111-4111-8111-111111111111"
        for index in range(MAX_COLLECTION_IDENTIFIERS + 1)
    ]
    candidates = tuple(
        _candidate(f"membership-{index}", printing_id=identifier, oracle_id=None)
        for index, identifier in enumerate(identifiers)
    )
    first_response = {
        "data": [],
        "not_found": [{"id": identifier} for identifier in identifiers[:75]],
    }
    second_response = {
        "data": [],
        "not_found": [{"id": identifiers[75]}],
    }
    resolver, opener, clock = _resolver(
        tmp_path,
        [
            FakeResponse(200, _body(first_response)),
            FakeResponse(500, b"retry"),
            FakeResponse(200, _body(second_response)),
        ],
    )

    snapshot = resolver.resolve(candidates)

    assert len(opener.calls) == 3
    assert all(
        result.outcome is MetadataResolutionOutcome.NOT_FOUND
        for result in snapshot.resolutions
    )
    assert clock.delays == [0.5, 0.5]


def test_rate_limit_stops_following_batch_for_the_policy_cooldown(
    tmp_path: Path,
) -> None:
    identifiers = [
        f"{index:08x}-2222-4222-8222-222222222222"
        for index in range(MAX_COLLECTION_IDENTIFIERS + 1)
    ]
    candidates = tuple(
        _candidate(f"membership-{index}", printing_id=identifier, oracle_id=None)
        for index, identifier in enumerate(identifiers)
    )
    second_response = {
        "data": [],
        "not_found": [{"id": identifiers[75]}],
    }
    resolver, _, clock = _resolver(
        tmp_path,
        [FakeResponse(429, b"slow"), FakeResponse(200, _body(second_response))],
    )

    snapshot = resolver.resolve(candidates)

    assert all(
        result.outcome is MetadataResolutionOutcome.PROVIDER_RATE_LIMITED
        for result in snapshot.resolutions[:75]
    )
    assert snapshot.resolutions[75].outcome is MetadataResolutionOutcome.NOT_FOUND
    assert RATE_LIMIT_COOLDOWN_SECONDS in clock.delays


def test_snapshot_is_deterministic_for_a_fixed_clock_and_cached_record(
    tmp_path: Path,
) -> None:
    resolver, _, clock = _resolver(
        tmp_path, [FakeResponse(200, _body(_fixture_document()))]
    )
    resolver.resolve((_candidate(),))
    reopened, _, _ = _resolver(tmp_path, [], clock=clock)
    first_cached = reopened.resolve((_candidate(),), offline=True)
    second_cached = reopened.resolve((_candidate(),), offline=True)

    assert first_cached == second_cached
    assert first_cached.resolutions[0].outcome is MetadataResolutionOutcome.CACHED_FRESH
