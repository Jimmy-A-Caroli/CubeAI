"""Pure wheel facts derived from ordered draft decision observations."""

from dataclasses import dataclass
from collections.abc import Sequence

from cubeai.lab.application.draft_observations import DraftDecisionObservation
from cubeai.lab.domain.draft import DraftCardInstance


@dataclass(frozen=True, slots=True)
class WheelObservation:
    """The first verified return of one passed draft-card instance to one seat."""

    seat_number: int
    draft_id: str
    card_instance_id: str
    first_seen_sequence: int
    first_seen_pack_number: int
    first_seen_pick_number: int
    returned_sequence: int
    returned_pack_number: int
    returned_pick_number: int


def derive_wheel_observations(
    observations: Sequence[DraftDecisionObservation],
) -> tuple[WheelObservation, ...]:
    """Return first verified instance returns without interpreting their meaning.

    A return requires a seat to pass an instance, encounter at least one later
    decision where that instance is absent, and then see that same instance
    again. This prevents a one-seat pack that simply remains available from
    being labelled a wheel. At most one first-return fact is emitted per
    ``(seat, draft-card instance)`` pair.
    """

    ordered = tuple(observations)
    if any(not isinstance(item, DraftDecisionObservation) for item in ordered):
        raise ValueError("observations must contain DraftDecisionObservation values")
    if any(
        later.event.sequence <= earlier.event.sequence
        for earlier, later in zip(ordered[:-1], ordered[1:], strict=True)
    ):
        raise ValueError("observations must be in strictly increasing event order")

    first_passes: dict[tuple[int, DraftCardInstance], DraftDecisionObservation] = {}
    left_seat: set[tuple[int, DraftCardInstance]] = set()
    returned: set[tuple[int, DraftCardInstance]] = set()
    wheels: list[WheelObservation] = []

    for observation in ordered:
        seat_number = observation.event.seat_number
        seen_instances = set(observation.cards_seen)
        for key in tuple(first_passes):
            if key[0] == seat_number and key[1] not in seen_instances:
                left_seat.add(key)
        for card in observation.cards_seen:
            key = (seat_number, card)
            first_seen = first_passes.get(key)
            if first_seen is not None and key in left_seat and key not in returned:
                wheels.append(
                    WheelObservation(
                        seat_number,
                        card.draft_id,
                        card.id,
                        first_seen.event.sequence,
                        first_seen.event.pack_number,
                        first_seen.event.pick_number,
                        observation.event.sequence,
                        observation.event.pack_number,
                        observation.event.pick_number,
                    )
                )
                returned.add(key)
        for card in observation.cards_seen:
            if card != observation.chosen_card:
                first_passes.setdefault((seat_number, card), observation)

    return tuple(wheels)
