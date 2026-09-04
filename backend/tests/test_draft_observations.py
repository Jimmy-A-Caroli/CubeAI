import pytest

from cubeai.lab.application import derive_draft_observations
from cubeai.lab.domain import (
    ActorOrigin,
    AllocatedPack,
    BotDecisionProvenance,
    BotTieBreakReason,
    Draft,
    DraftCardInstance,
    DraftConfiguration,
    DraftPack,
    RatingLookupOutcome,
    available_cards,
    pick_card,
    start_draft,
)


def _state():
    draft = Draft("observation-draft", "cube-version-1", DraftConfiguration(2, 1, 2, 7))
    allocation = (
        AllocatedPack(
            DraftPack(draft.id, 0, 0),
            (
                DraftCardInstance("instance-a", draft.id, "membership-duplicate-a"),
                DraftCardInstance("instance-b", draft.id, "membership-duplicate-b"),
            ),
        ),
        AllocatedPack(
            DraftPack(draft.id, 1, 1),
            (
                DraftCardInstance("instance-c", draft.id, "membership-c"),
                DraftCardInstance("instance-d", draft.id, "membership-d"),
            ),
        ),
    )
    state = start_draft(draft, allocation)
    state = pick_card(state, 0, "instance-a")
    state = pick_card(
        state,
        1,
        "instance-c",
        actor_origin=ActorOrigin.BOT,
        actor_id="seat:1",
        strategy_ref="raw-ranking-v0@1",
        bot_provenance=BotDecisionProvenance(
            "raw-ranking-v0",
            "1",
            "cubeai-raw-ranking-v0",
            "1",
            8.2,
            RatingLookupOutcome.RATED,
            BotTieBreakReason.HIGHEST_RATING,
        ),
    )
    state = pick_card(state, 0, available_cards(state, 0)[0].id)
    return pick_card(state, 1, available_cards(state, 1)[0].id)


def test_replays_chronological_cards_seen_pools_and_actor_provenance() -> None:
    state = _state()

    observations = derive_draft_observations(state)

    assert [item.event.sequence for item in observations] == [0, 1, 2, 3]
    assert [item.event.card_instance_id for item in observations] == [
        "instance-a",
        "instance-c",
        "instance-d",
        "instance-b",
    ]
    assert [card.id for card in observations[0].cards_seen] == [
        "instance-a",
        "instance-b",
    ]
    assert [card.cube_card_id for card in observations[0].cards_seen] == [
        "membership-duplicate-a",
        "membership-duplicate-b",
    ]
    assert observations[0].chosen_card.id == "instance-a"
    assert observations[0].pool_before == ()
    assert [card.id for card in observations[2].pool_before] == ["instance-a"]
    assert all(
        item.event.card_instance_id in {card.id for card in item.cards_seen}
        for item in observations
    )
    assert observations[0].event.actor_origin is ActorOrigin.HUMAN
    assert observations[0].event.bot_provenance is None
    assert observations[1].event.actor_origin is ActorOrigin.BOT
    assert observations[1].event.bot_provenance is not None
    assert observations[1].event.bot_provenance.selected_rating == 8.2


def test_projection_is_deterministic_and_does_not_mutate_state() -> None:
    state = _state()
    before = state

    first = derive_draft_observations(state)
    second = derive_draft_observations(state)

    assert first == second
    assert state == before


def test_projection_rejects_a_non_draft_state() -> None:
    with pytest.raises(ValueError, match="DraftState"):
        derive_draft_observations(object())  # type: ignore[arg-type]
