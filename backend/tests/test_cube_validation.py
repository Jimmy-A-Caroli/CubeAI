"""Focused tests for deterministic CubeVersion validation."""

from dataclasses import FrozenInstanceError

import pytest

from cubeai.lab.domain import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeValidationCode,
    CubeValidationSeverity,
    CubeVersion,
    DraftConfiguration,
    ResolutionStatus,
    validate_cube_version,
)


def _resolved_membership(
    membership_id: str, *, printing_id: str = "printing-1"
) -> CubeCard:
    identity = CardIdentity(
        id="oracle-1",
        name="Synthetic Ember",
        resolution_status=ResolutionStatus.RESOLVED,
        oracle_id="oracle-1",
    )
    return CubeCard(
        membership_id,
        ResolutionStatus.RESOLVED,
        CardPrinting(printing_id, identity),
    )


def _version(*cards: CubeCard) -> CubeVersion:
    return CubeVersion("version-1", Cube("cube-1", "Synthetic Cube"), cards)


def _configuration() -> DraftConfiguration:
    return DraftConfiguration(seats=1, packs_per_seat=1, pack_size=3, seed=1)


def test_exact_resolved_capacity_is_draftable() -> None:
    result = validate_cube_version(
        _version(
            _resolved_membership("membership-1"),
            _resolved_membership("membership-2"),
            _resolved_membership("membership-3"),
        ),
        _configuration(),
    )

    assert result.is_draftable
    assert result.cube_version_fingerprint == "version-1"
    assert result.usable_membership_count == 3
    assert result.diagnostics == ()


def test_insufficient_resolved_memberships_is_a_stable_error() -> None:
    result = validate_cube_version(
        _version(
            _resolved_membership("membership-1"),
            _resolved_membership("membership-2"),
        ),
        _configuration(),
    )

    assert not result.is_draftable
    assert [(item.code, item.severity) for item in result.diagnostics] == [
        (
            CubeValidationCode.INSUFFICIENT_USABLE_MEMBERSHIPS,
            CubeValidationSeverity.ERROR,
        )
    ]
    assert "requires 3 resolved memberships" in result.diagnostics[0].message
    assert (
        "1 seat(s) x 1 pack(s)/seat x 3 card(s)/pack" in result.diagnostics[0].message
    )


def test_excess_resolved_memberships_are_permitted_with_explicit_policy() -> None:
    result = validate_cube_version(
        _version(
            _resolved_membership("membership-1"),
            _resolved_membership("membership-2"),
            _resolved_membership("membership-3"),
            _resolved_membership("membership-4"),
        ),
        _configuration(),
    )

    assert result.is_draftable
    assert [(item.code, item.severity) for item in result.diagnostics] == [
        (
            CubeValidationCode.EXCESS_USABLE_MEMBERSHIPS,
            CubeValidationSeverity.INFO,
        )
    ]
    assert "deferred to M1-010" in result.diagnostics[0].message
    assert (
        "1 seat(s) x 1 pack(s)/seat x 3 card(s)/pack" in result.diagnostics[0].message
    )


def test_duplicate_printings_are_distinct_valid_memberships() -> None:
    result = validate_cube_version(
        _version(
            _resolved_membership("membership-1", printing_id="printing-1"),
            _resolved_membership("membership-2", printing_id="printing-1"),
            _resolved_membership("membership-3", printing_id="printing-2"),
        ),
        _configuration(),
    )

    assert result.is_draftable
    assert result.usable_membership_count == 3


def test_unresolved_and_custom_memberships_are_actionable_errors_without_mutation() -> (
    None
):
    version = _version(
        _resolved_membership("membership-1"),
        CubeCard("membership-2", ResolutionStatus.UNRESOLVED),
        CubeCard("membership-3", ResolutionStatus.CUSTOM),
    )
    first = validate_cube_version(version, _configuration())
    second = validate_cube_version(version, _configuration())

    assert first == second
    assert not first.is_draftable
    assert [(item.code, item.membership_id) for item in first.diagnostics] == [
        (CubeValidationCode.UNRESOLVED_MEMBERSHIP, "membership-2"),
        (CubeValidationCode.CUSTOM_MEMBERSHIP, "membership-3"),
        (CubeValidationCode.INSUFFICIENT_USABLE_MEMBERSHIPS, None),
    ]
    with pytest.raises(FrozenInstanceError):
        first.usable_membership_count = 0  # type: ignore[misc]
    assert [card.id for card in version.cards] == [
        "membership-1",
        "membership-2",
        "membership-3",
    ]


@pytest.mark.parametrize("field", ["seats", "packs_per_seat", "pack_size"])
def test_zero_draft_geometry_is_rejected_before_validation(field: str) -> None:
    values = {"seats": 1, "packs_per_seat": 1, "pack_size": 1, "seed": 1}
    values[field] = 0

    with pytest.raises(ValueError, match=field):
        DraftConfiguration(**values)
