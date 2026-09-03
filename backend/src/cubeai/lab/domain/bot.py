"""Pure, visible-state-only Bot v0 strategy values."""

from dataclasses import dataclass
from math import isfinite
from typing import Protocol, runtime_checkable

from cubeai.lab.domain.draft import (
    BotDecisionProvenance,
    BotTieBreakReason,
    RatingLookupOutcome,
)


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


@dataclass(frozen=True, slots=True)
class RatingEntry:
    oracle_id: str
    rating: float

    def __post_init__(self) -> None:
        _require_text(self.oracle_id, "oracle_id")
        if (
            not isinstance(self.rating, (int, float))
            or isinstance(self.rating, bool)
            or not isfinite(self.rating)
        ):
            raise ValueError("rating must be finite numeric")


@dataclass(frozen=True, slots=True)
class RatingArtifact:
    """A small, reviewed CubeAI-owned static rating snapshot."""

    id: str
    version: str
    ownership: str
    basis: str
    rights: str
    entries: tuple[RatingEntry, ...]

    def __post_init__(self) -> None:
        for field in ("id", "version", "ownership", "basis", "rights"):
            _require_text(getattr(self, field), field)
        entries = tuple(self.entries)
        if any(not isinstance(entry, RatingEntry) for entry in entries):
            raise ValueError("entries must contain RatingEntry values")
        if len({entry.oracle_id for entry in entries}) != len(entries):
            raise ValueError("entries must have unique Oracle IDs")
        object.__setattr__(self, "entries", entries)

    def rating_for(self, oracle_id: str) -> float | None:
        _require_text(oracle_id, "oracle_id")
        return next(
            (entry.rating for entry in self.entries if entry.oracle_id == oracle_id),
            None,
        )


@dataclass(frozen=True, slots=True)
class BotVisibleCandidate:
    """One legal card choice, without any broad draft-runner state."""

    draft_card_instance_id: str
    cube_card_id: str
    oracle_id: str

    def __post_init__(self) -> None:
        for field in ("draft_card_instance_id", "cube_card_id", "oracle_id"):
            _require_text(getattr(self, field), field)


@dataclass(frozen=True, slots=True)
class BotVisibleState:
    """The complete Bot v0 input: only the acting seat's legal choices."""

    seat_number: int
    pack_number: int
    pick_number: int
    candidates: tuple[BotVisibleCandidate, ...]

    def __post_init__(self) -> None:
        for field in ("seat_number", "pack_number", "pick_number"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field} must be a nonnegative integer")
        candidates = tuple(self.candidates)
        if not candidates:
            raise ValueError("candidates must be nonempty")
        if any(
            not isinstance(candidate, BotVisibleCandidate) for candidate in candidates
        ):
            raise ValueError("candidates must contain BotVisibleCandidate values")
        if len({candidate.draft_card_instance_id for candidate in candidates}) != len(
            candidates
        ):
            raise ValueError("candidates must have unique draft-card instance IDs")
        object.__setattr__(self, "candidates", candidates)


@dataclass(frozen=True, slots=True)
class BotPickDecision:
    selected_draft_card_instance_id: str
    provenance: BotDecisionProvenance

    def __post_init__(self) -> None:
        _require_text(
            self.selected_draft_card_instance_id, "selected_draft_card_instance_id"
        )
        if not isinstance(self.provenance, BotDecisionProvenance):
            raise ValueError("provenance must be a BotDecisionProvenance")


@runtime_checkable
class BotStrategy(Protocol):
    """The narrow replacement boundary for future seat-safe strategies."""

    @property
    def strategy_id(self) -> str: ...

    @property
    def strategy_version(self) -> str: ...

    def choose(self, visible_state: BotVisibleState) -> BotPickDecision: ...


@dataclass(frozen=True, slots=True)
class RawRankingStrategyV0:
    """A deterministic, context-free, Oracle-ID static-prior strategy."""

    artifact: RatingArtifact
    strategy_id: str = "raw-ranking-v0"
    strategy_version: str = "1"

    def __post_init__(self) -> None:
        if not isinstance(self.artifact, RatingArtifact):
            raise ValueError("artifact must be a RatingArtifact")
        _require_text(self.strategy_id, "strategy_id")
        _require_text(self.strategy_version, "strategy_version")

    def choose(self, visible_state: BotVisibleState) -> BotPickDecision:
        if not isinstance(visible_state, BotVisibleState):
            raise ValueError("visible_state must be a BotVisibleState")
        scored = tuple(
            (candidate, self.artifact.rating_for(candidate.oracle_id))
            for candidate in visible_state.candidates
        )
        highest_rating = max(0.0 if rating is None else rating for _, rating in scored)
        finalists = tuple(
            (candidate, rating)
            for candidate, rating in scored
            if (0.0 if rating is None else rating) == highest_rating
        )
        selected, selected_rating = min(
            finalists, key=lambda item: item[0].draft_card_instance_id
        )
        return BotPickDecision(
            selected.draft_card_instance_id,
            BotDecisionProvenance(
                self.strategy_id,
                self.strategy_version,
                self.artifact.id,
                self.artifact.version,
                highest_rating,
                (
                    RatingLookupOutcome.MISSING
                    if selected_rating is None
                    else RatingLookupOutcome.RATED
                ),
                (
                    BotTieBreakReason.INSTANCE_ID
                    if len(finalists) > 1
                    else BotTieBreakReason.HIGHEST_RATING
                ),
            ),
        )
