# CubeAI

CubeAI is an early-stage, open-source, web-first, local-capable platform for **Magic: The Gathering Cube** design, drafting, analytics, and simulation.

The project is focused on the Cube loop: import a Cube, validate it, draft it, understand the draft, simulate it, and use the resulting evidence to improve the Cube. It is not intended to compete with Magic Online or Arena as a general-purpose Magic platform.

## Status

CubeAI is in its repository-foundation phase. The `backend/` Python workspace and `frontend/` React/TypeScript workspace are established with locked local commands and smoke tests. No API endpoint, draft engine, bot, persistence layer, or product workflow has been implemented; the root aggregate command and the integrated health slice remain later M0 work.

## Intended capabilities

- Import and normalize Cube lists, initially investigating CubeCobra as the primary source.
- Run deterministic local drafts with configurable seats, packs, and bot strategies.
- Explain and review picks, wheels, colors, curves, archetypes, and drafted pools.
- Simulate draft batches while keeping simulated and human data distinguishable.
- Compare Cube versions as reproducible experiments.
- Investigate actual gameplay behind a stable engine adapter, with Forge as a candidate rather than a settled dependency.

## Proposed architecture

CubeAI will begin as a modular monorepo:

- **CubeLab:** framework-independent Python domain logic for Cube data, drafting, bots, analytics, and simulation.
- **CubeAI API:** a proposed FastAPI application exposing versioned DTOs and application services.
- **CubeUI:** a proposed React and TypeScript web client, designed to preserve a future local/offline path in the same codebase.
- **CubeGame:** a future engine-neutral gameplay protocol, separated from any Forge adapter.
- **Persistence:** repository interfaces backed initially by SQLite, if validated during M0.

The toolchain and the web-first/local-capable constraint are accepted in ADR-0003; offline implementation technology remains deferred. Other choices remain provisional. See [Architecture](docs/ARCHITECTURE.md) and the [roadmap](docs/ROADMAP.md).

## Development philosophy

CubeAI favors deterministic behavior, explicit data provenance, small replaceable components, strong tests, web-first operation, and local capability without a separate frontend. It deliberately avoids premature microservices, cloud infrastructure, authentication, billing, and production deployment concerns.

Development will be issue-driven. M0 and M1 are decomposed in the [initial backlog](docs/issues/INITIAL_BACKLOG.md); later milestones will be refined only after earlier work provides evidence.

## Current limitations

Everything beyond documentation is currently unimplemented. CubeCobra integration contracts, Scryfall usage, the persistence approach, and Forge feasibility still require validation.

## Contributing

Contribution processes are not open yet. Use the workspace-local commands in [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for the available foundation checks; root aggregate validation arrives in M0-006. Proposed changes should begin as a focused issue or architectural proposal. Agentic contributors must follow [AGENTS.md](AGENTS.md).

## License

CubeAI is licensed under the [MIT License](LICENSE). Dependencies and integrations retain their own licenses; Forge's GPL implications require explicit research before adoption.
