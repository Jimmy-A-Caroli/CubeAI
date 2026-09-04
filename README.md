# CubeAI

CubeAI is an early-stage, open-source, web-first, local-capable platform for **Magic: The Gathering Cube** design, drafting, analytics, and simulation.

The project is focused on the Cube loop: import a Cube, validate it, draft it, understand the draft, simulate it, and use the resulting evidence to improve the Cube. It is not intended to compete with Magic Online or Arena as a general-purpose Magic platform.

## Status

CubeAI has completed the Alpha-0 CubeLab draft-core boundary and the Alpha-1
M1 local-draft MVP. M1-001 through M1-018 provide a supported
CubeCobra read adapter, exact printing-ID Scryfall resolution with a local
cache, immutable Cube versions, capacity validation, deterministic allocation,
deterministic local draft state machine, raw-ranking Bot v0, local SQLite
restart persistence, a versioned local FastAPI contract, and a keyboard-ready
Cube import, validation, and human-seat drafting flow. The local draft UI now
uses existing resolved-metadata cache data to show canonical card images when
available, accessible card fallbacks/details when they are not, a result-first
pool, and completion-only human/Bot pick review. M1-018 has verified the
deterministic local end-to-end workflow and closes M1.

M2-001 adds a completed-draft observation foundation: deterministic,
event-derived cards-seen, pool-before-pick, and pick-history contexts with
actor and recorded Bot provenance. M2-002 derives first-return wheel facts for
specific draft instances from those observations, without strategic
interpretation. The observation context is exposed through a completion-only
API view; the Draft Inspector and all advice, metrics, and analytics interfaces
remain future work.

The `backend/` workspace keeps source candidates, card/printing identities,
Cube memberships, immutable versions, validation, allocation, and transitions
framework-independent. The `frontend/` workspace supplies the React/TypeScript
foundation and independent formatting, lint, typecheck, unit-test, and
production-build commands. The HTTP API and UI expose only a local,
one-human-seat draft view; import and validation diagnostics do not become
hidden client state.

The accepted Scryfall policy is exact printing-ID resolution, a durable local
cache, network calls only for required misses, and explicit
unavailable/custom/unresolved outcomes—without fuzzy fallback or bulk-data
infrastructure. The M1-004 adapter records populated supplementary CubeCobra
boards as non-blocking diagnostics while importing mainboard memberships only.
See the [initial backlog](docs/issues/INITIAL_BACKLOG.md) for canonical state
and dependencies.

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
- **Persistence:** repository interfaces backed by local SQLite snapshots and
  append-only event histories (ADR-0005).

The toolchain and the web-first/local-capable constraint are accepted in ADR-0003; offline implementation technology remains deferred. Other choices remain provisional. See [Architecture](docs/ARCHITECTURE.md) and the [roadmap](docs/ROADMAP.md).

## Development philosophy

CubeAI favors deterministic behavior, explicit data provenance, small replaceable components, strong tests, web-first operation, and local capability without a separate frontend. It deliberately avoids premature microservices, cloud infrastructure, authentication, billing, and production deployment concerns.

Development will be issue-driven. M0 and M1 are decomposed in the [initial backlog](docs/issues/INITIAL_BACKLOG.md); later milestones will be refined only after earlier work provides evidence.

## Current limitations

CubeCobra import and exact-ID metadata resolution are bounded adapters.
Deterministic local allocation/transitions, raw-ranking Bot v0, local SQLite
save/resume, and a focused import-to-human-draft UI are available through
framework-independent CubeLab boundaries. The metadata cache retains canonical
exact-printing image URLs but not image bytes: the browser renders the final
remote resource directly and falls back accessibly on absence or load failure.
Offline image caching is not implemented, and the browser never calls provider
APIs to resolve cards or receives raw provider/persistence payloads. Bot v0 is
a static raw-ranking baseline, not human-like drafting; archetype inference is
not implemented. Analytics beyond the completed-draft observation foundation,
simulation batches, gameplay, multiplayer, cloud hosting, and authentication
are future work or require further validation.

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

An opt-in public-source Checkpoint E smoke exercises one supported CubeCobra
snapshot through resolution, validation, allocation, and a completed
deterministic draft. It creates a temporary Scryfall cache by default and
prints aggregate evidence only; it is intentionally outside the default
offline test suite.

```powershell
uv --directory backend run --locked python ../scripts/alpha_checkpoint_e.py
```

To run the M0 connectivity slice, after `setup` run:

```powershell
uv --directory backend run --locked python ../scripts/cubeai.py dev
```

The runner starts the backend health server at
`http://127.0.0.1:8000/health` and Vite on its reported local URL (normally
`http://127.0.0.1:5173/`). Vite proxies `/health` and `/v1` to the local
backend; open the Vite URL to import a CubeCobra identifier, validate it, and
start or resume the one-human-seat draft. Use `Ctrl+C` to stop the two local
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
