# CubeAI project feasibility consolidation

## Question

What do Tasks 1–8 establish about the feasibility, sequencing, resource needs, and remaining decisions for CubeAI, and how should M0–M4 be reconciled without starting product implementation?

## Methodology

This synthesis uses the repository architecture, product, roadmap, milestone, backlog, three infographic sources, all eight research reports, and checked-in experiment results. Quantitative claims retain their provenance labels: **MEASURED** is a recorded experiment; **PROJECTED** is a stated linear estimate; **DOCUMENTED** is provider/tool documentation; **INFERRED** is an engineering interpretation; **UNKNOWN** is not established by current evidence. All measurements are deterministic synthetic probes on CPython 3.14.0/macOS 26.5.2 arm64 unless noted.

## Evidence inventory

| Evidence | Source | Boundary |
|---|---|---|
| Planning, package boundaries, M0–M5 sequencing | Tasks 1 and 6 reports; architecture/roadmap/milestones | Accepted direction, not implemented workspaces |
| Draft mechanics and retained state | `draft-engine.json`, `data-footprint.json` | Synthetic in-memory mechanics |
| Bot throughput | `bot-simulation.json`, bot baseline | Three transparent heuristics, synthetic drafts |
| Analytics comparison | `analytics.json`, analytics report | 1-seat × 1-pack × 3-card micro-drafts |
| Storage | `data-volume.json`, simulation-volume report | 1,000 standard drafts measured; larger targets projected |
| Provider contracts | CubeCobra/Scryfall reports | Official documentation separated from observations |
| Bot information boundary | bot-intelligence report | Fair-input and provenance contract; learned systems unmeasured |

## Consolidated feasibility matrix

Ratings mean: **LOW** = bounded, locally testable work with little unresolved dependency; **MEDIUM** = material design or integration work with a viable local path; **HIGH** = substantial domain/data or integration uncertainty; **VERY HIGH** = multiple coupled external, correctness, or product constraints; **UNKNOWN** = insufficient evidence to rate responsibly.

| Area | Complexity | Compute | Memory | Storage | External dependence | Domain | UI | Uncertainty | Data requirements | Testability | Agent suitability | Feasibility |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CubeCobra import | MEDIUM | LOW | LOW | LOW | MEDIUM | MEDIUM | LOW | HIGH | contract fixtures | HIGH | supervised | MEDIUM |
| Scryfall normalization | MEDIUM | LOW–MEDIUM | LOW | MEDIUM | HIGH | HIGH | LOW | HIGH | IDs, printings, cache policy | HIGH offline | supervised | MEDIUM |
| Local persistence | MEDIUM | LOW | LOW–MEDIUM | MEDIUM | LOW | MEDIUM | LOW | MEDIUM | schema and migrations | HIGH | safe after decision | MEDIUM |
| Deterministic draft logic | LOW | LOW | LOW | LOW | LOW | HIGH | LOW | LOW | synthetic + fixture Cubes | HIGH | safe | HIGH |
| Basic draft UI | MEDIUM | LOW | LOW | LOW | LOW | MEDIUM | MEDIUM | MEDIUM | API/view contracts | MEDIUM | safe after workspace | MEDIUM |
| Heuristic bots | LOW–MEDIUM | LOW | LOW | LOW | MEDIUM (ratings) | HIGH | LOW | MEDIUM | versioned ratings/tags | HIGH | supervised | HIGH |
| Simulation | MEDIUM | LOW now | LOW per run | HIGH at archive scale | LOW | MEDIUM | LOW | MEDIUM | seeds, events, provenance | HIGH | supervised | HIGH |
| Analytics | MEDIUM | LOW for bounded Python | LOW–MEDIUM | MEDIUM | LOW | HIGH | MEDIUM | MEDIUM | immutable events, bounded co-occurrence | HIGH | supervised | MEDIUM |
| Archetype inference | HIGH | UNKNOWN | UNKNOWN | MEDIUM | MEDIUM | HIGH | MEDIUM | HIGH | explicit tags and labeled definitions | MEDIUM | supervised | UNKNOWN |
| ML bots | VERY HIGH | UNKNOWN | UNKNOWN | HIGH | MEDIUM–HIGH | HIGH | MEDIUM | VERY HIGH | representative licensed choices/outcomes | MEDIUM later | supervised | UNKNOWN |
| Deck construction | HIGH | UNKNOWN | UNKNOWN | MEDIUM | LOW | VERY HIGH | HIGH | HIGH | card rules, constraints, evaluation | MEDIUM | supervised | UNKNOWN |
| Forge integration | VERY HIGH | UNKNOWN | UNKNOWN | UNKNOWN | HIGH | VERY HIGH | LOW initially | VERY HIGH | headless/legal/action evidence | LOW until spike | supervised | UNKNOWN |
| Gameplay UI | HIGH | UNKNOWN | MEDIUM | MEDIUM | engine-dependent | VERY HIGH | VERY HIGH | HIGH | player-safe state and actions | MEDIUM later | supervised | UNKNOWN |
| AI gameplay | VERY HIGH | UNKNOWN | UNKNOWN | HIGH | engine/data-dependent | VERY HIGH | HIGH | VERY HIGH | outcomes, policies, replay | LOW currently | supervised | UNKNOWN |
| Multiplayer | VERY HIGH | UNKNOWN | HIGH | HIGH | HIGH | VERY HIGH | HIGH | VERY HIGH | auth, visibility, reconnect protocol | LOW currently | supervised | UNKNOWN |
| Hosted deployment | VERY HIGH | UNKNOWN | HIGH | VERY HIGH | HIGH | HIGH | HIGH | VERY HIGH | operations, privacy, abuse, scale evidence | LOW currently | supervised | UNKNOWN |

