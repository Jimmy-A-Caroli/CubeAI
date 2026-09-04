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
    DraftSessionError,
    human_seat_view,
    import_local_cube,
    resume_local_draft,
    start_local_draft,
    submit_human_pick_and_advance_bots,
    validate_local_cube,
)
from cubeai.lab.application.cube_versions import CubeVersionAssemblyResult
from cubeai.lab.application.imports import CubeSource, ImportResult
from cubeai.lab.application.metadata import MetadataResolver
from cubeai.lab.application.repositories import DraftRepository
from cubeai.lab.application.ratings import load_raw_ranking_v0_artifact
from cubeai.lab.domain.bot import BotStrategy, RawRankingStrategyV0
from cubeai.lab.domain.cube import CubeCard, CubeVersion
from cubeai.lab.domain.draft import DraftCardInstance, DraftConfiguration
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


class CardDto(_Dto):
    instance_id: str
    cube_card_id: str
    name: str


class DraftViewDto(_Dto):
    draft_id: str
    cube_version_id: str
    seat_number: int
    status: str
    pack_number: int
    pick_number: int
    current_pack: list[CardDto]
    pool: list[CardDto]


@dataclass(frozen=True, slots=True)
class LocalApiServices:
    repository: DraftRepository
    source: CubeSource
    resolver: MetadataResolver
    strategy: RawRankingStrategyV0


def create_application(services: LocalApiServices) -> FastAPI:
    """Create the outer API adapter with only stable, local workflow routes."""

    app = FastAPI(title="CubeAI local draft API", version="1.0.0")

    @app.exception_handler(DraftSessionError)
    async def draft_session_error(_: Request, error: DraftSessionError) -> JSONResponse:
        return _error_response(409, "DRAFT_COMMAND_REJECTED", str(error))

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
        return _draft_view(services.repository, state)

    @app.get("/v1/drafts/{draft_id}", response_model=DraftViewDto)
    def resume_draft(draft_id: str) -> DraftViewDto:
        return _draft_view(
            services.repository, resume_local_draft(services.repository, draft_id)
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
        return _draft_view(services.repository, updated)

    return app


def create_default_application(state_directory: Path) -> FastAPI:
    """Wire caller-selected local paths to the accepted outer adapters."""

    return create_application(
        LocalApiServices(
            SQLiteDraftRepository(state_directory / "drafts.sqlite3"),
            CubeCobraSource(),
            ScryfallMetadataResolver(
                SQLiteScryfallCache(state_directory / "scryfall.sqlite3")
            ),
            RawRankingStrategyV0(load_raw_ranking_v0_artifact()),
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


def _draft_view(repository: DraftRepository, state: DraftState) -> DraftViewDto:
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
        current_pack=[
            _card_dto(instances[item], memberships)
            for item in view.current_card_instance_ids
        ],
        pool=[
            _card_dto(instances[item], memberships)
            for item in view.pool_card_instance_ids
        ],
    )


def _card_dto(
    instance: DraftCardInstance, memberships: Mapping[str, CubeCard]
) -> CardDto:
    membership = memberships[instance.cube_card_id]
    name = (
        membership.printing.card_identity.name
        if membership.printing is not None
        else "Unresolved card"
    )
    return CardDto(
        instance_id=instance.id, cube_card_id=instance.cube_card_id, name=name
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
