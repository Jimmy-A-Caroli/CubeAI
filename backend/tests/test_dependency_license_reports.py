"""Offline guardrails for the lock-backed dependency license report."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPORT_SCRIPT = REPOSITORY_ROOT / "scripts" / "report_backend_licenses.py"


def load_report_module() -> object:
    specification = importlib.util.spec_from_file_location(
        "report_backend_licenses", REPORT_SCRIPT
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_unknown_license_requires_review() -> None:
    module = load_report_module()

    assert module.review_status("backend:unlicensed@1.0.0", "UNKNOWN", {"MIT"}, {}) == (
        "REVIEW_REQUIRED"
    )


def test_metadata_lookup_requires_normalized_name_and_locked_version(
    tmp_path: Path,
) -> None:
    module = load_report_module()
    metadata_path = tmp_path / "metadata"
    distribution_info = metadata_path / "Unlicensed-9.9.9.dist-info"
    distribution_info.mkdir(parents=True)
    (distribution_info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: Unlicensed\nVersion: 9.9.9\nLicense: MIT\n",
        encoding="utf-8",
    )

    assert (
        module.license_from_metadata("unlicensed", "1.0.0", [metadata_path])
        == "UNKNOWN"
    )
    assert module.license_from_metadata("unlicensed", "9.9.9", [metadata_path]) == "MIT"


def test_report_surfaces_a_controlled_unknown_license(tmp_path: Path) -> None:
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(
        """version = 1
revision = 3
requires-python = \">=3.14\"

[[package]]
name = \"unlicensed\"
version = \"1.0.0\"
source = { registry = \"https://pypi.org/simple\" }
""",
        encoding="utf-8",
    )
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        json.dumps({"allowed_license_expressions": ["MIT"], "allowlist": {}}),
        encoding="utf-8",
    )
    metadata_path = tmp_path / "metadata"
    distribution_info = metadata_path / "unlicensed-1.0.0.dist-info"
    distribution_info.mkdir(parents=True)
    (distribution_info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: unlicensed\nVersion: 1.0.0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPORT_SCRIPT),
            "--lock",
            str(lock_path),
            "--policy",
            str(policy_path),
            "--metadata-path",
            str(metadata_path),
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 1
    assert "backend\tunlicensed\t1.0.0\tUNKNOWN\tREVIEW_REQUIRED" in result.stdout
    assert "REVIEW REQUIRED: 1 backend package(s)" in result.stderr
