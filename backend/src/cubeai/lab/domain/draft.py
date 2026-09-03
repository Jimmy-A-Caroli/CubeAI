"""Immutable draft vocabulary; allocation and transitions belong to later issues."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


class DraftStatus(StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ActorOrigin(StrEnum):
    HUMAN = "human"
    BOT = "bot"
    SIMULATION = "simulation"


class RatingLookupOutcome(StrEnum):
    RATED = "rated"
    MISSING = "missing"


class BotTieBreakReason(StrEnum):
    HIGHEST_RATING = "highest_rating"
    INSTANCE_ID = "instance_id"


@dataclass(frozen=True, slots=True)
class DraftConfiguration:
    seats: int
    packs_per_seat: int
    pack_size: int
    seed: int

    def __post_init__(self) -> None:
        for field in ("seats", "packs_per_seat", "pack_size"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{field} must be a positive integer")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed must be an integer")

    @property
    def card_count(self) -> int:
        return self.seats * self.packs_per_seat * self.pack_size


@dataclass(frozen=True, slots=True)
class Draft:
    id: str
    cube_version_id: str
    configuration: DraftConfiguration
    status: DraftStatus = DraftStatus.CREATED

    def __post_init__(self) -> None:
        _require_text(self.id, "id")
        _require_text(self.cube_version_id, "cube_version_id")
        if not isinstance(self.configuration, DraftConfiguration):
            raise ValueError("configuration must be a DraftConfiguration")
        if not isinstance(self.status, DraftStatus):
            raise ValueError("status must be a DraftStatus")


@dataclass(frozen=True, slots=True)
class DraftSeat:
    draft_id: str
    seat_number: int

    def __post_init__(self) -> None:
        _require_text(self.draft_id, "draft_id")
        if (
            not isinstance(self.seat_number, int)
            or isinstance(self.seat_number, bool)
            or self.seat_number < 0
        ):
            raise ValueError("seat_number must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class DraftPack:
    draft_id: str
    pack_number: int
    owner_seat: int

    def __post_init__(self) -> None:
        _require_text(self.draft_id, "draft_id")
        for field in ("pack_number", "owner_seat"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field} must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class DraftCardInstance:
    id: str
    draft_id: str
    cube_card_id: str

    def __post_init__(self) -> None:
        _require_text(self.id, "id")
        _require_text(self.draft_id, "draft_id")
        _require_text(self.cube_card_id, "cube_card_id")


@dataclass(frozen=True, slots=True)
class BotDecisionProvenance:
    """The durable, decision-local explanation for one Bot v0 pick."""

    strategy_id: str
    strategy_version: str
    rating_artifact_id: str
    rating_artifact_version: str
    selected_rating: float
    rating_lookup_outcome: RatingLookupOutcome
    tie_break_reason: BotTieBreakReason

    def __post_init__(self) -> None:
        for field in (
            "strategy_id",
            "strategy_version",
            "rating_artifact_id",
            "rating_artifact_version",
        ):
            _require_text(getattr(self, field), field)
        if (
            not isinstance(self.selected_rating, (int, float))
            or isinstance(self.selected_rating, bool)
            or not isfinite(self.selected_rating)
        ):
            raise ValueError("selected_rating must be finite numeric")
        if not isinstance(self.rating_lookup_outcome, RatingLookupOutcome):
            raise ValueError("rating_lookup_outcome must be a RatingLookupOutcome")
        if not isinstance(self.tie_break_reason, BotTieBreakReason):
            raise ValueError("tie_break_reason must be a BotTieBreakReason")


@dataclass(frozen=True, slots=True)
class PickEvent:
    draft_id: str
    sequence: int
    seat_number: int
    pack_number: int
    pick_number: int
    card_instance_id: str
    actor_origin: ActorOrigin
    actor_id: str
    strategy_ref: str | None = None
    bot_provenance: BotDecisionProvenance | None = None

    def __post_init__(self) -> None:
        _require_text(self.draft_id, "draft_id")
        _require_text(self.card_instance_id, "card_instance_id")
        _require_text(self.actor_id, "actor_id")
        for field in ("sequence", "seat_number", "pack_number", "pick_number"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field} must be a nonnegative integer")
        if not isinstance(self.actor_origin, ActorOrigin):
            raise ValueError("actor_origin must be an ActorOrigin")
        if self.strategy_ref is not None:
            _require_text(self.strategy_ref, "strategy_ref")
        if self.actor_origin is ActorOrigin.BOT and self.bot_provenance is None:
            raise ValueError("BOT pick events require bot_provenance")
        if self.bot_provenance is not None:
            if self.actor_origin is not ActorOrigin.BOT:
                raise ValueError("bot_provenance requires actor_origin BOT")
            if not isinstance(self.bot_provenance, BotDecisionProvenance):
                raise ValueError("bot_provenance must be a BotDecisionProvenance")


@dataclass(frozen=True, slots=True)
class DraftPool:
    draft_id: str
    seat_number: int
    card_instance_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.draft_id, "draft_id")
        if (
            not isinstance(self.seat_number, int)
            or isinstance(self.seat_number, bool)
            or self.seat_number < 0
        ):
            raise ValueError("seat_number must be a nonnegative integer")
        instances = tuple(self.card_instance_ids)
        if any(not isinstance(item, str) or not item.strip() for item in instances):
            raise ValueError("card_instance_ids must contain nonblank strings")
        if len(instances) != len(set(instances)):
            raise ValueError("card_instance_ids must be unique")
        object.__setattr__(self, "card_instance_ids", instances)
