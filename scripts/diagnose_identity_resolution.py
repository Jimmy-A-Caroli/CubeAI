"""Write a local, exact-ID identity-resolution diagnostic report.

This recovery tool never assigns strategy, changes an assignment artifact, or
persists provider card payloads.  The report identifies only membership keys,
source UUID evidence, resolver outcomes, and parser diagnostics so a human can
review unresolved records without name matching or inferred substitutions.

Example from the repository root:

    uv --directory backend run --locked python ../scripts/diagnose_identity_resolution.py \
      --identifier modovintage --output ../cubeai-local/modovintage-identity-diagnostic.json
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from cubeai.lab.adapters.cubecobra import CubeCobraSource  # noqa: E402
from cubeai.lab.adapters.scryfall import (  # noqa: E402
    ScryfallMetadataResolver,
    SQLiteScryfallCache,
)
from cubeai.lab.application import SourceRequest, assemble_cube_version  # noqa: E402


def _counts(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _is_uuid(value: str | None) -> bool:
    if value is None:
        return False
    try:
        UUID(value)
    except ValueError:
        return False
    return True


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifier", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    imported = CubeCobraSource().import_cube(
        SourceRequest("cubecobra", arguments.identifier)
    )
    if imported.snapshot is None:
        raise RuntimeError("source import did not produce a snapshot")

    with TemporaryDirectory(prefix="cubeai-identity-diagnostic-") as temporary:
        resolver = ScryfallMetadataResolver(
            SQLiteScryfallCache(Path(temporary) / "scryfall-cache.sqlite3")
        )
        resolution = resolver.resolve(imported.candidates)
    assembly = assemble_cube_version(
        imported,
        resolution,
        cube_id=f"cubecobra:{imported.snapshot.snapshot_id}",
        cube_name=f"CubeCobra {arguments.identifier}",
    )
    unresolved = [
        {
            "membership_key": item.candidate.membership_key,
            "position": item.candidate.position,
            "printing_id": item.candidate.printing_hint,
            "oracle_id": item.candidate.oracle_id,
            "outcome": (
                "resolved_printing_missing_oracle_identity"
                if item.printing is not None and item.printing.oracle_id is None
                else item.outcome.value
            ),
            "diagnostics": [
                {"code": diagnostic.code.value, "message": diagnostic.message}
                for diagnostic in item.diagnostics
            ],
        }
        for item in resolution.resolutions
        if item.printing is None or item.printing.oracle_id is None
    ]
    report = {
        "artifact_type": "cubeai.identity-resolution-diagnostic",
        "schema_version": 1,
        "capture_mode": "online_exact_lookup",
        "cache": "ephemeral_empty_cache",
        "source": {
            "name": imported.snapshot.source,
            "snapshot_id": imported.snapshot.snapshot_id,
            "retrieved_at": imported.snapshot.retrieved_at,
            "request_identifier": imported.snapshot.request_identifier,
        },
        "candidate_identity_evidence": {
            "total": len(imported.candidates),
            "valid_printing_uuid": sum(
                _is_uuid(item.printing_hint) for item in imported.candidates
            ),
            "valid_oracle_uuid": sum(
                _is_uuid(item.oracle_id) for item in imported.candidates
            ),
        },
        "resolution": {
            "snapshot_id": resolution.snapshot_id,
            "outcomes": _counts([item.outcome.value for item in resolution.resolutions]),
            "resolved_card_identities": sum(
                item.printing is not None and item.printing.oracle_id is not None
                for item in resolution.resolutions
            ),
            "unresolved_memberships": unresolved,
        },
        "assembly": {
            "outcome": assembly.outcome.value,
            "cube_version_id": (
                assembly.cube_version.id if assembly.cube_version is not None else None
            ),
        },
    }
    _write_json(arguments.output, report)
    print(json.dumps({"output": str(arguments.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
