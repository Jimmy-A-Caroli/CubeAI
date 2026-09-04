import pytest

from cubeai.lab.application import (
    DraftDecisionObservation,
    derive_draft_observations,
    derive_wheel_observations,
)
from cubeai.lab.domain import (
    ActorOrigin,
    AllocatedPack,
    Draft,
    DraftCardInstance,
    DraftConfiguration,
    DraftPack,
    PickEvent,
    available_cards,
    pick_card,
    start_draft,
)


def _completed_state(*, seats: int = 2, packs_per_seat: int = 1, pack_size: int = 3):
    draft = Draft(
        "wheel-draft",
        "cube-version-1",
        DraftConfiguration(seats, packs_per_seat, pack_size, 17),
    )
    allocation = tuple(
        AllocatedPack(
            DraftPack(draft.id, pack_number, pack_number % seats),
            tuple(
                DraftCardInstance(
                    f"{draft.id}:card:{pack_number}:{card_number}",
                    draft.id,
                    f"membership:{pack_number}:{card_number}",
                )
                for card_number in range(pack_size)
            ),
        )
        for pack_number in range(seats * packs_per_seat)
    )
    state = start_draft(draft, allocation)
    while state.active_seat is not None:
        state = pick_card(
            state,
            state.active_seat,
            available_cards(state, state.active_seat)[0].id,
        )
    return state


def _observation(
    *,
    sequence: int,
    seat: int,
    cards: tuple[DraftCardInstance, ...],
    chosen: DraftCardInstance,
    draft_id: str = "wheel-draft",
) -> DraftDecisionObservation:
    return DraftDecisionObservation(
        PickEvent(
            draft_id,
            sequence,
            seat,
            0,
            sequence,
            chosen.id,
            ActorOrigin.HUMAN,
            f"seat:{seat}",
        ),
        chosen,
        cards,
        (),
    )


def test_detects_one_instance_return_after_the_seat_passes_it() -> None:
    observations = derive_draft_observations(_completed_state())

    wheels = derive_wheel_observations(observations)

    assert [(wheel.seat_number, wheel.card_instance_id) for wheel in wheels] == [
        (0, "wheel-draft:card:0:2"),
        (1, "wheel-draft:card:1:2"),
    ]
    first = wheels[0]
    assert first.draft_id == "wheel-draft"
    assert (first.first_seen_sequence, first.returned_sequence) == (0, 4)
    assert first.first_seen_pack_number == first.returned_pack_number == 0
    assert first.first_seen_pick_number == 0
    assert first.returned_pick_number == 2


def test_uses_observations_for_alternating_directions_without_topology_rules() -> None:
    observations = derive_draft_observations(
        _completed_state(seats=3, packs_per_seat=2, pack_size=4)
    )

    wheels = derive_wheel_observations(observations)

    assert len(wheels) == 6
    assert {(wheel.seat_number, wheel.returned_pack_number) for wheel in wheels} == {
        (0, 0),
        (1, 1),
        (2, 2),
        (0, 3),
        (1, 4),
        (2, 5),
    }


def test_selected_or_once_seen_instances_do_not_false_wheel() -> None:
    observations = derive_draft_observations(_completed_state())

    wheels = derive_wheel_observations(observations)

    wheel_ids = {wheel.card_instance_id for wheel in wheels}
    assert "wheel-draft:card:0:0" not in wheel_ids
    assert "wheel-draft:card:0:1" not in wheel_ids


def test_distinct_instances_are_not_collapsed_by_shared_logical_identity() -> None:
    shared_a = DraftCardInstance("instance-a", "wheel-draft", "membership-shared")
    shared_b = DraftCardInstance("instance-b", "wheel-draft", "membership-shared")
    other_a = DraftCardInstance("instance-c", "wheel-draft", "membership-c")
    other_b = DraftCardInstance("instance-d", "wheel-draft", "membership-d")

    wheels = derive_wheel_observations(
        (
            _observation(
                sequence=0,
                seat=0,
                cards=(shared_a, other_a),
                chosen=other_a,
            ),
            _observation(
                sequence=1,
                seat=0,
                cards=(shared_b, other_b),
                chosen=other_b,
            ),
        )
    )

    assert wheels == ()


def test_same_instance_id_from_a_different_draft_is_not_a_return() -> None:
    first = DraftCardInstance("shared-instance", "draft-one", "membership-a")
    later = DraftCardInstance("shared-instance", "draft-two", "membership-a")
    choice_one = DraftCardInstance("choice-one", "draft-one", "membership-b")
    choice_two = DraftCardInstance("choice-two", "draft-one", "membership-c")
    choice_three = DraftCardInstance("choice-three", "draft-two", "membership-d")

    wheels = derive_wheel_observations(
        (
            _observation(
                sequence=0,
                seat=0,
                cards=(first, choice_one),
                chosen=choice_one,
                draft_id="draft-one",
            ),
            _observation(
                sequence=1,
                seat=0,
                cards=(choice_two,),
                chosen=choice_two,
                draft_id="draft-one",
            ),
            _observation(
                sequence=2,
                seat=0,
                cards=(later, choice_three),
                chosen=choice_three,
                draft_id="draft-two",
            ),
        )
    )

    assert wheels == ()


def test_emits_only_the_first_return_for_an_instance_and_keeps_seats_separate() -> None:
    observations = derive_draft_observations(_completed_state(pack_size=5))

    wheels = derive_wheel_observations(observations)

    assert len(wheels) == 10
    assert len({(wheel.seat_number, wheel.card_instance_id) for wheel in wheels}) == 10
    assert {(wheel.seat_number, wheel.returned_pack_number) for wheel in wheels} == {
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    }


def test_is_deterministic_immutable_and_rejects_unordered_input() -> None:
    state = _completed_state()
    observations = derive_draft_observations(state)
    before = observations

    first = derive_wheel_observations(observations)
    second = derive_wheel_observations(observations)

    assert first == second
    assert observations == before
    with pytest.raises(ValueError, match="strictly increasing"):
        derive_wheel_observations((observations[1], observations[0]))
