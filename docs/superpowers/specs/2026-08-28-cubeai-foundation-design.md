# CubeAI Foundation Design

## Purpose

This design defines the documentation and architectural foundation for an otherwise empty CubeAI repository. It does not implement product behavior or create speculative package scaffolding.

## Repository findings

At exploration time the repository contained only `README.md` with the title `CubeAI`, an MIT `LICENSE`, one `main` branch, and one initial commit. There was no application code, tooling, test configuration, CI, existing architecture, or historical implementation to preserve.

## Chosen direction

CubeAI will begin as a modular monorepo. The provisional technology baseline is React with TypeScript for CubeUI, Python with FastAPI and Pydantic for the API and CubeLab delivery layer, and SQLite for local persistence. M0 issues must validate and record these technology decisions before they become durable architecture constraints.

CubeLab domain logic remains independent of web frameworks, persistence implementations, user-interface types, and game-engine objects. CubeGame exposes an engine-neutral protocol; Forge is a leading candidate to investigate, not an adopted dependency.

## Component boundaries

- **CubeLab domain:** Cube identities, validation, draft state, bot interfaces, analytics, simulation, and experiment concepts.
- **Application layer:** use cases, transaction boundaries, authorization-free local workflows, and mapping between DTOs and domain commands.
- **CubeAI API:** versioned FastAPI DTOs and transport behavior.
- **CubeUI:** React/TypeScript draft and analysis interfaces consuming only the public API.
- **Persistence:** repository interfaces with a proposed SQLite implementation.
- **External adapters:** CubeCobra import and Scryfall metadata access with cached, fixture-tested contracts.
- **CubeGame boundary:** future commands, legal actions, player views, events, and engine-neutral state; a Forge adapter is conditional on M5.

## Data identity and provenance

`CardIdentity` represents the rules-level card, normally associated with an Oracle identifier. `CardPrinting` represents a particular set/collector-number or provider printing. `CubeCard` represents one membership entry in a `CubeVersion` and supports duplicates, custom metadata, and source traceability. Draft-card and game-card instances receive separate identities scoped to their lifecycles.

Every analytical observation records whether it came from a human, a named bot strategy and version, a simulation, or gameplay. Results also retain the Cube version, configuration, and deterministic seed information needed for replay. Datasets with different provenance are not silently combined.

## Data flow

An external adapter obtains a source payload and maps it into an import result containing normalized candidates and structured diagnostics. Metadata resolution links candidates to identities and printings without erasing source data. Validation produces a usable immutable Cube version. Application services create a seeded draft, accept commands through the API, persist state transactionally, and return player-appropriate views to CubeUI. Completed drafts feed provenance-aware analytics and later simulations.

CubeGame remains outside this path until a feasibility decision. If adopted, CubeUI communicates through CubeAI DTOs and never consumes Forge objects directly.

## Errors and resilience

Boundary errors distinguish transport failure, unsupported source data, unresolved cards, validation failure, stale commands, and illegal domain actions. Imports do not silently construct partially valid Cubes. Invalid entries retain source locations. Draft commands validate before mutation. External throttling, caching, retry limits, and provider-specific errors remain inside adapters.

## Testing

Randomness, clocks, and generated identifiers are controllable where necessary. Small synthetic Cubes test domain invariants; representative fixtures test import contracts. The same seed, Cube version, bot version, and configuration must reproduce a draft or simulation. API DTOs receive schema and contract tests. Critical UI flows receive focused browser tests after the UI exists.

## Planning strategy

M0 and M1 are decomposed into execution-ready issues. M2 has moderate detail. M3 through M5 identify capabilities and research. M6 through M9 remain high-level outcomes and must be refined using evidence from earlier milestones.

The repository contains documentation only at the end of this task. Product packages and configuration directories are created by M0 issues when they can include working tests and commands.

## Explicitly unresolved

- Exact Python and Node version floors and dependency managers.
- Whether FastAPI, React, and SQLite pass M0 validation and become accepted ADRs.
- CubeCobra's supported and stable import contract, including custom cards and historical data.
- Scryfall cache refresh, bulk-data, attribution, and image-use policies.
- The detailed schema and migration mechanism.
- Bot rating data sources and their licensing.
- Forge headless control, DTO translation, determinism, performance, upgrade strategy, and GPL implications.
- Multiplayer transport and hidden-information policy.

These uncertainties are backlog work, not permission to make silent implementation decisions.
