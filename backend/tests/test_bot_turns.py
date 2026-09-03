from dataclasses import dataclass, field

import pytest

from cubeai.lab.application import BotTurnError, advance_bot_turns
from cubeai.lab.domain import (
    ActorOrigin,
    BotDecisionProvenance,
    BotPickDecision,
    BotTieBreakReason,
    BotVisibleState,
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    Draft,
    DraftConfiguration,
    DraftStatus,
    DraftTransitionError,
    RatingArtifact,
    RatingEntry,
    RatingLookupOutcome,
    RawRankingStrategyV0,
    ResolutionStatus,
    allocate_packs,
    available_cards,
    pick_card,
    start_draft,
    validate_cube_version,
)


def _version(size: int) -> CubeVersion:
    return CubeVersion(
        "version-1",
        Cube("cube-1", "Synthetic Cube"),
        tuple(
            CubeCard(
                f"membership-{index}",
                ResolutionStatus.RESOLVED,
                CardPrinting(
                    f"printing-{index}",
                    CardIdentity(
                        f"oracle-{index}",
                        f"Synthetic {index}",
                        ResolutionStatus.RESOLVED,
                        f"oracle-{index}",
                    ),
                ),
            )
            for index in range(size)
        ),
    )


def _state(configuration: DraftConfiguration):
    version = _version(configuration.card_count)
    draft = Draft("draft-1", version.id, configuration)
    return start_draft(
        draft,
        allocate_packs(
            "draft-1", version, validate_cube_version(version, configuration)
        ),
    ), version


def _strategy() -> RawRankingStrategyV0:
    return RawRankingStrategyV0(
        RatingArtifact(
            "artifact-1",
            "1",
            "CubeAI",
            "Synthetic test prior",
            "CubeAI-owned",
            tuple(RatingEntry(f"oracle-{index}", float(index)) for index in range(8)),
        )
    )


def test_bot_only_draft_uses_legal_choices_and_retains_strategy_artifact_provenance() -> (
    None
):
    state, version = _state(DraftConfiguration(1, 1, 3, 17))

    completed = advance_bot_turns(state, version, {0: _strategy()})

    assert completed.status is DraftStatus.COMPLETED
    assert all(event.actor_origin is ActorOrigin.BOT for event in completed.pick_events)
    assert all(
        event.strategy_ref == "raw-ranking-v0@1" for event in completed.pick_events
    )
    assert all(event.bot_provenance is not None for event in completed.pick_events)
    assert {
        event.bot_provenance.rating_artifact_id
        for event in completed.pick_events
        if event.bot_provenance is not None
    } == {"artifact-1"}


def test_after_a_human_pick_bot_turns_stop_at_the_next_human_decision() -> None:
    state, version = _state(DraftConfiguration(2, 1, 2, 17))
    human_card = available_cards(state, 0)[0]
    after_human = pick_card(state, 0, human_card.id)

    after_bots = advance_bot_turns(after_human, version, {1: _strategy()})

    assert after_bots.active_seat == 0
    assert len(after_bots.pick_events) == 2
    assert after_bots.pick_events[-1].actor_origin is ActorOrigin.BOT
    assert after_bots.pick_events[-1].bot_provenance is not None


def test_one_human_and_seven_bots_complete_a_full_hand_off_to_next_human_turn() -> None:
    state, version = _state(DraftConfiguration(8, 1, 2, 17))
    after_human = pick_card(state, 0, available_cards(state, 0)[0].id)

    after_bots = advance_bot_turns(
        after_human,
        version,
        {seat: _strategy() for seat in range(1, 8)},
    )

    assert after_bots.active_seat == 0
    assert after_bots.pick_number == 1
    assert len(after_bots.pick_events) == 8
    bot_events = after_bots.pick_events[1:]
    assert [event.seat_number for event in bot_events] == list(range(1, 8))
    assert all(event.actor_origin is ActorOrigin.BOT for event in bot_events)
    assert all(event.strategy_ref == "raw-ranking-v0@1" for event in bot_events)
    assert all(event.bot_provenance is not None for event in bot_events)


