# Planning Refinement and Feasibility Spikes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine CubeAI's early plan and produce reproducible measurements and reconnaissance for toolchain, Cube data, drafting, bots, analytics, external providers, storage, and overall feasibility without implementing M1.

**Architecture:** Keep all executable work in an isolated `experiments` Python package using the standard library and deterministic synthetic data. Store stable benchmark summaries as JSON, explain them in ten research reports, then feed only material findings back into the accepted architecture, roadmap, milestone, and backlog documents.

**Tech Stack:** Python standard library (`argparse`, `dataclasses`, `json`, `random`, `sqlite3`, `statistics`, `time`, `tracemalloc`, `unittest`), Markdown, current official web documentation, Git.

**Spec:** `docs/superpowers/specs/2026-08-28-planning-refinement-and-feasibility-spikes-design.md`

## Global Constraints

- Do not implement M1 product behavior, create production infrastructure, or integrate Forge.
- Do not add a dependency to a production workspace; use Python's standard library for the experiment harness.
- Experimental code lives under `experiments/`, begins with a non-production warning, and is never imported by production modules.
- Use no credentials, private Cube data, large external dataset, or HTML scraping.
- Use fixed seeds and record machine, OS, architecture, runtime, command, dataset size, repetitions, elapsed time, and memory evidence.
- Separate measured values from projections and documented provider behavior from observations and assumptions.
- Stop and document a blocker if work needs an architectural commitment, questionable scraping, external cost, license decision, or production infrastructure.
- Keep `docs/issues/INITIAL_BACKLOG.md` authoritative during early M0 and do not create remote issues.
- Keep M5 technically independent but product-priority blocked until M1 completes unless a human explicitly overrides it.
- Do not accept M0-001's toolchain recommendation without human review.
- Do not merge or push.

---

### Task 1: Apply the Four Planning Refinements

**Files:**
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/milestones/M0-REPOSITORY-FOUNDATION.md`
- Modify: `docs/issues/INITIAL_BACKLOG.md`
- Create: `docs/adr/0002-cubelab-bounded-context-namespace.md`
- Modify: `docs/adr/README.md`

**Interfaces:**
- Consumes: accepted modular-monorepo ADR and the four refinements in the spec.
- Produces: conceptual namespace `cubeai.lab.domain` and `cubeai.lab.application`; M0 vertical smoke-slice acceptance criteria; M5 product-priority gate; authoritative-backlog transition policy.

- [ ] **Step 1: Write a documentation assertion script that initially fails**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

checks = {
    "docs/ARCHITECTURE.md": ["cubeai.lab.domain", "cubeai.lab.application"],
    "docs/ROADMAP.md": ["product-priority gate", "M1"],
    "docs/milestones/M0-REPOSITORY-FOUNDATION.md": ["GET /health", "Backend connected"],
    "docs/issues/INITIAL_BACKLOG.md": ["planning source of truth", "remote issue owns execution state"],
    "docs/adr/0002-cubelab-bounded-context-namespace.md": ["Status: Accepted", "cubeai.lab"],
}
missing = []
for name, needles in checks.items():
    path = Path(name)
    text = path.read_text() if path.exists() else ""
    missing.extend(f"{name}: {needle}" for needle in needles if needle not in text)
assert not missing, "\n".join(missing)
PY
```

Expected: FAIL listing missing refinements and ADR.

- [ ] **Step 2: Update the architecture and record ADR-0002**

Add the conceptual layout below to `docs/ARCHITECTURE.md` and explain that API/adapters are outer boundaries and CubeLab remains useful without CubeGame:

```text
backend/src/cubeai/
├── lab/
│   ├── domain/
│   └── application/
├── api/
└── adapters/
```

Create ADR-0002 with context, decision, alternatives (`cubeai.domain`, top-level `cubelab`, and `cubeai.lab`), consequences, and revisit conditions. Mark it accepted because the user explicitly approved the direction. Add it to the ADR index.

