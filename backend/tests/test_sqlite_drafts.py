import sqlite3

import pytest

from cubeai.lab.adapters import (
    PersistenceConflict,
    PersistenceError,
    SQLiteDraftRepository,
)
from cubeai.lab.application import submit_human_pick_and_advance_bots
from cubeai.lab.domain import (
    AllocatedPack,
    ActorOrigin,
    BotDecisionProvenance,
    BotTieBreakReason,
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    Draft,
    DraftCardInstance,
    DraftConfiguration,
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


def _version() -> CubeVersion:
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
                        f"identity-{index}",
                        f"Synthetic {index}",
                        ResolutionStatus.RESOLVED,
                        f"oracle-{index}",
                    ),
                ),
            )
            for index in range(4)
        ),
    )


def _state():
    version = _version()
    draft = Draft("draft-1", version.id, DraftConfiguration(2, 1, 2, 13))
    return (
        start_draft(
            draft,
            allocate_packs(
                "draft-1", version, validate_cube_version(version, draft.configuration)
            ),
        ),
        version,
    )


def _bot_provenance() -> BotDecisionProvenance:
    return BotDecisionProvenance(
        "raw-ranking-v0",
        "2026.09.03.1",
        "cubeai-raw-ranking-v0",
        "2026.09.03.1",
        3.0,
        RatingLookupOutcome.RATED,
        BotTieBreakReason.HIGHEST_RATING,
    )


def _strategy() -> RawRankingStrategyV0:
    return RawRankingStrategyV0(
        RatingArtifact(
            "artifact-1",
            "1",
            "CubeAI",
            "Synthetic test prior",
            "CubeAI-owned",
            tuple(RatingEntry(f"oracle-{index}", float(index)) for index in range(4)),
        )
    )


def test_migrates_and_rehydrates_exact_state_and_bot_provenance(tmp_path) -> None:
    state, version = _state()
    bot_card = available_cards(state, 0)[0]
    advanced = pick_card(
        state,
        0,
        bot_card.id,
        actor_origin=ActorOrigin.BOT,
        actor_id="seat:0",
        strategy_ref="raw-ranking-v0@2026.09.03.1",
        bot_provenance=_bot_provenance(),
    )
    database_path = tmp_path / "drafts.sqlite3"

    SQLiteDraftRepository(database_path).save_draft(version, advanced)
    restarted = SQLiteDraftRepository(database_path)

    assert restarted.load_cube_version(version.id) == version
    assert restarted.load_draft(advanced.draft.id) == advanced
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall() == [(1,), (2,)]


def test_save_rolls_back_when_transaction_fails_before_commit(tmp_path) -> None:
    state, version = _state()
    database_path = tmp_path / "drafts.sqlite3"
    SQLiteDraftRepository(database_path).save_draft(version, state)
    after_pick = pick_card(state, 0, available_cards(state, 0)[0].id)

    failing = SQLiteDraftRepository(
        database_path,
        before_commit=lambda: (_ for _ in ()).throw(RuntimeError("injected failure")),
    )

    with pytest.raises(RuntimeError, match="injected failure"):
        failing.save_draft(version, after_pick)

    restarted = SQLiteDraftRepository(database_path)
    assert restarted.load_cube_version(version.id) == version
    assert restarted.load_draft(state.draft.id) == state


def test_conflicting_prior_event_history_is_rejected(tmp_path) -> None:
    state, version = _state()
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    first = pick_card(state, 0, available_cards(state, 0)[0].id)
    conflicting = pick_card(state, 0, available_cards(state, 0)[1].id)

    repository.save_draft(version, first)

    with pytest.raises(PersistenceConflict, match="persisted prefix"):
        repository.save_draft(version, conflicting)


def test_save_extends_an_existing_event_history(tmp_path) -> None:
    state, version = _state()
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    first = pick_card(state, 0, available_cards(state, 0)[0].id)
    second = pick_card(first, 1, available_cards(first, 1)[0].id)

    repository.save_draft(version, first)
    repository.save_draft(version, second)

    assert repository.load_draft(second.draft.id) == second


def test_rejects_duplicate_cube_version_id_with_changed_snapshot(tmp_path) -> None:
    state, version = _state()
    repository = SQLiteDraftRepository(tmp_path / "drafts.sqlite3")
    repository.save_draft(version, state)
    changed = CubeVersion(
        version.id, Cube(version.cube.id, "Changed Cube"), version.cards
    )

    with pytest.raises(PersistenceConflict, match="CubeVersion snapshots"):
        repository.save_draft(changed, state)


def test_rejects_allocation_memberships_absent_from_the_cube_version(tmp_path) -> None:
    state, version = _state()
    first = state.allocation[0]
    invalid_first = AllocatedPack(
        first.pack,
        (
            DraftCardInstance(first.cards[0].id, state.draft.id, "unknown-membership"),
            first.cards[1],
        ),
    )
    invalid_state = start_draft(state.draft, (invalid_first, *state.allocation[1:]))

    with pytest.raises(PersistenceError, match="CubeVersion cards"):
        SQLiteDraftRepository(tmp_path / "drafts.sqlite3").save_draft(
            version, invalid_state
        )


def test_rejects_unsupported_sqlite_version(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 36, 0))

    with pytest.raises(PersistenceError, match="3.37"):
        SQLiteDraftRepository(tmp_path / "drafts.sqlite3")


def test_pick_and_consecutive_bot_turns_roll_back_as_one_transaction(tmp_path) -> None:
    state, version = _state()
    database_path = tmp_path / "drafts.sqlite3"
    SQLiteDraftRepository(database_path).save_draft(version, state)
    failing = SQLiteDraftRepository(
        database_path,
        before_commit=lambda: (_ for _ in ()).throw(RuntimeError("injected failure")),
    )

    with pytest.raises(RuntimeError, match="injected failure"):
        submit_human_pick_and_advance_bots(
            failing,
            state.draft.id,
            0,
            available_cards(state, 0)[0].id,
            {1: _strategy()},
        )

    assert SQLiteDraftRepository(database_path).load_draft(state.draft.id) == state


def test_pick_and_consecutive_bot_turns_persist_as_one_draft_update(tmp_path) -> None:
    state, version = _state()
    database_path = tmp_path / "drafts.sqlite3"
    repository = SQLiteDraftRepository(database_path)
    repository.save_draft(version, state)

    updated = submit_human_pick_and_advance_bots(
        repository,
        state.draft.id,
        0,
        available_cards(state, 0)[0].id,
        {1: _strategy()},
    )

    assert [event.actor_origin for event in updated.pick_events] == [
        ActorOrigin.HUMAN,
        ActorOrigin.BOT,
    ]
    assert SQLiteDraftRepository(database_path).load_draft(state.draft.id) == updated
