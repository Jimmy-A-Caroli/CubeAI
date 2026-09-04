"""Pure, event-derived decision observations for local draft inspection."""

from dataclasses import dataclass

from cubeai.lab.domain.draft import DraftCardInstance, PickEvent
from cubeai.lab.domain.draft_state import (
    DraftState,
    DraftTransitionError,
    available_cards,
    pick_card,
    pool_for_seat,
    start_draft,
)


class DraftObservationError(ValueError):
    """A persisted draft cannot be replayed into a trustworthy observation."""


@dataclass(frozen=True, slots=True)
class DraftDecisionObservation:
    """The information visible to one seat immediately before one recorded pick.

    The record derives entirely from a DraftState's immutable allocation and
    ordered event prefix. It intentionally stores no calculated advice or
    inferred human reasoning.
    """

    event: PickEvent
    chosen_card: DraftCardInstance
    cards_seen: tuple[DraftCardInstance, ...]
    pool_before: tuple[DraftCardInstance, ...]


def derive_draft_observations(
    state: DraftState,
) -> tuple[DraftDecisionObservation, ...]:
    """Replay a valid draft's event history into ordered decision observations.

    Replaying validates the active seat, pack, pick number, candidate ordering,
    and chosen instance at every event. The supplied state is never mutated.
    """

    if not isinstance(state, DraftState):
        raise ValueError("state must be a DraftState")

    instances = {
        instance.id: instance for pack in state.allocation for instance in pack.cards
    }
    replayed = start_draft(state.draft, state.allocation)
    observations: list[DraftDecisionObservation] = []
    for event in state.pick_events:
        try:
            if replayed.active_seat != event.seat_number:
                raise DraftObservationError("event seat does not match replay turn")
            active_pack = replayed.active_packs[event.seat_number].pack
            if (
                active_pack.pack_number != event.pack_number
                or replayed.pick_number != event.pick_number
            ):
                raise DraftObservationError("event pack or pick does not match replay")
            cards_seen = available_cards(replayed, event.seat_number)
            if event.card_instance_id not in {card.id for card in cards_seen}:
                raise DraftObservationError("chosen card is absent from replayed pack")
            chosen_card = next(
                card for card in cards_seen if card.id == event.card_instance_id
            )
            observations.append(
                DraftDecisionObservation(
                    event,
                    chosen_card,
                    cards_seen,
                    tuple(
                        instances[card_id]
                        for card_id in pool_for_seat(
                            replayed, event.seat_number
                        ).card_instance_ids
                    ),
                )
            )
            replayed = pick_card(
                replayed,
                event.seat_number,
                event.card_instance_id,
                actor_origin=event.actor_origin,
                actor_id=event.actor_id,
                strategy_ref=event.strategy_ref,
                bot_provenance=event.bot_provenance,
            )
        except DraftTransitionError as error:
            raise DraftObservationError("event cannot be replayed") from error
    if replayed != state:
        raise DraftObservationError("replayed state differs from persisted draft")
    return tuple(observations)
