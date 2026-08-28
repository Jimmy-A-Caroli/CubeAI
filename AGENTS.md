# Agent Development Guide

These instructions apply throughout the repository. More specific `AGENTS.md` files may add local rules but must not silently weaken these rules.

## Before starting

1. Read the relevant product, architecture, roadmap, milestone, and ADR documents.
2. Inspect all code and tests related to the issue before modifying them.
3. Work from one tracked issue or proposal with a verifiable outcome.
4. Confirm that every dependency is complete and the issue is marked `READY`.
5. Use a focused branch named with the `codex/` prefix unless a human requests otherwise.

If no issue is ready, report the blocker. Do not invent a large workaround or silently expand scope.

## Scope and decisions

- Implement only the selected issue. Do not refactor unrelated code.
- Prefer one issue per implementation unit and one independently reviewable change.
- Do not change fundamental architecture, major dependencies, public APIs, the game protocol, or milestone scope without explicit human approval.
- Record major decisions in an ADR or proposal before implementation.
- Explain and document justified public API changes. Preserve compatibility unless the issue explicitly changes it.
- Introduce dependencies only when their benefit, maintenance status, license, and simpler alternatives have been evaluated.
- Keep CubeLab useful independently of CubeGame and any particular game engine.

## Engineering rules

- Prefer deterministic behavior. Make randomness, clocks, identifiers, and external inputs injectable where tests need control.
- Preserve provenance. Never silently combine human, bot-generated, and gameplay-generated observations.
- Keep Oracle identity, printing identity, Cube membership, draft instance, and game instance distinct.
- Keep domain logic independent of web frameworks, database implementations, UI types, and external-service payloads.
- Validate data at boundaries and return diagnosable errors. Do not create partially valid domain objects silently.
- Use repository and adapter interfaces at replaceable boundaries; do not add services merely to imitate a distributed architecture.

## Tests and validation

- Write or update tests with every behavior change.
- Add a regression test for each bug fix whenever feasible.
- Use synthetic fixtures and fixed seeds for deterministic draft and simulation behavior.
- Add contract fixtures for external integrations and keep them free of secrets or private user data.
- Run the narrowest relevant tests while developing, then all repository validation required by the issue before completion.
- Report exact commands run and their results. Never claim tests passed without running them.

## Documentation and completion

- Update documentation when behavior, interfaces, development commands, or architectural assumptions change.
- Use an ADR for a durable, cross-component architectural decision; use a research report when evidence is still incomplete.
- Before completion, inspect the diff for unrelated changes, secrets, generated artifacts, and accidental API changes.
- Commit only when the task and environment authorize it.
- Provide a concise report of the outcome, files changed, tests run, remaining risks, and blockers.
- Mark work ready for human review; do not merge or close decisions on a human's behalf.

## Actions requiring human direction

Agents must stop and propose options before they:

- replace a major technology or persistence strategy;
- adopt or deeply integrate Forge or another game engine;
- change the CubeGame protocol;
- add authentication, cloud infrastructure, telemetry, or production deployment;
- create or redefine a major milestone;
- perform a large migration or unrelated refactor;
- change product requirements or combine datasets with different provenance.
