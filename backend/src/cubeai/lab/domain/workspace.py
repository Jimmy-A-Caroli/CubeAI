"""Domain value objects for the CubeLab workspace."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceName:
    """A non-blank CubeLab workspace name."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Workspace name must not be blank")
