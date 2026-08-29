"""Measure synthetic draft-event storage; non-production research only."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field, fields
import gzip
import json
from pathlib import Path
import platform
import sqlite3
import sys
import tempfile
from typing import Any

from experiments.draft_engine import run_draft
from experiments.model import make_cards

_SEATS = 8
_PACKS_PER_SEAT = 3
_PACK_SIZE = 15
_CARDS_PER_DRAFT = _SEATS * _PACKS_PER_SEAT * _PACK_SIZE


@dataclass(frozen=True)
class StorageRows:
    """Logical normalized rows emitted by the measured sample."""

    pick_rows: int
    seen_rows: int
    pool_rows: int
    run_metadata_rows: int


@dataclass(frozen=True)
class StorageBytes:
    """Byte counts measured for each compact serialization component."""

    pick_rows_bytes: int
    seen_rows_bytes: int
    pool_data_bytes: int
    run_metadata_bytes: int
    compact_ndjson_bytes: int
    gzip_ndjson_bytes: int
    sqlite_bytes: int


@dataclass(frozen=True)
class StorageSample:
    """A measured storage sample produced by generated deterministic drafts."""

    drafts: int
    seed: int
    row_counts: StorageRows
    byte_counts: StorageBytes
    record_type: str = field(default="measured_sample", init=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StorageProjection:
    """A linear estimate derived from a StorageSample, never a measurement."""

    source_sample_drafts: int
    target_drafts: int
    row_counts: StorageRows
    byte_counts: StorageBytes
    record_type: str = field(default="projection", init=False)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _compact_line(value: list[Any]) -> bytes:
    return (json.dumps(value, separators=(",", ":")) + "\n").encode("utf-8")


def _write_line(output: Any, value: list[Any]) -> int:
    line = _compact_line(value)
    output.write(line)
    return len(line)


def _create_schema(connection: sqlite3.Connection) -> None:
    """Create a compact normalized schema with logical identity keys only."""
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        PRAGMA journal_mode = DELETE;
        CREATE TABLE runs (
            run_id INTEGER PRIMARY KEY,
            seed INTEGER NOT NULL,
            draft_count INTEGER NOT NULL
        );
        CREATE TABLE drafts (
            draft_id INTEGER PRIMARY KEY,
            run_id INTEGER NOT NULL REFERENCES runs(run_id),
            seed INTEGER NOT NULL,
            seats INTEGER NOT NULL,
            packs_per_seat INTEGER NOT NULL,
            pack_size INTEGER NOT NULL
        );
        CREATE TABLE picks (
            draft_id INTEGER NOT NULL REFERENCES drafts(draft_id),
            pack_number INTEGER NOT NULL,
            pick_number INTEGER NOT NULL,
            seat INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            seen_count INTEGER NOT NULL,
            PRIMARY KEY (draft_id, pack_number, pick_number, seat)
        );
        CREATE TABLE seen (
            draft_id INTEGER NOT NULL REFERENCES drafts(draft_id),
            pack_number INTEGER NOT NULL,
            pick_number INTEGER NOT NULL,
            seat INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            PRIMARY KEY (draft_id, pack_number, pick_number, seat, card_id)
        );
        CREATE TABLE pool_entries (
            draft_id INTEGER NOT NULL REFERENCES drafts(draft_id),
            seat INTEGER NOT NULL,
            pool_order INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            PRIMARY KEY (draft_id, seat, pool_order)
        );
        """
    )


