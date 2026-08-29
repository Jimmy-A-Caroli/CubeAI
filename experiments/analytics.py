"""Bounded draft analytics experiment; not production analytics or persistence."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import sqlite3
import statistics
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from itertools import combinations
from pathlib import Path
from typing import Any

from experiments.bot_simulation import choose_bot0
from experiments.draft_engine import run_draft
from experiments.model import PickEvent, SyntheticCard, make_cards

# This deliberately bounds one expensive metric.  It is a sampling rule for a
# spike, not a proposed product co-occurrence definition.
_COOCCURRENCE_POOL_CARD_LIMIT = 12
_BENCHMARK_SEATS = 1
_BENCHMARK_PACKS_PER_SEAT = 1
_BENCHMARK_PACK_SIZE = 3
_BENCHMARK_CARD_COUNT = 12


def _sorted_events(events: Sequence[PickEvent]) -> list[PickEvent]:
    return sorted(events, key=lambda event: (event.pack_number, event.pick_number, event.seat))


def _validate_inputs(
    events: Sequence[Sequence[PickEvent]], cards: Sequence[SyntheticCard]
) -> dict[int, SyntheticCard]:
    cards_by_id = {card.card_id: card for card in cards}
    if len(cards_by_id) != len(cards):
        raise ValueError("card IDs must be unique")
    for draft in events:
        for event in draft:
            if event.card_id not in cards_by_id:
                raise ValueError(f"picked card {event.card_id} is not in cards")
            unknown_seen = set(event.seen_card_ids).difference(cards_by_id)
            if unknown_seen:
                raise ValueError(f"seen cards are not in cards: {sorted(unknown_seen)}")
            if event.card_id not in event.seen_card_ids:
                raise ValueError("picked card must be among seen cards")
    return cards_by_id


def _card_rows(values: dict[int, float]) -> list[dict[str, float | int]]:
    return [{"card_id": card_id, "value": float(value)} for card_id, value in sorted(values.items())]


def _result(
    average_pick: dict[int, float],
    median_pick: dict[int, float],
    first_seen: dict[int, float],
    last_pick_rate: dict[int, float],
    wheel_rate: dict[int, float],
    color_utilization: dict[str, float],
    card_utilization: dict[int, float],
    tag_frequency: dict[str, int],
    cooccurrence: dict[tuple[int, int], int],
) -> dict[str, list[dict[str, Any]]]:
    """Normalize all metrics to sorted JSON-compatible rows."""
    return {
        "average_pick": _card_rows(average_pick),
        "median_pick": _card_rows(median_pick),
        "first_seen": _card_rows(first_seen),
        "last_pick_rate": _card_rows(last_pick_rate),
        "wheel_rate": _card_rows(wheel_rate),
        "color_utilization": [
            {"color": color, "value": float(value)}
            for color, value in sorted(color_utilization.items())
        ],
        "card_utilization": _card_rows(card_utilization),
        "tag_frequency": [
            {"tag": tag, "value": value} for tag, value in sorted(tag_frequency.items())
        ],
        "cooccurrence": [
            {"card_ids": [first, second], "value": value}
            for (first, second), value in sorted(cooccurrence.items())
        ],
    }


def aggregate_python(
    events: Sequence[Sequence[PickEvent]], cards: Sequence[SyntheticCard]
) -> dict[str, list[dict[str, Any]]]:
    """Aggregate nested deterministic draft event sequences with dictionaries.

    Each inner sequence represents one draft.  Pick values are one-based within
    each pack.  ``first_seen`` uses the first chronological observation in a
    draft and reports its one-based pick number.  A synthetic wheel is an
    instance seen by one seat again at least the number of seats later.
    """
    cards_by_id = _validate_inputs(events, cards)
    pick_positions: dict[int, list[int]] = defaultdict(list)
    first_seen_positions: dict[int, list[int]] = defaultdict(list)
    last_pick_counts: Counter[int] = Counter()
    pick_counts: Counter[int] = Counter()
    wheel_counts: Counter[int] = Counter()
    color_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[int, int]] = Counter()

    for draft in events:
        ordered = _sorted_events(draft)
        seat_count = max((event.seat for event in ordered), default=-1) + 1
        first_by_card: dict[int, tuple[int, int]] = {}
        seen_by_seat_card: dict[tuple[int, int], list[int]] = defaultdict(list)
        pool_by_seat: dict[int, list[int]] = defaultdict(list)
        wheeled_cards: set[int] = set()
        for event in ordered:
            pick_position = event.pick_number + 1
            pick_positions[event.card_id].append(pick_position)
            pick_counts[event.card_id] += 1
            if len(event.seen_card_ids) == 1:
                last_pick_counts[event.card_id] += 1
            card = cards_by_id[event.card_id]
            color_counts[card.color] += 1
            tag_counts.update(card.archetype_tags)
            pool_by_seat[event.seat].append(event.card_id)
            sequence = event.pack_number * 1_000 + event.pick_number
            for card_id in event.seen_card_ids:
                first_by_card.setdefault(card_id, (sequence, pick_position))
                seen_key = (event.seat, card_id)
                prior_observations = seen_by_seat_card[seen_key]
                if any(sequence - prior >= seat_count for prior in prior_observations):
                    wheeled_cards.add(card_id)
                prior_observations.append(sequence)
        for card_id, (_, position) in first_by_card.items():
            first_seen_positions[card_id].append(position)
        for card_id in wheeled_cards:
            wheel_counts[card_id] += 1
        for pool in pool_by_seat.values():
            # Bounded to the first twelve chronological pool picks.
            for first, second in combinations(pool[:_COOCCURRENCE_POOL_CARD_LIMIT], 2):
                if first != second:
                    pair_counts[tuple(sorted((first, second)))] += 1

    total_drafts = len(events)
    total_picks = sum(pick_counts.values())
    return _result(
        {card_id: statistics.mean(values) for card_id, values in pick_positions.items()},
        {card_id: statistics.median(values) for card_id, values in pick_positions.items()},
        {card_id: statistics.mean(values) for card_id, values in first_seen_positions.items()},
        {
            card_id: last_pick_counts[card_id] / count
            for card_id, count in pick_counts.items()
        },
        {
            card_id: wheel_counts[card_id] / count
            for card_id, count in pick_counts.items()
        },
        {color: count / total_picks for color, count in color_counts.items()} if total_picks else {},
        {
            card_id: count / total_drafts
            for card_id, count in pick_counts.items()
        }
        if total_drafts
        else {},
        dict(tag_counts),
        dict(pair_counts),
    )


def _aggregate_sqlite(
    events: Sequence[Sequence[PickEvent]], cards: Sequence[SyntheticCard]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    """Load an in-memory normalized schema and calculate equivalent metrics."""
    _validate_inputs(events, cards)
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(
            """
            CREATE TABLE cards (card_id INTEGER PRIMARY KEY, color TEXT NOT NULL);
            CREATE TABLE drafts (draft_id INTEGER PRIMARY KEY, seat_count INTEGER NOT NULL);
            CREATE TABLE picks (
                draft_id INTEGER NOT NULL, pack_number INTEGER NOT NULL,
                pick_number INTEGER NOT NULL, seat INTEGER NOT NULL,
                card_id INTEGER NOT NULL, seen_count INTEGER NOT NULL
            );
            CREATE TABLE seen (
                draft_id INTEGER NOT NULL, pack_number INTEGER NOT NULL,
                pick_number INTEGER NOT NULL, seat INTEGER NOT NULL,
                card_id INTEGER NOT NULL, sequence INTEGER NOT NULL
            );
            CREATE TABLE pool_cards (
                draft_id INTEGER NOT NULL, seat INTEGER NOT NULL,
                pool_order INTEGER NOT NULL, card_id INTEGER NOT NULL
            );
            CREATE TABLE card_tags (card_id INTEGER NOT NULL, tag TEXT NOT NULL);
            CREATE INDEX seen_card_id ON seen(card_id);
            CREATE INDEX seen_draft_seat_card_sequence
                ON seen(draft_id, seat, card_id, sequence);
            CREATE INDEX picks_card_id ON picks(card_id);
            CREATE INDEX picks_draft_seat ON picks(draft_id, seat);
            CREATE INDEX picks_draft_pick_number ON picks(draft_id, pick_number);
            """
        )
        connection.executemany(
            "INSERT INTO cards VALUES (?, ?)", ((card.card_id, card.color) for card in cards)
        )
        connection.executemany(
            "INSERT INTO card_tags VALUES (?, ?)",
            ((card.card_id, tag) for card in cards for tag in card.archetype_tags),
        )
        picks: list[tuple[int, int, int, int, int, int]] = []
        seen: list[tuple[int, int, int, int, int, int]] = []
        pool_cards: list[tuple[int, int, int, int]] = []
        draft_rows: list[tuple[int, int]] = []
        for draft_id, draft in enumerate(events):
            ordered = _sorted_events(draft)
            draft_rows.append(
                (draft_id, max((event.seat for event in ordered), default=-1) + 1)
            )
            pool_order: Counter[int] = Counter()
            for event in ordered:
                picks.append(
                    (
                        draft_id,
                        event.pack_number,
                        event.pick_number,
                        event.seat,
                        event.card_id,
                        len(event.seen_card_ids),
                    )
                )
                pool_cards.append(
                    (draft_id, event.seat, pool_order[event.seat], event.card_id)
                )
                pool_order[event.seat] += 1
                sequence = event.pack_number * 1_000 + event.pick_number
                seen.extend(
                    (draft_id, event.pack_number, event.pick_number, event.seat, card_id, sequence)
                    for card_id in event.seen_card_ids
                )
        connection.executemany("INSERT INTO picks VALUES (?, ?, ?, ?, ?, ?)", picks)
        connection.executemany("INSERT INTO seen VALUES (?, ?, ?, ?, ?, ?)", seen)
        connection.executemany("INSERT INTO pool_cards VALUES (?, ?, ?, ?)", pool_cards)
        connection.executemany("INSERT INTO drafts VALUES (?, ?)", draft_rows)
        connection.commit()

        average_pick = dict(
            connection.execute(
                "SELECT card_id, AVG(pick_number + 1) FROM picks GROUP BY card_id"
            )
        )
        pick_lists: dict[int, list[int]] = defaultdict(list)
        for card_id, pick_position in connection.execute(
            "SELECT card_id, pick_number + 1 FROM picks ORDER BY card_id, pick_number"
        ):
            pick_lists[card_id].append(pick_position)
        median_pick = {
            card_id: statistics.median(positions) for card_id, positions in pick_lists.items()
        }
        first_seen = dict(
            connection.execute(
                """
                WITH first_observations AS (
                    SELECT draft_id, card_id, MIN(sequence) AS sequence
                    FROM seen GROUP BY draft_id, card_id
                )
                SELECT s.card_id, AVG(s.pick_number + 1)
                FROM seen AS s
                JOIN first_observations AS first
                  ON first.draft_id = s.draft_id
                 AND first.card_id = s.card_id
                 AND first.sequence = s.sequence
                GROUP BY s.card_id
                """
            )
        )
        last_pick_rate = dict(
            connection.execute(
                "SELECT card_id, AVG(seen_count = 1) FROM picks GROUP BY card_id"
            )
        )
        wheel_instances = set(
            connection.execute(
                """
                SELECT DISTINCT later.draft_id, later.card_id
                FROM seen AS earlier
                JOIN seen AS later
                  ON later.draft_id = earlier.draft_id
                 AND later.seat = earlier.seat
                 AND later.card_id = earlier.card_id
                JOIN drafts ON drafts.draft_id = later.draft_id
                WHERE later.sequence - earlier.sequence >= drafts.seat_count
                """
            )
        )
        pick_counts = dict(
            connection.execute("SELECT card_id, COUNT(*) FROM picks GROUP BY card_id")
        )
        wheel_counts = Counter(card_id for _, card_id in wheel_instances)
        wheel_rate = {
            card_id: wheel_counts[card_id] / count for card_id, count in pick_counts.items()
        }
        total_picks = len(picks)
        color_utilization = {
            color: count / total_picks
            for color, count in connection.execute(
                """
                SELECT cards.color, COUNT(*)
                FROM picks JOIN cards USING(card_id)
                GROUP BY cards.color
                """
            )
        } if total_picks else {}
        total_drafts = len(events)
        card_utilization = {
            card_id: count / total_drafts for card_id, count in pick_counts.items()
        } if total_drafts else {}
        tag_frequency = dict(
            connection.execute(
                """
                SELECT card_tags.tag, COUNT(*)
                FROM picks JOIN card_tags USING(card_id)
                GROUP BY card_tags.tag
                """
            )
        )
        cooccurrence = {
            (first, second): count
            for first, second, count in connection.execute(
                """
                SELECT
                    CASE WHEN first.card_id < second.card_id THEN first.card_id ELSE second.card_id END,
                    CASE WHEN first.card_id < second.card_id THEN second.card_id ELSE first.card_id END,
                    COUNT(*)
                FROM pool_cards AS first
                JOIN pool_cards AS second
                  ON second.draft_id = first.draft_id
                 AND second.seat = first.seat
                 AND second.pool_order > first.pool_order
                WHERE first.pool_order < ? AND second.pool_order < ?
                GROUP BY 1, 2
                """,
                (_COOCCURRENCE_POOL_CARD_LIMIT, _COOCCURRENCE_POOL_CARD_LIMIT),
            )
        }
        page_count = connection.execute("PRAGMA page_count").fetchone()[0]
        page_size = connection.execute("PRAGMA page_size").fetchone()[0]
        return _result(
            average_pick,
            median_pick,
            first_seen,
            last_pick_rate,
            wheel_rate,
            color_utilization,
            card_utilization,
            tag_frequency,
            cooccurrence,
        ), {"page_count": page_count, "page_size": page_size, "database_bytes": page_count * page_size}
    finally:
        connection.close()


def aggregate_sqlite(
    events: Sequence[Sequence[PickEvent]], cards: Sequence[SyntheticCard]
) -> dict[str, list[dict[str, Any]]]:
    """Aggregate the same nested draft event sequences through in-memory SQLite."""
    result, _ = _aggregate_sqlite(events, cards)
    return result


def _generate_drafts(count: int, seed: int) -> tuple[tuple[PickEvent, ...], ...]:
    cards = make_cards(_BENCHMARK_CARD_COUNT, seed)
    return tuple(
        run_draft(
            cards,
            _BENCHMARK_SEATS,
            _BENCHMARK_PACKS_PER_SEAT,
            _BENCHMARK_PACK_SIZE,
            seed + draft_id,
            chooser=choose_bot0,
        ).events
        for draft_id in range(count)
    )


def _serialized_input_size(events: Sequence[Sequence[PickEvent]]) -> int:
    payload = [
        [
            {
                "pack_number": event.pack_number,
                "pick_number": event.pick_number,
                "seat": event.seat,
                "card_id": event.card_id,
                "seen_card_ids": event.seen_card_ids,
            }
            for event in draft
        ]
        for draft in events
    ]
    return len(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def _checksum(result: dict[str, list[dict[str, Any]]]) -> str:
    encoded = json.dumps(result, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _measure(
    backend: str,
    events: Sequence[Sequence[PickEvent]],
    cards: Sequence[SyntheticCard],
    repetitions: int,
) -> dict[str, Any]:
    elapsed_samples: list[float] = []
    peak_samples: list[int] = []
    checksums: list[str] = []
    database_sizes: list[dict[str, int]] = []
    for _ in range(repetitions):
        tracemalloc.start()
        try:
            start = time.perf_counter()
            if backend == "python":
                result = aggregate_python(events, cards)
            else:
                result, database_size = _aggregate_sqlite(events, cards)
                database_sizes.append(database_size)
            elapsed_samples.append(time.perf_counter() - start)
            _, peak = tracemalloc.get_traced_memory()
            peak_samples.append(peak)
        finally:
            tracemalloc.stop()
        checksums.append(_checksum(result))
    if len(set(checksums)) != 1:
        raise AssertionError(f"{backend} returned different checksums for identical input")
    measurement: dict[str, Any] = {
        "mean_elapsed_seconds": sum(elapsed_samples) / len(elapsed_samples),
        "elapsed_seconds": elapsed_samples,
        "peak_traced_aggregation_bytes": max(peak_samples),
        "result_checksum": checksums[0],
    }
    if database_sizes:
        if len({tuple(size.items()) for size in database_sizes}) != 1:
            raise AssertionError("SQLite database size changed for identical input")
        measurement["database"] = database_sizes[0]
    return measurement


def _installed_dataframe_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in ("pandas", "polars"):
        try:
            module = importlib.import_module(name)
        except ImportError:
            continue
        versions[name] = getattr(module, "__version__", "unknown")
    return versions


def benchmark_aggregation(
    draft_counts: Iterable[int], seed: int, repetitions: int
) -> list[dict[str, Any]]:
    """Benchmark both aggregation implementations over generated small drafts."""
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    cards = make_cards(_BENCHMARK_CARD_COUNT, seed)
    cases = []
    for draft_count in draft_counts:
        if draft_count <= 0:
            raise ValueError("draft counts must be positive")
        events = _generate_drafts(draft_count, seed)
        python_measurement = _measure("python", events, cards, repetitions)
        sqlite_measurement = _measure("sqlite", events, cards, repetitions)
        if python_measurement["result_checksum"] != sqlite_measurement["result_checksum"]:
            raise AssertionError("Python and SQLite aggregation results differ")
        cases.append(
            {
                "drafts": draft_count,
                "event_count": sum(len(draft) for draft in events),
                "serialized_input_bytes": _serialized_input_size(events),
                "python": python_measurement,
                "sqlite": sqlite_measurement,
            }
        )
    return cases


def build_result_document(
    draft_counts: Iterable[int], seed: int, repetitions: int
) -> dict[str, Any]:
    """Build the stable, JSON-ready benchmark document."""
    counts = tuple(draft_counts)
    return {
        "environment": {
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
        },
        "command": "python3 -m experiments.analytics",
        "seed": seed,
        "repetitions": repetitions,
        "workload": {
            "cards_available": _BENCHMARK_CARD_COUNT,
            "seats": _BENCHMARK_SEATS,
            "packs_per_seat": _BENCHMARK_PACKS_PER_SEAT,
            "pack_size": _BENCHMARK_PACK_SIZE,
            "cooccurrence_pool_card_limit": _COOCCURRENCE_POOL_CARD_LIMIT,
        },
        "cases": benchmark_aggregation(counts, seed, repetitions),
        "installed_dataframe_versions": _installed_dataframe_versions(),
        "limitations": [
            "Uses synthetic deterministic drafts and in-memory data only.",
            "Pick values are one-based within each synthetic pack.",
            "A wheel is synthetically defined as one seat seeing a card again at least seat_count picks later.",
            "Co-occurrence considers only the first twelve chronological cards in each synthetic pool.",
            "Peak traced allocations cover aggregation only; tracing starts after the benchmark input is built, so pre-built input allocations are excluded.",
            "tracemalloc tracks Python allocations, not total process or SQLite native memory.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drafts", type=int, nargs="+", default=(100, 1_000, 10_000))
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    document = build_result_document(arguments.drafts, arguments.seed, arguments.repetitions)
    command = (
        "python3 -m experiments.analytics"
        f" --drafts {' '.join(str(count) for count in arguments.drafts)}"
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
