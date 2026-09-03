"""Atomic local draft commands composed at the application boundary."""

from collections.abc import Mapping

from cubeai.lab.application.bot_turns import advance_bot_turns
from cubeai.lab.application.repositories import DraftRepository
from cubeai.lab.domain.bot import BotStrategy
from cubeai.lab.domain.cube import CubeVersion
from cubeai.lab.domain.draft_state import DraftState, pick_card


def submit_human_pick_and_advance_bots(
    repository: DraftRepository,
    draft_id: str,
    seat_number: int,
    card_instance_id: str,
    strategies_by_seat: Mapping[int, BotStrategy],
) -> DraftState:
    """Persist one human command and consecutive configured Bot turns atomically."""

    def transition(state: DraftState, cube_version: CubeVersion) -> DraftState:
        after_human_pick = pick_card(state, seat_number, card_instance_id)
        return advance_bot_turns(after_human_pick, cube_version, strategies_by_seat)

    return repository.transact(draft_id, transition)
