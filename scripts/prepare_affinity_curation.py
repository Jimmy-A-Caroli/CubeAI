"""Capture one source snapshot and create a human affinity-curation baseline.

The command records the immutable CubeVersion only in caller-local SQLite and
emits a compact artifact and coverage report.  It never writes provider tags,
card text, names, images, or inferred associations into the reviewed outputs.

Example:
    uv --directory backend run --locked python ../scripts/prepare_affinity_curation.py \
      --identifier modovintage --state-directory ../cubeai-local \
      --worklist ../cubeai-local/modovintage-affinity-worklist.json \
      --artifact ../docs/artifacts/archetype-affinities/modovintage-affinities-v1.json \
      --coverage ../docs/artifacts/archetype-affinities/modovintage-affinities-v1-coverage.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from cubeai.lab.adapters.cubecobra import CubeCobraSource
from cubeai.lab.adapters.scryfall import ScryfallMetadataResolver, SQLiteScryfallCache
from cubeai.lab.adapters.sqlite_drafts import SQLiteDraftRepository
from cubeai.lab.application.affinity_curation import (
    assignment_artifact_document,
    coverage_report_document,
    curation_worklist_document,
    empty_assignment_set,
)
from cubeai.lab.application.local_imports import import_local_cube


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifier", required=True)
    parser.add_argument("--state-directory", type=Path, required=True)
    parser.add_argument(
        "--worklist",
        type=Path,
        required=True,
        help="Caller-local worklist; do not commit it as a provider-data export.",
    )
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--assignment-set-id", required=True)
    parser.add_argument("--offline", action="store_true")
    arguments = parser.parse_args()

    state_directory = arguments.state_directory
    repository = SQLiteDraftRepository(state_directory / "drafts.sqlite3")
    resolver = ScryfallMetadataResolver(
        SQLiteScryfallCache(state_directory / "scryfall-cache.sqlite3")
    )
    local_import = import_local_cube(
        repository,
        CubeCobraSource(),
        resolver,
        source_name="cubecobra",
        identifier=arguments.identifier,
        cube_name=f"CubeCobra {arguments.identifier}",
        offline=arguments.offline,
    )
    if local_import.assembly is None or local_import.assembly.cube_version is None:
        raise RuntimeError("source snapshot could not be assembled into a CubeVersion")

    version = local_import.assembly.cube_version
    assignment_set = empty_assignment_set(
        version, assignment_set_id=arguments.assignment_set_id
    )
    _write_json(arguments.worklist, curation_worklist_document(version))
    _write_json(arguments.artifact, assignment_artifact_document(assignment_set))
    _write_json(arguments.coverage, coverage_report_document(assignment_set, version))
    print(
        json.dumps(
            {
                "cube_version_id": version.id,
                "assembly_outcome": local_import.assembly.outcome.value,
                "worklist": str(arguments.worklist),
                "artifact": str(arguments.artifact),
                "coverage": str(arguments.coverage),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
