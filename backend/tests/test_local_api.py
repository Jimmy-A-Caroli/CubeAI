import asyncio
import json

from cubeai.api.app import LocalApiServices, create_application
from cubeai.lab.adapters.sqlite_drafts import SQLiteDraftRepository
from cubeai.lab.application.imports import (
    CandidateResolution,
    CubeSource,
    DiagnosticCode,
    DiagnosticSeverity,
    ImportCandidate,
    ImportDiagnostic,
    ImportResult,
    ImportOutcome,
    SourceRequest,
    SourceSnapshotReference,
)
from cubeai.lab.application.metadata import (
    MetadataResolution,
    MetadataResolutionOutcome,
    MetadataResolutionSnapshot,
    MetadataResolver,
    ResolvedPrinting,
)
from cubeai.lab.application.ratings import load_raw_ranking_v0_artifact
from cubeai.lab.domain import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    RawRankingStrategyV0,
    ResolutionStatus,
)


def _version() -> CubeVersion:
    return CubeVersion(
        "version-1",
        Cube("cube-1", "Synthetic Cube"),
        tuple(
            CubeCard(
                f"membership-{index}",
                ResolutionStatus.RESOLVED,
                CardPrinting(
                    f"printing-{index}",
                    CardIdentity(
                        f"identity-{index}",
                        f"Synthetic {index}",
                        ResolutionStatus.RESOLVED,
                        f"oracle-{index}",
                    ),
                ),
            )
            for index in range(4)
        ),
    )


class _UnusedSource(CubeSource):
    def import_cube(self, request: SourceRequest) -> ImportResult:
        raise AssertionError("this test does not invoke import")


class _UnusedResolver(MetadataResolver):
    def resolve(
        self, candidates, *, offline: bool = False
    ) -> MetadataResolutionSnapshot:
        raise AssertionError("this test does not invoke metadata resolution")


class _UnavailableSource(CubeSource):
    def import_cube(self, request: SourceRequest) -> ImportResult:
        return ImportResult(
            None,
            (),
            (
                ImportDiagnostic(
                    DiagnosticCode.SOURCE_UNAVAILABLE,
                    DiagnosticSeverity.ERROR,
                    "provider unavailable",
                ),
            ),
            ImportOutcome.SOURCE_UNAVAILABLE,
        )


class _FixtureSource(CubeSource):
    """Four resolved memberships for the fixed M1 acceptance geometry."""

    def import_cube(self, request: SourceRequest) -> ImportResult:
        snapshot = SourceSnapshotReference(
            "synthetic-fixture", "m1-acceptance-cube", "2026-09-04T00:00:00+00:00"
        )
        candidates = tuple(
            ImportCandidate(
                f"membership-{index}",
                snapshot,
                index,
                printing_hint=f"printing-{index}",
                oracle_id=f"oracle-{index}",
                resolution=CandidateResolution.RESOLUTION_HINTED,
            )
            for index in range(4)
        )
        return ImportResult(snapshot, candidates)


class _FixtureResolver(MetadataResolver):
    def __init__(self) -> None:
        self._resolution_count = 0

    def resolve(
        self, candidates, *, offline: bool = False
    ) -> MetadataResolutionSnapshot:
        self._resolution_count += 1
        resolutions = tuple(
            MetadataResolution(
                candidate,
                MetadataResolutionOutcome.RESOLVED,
                ResolvedPrinting(
                    "synthetic-fixture",
                    f"printing-{index}",
                    f"oracle-{index}",
                    f"Synthetic {index}",
                    "syn",
                    str(index),
                    "en",
                    "normal",
                    (),
                    (),
                    f"printing-{index}",
                    "2026-09-04T00:00:00+00:00",
                ),
                f"fixture:printing-{index}",
            )
            for index, candidate in enumerate(candidates)
        )
        return MetadataResolutionSnapshot(
            f"m1-acceptance-resolution-{self._resolution_count}",
            "2026-09-04T00:00:00+00:00",
            resolutions,
        )


class _DisplayLookup:
    """Cache-shaped display data for API presentation tests only."""

    def lookup_printing(self, printing_id: str) -> ResolvedPrinting | None:
        return ResolvedPrinting(
            "scryfall",
            printing_id,
            f"oracle-{printing_id}",
            "Cached display record",
            "syn",
            "1",
            "en",
            "normal",
            (),
            (("normal", "https://images.example.invalid/card.jpg"),),
            printing_id,
            "2026-09-04T00:00:00+00:00",
            mana_cost="{U}",
            type_line="Creature — Wizard",
            oracle_text="A cached rules line.",
            power="1",
            toughness="1",
        )


def _application(tmp_path, metadata_lookup=None):
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    repository.save_cube_version(_version())
    return create_application(
        LocalApiServices(
            repository,
            _UnusedSource(),
            _UnusedResolver(),
            RawRankingStrategyV0(load_raw_ranking_v0_artifact()),
            metadata_lookup,
        )
    )


def _fixture_application(tmp_path):
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    return create_application(
        LocalApiServices(
            repository,
            _FixtureSource(),
            _FixtureResolver(),
            RawRankingStrategyV0(load_raw_ranking_v0_artifact()),
        )
    )


