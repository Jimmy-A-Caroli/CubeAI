"""Versioned FastAPI adapter for the minimal local CubeAI draft workflow."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from cubeai.lab.adapters.cubecobra import CubeCobraSource
from cubeai.lab.adapters.scryfall import SQLiteScryfallCache, ScryfallMetadataResolver
from cubeai.lab.adapters.sqlite_drafts import (
    PersistenceConflict,
    PersistenceError,
    SQLiteDraftRepository,
)
from cubeai.lab.application import (
    CardMetadataLookup,
    DraftDecisionObservation,
    DraftSessionError,
    DraftTracking,
    DraftTrackingError,
    LOCAL_HUMAN_SEAT,
    TrackingPersistenceError,
    derive_draft_observations,
    human_seat_view,
    import_local_cube,
    resume_local_draft,
    start_local_draft,
    submit_human_pick_and_advance_bots,
    track_card,
    tracked_cards,
    untrack_card,
    validate_local_cube,
)
from cubeai.lab.application.cube_versions import CubeVersionAssemblyResult
from cubeai.lab.application.imports import CubeSource, ImportResult
from cubeai.lab.application.metadata import MetadataResolver, ResolvedPrinting
from cubeai.lab.application.repositories import DraftRepository
from cubeai.lab.application.ratings import load_raw_ranking_v0_artifact
from cubeai.lab.domain.bot import BotStrategy, RawRankingStrategyV0
from cubeai.lab.domain.cube import CubeCard, CubeVersion
from cubeai.lab.domain.draft import (
    ActorOrigin,
    DraftCardInstance,
    DraftConfiguration,
    DraftStatus,
    PickEvent,
)
from cubeai.lab.domain.draft_state import DraftState, DraftTransitionError
from cubeai.lab.domain.validation import CubeValidationDiagnostic


class _Dto(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorDto(_Dto):
    code: str
    detail: str


class DraftConfigurationDto(_Dto):
    seats: int = Field(gt=0)
    packs_per_seat: int = Field(gt=0)
    pack_size: int = Field(gt=0)
    seed: int

    def domain(self) -> DraftConfiguration:
        return DraftConfiguration(
            self.seats, self.packs_per_seat, self.pack_size, self.seed
        )


class CubeImportRequestDto(_Dto):
    identifier: str = Field(min_length=1)
    cube_name: str = Field(min_length=1)
    offline: bool = False


class DiagnosticDto(_Dto):
    code: str
    severity: str
    message: str


class CubeImportDto(_Dto):
    outcome: str
    cube_version_id: str | None
    usable: bool | None
    diagnostics: list[DiagnosticDto]
    supplementary_boards: list[str]


class CubeVersionDto(_Dto):
    id: str
    cube_name: str
    membership_count: int


class ValidationDto(_Dto):
    draftable: bool
    usable_membership_count: int
    diagnostics: list[DiagnosticDto]


class StartDraftRequestDto(_Dto):
    draft_id: str = Field(min_length=1)
    cube_version_id: str = Field(min_length=1)
    configuration: DraftConfigurationDto


class PickRequestDto(_Dto):
    card_instance_id: str = Field(min_length=1)


class CardDetailsDto(_Dto):
    name: str
    image_url: str | None
    mana_cost: str | None
    type_line: str | None
    oracle_text: str | None
    power: str | None
    toughness: str | None
    loyalty: str | None
    colors: list[str]


class CardDto(CardDetailsDto):
    instance_id: str
    cube_card_id: str


class DraftViewDto(_Dto):
    draft_id: str
    cube_version_id: str
    seat_number: int
    status: str
    pack_number: int
    pick_number: int
    cube_name: str
    configuration: DraftConfigurationDto
    current_pack: list[CardDto]
    pool: list[CardDto]


class BotProvenanceDto(_Dto):
    strategy_id: str
    strategy_version: str
    rating_artifact_id: str
    rating_artifact_version: str
    selected_rating: float
    rating_lookup_outcome: str
    tie_break_reason: str


class DraftReviewPickDto(_Dto):
    seat_number: int
    round_number: int
    pick_number: int
    card: CardDetailsDto
    bot_provenance: BotProvenanceDto | None


class DraftReviewDto(_Dto):
    draft_id: str
    cube_name: str
    configuration: DraftConfigurationDto
    human_picks: list[DraftReviewPickDto]
    bot_picks: list[DraftReviewPickDto]


class ObservationCardDto(CardDetailsDto):
    instance_id: str
    cube_card_id: str
    printing_id: str | None
    oracle_id: str | None


class DraftDecisionObservationDto(_Dto):
    sequence: int
    seat_number: int
    actor_origin: str
    actor_id: str
    pack_number: int
    pick_number: int
    chosen_card: ObservationCardDto
    cards_seen: list[ObservationCardDto]
    pool_before: list[ObservationCardDto]
    bot_provenance: BotProvenanceDto | None


class DraftObservationsDto(_Dto):
    draft_id: str
    cube_version_id: str
    cube_name: str
    configuration: DraftConfigurationDto
    observations: list[DraftDecisionObservationDto]


class DraftTrackingDto(_Dto):
    draft_id: str
    observer_seat: int
    tracked_card_instance_ids: list[str]


@dataclass(frozen=True, slots=True)
class LocalApiServices:
    repository: DraftRepository
    source: CubeSource
    resolver: MetadataResolver
    strategy: RawRankingStrategyV0
    metadata_lookup: CardMetadataLookup | None = None


def create_application(services: LocalApiServices) -> FastAPI:
    """Create the outer API adapter with only stable, local workflow routes."""

    app = FastAPI(title="CubeAI local draft API", version="1.0.0")

    @app.exception_handler(DraftSessionError)
    async def draft_session_error(_: Request, error: DraftSessionError) -> JSONResponse:
        return _error_response(409, "DRAFT_COMMAND_REJECTED", str(error))

    @app.exception_handler(TrackingPersistenceError)
    async def tracking_persistence_error(
        _: Request, error: TrackingPersistenceError
    ) -> JSONResponse:
        return _error_response(500, "DRAFT_TRACKING_PERSISTENCE_FAILED", str(error))

    @app.exception_handler(DraftTrackingError)
    async def tracking_error(_: Request, error: DraftTrackingError) -> JSONResponse:
        return _error_response(409, "DRAFT_TRACKING_REJECTED", str(error))

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, error: HTTPException) -> JSONResponse:
        detail = error.detail
        if isinstance(detail, dict) and isinstance(detail.get("code"), str):
            message = detail.get("detail")
            return _error_response(
                error.status_code,
                detail["code"],
                message if isinstance(message, str) else "request failed",
            )
        return _error_response(error.status_code, "HTTP_ERROR", "request failed")

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        _: Request, error: RequestValidationError
    ) -> JSONResponse:
        return _error_response(422, "INVALID_REQUEST", str(error.errors()[0]["msg"]))

    @app.exception_handler(DraftTransitionError)
    async def draft_transition_error(
        _: Request, error: DraftTransitionError
    ) -> JSONResponse:
        return _error_response(409, "DRAFT_COMMAND_REJECTED", str(error))

    @app.exception_handler(PersistenceConflict)
    async def persistence_conflict(
        _: Request, error: PersistenceConflict
    ) -> JSONResponse:
        return _error_response(409, "PERSISTENCE_CONFLICT", str(error))

    @app.exception_handler(PersistenceError)
    async def persistence_error(_: Request, error: PersistenceError) -> JSONResponse:
        return _error_response(500, "PERSISTENCE_FAILED", str(error))

    @app.get("/health", response_model=dict[str, str])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/cube-imports", response_model=CubeImportDto)
    def import_cube(request: CubeImportRequestDto) -> CubeImportDto:
        result = import_local_cube(
            services.repository,
            services.source,
            services.resolver,
            source_name="cubecobra",
            identifier=request.identifier,
            cube_name=request.cube_name,
            offline=request.offline,
        )
        return _import_dto(result.source_result, result.assembly)

    @app.get("/v1/cube-versions/{cube_version_id}", response_model=CubeVersionDto)
    def cube_version(cube_version_id: str) -> CubeVersionDto:
        version = _required_cube_version(services.repository, cube_version_id)
        return CubeVersionDto(
            id=version.id,
            cube_name=version.cube.name,
            membership_count=len(version.cards),
        )

    @app.post(
        "/v1/cube-versions/{cube_version_id}/validation", response_model=ValidationDto
    )
    def validate_cube(
        cube_version_id: str, configuration: DraftConfigurationDto
    ) -> ValidationDto:
        validation = validate_local_cube(
            services.repository, cube_version_id, configuration.domain()
        )
        return ValidationDto(
            draftable=validation.is_draftable,
            usable_membership_count=validation.usable_membership_count,
            diagnostics=[
                _validation_diagnostic_dto(item) for item in validation.diagnostics
            ],
        )

    @app.post("/v1/drafts", response_model=DraftViewDto, status_code=201)
    def start_draft(request: StartDraftRequestDto) -> DraftViewDto:
        state = start_local_draft(
            services.repository,
            draft_id=request.draft_id,
            cube_version_id=request.cube_version_id,
            configuration=request.configuration.domain(),
        )
        return _draft_view(services.repository, state, services.metadata_lookup)

    @app.get("/v1/drafts/{draft_id}", response_model=DraftViewDto)
    def resume_draft(draft_id: str) -> DraftViewDto:
        return _draft_view(
            services.repository,
            resume_local_draft(services.repository, draft_id),
            services.metadata_lookup,
        )

    @app.post("/v1/drafts/{draft_id}/picks", response_model=DraftViewDto)
    def submit_pick(draft_id: str, request: PickRequestDto) -> DraftViewDto:
        state = resume_local_draft(services.repository, draft_id)
        strategies: dict[int, BotStrategy] = {
            seat: services.strategy
            for seat in range(1, state.draft.configuration.seats)
        }
        updated = submit_human_pick_and_advance_bots(
            services.repository,
            draft_id,
            0,
            request.card_instance_id,
            strategies,
        )
        return _draft_view(services.repository, updated, services.metadata_lookup)

    @app.get("/v1/drafts/{draft_id}/tracking", response_model=DraftTrackingDto)
    def get_tracking(draft_id: str) -> DraftTrackingDto:
        return _draft_tracking_dto(
            draft_id, tracked_cards(services.repository, draft_id)
        )

    @app.put(
        "/v1/drafts/{draft_id}/tracking/{card_instance_id}",
        response_model=DraftTrackingDto,
    )
    def add_tracking(draft_id: str, card_instance_id: str) -> DraftTrackingDto:
        return _draft_tracking_dto(
            draft_id, track_card(services.repository, draft_id, card_instance_id)
        )

    @app.delete(
        "/v1/drafts/{draft_id}/tracking/{card_instance_id}",
        response_model=DraftTrackingDto,
    )
    def remove_tracking(draft_id: str, card_instance_id: str) -> DraftTrackingDto:
        return _draft_tracking_dto(
            draft_id, untrack_card(services.repository, draft_id, card_instance_id)
        )

    @app.get("/v1/drafts/{draft_id}/review", response_model=DraftReviewDto)
    def review_draft(draft_id: str) -> DraftReviewDto:
        state = resume_local_draft(services.repository, draft_id)
        if state.status is not DraftStatus.COMPLETED:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "DRAFT_REVIEW_UNAVAILABLE",
                    "detail": "draft review is available after completion",
                },
            )
        return _draft_review(services.repository, state, services.metadata_lookup)

    @app.get("/v1/drafts/{draft_id}/observations", response_model=DraftObservationsDto)
    def draft_observations(draft_id: str) -> DraftObservationsDto:
        state = resume_local_draft(services.repository, draft_id)
        if state.status is not DraftStatus.COMPLETED:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "DRAFT_OBSERVATIONS_UNAVAILABLE",
                    "detail": "draft observations are available after completion",
                },
            )
        return _draft_observations(services.repository, state, services.metadata_lookup)

    return app


def create_default_application(state_directory: Path) -> FastAPI:
    """Wire caller-selected local paths to the accepted outer adapters."""

    resolver = ScryfallMetadataResolver(
        SQLiteScryfallCache(state_directory / "scryfall.sqlite3")
    )
    return create_application(
        LocalApiServices(
            SQLiteDraftRepository(state_directory / "drafts.sqlite3"),
            CubeCobraSource(),
            resolver,
            RawRankingStrategyV0(load_raw_ranking_v0_artifact()),
            resolver,
        )
    )


def _required_cube_version(
    repository: DraftRepository, cube_version_id: str
) -> CubeVersion:
    version = repository.load_cube_version(cube_version_id)
    if version is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "CUBE_VERSION_NOT_FOUND",
                "detail": "CubeVersion does not exist",
            },
        )
    return version


def _draft_tracking_dto(
    draft_id: str, tracking: tuple[DraftTracking, ...]
) -> DraftTrackingDto:
    return DraftTrackingDto(
        draft_id=draft_id,
        observer_seat=LOCAL_HUMAN_SEAT,
        tracked_card_instance_ids=[item.card_instance_id for item in tracking],
    )


def _draft_view(
    repository: DraftRepository,
    state: DraftState,
    metadata_lookup: CardMetadataLookup | None,
) -> DraftViewDto:
    version = _required_cube_version(repository, state.draft.cube_version_id)
    view = human_seat_view(state, version, 0)
    instances = {card.id: card for pack in state.allocation for card in pack.cards}
    memberships = {card.id: card for card in version.cards}
    return DraftViewDto(
        draft_id=view.draft_id,
        cube_version_id=view.cube_version_id,
        seat_number=view.seat_number,
        status=view.status.value,
        pack_number=view.pack_round + 1,
        pick_number=view.pick_number + 1,
        cube_name=version.cube.name,
        configuration=DraftConfigurationDto(
            seats=state.draft.configuration.seats,
            packs_per_seat=state.draft.configuration.packs_per_seat,
            pack_size=state.draft.configuration.pack_size,
            seed=state.draft.configuration.seed,
        ),
        current_pack=[
            _card_dto(instances[item], memberships, metadata_lookup)
            for item in view.current_card_instance_ids
        ],
        pool=[
            _card_dto(instances[item], memberships, metadata_lookup)
            for item in view.pool_card_instance_ids
        ],
    )


def _card_dto(
    instance: DraftCardInstance,
    memberships: Mapping[str, CubeCard],
    metadata_lookup: CardMetadataLookup | None,
) -> CardDto:
    return CardDto(
        instance_id=instance.id,
        cube_card_id=instance.cube_card_id,
        **_card_details_dto(
            memberships[instance.cube_card_id], metadata_lookup
        ).model_dump(),
    )


def _observation_card_dto(
    instance: DraftCardInstance,
    memberships: Mapping[str, CubeCard],
    metadata_lookup: CardMetadataLookup | None,
) -> ObservationCardDto:
    membership = memberships[instance.cube_card_id]
    printing = membership.printing
    return ObservationCardDto(
        instance_id=instance.id,
        cube_card_id=instance.cube_card_id,
        printing_id=None if printing is None else printing.id,
        oracle_id=None if printing is None else printing.card_identity.oracle_id,
        **_card_details_dto(membership, metadata_lookup).model_dump(),
    )


def _card_details_dto(
    membership: CubeCard, metadata_lookup: CardMetadataLookup | None
) -> CardDetailsDto:
    if membership.printing is None:
        return CardDetailsDto(
            name="Unresolved card",
            image_url=None,
            mana_cost=None,
            type_line=None,
            oracle_text=None,
            power=None,
            toughness=None,
            loyalty=None,
            colors=[],
        )
    printing = (
        metadata_lookup.lookup_printing(membership.printing.id)
        if metadata_lookup is not None
        else None
    )
    return CardDetailsDto(
        name=membership.printing.card_identity.name,
        image_url=None if printing is None else _image_url(printing),
        mana_cost=None if printing is None else printing.mana_cost,
        type_line=None if printing is None else printing.type_line,
        oracle_text=None if printing is None else printing.oracle_text,
        power=None if printing is None else printing.power,
        toughness=None if printing is None else printing.toughness,
        loyalty=None if printing is None else printing.loyalty,
        colors=[]
        if printing is None
        else list(printing.colors or printing.color_identity),
    )


def _image_url(printing: ResolvedPrinting) -> str | None:
    """Choose an existing printing image URL without changing printing identity."""

    if (image_url := _preferred_image_url(printing.image_uris)) is not None:
        return image_url
    for face in printing.faces:
        if (image_url := _preferred_image_url(face.image_uris)) is not None:
            return image_url
    return None


def _preferred_image_url(image_uris: tuple[tuple[str, str], ...]) -> str | None:
    image_by_size = dict(image_uris)
    for size in ("normal", "grid", "large", "display", "small", "thumb"):
        if (image_url := image_by_size.get(size)) is not None:
            return image_url
    return next(iter(image_by_size.values()), None)


def _draft_review(
    repository: DraftRepository,
    state: DraftState,
    metadata_lookup: CardMetadataLookup | None,
) -> DraftReviewDto:
    version = _required_cube_version(repository, state.draft.cube_version_id)
    instances = {card.id: card for pack in state.allocation for card in pack.cards}
    memberships = {card.id: card for card in version.cards}

    def pick_dto(event: PickEvent) -> DraftReviewPickDto:
        provenance = event.bot_provenance
        return DraftReviewPickDto(
            seat_number=event.seat_number,
            round_number=(
                event.sequence
                // (
                    state.draft.configuration.seats
                    * state.draft.configuration.pack_size
                )
                + 1
            ),
            pick_number=event.pick_number + 1,
            card=_card_details_dto(
                memberships[instances[event.card_instance_id].cube_card_id],
                metadata_lookup,
            ),
            bot_provenance=(
                None
                if provenance is None
                else BotProvenanceDto(
                    strategy_id=provenance.strategy_id,
                    strategy_version=provenance.strategy_version,
                    rating_artifact_id=provenance.rating_artifact_id,
                    rating_artifact_version=provenance.rating_artifact_version,
                    selected_rating=provenance.selected_rating,
                    rating_lookup_outcome=provenance.rating_lookup_outcome.value,
                    tie_break_reason=(
                        "deterministic_order"
                        if provenance.tie_break_reason.value == "instance_id"
                        else provenance.tie_break_reason.value
                    ),
                )
            ),
        )

    configuration = DraftConfigurationDto(
        seats=state.draft.configuration.seats,
        packs_per_seat=state.draft.configuration.packs_per_seat,
        pack_size=state.draft.configuration.pack_size,
        seed=state.draft.configuration.seed,
    )
    return DraftReviewDto(
        draft_id=state.draft.id,
        cube_name=version.cube.name,
        configuration=configuration,
        human_picks=[
            pick_dto(event)
            for event in state.pick_events
            if event.actor_origin is ActorOrigin.HUMAN
        ],
        bot_picks=[
            pick_dto(event)
            for event in state.pick_events
            if event.actor_origin is ActorOrigin.BOT
        ],
    )


def _draft_observations(
    repository: DraftRepository,
    state: DraftState,
    metadata_lookup: CardMetadataLookup | None,
) -> DraftObservationsDto:
    version = _required_cube_version(repository, state.draft.cube_version_id)
    memberships = {card.id: card for card in version.cards}

    def observation_dto(
        observation: DraftDecisionObservation,
    ) -> DraftDecisionObservationDto:
        event = observation.event
        return DraftDecisionObservationDto(
            sequence=event.sequence,
            seat_number=event.seat_number,
            actor_origin=event.actor_origin.value,
            actor_id=event.actor_id,
            pack_number=event.pack_number + 1,
            pick_number=event.pick_number + 1,
            chosen_card=_observation_card_dto(
                observation.chosen_card, memberships, metadata_lookup
            ),
            cards_seen=[
                _observation_card_dto(card, memberships, metadata_lookup)
                for card in observation.cards_seen
            ],
            pool_before=[
                _observation_card_dto(card, memberships, metadata_lookup)
                for card in observation.pool_before
            ],
            bot_provenance=_bot_provenance_dto(event),
        )

    return DraftObservationsDto(
        draft_id=state.draft.id,
        cube_version_id=version.id,
        cube_name=version.cube.name,
        configuration=DraftConfigurationDto(
            seats=state.draft.configuration.seats,
            packs_per_seat=state.draft.configuration.packs_per_seat,
            pack_size=state.draft.configuration.pack_size,
            seed=state.draft.configuration.seed,
        ),
        observations=[
            observation_dto(observation)
            for observation in derive_draft_observations(state)
        ],
    )


def _bot_provenance_dto(event: PickEvent) -> BotProvenanceDto | None:
    provenance = event.bot_provenance
    if provenance is None:
        return None
    return BotProvenanceDto(
        strategy_id=provenance.strategy_id,
        strategy_version=provenance.strategy_version,
        rating_artifact_id=provenance.rating_artifact_id,
        rating_artifact_version=provenance.rating_artifact_version,
        selected_rating=provenance.selected_rating,
        rating_lookup_outcome=provenance.rating_lookup_outcome.value,
        tie_break_reason=(
            "deterministic_order"
            if provenance.tie_break_reason.value == "instance_id"
            else provenance.tie_break_reason.value
        ),
    )


def _import_dto(
    imported: ImportResult, assembly: CubeVersionAssemblyResult | None
) -> CubeImportDto:
    diagnostics = [
        DiagnosticDto(
            code=item.code.value, severity=item.severity.value, message=item.message
        )
        for item in imported.diagnostics
    ]
    if assembly is not None:
        diagnostics.extend(
            DiagnosticDto(code=item.code.value, severity="error", message=item.message)
            for item in assembly.diagnostics
        )
    snapshot = imported.snapshot
    return CubeImportDto(
        outcome=imported.outcome.value,
        cube_version_id=None
        if assembly is None or assembly.cube_version is None
        else assembly.cube_version.id,
        usable=None if assembly is None else assembly.outcome.value == "usable",
        diagnostics=diagnostics,
        supplementary_boards=[]
        if snapshot is None
        else [board.name for board in snapshot.supplementary_boards],
    )


def _validation_diagnostic_dto(item: CubeValidationDiagnostic) -> DiagnosticDto:
    return DiagnosticDto(
        code=item.code.value, severity=item.severity.value, message=item.message
    )


def _error_response(status_code: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content=ErrorDto(code=code, detail=detail).model_dump()
    )
