from fractions import Fraction

import pytest

from cubeai.lab.application import (
    BotActorScope,
    CombinedActorScope,
    HumanActorScope,
    MetricId,
    derive_draft_metrics,
)
from cubeai.lab.domain import (
    ActorOrigin,
    AllocatedPack,
    BotDecisionProvenance,
    BotTieBreakReason,
    Draft,
    DraftCardInstance,
    DraftConfiguration,
    DraftPack,
    DraftStatus,
    RatingLookupOutcome,
    available_cards,
    pick_card,
    start_draft,
)


def _provenance(strategy_id: str, version: str) -> BotDecisionProvenance:
    return BotDecisionProvenance(
        strategy_id,
        version,
        f"artifact:{strategy_id}",
        version,
        1.0,
        RatingLookupOutcome.RATED,
        BotTieBreakReason.HIGHEST_RATING,
    )


def _pick_bot(state, card_id: str, strategy_id: str, version: str):
    assert state.active_seat is not None
    return pick_card(
        state,
        state.active_seat,
        card_id,
        actor_origin=ActorOrigin.BOT,
        actor_id=f"seat:{state.active_seat}",
        strategy_ref=f"{strategy_id}@{version}",
        bot_provenance=_provenance(strategy_id, version),
    )


def _two_seat_completed(
    *, draft_id: str = "metrics-draft", cube_version_id: str = "cube-version-1"
):
    draft = Draft(draft_id, cube_version_id, DraftConfiguration(2, 1, 3, 7))
    allocation = tuple(
        AllocatedPack(
            DraftPack(draft.id, pack_number, pack_number),
            tuple(
                DraftCardInstance(
                    f"{draft.id}:{pack_number}:{card_number}",
                    draft.id,
                    f"membership:{pack_number}:{card_number}",
                )
                for card_number in range(3)
            ),
        )
        for pack_number in range(2)
    )
    state = start_draft(draft, allocation)
    state = pick_card(state, 0, f"{draft.id}:0:1")
    state = _pick_bot(state, f"{draft.id}:1:0", "strategy-a", "1")
    state = pick_card(state, 0, f"{draft.id}:1:1")
    state = _pick_bot(state, f"{draft.id}:0:2", "strategy-b", "2")
    state = pick_card(state, 0, f"{draft.id}:0:0")
    state = _pick_bot(state, f"{draft.id}:1:2", "strategy-b", "2")
    assert state.status is DraftStatus.COMPLETED
    return state


def _standard_completed():
    draft = Draft("standard-draft", "cube-version-1", DraftConfiguration(1, 1, 15, 3))
    allocation = (
        AllocatedPack(
            DraftPack(draft.id, 0, 0),
            tuple(
                DraftCardInstance(f"standard:{index}", draft.id, f"membership:{index}")
                for index in range(15)
            ),
        ),
    )
    state = start_draft(draft, allocation)
    while state.status is not DraftStatus.COMPLETED:
        assert state.active_seat is not None
        state = pick_card(
            state, state.active_seat, available_cards(state, state.active_seat)[0].id
        )
    return state


def _eight_by_three_by_fifteen_completed():
    draft = Draft(
        "eight-by-three-by-fifteen",
        "cube-version-1",
        DraftConfiguration(8, 3, 15, 13),
    )
    allocation = tuple(
        AllocatedPack(
            DraftPack(draft.id, pack_number, pack_number % 8),
            tuple(
                DraftCardInstance(
                    f"{draft.id}:{pack_number}:{card_number}",
                    draft.id,
                    f"membership:{pack_number}:{card_number}",
                )
                for card_number in range(15)
            ),
        )
        for pack_number in range(24)
    )
    state = start_draft(draft, allocation)
    while state.status is not DraftStatus.COMPLETED:
        assert state.active_seat is not None
        state = pick_card(
            state, state.active_seat, available_cards(state, state.active_seat)[0].id
        )
    return state


def _repeated_return_completed():
    """Make one exact instance appear, leave, return, leave, return, and be picked."""

    draft = Draft("repeated-return", "cube-version-1", DraftConfiguration(2, 1, 5, 11))
    allocation = tuple(
        AllocatedPack(
            DraftPack(draft.id, pack_number, pack_number),
            tuple(
                DraftCardInstance(
                    f"{draft.id}:{pack_number}:{card_number}",
                    draft.id,
                    f"membership:{pack_number}:{card_number}",
                )
                for card_number in range(5)
            ),
        )
        for pack_number in range(2)
    )
    state = start_draft(draft, allocation)
    state = pick_card(state, 0, f"{draft.id}:0:1")
    state = _pick_bot(state, f"{draft.id}:1:0", "strategy-a", "1")
    state = pick_card(state, 0, f"{draft.id}:1:1")
    state = _pick_bot(state, f"{draft.id}:0:2", "strategy-a", "1")
    state = pick_card(state, 0, f"{draft.id}:0:3")
    state = _pick_bot(state, f"{draft.id}:1:2", "strategy-a", "1")
    state = pick_card(state, 0, f"{draft.id}:1:3")
    state = _pick_bot(state, f"{draft.id}:0:4", "strategy-a", "1")
    state = pick_card(state, 0, f"{draft.id}:0:0")
    state = _pick_bot(state, f"{draft.id}:1:4", "strategy-a", "1")
    assert state.status is DraftStatus.COMPLETED
    return state


