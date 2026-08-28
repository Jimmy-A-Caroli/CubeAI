# CubeAI Architecture

## Status

This is the proposed initial architecture for an early-stage repository. Only the modular-monorepo decision is accepted. Technology selections remain assumptions to validate during M0, and Forge remains a research candidate.

## System context

CubeAI turns external Cube definitions and card metadata into versioned local Cubes. Users and bots draft those Cubes through deterministic domain rules. Completed drafts feed provenance-aware analysis and simulation. Gameplay is a later, independent workstream behind an engine-neutral boundary.

```text
CubeCobra / files       Scryfall
        \                  /
         import + metadata adapters
                    |
             CubeLab domain
      cube → draft → analysis → simulation
                    |
       application services + repositories
             /                    \
    versioned HTTP API        SQLite (initial)
             |
          CubeUI

Future only:
CubeUI → CubeAI Game API → engine adapter → Forge or alternative
```

## Proposed repository shape

Directories are created only when an issue supplies working contents:

```text
CubeAI/
├── backend/                 # Python workspace when M0 establishes it
│   ├── src/cubeai/          # lab, API, adapters
│   └── tests/
├── frontend/                # React/TypeScript workspace when established
├── fixtures/                # synthetic and sanitized integration fixtures
├── scripts/                 # focused developer automation
├── docs/
│   ├── adr/
│   ├── issues/
│   ├── milestones/
│   ├── research/
│   └── superpowers/
└── compose.yaml             # only when it runs a useful local slice
```

### Conceptual CubeLab package layout

The Python workspace will use `cubeai.lab` as CubeLab's first-class bounded-context namespace. This is a conceptual layout, not authorization to create empty package trees before their M0 issues supply working contents:

```text
backend/src/cubeai/
├── lab/
│   ├── domain/
│   └── application/
├── api/
└── adapters/
```

`cubeai.lab.domain` and `cubeai.lab.application` keep CubeLab framework-independent inside the modular monorepo rather than making it a separate deployable service. `cubeai.api` and `cubeai.adapters` are outer boundaries around that bounded context: transport, persistence, and external-provider details must not flow inward. CubeLab remains useful without CubeGame or any particular game engine. A future Forge adapter may use a separate Java build because its runtime and license boundary differ.

## Components and dependencies

### `cubeai.lab.domain` (CubeLab domain)

Owns domain entities, invariants, deterministic draft rules, bot strategy contracts, metrics, and simulation concepts. It depends only on small standard or domain-focused libraries approved through M0. It does not import FastAPI, SQL models, HTTP clients, React types, or Forge classes.

### `cubeai.lab.application` (application layer)

Coordinates use cases and transactions: import a Cube, resolve metadata, start a draft, submit a pick, complete bots' turns, and query a player-safe view. It consumes domain and repository ports and maps errors into transport-neutral results.

### `cubeai.api` (CubeAI API)

Provides a versioned local HTTP boundary, proposed as FastAPI with Pydantic DTOs. API DTOs are not domain entities. Initial APIs have no authentication and bind for local development according to explicit configuration.

### CubeUI

Provides Cube loading, validation, drafting, pool visualization, and later analytics. It consumes generated or explicitly maintained API contracts, never database or engine objects. State authoritative to a draft remains in the backend.

### Persistence

Repository protocols describe required storage behavior. SQLite is the proposed first implementation because the product is local and transactional. Domain behavior cannot depend on SQLite-specific features. Schema migrations and PostgreSQL suitability remain M0 decisions.

### `cubeai.adapters` (external adapters)

CubeCobra and Scryfall payloads terminate at adapters. Adapters preserve raw source identifiers, map into explicit import candidates, cache responsibly, and expose structured failures. Saved, sanitized fixtures detect contract changes. Provider assumptions do not leak into stable domain identities.

### CubeGame

Defines future DTOs for player-visible state, legal actions, submitted commands, game events, and replay information. It must prevent hidden-information leakage and isolate CubeUI from engine internals. Forge integration cannot begin before M5 resolves feasibility, upgrade, and licensing risks.

## Core identities

| Concept | Identity scope | Purpose |
|---|---|---|
| `Cube` | Stable local aggregate | A continuing Cube project from one or more sources |
| `CubeVersion` | Immutable version | Exact Cube contents and source snapshot used by drafts or experiments |
| `CardIdentity` | Rules identity | A named card's shared rules identity, normally linked to Oracle ID |
| `CardPrinting` | Printing identity | Set, collector number, language, finish, artwork, and provider IDs |
| `CubeCard` | Membership identity | One entry in one Cube version, preserving duplicates, tags, and overrides |
| `Draft` | Draft lifecycle | Configuration, seed, version, seats, packs, and status |
| `DraftCardInstance` | Draft-local | One physical/logical occurrence allocated into a draft pack |
| `Pick` | Ordered event | Actor, pack, chosen instance, seen cards, time/order, and provenance |
| `DraftPool` | Seat within draft | Cards acquired by one seat; derivable from picks but useful as a view |
| `Deck` | Build/version | Main deck, sideboard, lands, and source draft or import |
| `BotStrategy` | Named version | Reproducible strategy identifier and configuration |
| `SimulationRun` | Experiment run | Cube version, strategy mix, seed range, configuration, and results |
| `Game` | Game lifecycle | Engine-independent match/game reference and configuration |
| `GameCardInstance` | Game-local | Zone-changing card/object identity independent of draft instances |
| `GameResult` | Completed game | Outcome and provenance linked to decks and engine version |

