"""Focused tests for deterministic allocation from validated CubeVersions."""

from dataclasses import FrozenInstanceError

import pytest

from cubeai.lab.domain import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    DraftConfiguration,
    InsufficientCubeCapacity,
    ResolutionStatus,
    allocate_packs,
    validate_cube_version,
)


def _membership(membership_id: str, *, printing_id: str) -> CubeCard:
    identity = CardIdentity(
        id=f"oracle:{printing_id}",
        name=f"Synthetic {printing_id}",
        resolution_status=ResolutionStatus.RESOLVED,
        oracle_id=f"oracle:{printing_id}",
    )
    return CubeCard(
        membership_id,
        ResolutionStatus.RESOLVED,
        CardPrinting(printing_id, identity),
    )


def _version(size: int) -> CubeVersion:
    return CubeVersion(
        "version-1",
        Cube("cube-1", "Synthetic Cube"),
        tuple(
            _membership(f"membership-{index}", printing_id=f"printing-{index}")
            for index in range(size)
        ),
    )


def _validation(version: CubeVersion, configuration: DraftConfiguration):
    return validate_cube_version(version, configuration)


def _membership_ids(allocation: object) -> tuple[str, ...]:
    assert isinstance(allocation, tuple)
    return tuple(
        instance.cube_card_id
        for allocated_pack in allocation
        for instance in allocated_pack.cards
    )


def test_allocation_is_deterministic_and_uses_validation_geometry() -> None:
    version = _version(12)
    configuration = DraftConfiguration(2, 2, 3, 42)
    validation = _validation(version, configuration)

    first = allocate_packs("draft-1", version, validation)
    second = allocate_packs("draft-1", version, validation)

    assert first == second
    assert len(first) == 4
    assert all(len(pack.cards) == 3 for pack in first)
    assert [pack.pack.owner_seat for pack in first] == [0, 1, 0, 1]


def test_different_seed_changes_a_nontrivial_allocation() -> None:
    version = _version(12)
    first = allocate_packs(
        "draft-1", version, _validation(version, DraftConfiguration(2, 2, 3, 42))
    )
    second = allocate_packs(
        "draft-1", version, _validation(version, DraftConfiguration(2, 2, 3, 43))
    )

    assert _membership_ids(first) != _membership_ids(second)


def test_membership_accounting_preserves_duplicates_and_excess_policy() -> None:
    version = CubeVersion(
        "version-duplicates",
        Cube("cube-1", "Synthetic Cube"),
        (
            _membership("membership-1", printing_id="printing-1"),
            _membership("membership-2", printing_id="printing-1"),
            _membership("membership-3", printing_id="printing-2"),
            _membership("membership-4", printing_id="printing-3"),
        ),
    )
    configuration = DraftConfiguration(1, 1, 3, 1)
    allocation = allocate_packs("draft-1", version, _validation(version, configuration))

    membership_ids = _membership_ids(allocation)
    assert len(membership_ids) == 3
    assert len(set(membership_ids)) == 3
    assert set(membership_ids).issubset({card.id for card in version.cards})
    assert len({instance.id for pack in allocation for instance in pack.cards}) == 3


def test_insufficient_or_blocking_validation_cannot_allocate() -> None:
    small = _version(2)
    configuration = DraftConfiguration(1, 1, 3, 1)
    with pytest.raises(InsufficientCubeCapacity):
        allocate_packs("draft-1", small, _validation(small, configuration))

    unresolved = CubeVersion(
        "version-unresolved",
        Cube("cube-1", "Synthetic Cube"),
        (
            _membership("membership-1", printing_id="printing-1"),
            _membership("membership-2", printing_id="printing-2"),
            _membership("membership-3", printing_id="printing-3"),
            CubeCard("membership-4", ResolutionStatus.UNRESOLVED),
        ),
    )
    with pytest.raises(ValueError, match="blocking"):
        allocate_packs("draft-1", unresolved, _validation(unresolved, configuration))


def test_allocation_rejects_other_version_validation_and_cannot_mutate_inputs() -> None:
    version = _version(3)
    other_version = CubeVersion(
        "version-2", Cube("cube-2", "Other Cube"), version.cards
    )
    validation = _validation(version, DraftConfiguration(1, 1, 3, 1))

    with pytest.raises(ValueError, match="belong"):
        allocate_packs("draft-1", other_version, validation)
    allocation = allocate_packs("draft-1", version, validation)
    with pytest.raises(FrozenInstanceError):
        allocation[0].cards = ()  # type: ignore[misc]
    assert [card.id for card in version.cards] == [
        "membership-0",
        "membership-1",
        "membership-2",
    ]
