# CubeAI

CubeAI is an early-stage, open-source, web-first, local-capable platform for **Magic: The Gathering Cube** design, drafting, analytics, and simulation.

The project is focused on the Cube loop: import a Cube, validate it, draft it, understand the draft, simulate it, and use the resulting evidence to improve the Cube. It is not intended to compete with Magic Online or Arena as a general-purpose Magic platform.

## Status

CubeAI is in its repository-foundation phase, with the first CubeLab domain
foundation now underway. The completed work packages are M0-001 through
M0-005, M0-008 through M0-009, M1-001 through M1-003, and M1-009. They establish locked Python and
React/TypeScript workspaces, synthetic-fixture policy, frontend quality checks,
the supported CubeCobra import contract, and immutable Cube/card identity and
membership domain types. It also includes a minimal local connectivity slice:
the backend serves `GET /health` and CubeUI displays its resulting connection
status.

The `backend/` workspace provides framework-independent types for source
references, import candidates, card and printing identities, Cube memberships,
immutable Cube versions, and draft configuration/identity vocabulary. The `frontend/` workspace provides the React/TypeScript foundation
and independent formatting, lint, typecheck, unit-test, and production-build
commands. The M0 health endpoint is a connectivity proof only; it is not a
product API or an import, metadata, drafting, persistence, or gameplay
workflow.

The currently eligible agent-safe work packages are M0-006 and M0-010.
M1-005 is ready for research only; policy adoption is a human decision.
M1-004 remains blocked pending a human-authorized supervised repair. See the
[initial backlog](docs/issues/INITIAL_BACKLOG.md) for dependencies and the
canonical task state.

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

Run these commands from the repository root. The root runner uses only the
accepted `uv` backend environment and `corepack`/npm frontend tools, executes
child commands directly, and returns a failing child command's nonzero status.

```powershell
uv --directory backend run --locked python ../scripts/cubeai.py setup
uv --directory backend run --locked python ../scripts/cubeai.py format
uv --directory backend run --locked python ../scripts/cubeai.py check
uv --directory backend run --locked python ../scripts/cubeai.py test
```

`setup` installs the two locked workspaces. `format` intentionally rewrites
only backend and frontend source files using their existing formatters; `check`
is read-only and runs formatting verification, linting, type checks, and the
backend architecture boundary check. `test` runs both workspace test suites.
Focused workspace commands remain available in [backend/README.md](backend/README.md)
and [frontend/README.md](frontend/README.md).

To run the M0 connectivity slice, after `setup` run:

```powershell
uv --directory backend run --locked python ../scripts/cubeai.py dev
```

The runner starts the backend health server at
`http://127.0.0.1:8000/health` and Vite on its reported local URL (normally
`http://127.0.0.1:5173/`). Vite proxies `/health` to the local backend; open
the Vite URL to see `Backend connected`. Use `Ctrl+C` to stop the two local
processes. This command is intentionally minimal and does not add Docker,
deployment configuration, or durable local-service management.

The existing Make targets are optional shortcuts on hosts where Make is
available; the Python root-runner commands above are the supported
cross-platform-enough entry points.

For individual workspace validation, run:

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


## Dependency and license review

Before adding or upgrading a package, follow the reviewed
[dependency and license policy](docs/DEPENDENCY-LICENSE-POLICY.md). The
policy documents the required approval evidence, lockfile-based inventories,
license reports, failure behavior, and narrow temporary exceptions.

```powershell
uv --directory backend tree --locked
corepack npm --prefix frontend ls --package-lock-only --all

uv --directory backend run --locked python ../scripts/report_backend_licenses.py
node scripts/report_frontend_licenses.mjs

uv --directory backend run --locked pytest -q tests/test_dependency_license_reports.py
node --test scripts/report_frontend_licenses.test.mjs
```

On hosts with Make available, `make dependency-inventory`, `make
license-report`, and `make dependency-license-test` provide optional shortcuts
for the same commands.

## Contributing

Contribution processes are not open yet. Use the root commands above for
aggregate validation or the workspace-local commands in
[backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md)
while developing a focused change. Proposed changes should begin as a focused
issue or architectural proposal. Agentic contributors must follow
[AGENTS.md](AGENTS.md).

## License

CubeAI is licensed under the [MIT License](LICENSE). Dependencies and integrations retain their own licenses; Forge's GPL implications require explicit research before adoption.
