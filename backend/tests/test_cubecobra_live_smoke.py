"""Opt-in, low-frequency live contract smoke check with no response retention."""

from __future__ import annotations

import os

import pytest

from cubeai.lab.adapters.cubecobra import CubeCobraSource
from cubeai.lab.application import ImportOutcome, SourceRequest


pytestmark = pytest.mark.live_smoke


@pytest.mark.skipif(
    os.getenv("CUBEAI_LIVE_SMOKE") != "1",
    reason="set CUBEAI_LIVE_SMOKE=1 to permit the CubeCobra live smoke check",
)
def test_current_public_core_identifier_has_a_supported_contract_shape() -> None:
    result = CubeCobraSource(retries=0).import_cube(
        SourceRequest("cubecobra", "modovintage")
    )

    assert result.outcome in {
        ImportOutcome.SUPPORTED,
        ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT,
    }
    assert result.snapshot is not None
    assert result.candidates