## Measured results

- **MEASURED:** standard 8-seat × 3-pack × 15-card draft mechanics averaged 0.008940512 seconds/draft (111.850 drafts/s); retained synthetic result state was 82,816 bytes (~80.9 KiB) for 360 events.
- **MEASURED:** at 10,000 standard synthetic drafts, Bot 0 averaged 394.8028 drafts/s (25.329 s mean), Bot 1 148.2022 drafts/s (67.475 s), and Bot 2 130.4594 drafts/s (76.652 s).
- **MEASURED, micro-workload only:** analytics on 10,000 one-seat × one-pack × three-card micro-drafts took 0.5612 s in pure Python and 28.5279 s in normalized SQLite, with matching checksums. These absolute timings are not standard-draft analytics timings.
- **MEASURED:** 1,000 standard drafts occupied 67.58 MiB compact NDJSON, 11.61 MiB gzip level 6, and 120.95 MiB normalized SQLite. Seen-card rows dominate the NDJSON sample.

## Projections

Linear **PROJECTED** storage from the measured 1,000-draft sample is 0.66/6.60/65.99 GiB NDJSON, 0.11/1.13/11.34 GiB gzip NDJSON, and 1.18/11.81/118.12 GiB SQLite at 10,000/100,000/1,000,000 drafts respectively. These are not additional measurements.

For simulation wall-clock planning, applying the **MEASURED** 10,000-draft throughputs gives **PROJECTED** sequential totals of approximately 2.5/6.7/7.7 minutes for Bot 0/1/2 at 100,000 drafts. Memory remains primarily per-run working state, but retained archives grow with seen history. Sequential execution remains reasonable for local batches; batching/export becomes relevant before any parallel or distributed architecture is justified.

## Dominant complexity drivers

- **Engineering effort:** gameplay/engine boundaries, deck construction, and multiplayer dominate because correctness, visibility, and external contracts couple together.
- **CPU:** currently bot strategy and retained-event processing; measured throughput is adequate for sequential batches, while ML/gameplay cost is UNKNOWN.
- **Memory:** per-process gameplay state and future model artifacts are UNKNOWN; current draft state is small.
- **Storage:** seen-card history is the measured dominant growth driver; compressed exports are materially smaller than SQLite.
- **External API dependence:** Scryfall and CubeCobra resolution, including rate/cache/identity policy, are the principal early dependency.
- **Domain complexity:** Magic identity, draft semantics, archetypes, deck legality, and gameplay action rules rise sharply after M2.
- **UI complexity:** basic import/draft/review is bounded; gameplay and multiplayer visibility are high.
- **Research uncertainty:** learned bots, Forge, real outcome data, licensing, multiplayer, and hosting remain the least evidenced areas.

## Resource planning

