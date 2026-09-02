from dataclasses import FrozenInstanceError

import pytest

from cubeai.lab.domain import (
    ActorOrigin,
    Draft,
    DraftCardInstance,
    DraftConfiguration,
    DraftPack,
    DraftPool,
    DraftSeat,
    DraftStatus,
    PickEvent,
)


def test_configuration_is_generic_and_computes_required_cards() -> None:
    config = DraftConfiguration(seats=8, packs_per_seat=3, pack_size=15, seed=20260828)
    assert config.card_count == 360
    assert (
        DraftConfiguration(seats=2, packs_per_seat=1, pack_size=3, seed=1).card_count
        == 6
    )


@pytest.mark.parametrize("field", ["seats", "packs_per_seat", "pack_size"])
def test_configuration_rejects_nonpositive_geometry(field: str) -> None:
    values = {"seats": 2, "packs_per_seat": 1, "pack_size": 3, "seed": 1}
    values[field] = 0
    with pytest.raises(ValueError, match=field):
        DraftConfiguration(**values)


def test_configuration_rejects_boolean_seed_and_geometry() -> None:
    with pytest.raises(ValueError, match="seed"):
        DraftConfiguration(2, 1, 3, True)
    with pytest.raises(ValueError, match="seats"):
        DraftConfiguration(True, 1, 3, 1)


def test_identity_scopes_and_duplicate_memberships_remain_distinct() -> None:
    first = DraftCardInstance("instance-1", "draft-1", "cube-membership-a")
    second = DraftCardInstance("instance-2", "draft-1", "cube-membership-a")
    assert first != second
    assert first.cube_card_id == second.cube_card_id
    assert DraftSeat("draft-1", 0) != DraftSeat("draft-1", 1)
    assert DraftPack("draft-1", 0, 0) != DraftPack("draft-1", 1, 0)


def test_pick_event_carries_actor_provenance_without_transition_logic() -> None:
    event = PickEvent(
        "draft-1", 0, 1, 0, 0, "instance-1", ActorOrigin.BOT, "seat-1", "bot-v0"
    )
    assert event.actor_origin is ActorOrigin.BOT
    assert event.strategy_ref == "bot-v0"
    assert (
        Draft("draft-1", "cube-version-1", DraftConfiguration(2, 1, 3, 1)).status
        is DraftStatus.CREATED
    )


def test_immutable_values_and_pool_identity() -> None:
    pool = DraftPool("draft-1", 0, ["instance-1", "instance-2"])
    assert pool.card_instance_ids == ("instance-1", "instance-2")
    with pytest.raises(FrozenInstanceError):
        pool.seat_number = 2  # type: ignore[misc]
    with pytest.raises(ValueError, match="unique"):
        DraftPool("draft-1", 0, ["instance-1", "instance-1"])


def test_invalid_identity_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="cube_card_id"):
        DraftCardInstance("instance-1", "draft-1", "")
    with pytest.raises(ValueError, match="actor_origin"):
        PickEvent("draft-1", 0, 0, 0, 0, "instance-1", "bot", "actor")  # type: ignore[arg-type]
