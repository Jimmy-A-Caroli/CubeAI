# Initial Issue Backlog

This file is the source backlog until a remote issue tracker is intentionally configured. Issue IDs are stable references. An issue is `READY` only when every dependency is complete and no listed human decision remains.

## Planning authority and remote-tracker transition

`INITIAL_BACKLOG.md` owns planning scope during early M0 and is the planning source of truth. When a remote issue is created, the Markdown entry records its URL and stops duplicating execution state; the remote issue owns execution state: assignee, status, discussion, and closure.

## Labels

- Components: `component::lab`, `component::game`, `component::ui`, `component::infra`, `component::docs`
- Types: `type::feature`, `type::bug`, `type::refactor`, `type::test`, `type::research`, `type::proposal`
- Priorities: `priority::high`, `priority::medium`, `priority::low`
- Suitability: `agent::safe`, `agent::supervised`, `human::decision`
- State: `READY`, `BLOCKED`, `COMPLETE`

`agent::safe` means requirements and dependencies are sufficiently bounded for autonomous implementation. `agent::supervised` requires review of assumptions or external contracts. `human::decision` produces or requires an explicit choice.

## M0 — Repository Foundation

### M0-001 — Select and record the initial toolchains

- **Labels/state:** `component::infra`, `type::proposal`, `priority::high`, `human::decision`, `COMPLETE`
- **Dependencies:** None.
- **Goal/context:** Turn the provisional Python/FastAPI and React/TypeScript direction into exact, supportable version floors, dependency managers, lockfile policy, package layout, and developer commands.
- **Scope:** Compare maintained versions and boring tooling; document Python, Node, package managers, test/lint/type/format tools, lockfiles, and local/CI compatibility; record approved decisions and the web-first/local-capable boundary in an ADR after review.
- **Out of scope:** Installing workspaces, domain models, APIs, UI, Docker, or CI.
- **Acceptance criteria:** A proposal recommends one coherent toolchain; alternatives and migration cost are recorded; licenses and platform support are checked; approval converts decisions into ADRs without treating Forge as adopted.
- **Required tests:** Documentation link check and command/version examples manually validated against upstream documentation.
- **Expected artifacts/areas:** `docs/research/`, `docs/adr/`, README development prerequisites.

The accepted decision is documented in [the toolchain evaluation](../research/toolchain-evaluation.md) and [ADR-0003](../adr/0003-initial-toolchain-and-web-first-local-capable.md). M0-002 and M0-003 are `READY`; all other dependency relationships are unchanged.

### M0-002 — Establish the Python CubeLab workspace

- **Labels/state:** `component::lab`, `component::infra`, `type::feature`, `priority::high`, `agent::safe`, `READY`
- **Dependencies:** M0-001.
- **Goal/context:** Create the first executable domain boundary using the approved Python toolchain.
- **Scope:** Package metadata and lockfile; `cubeai.lab.domain` and `cubeai.lab.application` packages; one trivial framework-free domain value and smoke test; prepare the backend half of the M0 `GET /health` connectivity proof; documented install and test commands.
- **Out of scope:** Cards, Cubes, drafts, FastAPI endpoints, SQL, external calls, and Docker.
- **Acceptance criteria:** Clean environment installs reproducibly; package imports without path hacks; smoke test passes; no framework or adapter import exists in the domain package; the workspace can expose the M0 `GET /health` status response through the outer API boundary once M0-006 joins the slice.
- **Required tests:** Package import test, domain smoke unit test, build/install check.
- **Expected artifacts/areas:** `backend/`, backend README or root development documentation.

### M0-003 — Establish the React and TypeScript workspace

- **Labels/state:** `component::ui`, `component::infra`, `type::feature`, `priority::high`, `agent::safe`, `READY`
- **Dependencies:** M0-001.
- **Goal/context:** Create a minimal, tested UI workspace using the approved frontend toolchain.
- **Scope:** Locked dependencies, strict TypeScript configuration, one accessible status component showing the M0 `Backend connected` state, unit test, development/build commands; prepare the frontend half of the connectivity proof.
- **Out of scope:** Cube import, drafting, API client generation, design system, routing beyond what the smoke slice needs.
- **Acceptance criteria:** Clean install is reproducible; dev and production builds start; strict type check passes; test asserts the user-visible `Backend connected` status content; no backend implementation types are copied into the UI.
- **Required tests:** Component unit/accessibility smoke test, TypeScript check, production build.
- **Expected artifacts/areas:** `frontend/`, development documentation.

### M0-004 — Add backend quality and architecture-boundary checks

