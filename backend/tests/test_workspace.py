import pytest

from cubeai.lab.domain.workspace import WorkspaceName


def test_domain_and_application_packages_are_importable() -> None:
    from cubeai.lab import application, domain

    assert application is not None
    assert domain is not None


def test_workspace_name_preserves_a_non_blank_value() -> None:
    assert WorkspaceName("CubeLab").value == "CubeLab"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_workspace_name_rejects_blank_values(value: str) -> None:
    with pytest.raises(ValueError, match="must not be blank"):
        WorkspaceName(value)
