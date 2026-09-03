# M0 — Repository Foundation

## Goal

Turn the documentation-only repository into a coherent, reproducible development environment without implementing product functionality.

## Exit criteria

- A clean clone has one documented setup path for supported developer platforms.
- Python and frontend version floors and dependency managers are explicit and locked.
- Backend domain and frontend smoke tests run through documented commands.
- A vertical smoke slice proves connectivity: backend `GET /health` returns `{"status": "ok"}` and the frontend status view shows `Backend connected`.
- Formatting, linting, type checking, tests, and documentation checks share one aggregate validation entry point.
- CI executes the same validation without hidden CI-only behavior.
- Package boundaries prevent the domain from importing API, persistence, or provider implementations.
- Synthetic fixture and external-contract fixture policies exist.
- Dependency and license review is reproducible.
- Contribution and issue workflows tell humans and agents how to select unblocked work.

## Work packages

| ID | Outcome | Depends on | State |
|---|---|---|---|
| M0-001 | Record toolchain and dependency-management decision | — | COMPLETE |
| M0-002 | Establish Python CubeLab workspace with a smoke test | M0-001 | COMPLETE |
| M0-003 | Establish React/TypeScript workspace with a smoke test | M0-001 | COMPLETE |
| M0-004 | Add backend quality and boundary checks | M0-002 | COMPLETE |
| M0-005 | Add frontend quality checks | M0-003 | COMPLETE |
| M0-006 | Provide aggregate developer commands | M0-004, M0-005 | COMPLETE |
| M0-007 | Add continuous integration | M0-006 | READY |
| M0-008 | Define fixture and test-data policy | M0-002 | COMPLETE |
| M0-009 | Add dependency and license reporting | M0-002, M0-003 | COMPLETE |
| M0-010 | Add issue and proposal templates | — | READY |
| M0-011 | Add minimal local orchestration | M0-006 | READY |
| M0-012 | Verify clean-clone onboarding and accept M0 | M0-007, M0-008, M0-009, M0-010, M0-011 | BLOCKED |

Full issue definitions are in [the initial backlog](../issues/INITIAL_BACKLOG.md).

## Vertical smoke slice

M0's smallest integrated proof is:

```text
backend GET /health → {"status": "ok"}
frontend status view → "Backend connected"
```

M0-002 prepares the backend side, M0-003 prepares the frontend side, M0-006 joins them under one developer entry point, M0-007 validates the slice in CI where practical, and M0-011 runs it locally. M0-001 may refine the endpoint wording or response schema while selecting the toolchains. This is a connectivity proof only; it does not introduce product functionality.

## Supported initial boundaries

M0 should create the smallest useful workspaces:

- `backend/src/cubeai/lab/domain/` for framework-independent code;
- `backend/src/cubeai/lab/application/` for use-case orchestration and ports;
- `backend/src/cubeai/api/` only when an API smoke test is justified;
- `backend/src/cubeai/adapters/` for later persistence and providers;
- `backend/tests/` organized primarily by behavior/boundary;
- `frontend/` for the user interface and API client boundary.

Naming may be refined by M0-001, but a change to the component model requires explicit review.

## Non-goals

- Cube, card, or draft domain models beyond a minimal smoke-test type.
- External API calls.
- Database schema or migrations.
- Draft UI.
- Docker images that do not run a meaningful development slice.
- Forge, Java, cloud services, accounts, or deployment.

## Risks and decisions

M0-001 must compare currently supported versions and tooling rather than copy arbitrary defaults. M0-011 should prefer native development commands plus a small Compose option; Docker must not become mandatory for basic tests if local toolchains are available.