- **Labels/state:** `component::lab`, `component::infra`, `type::test`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M0-002.
- **Goal/context:** Make formatting, linting, typing, tests, and forbidden dependency directions enforceable.
- **Scope:** Configure approved formatter/linter/type checker; add a check that domain cannot import API, adapters, persistence, or FastAPI; document commands.
- **Out of scope:** High coverage targets or checking nonexistent product behavior.
- **Acceptance criteria:** Each check has a focused command; an intentionally forbidden import makes the boundary test fail; generated/cache directories are excluded explicitly.
- **Required tests:** Run all backend checks and a temporary negative boundary fixture/test.
- **Expected artifacts/areas:** backend configuration and tests, developer docs.

### M0-005 — Add frontend quality checks

- **Labels/state:** `component::ui`, `component::infra`, `type::test`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M0-003.
- **Goal/context:** Establish consistent frontend formatting, linting, typing, tests, and accessible component defaults.
- **Scope:** Configure approved checks with non-overlapping responsibility and document focused commands.
- **Out of scope:** End-to-end browser infrastructure or broad style rules unrelated to correctness.
- **Acceptance criteria:** Format check, lint, strict type check, unit tests, and build pass independently; accessibility test detects a representative invalid component.
- **Required tests:** Run each check and production build from a clean dependency install.
- **Expected artifacts/areas:** frontend configuration, tests, developer docs.

### M0-006 — Provide aggregate developer commands

- **Labels/state:** `component::infra`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M0-004, M0-005.
- **Goal/context:** Give humans and agents stable commands instead of tool-specific guesswork.
- **Scope:** Add cross-platform-enough entry points for setup, format, check, test, and development; join the backend health endpoint and frontend status view into the M0 connectivity slice; delegate to workspace tools without hiding errors.
- **Out of scope:** Production packaging and deployment.
- **Acceptance criteria:** Root documentation lists each command; aggregate check returns nonzero on any child failure; focused backend/frontend commands remain available; the documented development entry point joins `GET /health` with the `Backend connected` status view; no command modifies unrelated source unexpectedly.
- **Required tests:** Clean setup followed by aggregate validation; inject one controlled failure to verify propagation.
- **Expected artifacts/areas:** root task runner or scripts, README.

### M0-007 — Add continuous integration

- **Labels/state:** `component::infra`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M0-006.
- **Goal/context:** Run the same repository validation on proposed changes.
- **Scope:** Minimal GitHub Actions workflow with dependency caching, locked installs, aggregate checks, least necessary permissions, cancellation of superseded runs, and M0 connectivity-slice validation where practical in CI.
- **Out of scope:** Deployment, release publishing, coverage services, multi-platform matrices without evidence.
- **Acceptance criteria:** CI invokes documented commands rather than duplicating logic; lockfile changes invalidate caches; workflow has read-only default permissions; the connectivity slice is validated in CI where practical; status is documented.
- **Required tests:** Local workflow syntax validation where supported and one successful remote run before issue acceptance.
- **Expected artifacts/areas:** `.github/workflows/`, README.

### M0-008 — Define fixture and test-data policy

- **Labels/state:** `component::lab`, `component::docs`, `type::proposal`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M0-002.
- **Goal/context:** Provide safe, deterministic fixtures before external payloads enter the repository.
- **Scope:** Define synthetic Cube sizes/purposes, naming, provenance, update procedure, sanitization, licensing, and contract-fixture review; add the smallest synthetic fixture with schema/test.
- **Out of scope:** Copying a private or complete third-party Cube, CubeCobra calls, Scryfall bulk data.
- **Acceptance criteria:** Fixture policy forbids secrets/private data; every fixture states source/license; synthetic fixture represents duplicate memberships and unresolved/custom identity cases; test validates its declared shape.
- **Required tests:** Fixture schema/shape validation and secret-pattern scan.
- **Expected artifacts/areas:** `fixtures/`, test helpers, documentation.

### M0-009 — Add dependency and license reporting

- **Labels/state:** `component::infra`, `type::test`, `priority::medium`, `agent::safe`, `BLOCKED`
- **Dependencies:** M0-002, M0-003.
- **Goal/context:** Make dependency review repeatable before Forge or data packages introduce risk.
- **Scope:** Document dependency approval criteria; add reproducible inventory/license commands for both workspaces; define failure/allowlist policy.
- **Out of scope:** Legal conclusions about Forge or automated license compatibility guarantees.
- **Acceptance criteria:** Direct and transitive dependencies can be inventoried from locks; unknown/disallowed licenses are visible; reports do not need committing unless documented.
- **Required tests:** Run inventory commands on clean locks and verify a controlled unknown license is surfaced.
- **Expected artifacts/areas:** scripts/configuration, dependency policy documentation.

### M0-010 — Add issue and proposal templates

- **Labels/state:** `component::docs`, `type::feature`, `priority::medium`, `agent::safe`, `READY`
- **Dependencies:** None.
- **Goal/context:** Preserve the backlog's scope and verification standards when work moves to GitHub.
- **Scope:** Feature/bug/research/proposal templates containing goal, context, scope, exclusions, dependencies, acceptance criteria, tests, artifacts, and agent suitability; concise pull-request checklist.
- **Out of scope:** Creating remote issues, labels, projects, or automation.
- **Acceptance criteria:** Templates map to documented labels and issue fields; proposal template calls out human decisions and ADR impact; bug template asks for regression coverage.
- **Required tests:** Template syntax validation and manual dry run for one M0 issue.
- **Expected artifacts/areas:** `.github/ISSUE_TEMPLATE/`, pull-request template, docs links.

