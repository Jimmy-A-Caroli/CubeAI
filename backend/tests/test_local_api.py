import asyncio
import json

from cubeai.api.app import LocalApiServices, create_application
from cubeai.lab.adapters.sqlite_drafts import SQLiteDraftRepository
from cubeai.lab.application.imports import (
    CubeSource,
    DiagnosticCode,
    DiagnosticSeverity,
    ImportDiagnostic,
    ImportResult,
    ImportOutcome,
    SourceRequest,
)
from cubeai.lab.application.metadata import (
    MetadataResolutionSnapshot,
    MetadataResolver,
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


def _application(tmp_path):
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    repository.save_cube_version(_version())
    return create_application(
        LocalApiServices(
            repository,
            _UnusedSource(),
            _UnusedResolver(),
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