@dataclass
class _RecordingStrategy:
    delegate: RawRankingStrategyV0
    seen: list[BotVisibleState] = field(default_factory=list)

    @property
    def strategy_id(self) -> str:
        return self.delegate.strategy_id

    @property
    def strategy_version(self) -> str:
        return self.delegate.strategy_version

    def choose(self, visible_state: BotVisibleState) -> BotPickDecision:
        self.seen.append(visible_state)
        return self.delegate.choose(visible_state)


def test_strategy_receives_only_the_active_bot_pack_and_never_the_runner_state() -> (
    None
):
    state, version = _state(DraftConfiguration(2, 1, 2, 17))
    strategy = _RecordingStrategy(_strategy())
    expected_ids = {card.id for card in available_cards(state, 0)}

    after_bot = advance_bot_turns(state, version, {0: strategy})

    assert after_bot.active_seat == 1
    assert len(strategy.seen) == 1
    visible = strategy.seen[0]
    assert {
        candidate.draft_card_instance_id for candidate in visible.candidates
    } == expected_ids
    assert not hasattr(visible, "allocation")
    assert not hasattr(visible, "pick_events")


@dataclass(frozen=True)
class _IllegalStrategy:
    strategy_id: str = "raw-ranking-v0"
    strategy_version: str = "1"

    def choose(self, visible_state: BotVisibleState) -> BotPickDecision:
        return BotPickDecision(
            "not-a-current-card",
            BotDecisionProvenance(
                self.strategy_id,
                self.strategy_version,
                "artifact-1",
                "1",
                0.0,
                RatingLookupOutcome.MISSING,
                BotTieBreakReason.INSTANCE_ID,
            ),
        )


@dataclass(frozen=True)
class _MalformedDecisionStrategy:
    strategy_id: str = "raw-ranking-v0"
    strategy_version: str = "1"

    def choose(self, visible_state: BotVisibleState) -> BotPickDecision:
        return object()  # type: ignore[return-value]


def test_illegal_strategy_output_aborts_without_mutating_state() -> None:
    state, version = _state(DraftConfiguration(1, 1, 2, 17))

    with pytest.raises(DraftTransitionError, match="not available"):
        advance_bot_turns(state, version, {0: _IllegalStrategy()})

    assert state.pick_events == ()
    assert state.active_seat == 0


def test_invalid_strategy_configuration_or_return_aborts_without_mutating_state() -> (
    None
):
    state, version = _state(DraftConfiguration(1, 1, 2, 17))

    with pytest.raises(BotTurnError, match="BotStrategy"):
        advance_bot_turns(state, version, {0: object()})  # type: ignore[dict-item]
    with pytest.raises(BotTurnError, match="BotPickDecision"):
        advance_bot_turns(state, version, {0: _MalformedDecisionStrategy()})

    assert state.pick_events == ()
    assert state.active_seat == 0


def test_same_state_and_artifact_replay_to_the_same_bot_events() -> None:
    first, version = _state(DraftConfiguration(1, 1, 3, 17))
    second, same_version = _state(DraftConfiguration(1, 1, 3, 17))

    completed_first = advance_bot_turns(first, version, {0: _strategy()})
    completed_second = advance_bot_turns(second, same_version, {0: _strategy()})

    assert completed_first.pick_events == completed_second.pick_events


def test_rejects_a_mismatched_cube_version_before_a_bot_can_pick() -> None:
    state, _ = _state(DraftConfiguration(1, 1, 2, 17))
    other = _version(2)
    mismatched = CubeVersion("version-2", other.cube, other.cards)

    with pytest.raises(BotTurnError, match="belong"):
        advance_bot_turns(state, mismatched, {0: _strategy()})
