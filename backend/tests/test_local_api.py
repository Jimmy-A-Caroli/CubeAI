import asyncio
import json

from cubeai.api.app import LocalApiServices, _image_url, create_application
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
    ScryfallFace,
)
from cubeai.lab.application.ratings import load_raw_ranking_v0_artifact
from cubeai.lab.domain import (
    ActorOrigin,
    AllocatedPack,
    BotDecisionProvenance,
    BotTieBreakReason,
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    Draft,
    DraftCardInstance,
    DraftConfiguration,
    DraftPack,
    RawRankingStrategyV0,
    RatingLookupOutcome,
    ResolutionStatus,
    pick_card,
    start_draft,
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


def _eight_card_version() -> CubeVersion:
    return CubeVersion(
        "fast-version",
        Cube("fast-cube", "Fast Draft Cube"),
        tuple(
            CubeCard(
                f"fast-membership-{index}",
                ResolutionStatus.RESOLVED,
                CardPrinting(
                    f"fast-printing-{index}",
                    CardIdentity(
                        f"fast-identity-{index}",
                        f"Fast Synthetic {index}",
                        ResolutionStatus.RESOLVED,
                        f"fast-oracle-{index}",
                    ),
                ),
            )
            for index in range(8)
        ),
    )


def _duplicate_identity_version() -> CubeVersion:
    duplicate_identity = CardIdentity(
        "identity-shared",
        "Shared identity",
        ResolutionStatus.RESOLVED,
        "oracle-shared",
    )
    return CubeVersion(
        "duplicate-version",
        Cube("cube-duplicate", "Duplicate Cube"),
        (
            CubeCard(
                "membership-duplicate-a",
                ResolutionStatus.RESOLVED,
                CardPrinting("printing-shared", duplicate_identity),
            ),
            CubeCard(
                "membership-duplicate-b",
                ResolutionStatus.RESOLVED,
                CardPrinting("printing-shared", duplicate_identity),
            ),
            CubeCard(
                "membership-c",
                ResolutionStatus.RESOLVED,
                CardPrinting(
                    "printing-c",
                    CardIdentity(
                        "identity-c",
                        "Synthetic C",
                        ResolutionStatus.RESOLVED,
                        "oracle-c",
                    ),
                ),
            ),
            CubeCard(
                "membership-d",
                ResolutionStatus.RESOLVED,
                CardPrinting(
                    "printing-d",
                    CardIdentity(
                        "identity-d",
                        "Synthetic D",
                        ResolutionStatus.RESOLVED,
                        "oracle-d",
                    ),
                ),
            ),
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
            colors=("U",),
        )


def _application(tmp_path, metadata_lookup=None, version=None):
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    repository.save_cube_version(_version() if version is None else version)
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


def test_fast_draft_completes_eight_bot_seats_and_survives_restart(tmp_path) -> None:
    version = _eight_card_version()
    request = {
        "draft_id": "fast-draft-1",
        "cube_version_id": version.id,
        "configuration": {"seats": 8, "packs_per_seat": 1, "pack_size": 1, "seed": 23},
    }
    app = _application(tmp_path, version=version)

    status, completed = _request(app, "POST", "/v1/drafts/fast", request)

    assert status == 201
    assert completed["status"] == "completed"
    assert completed["mode"] == "all_bot"
    assert len(completed["pool"]) == 1
    inspector_status, inspector = _request(
        app, "GET", "/v1/drafts/fast-draft-1/inspector"
    )
    assert inspector_status == 200
    assert len(inspector["decisions"]) == 8
    assert {item["actor_origin"] for item in inspector["decisions"]} == {"bot"}
    assert {
        item["bot_provenance"]["strategy_id"] for item in inspector["decisions"]
    } == {"raw-ranking-v0"}

    restarted = _application(tmp_path, version=version)
    assert _request(restarted, "GET", "/v1/drafts/fast-draft-1") == (200, completed)
    assert _request(restarted, "GET", "/v1/drafts/fast-draft-1/inspector") == (
        200,
        inspector,
    )


def test_fast_draft_rejects_a_non_eight_seat_configuration(tmp_path) -> None:
    app = _application(tmp_path)
    request = _draft_request()

    status, payload = _request(app, "POST", "/v1/drafts/fast", request)

    assert (status, payload) == (
        422,
        {
            "code": "FAST_DRAFT_REQUIRES_EIGHT_SEATS",
            "detail": "fast draft requires exactly eight seats",
        },
    )


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
    assert card["image_url"] == "https://images.example.invalid/card.jpg"
    assert card["mana_cost"] == "{U}"
    assert card["type_line"] == "Creature — Wizard"
    assert card["oracle_text"] == "A cached rules line."
    assert card["power"] == "1"
    assert card["toughness"] == "1"
    assert card["colors"] == ["U"]
    rendered = json.dumps(started)
    assert "allocation" not in rendered


def test_card_image_selection_prefers_printing_and_uses_face_or_fallback() -> None:
    base = dict(
        provider="scryfall",
        printing_id="printing-1",
        oracle_id="oracle-1",
        name="Split Card",
        set_code="syn",
        collector_number="1",
        language="en",
        layout="transform",
        original_reference="printing-1",
        fetched_at="2026-09-04T00:00:00+00:00",
    )
    face = ScryfallFace(
        "Back Face",
        "oracle-1",
        (("normal", "https://images.example.invalid/face.jpg"),),
    )

    assert (
        _image_url(
            ResolvedPrinting(
                **base,
                faces=(face,),
                image_uris=(("normal", "https://images.example.invalid/printing.jpg"),),
            )
        )
        == "https://images.example.invalid/printing.jpg"
    )
    assert _image_url(ResolvedPrinting(**base, faces=(face,), image_uris=())) == (
        "https://images.example.invalid/face.jpg"
    )
    assert _image_url(ResolvedPrinting(**base, faces=(), image_uris=())) is None
    for key in ("grid", "display", "thumb"):
        assert (
            _image_url(
                ResolvedPrinting(
                    **base,
                    faces=(),
                    image_uris=((key, f"https://images.example.invalid/{key}.jpg"),),
                )
            )
            == f"https://images.example.invalid/{key}.jpg"
        )
        assert (
            _image_url(
                ResolvedPrinting(
                    **base,
                    faces=(
                        ScryfallFace(
                            "Back Face",
                            "oracle-1",
                            ((key, f"https://images.example.invalid/face-{key}.jpg"),),
                        ),
                    ),
                    image_uris=(),
                )
            )
            == f"https://images.example.invalid/face-{key}.jpg"
        )
    assert (
        _image_url(
            ResolvedPrinting(
                **base,
                faces=(),
                image_uris=(("art_crop", "https://images.example.invalid/art.jpg"),),
            )
        )
        == "https://images.example.invalid/art.jpg"
    )
    assert (
        _image_url(
            ResolvedPrinting(
                **base,
                faces=(
                    ScryfallFace(
                        "Back Face",
                        "oracle-1",
                        (("border_crop", "https://images.example.invalid/border.jpg"),),
                    ),
                ),
                image_uris=(),
            )
        )
        == "https://images.example.invalid/border.jpg"
    )


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


def test_review_reports_draft_round_not_physical_pack_identity(tmp_path) -> None:
    app = _application(tmp_path)
    request = _draft_request()
    request["configuration"] = {
        "seats": 2,
        "packs_per_seat": 2,
        "pack_size": 1,
        "seed": 13,
    }
    _, view = _request(app, "POST", "/v1/drafts", request)

    while view["status"] != "completed":
        _, view = _request(
            app,
            "POST",
            "/v1/drafts/draft-1/picks",
            {"card_instance_id": view["current_pack"][0]["instance_id"]},
        )
    status, review = _request(app, "GET", "/v1/drafts/draft-1/review")

    assert status == 200
    assert [pick["round_number"] for pick in review["human_picks"]] == [1, 2]
    assert [pick["pick_number"] for pick in review["human_picks"]] == [1, 1]
    assert all("pack_number" not in pick for pick in review["human_picks"])
    assert [pick["round_number"] for pick in review["bot_picks"]] == [1, 2]
    assert all("pack_number" not in pick for pick in review["bot_picks"])


def test_observations_are_completion_gated_and_replay_decision_context(
    tmp_path,
) -> None:
    app = _application(tmp_path)
    _, started = _request(app, "POST", "/v1/drafts", _draft_request())

    active_status, active_error = _request(
        app, "GET", "/v1/drafts/draft-1/observations"
    )

    assert (active_status, active_error) == (
        409,
        {
            "code": "DRAFT_OBSERVATIONS_UNAVAILABLE",
            "detail": "draft observations are available after completion",
        },
    )

    view = started
    while view["status"] != "completed":
        _, view = _request(
            app,
            "POST",
            "/v1/drafts/draft-1/picks",
            {"card_instance_id": view["current_pack"][0]["instance_id"]},
        )
    status, response = _request(app, "GET", "/v1/drafts/draft-1/observations")

    assert status == 200
    observations = response["observations"]
    assert [item["sequence"] for item in observations] == [0, 1, 2, 3]
    assert observations[0]["actor_origin"] == "human"
    assert observations[0]["pool_before"] == []
    assert observations[0]["chosen_card"]["instance_id"] in {
        card["instance_id"] for card in observations[0]["cards_seen"]
    }
    assert observations[1]["actor_origin"] == "bot"
    assert observations[1]["bot_provenance"]["strategy_id"] == "raw-ranking-v0"
    assert observations[1]["bot_provenance"]["selected_rating"] is not None
    assert (
        observations[2]["pool_before"][0]["instance_id"]
        == observations[0]["chosen_card"]["instance_id"]
    )
    chosen = observations[0]["chosen_card"]
    assert chosen["printing_id"] is not None
    assert chosen["oracle_id"] is not None


def test_inspector_is_completion_gated_and_projects_factual_bot_evidence(
    tmp_path,
) -> None:
    app = _application(tmp_path)
    _, started = _request(app, "POST", "/v1/drafts", _draft_request())

    active_status, active_error = _request(app, "GET", "/v1/drafts/draft-1/inspector")

    assert (active_status, active_error) == (
        409,
        {
            "code": "DRAFT_INSPECTOR_UNAVAILABLE",
            "detail": "draft inspection is available after completion",
        },
    )

    view = started
    while view["status"] != "completed":
        _, view = _request(
            app,
            "POST",
            "/v1/drafts/draft-1/picks",
            {"card_instance_id": view["current_pack"][0]["instance_id"]},
        )
    status, inspector = _request(app, "GET", "/v1/drafts/draft-1/inspector")

    assert status == 200
    assert inspector["cube_version_id"] == "version-1"
    decisions = inspector["decisions"]
    assert [item["sequence"] for item in decisions] == [0, 1, 2, 3]
    first = decisions[0]
    assert first["actor_origin"] == "human"
    assert first["round_number"] == 1
    assert first["pick_number"] == 1
    assert first["physical_pack_number"] == 1
    assert first["pool_before"] == []
    assert first["seen_before_pick_count"] == 0
    assert first["chosen_card"]["instance_id"] in {
        card["instance_id"] for card in first["cards_seen"]
    }
    bot = decisions[1]
    assert bot["actor_origin"] == "bot"
    assert bot["bot_provenance"]["strategy_id"] == "raw-ranking-v0"
    assert bot["bot_provenance"]["selected_rating"] is not None
    assert "alternative_score" not in json.dumps(inspector)
    assert "annotation" not in json.dumps(inspector)


def test_inspector_consumes_exact_instance_wheel_and_seen_before_pick_facts(
    tmp_path,
) -> None:
    version = CubeVersion(
        "inspector-version",
        Cube("inspector-cube", "Inspector Cube"),
        tuple(
            CubeCard(
                f"membership-{index}",
                ResolutionStatus.RESOLVED,
                CardPrinting(
                    f"printing-{index}",
                    CardIdentity(
                        f"identity-{index}",
                        f"Inspector {index}",
                        ResolutionStatus.RESOLVED,
                        f"oracle-{index}",
                    ),
                ),
            )
            for index in range(6)
        ),
    )
    draft = Draft("wheel-inspector", version.id, DraftConfiguration(2, 1, 3, 5))
    allocation = tuple(
        AllocatedPack(
            DraftPack(draft.id, pack_number, pack_number),
            tuple(
                DraftCardInstance(
                    f"wheel:{pack_number}:{card_number}",
                    draft.id,
                    f"membership-{pack_number * 3 + card_number}",
                )
                for card_number in range(3)
            ),
        )
        for pack_number in range(2)
    )
    bot_provenance = BotDecisionProvenance(
        "raw-ranking-v0",
        "test",
        "test-artifact",
        "test",
        1.0,
        RatingLookupOutcome.RATED,
        BotTieBreakReason.HIGHEST_RATING,
    )
    state = start_draft(draft, allocation)
    state = pick_card(state, 0, "wheel:0:1")
    state = pick_card(
        state,
        1,
        "wheel:1:0",
        actor_origin=ActorOrigin.BOT,
        actor_id="bot-seat-1",
        strategy_ref="raw-ranking-v0@test",
        bot_provenance=bot_provenance,
    )
    state = pick_card(state, 0, "wheel:1:1")
    state = pick_card(
        state,
        1,
        "wheel:0:2",
        actor_origin=ActorOrigin.BOT,
        actor_id="bot-seat-1",
        strategy_ref="raw-ranking-v0@test",
        bot_provenance=bot_provenance,
    )
    state = pick_card(state, 0, "wheel:0:0")
    state = pick_card(
        state,
        1,
        "wheel:1:2",
        actor_origin=ActorOrigin.BOT,
        actor_id="bot-seat-1",
        strategy_ref="raw-ranking-v0@test",
        bot_provenance=bot_provenance,
    )

    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    repository.save_draft(version, state)
    app = create_application(
        LocalApiServices(
            repository,
            _UnusedSource(),
            _UnusedResolver(),
            RawRankingStrategyV0(load_raw_ranking_v0_artifact()),
        )
    )
    status, inspector = _request(app, "GET", "/v1/drafts/wheel-inspector/inspector")

    assert status == 200
    first_seen = inspector["decisions"][0]
    returned = inspector["decisions"][4]
    assert first_seen["wheel_facts"] == [
        {
            "role": "first_seen",
            "card": first_seen["cards_seen"][0],
            "first_seen_sequence": 0,
            "returned_sequence": 4,
        }
    ]
    assert returned["wheel_facts"][0]["role"] == "returned"
    assert returned["wheel_facts"][0]["card"]["instance_id"] == "wheel:0:0"
    assert returned["seen_before_pick_count"] == 1


def test_observations_preserve_duplicate_memberships_with_shared_identity(
    tmp_path,
) -> None:
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    version = _duplicate_identity_version()
    repository.save_cube_version(version)
    app = create_application(
        LocalApiServices(
            repository,
            _UnusedSource(),
            _UnusedResolver(),
            RawRankingStrategyV0(load_raw_ranking_v0_artifact()),
        )
    )
    _, view = _request(
        app,
        "POST",
        "/v1/drafts",
        {
            "draft_id": "duplicate-draft",
            "cube_version_id": version.id,
            "configuration": {
                "seats": 1,
                "packs_per_seat": 1,
                "pack_size": 4,
                "seed": 7,
            },
        },
    )
    while view["status"] != "completed":
        _, view = _request(
            app,
            "POST",
            "/v1/drafts/duplicate-draft/picks",
            {"card_instance_id": view["current_pack"][0]["instance_id"]},
        )
    _, response = _request(app, "GET", "/v1/drafts/duplicate-draft/observations")

    shared = [
        card
        for card in response["observations"][0]["cards_seen"]
        if card["oracle_id"] == "oracle-shared"
    ]
    assert {card["cube_card_id"] for card in shared} == {
        "membership-duplicate-a",
        "membership-duplicate-b",
    }
    assert len({card["instance_id"] for card in shared}) == 2
    shared_picks = [
        item["chosen_card"]
        for item in response["observations"]
        if item["chosen_card"]["oracle_id"] == "oracle-shared"
    ]
    assert {card["cube_card_id"] for card in shared_picks} == {
        "membership-duplicate-a",
        "membership-duplicate-b",
    }
    assert len({card["instance_id"] for card in shared_picks}) == 2


def test_local_human_tracking_survives_restart_without_changing_observations(
    tmp_path,
) -> None:
    app = _application(tmp_path)
    _, started = _request(app, "POST", "/v1/drafts", _draft_request())
    target = started["current_pack"][1]["instance_id"]

    assert _request(app, "GET", "/v1/drafts/draft-1/tracking") == (
        200,
        {
            "draft_id": "draft-1",
            "observer_seat": 0,
            "tracked_card_instance_ids": [],
        },
    )

    status, tracked = _request(app, "PUT", f"/v1/drafts/draft-1/tracking/{target}")

    assert (status, tracked) == (
        200,
        {
            "draft_id": "draft-1",
            "observer_seat": 0,
            "tracked_card_instance_ids": [target],
        },
    )
    rejected_status, rejected = _request(
        app, "PUT", "/v1/drafts/draft-1/tracking/other-draft:card:0:0"
    )
    assert (rejected_status, rejected["code"]) == (409, "DRAFT_TRACKING_REJECTED")

    view = started
    while view["status"] != "completed":
        _, view = _request(
            app,
            "POST",
            "/v1/drafts/draft-1/picks",
            {"card_instance_id": view["current_pack"][0]["instance_id"]},
        )
    _, before_observations = _request(app, "GET", "/v1/drafts/draft-1/observations")

    restarted = _application(tmp_path)
    tracking_status, restored_tracking = _request(
        restarted, "GET", "/v1/drafts/draft-1/tracking"
    )
    _, restored_observations = _request(
        restarted, "GET", "/v1/drafts/draft-1/observations"
    )

    assert tracking_status == 200
    assert restored_tracking == tracked
    assert restored_observations == before_observations


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