### M0-011 — Add minimal local orchestration

- **Labels/state:** `component::infra`, `type::feature`, `priority::medium`, `agent::safe`, `BLOCKED`
- **Dependencies:** M0-006.
- **Goal/context:** Start the first meaningful backend/frontend development slice with a simple command.
- **Scope:** Add local process orchestration and, if justified, a small Compose configuration; run the M0 connectivity slice locally with health/status behavior and clean shutdown; preserve native commands.
- **Out of scope:** PostgreSQL, reverse proxies, authentication, production images, Kubernetes, observability stacks.
- **Acceptance criteria:** Documented start command brings up `GET /health` and the `Backend connected` status slice locally; ports/config are explicit; shutdown leaves no persistent mystery state; native tests do not require Docker.
- **Required tests:** Startup/health/shutdown smoke test and configuration validation.
- **Expected artifacts/areas:** root scripts/task runner, optional `compose.yaml`, README.

### M0-012 — Verify clean-clone onboarding and accept M0

- **Labels/state:** `component::infra`, `component::docs`, `type::test`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M0-007, M0-008, M0-009, M0-010, M0-011.
- **Goal/context:** Prove the repository foundation works outside an existing developer environment.
- **Scope:** Follow documentation from a clean clone/environment; record duration, prerequisites, commands, failures, and CI result; correct only M0 documentation/setup defects.
- **Out of scope:** Product models or M1 work.
- **Acceptance criteria:** Setup and aggregate validation succeed exactly as documented; local status slice runs; CI is green; M0 exit criteria have evidence; remaining limitations are recorded.
- **Required tests:** Full clean-clone setup, validation, and runtime smoke test.
- **Expected artifacts/areas:** onboarding report, README corrections, M0 status update.

## M1 — Cube Import and Local Draft MVP

### M1-001 — Research and freeze the supported CubeCobra import contract

- **Labels/state:** `component::lab`, `type::research`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M0-008.
- **Goal/context:** Establish a supported read contract without hardcoding an undocumented route assumption.
- **Scope:** Review current official API/export documentation and terms; probe public test Cubes; catalog IDs, boards, tags, printings, duplicates, custom cards, errors, caching guidance, and historical-draft availability; save sanitized fixtures and recommend one contract.
- **Out of scope:** Write access, production adapter, scraping UI HTML, or bulk dataset download.
- **Acceptance criteria:** Report distinguishes documented guarantees from observations; fixtures cover normal, duplicate, custom/unresolved, and error cases where available; change-detection/update procedure exists; human approves supported contract.
- **Required tests:** Fixture schema checks and replayable response parsing probe labeled as research.
- **Expected artifacts/areas:** `docs/research/cubecobra-import.md`, `fixtures/contracts/cubecobra/`.

### M1-002 — Model card and Cube identities

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M0-002.
- **Goal/context:** Prevent rules identity, printing, Cube membership, and Cube version from being conflated.
- **Scope:** Immutable domain values/entities for `CardIdentity`, `CardPrinting`, `Cube`, `CubeVersion`, and `CubeCard`; local IDs; source references; duplicates; custom/unresolved resolution status.
- **Out of scope:** HTTP payloads, database models, live metadata, draft instances, image downloading.
- **Acceptance criteria:** Two printings can share one identity; two memberships can reference the same printing; versions are immutable; custom identity need not fabricate Oracle ID; invalid identifiers fail diagnostically.
- **Required tests:** Identity equality/scope, duplicate memberships, version immutability, custom/unresolved cases, serialization-neutral construction.
- **Expected artifacts/areas:** CubeLab domain and tests, architecture docs if names change.

### M1-003 — Define import candidates and the Cube source port

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-001, M1-002.
- **Goal/context:** Terminate provider payloads at an explicit boundary before normalization.
- **Scope:** Provider-neutral source request, source snapshot reference, import candidate, severity-coded diagnostic, and source adapter protocol; preserve raw field references without embedding full payloads in domain entities.
- **Out of scope:** HTTP client, Scryfall matching, persistence, acceptance of invalid Cubes.
- **Acceptance criteria:** Candidates represent duplicates, board/location, tags, notes, printing hints, and custom data; failures distinguish transport, unsupported contract, and record diagnostics; no CubeCobra type enters domain entities.
- **Required tests:** Protocol fake, candidate mapping cases, stable diagnostic codes, malformed input behavior.
- **Expected artifacts/areas:** application ports/import types and tests.