def _rate(results, membership_id: str, metric_id: MetricId):
    return next(
        metric
        for metric in results.rate_metrics
        if metric.membership_id == membership_id and metric.metric_id is metric_id
    )


def _position(results, membership_id: str, metric_id: MetricId):
    return next(
        metric
        for metric in results.position_metrics
        if metric.membership_id == membership_id and metric.metric_id is metric_id
    )


def test_human_membership_metrics_use_observed_opportunities_and_wheel_facts() -> None:
    results = derive_draft_metrics((_two_seat_completed(),), HumanActorScope())
    membership = "membership:0:0"

    pick_rate = _rate(results, membership, MetricId.PICK_RATE)
    assert (pick_rate.value, pick_rate.numerator, pick_rate.denominator) == (
        Fraction(1, 2),
        1,
        2,
    )
    assert (_rate(results, membership, MetricId.FIRST_PICK_RATE).value,) == (
        Fraction(0, 1),
    )
    assert (_rate(results, membership, MetricId.LAST_PICK_RATE).value,) == (
        Fraction(1, 1),
    )
    second_last = _rate(results, membership, MetricId.SECOND_TO_LAST_PICK_RATE)
    assert (second_last.value, second_last.numerator, second_last.denominator) == (
        None,
        0,
        0,
    )
    wheel = _rate(results, membership, MetricId.WHEEL_RETURN_RATE)
    assert (wheel.value, wheel.numerator, wheel.denominator) == (Fraction(1, 1), 1, 1)
    no_return = _rate(results, "membership:0:2", MetricId.WHEEL_RETURN_RATE)
    assert (no_return.value, no_return.numerator, no_return.denominator) == (
        Fraction(0, 1),
        0,
        1,
    )
    no_opportunity = _rate(results, "membership:0:1", MetricId.WHEEL_RETURN_RATE)
    assert (
        no_opportunity.value,
        no_opportunity.numerator,
        no_opportunity.denominator,
    ) == (
        None,
        0,
        0,
    )
    assert _position(results, membership, MetricId.MEAN_PICK).value == Fraction(3, 1)
    assert _position(results, membership, MetricId.MEDIAN_PICK).value == Fraction(3, 1)

    assert results.seen_before_pick.n == 3
    sample = next(
        item
        for item in results.seen_before_pick.samples
        if item.membership_id == membership
    )
    assert (
        sample.prior_appearances,
        sample.round_number,
        sample.pick_number,
        sample.cards_available_before_pick,
    ) == (1, 1, 3, 1)
    assert results.context.completed_draft_ids == ("metrics-draft",)
    assert results.context.cube_version_id == "cube-version-1"
    assert results.context.configuration.pack_size == 3
    assert results.context.completion_scope == "completed-drafts-only"
    assert results.context.provenance.calculation_version == "m2-009-v1"
    assert results.context.provenance.observation_basis == "M2-001"
    assert results.context.provenance.wheel_basis == "M2-002"

    # These membership IDs represent separate Cube slots. Their facts are not
    # coalesced merely because a future source may identify the cards alike.
    assert _rate(results, "membership:0:0", MetricId.PICK_RATE).membership_id != (
        _rate(results, "membership:0:1", MetricId.PICK_RATE).membership_id
    )


def test_seen_before_pick_counts_only_prior_sightings_of_the_same_instance() -> None:
    results = derive_draft_metrics((_repeated_return_completed(),), HumanActorScope())

    repeated = next(
        sample
        for sample in results.seen_before_pick.samples
        if sample.card_instance_id == "repeated-return:0:0"
    )
    first_sight = next(
        sample
        for sample in results.seen_before_pick.samples
        if sample.card_instance_id == "repeated-return:0:1"
    )
    assert repeated.prior_appearances == 2
    assert first_sight.prior_appearances == 0


