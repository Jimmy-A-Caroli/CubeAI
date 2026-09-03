"""Immutable deterministic state transitions for a locally managed draft."""

from dataclasses import dataclass

from cubeai.lab.domain.allocation import AllocatedPack
from cubeai.lab.domain.draft import (
    ActorOrigin,
    Draft,
    DraftCardInstance,
    DraftPack,
    DraftPool,
    DraftStatus,
    PickEvent,
)


class DraftTransitionError(ValueError):
    """A command cannot be applied to the supplied immutable draft state."""


@dataclass(frozen=True, slots=True)
class ActiveDraftPack:
    """An allocated pack and its remaining cards at its current table position."""

    pack: DraftPack
    cards: tuple[DraftCardInstance, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.pack, DraftPack):
            raise ValueError("pack must be a DraftPack")
        cards = tuple(self.cards)
        if any(not isinstance(card, DraftCardInstance) for card in cards):
            raise ValueError("cards must contain DraftCardInstance values")
        if any(card.draft_id != self.pack.draft_id for card in cards):
            raise ValueError("cards must belong to the active pack draft")
        if len({card.id for card in cards}) != len(cards):
            raise ValueError("cards must have unique draft-card instance IDs")
        object.__setattr__(self, "cards", cards)


@dataclass(frozen=True, slots=True)
class DraftState:
    """The complete immutable state needed to advance one deterministic draft.

    ``active_packs`` is ordered by the seat currently holding each pack. A
    left pass gives seat ``i`` the pack previously held by seat ``i + 1``;
    a right pass gives seat ``i`` the pack previously held by seat ``i - 1``.
    """

    draft: Draft
    allocation: tuple[AllocatedPack, ...]
    pack_round: int
    pick_number: int
    active_seat: int | None
    active_packs: tuple[ActiveDraftPack, ...]
    pick_events: tuple[PickEvent, ...] = ()
    status: DraftStatus = DraftStatus.IN_PROGRESS

    def __post_init__(self) -> None:
        if not isinstance(self.draft, Draft):
            raise ValueError("draft must be a Draft")
        allocation = tuple(self.allocation)
        if any(not isinstance(pack, AllocatedPack) for pack in allocation):
            raise ValueError("allocation must contain AllocatedPack values")
        _validate_allocation(self.draft, allocation)
        if not isinstance(self.pack_round, int) or isinstance(self.pack_round, bool):
            raise ValueError("pack_round must be an integer")
        if not isinstance(self.pick_number, int) or isinstance(self.pick_number, bool):
            raise ValueError("pick_number must be an integer")
        if self.pick_number < 0:
            raise ValueError("pick_number must be nonnegative")
        active_packs = tuple(self.active_packs)
        if any(not isinstance(pack, ActiveDraftPack) for pack in active_packs):
            raise ValueError("active_packs must contain ActiveDraftPack values")
        events = tuple(self.pick_events)
        if any(not isinstance(event, PickEvent) for event in events):
            raise ValueError("pick_events must contain PickEvent values")
        expected_turn = _validate_pick_events(self.draft, allocation, events)
        if not isinstance(self.status, DraftStatus):
            raise ValueError("status must be a DraftStatus")
        if self.status is DraftStatus.COMPLETED:
            if self.active_seat is not None or active_packs:
                raise ValueError("completed drafts cannot have active packs or seats")
        else:
            if not 0 <= self.pack_round < self.draft.configuration.packs_per_seat:
                raise ValueError("in-progress pack_round must be within draft geometry")
            if self.active_seat is None or not 0 <= self.active_seat < self.draft.configuration.seats:
                raise ValueError("in-progress drafts require an active seat")
            if len(active_packs) != self.draft.configuration.seats:
                raise ValueError("in-progress drafts require one active pack per seat")
            expected_event_count = (
                self.pack_round * self.draft.configuration.seats * self.draft.configuration.pack_size
                + self.pick_number * self.draft.configuration.seats
                + self.active_seat
            )
            if len(events) != expected_event_count:
                raise ValueError("in-progress event count must match the current turn")
            if (
                self.pack_round,
                self.pick_number,
                self.active_seat,
                active_packs,
            ) != expected_turn:
                raise ValueError("in-progress state must match the legal event history")
        if self.status is DraftStatus.COMPLETED:
            if len(events) != self.draft.configuration.card_count:
                raise ValueError("completed drafts must contain every allocated pick")
            if expected_turn[0] != self.draft.configuration.packs_per_seat:
                raise ValueError("completed draft history must exhaust every pack round")
        object.__setattr__(self, "allocation", allocation)
        object.__setattr__(self, "active_packs", active_packs)
        object.__setattr__(self, "pick_events", events)


