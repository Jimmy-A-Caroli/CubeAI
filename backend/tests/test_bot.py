from dataclasses import fields

import pytest

from cubeai.lab.application import load_raw_ranking_v0_artifact
from cubeai.lab.domain import (
    BotDecisionProvenance,
    BotTieBreakReason,
    BotVisibleCandidate,
    BotVisibleState,
    RatingArtifact,
    RatingEntry,
    RatingLookupOutcome,
    RawRankingStrategyV0,
)


def _strategy() -> RawRankingStrategyV0:
    return RawRankingStrategyV0(
        RatingArtifact(
            "artifact-1",
            "1",
            "CubeAI",
            "Synthetic test prior",
            "CubeAI-owned",
            (RatingEntry("oracle-high", 4.0), RatingEntry("oracle-low", 1.0)),
        )
    )


def _state(*candidates: BotVisibleCandidate) -> BotVisibleState:
    return BotVisibleState(1, 0, 0, candidates)


def test_raw_ranking_chooses_the_highest_rated_legal_candidate() -> None:
    decision = _strategy().choose(
        _state(
            BotVisibleCandidate("instance-low", "membership-1", "oracle-low"),
            BotVisibleCandidate("instance-high", "membership-2", "oracle-high"),
        )
    )

    assert decision.selected_draft_card_instance_id == "instance-high"
    assert decision.provenance.selected_rating == 4.0
    assert decision.provenance.rating_lookup_outcome is RatingLookupOutcome.RATED
    assert decision.provenance.tie_break_reason is BotTieBreakReason.HIGHEST_RATING


def test_unlisted_ratings_use_the_artifact_fallback_and_choose_lowest_instance_id() -> (
    None
):
    decision = _strategy().choose(
        _state(
            BotVisibleCandidate("instance-z", "membership-1", "oracle-missing-a"),
            BotVisibleCandidate("instance-a", "membership-2", "oracle-missing-b"),
        )
    )

    assert decision.selected_draft_card_instance_id == "instance-a"
    assert decision.provenance.selected_rating == 0.0
    assert decision.provenance.rating_lookup_outcome is RatingLookupOutcome.FALLBACK
    assert decision.provenance.tie_break_reason is BotTieBreakReason.INSTANCE_ID


def test_fallback_is_a_mid_tier_score_with_explicit_provenance() -> None:
    strategy = RawRankingStrategyV0(
        RatingArtifact(
            "artifact-1",
            "1",
            "CubeAI",
            "Synthetic test prior",
            "CubeAI-owned",
            (RatingEntry("oracle-low", 1.0),),
            fallback_rating=2.6,
        )
    )

    decision = strategy.choose(
        _state(
            BotVisibleCandidate("instance-low", "membership-1", "oracle-low"),
            BotVisibleCandidate("instance-fallback", "membership-2", "oracle-unlisted"),
        )
    )

    assert decision.selected_draft_card_instance_id == "instance-fallback"
    assert decision.provenance.selected_rating == 2.6
    assert decision.provenance.rating_lookup_outcome is RatingLookupOutcome.FALLBACK


def test_equal_ratings_and_duplicate_memberships_remain_distinct_choices() -> None:
    strategy = RawRankingStrategyV0(
        RatingArtifact(
            "artifact-1",
            "1",
            "CubeAI",
            "Synthetic test prior",
            "CubeAI-owned",
            (RatingEntry("oracle-1", 2.0),),
        )
    )
    state = _state(
        BotVisibleCandidate("instance-2", "membership-a", "oracle-1"),
        BotVisibleCandidate("instance-1", "membership-b", "oracle-1"),
    )

    assert strategy.choose(state).selected_draft_card_instance_id == "instance-1"
    assert strategy.choose(state) == strategy.choose(state)


def test_visible_state_cannot_receive_a_broad_draft_state_field() -> None:
    assert {field.name for field in fields(BotVisibleState)} == {
        "seat_number",
        "pack_number",
        "pick_number",
        "candidates",
    }


def test_artifact_rejects_duplicate_oracle_ids_and_visible_state_rejects_no_choices() -> (
    None
):
    with pytest.raises(ValueError, match="unique Oracle IDs"):
        RatingArtifact(
            "artifact-1",
            "1",
            "CubeAI",
            "Synthetic test prior",
            "CubeAI-owned",
            (RatingEntry("oracle-1", 1.0), RatingEntry("oracle-1", 2.0)),
        )
    with pytest.raises(ValueError, match="nonempty"):
        BotVisibleState(0, 0, 0, ())
    with pytest.raises(ValueError, match="finite"):
        RatingEntry("oracle-not-a-number", float("nan"))
    with pytest.raises(ValueError, match="finite"):
        BotDecisionProvenance(
            "raw-ranking-v0",
            "1",
            "artifact-1",
            "1",
            float("inf"),
            RatingLookupOutcome.RATED,
            BotTieBreakReason.HIGHEST_RATING,
        )


def test_package_local_artifact_is_versioned_provenanced_and_covers_target_cube() -> (
    None
):
    artifact = load_raw_ranking_v0_artifact()

    assert artifact.id == "cubeai-raw-ranking-v0"
    assert artifact.version == "2026.09.04.1"
    assert artifact.provenance is not None
    assert artifact.provenance.source_name == "Draftsim"
    assert (
        artifact.provenance.source_url
        == "https://draftsim.com/vintage_cube-pick-order.php"
    )
    assert len(artifact.entries) >= 480
    assert artifact.fallback_rating == 2.6
    assert artifact.rating_for("unlisted-oracle") is None
    assert artifact.score_for("unlisted-oracle") == (2.6, RatingLookupOutcome.FALLBACK)
