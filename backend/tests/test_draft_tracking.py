import sqlite3
import shutil

import pytest

from cubeai.lab.adapters import SQLiteDraftRepository
from cubeai.lab.application import (
    DraftTrackingError,
    TrackingPersistenceError,
    track_card,
    tracked_cards,
    untrack_card,
)
from cubeai.lab.application.draft_observations import derive_draft_observations
from cubeai.lab.application.wheel_observations import derive_wheel_observations
from cubeai.lab.domain import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    Draft,
    DraftConfiguration,
    ResolutionStatus,
    allocate_packs,
    available_cards,
    pick_card,
    start_draft,
    validate_cube_version,
)


def _version() -> CubeVersion:
    return CubeVersion(
        "tracking-version",
        Cube("tracking-cube", "Synthetic Tracking Cube"),
        tuple(
            CubeCard(
                f"membership-{index}",
                ResolutionStatus.RESOLVED,
                CardPrinting(
                    "printing-shared" if index < 2 else f"printing-{index}",
                    CardIdentity(
                        "identity-shared" if index < 2 else f"identity-{index}",
                        "Shared Card" if index < 2 else f"Synthetic {index}",
                        ResolutionStatus.RESOLVED,
                        "oracle-shared" if index < 2 else f"oracle-{index}",
                    ),
                ),
            )
            for index in range(6)
        ),
    )


def _state():
    version = _version()
    draft = Draft("tracking-draft", version.id, DraftConfiguration(2, 1, 3, 19))
    return (
        start_draft(
            draft,
            allocate_packs(
                draft.id, version, validate_cube_version(version, draft.configuration)
            ),
        ),
        version,
    )


def _complete_with_first_legal_card(state):
    while state.active_seat is not None:
        state = pick_card(
            state,
            state.active_seat,
            available_cards(state, state.active_seat)[0].id,
        )
    return state


def test_tracks_distinct_instances_and_reopens_with_equal_observations_and_wheels(
    tmp_path,
) -> None:
    state, version = _state()
    database_path = tmp_path / "tracking.sqlite3"
    repository = SQLiteDraftRepository(database_path)
    repository.save_draft(version, state)

    completed = _complete_with_first_legal_card(state)
    repository.save_draft(version, completed)
    before_observations = derive_draft_observations(completed)
    before_wheels = derive_wheel_observations(before_observations)
    shared_targets = tuple(
        card
        for pack in completed.allocation
        for card in pack.cards
        if card.cube_card_id in {"membership-0", "membership-1"}
    )

    for target in shared_targets:
        track_card(repository, state.draft.id, target.id)

    restored_database_path = tmp_path / "restored-tracking.sqlite3"
    shutil.copyfile(database_path, restored_database_path)
    restarted = SQLiteDraftRepository(restored_database_path)
    rehydrated = restarted.load_draft(state.draft.id)

    assert rehydrated == completed
    assert derive_draft_observations(rehydrated) == before_observations
    assert (
        derive_wheel_observations(derive_draft_observations(rehydrated))
        == before_wheels
    )
    assert [
        item.card_instance_id for item in tracked_cards(restarted, state.draft.id)
    ] == sorted(target.id for target in shared_targets)
    assert {target.cube_card_id for target in shared_targets} == {
        "membership-0",
        "membership-1",
    }


def test_migrates_an_existing_v1_database_to_local_tracking(tmp_path) -> None:
    database_path = tmp_path / "v1.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            ) STRICT;
            INSERT INTO schema_migrations(version, applied_at) VALUES (1, 'then');
            CREATE TABLE cube_versions (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            ) STRICT;
            CREATE TABLE drafts (
                id TEXT PRIMARY KEY,
                cube_version_id TEXT NOT NULL,
                initial_payload TEXT NOT NULL,
                events_payload TEXT NOT NULL,
                FOREIGN KEY(cube_version_id) REFERENCES cube_versions(id)
            ) STRICT;
            """
        )

    SQLiteDraftRepository(database_path)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall() == [(1,), (2,)]
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'draft_tracking'"
        ).fetchone() == ("draft_tracking",)


def test_rejects_unseen_or_cross_draft_targets_without_creating_a_marker(
    tmp_path,
) -> None:
    state, version = _state()
    repository = SQLiteDraftRepository(tmp_path / "tracking.sqlite3")
    repository.save_draft(version, state)

    with pytest.raises(DraftTrackingError, match="was not seen"):
        track_card(repository, state.draft.id, "other-draft:card:0:0")
    with pytest.raises(DraftTrackingError, match="was not seen"):
        untrack_card(repository, state.draft.id, "other-draft:card:0:0")
    with pytest.raises(DraftTrackingError, match="was not seen"):
        track_card(repository, state.draft.id, state.allocation[1].cards[0].id)

    assert tracked_cards(repository, state.draft.id) == ()


def test_untrack_is_idempotent_and_preserves_the_draft_event_history(tmp_path) -> None:
    state, version = _state()
    repository = SQLiteDraftRepository(tmp_path / "tracking.sqlite3")
    repository.save_draft(version, state)
    target = available_cards(state, 0)[1]

    track_card(repository, state.draft.id, target.id)
    assert untrack_card(repository, state.draft.id, target.id) == ()
    assert untrack_card(repository, state.draft.id, target.id) == ()
    assert repository.load_draft(state.draft.id) == state


def test_reports_a_dangling_stored_marker_without_mutating_the_draft(tmp_path) -> None:
    state, version = _state()
    database_path = tmp_path / "tracking.sqlite3"
    repository = SQLiteDraftRepository(database_path)
    repository.save_draft(version, state)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO draft_tracking(draft_id, observer_seat, card_instance_id) "
            "VALUES (?, ?, ?)",
            (state.draft.id, 0, "missing-instance"),
        )

    with pytest.raises(TrackingPersistenceError, match="cannot be resolved"):
        tracked_cards(repository, state.draft.id)
    assert repository.load_draft(state.draft.id) == state