### M1-004 — Implement the CubeCobra read adapter

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M1-003.
- **Goal/context:** Import the approved CubeCobra contract through the provider-neutral port.
- **Scope:** URL/identifier parsing, responsible HTTP behavior, supported response mapping, bounded timeout/retry, cache validators if supported, structured failures, contract fixtures.
- **Out of scope:** Undocumented fallback scraping, write access, Scryfall resolution, database storage.
- **Acceptance criteria:** Fixture cases map deterministically; invalid IDs and unsupported payload versions are distinct; configured user agent and timeouts exist; raw provider exceptions do not escape the adapter.
- **Required tests:** Offline contract tests for all fixtures, HTTP fake tests for timeout/rate/error behavior, one opt-in live smoke test excluded from default suite.
- **Expected artifacts/areas:** external adapter, tests, CubeCobra research updates.

### M1-005 — Define the Scryfall metadata and cache policy

- **Labels/state:** `component::lab`, `type::research`, `priority::high`, `human::decision`, `BLOCKED`
- **Dependencies:** M0-009.
- **Goal/context:** Use Scryfall responsibly and choose when live collection lookup versus bulk data is appropriate.
- **Scope:** Official API/bulk guidance, identifiers, attribution, images, required headers, throttling, retries, cache refresh, offline behavior, custom cards, and data/license implications; recommend M1 strategy.
- **Out of scope:** Adapter implementation or downloading the full dataset into Git.
- **Acceptance criteria:** Policy states exact client behavior and cache invalidation; separates Oracle and printing IDs; documents unavailable/ambiguous resolution; has human approval.
- **Required tests:** Validate documented example requests and bulk metadata shape with a small sanitized sample.
- **Expected artifacts/areas:** `docs/research/scryfall-metadata.md`, proposed ADR if warranted.

### M1-006 — Define metadata resolution and implement the Scryfall adapter

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M1-002, M1-005.
- **Goal/context:** Resolve import candidates without hiding ambiguity or coupling domain entities to Scryfall payloads.
- **Scope:** Resolver port; batch identifiers; exact printing and Oracle resolution; cache implementation approved by policy; structured missing/ambiguous/custom outcomes.
- **Out of scope:** Fuzzy auto-acceptance without evidence, price analytics, image mirroring, full search UI.
- **Acceptance criteria:** Resolution prefers stable IDs over names; cached repeated resolution avoids redundant traffic; provider throttling is enforced; custom/unresolved outcomes preserve candidate data; mappings are deterministic for a metadata snapshot.
- **Required tests:** Fixture contract tests, cache hit/stale behavior, batch mapping, ambiguity/missing cases, rate-limit fake.
- **Expected artifacts/areas:** metadata port/adapter/cache, tests, fixtures.

### M1-007 — Assemble immutable Cube versions

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-004, M1-006.
- **Goal/context:** Combine source candidates and resolution results into a reviewable version without partial silent acceptance.
- **Scope:** Import application service, version fingerprint/identity, resolved memberships, diagnostics summary, source snapshot link, explicit usability state.
- **Out of scope:** Draft-capacity rules, persistence schema, UI.
- **Acceptance criteria:** Same normalized source snapshot yields equivalent content fingerprint; changed membership yields a new version; diagnostics retain membership/source context; unusable imports cannot masquerade as validated versions.
- **Required tests:** Normal, duplicate, unresolved/custom, changed-version, and deterministic fingerprint scenarios.
- **Expected artifacts/areas:** application service/domain tests.

### M1-008 — Validate Cube contents and draft capacity

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-007.
- **Goal/context:** Explain whether a Cube version supports a requested draft before allocation.
- **Scope:** Severity-coded validation for usable memberships, unresolved cards, duplicate semantics, configured seats/packs/pack size, excess cards, and unsupported custom behavior.
- **Out of scope:** Subjective Cube quality, archetype balance, automatic fixes, pack allocation.
- **Acceptance criteria:** Required size is computed safely; too-small Cube is an error; excess is permitted by explicit allocation policy; duplicate names are not inherently errors; messages identify affected membership/configuration.
- **Required tests:** Exact size, too small, excess, zero/invalid configuration, duplicates, unresolved/custom policy cases.
- **Expected artifacts/areas:** domain validation and application tests.

### M1-009 — Define draft entities and configuration

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-002.
- **Goal/context:** Establish lifecycle-specific identities and provenance before algorithms mutate state.
- **Scope:** `Draft`, configuration, seat, pack, draft-card instance, pick event, pool view, status, actor origin, bot strategy reference; invariants and explicit ordering.
- **Out of scope:** Pack allocation algorithm, bot scoring, persistence, API DTOs.
- **Acceptance criteria:** Draft instances are distinct from Cube memberships; configuration supports seat/pack/size/seed; picks carry actor provenance; invalid status/configuration transitions cannot be constructed silently.
- **Required tests:** Identity scopes, configuration validation, provenance variants, pack/pick invariants, immutable event ordering.
- **Expected artifacts/areas:** CubeLab draft domain and tests.