def _request(app, method: str, path: str, payload: dict[str, object] | None = None):
    body = b"" if payload is None else json.dumps(payload).encode()
    messages: list[dict[str, object]] = []
    received = False

    async def receive() -> dict[str, object]:
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("test", 123),
        "server": ("test", 80),
    }
    asyncio.run(app(scope, receive, send))
    status = next(
        item["status"] for item in messages if item["type"] == "http.response.start"
    )
    response_body = b"".join(
        item.get("body", b"")
        for item in messages
        if item["type"] == "http.response.body"
    )
    return status, json.loads(response_body)


def _draft_request() -> dict[str, object]:
    return {
        "draft_id": "draft-1",
        "cube_version_id": "version-1",
        "configuration": {"seats": 2, "packs_per_seat": 1, "pack_size": 2, "seed": 13},
    }


def test_local_api_starts_resumes_and_advances_a_human_pick_with_bot_turns(
    tmp_path,
) -> None:
    app = _application(tmp_path)

    status, started = _request(app, "POST", "/v1/drafts", _draft_request())
    assert status == 201
    assert started["seat_number"] == 0
    assert len(started["current_pack"]) == 2
    selected = started["current_pack"][0]["instance_id"]

    status, updated = _request(
        app, "POST", "/v1/drafts/draft-1/picks", {"card_instance_id": selected}
    )

    assert status == 200
    assert [card["instance_id"] for card in updated["pool"]] == [selected]
    assert len(updated["current_pack"]) == 1
    assert _request(app, "GET", "/v1/drafts/draft-1") == (200, updated)


def test_hidden_draft_state_is_absent_from_the_view_and_openapi_contract(
    tmp_path,
) -> None:
    app = _application(tmp_path)
    _, started = _request(app, "POST", "/v1/drafts", _draft_request())

    rendered = json.dumps(started)
    schema = json.dumps(app.openapi())

    for forbidden in (
        "allocation",
        "active_packs",
        "pick_events",
        "other_seat",
        "bot_state",
    ):
        assert forbidden not in rendered
        assert forbidden not in schema
    assert "/v1/drafts/{draft_id}/seats/{seat_number}" not in app.openapi()["paths"]


def test_draft_view_uses_cached_display_data_without_exposing_hidden_state(
    tmp_path,
) -> None:
    app = _application(tmp_path, _DisplayLookup())

    status, started = _request(app, "POST", "/v1/drafts", _draft_request())

    assert status == 201
    card = started["current_pack"][0]
    assert card["image_url"] is None
    assert card["mana_cost"] == "{U}"
    assert card["type_line"] == "Creature — Wizard"
    assert card["oracle_text"] == "A cached rules line."
    assert card["power"] == "1"
    assert card["toughness"] == "1"
    rendered = json.dumps(started)
    assert "images.example.invalid" not in rendered
    assert "allocation" not in rendered


def test_review_is_gated_until_completion_then_exposes_human_and_bot_history(
    tmp_path,
) -> None:
    app = _application(tmp_path)
    _, started = _request(app, "POST", "/v1/drafts", _draft_request())

    active_status, active_error = _request(app, "GET", "/v1/drafts/draft-1/review")

    assert (active_status, active_error) == (
        409,
        {
            "code": "DRAFT_REVIEW_UNAVAILABLE",
            "detail": "draft review is available after completion",
        },
    )

    view = started
    while view["status"] != "completed":
        selected = view["current_pack"][0]["instance_id"]
        _, view = _request(
            app,
            "POST",
            "/v1/drafts/draft-1/picks",
            {"card_instance_id": selected},
        )
    review_status, review = _request(app, "GET", "/v1/drafts/draft-1/review")

    assert review_status == 200
    assert len(review["human_picks"]) == 2
    assert len(review["bot_picks"]) == 2
    assert review["human_picks"][0]["bot_provenance"] is None
    provenance = review["bot_picks"][0]["bot_provenance"]
    assert provenance["strategy_id"] == "raw-ranking-v0"
    assert provenance["selected_rating"] is not None
    rendered = json.dumps(review)
    for forbidden in ("instance_id", "cube_card_id", "allocation", "active_packs"):
        assert forbidden not in rendered


def test_stale_pick_maps_to_a_stable_error_without_mutating_the_persisted_draft(
    tmp_path,
) -> None:
    app = _application(tmp_path)
    _, started = _request(app, "POST", "/v1/drafts", _draft_request())

    status, error = _request(
        app,
        "POST",
        "/v1/drafts/draft-1/picks",
        {"card_instance_id": "not-a-current-card"},
    )

    assert status == 409
    assert error["code"] == "DRAFT_COMMAND_REJECTED"
    assert _request(app, "GET", "/v1/drafts/draft-1")[1] == started


