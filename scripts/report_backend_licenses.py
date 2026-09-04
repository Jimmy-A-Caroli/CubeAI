"""Report licenses for every registry package recorded in a uv lockfile."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime
from pathlib import Path

import tomllib

UNKNOWN_LICENSE = "UNKNOWN"


def normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def read_policy(path: Path) -> tuple[set[str], Mapping[str, object]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    allowed = document.get("allowed_license_expressions")
    allowlist = document.get("allowlist")
    if not isinstance(allowed, list) or not all(
        isinstance(item, str) for item in allowed
    ):
        raise ValueError("policy allowed_license_expressions must be a list of strings")
    if not isinstance(allowlist, dict):
        raise TypeError("policy allowlist must be an object")
    return set(allowed), allowlist


def registry_packages(lock_path: Path) -> list[tuple[str, str]]:
    lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    packages = lock.get("package")
    if not isinstance(packages, list):
        raise TypeError("uv lockfile has no package list")

    resolved: list[tuple[str, str]] = []
    for package in packages:
        if not isinstance(package, dict):
            continue
        source = package.get("source")
        name = package.get("name")
        version = package.get("version")
        if (
            isinstance(source, dict)
            and "registry" in source
            and isinstance(name, str)
            and isinstance(version, str)
        ):
            resolved.append((name, version))
    return sorted(
        resolved, key=lambda package: (normalized_name(package[0]), package[1])
    )


def license_from_metadata(
    name: str, version: str, paths: Iterable[Path] | None = None
) -> str:
    discovery_arguments = {} if paths is None else {"path": list(paths)}
    for distribution in importlib.metadata.distributions(**discovery_arguments):
        metadata = distribution.metadata
        metadata_name = metadata.get("Name")
        metadata_version = metadata.get("Version")
        if (
            isinstance(metadata_name, str)
            and normalized_name(metadata_name) == normalized_name(name)
            and metadata_version == version
        ):
            expression = metadata.get("License-Expression") or metadata.get("License")
            if isinstance(expression, str) and expression.strip():
                return " ".join(expression.split())
            return UNKNOWN_LICENSE
    return UNKNOWN_LICENSE


def review_status(
    package_key: str,
    license_expression: str,
    allowed: set[str],
    allowlist: Mapping[str, object],
) -> str:
    if license_expression in allowed:
        return "ALLOWED"
    exception = allowlist.get(package_key)
    if not isinstance(exception, dict):
        return "REVIEW_REQUIRED"
    required = ("license", "reason", "reviewed_by", "expires_on")
    if not all(
        isinstance(exception.get(field), str) and exception[field].strip()
        for field in required
    ):
        return "REVIEW_REQUIRED"
    if exception["license"] != license_expression:
        return "REVIEW_REQUIRED"
    try:
        expires_on = date.fromisoformat(exception["expires_on"])
    except ValueError:
        return "REVIEW_REQUIRED"
    return (
        "ALLOWLISTED" if expires_on >= datetime.now(UTC).date() else "REVIEW_REQUIRED"
    )


def report(
    lock_path: Path, policy_path: Path, metadata_paths: Iterable[Path] | None = None
) -> int:
    allowed, allowlist = read_policy(policy_path)
    rows: list[tuple[str, str, str, str]] = []
    for name, version in registry_packages(lock_path):
        license_expression = license_from_metadata(name, version, metadata_paths)
        package_key = f"backend:{normalized_name(name)}@{version}"
        status = review_status(package_key, license_expression, allowed, allowlist)
        rows.append((name, version, license_expression, status))

    print("workspace\tpackage\tversion\tlicense\tstatus")
    for name, version, license_expression, status in rows:
        print(f"backend\t{name}\t{version}\t{license_expression}\t{status}")

    failures = [row for row in rows if row[-1] == "REVIEW_REQUIRED"]
    if failures:
        print(f"REVIEW REQUIRED: {len(failures)} backend package(s)", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lock", type=Path, default=repository_root / "backend" / "uv.lock"
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=repository_root / "config" / "dependency-license-policy.json",
    )
    parser.add_argument(
        "--metadata-path",
        type=Path,
        action="append",
        dest="metadata_paths",
        help="Use this distribution metadata directory instead of the locked environment.",
    )
    arguments = parser.parse_args()
    return report(arguments.lock, arguments.policy, arguments.metadata_paths)


if __name__ == "__main__":
    raise SystemExit(main())