### M1-010 — Allocate deterministic packs

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-008, M1-009.
- **Goal/context:** Allocate a valid Cube version into packs reproducibly without duplicating membership instances.
- **Scope:** Seeded sampling/shuffle policy, stable pre-randomization ordering, draft-card instance creation, configurable geometry, and explicit excess-card handling.
- **Out of scope:** Collation by rarity/theme, custom pack structures, pack passing, bot picks.
- **Acceptance criteria:** Same version/configuration/seed yields identical pack contents/order; each selected membership occurs exactly once; insufficient Cube fails before allocation; different seeds are not required to differ but are tested statistically only where appropriate.
- **Required tests:** Golden seed, conservation/uniqueness invariant, duplicate memberships, exact/excess/insufficient sizes, invalid configuration.
- **Expected artifacts/areas:** draft allocation domain service and tests.

### M1-011 — Implement draft state transitions and pack rotation

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-010.
- **Goal/context:** Advance simultaneous draft rounds correctly through alternating directions.
- **Scope:** Start pack, legal pick command, one pick per active seat per round, pack transfer, left/right alternation by pack number, empty-pack handling, completion, pools and immutable pick events.
- **Out of scope:** Timers, networking, bots, advice, persistence.
- **Acceptance criteria:** Stale/illegal picks do not mutate state; no instance is picked twice or lost; direction alternates; draft completes only after every allocated card is picked; seat-visible view exposes appropriate current pack and public progress.
- **Required tests:** Two- and eight-seat golden scenarios, direction changes, stale/wrong-seat/card errors, conservation invariant, completion and pool derivation.
- **Expected artifacts/areas:** draft state machine, commands/views, tests.

### M1-012 — Define the bot port and Bot v0 rating policy

- **Labels/state:** `component::lab`, `type::research`, `type::feature`, `priority::high`, `human::decision`, `BLOCKED`
- **Dependencies:** M1-009.
- **Goal/context:** Establish a transparent raw-ranking bot with licensed, versioned data and deterministic tie-breaking.
- **Scope:** Strategy input/output port limited to visible state; rating dataset/source investigation; missing-rating fallback; strategy ID/version/configuration; score explanation and tie policy.
- **Out of scope:** Color preference, curve, archetypes, synergy, learning, human-likeness claims.
- **Acceptance criteria:** Rating source and license are approved; no hidden information enters strategy input; all legal cards receive a deterministic comparable score; decision records rating and tie-break reason.
- **Required tests:** Ordered ratings, equal scores, missing ratings, duplicate card names/printings, input visibility, stable version/config serialization.
- **Expected artifacts/areas:** bot domain port, rating data policy/artifact, tests, research note.

### M1-013 — Execute deterministic bot turns

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-011, M1-012.
- **Goal/context:** Advance seven bot seats around each human decision while retaining strategy provenance.
- **Scope:** Bot-turn application service, per-seat strategy configuration, deterministic RNG derivation, legal-choice validation, failure behavior, bot pick events.
- **Out of scope:** Parallel bot execution, timeouts across processes, advanced strategies, simulation batches.
- **Acceptance criteria:** Same draft/strategy/seed yields identical bot choices; every bot event names strategy/version; illegal strategy output aborts without corrupting state; human view stops at the next human decision.
- **Required tests:** One-human/seven-bot golden draft segment, mixed strategy fake, illegal output rollback, deterministic RNG isolation, complete bot-only round.
- **Expected artifacts/areas:** application service and tests.

### M1-014 — Persist Cube versions and drafts in SQLite

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M1-007, M1-013.
- **Goal/context:** Support local restart and future schema evolution without leaking SQL models into the domain.
- **Scope:** Repository ports, approved schema/migration tool, SQLite adapters, transaction boundary for pick plus bot turns, version/event persistence and rehydration.
- **Out of scope:** PostgreSQL, cloud backups, cross-device sync, analytics warehouse.
- **Acceptance criteria:** Persisted drafts rehydrate equivalently; immutable events/versions cannot be silently overwritten; transaction failure leaves prior state intact; migrations work from empty database; SQLite types remain in adapter layer.
- **Required tests:** Temporary-database repository contract suite, rollback injection, restart/rehydration, migration-up test, duplicate ID/conflict behavior.
- **Expected artifacts/areas:** persistence ports/adapters/migrations and tests; ADR for persistence/migrations after review.

### M1-015 — Expose the local draft API