def measure_sample(drafts: int, seed: int) -> StorageSample:
    """Emit and measure a real deterministic synthetic draft sample.

    The NDJSON uses short array records: ``p`` picks, ``s`` seen-card rows,
    ``o`` pool entries, and ``r`` per-draft run metadata.  SQLite holds the
    same normalized facts in a temporary file.  Both files are discarded after
    their byte counts have been observed.
    """
    if drafts <= 0:
        raise ValueError("drafts must be positive")

    cards = make_cards(_CARDS_PER_DRAFT, seed)
    row_counts = {name: 0 for name in ("pick_rows", "seen_rows", "pool_rows", "run_metadata_rows")}
    component_bytes = {
        name: 0
        for name in (
            "pick_rows_bytes",
            "seen_rows_bytes",
            "pool_data_bytes",
            "run_metadata_bytes",
        )
    }
    with tempfile.TemporaryDirectory(prefix="cubeai-data-volume-") as temporary_directory:
        directory = Path(temporary_directory)
        ndjson_path = directory / "sample.ndjson"
        sqlite_path = directory / "sample.sqlite"
        connection = sqlite3.connect(sqlite_path)
        try:
            _create_schema(connection)
            connection.execute("INSERT INTO runs VALUES (0, ?, ?)", (seed, drafts))
            with ndjson_path.open("wb") as output:
                for draft_id in range(drafts):
                    draft_seed = seed + draft_id
                    result = run_draft(
                        cards,
                        _SEATS,
                        _PACKS_PER_SEAT,
                        _PACK_SIZE,
                        seed=draft_seed,
                    )
                    connection.execute(
                        "INSERT INTO drafts VALUES (?, 0, ?, ?, ?, ?)",
                        (draft_id, draft_seed, _SEATS, _PACKS_PER_SEAT, _PACK_SIZE),
                    )
                    component_bytes["run_metadata_bytes"] += _write_line(
                        output, ["r", draft_id, draft_seed, _SEATS, _PACKS_PER_SEAT, _PACK_SIZE]
                    )
                    row_counts["run_metadata_rows"] += 1

                    pick_rows: list[tuple[int, int, int, int, int, int]] = []
                    seen_rows: list[tuple[int, int, int, int, int]] = []
                    for event in result.events:
                        component_bytes["pick_rows_bytes"] += _write_line(
                            output,
                            [
                                "p",
                                draft_id,
                                event.pack_number,
                                event.pick_number,
                                event.seat,
                                event.card_id,
                                len(event.seen_card_ids),
                            ],
                        )
                        row_counts["pick_rows"] += 1
                        pick_rows.append(
                            (
                                draft_id,
                                event.pack_number,
                                event.pick_number,
                                event.seat,
                                event.card_id,
                                len(event.seen_card_ids),
                            )
                        )
                        for seen_card_id in event.seen_card_ids:
                            component_bytes["seen_rows_bytes"] += _write_line(
                                output,
                                [
                                    "s",
                                    draft_id,
                                    event.pack_number,
                                    event.pick_number,
                                    event.seat,
                                    seen_card_id,
                                ],
                            )
                            row_counts["seen_rows"] += 1
                            seen_rows.append(
                                (
                                    draft_id,
                                    event.pack_number,
                                    event.pick_number,
                                    event.seat,
                                    seen_card_id,
                                )
                            )
                    pool_rows: list[tuple[int, int, int, int]] = []
                    for seat, pool in enumerate(result.pools):
                        for pool_order, card_id in enumerate(pool):
                            component_bytes["pool_data_bytes"] += _write_line(
                                output, ["o", draft_id, seat, pool_order, card_id]
                            )
                            row_counts["pool_rows"] += 1
                            pool_rows.append((draft_id, seat, pool_order, card_id))
                    connection.executemany("INSERT INTO picks VALUES (?, ?, ?, ?, ?, ?)", pick_rows)
                    connection.executemany("INSERT INTO seen VALUES (?, ?, ?, ?, ?)", seen_rows)
                    connection.executemany(
                        "INSERT INTO pool_entries VALUES (?, ?, ?, ?)", pool_rows
                    )
            connection.commit()
            connection.execute("VACUUM")
        finally:
            connection.close()

        compact_ndjson_bytes = ndjson_path.stat().st_size
        gzip_ndjson_bytes = len(
            gzip.compress(ndjson_path.read_bytes(), compresslevel=6)
        )
        sqlite_bytes = sqlite_path.stat().st_size

    return StorageSample(
        drafts=drafts,
        seed=seed,
        row_counts=StorageRows(**row_counts),
        byte_counts=StorageBytes(
            **component_bytes,
            compact_ndjson_bytes=compact_ndjson_bytes,
            gzip_ndjson_bytes=gzip_ndjson_bytes,
            sqlite_bytes=sqlite_bytes,
        ),
    )


def _scale_value(value: int, source_drafts: int, target_drafts: int) -> int:
    """Conservatively round a linear byte or row projection up to an integer."""
    return (value * target_drafts + source_drafts - 1) // source_drafts


def _scale_dataclass(value: StorageRows | StorageBytes, source_drafts: int, target_drafts: int) -> Any:
    return type(value)(
        **{
            item.name: _scale_value(getattr(value, item.name), source_drafts, target_drafts)
            for item in fields(value)
        }
    )


def project(sample: StorageSample, target_drafts: int) -> StorageProjection:
    """Project all measured components linearly without relabeling them as facts."""
    if target_drafts <= 0:
        raise ValueError("target_drafts must be positive")
    return StorageProjection(
        source_sample_drafts=sample.drafts,
        target_drafts=target_drafts,
        row_counts=_scale_dataclass(sample.row_counts, sample.drafts, target_drafts),
        byte_counts=_scale_dataclass(sample.byte_counts, sample.drafts, target_drafts),
    )


def build_result_document(sample_drafts: int, targets: tuple[int, ...], seed: int) -> dict[str, Any]:
    """Build a JSON result with measured values and projections kept separate."""
    sample = measure_sample(sample_drafts, seed)
    return {
        "schema_version": 1,
        "environment": {
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
        },
        "command": "python3 -m experiments.data_volume",
        "seed": seed,
        "geometry": {
            "seats": _SEATS,
            "packs_per_seat": _PACKS_PER_SEAT,
            "pack_size": _PACK_SIZE,
            "cards_per_draft": _CARDS_PER_DRAFT,
        },
        "measured_sample": sample.to_dict(),
        "projections": [project(sample, target).to_dict() for target in targets],
        "limitations": [
            "Uses deterministic synthetic cards and draft events only; it is not a production persistence design.",
            "Compact NDJSON is measured as UTF-8 array records; gzip uses gzip.compress with compresslevel=6.",
            "SQLite is a VACUUMed temporary normalized file with identity keys but no query-specific secondary indexes or WAL sidecars.",
            "Projections are linear estimates from the measured sample, not additional measurements.",
            "No Parquet dependency or numeric Parquet estimate is included.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-drafts", type=int, default=1_000)
    parser.add_argument("--targets", type=int, nargs="+", default=(1_000, 10_000, 100_000, 1_000_000))
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    document = build_result_document(
        arguments.sample_drafts, tuple(arguments.targets), arguments.seed
    )
    command = (
        "python3 -m experiments.data_volume"
        f" --sample-drafts {arguments.sample_drafts}"
        f" --targets {' '.join(str(target) for target in arguments.targets)}"
        f" --seed {arguments.seed}"
    )
    if arguments.output:
        command += f" --output {arguments.output}"
    document["command"] = command
    rendered = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)


if __name__ == "__main__":
    main()
