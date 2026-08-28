# Planning Refinement and Feasibility Spikes Design

## Purpose

Refine four narrow planning details and replace early CubeAI assumptions with reproducible measurements. This work does not implement M1 product behavior, establish production dependencies, integrate Forge, or create deployment infrastructure.

## Planning refinements

1. Preserve M5's technical independence while making completion of M1 the default product-priority gate for active Forge feasibility work. A human may explicitly override the priority gate.
2. Make CubeLab a first-class bounded context under the conceptual namespace `cubeai.lab`, with domain and application packages below it. API and adapters remain outer boundaries. No directory is created merely to record the decision.
3. Define M0's acceptance slice as a minimal backend health/status response consumed by a frontend connection-status view. This proves workspaces, API connectivity, orchestration, tests, commands, CI, and boundaries without implementing product behavior.
4. Keep `docs/issues/INITIAL_BACKLOG.md` authoritative during early M0. Remote issues are created progressively; once created, the remote issue owns execution state and the Markdown entry links to it rather than duplicating status maintenance.

## Experimental approach

Use small deterministic Python standard-library experiments isolated under `experiments/`. SQLite may be exercised through Python's standard library. No package is added to a production workspace for a spike. A dataframe comparison is included only if a relevant library is already installed and its use answers a measured question.

Experiments are explicitly non-production, have clear entry points, avoid network access and private data, record fixed seeds and environment context, and are never imported by production modules.

## Measurement model

Record machine, operating system, architecture, runtime version, command, seed, dataset size, repetitions, elapsed time, throughput, and a defensible memory measurement or estimate. Round results to honest precision. Separate measured values from projections.

Synthetic Cube sizes cover 90, 180, 360, 540, 720, and at least one 1,000-plus-card context. Draft workloads include standard 8 × 3 × 15 and smaller/larger configurations. Bot and analytics workloads cover 100, 1,000, and 10,000 drafts where local runtime remains reasonable. Storage projections cover 1,000 through 1,000,000 drafts.

## Experiment components

- A data-footprint probe builds lightweight normalized card, Cube-version, draft-instance, event, and pool structures and measures their deep retained size using a transparent recursive estimator.
- A deterministic draft probe uses integer card IDs, local RNG instances, alternating pack direction, legal pick progression, completion checks, and conservation assertions.
- A bot-simulation probe adds synthetic rating, color, mana-value, and archetype attributes with three deliberately simple strategies. It measures sequential execution before considering parallelism.
- An analytics probe consumes generated event data and computes requested metrics in pure Python and SQLite. Optional installed columnar tooling is compared only if justified.
- A volume projection derives normalized-row, compact event, JSON, and conceptual columnar ranges from measured serialized samples, explicitly labeling extrapolation.

Shared experimental helpers may reduce duplicated event generation, but each report identifies the exact command and input it used. Experimental structures do not define future production interfaces.

## External reconnaissance

CubeCobra and Scryfall research uses current official documentation and official source repositories where available. Reports separate:

- documented behavior supported by a citation;
- behavior observed through non-invasive public requests or public payload examples;
- assumptions requiring contract tests or human decisions.

No HTML scraping is proposed as architecture, no credentials or private Cubes are used, and no large datasets are downloaded. Provider limits, attribution, identifiers, custom-card behavior, and cache implications are recorded.

## Research outputs

Create these reports under `docs/research/`:

1. `toolchain-evaluation.md`
2. `cube-data-footprint.md`
3. `draft-engine-spike.md`
4. `bot-simulation-baseline.md`
5. `analytics-compute-spike.md`
6. `bot-intelligence-complexity.md`
7. `cubecobra-reconnaissance.md`
8. `scryfall-resolution-reconnaissance.md`
9. `simulation-data-volume.md`
10. `project-feasibility.md`

Each spike report states its question, methodology, observations, measurements, limitations, risks, recommendation, and impact on the roadmap/backlog.

## Roadmap reconciliation

After measurement, revisit M0–M4 without redesigning them or creating a large speculative issue expansion. Mark issues ready only when dependencies and human decisions permit it. M0-001 remains a human decision until the toolchain recommendation is approved. Recommend exactly three next implementation issues in dependency order.

## Validation

- Run deterministic experiments twice where reproducibility is relevant and compare stable result fields.
- Assert card-instance conservation and valid draft completion for all draft configurations.
- Check benchmark result schemas and report every command used.
- Cross-check projections against measured serialized samples.
- Verify documentation links, required report sections, Markdown whitespace, Git diff, and repository status.
- Do not claim production performance from experimental models.

## Stop conditions

Stop an individual spike and document the blocker if it needs a major architectural commitment, large dataset, questionable scraping, credentials, external cost, license decision, or production infrastructure. A blocked result remains a valid research outcome.

## Completion boundary

The session ends with planning refinements, reproducible experimental evidence, ten research reports, a consolidated feasibility/risk map, and an updated M0–M4 interpretation. It does not accept the recommended toolchain on the human's behalf and does not advance Forge beyond planning.