- **Labels/state:** `component::lab`, `component::ui`, `type::feature`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M1-008, M1-013, M1-014.
- **Goal/context:** Provide the smallest versioned HTTP contract needed for import, validation, draft commands, and seat-safe views.
- **Scope:** Proposed FastAPI app; DTO mapping; endpoints to import/inspect Cube version, start/resume draft, submit a pick, and read current/complete human-seat view; stable error envelope and local configuration.
- **Out of scope:** Authentication, WebSockets, analytics, admin endpoints, exposing persistence/provider models.
- **Acceptance criteria:** OpenAPI describes versioned DTOs; illegal/stale commands use stable codes and do not mutate state; views omit other seats' current packs/pools; provider errors map safely; health endpoint reflects local readiness.
- **Required tests:** API integration tests for happy path, validation errors, stale/illegal picks, provider failure, restart/resume, and hidden-information assertions; schema snapshot/compatibility check.
- **Expected artifacts/areas:** API package, DTOs/mappers, tests, API documentation.

### M1-016 — Build Cube import and validation UI

- **Labels/state:** `component::ui`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-015, M0-005.
- **Goal/context:** Let a local user enter a CubeCobra URL/ID and understand whether the Cube is draftable.
- **Scope:** Source form, loading/error states, Cube/version summary, grouped diagnostics with affected entries, retry, and start-draft configuration/defaults.
- **Out of scope:** Cube editing, source authentication, analytics dashboard, visual design system overhaul.
- **Acceptance criteria:** Keyboard-accessible workflow; network, unsupported source, unresolved entry, and capacity problems are distinguishable; user cannot start an unusable Cube; supported warnings remain visible.
- **Required tests:** Component tests for every state, accessibility checks, API-client contract mocks, one browser happy/error flow.
- **Expected artifacts/areas:** frontend feature components/client/types/tests.

### M1-017 — Build pack, pick, and drafted-pool UI

- **Labels/state:** `component::ui`, `type::feature`, `priority::high`, `agent::safe`, `BLOCKED`
- **Dependencies:** M1-015, M0-005.
- **Goal/context:** Complete a draft quickly with a clear current pack, selected card, progress, and pool.
- **Scope:** Current pack grid/list, card detail on demand, pick confirmation/command state, pack/seat progress, drafted pool grouped by a simple deterministic view, completion state, resume/error recovery.
- **Out of scope:** Drag-and-drop requirement, cards-seen history, wheels, advice, curve, archetypes, deck building, animation polish.
- **Acceptance criteria:** Legal card selection and pending command are unambiguous; duplicate cards/printings remain distinguishable; stale pick refreshes safely; keyboard flow can complete a pick; only API-provided information is displayed.
- **Required tests:** Component and accessibility tests, duplicate/stale/loading/error states, browser flow over a small fixture draft.
- **Expected artifacts/areas:** frontend draft feature/client/tests.

### M1-018 — Verify the deterministic local draft MVP

- **Labels/state:** `component::lab`, `component::ui`, `component::infra`, `type::test`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M1-016, M1-017.
- **Goal/context:** Prove the milestone from clean setup through completed draft and restart behavior.
- **Scope:** Fixed synthetic/contract fixture acceptance scenario; same-seed replay comparison; supported public Cube opt-in smoke; documentation and measured usability/performance notes; M1 exit review.
- **Out of scope:** Fixes that expand into M2, bot improvements, gameplay, production load claims.
- **Acceptance criteria:** Clean local workflow imports, validates, drafts, persists/resumes, and completes; golden replay matches pack/pick/pool event data; human/bot provenance is queryable; M1 non-goals remain absent; known limitations are documented.
- **Required tests:** Full local/browser acceptance, deterministic replay diff, restart/resume, aggregate CI suite, opt-in live-source smoke.
- **Expected artifacts/areas:** acceptance tests, README quick start, M1 acceptance report.

## M2 — Draft Intelligence and Analytics

M2 issues are intentionally moderate-detail and remain `BLOCKED` until M1-018 and schema refinement.

### M2-001 — Derive cards-seen and pick-history projections

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M1-018.
- **Goal/context:** Reconstruct seat-visible history from immutable draft events.
- **Scope/out of scope:** Define projections and API views; do not add advice or mutate event truth.
- **Acceptance criteria:** Every visible pack and pick is reproducible with duplicate-instance identity and correct visibility.
- **Required tests:** Golden event projection and hidden-information cases.
- **Expected artifacts/areas:** analytics projections/API/tests.

### M2-002 — Define and implement wheel detection

- **Labels/state:** `component::lab`, `type::feature`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M2-001.
- **Goal/context:** Identify returning card instances for configurable seats and packs.
- **Scope/out of scope:** Formal wheel definition and event-derived result; no strategic judgment.
- **Acceptance criteria:** Results use instance IDs and handle small seat counts, exhausted packs, and duplicate names.
- **Required tests:** Direction/seat-count golden scenarios and duplicates.
- **Expected artifacts/areas:** analysis model/tests/docs.

### M2-003 — Add tracked-card behavior