- [ ] **Step 3: Update roadmap priority and M0 smoke-slice language**

State in `docs/ROADMAP.md` that M5 has no code dependency on M1–M4 but is behind a product-priority gate until M1 succeeds, unless explicitly overridden by a human. Add an M0 vertical slice:

```text
backend GET /health → {"status": "ok"}
frontend status view → "Backend connected"
```

Make clear that wording/schema may change during M0-001 and that this is connectivity proof, not product functionality.

- [ ] **Step 4: Refine M0 issue boundaries and backlog authority**

Update M0-002/M0-003 to prepare each side of the smoke slice, M0-006 to join them, M0-007 to validate it in CI where practical, and M0-011 to run it locally. Add a backlog policy stating:

```text
INITIAL_BACKLOG.md owns planning scope during early M0. When a remote issue is created,
the Markdown entry records its URL and stops duplicating execution state; the remote issue
then owns assignee, status, discussion, and closure.
```

- [ ] **Step 5: Run the documentation assertion and whitespace checks**

Run the Step 1 script again.

Expected: PASS with no output.

Run: `git diff --check`

Expected: exit 0.

- [ ] **Step 6: Commit the planning refinements**

```bash
git add docs/ARCHITECTURE.md docs/ROADMAP.md docs/milestones/M0-REPOSITORY-FOUNDATION.md docs/issues/INITIAL_BACKLOG.md docs/adr/0002-cubelab-bounded-context-namespace.md docs/adr/README.md
git commit -m "docs: refine early CubeAI planning boundaries"
```

### Task 2: Build the Deterministic Experimental Core and Data-Footprint Probe

**Files:**
- Create: `experiments/README.md`
- Create: `experiments/__init__.py`
- Create: `experiments/model.py`
- Create: `experiments/draft_engine.py`
- Create: `experiments/data_footprint.py`
- Create: `experiments/tests/__init__.py`
- Create: `experiments/tests/test_draft_engine.py`
- Create: `experiments/tests/test_data_footprint.py`
- Create: `experiments/results/data-footprint.json`
- Create: `experiments/results/draft-engine.json`
- Create: `docs/research/cube-data-footprint.md`
- Create: `docs/research/draft-engine-spike.md`

**Interfaces:**
- Consumes: Python 3 standard library only.
- Produces: `SyntheticCard`, `PickEvent`, `DraftResult`; `make_cards(count, seed)`; `run_draft(cards, seats, packs_per_seat, pack_size, seed, chooser)`; `deep_size(value)`; JSON result schema with `environment`, `command`, `seed`, `cases`, and `limitations`.

- [ ] **Step 1: Write failing deterministic-draft tests**

Create `experiments/tests/test_draft_engine.py`:

```python
import unittest

from experiments.draft_engine import run_draft
from experiments.model import make_cards


class DraftEngineTests(unittest.TestCase):
    def test_standard_draft_is_deterministic_and_conserves_instances(self):
        cards = make_cards(360, seed=17)
        first = run_draft(cards, 8, 3, 15, seed=20260828)
        second = run_draft(cards, 8, 3, 15, seed=20260828)
        self.assertEqual(first.events, second.events)
        picked = [event.card_id for event in first.events]
        self.assertEqual(360, len(picked))
        self.assertEqual(360, len(set(picked)))
        self.assertTrue(first.complete)
        self.assertEqual([45] * 8, [len(pool) for pool in first.pools])

    def test_pack_directions_alternate(self):
        result = run_draft(make_cards(24, 9), 4, 2, 3, seed=11)
        self.assertEqual((1, -1), result.pack_directions)

    def test_insufficient_cards_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "requires 24 cards"):
            run_draft(make_cards(23, 1), 4, 2, 3, seed=2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the draft tests and confirm failure**

Run: `python3 -m unittest experiments.tests.test_draft_engine -v`

Expected: FAIL because `experiments.draft_engine` and `experiments.model` do not exist.

- [ ] **Step 3: Implement the minimal synthetic model and draft engine**

Create `experiments/model.py` with frozen dataclasses:

```python
from dataclasses import dataclass
import random


