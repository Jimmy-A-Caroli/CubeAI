"""Retained-size estimates for non-production synthetic Cube structures."""

from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import sys
import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from experiments.draft_engine import run_draft
from experiments.model import make_cards


def deep_size(value: object, seen: set[int] | None = None) -> int:
    """Estimate Python retained size while counting each reachable object once.

    This transparent estimator includes container objects, dataclass fields,
    mapping keys and values, and iterable members. It is not a portable or
    total-process-memory metric.
    """
    known_ids = seen if seen is not None else set()
    value_id = id(value)
    if value_id in known_ids:
        return 0
    known_ids.add(value_id)

    size = sys.getsizeof(value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            size += deep_size(getattr(value, field.name), known_ids)
    elif isinstance(value, Mapping):
        for key, member in value.items():
            size += deep_size(key, known_ids)
            size += deep_size(member, known_ids)
    elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
        for member in value:
            size += deep_size(member, known_ids)
    return size


def measure_footprints(seed: int, repetitions: int) -> list[dict[str, Any]]:
    """Measure the requested cube sizes and one standard draft result."""
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    cases: list[dict[str, Any]] = []
    for card_count in (90, 180, 360, 540, 720, 1_080):
        elapsed_samples = []
        retained_bytes = 0
        for _ in range(repetitions):
            start = time.perf_counter()
            retained_bytes = deep_size(make_cards(card_count, seed))
            elapsed_samples.append(time.perf_counter() - start)
        cases.append(
            {
                "kind": "synthetic_cube",
                "cards": card_count,
                "retained_bytes": retained_bytes,
                "bytes_per_card": retained_bytes / card_count,
                "elapsed_seconds": sum(elapsed_samples),
                "mean_elapsed_seconds": sum(elapsed_samples) / repetitions,
            }
        )
    elapsed_samples = []
    retained_bytes = 0
    for _ in range(repetitions):
        start = time.perf_counter()
        standard_result = run_draft(make_cards(360, seed), 8, 3, 15, seed)
        retained_bytes = deep_size(standard_result)
        elapsed_samples.append(time.perf_counter() - start)
    cases.append(
        {
            "kind": "standard_draft_result",
            "configuration": {"seats": 8, "packs_per_seat": 3, "pack_size": 15},
            "events": len(standard_result.events),
            "retained_bytes": retained_bytes,
            "bytes_per_event": retained_bytes / len(standard_result.events),
            "elapsed_seconds": sum(elapsed_samples),
            "mean_elapsed_seconds": sum(elapsed_samples) / repetitions,
        }
    )
    return cases


def build_result_document(seed: int, repetitions: int = 5) -> dict[str, Any]:
    return {
        "environment": {
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
        },
        "command": "python3 -m experiments.data_footprint",
        "seed": seed,
        "repetitions": repetitions,
        "cases": measure_footprints(seed, repetitions),
        "limitations": [
            "Python retained size is runtime-specific and excludes interpreter overhead.",
            "The recursive estimator is a synthetic in-memory estimate, not serialized storage size.",
            "Synthetic cards do not represent imported Cube metadata, printings, or provenance.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    document = build_result_document(arguments.seed, arguments.repetitions)
    document["command"] = " ".join(
        ("python3", "-m", "experiments.data_footprint", *sys.argv[1:])
    )
    rendered = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)


if __name__ == "__main__":
    main()