def test_wheel_opportunity_first_sighting_is_not_redefined_by_actor_filter() -> None:
    draft = Draft("actor-change", "cube-version-1", DraftConfiguration(2, 1, 3, 5))
    allocation = tuple(
        AllocatedPack(
            DraftPack(draft.id, pack_number, pack_number),
            tuple(
                DraftCardInstance(
                    f"{draft.id}:{pack_number}:{card_number}",
                    draft.id,
                    f"membership:{pack_number}:{card_number}",
                )
                for card_number in range(3)
            ),
        )
        for pack_number in range(2)
    )
    state = start_draft(draft, allocation)
    state = pick_card(state, 0, "actor-change:0:1")
    state = _pick_bot(state, "actor-change:1:0", "strategy-b", "1")
    state = _pick_bot(state, "actor-change:1:1", "strategy-a", "1")
    state = _pick_bot(state, "actor-change:0:2", "strategy-b", "1")
    state = _pick_bot(state, "actor-change:0:0", "strategy-a", "1")
    state = _pick_bot(state, "actor-change:1:2", "strategy-b", "1")

    results = derive_draft_metrics((state,), BotActorScope("strategy-a", "1"))
    wheel = _rate(results, "membership:0:0", MetricId.WHEEL_RETURN_RATE)

    assert state.status is DraftStatus.COMPLETED
    assert (wheel.value, wheel.numerator, wheel.denominator) == (None, 0, 0)


def test_actor_scopes_do_not_mix_human_or_bot_strategies_without_combined_scope() -> (
    None
):
    state = _two_seat_completed()
    human = derive_draft_metrics((state,), HumanActorScope())
    bot_a = derive_draft_metrics((state,), BotActorScope("strategy-a", "1"))
    bot_b = derive_draft_metrics((state,), BotActorScope("strategy-b", "2"))
    combined = derive_draft_metrics(
        (state,),
        CombinedActorScope(
            (
                HumanActorScope(),
                BotActorScope("strategy-a", "1"),
                BotActorScope("strategy-b", "2"),
            )
        ),
    )

    assert _rate(human, "membership:0:1", MetricId.PICK_RATE).numerator == 1
    assert _rate(bot_a, "membership:1:0", MetricId.PICK_RATE).numerator == 1
    assert _rate(bot_a, "membership:0:2", MetricId.PICK_RATE).numerator == 0
    assert _rate(bot_b, "membership:0:2", MetricId.PICK_RATE).numerator == 1
    assert combined.seen_before_pick.n == 6
    assert isinstance(combined.context.actor_scope, CombinedActorScope)


def test_standard_pick_positions_and_nonstandard_late_categories_are_geometric() -> (
    None
):
    standard = derive_draft_metrics((_standard_completed(),), HumanActorScope())
    positions = sorted(
        metric.value
        for metric in standard.position_metrics
        if metric.metric_id is MetricId.MEAN_PICK
    )
    assert positions == [Fraction(value, 1) for value in range(1, 16)]

    nonstandard = derive_draft_metrics((_two_seat_completed(),), HumanActorScope())
    assert (
        _rate(nonstandard, "membership:0:0", MetricId.LAST_PICK_RATE).denominator == 1
    )
    assert (
        _rate(
            nonstandard, "membership:0:1", MetricId.SECOND_TO_LAST_PICK_RATE
        ).denominator
        == 0
    )


def test_eight_by_three_by_fifteen_reference_has_all_local_human_positions() -> None:
    results = derive_draft_metrics(
        (_eight_by_three_by_fifteen_completed(),), HumanActorScope()
    )

    assert results.context.configuration.seats == 8
    assert results.context.configuration.packs_per_seat == 3
    assert results.context.configuration.pack_size == 15
    assert results.seen_before_pick.n == 45
    assert sorted(
        sample.pick_number for sample in results.seen_before_pick.samples
    ) == ([pick for pick in range(1, 16) for _round in range(3)])
    assert sorted(
        sample.round_number for sample in results.seen_before_pick.samples
    ) == ([round_number for round_number in range(1, 4) for _pick in range(15)])


def test_completed_population_is_separated_by_cube_version_and_excludes_incomplete() -> (
    None
):
    completed = _two_seat_completed()
    other_version = _two_seat_completed(
        draft_id="other-version-draft", cube_version_id="cube-version-2"
    )
    incomplete_draft = Draft(
        "incomplete-draft", "cube-version-2", DraftConfiguration(2, 1, 3, 9)
    )
    incomplete = start_draft(
        incomplete_draft,
        tuple(
            AllocatedPack(
                DraftPack(incomplete_draft.id, pack_number, pack_number),
                tuple(
                    DraftCardInstance(
                        f"incomplete:{pack_number}:{card_number}",
                        incomplete_draft.id,
                        f"incomplete-membership:{pack_number}:{card_number}",
                    )
                    for card_number in range(3)
                ),
            )
            for pack_number in range(2)
        ),
    )
    incomplete = pick_card(incomplete, 0, "incomplete:0:1")
    assert incomplete.status is DraftStatus.IN_PROGRESS

    results = derive_draft_metrics((completed, incomplete), HumanActorScope())
    assert results.context.completed_draft_ids == ("metrics-draft",)
    with pytest.raises(ValueError, match="CubeVersions"):
        derive_draft_metrics((completed, other_version), HumanActorScope())
    with pytest.raises(ValueError, match="completed draft"):
        derive_draft_metrics((incomplete,), HumanActorScope())