@dataclass(frozen=True, slots=True)
class SyntheticCard:
    card_id: int
    rating: float
    color: str
    mana_value: int
    archetype_tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PickEvent:
    pack_number: int
    pick_number: int
    seat: int
    card_id: int
    seen_card_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DraftResult:
    events: tuple[PickEvent, ...]
    pools: tuple[tuple[int, ...], ...]
    pack_directions: tuple[int, ...]
    complete: bool


def make_cards(count: int, seed: int) -> tuple[SyntheticCard, ...]:
    rng = random.Random(seed)
    colors = "WUBRG"
    tags = ("aggro", "control", "artifacts", "graveyard")
    return tuple(
        SyntheticCard(i, rng.random() * 5, colors[i % 5], 1 + i % 7, (tags[i % 4],))
        for i in range(count)
    )
```

Create `run_draft` in `experiments/draft_engine.py` using `random.Random(seed)`, shuffled card IDs, pack arrays, one synchronous pick per seat per pick round, and rotation mapping `(seat + direction) % seats`. Default chooser selects `max(pack)` only as a deterministic mechanical placeholder. Preserve `seen_card_ids` before removal.

- [ ] **Step 4: Run draft tests**

Run: `python3 -m unittest experiments.tests.test_draft_engine -v`

Expected: 3 tests PASS.

- [ ] **Step 5: Write failing deep-size tests**

Create `experiments/tests/test_data_footprint.py`:

```python
import unittest

from experiments.data_footprint import deep_size
from experiments.model import make_cards