- **Labels/state:** `component::ui`, `type::feature`, `priority::medium`, `agent::safe`, `BLOCKED`
- **Dependencies:** M2-001.
- **Goal/context:** Let users mark seen instances for later attention without altering draft state.
- **Scope/out of scope:** Local tracking and wheel/history linkage; no automated recommendations.
- **Acceptance criteria:** Tracking survives supported resume and distinguishes instances with the same name.
- **Required tests:** UI/state persistence and removed/returned-card cases.
- **Expected artifacts/areas:** UI, local preference/application port, tests.

### M2-004 — Add mana curve and color projections

- **Labels/state:** `component::lab`, `component::ui`, `type::feature`, `priority::high`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M1-018.
- **Goal/context:** Show pool shape using documented card-face and land rules.
- **Scope/out of scope:** Curve, colors, color identity, user inclusion toggles; no castability claim yet.
- **Acceptance criteria:** Metric definitions are visible and deterministic for modal/multi-face/land fixtures.
- **Required tests:** Representative card-layout fixtures and UI rendering.
- **Expected artifacts/areas:** projections/API/UI/tests.

### M2-005 — Model mana requirements and sources

- **Labels/state:** `component::lab`, `type::research`, `type::feature`, `priority::medium`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M2-004.
- **Goal/context:** Separate colored requirements from potential mana sources and communicate uncertainty.
- **Scope/out of scope:** Versioned heuristic and explanation; not a complete deck optimizer.
- **Acceptance criteria:** Hybrid, phyrexian, colorless, variable, modal, and fixing cases have documented behavior.
- **Required tests:** Synthetic mana-symbol/source matrix.
- **Expected artifacts/areas:** research note, projection, tests, UI explanation.

### M2-006 — Define a versioned archetype/tag vocabulary

- **Labels/state:** `component::lab`, `type::proposal`, `priority::medium`, `human::decision`, `BLOCKED`
- **Dependencies:** M1-007.
- **Goal/context:** Represent Cube-specific archetypes and card roles without pretending one universal taxonomy exists.
- **Scope/out of scope:** Schema, source, version, confidence, overrides, and fixture; no auto-tagging ML.
- **Acceptance criteria:** Tags can be Cube-specific, multi-valued, explainable, and migrated/versioned.
- **Required tests:** Schema validation and override/unknown cases.
- **Expected artifacts/areas:** proposal/ADR, domain schema, fixture.

### M2-007 — Add explainable draft-fit features

- **Labels/state:** `component::lab`, `type::feature`, `priority::medium`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M2-004, M2-006.
- **Goal/context:** Decompose advice into power, openness, curve, synergy, and pool fit.
- **Scope/out of scope:** Versioned heuristics and explanations; no single opaque truth score or ML.
- **Acceptance criteria:** Each output lists inputs/contributions and uncertainty; missing tags/ratings degrade visibly.
- **Required tests:** Fixed-pool feature scenarios and missing-data behavior.
- **Expected artifacts/areas:** analysis services/API/tests.

### M2-008 — Build post-draft Draft Inspector and timeline review

- **Labels/state:** `component::ui`, `type::feature`, `priority::medium`, `agent::safe`, `BLOCKED`
- **Dependencies:** M2-001, M2-007.
- **Goal/context:** Provide the first full Draft Inspector by replaying each decision with information actually available at that time.
- **Scope/out of scope:** Accessible timeline/replay, pack/pick/pool snapshot, seat context, derivable cards-seen history, active strategy contributions, alternative scores, and derived context; no hindsight win-rate claims, annotations, deck construction, or ML.
- **Acceptance criteria:** A selected draft/seat/pick reconstructs from immutable events plus versioned strategy/configuration data; later information is not inserted into the decision snapshot; repeated inspection is usable.
- **Required tests:** Timeline ordering, snapshot correctness, browser review flow.
- **Expected artifacts/areas:** review UI/API/tests.

### M2-009 — Define provenance-aware pick metrics

- **Labels/state:** `component::lab`, `type::proposal`, `priority::high`, `human::decision`, `BLOCKED`
- **Dependencies:** M2-001.
- **Goal/context:** Specify denominators and dimensions for average/median pick, last pick, seen-to-pick, and wheel rates.
- **Scope/out of scope:** Metric contracts and reference calculations; no performance or gameplay metrics.
- **Acceptance criteria:** Every metric defines population, denominator, duplicates, incomplete drafts, Cube version, and origin filters.
- **Required tests:** Hand-calculated miniature event datasets.
- **Expected artifacts/areas:** metric specification/ADR and reference tests.

### M2-010 — Build initial analytics views

- **Labels/state:** `component::lab`, `component::ui`, `type::feature`, `priority::medium`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M2-009.
- **Goal/context:** Query and visualize initial pick metrics without blending origins.
- **Scope/out of scope:** Filtered tables/charts for defined metrics; no predictive conclusions.
- **Acceptance criteria:** Default view separates human and each bot strategy/version; active Cube/time/origin filters are explicit; empty/small samples are labeled.
- **Required tests:** Aggregation fixtures, filter isolation, UI empty/small/normal states.
- **Expected artifacts/areas:** analytics storage/query/API/UI/tests.

