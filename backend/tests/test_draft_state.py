from dataclasses import FrozenInstanceError

import pytest

from cubeai.lab.domain import (
    ActorOrigin,
    AllocatedPack,
    Draft,
    DraftCardInstance,
    DraftConfiguration,
    DraftPack,
    DraftState,
    DraftStatus,
    DraftTransitionError,
    PickEvent,
    available_cards,
    pick_card,
    pool_for_seat,
    start_draft,
)


def _allocation(
    draft_id: str, configuration: DraftConfiguration
) -> tuple[AllocatedPack, ...]:
    return tuple(
        AllocatedPack(
            DraftPack(draft_id, pack_number, pack_number % configuration.seats),
            tuple(
                DraftCardInstance(
                    f"{draft_id}:card:{pack_number}:{card_number}",
                    draft_id,
                    f"membership:{pack_number}:{card_number}",
                )
                for card_number in range(configuration.pack_size)
            ),
        )
        for pack_number in range(configuration.seats * configuration.packs_per_seat)
    )


def _draft_state(
    *, seats: int = 2, packs_per_seat: int = 1, pack_size: int = 2
) -> DraftState:
    configuration = DraftConfiguration(seats, packs_per_seat, pack_size, seed=17)
    draft = Draft("draft-1", "cube-version-1", configuration)
    return start_draft(draft, _allocation(draft.id, configuration))


def _complete_with_first_legal_card(state: DraftState) -> DraftState:
    while state.status is not DraftStatus.COMPLETED:
        assert state.active_seat is not None
        cards = available_cards(state, state.active_seat)
        state = pick_card(state, state.active_seat, cards[0].id)
    return state


def test_two_seat_golden_passes_left_then_completes_with_conserved_instances() -> None:
    state = _draft_state()

    state = pick_card(state, 0, "draft-1:card:0:0")
    state = pick_card(state, 1, "draft-1:card:1:0")

    assert state.active_seat == 0
    assert state.pick_number == 1
    assert [card.id for card in available_cards(state, 0)] == ["draft-1:card:1:1"]
    assert [card.id for card in state.active_packs[1].cards] == ["draft-1:card:0:1"]

    completed = _complete_with_first_legal_card(state)
    assert completed.status is DraftStatus.COMPLETED
    assert completed.active_seat is None
    assert completed.active_packs == ()
    assert [event.card_instance_id for event in completed.pick_events] == [
        "draft-1:card:0:0",
        "draft-1:card:1:0",
        "draft-1:card:1:1",
        "draft-1:card:0:1",
    ]
    allocated_ids = {
        card.id for pack in completed.allocation for card in pack.cards
    }
    picked_ids = {event.card_instance_id for event in completed.pick_events}
    assert picked_ids == allocated_ids
    assert len(completed.pick_events) == len(picked_ids)


def test_three_seat_two_pack_golden_alternates_left_then_right_by_pack_round() -> None:
    state = _draft_state(seats=3, packs_per_seat=2)

    state = pick_card(state, 0, "draft-1:card:0:0")
    state = pick_card(state, 1, "draft-1:card:1:0")
    state = pick_card(state, 2, "draft-1:card:2:0")
    assert [pack.pack.pack_number for pack in state.active_packs] == [1, 2, 0]
    state = _complete_with_first_legal_card(state)

    assert [event.pack_number for event in state.pick_events] == [
        0,
        1,
        2,
        1,
        2,
        0,
        3,
        4,
        5,
        5,
        3,
        4,
    ]
    assert state.status is DraftStatus.COMPLETED


def test_eight_seat_golden_scenario_uses_one_legal_pick_per_active_seat() -> None:
    state = _draft_state(seats=8, pack_size=1)
    completed = _complete_with_first_legal_card(state)

    assert [event.seat_number for event in completed.pick_events] == list(range(8))
    assert [event.pack_number for event in completed.pick_events] == list(range(8))
    assert [event.sequence for event in completed.pick_events] == list(range(8))