Custom cards may lack Oracle or Scryfall IDs. They receive stable local identities, retain source fields, and must not be falsely matched by name alone without an explicit resolution status.

## Draft data flow

1. A source adapter retrieves a Cube snapshot or reads an uploaded file.
2. It produces source-preserving import candidates and diagnostics.
3. Metadata resolution links candidates to `CardIdentity` and `CardPrinting` records or marks them unresolved/custom.
4. Validation creates an immutable, usable `CubeVersion` or returns actionable errors.
5. A draft configuration and seed deterministically allocate `DraftCardInstance` values into packs.
6. Commands advance a draft state machine; all picks record actor and strategy provenance.
7. API views expose only information appropriate to the requesting seat and current phase.
8. Completion produces pools and analytical events without erasing the immutable pick history.

## Determinism and provenance

- Random generators are injected or created from recorded seeds.
- Ordering rules are explicit before randomization.
- Bot decisions are functions of visible state, named strategy version, configuration, and RNG state.
- Simulation runs record code/schema-relevant version information sufficient for interpretation.
- `HUMAN`, `BOT`, `SIMULATION`, and later `GAMEPLAY` origins remain queryable dimensions.
- Aggregations may combine origins only through an explicit user-selected comparison, never by default.

## Errors and consistency

- Transport, parsing, resolution, validation, domain-command, and persistence failures use distinct error categories.
- Import results retain row/card context and may be inspected before a user chooses whether resolvable warnings are acceptable.
- No invalid or stale pick mutates draft state.
- A pick and all resulting bot turns are committed through explicit transaction semantics appropriate to the use case.
- API errors use stable machine-readable codes plus safe human-readable detail.
- Adapter retry behavior is bounded and respects provider guidance; domain code never performs retries.

## Security and privacy assumptions

M0/M1 are local and unauthenticated. Local does not mean unrestricted: configuration must make bind addresses explicit, imported content is untrusted, logs must avoid private source payloads, and fixtures must contain no credentials or private Cube data. Multiplayer requires a new threat model before implementation.

## Testing strategy

- Domain unit tests use synthetic Cubes and assert invariants rather than implementation details.
- Property-style tests are considered for allocation uniqueness, pick conservation, and state transitions.
- Golden deterministic scenarios assert identical outcomes for fixed inputs and seeds.
- Contract tests replay sanitized CubeCobra and Scryfall fixtures.
- Repository tests run against temporary SQLite databases.
- API tests verify DTO schemas, error codes, and state transitions.
- Frontend tests cover components and critical flows; browser tests remain few and user-centered.
- Simulation benchmarks separate correctness, determinism, and performance thresholds.

## External systems

### CubeCobra

CubeCobra is the intended initial import source. Its documented API/export behavior, identifiers, boards, tags, duplicates, custom cards, and usage expectations must be captured by M1 research before implementation commits to a route or payload. The adapter must also permit file-based import later.

### Scryfall

Scryfall is the proposed metadata authority. Live requests require responsible headers, throttling, caching, and bounded retries; bulk data is preferable for large-scale resolution. Oracle IDs and Scryfall printing IDs serve different identity layers. Attribution and image-use expectations require documentation.

### Forge

Forge is a Java, GPL-3.0 candidate rules engine. Current public capabilities do not prove that it can serve CubeAI through a stable headless API. M5 must test legal-action access, action submission, player-safe serialization, determinism, replay, performance, upgrade cost, and license implications before an adoption ADR.

## Unresolved decisions

- Toolchain versions, dependency managers, lint/format commands, and CI matrix.
- Final Python package layout and whether one or multiple distributable packages are useful.
- API contract generation and client strategy.
- SQLite schema, migrations, and repository implementation.
- Supported CubeCobra contract and fallback imports.
- Metadata cache format and refresh policy.
- Initial card-rating source and license.
- Detailed analytics schemas and archetype vocabulary.
- Forge adoption and process/license boundary.
- Multiplayer transport, authorization, reconnection, and hidden-information model.

Each durable resolution requires evidence and an ADR; major decisions must not be made incidentally inside feature issues.