### M2-011 — Add lightweight human pick-review annotations

- **Labels/state:** `component::lab`, `component::ui`, `type::feature`, `priority::medium`, `agent::supervised`, `BLOCKED`
- **Dependencies:** M2-008.
- **Goal/context:** Let an inspecting user record a lightweight, provenance-aware review without rewriting immutable draft truth.
- **Scope/out of scope:** Reasonable/Debatable/Bad labels, optional reason categories (power, color commitment, curve, synergy, archetype fit, fixing, narrow payoff, other), optional note, and author/source plus Cube version, draft, seat, pick, strategy/version, and configuration references; no objective-quality claim, training-data pipeline, ML, or event mutation.
- **Acceptance criteria:** An annotation is a separate layer, can be queried alongside but not merged into events, preserves its author/source and target identity, and remains usable without ML.
- **Required tests:** Schema validation, provenance/target identity, event immutability, update/delete policy, and UI empty/normal states.
- **Expected artifacts/areas:** annotation schema/application port, persistence/API/UI/tests.

## Later milestone capability backlog

### M3 — Improved bots

- Externalize licensed ratings and benchmark Bot v0.
- Add color-preference and commitment strategy behind the existing bot port.
- Add curve/mana-aware features with explanations.
- Add versioned archetype/synergy features after M2-006.
- Create fixed-scenario and seed-set benchmarks that compare strategies without labeling them human-like.
- Use the Draft Inspector and M2 annotations for human calibration: compare changed picks and reviewed decisions before/after versioned feature/weight changes on the same benchmark set; do not treat agreement as objective draft quality.

### M4 — Simulation framework

- Define `SimulationRun` identity, configuration, provenance, status, and reproducibility contract.
- Add a sequential batch runner and CLI/API entry point before parallel execution.
- Define seed allocation, cancellation, resumability, and failure reporting.
- Implement metric aggregation from immutable draft events.
- Benchmark and then add bounded parallel execution if evidence warrants it.
- Export machine-readable and human-readable reports.
- Compare two immutable Cube versions over paired seeds as an explicit experiment.
- Preserve selective drill-down from aggregate or deterministic anomaly signals into the Draft Inspector; do not require manual review of every simulated draft.

### M5 — Forge feasibility spike

- Inventory Forge modules and identify the narrowest game-core entry points.
- Prototype headless game initialization using throwaway code.
- Exercise legal actions, priority, choices, targets, combat, and game completion.
- Design and test player-safe DTO serialization and hidden-information boundaries.
- Test deterministic seed/replay and event capture.
- Measure startup, memory, throughput, concurrency, and failure recovery.
- Evaluate upgrade strategy and cost of avoiding a deep fork.
- Obtain qualified GPL-3.0 guidance for considered integration/distribution models.
- Produce an adopt/reject/further-research ADR; do not retain prototype code as production by default.

### M6–M9 skeleton

- **M6:** Engine-neutral local game API and correctness-first play UI.
- **M7:** Battlefield interaction, priority controls, logs/replay, accessibility, and density settings.
- **M8:** Direct sessions, secure player views, reconnect, spectators, draft rooms, mixed seats.
- **M9:** Authentication, hosted persistence, deployment, observability, privacy, abuse controls, backup, and measured scaling.

## Research backlog

| ID | Question | Earliest milestone | Suitability |
|---|---|---|---|
| R-001 | Which CubeCobra read/export contract is documented and stable enough for M1? | M1 | supervised + human decision |
| R-002 | How are custom cards, alters, boards, duplicates, and printing hints represented? | M1 | supervised |
| R-003 | Are historical CubeCobra draft datasets available, representative, and legally usable? | M3/M4 | supervised + human decision |
| R-004 | What Scryfall live/bulk/cache/attribution/image policy should local CubeAI use? | M1 | human decision |
| R-005 | Which rating or training datasets are available and license-compatible? | M1/M3 | human decision |
| R-006 | Which custom pack structures matter beyond standard Cube draft, and how are they modeled? | after M1 | product decision |
| R-007 | Can Forge be controlled headlessly through stable core APIs? | M5 | supervised |
| R-008 | Can Forge expose complete legal actions and player-safe state without UI coupling? | M5 | supervised |
| R-009 | What Forge determinism, replay, performance, and concurrency are achievable? | M5 | supervised |
| R-010 | What upgrade strategy avoids a deep Forge fork? | M5 | human decision |
| R-011 | What GPL-3.0 obligations apply to each adapter/process/distribution design? | M5 | qualified human/legal decision |
| R-012 | What hidden-information and reconnect protocol is required before multiplayer? | M8 | security/product decision |

## Recommended first issue

M0-001 is complete. **M0-002 — Establish the Python CubeLab workspace** and **M0-003 — Establish the React and TypeScript workspace** are now the next eligible foundation issues, subject to explicit authorization to begin either one.