| Scale | CPU/wall clock | Memory | Storage | Operating interpretation |
|---|---|---|---|---|
| One local draft | **MEASURED** ~9 ms mechanics; one small retained state | **MEASURED** ~83 KiB synthetic result | Small local record | Interactive and sequential |
| 1,000 drafts | **INFERRED** seconds to minutes depending strategy; no new benchmark claim | Per-run state remains bounded | **MEASURED** 67.58/11.61/120.95 MiB | Sequential local batch; export optional |
| 10,000 drafts | **MEASURED** bot means 25.329/67.475/76.652 s for the three strategies; analytics number is micro-only | Bounded working memory; archive retention matters | **PROJECTED** 0.66/0.11/1.18 GiB | Sequential remains reasonable; batch/export useful |
| 100,000 drafts | **PROJECTED** roughly 4.2/11.2/12.8 min from measured Bot 0/1/2 rates | Bounded per process; large retained archive | **PROJECTED** 6.60/1.13/11.81 GiB | Batch scheduling and compressed export become operationally relevant |

## Architecture implications

Tasks 1–8 support retaining the local-first, modular, engine-neutral architecture. Use sequential simulation first, pure Python aggregation for bounded interactive workloads, SQLite for ordinary local transactional state and precomputed normalized views, bounded co-occurrence, and compressed NDJSON for large archives. Keep provider adapters and durable cache boundaries explicit; preserve fair bot visibility and provenance. Delay ML and gameplay decisions until their evidence gates are met.

No evidence supports adding PostgreSQL, Redis, Kafka, Celery, Ray, Spark, Kubernetes, pandas/Polars, Parquet, vector databases, distributed simulation, or ML infrastructure now. They remain possible future options only after measured need and human review.

## Roadmap implications

The dependency order remains appropriate: M0 → M1 → M2 → M3 → M4, with M5 independent technically but behind its existing product-priority gate. Feasibility evidence supports keeping M1 focused on import, identity, deterministic draft, Bot v0, SQLite, and a small UI; M2 on event-derived intelligence and bounded analytics; M3 on explainable heuristic progression; and M4 on reproducible batches before parallelism. It does not justify accelerating deck construction, ML, gameplay, multiplayer, or hosting.

## M0 readiness

M0-001 is **AWAITING HUMAN DECISION** and links to [toolchain evaluation](toolchain-evaluation.md). M0-002 and M0-003 remain **BLOCKED** until that decision. M0-010 remains **READY**. After M0-001 approval, the next implementation sequence is exactly M0-002, M0-003, then M0-006; the first two may proceed independently and M0-006 depends on both.

## Human decisions still required

### Decisions required now

- Approve or revise M0-001’s proposed toolchain and dependency policy.
- Approve the M1-005 Scryfall/import resolution and cache strategy.
- Decide acceptable rating/tag/data licenses and attribution for M1/M3.

### Explicitly deferred

Forge adoption and GPL boundary, learned-bot data and outcome methodology, deck-construction policy, gameplay engine/API, multiplayer threat model, and hosted deployment are deferred to their later evidence gates. No decision is made here on the human’s behalf.

## Major risks

Provider contracts and rate expectations can change; custom cards and printings can be ambiguous; cache refresh can rewrite identity assumptions; self-play can amplify bot assumptions; seen history can make archives large; and Forge/gameplay may not expose a stable, legally acceptable headless boundary.

## Limitations

This report synthesizes synthetic benchmarks and documentation reconnaissance; it is not production capacity testing, a live provider conformance test, a gameplay evaluation, or a licensing opinion. The analytics timings use deliberately small micro-drafts, and storage and 100,000-draft timing figures marked **PROJECTED** are linear estimates rather than new measurements.

## Major unknowns

Real-world learned-model data quality and licensing, archetype/deck evaluation validity, production gameplay CPU/memory, Forge control and upgrade cost, multiplayer security/reconnection, and hosted operational cost are not established by Tasks 1–8.

## Recommendation

Proceed with the local-first M0/M1 path after the human toolchain and provider decisions. The measured mechanics and heuristic throughput support sequential local drafting and simulation. Keep storage explicitly budgeted, retain provenance, and require new evidence before adopting heavier analytics, parallelism, ML, gameplay, or hosted infrastructure.

## Roadmap/backlog impact

Reconcile M0 readiness and decision labels as described above; preserve existing M1–M5 scope and product-priority gates. The evidence changes implementation confidence, not milestone boundaries.

## Exactly three next implementation issues

1. **M0-002 — Establish the Python CubeLab workspace** (after M0-001 approval).
2. **M0-003 — Establish the React and TypeScript workspace** (after M0-001 approval; independent of M0-002).
3. **M0-006 — Provide aggregate developer commands and connect the vertical smoke slice** (after M0-002 and M0-003).