def test_api_uses_one_error_envelope_for_not_found_and_invalid_requests(
    tmp_path,
) -> None:
    app = _application(tmp_path)

    missing_status, missing = _request(app, "GET", "/v1/cube-versions/missing")
    invalid_status, invalid = _request(app, "POST", "/v1/drafts", {})

    assert (missing_status, missing) == (
        404,
        {"code": "CUBE_VERSION_NOT_FOUND", "detail": "CubeVersion does not exist"},
    )
    assert invalid_status == 422
    assert invalid["code"] == "INVALID_REQUEST"
    assert set(invalid) == {"code", "detail"}


def test_restart_resumes_the_same_human_safe_view(tmp_path) -> None:
    app = _application(tmp_path)
    _, started = _request(app, "POST", "/v1/drafts", _draft_request())

    restarted = _application(tmp_path)

    assert _request(restarted, "GET", "/v1/drafts/draft-1") == (200, started)


def test_provider_failure_returns_a_safe_structured_import_outcome(tmp_path) -> None:
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    app = create_application(
        LocalApiServices(
            repository,
            _UnavailableSource(),
            _UnusedResolver(),
            RawRankingStrategyV0(load_raw_ranking_v0_artifact()),
        )
    )

    status, response = _request(
        app,
        "POST",
        "/v1/cube-imports",
        {"identifier": "modovintage", "cube_name": "Vintage Cube"},
    )

    assert status == 200
    assert response["outcome"] == "source_unavailable"
    assert response["diagnostics"] == [
        {
            "code": "source_unavailable",
            "severity": "error",
            "message": "provider unavailable",
        }
    ]


def test_m1_acceptance_replays_the_fixed_fixture_through_restart(tmp_path) -> None:
    first_directory = tmp_path / "first"
    second_directory = tmp_path / "second"

    first = _complete_m1_fixture_draft(_fixture_application(first_directory))
    second = _complete_m1_fixture_draft(_fixture_application(second_directory))

    assert first == second

    restarted = _fixture_application(first_directory)
    status, resumed = _request(restarted, "GET", "/v1/drafts/m1-acceptance-draft")
    assert status == 200
    assert resumed["status"] == "completed"
    assert resumed["current_pack"] == []
    assert len(resumed["pool"]) == 2


def test_repeated_import_reuses_equivalent_immutable_snapshot_for_new_drafts(
    tmp_path,
) -> None:
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    app = create_application(
        LocalApiServices(
            repository,
            _FixtureSource(),
            _FixtureResolver(),
            RawRankingStrategyV0(load_raw_ranking_v0_artifact()),
        )
    )

    first_status, first_import = _request(
        app,
        "POST",
        "/v1/cube-imports",
        {"identifier": "fixture", "cube_name": "First local label"},
    )
    second_status, second_import = _request(
        app,
        "POST",
        "/v1/cube-imports",
        {"identifier": "fixture", "cube_name": "Renamed local label"},
    )

    assert (first_status, second_status) == (200, 200)
    assert first_import["usable"] is True
    assert second_import["usable"] is True
    assert first_import["cube_version_id"] == second_import["cube_version_id"]
    cube_version_id = first_import["cube_version_id"]
    assert isinstance(cube_version_id, str)
    persisted = repository.load_cube_version(cube_version_id)
    assert persisted is not None
    assert persisted.cube.name == "First local label"
    assert persisted.resolution_snapshot_id == "m1-acceptance-resolution-1"

    configuration = {"seats": 2, "packs_per_seat": 1, "pack_size": 2, "seed": 13}
    for draft_id in ("first-draft", "second-draft"):
        status, view = _request(
            app,
            "POST",
            "/v1/drafts",
            {
                "draft_id": draft_id,
                "cube_version_id": cube_version_id,
                "configuration": configuration,
            },
        )
        assert status == 201
        assert view["cube_version_id"] == cube_version_id


def _complete_m1_fixture_draft(app) -> tuple[object, ...]:
    import_status, imported = _request(
        app,
        "POST",
        "/v1/cube-imports",
        {"identifier": "fixture", "cube_name": "M1 acceptance fixture"},
    )
    assert import_status == 200
    assert imported["usable"] is True
    cube_version_id = imported["cube_version_id"]
    assert isinstance(cube_version_id, str)

    configuration = {"seats": 2, "packs_per_seat": 1, "pack_size": 2, "seed": 13}
    validation_status, validation = _request(
        app, "POST", f"/v1/cube-versions/{cube_version_id}/validation", configuration
    )
    assert validation_status == 200
    assert validation["draftable"] is True

    start_status, view = _request(
        app,
        "POST",
        "/v1/drafts",
        {
            "draft_id": "m1-acceptance-draft",
            "cube_version_id": cube_version_id,
            "configuration": configuration,
        },
    )
    assert start_status == 201
    assert view["seat_number"] == 0

    initial_pack = tuple(card["instance_id"] for card in view["current_pack"])
    while view["status"] != "completed":
        selected = view["current_pack"][0]["instance_id"]
        pick_status, view = _request(
            app,
            "POST",
            "/v1/drafts/m1-acceptance-draft/picks",
            {"card_instance_id": selected},
        )
        assert pick_status == 200

    return (
        initial_pack,
        tuple(card["instance_id"] for card in view["pool"]),
        view["status"],
        view["current_pack"],
    )
