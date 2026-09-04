"""Deterministic integer-card draft mechanics for non-production experiments."""

from __future__ import annotations

import argparse
import json
import platform
import random
import sys
import time
import tracemalloc
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from experiments.model import DraftResult, PickEvent, SyntheticCard, make_cards

Chooser = Callable[[tuple[SyntheticCard, ...], tuple[int, ...]], int]


def _choose_largest_id(pack: tuple[SyntheticCard, ...], _: tuple[int, ...]) -> int:
    """Provide a stable placeholder until a benchmark supplies a strategy."""
    return max(card.card_id for card in pack)


def run_draft(
    cards: Sequence[SyntheticCard],
    seats: int,
    packs_per_seat: int,
    pack_size: int,
    seed: int,
    chooser: Chooser | None = None,
) -> DraftResult:
    """Run synchronous picks with alternating pack directions.

    The chooser receives only the cards in the current pack and the calling
    seat's existing pool.  It returns the chosen card ID, so later benchmark
    strategies can use synthetic attributes without changing draft mechanics.
    """
    if seats <= 0 or packs_per_seat <= 0 or pack_size <= 0:
        raise ValueError("seats, packs_per_seat, and pack_size must be positive")
    required_cards = seats * packs_per_seat * pack_size
    if len(cards) < required_cards:
        raise ValueError(
            f"draft requires {required_cards} cards but received {len(cards)}"
        )

    cards_by_id = {card.card_id: card for card in cards}
    if len(cards_by_id) != len(cards):
        raise ValueError("card IDs must be unique")

    choose = chooser or _choose_largest_id
    card_ids = list(cards_by_id)
    random.Random(seed).shuffle(card_ids)
    allocated_ids = card_ids[:required_cards]
    pools: list[list[int]] = [[] for _ in range(seats)]
    events: list[PickEvent] = []
    directions: list[int] = []

    for pack_number in range(packs_per_seat):
        direction = 1 if pack_number % 2 == 0 else -1
        directions.append(direction)
        offset = pack_number * seats * pack_size
        packs = [
            allocated_ids[offset + seat * pack_size : offset + (seat + 1) * pack_size]
            for seat in range(seats)
        ]
        for pick_number in range(pack_size):
            for seat, pack in enumerate(packs):
                seen_card_ids = tuple(pack)
                visible_cards = tuple(cards_by_id[card_id] for card_id in seen_card_ids)
                chosen_id = choose(visible_cards, tuple(pools[seat]))
                if chosen_id not in pack:
                    raise ValueError("chooser must return an ID from the current pack")
                pack.remove(chosen_id)
                pools[seat].append(chosen_id)
                events.append(
                    PickEvent(pack_number, pick_number, seat, chosen_id, seen_card_ids)
                )
            if pick_number + 1 < pack_size:
                next_packs: list[list[int]] = [[] for _ in range(seats)]
                for seat, pack in enumerate(packs):
                    next_packs[(seat + direction) % seats] = pack
                packs = next_packs

    expected_pool_size = packs_per_seat * pack_size
    complete = (
        len(events) == required_cards
        and all(len(pool) == expected_pool_size for pool in pools)
        and len({event.card_id for event in events}) == required_cards
    )
    return DraftResult(
        events=tuple(events),
        pools=tuple(tuple(pool) for pool in pools),
        pack_directions=tuple(directions),
        complete=complete,
    )


def _event_checksum(result: DraftResult) -> int:
    """Return a deterministic, process-independent checksum for comparisons."""
    checksum = 0
    for event in result.events:
        checksum = (checksum * 1_000_003 + event.card_id + event.seat) % (2**64)
    return checksum


def benchmark_drafts(seed: int, repetitions: int) -> list[dict[str, Any]]:
    """Measure fixed draft configurations using elapsed time and traced memory."""
    if repetitions < 5:
        raise ValueError("repetitions must be at least 5")
    cases = []
    for seats, packs_per_seat, pack_size in ((4, 2, 3), (8, 3, 15), (8, 5, 18)):
        card_count = seats * packs_per_seat * pack_size
        cards = make_cards(card_count, seed)
        elapsed_samples = []
        checksums = []
        tracemalloc.start()
        try:
            for repetition in range(repetitions):
                start = time.perf_counter()
                result = run_draft(
                    cards, seats, packs_per_seat, pack_size, seed + repetition
                )
                elapsed_samples.append(time.perf_counter() - start)
                checksums.append(_event_checksum(result))
            _, peak_bytes = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        total_elapsed_seconds = sum(elapsed_samples)
        cases.append(
            {
                "configuration": {
                    "seats": seats,
                    "packs_per_seat": packs_per_seat,
                    "pack_size": pack_size,
                },
                "drafts": repetitions,
                "events_per_draft": card_count,
                "elapsed_seconds": total_elapsed_seconds,
                "mean_elapsed_seconds": total_elapsed_seconds / repetitions,
                "drafts_per_second": repetitions / total_elapsed_seconds,
                "peak_tracemalloc_bytes": peak_bytes,
                "checksums": checksums,
            }
        )
    return cases


def build_result_document(seed: int, repetitions: int) -> dict[str, Any]:
    return {
        "environment": {
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
        },
        "command": "python3 -m experiments.draft_engine",
        "seed": seed,
        "repetitions": repetitions,
        "cases": benchmark_drafts(seed, repetitions),
        "limitations": [
            "Uses synthetic integer card IDs and in-memory lists only.",
            "Measures mechanics, not production serialization, persistence, or bot quality.",
            "tracemalloc records Python allocations and is not total process memory.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    document = build_result_document(arguments.seed, arguments.repetitions)
    command = (
        f"python3 -m experiments.draft_engine --seed {arguments.seed} "
        f"--repetitions {arguments.repetitions}"
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
