from dataclasses import FrozenInstanceError

import pytest

from cubeai.lab.domain import (
    CardIdentity,
    CardPrinting,
    Cube,
    CubeCard,
    CubeVersion,
    ResolutionStatus,
    SourceReference,
)


def _resolved_identity(identity_id: str = "identity-1") -> CardIdentity:
    return CardIdentity(
        id=identity_id,
        name="Lightning Bolt",
        resolution_status=ResolutionStatus.RESOLVED,
        oracle_id="oracle-1",
    )


def _printing(printing_id: str = "printing-1") -> CardPrinting:
    return CardPrinting(id=printing_id, card_identity=_resolved_identity())


def _membership(membership_id: str = "membership-1") -> CubeCard:
    return CubeCard(
        id=membership_id,
        resolution_status=ResolutionStatus.RESOLVED,
        printing=_printing(),
    )


def test_printing_and_membership_ids_keep_identity_scopes_distinct() -> None:
    card_identity = _resolved_identity()
    first_printing = CardPrinting(id="printing-1", card_identity=card_identity)
    second_printing = CardPrinting(id="printing-2", card_identity=card_identity)
    first_membership = CubeCard(
        id="membership-1",
        resolution_status=ResolutionStatus.RESOLVED,
        printing=first_printing,
    )
    second_membership = CubeCard(
        id="membership-2",
        resolution_status=ResolutionStatus.RESOLVED,
        printing=first_printing,
    )

    version = CubeVersion(
        id="version-1",
        cube=Cube(id="cube-1", name="Test Cube"),
        cards=(first_membership, second_membership),
    )

    assert first_printing != second_printing
    assert first_printing.card_identity is card_identity
    assert second_printing.card_identity is card_identity
    assert first_membership != second_membership
    assert first_membership.printing is second_membership.printing
    assert version.cards == (first_membership, second_membership)


@pytest.mark.parametrize(
    ("instance", "field_name"),
    [
        (SourceReference(source="test", external_id="external-1"), "source"),
        (_resolved_identity(), "id"),
        (_printing(), "id"),
        (Cube(id="cube-1", name="Test Cube"), "id"),
        (_membership(), "id"),
        (
            CubeVersion(
                id="version-1",
                cube=Cube(id="cube-1", name="Test Cube"),
                cards=(_membership(),),
            ),
            "id",
        ),
    ],
)
def test_domain_values_are_frozen(instance: object, field_name: str) -> None:
    with pytest.raises(FrozenInstanceError):
        setattr(instance, field_name, "changed")


def test_cube_version_converts_a_list_to_an_independent_tuple() -> None:
    first_membership = _membership("membership-1")
    source_cards = [first_membership]

    version = CubeVersion(
        id="version-1",
        cube=Cube(id="cube-1", name="Test Cube"),
        cards=source_cards,
    )
    source_cards.append(_membership("membership-2"))

    assert isinstance(version.cards, tuple)
    assert version.cards == (first_membership,)


@pytest.mark.parametrize(
    "status",
    [ResolutionStatus.UNRESOLVED, ResolutionStatus.CUSTOM],
)
def test_nonresolved_identity_does_not_fabricate_an_oracle_id(
    status: ResolutionStatus,
) -> None:
    identity = CardIdentity(
        id="identity-1",
        name="Source-only card",
        resolution_status=status,
        oracle_id=None,
    )

    assert identity.oracle_id is None


@pytest.mark.parametrize("invalid_status", ["resolved", None, 17])
@pytest.mark.parametrize(
    "factory",
    [
        lambda invalid_status: CardIdentity(
            id="identity-1",
            name="Lightning Bolt",
            resolution_status=invalid_status,
        ),
        lambda invalid_status: CubeCard(
            id="membership-1",
            resolution_status=invalid_status,
        ),
    ],
    ids=["identity", "membership"],
)
def test_identity_and_membership_reject_invalid_resolution_status(
    factory,
    invalid_status,
) -> None:
    with pytest.raises(ValueError, match="resolution_status"):
        factory(invalid_status)


@pytest.mark.parametrize("invalid_id", ["", "   ", 17])
@pytest.mark.parametrize(
    "factory",
    [
        lambda invalid_id: CardIdentity(
            id=invalid_id,
            name="Lightning Bolt",
            resolution_status=ResolutionStatus.RESOLVED,
            oracle_id="oracle-1",
        ),
        lambda invalid_id: CardPrinting(
            id=invalid_id,
            card_identity=_resolved_identity(),
        ),
        lambda invalid_id: Cube(id=invalid_id, name="Test Cube"),
        lambda invalid_id: CubeCard(
            id=invalid_id,
            resolution_status=ResolutionStatus.RESOLVED,
            printing=_printing(),
        ),
        lambda invalid_id: CubeVersion(
            id=invalid_id,
            cube=Cube(id="cube-1", name="Test Cube"),
            cards=(),
        ),
    ],
    ids=["identity", "printing", "cube", "membership", "version"],
)
def test_local_ids_reject_blank_or_nonstring_values(factory, invalid_id) -> None:
    with pytest.raises(ValueError, match="id"):
        factory(invalid_id)


@pytest.mark.parametrize("field_name", ["source", "external_id"])
@pytest.mark.parametrize("invalid_value", ["", "   ", None])
def test_source_reference_rejects_blank_or_nonstring_fields(
    field_name: str,
    invalid_value: object,
) -> None:
    values = {"source": "test", "external_id": "external-1"}
    values[field_name] = invalid_value

    with pytest.raises(ValueError, match=field_name):
        SourceReference(**values)


@pytest.mark.parametrize("invalid_oracle_id", ["", "   ", 17])
def test_resolved_identity_rejects_blank_or_nonstring_oracle_id(
    invalid_oracle_id,
) -> None:
    with pytest.raises(ValueError, match="oracle_id"):
        CardIdentity(
            id="identity-1",
            name="Lightning Bolt",
            resolution_status=ResolutionStatus.RESOLVED,
            oracle_id=invalid_oracle_id,
        )


def test_resolved_identity_requires_an_oracle_id() -> None:
    with pytest.raises(ValueError, match="oracle_id"):
        CardIdentity(
            id="identity-1",
            name="Lightning Bolt",
            resolution_status=ResolutionStatus.RESOLVED,
        )


@pytest.mark.parametrize(
    "status",
    [ResolutionStatus.UNRESOLVED, ResolutionStatus.CUSTOM],
)
def test_nonresolved_identity_rejects_an_oracle_id(
    status: ResolutionStatus,
) -> None:
    with pytest.raises(ValueError, match="oracle_id"):
        CardIdentity(
            id="identity-1",
            name="Source-only card",
            resolution_status=status,
            oracle_id="oracle-1",
        )


def test_resolved_membership_requires_a_printing() -> None:
    with pytest.raises(ValueError, match="printing"):
        CubeCard(
            id="membership-1",
            resolution_status=ResolutionStatus.RESOLVED,
        )


@pytest.mark.parametrize(
    "status",
    [ResolutionStatus.UNRESOLVED, ResolutionStatus.CUSTOM],
)
def test_nonresolved_membership_rejects_a_printing(
    status: ResolutionStatus,
) -> None:
    with pytest.raises(ValueError, match="printing"):
        CubeCard(
            id="membership-1",
            resolution_status=status,
            printing=_printing(),
        )


def test_cube_version_rejects_duplicate_membership_ids() -> None:
    with pytest.raises(ValueError, match="duplicate.*CubeCard.id"):
        CubeVersion(
            id="version-1",
            cube=Cube(id="cube-1", name="Test Cube"),
            cards=(_membership("membership-1"), _membership("membership-1")),
        )
