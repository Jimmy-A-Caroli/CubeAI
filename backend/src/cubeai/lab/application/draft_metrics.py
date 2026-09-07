"""Pure provenance-aware metrics derived from completed draft observations."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from cubeai.lab.application.draft_observations import (
    DraftDecisionObservation,
    derive_draft_observations,
)
from cubeai.lab.application.draft_tracking import LOCAL_HUMAN_SEAT
from cubeai.lab.application.wheel_observations import (
    WheelObservation,
    derive_wheel_observations,
)
from cubeai.lab.domain.draft import (
    ActorOrigin,
    DraftCardInstance,
    DraftConfiguration,
    DraftStatus,
)
from cubeai.lab.domain.draft_state import DraftState


METRIC_CALCULATION_VERSION = "m2-009-v1"


class MetricId(StrEnum):
    MEAN_PICK = "mean-pick"
    MEDIAN_PICK = "median-pick"
    PICK_RATE = "pick-rate"
    FIRST_PICK_RATE = "first-pick-rate"
    LAST_PICK_RATE = "last-pick-rate"
    SECOND_TO_LAST_PICK_RATE = "second-to-last-pick-rate"
    WHEEL_RETURN_RATE = "wheel-return-rate"
    SEEN_BEFORE_PICK = "seen-before-pick"


class MetricIdentityScope(StrEnum):
    CUBE_MEMBERSHIP = "cube-membership"
    DRAFT_CARD_INSTANCE = "draft-card-instance"


@dataclass(frozen=True, slots=True)
class MetricConfiguration:
    """The geometry used for a metric population, excluding the draft seed."""

    seats: int
    packs_per_seat: int
    pack_size: int

    @classmethod
    def from_draft_configuration(
        cls, configuration: DraftConfiguration
    ) -> MetricConfiguration:
        return cls(
            configuration.seats,
            configuration.packs_per_seat,
            configuration.pack_size,
        )


@dataclass(frozen=True, slots=True)
class HumanActorScope:
    """The one local human population defined by the current product."""

    local_human_seat: int = LOCAL_HUMAN_SEAT

    def __post_init__(self) -> None:
        if self.local_human_seat != LOCAL_HUMAN_SEAT:
            raise ValueError("human metrics are limited to the local human seat")


@dataclass(frozen=True, slots=True)
class BotActorScope:
    """One recorded Bot strategy/version population."""

    strategy_id: str
    strategy_version: str

    def __post_init__(self) -> None:
        for field in ("strategy_id", "strategy_version"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a nonblank string")


MetricBaseActorScope = HumanActorScope | BotActorScope


@dataclass(frozen=True, slots=True)
class CombinedActorScope:
    """An explicit, labelled union of human and/or Bot populations."""

    selectors: tuple[MetricBaseActorScope, ...]

    def __post_init__(self) -> None:
        selectors = tuple(self.selectors)
        if not selectors:
            raise ValueError("combined metrics require at least one actor selector")
        if any(
            not isinstance(item, (HumanActorScope, BotActorScope)) for item in selectors
        ):
            raise ValueError("combined selectors must be human or bot scopes")
        if len(selectors) != len(set(selectors)):
            raise ValueError("combined selectors must be unique")
        object.__setattr__(self, "selectors", selectors)


MetricActorScope = MetricBaseActorScope | CombinedActorScope


@dataclass(frozen=True, slots=True)
class MetricProvenance:
    calculation_version: str = METRIC_CALCULATION_VERSION
    observation_basis: str = "M2-001"
    wheel_basis: str = "M2-002"


@dataclass(frozen=True, slots=True)
class MetricContext:
    """Stable scope and source facts shared by every result in a calculation."""

    cube_version_id: str
    configuration: MetricConfiguration
    actor_scope: MetricActorScope
    completed_draft_ids: tuple[str, ...]
    completion_scope: str = "completed-drafts-only"
    provenance: MetricProvenance = MetricProvenance()


@dataclass(frozen=True, slots=True)
class RateMetric:
    metric_id: MetricId
    identity_scope: MetricIdentityScope
    membership_id: str
    value: Fraction | None
    numerator: int
    denominator: int
    context: MetricContext

    def __post_init__(self) -> None:
        if self.denominator < 0 or self.numerator < 0:
            raise ValueError("metric counts must be nonnegative")
        if self.numerator > self.denominator:
            raise ValueError("metric numerator cannot exceed its denominator")
        expected = (
            None
            if self.denominator == 0
            else Fraction(self.numerator, self.denominator)
        )
        if self.value != expected:
            raise ValueError("rate metric value must match its exact counts")


@dataclass(frozen=True, slots=True)
class PositionMetric:
    metric_id: MetricId
    identity_scope: MetricIdentityScope
    membership_id: str
    value: Fraction | None
    n: int
    context: MetricContext

    def __post_init__(self) -> None:
        if self.n < 0:
            raise ValueError("position sample size must be nonnegative")
        if (self.n == 0) != (self.value is None):
            raise ValueError("position metrics are undefined exactly when n is zero")


@dataclass(frozen=True, slots=True)
class SeenBeforePickSample:
    draft_id: str
    seat_number: int
    card_instance_id: str
    membership_id: str
    prior_appearances: int
    round_number: int
    pick_number: int
    cards_available_before_pick: int


@dataclass(frozen=True, slots=True)
class SeenBeforePickMetric:
    metric_id: MetricId
    identity_scope: MetricIdentityScope
    samples: tuple[SeenBeforePickSample, ...]
    n: int
    context: MetricContext

    def __post_init__(self) -> None:
        samples = tuple(self.samples)
        if self.n != len(samples):
            raise ValueError("seen-before-pick n must match its sample count")
        object.__setattr__(self, "samples", samples)


@dataclass(frozen=True, slots=True)
class DraftMetricResults:
    """One completed-population calculation; no persistence or live state."""

    context: MetricContext
    position_metrics: tuple[PositionMetric, ...]
    rate_metrics: tuple[RateMetric, ...]
    seen_before_pick: SeenBeforePickMetric


def derive_draft_metrics(
    states: Sequence[DraftState], actor_scope: MetricActorScope
) -> DraftMetricResults:
    """Calculate the frozen M2-009 facts from completed immutable drafts only.

    All qualifying drafts must share an exact CubeVersion and draft geometry.
    Observations and wheels are re-derived from replayed history; this function
    neither stores results nor exposes active-draft information.
    """

    source_states = tuple(states)
    if any(not isinstance(state, DraftState) for state in source_states):
        raise ValueError("states must contain DraftState values")
    _validate_actor_scope(actor_scope)
    completed = tuple(
        state for state in source_states if state.status is DraftStatus.COMPLETED
    )
    if not completed:
        raise ValueError("metrics require at least one completed draft")

    context = _metric_context(completed, actor_scope)
    membership_ids = _membership_ids(completed)
    position_values: dict[str, list[int]] = {
        membership_id: [] for membership_id in membership_ids
    }
    opportunity_counts = {membership_id: 0 for membership_id in membership_ids}
    selection_counts = {membership_id: 0 for membership_id in membership_ids}
    first_opportunities = {membership_id: 0 for membership_id in membership_ids}
    first_selections = {membership_id: 0 for membership_id in membership_ids}
    last_opportunities = {membership_id: 0 for membership_id in membership_ids}
    last_selections = {membership_id: 0 for membership_id in membership_ids}
    second_last_opportunities = {membership_id: 0 for membership_id in membership_ids}
    second_last_selections = {membership_id: 0 for membership_id in membership_ids}
    completed_pass_opportunities = {
        membership_id: 0 for membership_id in membership_ids
    }
    wheel_returns = {membership_id: 0 for membership_id in membership_ids}
    seen_samples: list[SeenBeforePickSample] = []

    for state in completed:
        observations = derive_draft_observations(state)
        _accumulate_member_opportunities(
            observations,
            actor_scope,
            opportunity_counts,
            first_opportunities,
            last_opportunities,
            second_last_opportunities,
        )
        _accumulate_member_selections(
            observations,
            state,
            actor_scope,
            selection_counts,
            first_selections,
            last_selections,
            second_last_selections,
            position_values,
            seen_samples,
        )
        _accumulate_wheel_facts(
            observations,
            derive_wheel_observations(observations),
            state,
            actor_scope,
            completed_pass_opportunities,
            wheel_returns,
        )

    position_metrics = tuple(
        metric
        for membership_id in membership_ids
        for metric in _position_metrics(
            membership_id, position_values[membership_id], context
        )
    )
    rate_metrics = tuple(
        metric
        for membership_id in membership_ids
        for metric in _rate_metrics(
            membership_id,
            context,
            selection_counts[membership_id],
            opportunity_counts[membership_id],
            first_selections[membership_id],
            first_opportunities[membership_id],
            last_selections[membership_id],
            last_opportunities[membership_id],
            second_last_selections[membership_id],
            second_last_opportunities[membership_id],
            wheel_returns[membership_id],
            completed_pass_opportunities[membership_id],
        )
    )
    seen = SeenBeforePickMetric(
        MetricId.SEEN_BEFORE_PICK,
        MetricIdentityScope.DRAFT_CARD_INSTANCE,
        tuple(seen_samples),
        len(seen_samples),
        context,
    )
    return DraftMetricResults(context, position_metrics, rate_metrics, seen)


def _metric_context(
    completed: tuple[DraftState, ...], actor_scope: MetricActorScope
) -> MetricContext:
    first = completed[0]
    configuration = MetricConfiguration.from_draft_configuration(
        first.draft.configuration
    )
    if any(
        state.draft.cube_version_id != first.draft.cube_version_id
        for state in completed
    ):
        raise ValueError("metrics cannot combine CubeVersions")
    if any(
        MetricConfiguration.from_draft_configuration(state.draft.configuration)
        != configuration
        for state in completed
    ):
        raise ValueError("metrics cannot combine draft configurations")
    return MetricContext(
        first.draft.cube_version_id,
        configuration,
        actor_scope,
        tuple(state.draft.id for state in completed),
    )


def _membership_ids(states: tuple[DraftState, ...]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            card.cube_card_id
            for state in states
            for allocated in state.allocation
            for card in allocated.cards
        )
    )


def _accumulate_member_opportunities(
    observations: tuple[DraftDecisionObservation, ...],
    actor_scope: MetricActorScope,
    opportunities: dict[str, int],
    first_opportunities: dict[str, int],
    last_opportunities: dict[str, int],
    second_last_opportunities: dict[str, int],
) -> None:
    for observation in observations:
        if not _matches_actor_scope(observation, actor_scope):
            continue
        cards_available = len(observation.cards_seen)
        for card in observation.cards_seen:
            opportunities[card.cube_card_id] += 1
            if observation.event.pick_number == 0:
                first_opportunities[card.cube_card_id] += 1
            if cards_available == 1:
                last_opportunities[card.cube_card_id] += 1
            if cards_available == 2:
                second_last_opportunities[card.cube_card_id] += 1


def _accumulate_member_selections(
    observations: tuple[DraftDecisionObservation, ...],
    state: DraftState,
    actor_scope: MetricActorScope,
    selections: dict[str, int],
    first_selections: dict[str, int],
    last_selections: dict[str, int],
    second_last_selections: dict[str, int],
    positions: dict[str, list[int]],
    seen_samples: list[SeenBeforePickSample],
) -> None:
    for index, observation in enumerate(observations):
        if not _matches_actor_scope(observation, actor_scope):
            continue
        chosen = observation.chosen_card
        membership_id = chosen.cube_card_id
        selections[membership_id] += 1
        positions[membership_id].append(observation.event.pick_number + 1)
        cards_available = len(observation.cards_seen)
        if observation.event.pick_number == 0:
            first_selections[membership_id] += 1
        if cards_available == 1:
            last_selections[membership_id] += 1
        if cards_available == 2:
            second_last_selections[membership_id] += 1
        seen_samples.append(
            SeenBeforePickSample(
                state.draft.id,
                observation.event.seat_number,
                chosen.id,
                membership_id,
                _prior_appearances(observations[:index], observation),
                _round_number(state, observation),
                observation.event.pick_number + 1,
                cards_available,
            )
        )


def _accumulate_wheel_facts(
    observations: tuple[DraftDecisionObservation, ...],
    wheels: tuple[WheelObservation, ...],
    state: DraftState,
    actor_scope: MetricActorScope,
    completed_pass_opportunities: dict[str, int],
    wheel_returns: dict[str, int],
) -> None:
    opportunities = _completed_pass_opportunities(observations, state, actor_scope)
    for card in opportunities.values():
        completed_pass_opportunities[card.cube_card_id] += 1
    wheel_keys = {
        (wheel.seat_number, wheel.card_instance_id, wheel.first_seen_sequence)
        for wheel in wheels
    }
    for key, card in opportunities.items():
        if key in wheel_keys:
            wheel_returns[card.cube_card_id] += 1


def _completed_pass_opportunities(
    observations: tuple[DraftDecisionObservation, ...],
    state: DraftState,
    actor_scope: MetricActorScope,
) -> dict[tuple[int, str, int], DraftCardInstance]:
    first_seen: set[tuple[int, DraftCardInstance]] = set()
    completed: dict[tuple[int, str, int], DraftCardInstance] = {}
    for index, observation in enumerate(observations):
        seat = observation.event.seat_number
        round_number = _round_number(state, observation)
        for card in observation.cards_seen:
            key = (seat, card)
            if key in first_seen:
                continue
            first_seen.add(key)
            if not _matches_actor_scope(observation, actor_scope):
                continue
            if card == observation.chosen_card:
                continue
            if any(
                later.event.seat_number == seat
                and _round_number(state, later) == round_number
                and card not in later.cards_seen
                for later in observations[index + 1 :]
            ):
                completed[(seat, card.id, observation.event.sequence)] = card
    return completed


def _prior_appearances(
    earlier: tuple[DraftDecisionObservation, ...],
    selected: DraftDecisionObservation,
) -> int:
    return sum(
        selected.chosen_card in observation.cards_seen
        and observation.event.seat_number == selected.event.seat_number
        for observation in earlier
    )


def _round_number(state: DraftState, observation: DraftDecisionObservation) -> int:
    configuration = state.draft.configuration
    return (
        observation.event.sequence // (configuration.seats * configuration.pack_size)
        + 1
    )


def _position_metrics(
    membership_id: str, positions: list[int], context: MetricContext
) -> tuple[PositionMetric, PositionMetric]:
    n = len(positions)
    ordered = sorted(positions)
    mean = None if n == 0 else Fraction(sum(positions), n)
    median = None if n == 0 else Fraction(ordered[(n - 1) // 2] + ordered[n // 2], 2)
    return (
        PositionMetric(
            MetricId.MEAN_PICK,
            MetricIdentityScope.CUBE_MEMBERSHIP,
            membership_id,
            mean,
            n,
            context,
        ),
        PositionMetric(
            MetricId.MEDIAN_PICK,
            MetricIdentityScope.CUBE_MEMBERSHIP,
            membership_id,
            median,
            n,
            context,
        ),
    )


def _rate_metrics(
    membership_id: str,
    context: MetricContext,
    selections: int,
    opportunities: int,
    first_selections: int,
    first_opportunities: int,
    last_selections: int,
    last_opportunities: int,
    second_last_selections: int,
    second_last_opportunities: int,
    wheels: int,
    completed_passes: int,
) -> tuple[RateMetric, ...]:
    values = (
        (MetricId.PICK_RATE, selections, opportunities),
        (MetricId.FIRST_PICK_RATE, first_selections, first_opportunities),
        (MetricId.LAST_PICK_RATE, last_selections, last_opportunities),
        (
            MetricId.SECOND_TO_LAST_PICK_RATE,
            second_last_selections,
            second_last_opportunities,
        ),
        (MetricId.WHEEL_RETURN_RATE, wheels, completed_passes),
    )
    return tuple(
        RateMetric(
            metric_id,
            MetricIdentityScope.CUBE_MEMBERSHIP,
            membership_id,
            None if denominator == 0 else Fraction(numerator, denominator),
            numerator,
            denominator,
            context,
        )
        for metric_id, numerator, denominator in values
    )


def _validate_actor_scope(actor_scope: MetricActorScope) -> None:
    if not isinstance(
        actor_scope, (HumanActorScope, BotActorScope, CombinedActorScope)
    ):
        raise ValueError("actor_scope must be a human, bot, or combined scope")


def _matches_actor_scope(
    observation: DraftDecisionObservation, actor_scope: MetricActorScope
) -> bool:
    event = observation.event
    if isinstance(actor_scope, HumanActorScope):
        return (
            event.actor_origin is ActorOrigin.HUMAN
            and event.seat_number == actor_scope.local_human_seat
        )
    if isinstance(actor_scope, BotActorScope):
        provenance = event.bot_provenance
        return (
            event.actor_origin is ActorOrigin.BOT
            and provenance is not None
            and provenance.strategy_id == actor_scope.strategy_id
            and provenance.strategy_version == actor_scope.strategy_version
        )
    return any(
        _matches_actor_scope(observation, selector)
        for selector in actor_scope.selectors
    )
