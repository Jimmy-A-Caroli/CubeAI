"""Local-human tracking preferences joined to immutable draft facts."""

from dataclasses import dataclass

from cubeai.lab.application.draft_observations import derive_draft_observations
from cubeai.lab.application.draft_sessions import resume_local_draft
from cubeai.lab.application.repositories import DraftRepository
from cubeai.lab.domain.draft import DraftStatus
from cubeai.lab.domain.draft_state import DraftState, available_cards


LOCAL_HUMAN_SEAT = 0


class DraftTrackingError(ValueError):
    """A local tracking command does not identify a card the human saw."""


class TrackingPersistenceError(DraftTrackingError):
    """A stored local marker no longer resolves against immutable draft facts."""


@dataclass(frozen=True, slots=True)
class DraftTracking:
    """One local-human marker for one exact draft-card instance."""

    draft_id: str
    observer_seat: int
    card_instance_id: str


def tracked_cards(
    repository: DraftRepository, draft_id: str
) -> tuple[DraftTracking, ...]:
    """Return local-human markers after proving they still resolve to seen cards."""

    state = resume_local_draft(repository, draft_id)
    tracked_ids = repository.load_tracked_card_instance_ids(
        state.draft.id, LOCAL_HUMAN_SEAT
    )
    _validate_tracked_ids(state, tracked_ids, stored=True)
    return tuple(
        DraftTracking(state.draft.id, LOCAL_HUMAN_SEAT, card_id)
        for card_id in tracked_ids
    )


def track_card(
    repository: DraftRepository, draft_id: str, card_instance_id: str
) -> tuple[DraftTracking, ...]:
    """Track one card that the local human currently or historically saw."""

    state = resume_local_draft(repository, draft_id)
    _validate_tracked_ids(state, (card_instance_id,), stored=False)
    repository.track_card_instance(state.draft.id, LOCAL_HUMAN_SEAT, card_instance_id)
    return tracked_cards(repository, state.draft.id)


def untrack_card(
    repository: DraftRepository, draft_id: str, card_instance_id: str
) -> tuple[DraftTracking, ...]:
    """Remove one local marker without changing draft history or projections."""

    state = resume_local_draft(repository, draft_id)
    _validate_tracked_ids(state, (card_instance_id,), stored=False)
    repository.untrack_card_instance(state.draft.id, LOCAL_HUMAN_SEAT, card_instance_id)
    return tracked_cards(repository, state.draft.id)


def _validate_tracked_ids(
    state: DraftState, card_instance_ids: tuple[str, ...], *, stored: bool
) -> None:
    seen = _seen_card_instance_ids(state)
    for card_instance_id in card_instance_ids:
        try:
            _validate_card_instance_id(card_instance_id)
            if card_instance_id not in seen:
                raise DraftTrackingError(
                    "card_instance_id was not seen by the local human seat"
                )
        except DraftTrackingError as error:
            if stored:
                raise TrackingPersistenceError(
                    "stored tracking marker cannot be resolved"
                ) from error
            raise


def _seen_card_instance_ids(state: DraftState) -> frozenset[str]:
    seen = {
        card.id
        for observation in derive_draft_observations(state)
        if observation.event.seat_number == LOCAL_HUMAN_SEAT
        for card in observation.cards_seen
    }
    if (
        state.status is not DraftStatus.COMPLETED
        and state.active_seat == LOCAL_HUMAN_SEAT
    ):
        seen.update(card.id for card in available_cards(state, LOCAL_HUMAN_SEAT))
    return frozenset(seen)


def _validate_card_instance_id(card_instance_id: object) -> None:
    if not isinstance(card_instance_id, str) or not card_instance_id.strip():
        raise DraftTrackingError("card_instance_id must be a nonblank string")