class DataFootprintTests(unittest.TestCase):
    def test_deep_size_counts_nested_content_once(self):
        shared = [1, 2, 3]
        self.assertGreater(deep_size([shared, shared]), deep_size(shared))
        self.assertLess(deep_size([shared, shared]), deep_size([shared, list(shared)]))

    def test_larger_cube_uses_more_memory(self):
        self.assertGreater(deep_size(make_cards(720, 1)), deep_size(make_cards(360, 1)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Run the data-footprint tests and confirm failure**

Run: `python3 -m unittest experiments.tests.test_data_footprint -v`

Expected: FAIL because `experiments.data_footprint` does not exist.

- [ ] **Step 7: Implement retained-size measurement and benchmark entry points**

Implement `deep_size(value, seen=None)` using `sys.getsizeof`, object IDs, dataclass fields, mappings, and iterable members. Add CLIs to both experiment modules with fixed defaults and JSON output. `data_footprint.py` must measure 90, 180, 360, 540, 720, and 1,080 cards plus a standard draft result. `draft_engine.py` must measure `(4,2,3)`, `(8,3,15)`, and `(8,5,18)` across at least five repetitions with `time.perf_counter` and `tracemalloc`.

- [ ] **Step 8: Run all core experiment tests twice**

Run twice: `python3 -m unittest discover -s experiments/tests -v`

Expected each run: 5 tests PASS.

- [ ] **Step 9: Generate results and write the two reports**

Run:

```bash
python3 -m experiments.data_footprint --seed 20260828 --output experiments/results/data-footprint.json
python3 -m experiments.draft_engine --seed 20260828 --repetitions 7 --output experiments/results/draft-engine.json
```

Write both reports with the required headings: Question, Methodology, Environment and command, Observations, Measurements, Limitations, Risks, Recommendation, Roadmap/backlog impact. Explicitly state that Python retained size is runtime-specific and that the integer-card draft engine measures mechanics, not production serialization or bots.

- [ ] **Step 10: Commit the core experiments and reports**

```bash
git add experiments docs/research/cube-data-footprint.md docs/research/draft-engine-spike.md
git commit -m "research: measure Cube data and draft mechanics"
```

### Task 3: Benchmark Heuristic Bot Simulation

**Files:**
- Create: `experiments/bot_simulation.py`
- Create: `experiments/tests/test_bot_simulation.py`
- Create: `experiments/results/bot-simulation.json`
- Create: `docs/research/bot-simulation-baseline.md`

**Interfaces:**
- Consumes: `SyntheticCard`, `DraftResult`, and `run_draft` from Task 2.
- Produces: `choose_bot0(pack, pool)`, `choose_bot1(pack, pool)`, `choose_bot2(pack, pool)` returning a card ID; `benchmark_batches(counts, seed, strategy)` returning timings, throughput, peak memory, and checksum.

- [ ] **Step 1: Write failing strategy tests**

Create tests that use four explicit `SyntheticCard` values and assert:

```python
self.assertEqual(3, choose_bot0(cards, ()))
self.assertEqual(2, choose_bot1(cards, (0, 1, 1)))
self.assertEqual(1, choose_bot2(cards, (0, 0, 0, 6, 6)))
```

The fixture must make card 3 the raw-rating winner, card 2 the color-fit winner for a blue-heavy pool, and card 1 the lower-curve winner when the pool is top-heavy. Add a determinism test asserting identical event checksums for 100 drafts with the same seed.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python3 -m unittest experiments.tests.test_bot_simulation -v`

Expected: FAIL because `experiments.bot_simulation` does not exist.

- [ ] **Step 3: Implement three deliberately simple strategies**

Use these transparent scores:

```python
bot0 = card.rating
bot1 = card.rating + 0.75 * pool_color_share(card.color)
bot2 = bot1 + (0.35 if card.mana_value <= 3 and high_curve_share(pool) > 0.45 else 0.0)
```

Break equal scores by the lowest card ID. Do not add archetype learning, signals, multiprocessing, NumPy, or caching that obscures the baseline.

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest experiments.tests.test_bot_simulation -v`

Expected: strategy and deterministic checksum tests PASS.

- [ ] **Step 5: Run sequential benchmarks**

Run:

```bash
python3 -m experiments.bot_simulation --drafts 100 1000 10000 --strategies bot0 bot1 bot2 --seed 20260828 --repetitions 3 --output experiments/results/bot-simulation.json
```

If 10,000 drafts exceeds ten minutes for one strategy, stop that case, record the completed counts and elapsed limit, and do not introduce parallel execution.

- [ ] **Step 6: Validate benchmark determinism**

Run the same command a second time to `/tmp/bot-simulation-repeat.json`. Compare stable `checksum`, `drafts`, `strategy`, and `seed` fields while excluding timing/memory/environment noise.

Expected: all stable fields match.

- [ ] **Step 7: Write the report and commit**

Document CPU model/logical count when available, approximate process CPU interpretation, wall time, drafts/second, peak traced memory, repetition spread, and whether parallelism is justified.

```bash
git add experiments/bot_simulation.py experiments/tests/test_bot_simulation.py experiments/results/bot-simulation.json docs/research/bot-simulation-baseline.md
git commit -m "research: benchmark heuristic draft bots"
```

### Task 4: Measure Analytics Aggregation Cost

**Files:**
- Create: `experiments/analytics.py`
- Create: `experiments/tests/test_analytics.py`
- Create: `experiments/results/analytics.json`
- Create: `docs/research/analytics-compute-spike.md`

**Interfaces:**
- Consumes: deterministic synthetic `PickEvent` sequences generated by Task 3.
- Produces: `aggregate_python(events, cards) -> dict`; `aggregate_sqlite(events, cards) -> dict`; metrics `average_pick`, `median_pick`, `first_seen`, `last_pick_rate`, `wheel_rate`, `color_utilization`, `card_utilization`, `tag_frequency`, and `cooccurrence`.

- [ ] **Step 1: Write a hand-calculated failing metric test**

Create a tiny two-draft event fixture with explicit seen-card lists and assert exact expected values for each metric. Compare normalized pure-Python and SQLite results:

```python
self.assertEqual(expected, aggregate_python(events, cards))
self.assertEqual(expected, aggregate_sqlite(events, cards))
```

Define wheel in the experiment as the same card instance being seen by the same seat at least `seat_count` picks later; label this synthetic definition in the report.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python3 -m unittest experiments.tests.test_analytics -v`

Expected: FAIL because `experiments.analytics` does not exist.

- [ ] **Step 3: Implement pure-Python and SQLite aggregators**

Use dictionaries, `statistics.median`, sets, and bounded pair combinations for Python. For SQLite use an in-memory database with `cards`, `picks`, `seen`, `pool_cards`, and `card_tags` tables plus indexes on `(card_id)`, `(draft_id, seat)`, and `(draft_id, pick_number)`. Ensure results normalize to identical sorted JSON-compatible structures.

- [ ] **Step 4: Run correctness tests**

Run: `python3 -m unittest experiments.tests.test_analytics -v`

Expected: all hand-calculated and backend-equivalence tests PASS.

- [ ] **Step 5: Benchmark 100, 1,000, and 10,000 draft datasets**

Run:

```bash
python3 -m experiments.analytics --drafts 100 1000 10000 --seed 20260828 --repetitions 3 --output experiments/results/analytics.json
```

Record event counts, serialized input size, aggregation elapsed time, peak traced memory, result checksum, and SQLite database size via page count × page size. If an already-installed pandas or Polars import succeeds, record its installed version but do not implement a comparison unless Python or SQLite exceeds a two-second interactive threshold at 10,000 drafts.

- [ ] **Step 6: Write the report and commit**

Classify metrics as interactive, precomputable, or increasingly expensive. Explain the quadratic risk in unrestricted card-card co-occurrence and the need to bound pairs to cards sharing a pool/deck or minimum support.

```bash
git add experiments/analytics.py experiments/tests/test_analytics.py experiments/results/analytics.json docs/research/analytics-compute-spike.md
git commit -m "research: measure draft analytics aggregation"
```

### Task 5: Project Simulation Storage Volume

**Files:**
- Create: `experiments/data_volume.py`
- Create: `experiments/tests/test_data_volume.py`
- Create: `experiments/results/data-volume.json`
- Create: `docs/research/simulation-data-volume.md`

**Interfaces:**
- Consumes: event and pool samples from Tasks 3–4.
- Produces: `measure_sample(drafts, seed) -> StorageSample`; `project(sample, target_drafts) -> StorageProjection` for 1,000, 10,000, 100,000, and 1,000,000 drafts.

- [ ] **Step 1: Write failing projection tests**

Assert that projections scale linearly from the measured sample, contain separate byte counts for pick rows, seen rows, pools, run metadata, JSON, gzip JSON, and SQLite, and never label a projection as measured.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python3 -m unittest experiments.tests.test_data_volume -v`

Expected: FAIL because `experiments.data_volume` does not exist.

- [ ] **Step 3: Implement measured serialization and projections**

Measure compact newline-delimited JSON, `gzip.compress(..., compresslevel=6)`, and a temporary SQLite file populated with normalized rows. Derive per-draft bytes from at least 1,000 generated drafts. Provide conceptual Parquet ranges only as explicitly labeled estimates sourced from observed compression ranges or omit the numeric range if no defensible local evidence exists.

- [ ] **Step 4: Run tests and generate results**

Run:

```bash
python3 -m unittest experiments.tests.test_data_volume -v
python3 -m experiments.data_volume --sample-drafts 1000 --targets 1000 10000 100000 1000000 --seed 20260828 --output experiments/results/data-volume.json
```

Expected: tests PASS; JSON distinguishes `measured_sample` and `projections`.

- [ ] **Step 5: Write the report and commit**

Identify when SQLite is merely large versus operationally inconvenient, including index/write-amplification, query latency, backup, vacuum, and export considerations. Do not claim a hard cutoff from byte size alone.

```bash
git add experiments/data_volume.py experiments/tests/test_data_volume.py experiments/results/data-volume.json docs/research/simulation-data-volume.md
git commit -m "research: project simulation storage volume"
```

### Task 6: Evaluate the Initial Toolchain

**Files:**
- Create: `docs/research/toolchain-evaluation.md`

**Interfaces:**
- Consumes: current official Python, FastAPI, Pydantic, pytest, Node.js, React, TypeScript, Vite, frontend-test-tool, SQLite, Docker Compose, and GitHub Actions documentation; local machine version/resource observations.
- Produces: one human-review recommendation for M0-001 with exact version floors, dependency managers, lockfiles, quality tools, package layout, commands, CI compatibility, resource expectations, alternatives, and decision checklist.

- [ ] **Step 1: Capture local environment evidence**

Run and record available output without installing anything:

```bash
uname -a
sw_vers
sysctl -n machdep.cpu.brand_string
sysctl -n hw.memsize
python3 --version
node --version
npm --version
docker --version
docker compose version
git --version
```

If a command is unavailable, record `not installed`; do not treat local absence as ecosystem evidence.

- [ ] **Step 2: Research only official current sources**

Verify supported/stable versions and compatibility from primary documentation. Record access date and direct URLs next to claims. Compare:

- Python packaging: `uv` versus `pip`/`venv` with a lock-capable workflow.
- Backend checks: Ruff, based type checker choice, pytest, import-boundary check.
- Frontend: supported Node LTS, npm lockfile, React, strict TypeScript, Vite, Vitest, Testing Library, ESLint/formatter responsibility.
- Local runtime: native commands first and Compose as an optional useful slice.
- CI: locked installs, cache keys, least permissions, and same root commands.

- [ ] **Step 3: Write the evaluation with an explicit recommendation**

Use sections: Question, Methodology, Candidate matrix, Supported versions, Package layout, Quality commands, Lockfiles, Cross-platform/CI, Agent friendliness, Resource estimate, Risks, Recommendation for human review, M0-001 acceptance checklist, Roadmap/backlog impact.

Recommend `backend/src/cubeai/lab/{domain,application}` conceptually but do not create it. Label every exact version as either a floor, compatible range, or resolved lock.

- [ ] **Step 4: Validate and commit**

Run: `rg -n 'https://|human review|lockfile|strict|resource' docs/research/toolchain-evaluation.md`

Expected: citations and required decision subjects are present.

```bash
git add docs/research/toolchain-evaluation.md
git commit -m "research: evaluate initial development toolchain"
```

### Task 7: Perform CubeCobra and Scryfall Reconnaissance

**Files:**
- Create: `docs/research/cubecobra-reconnaissance.md`
- Create: `docs/research/scryfall-resolution-reconnaissance.md`

**Interfaces:**
- Consumes: official CubeCobra API/export/help/source material and official Scryfall API/bulk-data/card-object guidance.
- Produces: smallest proposed M1 CubeCobra import contract; Cube-scale Scryfall live/bulk/hybrid comparison; documented/observed/assumed fact tables; blockers and contract-test requirements.

- [ ] **Step 1: Research CubeCobra non-invasively**

Use current official sources to identify URL/ID forms, documented read/export routes, card-list fields, boards/maybeboard, tags, duplicates, custom cards, printings, stable identifiers, rate/usage expectations, and error behavior. At most make small GET requests to public documentation or a deliberately selected public example; do not scrape HTML or enumerate Cubes.

- [ ] **Step 2: Write CubeCobra findings**

Include a table with columns `Claim`, `Documented`, `Observed`, `Assumption`, `Source`, and `M1 contract impact`. Recommend the smallest first contract, likely public mainboard import with source/card/printing identifiers and explicit unsupported diagnostics for uncertain features; adjust this recommendation to actual evidence.

- [ ] **Step 3: Research Scryfall resolution**

Verify official collection lookup limits, API request expectations, bulk-data offerings, Oracle ID versus card/printing ID, data update timestamps, images/attribution, and custom-card implications. Calculate the worst-case live request count for 360/540/720 cards using documented batch size, alongside the individual-lookup upper bound.

- [ ] **Step 4: Write Scryfall findings**

Compare live collection lookup, bulk snapshot, and hybrid local cache for first import, repeat import, offline operation, staleness, disk, and implementation complexity. Recommend the smallest M1 strategy but leave M1-005 as a human decision.

- [ ] **Step 5: Validate evidence separation and commit**

Run:

```bash
for file in docs/research/cubecobra-reconnaissance.md docs/research/scryfall-resolution-reconnaissance.md; do
  rg -q '^## Documented behavior' "$file"
  rg -q '^## Observed behavior' "$file"
  rg -q '^## Assumptions and unknowns' "$file"
  rg -q 'https://' "$file"
done
```

Expected: exit 0.

```bash
git add docs/research/cubecobra-reconnaissance.md docs/research/scryfall-resolution-reconnaissance.md
git commit -m "research: examine CubeCobra and Scryfall contracts"
```

### Task 8: Map Bot Intelligence Complexity

**Files:**
- Create: `docs/research/bot-intelligence-complexity.md`

**Interfaces:**
- Consumes: product visibility rules, M1/M2 bot and analytics boundaries, measured bot baseline.
- Produces: observable/derived/private information map; heuristic → weighted → learned ranking → contextual progression; data requirements and evaluation risks.

- [ ] **Step 1: Write the information-boundary matrix**

For current pack, previous picks, drafted pool, pack/pick number, cards previously seen, wheels, known Cube list, other pools, future order, and strategy internals, record whether each is observable, derived, unknown/private, or simulation-only. Explicitly prohibit look-ahead and access to other exact pools in fair benchmarks.

- [ ] **Step 2: Write the model-progression and data table**

For heuristic, weighted features, learned ranking, and contextual model, record required labels/data, minimum evaluation method, explainability, compute expectation, leakage risks, licensing risks, and whether gameplay outcomes are required. State that historical picks measure behavior, while gameplay outcomes are needed for performance claims.

- [ ] **Step 3: Connect complexity to roadmap**

Explain why M1 Bot v0 needs ratings but no training data, M2 supplies derived features, M3 benchmarks strategies, and ML needs a separate proposal after data provenance/licensing are resolved.

- [ ] **Step 4: Validate and commit**

Run:

```bash
rg -q '^## Observable state' docs/research/bot-intelligence-complexity.md
rg -q '^## Derived features' docs/research/bot-intelligence-complexity.md
rg -q '^## Unknown and private information' docs/research/bot-intelligence-complexity.md
rg -q 'heuristic.*weighted.*learned.*contextual' docs/research/bot-intelligence-complexity.md
```

Expected: exit 0.

```bash
git add docs/research/bot-intelligence-complexity.md
git commit -m "research: map draft bot intelligence complexity"
```

### Task 9: Consolidate Feasibility and Reconcile M0–M4

**Files:**
- Create: `docs/research/project-feasibility.md`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/issues/INITIAL_BACKLOG.md`
- Modify: `docs/milestones/M0-REPOSITORY-FOUNDATION.md`

**Interfaces:**
- Consumes: all nine preceding research reports and JSON result files.
- Produces: LOW/MEDIUM/HIGH/VERY HIGH/UNKNOWN feasibility matrix; compute estimates for local draft and 1k/10k/100k simulation; measured-hypothesis conclusion; M0 readiness; exactly three dependency-ordered next implementation issues.

- [ ] **Step 1: Build the consolidated evidence table**

Cover CubeCobra import, Scryfall normalization, local persistence, deterministic draft logic, basic draft UI, heuristic bots, simulation, analytics, archetype inference, ML bots, deck construction, Forge, gameplay UI, AI gameplay, multiplayer, and hosted deployment. For each record implementation complexity, compute cost, data requirements, external risk, testability, and agent suitability.

- [ ] **Step 2: Rank dominant complexity drivers**

Separately rank engineering effort, CPU, memory, storage, external API dependence, domain complexity, UI complexity, and research uncertainty. Use measured experiment references for draft/simulation/analytics claims; label 100,000-draft compute as an estimate based on observed 10,000-draft throughput unless directly measured cheaply.

- [ ] **Step 3: Reconcile architecture and roadmap**

Update only assumptions materially affected by evidence. Examples include sequential simulation first if measured throughput is high, SQLite sufficiency for local draft state, bounded co-occurrence aggregation, cache recommendations, and explicit experimental limitations. Do not accept M0-001 or M1-005 for the human.

- [ ] **Step 4: Update readiness and next issue sequence**

Mark M0-001 as `AWAITING HUMAN DECISION` with a link to the toolchain evaluation. Keep M0-002 and M0-003 blocked until that decision. M0-010 may remain READY if unchanged. Recommend exactly these three implementation issues in dependency order after toolchain approval unless findings demonstrate a necessary change:

1. M0-002 — Establish the Python CubeLab workspace.
2. M0-003 — Establish the React and TypeScript workspace.
3. M0-006 — Provide aggregate developer commands and connect the vertical smoke slice.

Explain that M0-002 and M0-003 can be implemented independently after M0-001, while M0-006 depends on both.

- [ ] **Step 5: Verify all required report structures**

Run:

```bash
for file in docs/research/*.md; do
  for heading in "Question" "Methodology" "Limitations" "Risks" "Recommendation" "Roadmap/backlog impact"; do
    rg -qi "^## .*${heading}" "$file" || printf 'Missing %s: %s\n' "$heading" "$file"
  done
done
```

For conceptual reports where `Measurements` is not applicable, require an explicit `## Measurements` section stating that the spike is qualitative and citing evidence inputs.

- [ ] **Step 6: Run the full experiment verification**

Run:

```bash
python3 -m unittest discover -s experiments/tests -v
python3 -m experiments.draft_engine --seed 20260828 --repetitions 2 --output /tmp/draft-engine-verify.json
python3 -m experiments.bot_simulation --drafts 100 --strategies bot0 bot1 bot2 --seed 20260828 --repetitions 1 --output /tmp/bot-verify.json
python3 -m experiments.analytics --drafts 100 --seed 20260828 --repetitions 1 --output /tmp/analytics-verify.json
python3 -m experiments.data_volume --sample-drafts 100 --targets 1000 10000 --seed 20260828 --output /tmp/volume-verify.json
git diff --check
```

Expected: all tests PASS, each command exits 0, and Git reports no whitespace errors.

- [ ] **Step 7: Check scope and secrets**

Run:

```bash
test ! -d backend
test ! -d frontend
! rg -n '(api[_-]?key|authorization: bearer|BEGIN .*PRIVATE KEY)' experiments docs/research
! rg -n "TB"'D|TO'"DO|FIX"'ME|implement lat'"er|appropriate error hand"'ling' experiments docs/research docs/ROADMAP.md docs/ARCHITECTURE.md docs/issues/INITIAL_BACKLOG.md docs/milestones/M0-REPOSITORY-FOUNDATION.md
git status --short
```

Expected: no production workspace directories, no secret-like content, no placeholders, and only intended files modified/untracked.

- [ ] **Step 8: Commit the consolidation**

```bash
git add docs/research/project-feasibility.md docs/ROADMAP.md docs/ARCHITECTURE.md docs/issues/INITIAL_BACKLOG.md docs/milestones/M0-REPOSITORY-FOUNDATION.md
git commit -m "docs: reconcile roadmap with feasibility evidence"
```

- [ ] **Step 9: Produce the final evidence report**

Report planning refinements, all ten completed spikes, actual measurements, architecture implications, resource needs for local/1k/10k/100k, ranked complexity drivers, M0 readiness, genuine human decisions, exactly three next issues, changed/untracked files, commits, and branch. Do not merge or push.
