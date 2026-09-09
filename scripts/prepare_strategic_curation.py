"""Create an exact-version all-UNKNOWN strategic baseline and local worklist.

The committed artifact contains no source display data and no active strategic
assignments.  The caller-local worklist contains only normalized review facts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from cubeai.lab.adapters.cubecobra import CubeCobraSource  # noqa: E402
from cubeai.lab.adapters.scryfall import (  # noqa: E402
    SQLiteScryfallCache,
    ScryfallMetadataResolver,
)
from cubeai.lab.application import SourceRequest, assemble_cube_version  # noqa: E402
from cubeai.lab.application.strategic_curation import (  # noqa: E402
    empty_strategic_assignment_set,
    strategic_assignment_artifact_document,
    strategic_coverage_report_document,
    strategic_curation_worklist_document,
)
from cubeai.lab.application.strategic_proposals import (  # noqa: E402
    load_proposal_set,
    validate_proposal_set,
)


def _write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifier", required=True)
    parser.add_argument("--state-directory", type=Path, required=True)
    parser.add_argument("--expected-cube-version-id", required=True)
    parser.add_argument("--assignment-set-id", required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--worklist", type=Path, required=True)
    parser.add_argument(
        "--proposals",
        type=Path,
        help="Optional separate proposal artifact to validate; it is never activated.",
    )
    arguments = parser.parse_args()

    imported = CubeCobraSource().import_cube(
        SourceRequest("cubecobra", arguments.identifier)
    )
    if imported.snapshot is None:
        raise RuntimeError("source import did not produce a snapshot")
    resolver = ScryfallMetadataResolver(
        SQLiteScryfallCache(arguments.state_directory / "scryfall-cache.sqlite3")
    )
    resolution = resolver.resolve(imported.candidates)
    assembly = assemble_cube_version(
        imported,
        resolution,
        cube_id=f"cubecobra:{imported.snapshot.snapshot_id}",
        cube_name=f"CubeCobra {arguments.identifier}",
    )
    if assembly.cube_version is None:
        raise RuntimeError("source snapshot could not be assembled into a CubeVersion")
    cube_version = assembly.cube_version
    if cube_version.id != arguments.expected_cube_version_id:
        raise RuntimeError(
            "live source/resolution does not match the requested CubeVersion: "
            f"{cube_version.id}"
        )
    assignment_set = empty_strategic_assignment_set(
        cube_version, assignment_set_id=arguments.assignment_set_id
    )
    if arguments.proposals is not None:
        validate_proposal_set(load_proposal_set(arguments.proposals), cube_version)
    _write_json(arguments.artifact, strategic_assignment_artifact_document(assignment_set))
    _write_json(
        arguments.coverage,
        strategic_coverage_report_document(assignment_set, cube_version),
    )
    _write_json(
        arguments.worklist,
        strategic_curation_worklist_document(cube_version, resolution),
    )
    print(
        json.dumps(
            {
                "cube_version_id": cube_version.id,
                "artifact": str(arguments.artifact),
                "coverage": str(arguments.coverage),
                "worklist": str(arguments.worklist),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
