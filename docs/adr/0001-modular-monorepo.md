# ADR-0001: Use a Modular Monorepo

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

CubeAI has three conceptual workstreams: CubeLab, CubeUI, and CubeGame. They will share domain contracts and evolve together during early development. The project must be easy to run locally and easy for focused agentic sessions to navigate. It does not yet have operational requirements that justify independent deployment.

## Decision

CubeAI will use one Git repository with explicit component and package boundaries. CubeLab domain logic, API delivery, CubeUI, and a future game adapter may use different languages or toolchains, but their contracts, documentation, tests, and local orchestration will be versioned together.

The monorepo is modular, not a single undifferentiated application. Domain code must not depend on FastAPI, a database implementation, frontend types, or Forge objects. A component may be extracted later if measured deployment or ownership needs justify it.

Empty package trees will not be created solely to advertise the target structure. M0 issues will add each directory together with working configuration, tests, and commands.

## Alternatives considered

### Multiple repositories

This offers independent release histories but imposes contract versioning and cross-repository coordination before the project has stable interfaces or separate teams.

### Independent services in one repository

This provides deployable seams immediately but introduces networking, orchestration, and failure modes that do not advance the local draft MVP.

### One tightly coupled application

This is initially simple but would allow UI, persistence, and external-provider types to leak into the CubeLab domain and make game-engine replacement harder.

## Consequences

- Cross-component changes can be reviewed and tested atomically.
- Local development and CI can use shared entry points.
- Boundaries require active enforcement through imports, schemas, and tests.
- A monorepo does not imply one runtime process forever.
- Extraction remains possible but is not planned without evidence.

## Revisit when

Independent release cadence, security isolation, scaling characteristics, or team ownership creates a demonstrated need that outweighs cross-repository coordination.