def test_stale_wrong_seat_and_unknown_card_commands_leave_state_unchanged() -> None:
    state = _draft_state()
    before = state

    with pytest.raises(DraftTransitionError, match="not active"):
        pick_card(state, 1, "draft-1:card:1:0")
    with pytest.raises(DraftTransitionError, match="not available"):
        pick_card(state, 0, "missing")

    assert state == before


def test_only_active_seat_can_view_its_current_pack() -> None:
    state = _draft_state()

    with pytest.raises(DraftTransitionError, match="not active"):
        available_cards(state, 1)

    assert [card.id for card in available_cards(state, 0)] == [
        "draft-1:card:0:0",
        "draft-1:card:0:1",
    ]


def test_pools_are_derived_from_immutable_event_history() -> None:
    completed = _complete_with_first_legal_card(_draft_state())

    assert pool_for_seat(completed, 0).card_instance_ids == (
        "draft-1:card:0:0",
        "draft-1:card:1:1",
    )
    assert pool_for_seat(completed, 1).card_instance_ids == (
        "draft-1:card:1:0",
        "draft-1:card:0:1",
    )
    with pytest.raises(FrozenInstanceError):
        completed.pick_events = ()  # type: ignore[misc]


def test_completed_draft_rejects_new_or_stale_commands() -> None:
    completed = _complete_with_first_legal_card(_draft_state())

    with pytest.raises(DraftTransitionError, match="completed"):
        available_cards(completed, 0)
    with pytest.raises(DraftTransitionError, match="completed"):
        pick_card(completed, 0, "draft-1:card:0:0")


@pytest.mark.parametrize("broken", ["wrong_count", "wrong_size", "duplicate_instance"])
def test_start_rejects_invalid_allocation_geometry_or_identity(broken: str) -> None:
    configuration = DraftConfiguration(2, 1, 2, seed=17)
    draft = Draft("draft-1", "cube-version-1", configuration)
    allocation = list(_allocation(draft.id, configuration))
    if broken == "wrong_count":
        allocation.pop()
    elif broken == "wrong_size":
        allocation[0] = AllocatedPack(allocation[0].pack, allocation[0].cards[:1])
    else:
        duplicate = allocation[0].cards[0]
        allocation[1] = AllocatedPack(
            allocation[1].pack,
            (duplicate, allocation[1].cards[1]),
        )

    with pytest.raises(ValueError):
        start_draft(draft, tuple(allocation))


def test_replay_with_the_same_legal_choices_is_identical() -> None:
    first = _complete_with_first_legal_card(_draft_state(packs_per_seat=2))
    second = _complete_with_first_legal_card(_draft_state(packs_per_seat=2))

    assert first == second


def test_constructor_rejects_a_forged_completed_history() -> None:
    configuration = DraftConfiguration(2, 1, 2, seed=17)
    draft = Draft("draft-1", "cube-version-1", configuration)
    allocation = _allocation(draft.id, configuration)
    forged_events = tuple(
        PickEvent(
            draft.id,
            sequence,
            0,
            0,
            0,
            card.id,
            actor_origin=ActorOrigin.HUMAN,
            actor_id="seat:0",
        )
        for sequence, card in enumerate(
            card for pack in allocation for card in pack.cards
        )
    )

    with pytest.raises(ValueError, match="legal turn"):
        DraftState(
            draft,
            allocation,
            pack_round=1,
            pick_number=2,
            active_seat=None,
            active_packs=(),
            pick_events=forged_events,
            status=DraftStatus.COMPLETED,
        )


def test_constructor_rejects_forged_in_progress_pack_positions() -> None:
    state = _draft_state()
    state = pick_card(state, 0, "draft-1:card:0:0")
    state = pick_card(state, 1, "draft-1:card:1:0")

    with pytest.raises(ValueError, match="legal event history"):
        DraftState(
            state.draft,
            state.allocation,
            state.pack_round,
            state.pick_number,
            state.active_seat,
            tuple(reversed(state.active_packs)),
            state.pick_events,
        )
