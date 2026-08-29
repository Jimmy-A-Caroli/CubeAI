"""Sequential heuristic-bot benchmark for non-production experiments only."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
import tracemalloc
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from experiments.draft_engine import run_draft
from experiments.model import DraftResult, SyntheticCard, make_cards

Chooser = Callable[[tuple[SyntheticCard, ...], tuple[int, ...]], int]
_COLORS = "WUBRG"
_STANDARD_SEATS = 8
_STANDARD_PACKS_PER_SEAT = 3
_STANDARD_PACK_SIZE = 15
_STANDARD_CARD_COUNT = _STANDARD_SEATS * _STANDARD_PACKS_PER_SEAT * _STANDARD_PACK_SIZE


def _pool_color_share(pool: tuple[int, ...], color: str) -> float:
    """Estimate color share from the fixed synthetic-card ID convention."""
    if not pool:
        return 0.0
    return sum(_COLORS[card_id % len(_COLORS)] == color for card_id in pool) / len(pool)


def _high_curve_share(pool: tuple[int, ...]) -> float:
    """Return average synthetic mana value as a share of the seven-mana ceiling."""
    if not pool:
        return 0.0
    return sum(1 + card_id % 7 for card_id in pool) / (7 * len(pool))


def _choose_highest_score(
    pack: tuple[SyntheticCard, ...], score: Callable[[SyntheticCard], float]
) -> int:
    """Choose the highest score, resolving equal scores with the lowest ID."""
    return min(pack, key=lambda card: (-score(card), card.card_id)).card_id


def choose_bot0(pack: tuple[SyntheticCard, ...], pool: tuple[int, ...]) -> int:
    """Choose the card with the highest raw synthetic rating."""
    del pool
    return _choose_highest_score(pack, lambda card: card.rating)


def choose_bot1(pack: tuple[SyntheticCard, ...], pool: tuple[int, ...]) -> int:
    """Choose rating plus a small preference for the pool's colors."""
    return _choose_highest_score(
        pack,
        lambda card: card.rating + 0.75 * _pool_color_share(pool, card.color),
    )


def choose_bot2(pack: tuple[SyntheticCard, ...], pool: tuple[int, ...]) -> int:
    """Add a transparent low-curve preference when the current pool is top-heavy."""
    high_curve = _high_curve_share(pool) > 0.45
    return _choose_highest_score(
        pack,
        lambda card: (
            card.rating
            + 0.75 * _pool_color_share(pool, card.color)
            + (0.35 if card.mana_value <= 3 and high_curve else 0.0)
        ),
    )


STRATEGIES: dict[str, Chooser] = {
    "bot0": choose_bot0,
    "bot1": choose_bot1,
    "bot2": choose_bot2,
}


def _event_checksum(result: DraftResult) -> int:
    """Return a deterministic process-independent checksum for one draft."""
    checksum = 0
    for event in result.events:
        checksum = (checksum * 1_000_003 + event.card_id + event.seat) % (2**64)
    return checksum


def _batch_checksum(checksum: int, result: DraftResult) -> int:
    return (checksum * 1_000_003 + _event_checksum(result)) % (2**64)


def _strategy_name(strategy: str | Chooser) -> tuple[str, Chooser]:
    if isinstance(strategy, str):
        try:
            return strategy, STRATEGIES[strategy]
        except KeyError as error:
            raise ValueError(f"unknown strategy: {strategy}") from error
    for name, chooser in STRATEGIES.items():
        if strategy is chooser:
            return name, chooser
    return strategy.__name__, strategy


def benchmark_batches(
    counts: Iterable[int],
    seed: int,
    strategy: str | Chooser,
    repetitions: int = 1,
    time_limit_seconds: float = 600.0,
) -> list[dict[str, Any]]:
    """Benchmark sequential standard drafts for each requested count.

    The 10,000-draft batch checks the ten-minute stop condition after every
    completed draft.  Smaller batches deliberately run to completion.
    """
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if time_limit_seconds <= 0:
        raise ValueError("time_limit_seconds must be positive")

    strategy_name, chooser = _strategy_name(strategy)
    cards = make_cards(_STANDARD_CARD_COUNT, seed)
    cases: list[dict[str, Any]] = []
    for count in counts:
        if count <= 0:
            raise ValueError("draft counts must be positive")
        elapsed_samples: list[float] = []
        checksum_samples: list[int] = []
        completed_samples: list[int] = []
        peak_samples: list[int] = []
        stopped = False
        for _ in range(repetitions):
            checksum = 0
            completed = 0
            start = time.perf_counter()
            tracemalloc.start()
            try:
                while completed < count:
                    result = run_draft(
                        cards,
                        _STANDARD_SEATS,
                        _STANDARD_PACKS_PER_SEAT,
                        _STANDARD_PACK_SIZE,
                        seed + completed,
                        chooser=chooser,
                    )
                    checksum = _batch_checksum(checksum, result)
                    completed += 1
                    if count >= 10_000 and time.perf_counter() - start > time_limit_seconds:
                        stopped = completed < count
                        break
                _, peak_bytes = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            elapsed_samples.append(time.perf_counter() - start)
            checksum_samples.append(checksum)
            completed_samples.append(completed)
            peak_samples.append(peak_bytes)
            if stopped:
                break
        total_completed = sum(completed_samples)
        total_elapsed = sum(elapsed_samples)
        cases.append(
            {
                "strategy": strategy_name,
                "seed": seed,
                "drafts": count,
                "repetitions_requested": repetitions,
                "repetitions_completed": len(elapsed_samples),
                "completed_drafts": completed_samples,
                "stopped_at_time_limit": stopped,
                "time_limit_seconds": time_limit_seconds if count >= 10_000 else None,
                "elapsed_seconds": total_elapsed,
                "mean_elapsed_seconds": total_elapsed / len(elapsed_samples),
                "drafts_per_second": total_completed / total_elapsed,
                "repetition_elapsed_seconds": elapsed_samples,
                "peak_tracemalloc_bytes": max(peak_samples),
                "checksum": checksum_samples[0],
                "checksum_samples": checksum_samples,
            }
        )
    return cases


def build_result_document(
    counts: Iterable[int], seed: int, strategies: Iterable[str], repetitions: int
) -> dict[str, Any]:
    """Build a JSON-ready sequential benchmark document."""
    requested_counts = tuple(counts)
    requested_strategies = tuple(strategies)
    return {
        "environment": {
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
        },
        "command": "python3 -m experiments.bot_simulation",
        "seed": seed,
        "counts": requested_counts,
        "repetitions": repetitions,
        "sequential": True,
        "cases": [
            case
            for strategy in requested_strategies
            for case in benchmark_batches(requested_counts, seed, strategy, repetitions)
        ],
        "limitations": [
            "Uses the deterministic synthetic card generator and in-memory draft engine only.",
            "Pool color and curve shares reconstruct attributes from synthetic card IDs because the injected chooser receives pool IDs.",
            "tracemalloc records Python allocations and is not total process memory.",
            "This measures transparent baseline strategy cost, not bot quality or production throughput.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", type=int, nargs="+", default=(100, 1_000, 10_000))
    parser.add_argument("--strategies", choices=tuple(STRATEGIES), nargs="+", default=tuple(STRATEGIES))
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    document = build_result_document(
        arguments.drafts, arguments.seed, arguments.strategies, arguments.repetitions
    )
    command = (
        "python3 -m experiments.bot_simulation"
        f" --drafts {' '.join(str(count) for count in arguments.drafts)}"
        f" --strategies {' '.join(arguments.strategies)}"
        f" --seed {arguments.seed} --repetitions {arguments.repetitions}"
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
