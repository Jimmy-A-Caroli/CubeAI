import pytest
from cubeai.lab.domain import Cube, CubeCard, CubeVersion, ResolutionStatus, DraftConfiguration, allocate_packs, InsufficientCubeCapacity

def version(size: int) -> CubeVersion:
    return CubeVersion("v", Cube("c", "Cube"), tuple(CubeCard(f"m{i}", ResolutionStatus.UNRESOLVED) for i in range(size)))

def test_allocation_is_deterministic_and_configurable() -> None:
    config = DraftConfiguration(2, 2, 3, 42)
    first = allocate_packs("d", version(12), config)
    second = allocate_packs("d", version(12), config)
    assert first == second and len(first) == 4 and all(len(p.cards) == 3 for p in first)
    assert allocate_packs("d", version(12), DraftConfiguration(2, 2, 3, 43)) != first

def test_duplicate_memberships_are_distinct_and_capacity_is_checked() -> None:
    allocated = allocate_packs("d", version(6), DraftConfiguration(1, 1, 6, 1))
    assert len({card.cube_card_id for card in allocated[0].cards}) == 6
    with pytest.raises(InsufficientCubeCapacity):
        allocate_packs("d", version(5), DraftConfiguration(1, 1, 6, 1))
