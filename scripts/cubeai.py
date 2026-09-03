"""Run CubeAI's documented repository-level development commands.

Invoke this script through the locked backend environment so it works the same
way on supported Windows, macOS, and Linux hosts:

    uv --directory backend run --locked python ../scripts/cubeai.py check
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Command = tuple[str, ...]
CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[object]]
COREPACK = "corepack.cmd" if sys.platform == "win32" else "corepack"

COMMANDS: dict[str, tuple[Command, ...]] = {
    "setup": (
        ("uv", "--directory", "backend", "sync", "--locked", "--all-groups"),
        (COREPACK, "npm", "--prefix", "frontend", "ci"),
    ),
    "format": (
        ("uv", "--directory", "backend", "run", "ruff", "format", "."),
        (COREPACK, "npm", "--prefix", "frontend", "run", "format"),
    ),
    "check": (
        ("uv", "--directory", "backend", "run", "ruff", "format", "--check", "."),
        ("uv", "--directory", "backend", "run", "ruff", "check", "."),
        ("uv", "--directory", "backend", "run", "mypy", "--strict", "src"),
        ("uv", "--directory", "backend", "run", "lint-imports"),
        (COREPACK, "npm", "--prefix", "frontend", "run", "format:check"),
        (COREPACK, "npm", "--prefix", "frontend", "run", "lint"),
        (COREPACK, "npm", "--prefix", "frontend", "run", "typecheck"),
    ),
    "test": (
        ("uv", "--directory", "backend", "run", "--locked", "pytest", "-q", "tests"),
        (COREPACK, "npm", "--prefix", "frontend", "test"),
    ),
}

DEV_COMMANDS: tuple[Command, Command] = (
    ("uv", "--directory", "backend", "run", "--locked", "python", "-m", "cubeai.api"),
    (COREPACK, "npm", "--prefix", "frontend", "run", "dev", "--", "--host", "127.0.0.1"),
)


def run_steps(
    steps: Sequence[Command],
    run_command: CommandRunner | None = None,
) -> int:
    """Run each command in order and preserve the first nonzero exit status."""
    runner = run_command or _run_command
    for command in steps:
        print(f"+ {subprocess.list2cmdline(command)}", flush=True)
        try:
            result = runner(command)
        except OSError as error:
            print(f"Could not start {command[0]!r}: {error}", file=sys.stderr)
            return 127
        if result.returncode:
            print(
                f"Command failed with exit status {result.returncode}: "
                f"{subprocess.list2cmdline(command)}",
                file=sys.stderr,
            )
            return result.returncode
    return 0


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[object]:
    return subprocess.run(command, cwd=ROOT, check=False)


def run_development_servers() -> int:
    """Run the local health server and Vite together until either exits."""
    processes: list[subprocess.Popen[object]] = []
    try:
        for command in DEV_COMMANDS:
            print(f"+ {subprocess.list2cmdline(command)}", flush=True)
            processes.append(subprocess.Popen(command, cwd=ROOT))

        while True:
            for process, command in zip(processes, DEV_COMMANDS, strict=True):
                exit_code = process.poll()
                if exit_code is not None:
                    if exit_code:
                        print(
                            f"Development command failed with exit status {exit_code}: "
                            f"{subprocess.list2cmdline(command)}",
                            file=sys.stderr,
                        )
                    return exit_code
            time.sleep(0.1)
    except KeyboardInterrupt:
        return 130
    except OSError as error:
        print(f"Could not start development command: {error}", file=sys.stderr)
        return 127
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            if process.poll() is None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=(*COMMANDS, "dev"))
    command = parser.parse_args().command
    if command == "dev":
        return run_development_servers()
    return run_steps(COMMANDS[command])


if __name__ == "__main__":
    raise SystemExit(main())
