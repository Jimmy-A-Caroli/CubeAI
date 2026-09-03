"""Local draft-session orchestration without transport or persistence models."""

from dataclasses import dataclass

from cubeai.lab.application.repositories import DraftRepository
from cubeai.lab.domain.allocation import allocate_packs
from cubeai.lab.domain.cube import CubeVersion
from cubeai.lab.domain.draft import Draft, DraftConfiguration, DraftStatus
from cubeai.lab.domain.draft_state import DraftState, available_cards, start_draft
from cubeai.lab.domain.validation import CubeValidationResult, validate_cube_version


class DraftSessionError(ValueError):
    """A local session command cannot start or read a durable draft."""


@dataclass(frozen=True, slots=True)
class DraftSeatView:
    """The one-seat-safe application projection used by the local API."""

    draft_id: str
    cube_version_id: str
    seat_number: int
    status: DraftStatus
    pack_round: int
    pick_number: int
    active_seat: int | None
    current_card_instance_ids: tuple[str, ...]
    pool_card_instance_ids: tuple[str, ...]


def start_local_draft(
    repository: DraftRepository,
    *,
    draft_id: str,
    cube_version_id: str,
    configuration: DraftConfiguration,
) -> DraftState:
    """Validate, allocate, and durably create one deterministic local draft."""

    version = repository.load_cube_version(cube_version_id)
    if version is None:
        raise DraftSessionError("CubeVersion does not exist")
    validation = validate_cube_version(version, configuration)
    if not validation.is_draftable:
        raise DraftSessionError("CubeVersion is not draftable for this configuration")
    draft = Draft(draft_id, version.id, configuration)
    state = start_draft(draft, allocate_packs(draft.id, version, validation))
    repository.save_draft(version, state)
    return state


def resume_local_draft(repository: DraftRepository, draft_id: str) -> DraftState:
    """Load one existing draft or return a stable application error."""

    state = repository.load_draft(draft_id)
    if state is None:
        raise DraftSessionError("draft does not exist")
    return state


def validate_local_cube(
    repository: DraftRepository,
    cube_version_id: str,
    configuration: DraftConfiguration,
) -> CubeValidationResult:
    """Validate one stored CubeVersion for an explicit requested geometry."""

    version = repository.load_cube_version(cube_version_id)
    if version is None:
        raise DraftSessionError("CubeVersion does not exist")
    return validate_cube_version(version, configuration)


def human_seat_view(
    state: DraftState, cube_version: CubeVersion, seat_number: int
) -> DraftSeatView:
    """Return only a human seat's own pool and its currently legal pack."""

    if not 0 <= seat_number < state.draft.configuration.seats:
        raise DraftSessionError("seat number is outside the draft geometry")
    if cube_version.id != state.draft.cube_version_id:
        raise DraftSessionError("CubeVersion does not belong to the draft")
    current = (
        tuple(card.id for card in available_cards(state, seat_number))
        if state.status is not DraftStatus.COMPLETED
        and state.active_seat == seat_number
        else ()
    )
    pool = tuple(
        event.card_instance_id
        for event in state.pick_events
        if event.seat_number == seat_number
    )
    return DraftSeatView(
        state.draft.id,
        cube_version.id,
        seat_number,
        state.status,
        state.pack_round,
        state.pick_number,
        state.active_seat,
        current,
        pool,
    )
