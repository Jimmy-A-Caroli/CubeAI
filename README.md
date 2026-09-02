# CubeAI

CubeAI is an early-stage, open-source, web-first, local-capable platform for **Magic: The Gathering Cube** design, drafting, analytics, and simulation.

The project is focused on the Cube loop: import a Cube, validate it, draft it, understand the draft, simulate it, and use the resulting evidence to improve the Cube. It is not intended to compete with Magic Online or Arena as a general-purpose Magic platform.

## Status

CubeAI is in its repository-foundation phase, with the first CubeLab domain
foundation now underway. The completed work packages are M0-001 through
M0-003, M0-005, M0-008, M1-001, and M1-002. They establish locked Python and
React/TypeScript workspaces, synthetic-fixture policy, frontend quality checks,
the supported CubeCobra import contract, and immutable Cube/card identity and
membership domain types.

The `backend/` workspace provides framework-independent types for source
references, card and printing identities, Cube memberships, and immutable Cube
versions. The `frontend/` workspace provides the React/TypeScript foundation
and independent formatting, lint, typecheck, unit-test, and production-build
commands. No API endpoint, CubeCobra read adapter, metadata resolver, draft
engine, bot, persistence layer, or user-facing product workflow has been
implemented. The root aggregate command and integrated health slice remain later
M0 work.

The currently eligible work packages are M0-004, M0-009, M0-010, M1-003, and
M1-009. See the [initial backlog](docs/issues/INITIAL_BACKLOG.md) for their
dependencies and the canonical task state.

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

CubeCobra's supported import contract is documented, but its read adapter is
not implemented. Scryfall metadata/cache policy, persistence, deterministic
drafting, bots, analytics, simulation, gameplay, Forge feasibility, and all
hosted-service concerns remain future work or require further validation.

## Available local validation

Run these commands from the repository root:

```powershell
uv --directory backend sync --locked --all-groups
uv --directory backend run pytest -q tests
uv --directory backend build

corepack npm --prefix frontend ci
corepack npm --prefix frontend run format:check
corepack npm --prefix frontend run lint
corepack npm --prefix frontend run typecheck
corepack npm --prefix frontend test
corepack npm --prefix frontend run build
```

There is intentionally no root aggregate command yet; M0-006 depends on the
remaining backend quality work in M0-004.

## Contributing

Contribution processes are not open yet. Use the workspace-local commands in
[backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md)
for the available checks; root aggregate validation arrives in M0-006. Proposed
changes should begin as a focused issue or architectural proposal. Agentic
contributors must follow [AGENTS.md](AGENTS.md).

## License

CubeAI is licensed under the [MIT License](LICENSE). Dependencies and integrations retain their own licenses; Forge's GPL implications require explicit research before adoption.
