# ADR-0003: Record the initial toolchain and web-first, local-capable boundary

- **Status:** Accepted
- **Date:** 2026-09-01

## Context

M0-001 evaluated maintained, conventional tooling for the accepted modular
monorepo and `cubeai.lab` bounded context. Human review approved the proposed
runtime floors, package managers, lockfile policy, quality tools, native-first
workflow, and SQLite capability floor.

The same review establishes that CubeAI's primary frontend is web-first while
preserving a future path to appropriate local/offline operation in the same
frontend codebase. This records a boundary requirement, not premature offline
infrastructure.

## Decision

### Accepted now

- **Backend:** Python `>=3.14,<3.15`, uv 0.12.7, PEP 621 `pyproject.toml`,
  Hatchling 1.28, committed `uv.lock`, FastAPI 0.141.1, Pydantic 2.12.5,
  pytest 9.1.1, Ruff 0.16.0, mypy 2.3.1 in strict mode, and Import Linter 2.14.
- **Frontend:** Node `>=24,<25`, npm 11.19.1, committed `package-lock.json`,
  React 19.2.7, TypeScript 5.9.3 in strict mode, Vite 8.2.2, Vitest 4.1.11,
  React Testing Library 16.3.2, ESLint 10.9.1, typescript-eslint 8.67.0, and
  Prettier 3.9.6.
- **Repository workflow:** native developer commands first; a future root
  validation entrypoint shared by local development and CI; locked,
  reproducible installs; explicit reviewed lockfile upgrades only;
  least-privilege CI; and optional Compose only when an integrated slice gives
  it a concrete purpose.
- **Persistence capability:** standard-library `sqlite3` with SQLite 3.37+ for
  `STRICT` tables.
- **Web-first, local-capable:** CubeUI is a web application and online
  operation is the default and primary deployment model. Its future
  frontend/application boundary must not unnecessarily assume permanent
  connectivity and must permit appropriate local storage and local
  implementations of selected application ports/adapters without creating a
  separate frontend codebase.

The decision complements ADR-0001's modular monorepo and ADR-0002's
framework-independent CubeLab namespace. It does not alter their dependency
direction: domain and application logic remain independent of delivery and
adapter implementations.

## Deferred

The following are deliberately not selected by this ADR:

- PWA framework/plugin or a service-worker implementation;
- Electron, Tauri, or any desktop wrapper;
- IndexedDB or another browser-local storage technology;
- offline caching policy or implementation;
- synchronization protocol, reconnect behavior, or conflict-resolution
  semantics;
- local/remote replication architecture; and
- a second frontend application or separate desktop frontend.

Future work may evaluate these after a working vertical slice supplies concrete
requirements and evidence. A plausible PWA path is not an accepted technology
decision.

## Consequences

- M0-002 and M0-003 may create their respective workspaces using the selected
  toolchains; they remain separate, unstarted issues.
- Future UI/application code must retain a clear boundary around application
  operations and data access, but must not add speculative offline abstractions
  before an actual milestone needs them.
- `uv.lock` and `package-lock.json` become the reproducible resolution records
  when those workspaces are created; their upgrades require review.
- Docker/Compose, CI, storage implementation, API-client generation, and all
  offline technology remain outside this decision's implementation scope.

## Revisit when

Revisit individual deferred decisions only after a running vertical slice
demonstrates a supported offline/local use case, persistence need, or
reconnection requirement. Any selection of offline technology or a desktop
wrapper requires a separate evidence-backed decision record.