def start_draft(draft: Draft, allocation: tuple[AllocatedPack, ...]) -> DraftState:
    """Start a draft from one complete deterministic allocation."""

    if not isinstance(draft, Draft):
        raise ValueError("draft must be a Draft")
    allocation = tuple(allocation)
    _validate_allocation(draft, allocation)
    if draft.status is not DraftStatus.CREATED:
        raise DraftTransitionError("only a created draft can be started")
    return DraftState(
        draft=draft,
        allocation=allocation,
        pack_round=0,
        pick_number=0,
        active_seat=0,
        active_packs=_active_packs_for_round(draft, allocation, 0),
    )


def available_cards(state: DraftState, seat_number: int) -> tuple[DraftCardInstance, ...]:
    """Return the current pack only for the active seat's legal pick command."""

    _require_active_seat(state, seat_number)
    return state.active_packs[seat_number].cards


def pick_card(
    state: DraftState,
    seat_number: int,
    card_instance_id: str,
    *,
    actor_origin: ActorOrigin = ActorOrigin.HUMAN,
    actor_id: str | None = None,
    strategy_ref: str | None = None,
) -> DraftState:
    """Apply one legal pick and return a new state without changing ``state``."""

    _require_active_seat(state, seat_number)
    if not isinstance(card_instance_id, str) or not card_instance_id.strip():
        raise DraftTransitionError("card_instance_id must be a nonblank string")
    if not isinstance(actor_origin, ActorOrigin):
        raise DraftTransitionError("actor_origin must be an ActorOrigin")
    if actor_id is None:
        actor_id = f"seat:{seat_number}"
    current_pack = state.active_packs[seat_number]
    selected = next(
        (card for card in current_pack.cards if card.id == card_instance_id), None
    )
    if selected is None:
        raise DraftTransitionError("card_instance_id is not available to the active seat")
    event = PickEvent(
        draft_id=state.draft.id,
        sequence=len(state.pick_events),
        seat_number=seat_number,
        pack_number=current_pack.pack.pack_number,
        pick_number=state.pick_number,
        card_instance_id=selected.id,
        actor_origin=actor_origin,
        actor_id=actor_id,
        strategy_ref=strategy_ref,
    )
    updated_packs = list(state.active_packs)
    updated_packs[seat_number] = ActiveDraftPack(
        current_pack.pack,
        tuple(card for card in current_pack.cards if card.id != selected.id),
    )
    events = (*state.pick_events, event)
    if seat_number + 1 < state.draft.configuration.seats:
        return DraftState(
            state.draft,
            state.allocation,
            state.pack_round,
            state.pick_number,
            seat_number + 1,
            tuple(updated_packs),
            events,
        )
    return _advance_round(state, tuple(updated_packs), events)


def pool_for_seat(state: DraftState, seat_number: int) -> DraftPool:
    """Derive one seat's pool from the immutable ordered event history."""

    _require_seat_number(state, seat_number)
    return DraftPool(
        state.draft.id,
        seat_number,
        tuple(
            event.card_instance_id
            for event in state.pick_events
            if event.seat_number == seat_number
        ),
    )


def _advance_round(
    state: DraftState,
    updated_packs: tuple[ActiveDraftPack, ...],
    events: tuple[PickEvent, ...],
) -> DraftState:
    if not all(not pack.cards for pack in updated_packs):
        return DraftState(
            state.draft,
            state.allocation,
            state.pack_round,
            state.pick_number + 1,
            0,
            _rotate_packs(updated_packs, state.pack_round),
            events,
        )
    next_round = state.pack_round + 1
    if next_round == state.draft.configuration.packs_per_seat:
        return DraftState(
            state.draft,
            state.allocation,
            next_round,
            state.pick_number + 1,
            None,
            (),
            events,
            DraftStatus.COMPLETED,
        )
    return DraftState(
        state.draft,
        state.allocation,
        next_round,
        0,
        0,
        _active_packs_for_round(state.draft, state.allocation, next_round),
        events,
    )


def _rotate_packs(
    active_packs: tuple[ActiveDraftPack, ...], pack_round: int
) -> tuple[ActiveDraftPack, ...]:
    seats = len(active_packs)
    if pack_round % 2 == 0:  # Left: seat i receives the former i + 1 pack.
        return tuple(active_packs[(seat + 1) % seats] for seat in range(seats))
    return tuple(active_packs[(seat - 1) % seats] for seat in range(seats))


def _active_packs_for_round(
    draft: Draft,
    allocation: tuple[AllocatedPack, ...],
    pack_round: int,
) -> tuple[ActiveDraftPack, ...]:
    start = pack_round * draft.configuration.seats
    return tuple(
        ActiveDraftPack(allocated.pack, allocated.cards)
        for allocated in allocation[start : start + draft.configuration.seats]
    )


