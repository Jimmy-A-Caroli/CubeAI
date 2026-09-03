"""Deterministically advance configured Bot v0 seats through legal picks."""

from collections.abc import Mapping

from cubeai.lab.domain.bot import (
    BotPickDecision,
    BotStrategy,
    BotVisibleCandidate,
    BotVisibleState,
)
from cubeai.lab.domain.cube import CubeVersion, ResolutionStatus
from cubeai.lab.domain.draft import ActorOrigin, DraftStatus
from cubeai.lab.domain.draft_state import DraftState, available_cards, pick_card


class BotTurnError(ValueError):
    """A configured strategy cannot receive a safe, valid bot-turn input."""


def advance_bot_turns(
    state: DraftState,
    cube_version: CubeVersion,
    strategies_by_seat: Mapping[int, BotStrategy],
) -> DraftState:
    """Advance only consecutive configured bot seats from the current turn.

    The runner owns complete state for transition validation. A strategy receives
    only the current active pack's legal instance candidates and their resolved
    Oracle IDs. A missing strategy means the current turn belongs to a human.
    """

    if not isinstance(state, DraftState):
        raise ValueError("state must be a DraftState")
    if not isinstance(cube_version, CubeVersion):
        raise ValueError("cube_version must be a CubeVersion")
    if state.draft.cube_version_id != cube_version.id:
        raise BotTurnError("cube_version must belong to the draft")
    strategies = dict(strategies_by_seat)
    if any(
        not isinstance(seat, int)
        or isinstance(seat, bool)
        or not 0 <= seat < state.draft.configuration.seats
        for seat in strategies
    ):
        raise BotTurnError("strategy seats must match the draft geometry")
    if any(not isinstance(strategy, BotStrategy) for strategy in strategies.values()):
        raise BotTurnError("strategies must implement the BotStrategy contract")

    current = state
    while current.status is not DraftStatus.COMPLETED:
        assert current.active_seat is not None
        strategy = strategies.get(current.active_seat)
        if strategy is None:
            return current
        visible_state = _visible_state(current, cube_version)
        decision = strategy.choose(visible_state)
        if not isinstance(decision, BotPickDecision):
            raise BotTurnError("strategy must return a BotPickDecision")
        if decision.provenance.strategy_id != strategy.strategy_id:
            raise BotTurnError(
                "decision strategy ID must match the configured strategy"
            )
        if decision.provenance.strategy_version != strategy.strategy_version:
            raise BotTurnError(
                "decision strategy version must match the configured strategy"
            )
        current = pick_card(
            current,
            visible_state.seat_number,
            decision.selected_draft_card_instance_id,
            actor_origin=ActorOrigin.BOT,
            actor_id=f"seat:{visible_state.seat_number}",
            strategy_ref=(
                f"{decision.provenance.strategy_id}"
                f"@{decision.provenance.strategy_version}"
            ),
            bot_provenance=decision.provenance,
        )
    return current


def _visible_state(state: DraftState, cube_version: CubeVersion) -> BotVisibleState:
    assert state.active_seat is not None
    memberships = {card.id: card for card in cube_version.cards}
    candidates: list[BotVisibleCandidate] = []
    for instance in available_cards(state, state.active_seat):
        membership = memberships.get(instance.cube_card_id)
        if (
            membership is None
            or membership.resolution_status is not ResolutionStatus.RESOLVED
            or membership.printing is None
            or membership.printing.card_identity.oracle_id is None
        ):
            raise BotTurnError("legal bot candidates require resolved Oracle IDs")
        candidates.append(
            BotVisibleCandidate(
                instance.id,
                instance.cube_card_id,
                membership.printing.card_identity.oracle_id,
            )
        )
    active_pack = state.active_packs[state.active_seat].pack
    return BotVisibleState(
        state.active_seat,
        active_pack.pack_number,
        state.pick_number,
        tuple(candidates),
    )
