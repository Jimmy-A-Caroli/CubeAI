"""Storage ports for immutable Cube versions and append-only draft histories."""

from collections.abc import Callable
from typing import Protocol

from cubeai.lab.domain.cube import CubeVersion
from cubeai.lab.domain.draft_state import DraftState


DraftTransaction = Callable[[DraftState, CubeVersion], DraftState]


class DraftRepository(Protocol):
    def save_cube_version(self, cube_version: CubeVersion) -> None: ...

    def save_draft(self, cube_version: CubeVersion, state: DraftState) -> None: ...

    def load_cube_version(self, cube_version_id: str) -> CubeVersion | None: ...

    def load_draft(self, draft_id: str) -> DraftState | None: ...

    def transact(self, draft_id: str, transition: DraftTransaction) -> DraftState: ...

    def track_card_instance(
        self, draft_id: str, observer_seat: int, card_instance_id: str
    ) -> None: ...

    def untrack_card_instance(
        self, draft_id: str, observer_seat: int, card_instance_id: str
    ) -> None: ...

    def load_tracked_card_instance_ids(
        self, draft_id: str, observer_seat: int
    ) -> tuple[str, ...]: ...