def _require_active_seat(state: DraftState, seat_number: int) -> None:
    if not isinstance(state, DraftState):
        raise ValueError("state must be a DraftState")
    _require_seat_number(state, seat_number)
    if state.status is DraftStatus.COMPLETED:
        raise DraftTransitionError("draft is completed")
    if state.active_seat != seat_number:
        raise DraftTransitionError("seat is not active for the current pick")


def _require_seat_number(state: DraftState, seat_number: int) -> None:
    if not isinstance(seat_number, int) or isinstance(seat_number, bool):
        raise DraftTransitionError("seat_number must be an integer")
    if not 0 <= seat_number < state.draft.configuration.seats:
        raise DraftTransitionError("seat_number is outside the draft geometry")


def _validate_allocation(draft: Draft, allocation: tuple[AllocatedPack, ...]) -> None:
    configuration = draft.configuration
    expected_pack_count = configuration.seats * configuration.packs_per_seat
    if len(allocation) != expected_pack_count:
        raise ValueError("allocation must contain exactly one pack for each draft pack")
    expected_numbers = tuple(range(expected_pack_count))
    if tuple(allocated.pack.pack_number for allocated in allocation) != expected_numbers:
        raise ValueError("allocation packs must be ordered by contiguous pack number")
    if any(allocated.pack.draft_id != draft.id for allocated in allocation):
        raise ValueError("allocation packs must belong to the draft")
    if any(
        allocated.pack.owner_seat != allocated.pack.pack_number % configuration.seats
        for allocated in allocation
    ):
        raise ValueError("allocation pack owners must match the draft geometry")
    if any(len(allocated.cards) != configuration.pack_size for allocated in allocation):
        raise ValueError("allocation packs must match the configured pack size")
    instance_ids = tuple(card.id for allocated in allocation for card in allocated.cards)
    if len(instance_ids) != len(set(instance_ids)):
        raise ValueError("allocation cannot contain duplicate draft-card instance IDs")


def _validate_pick_events(
    draft: Draft, allocation: tuple[AllocatedPack, ...], events: tuple[PickEvent, ...]
) -> tuple[int, int, int, tuple[ActiveDraftPack, ...]]:
    allocation_ids = {card.id for allocated in allocation for card in allocated.cards}
    if any(event.draft_id != draft.id for event in events):
        raise ValueError("pick events must belong to the draft")
    if tuple(event.sequence for event in events) != tuple(range(len(events))):
        raise ValueError("pick event sequences must be contiguous and ordered")
    event_ids = tuple(event.card_instance_id for event in events)
    if any(card_id not in allocation_ids for card_id in event_ids):
        raise ValueError("pick events must reference allocated card instances")
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("a draft-card instance cannot be picked twice")
    if any(not 0 <= event.seat_number < draft.configuration.seats for event in events):
        raise ValueError("pick event seats must match the draft geometry")
    return _validate_legal_event_sequence(draft, allocation, events)


def _validate_legal_event_sequence(
    draft: Draft, allocation: tuple[AllocatedPack, ...], events: tuple[PickEvent, ...]
) -> tuple[int, int, int, tuple[ActiveDraftPack, ...]]:
    """Replay the command schedule so direct construction cannot forge history."""

    pack_round = 0
    pick_number = 0
    active_seat = 0
    active_packs = _active_packs_for_round(draft, allocation, pack_round)
    for event in events:
        active_pack = active_packs[active_seat]
        if event.seat_number != active_seat:
            raise ValueError("pick event seat does not match the legal turn")
        if event.pick_number != pick_number:
            raise ValueError("pick event number does not match the legal turn")
        if event.pack_number != active_pack.pack.pack_number:
            raise ValueError("pick event pack does not match the current active pack")
        if not any(card.id == event.card_instance_id for card in active_pack.cards):
            raise ValueError("pick event card is not available in the current active pack")
        updated_packs = list(active_packs)
        updated_packs[active_seat] = ActiveDraftPack(
            active_pack.pack,
            tuple(card for card in active_pack.cards if card.id != event.card_instance_id),
        )
        active_packs = tuple(updated_packs)
        if active_seat + 1 < draft.configuration.seats:
            active_seat += 1
            continue
        if not all(not pack.cards for pack in active_packs):
            active_packs = _rotate_packs(active_packs, pack_round)
            pick_number += 1
            active_seat = 0
            continue
        pack_round += 1
        if pack_round == draft.configuration.packs_per_seat:
            if event is not events[-1]:
                raise ValueError("pick events continue after the draft is complete")
            continue
        pick_number = 0
        active_seat = 0
        active_packs = _active_packs_for_round(draft, allocation, pack_round)
    return pack_round, pick_number, active_seat, active_packs
