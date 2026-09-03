"""Tests for the cross-platform repository command runner."""

import importlib.util
import subprocess
from collections.abc import Sequence
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[2] / "scripts" / "cubeai.py"
SPEC = importlib.util.spec_from_file_location("cubeai_root_commands", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
ROOT_COMMANDS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROOT_COMMANDS)


def test_aggregate_runner_stops_and_returns_a_controlled_child_failure() -> None:
    calls: list[Sequence[str]] = []

    def controlled_runner(
        command: Sequence[str],
    ) -> subprocess.CompletedProcess[object]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 23 if len(calls) == 2 else 0)

    exit_code = ROOT_COMMANDS.run_steps(
        (("first-child",), ("failing-child",), ("unreached-child",)),
        controlled_runner,
    )

    assert exit_code == 23
    assert calls == [("first-child",), ("failing-child",)]


def test_backend_format_and_check_commands_keep_the_lockfile_guard() -> None:
    commands = ROOT_COMMANDS.COMMANDS["format"] + ROOT_COMMANDS.COMMANDS["check"]
    backend_commands = [
        command
        for command in commands
        if command[:4] == ("uv", "--directory", "backend", "run")
    ]

    assert backend_commands
    assert all(command[4] == "--locked" for command in backend_commands)
