"""Human review annotations kept separate from immutable draft truth."""
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

class ReviewAssessment(StrEnum):
    REASONABLE = "reasonable"
    DEBATABLE = "debatable"
    BAD = "bad"

class ReviewReason(StrEnum):
    BASE_RATING = "base_rating"
    COLOR_COMMITMENT = "color_commitment"
    CURVE = "curve"
    SYNERGY = "synergy"
    ARCHETYPE_FIT = "archetype_fit"
    FIXING = "fixing"
    NARROW_PAYOFF = "narrow_payoff"
    OTHER = "other"

@dataclass(frozen=True, slots=True)
class PickReviewAnnotation:
    id: str
    author: str
    cube_version_id: str
    draft_id: str
    sequence: int
    seat_number: int
    pack_number: int
    pick_number: int
    card_instance_id: str
    strategy_ref: str | None
    assessment: ReviewAssessment
    reasons: tuple[ReviewReason, ...] = ()
    note: str | None = None
    suggested_rating: float | None = None

    def __post_init__(self) -> None:
        for name in ("id", "author", "cube_version_id", "draft_id", "card_instance_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a nonblank string")
        for name in ("sequence", "seat_number", "pack_number", "pick_number"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.strategy_ref is not None and (not isinstance(self.strategy_ref, str) or not self.strategy_ref.strip()):
            raise ValueError("strategy_ref must be blank or null")
        if not isinstance(self.assessment, ReviewAssessment):
            raise ValueError("assessment must be a ReviewAssessment")
        reasons = tuple(self.reasons)
        if any(not isinstance(reason, ReviewReason) for reason in reasons) or len(set(reasons)) != len(reasons):
            raise ValueError("reasons must contain unique ReviewReason values")
        if self.note is not None and (not isinstance(self.note, str) or len(self.note) > 2000):
            raise ValueError("note must be at most 2000 characters")
        if self.suggested_rating is not None and (not isinstance(self.suggested_rating, (int, float)) or isinstance(self.suggested_rating, bool) or not isfinite(self.suggested_rating)):
            raise ValueError("suggested_rating must be finite numeric")
        object.__setattr__(self, "reasons", reasons)
