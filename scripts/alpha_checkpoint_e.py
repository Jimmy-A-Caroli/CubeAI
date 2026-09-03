"""Run the Alpha-0 live-source import-to-completed-draft checkpoint.

Example from the repository root:

    uv --directory backend run --locked python ../scripts/alpha_checkpoint_e.py

The script makes one CubeCobra import, then resolves the same source snapshot
twice: first normally and then offline from a temporary Scryfall cache. It
prints aggregate evidence only, never the provider card payload or card list.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

# ``scripts/cubeai.py`` otherwise shadows the installed ``cubeai`` package
# when Python executes this developer harness directly from ``scripts``.
BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from cubeai.lab.adapters.cubecobra import CubeCobraSource
from cubeai.lab.adapters.scryfall import SQLiteScryfallCache, ScryfallMetadataResolver
from cubeai.lab.application import (
    ImportOutcome,
    SourceRequest,
    assemble_cube_version,
)
from cubeai.lab.domain import (
    Draft,
    DraftConfiguration,
    DraftStatus,
    allocate_packs,
    available_cards,
    pick_card,
    pool_for_seat,
    start_draft,
    validate_cube_version,
)


_SUPPORTED_IMPORTS = {
    ImportOutcome.SUPPORTED,
    ImportOutcome.SUPPORTED_WITH_OPTIONAL_DATA_ABSENT,
}


def _counts(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _event_fingerprint(state_events: object) -> str:
    events = [
        {
            "sequence": event.sequence,
            "seat": event.seat_number,
            "pack": event.pack_number,
            "pick": event.pick_number,
            "instance": event.card_instance_id,
            "actor_origin": event.actor_origin.value,
            "actor_id": event.actor_id,
            "strategy_ref": event.strategy_ref,
        }
        for event in state_events
    ]
    encoded = json.dumps(events, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _complete_draft(
    *,
    imported: object,
    resolver: ScryfallMetadataResolver,
    configuration: DraftConfiguration,
    offline: bool,
) -> tuple[dict[str, object], dict[str, int]]:
    resolution = resolver.resolve(imported.candidates, offline=offline)
    assembled = assemble_cube_version(
        imported,
        resolution,
        cube_id=f"cubecobra:{imported.snapshot.snapshot_id}",
        cube_name="live-checkpoint",
    )
    if assembled.cube_version is None:
        raise RuntimeError(f"CubeVersion assembly failed: {assembled.outcome.value}")
    version = assembled.cube_version
    validation = validate_cube_version(version, configuration)
    if not validation.is_draftable:
        raise RuntimeError("CubeVersion is not draftable for the requested geometry")
    draft = Draft(
        id=f"checkpoint-e:{version.content_fingerprint}",
        cube_version_id=version.id,
        configuration=configuration,
    )
    state = start_draft(draft, allocate_packs(draft.id, version, validation))
    while state.status is DraftStatus.IN_PROGRESS:
        assert state.active_seat is not None
        state = pick_card(
            state,
            state.active_seat,
            available_cards(state, state.active_seat)[0].id,
        )
    pools = [
        len(pool_for_seat(state, seat_number).card_instance_ids)
        for seat_number in range(configuration.seats)
    ]
    summary = {
        "cube_version_fingerprint": version.content_fingerprint,
        "validation": {
            "draftable": validation.is_draftable,
            "usable_memberships": validation.usable_membership_count,
            "diagnostics": [diagnostic.code.value for diagnostic in validation.diagnostics],
        },
        "allocation": {
            "pack_count": len(state.allocation),
            "card_instances": sum(len(pack.cards) for pack in state.allocation),
        },
        "draft": {
            "status": state.status.value,
            "event_count": len(state.pick_events),
            "pool_sizes": pools,
            "event_fingerprint": _event_fingerprint(state.pick_events),
        },
    }
    outcomes = _counts([item.outcome.value for item in resolution.resolutions])
    return summary, outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifier", default="modovintage")
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--seats", type=int, default=8)
    parser.add_argument("--packs-per-seat", type=int, default=3)
    parser.add_argument("--pack-size", type=int, default=15)
    parser.add_argument(
        "--cache",
        type=Path,
        help="Optional durable cache directory; otherwise a temporary cache is removed.",
    )
    args = parser.parse_args()
    configuration = DraftConfiguration(
        args.seats, args.packs_per_seat, args.pack_size, args.seed
    )
    imported = CubeCobraSource().import_cube(
        SourceRequest("cubecobra", args.identifier)
    )
    if imported.outcome not in _SUPPORTED_IMPORTS or imported.snapshot is None:
        raise RuntimeError(f"CubeCobra import did not produce a supported snapshot: {imported.outcome.value}")

    temporary_directory: TemporaryDirectory[str] | None = None
    cache_directory = args.cache
    if cache_directory is None:
        temporary_directory = TemporaryDirectory(prefix="cubeai-checkpoint-e-")
        cache_directory = Path(temporary_directory.name)
    try:
        resolver = ScryfallMetadataResolver(
            SQLiteScryfallCache(cache_directory / "scryfall-cache.sqlite3")
        )
        first, first_resolution_outcomes = _complete_draft(
            imported=imported,
            resolver=resolver,
            configuration=configuration,
            offline=False,
        )
        second, cached_resolution_outcomes = _complete_draft(
            imported=imported,
            resolver=resolver,
            configuration=configuration,
            offline=True,
        )
    finally:
        if temporary_directory is not None:
            temporary_directory.cleanup()
    if first != second:
        raise RuntimeError("same source snapshot and inputs produced different drafts")
    print(
        json.dumps(
            {
                "import": {
                    "outcome": imported.outcome.value,
                    "memberships": len(imported.candidates),
                    "diagnostics": [diagnostic.code.value for diagnostic in imported.diagnostics],
                },
                "resolution_outcomes": {
                    "first": first_resolution_outcomes,
                    "offline_replay": cached_resolution_outcomes,
                },
                "checkpoint": first,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
