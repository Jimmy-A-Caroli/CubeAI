# Alpha-0 orchestration ledger

## Run boundary

- Base: `main` at `7dc1964585259a40ca0bcde272d2fc1562927527` on 2026-09-03.
- Branch: `codex/alpha-0-orchestration-2026-09-03`.
- Target: Alpha-0 — a supported public CubeCobra Cube can progress through
  source candidates, identity/metadata resolution, a validated immutable
  `CubeVersion`, seeded pack allocation, and deterministic draft transitions.
- Default tests remain offline. The reference corpus is discovery evidence, not
  a committed provider dataset; one conventional `CORE` Cube may later be an
  opt-in live smoke target.
- No push, merge to `main`, provider-policy adoption, production deployment,
  or other human-decision crossing is authorized by this ledger.

## Current-state ruling

The canonical backlog and milestone tables are authoritative for task state.
They conflict with current implementation evidence for M0-006 and M1-004:

- `027f9e0` adds an aggregate health/connectivity implementation, but the
  backlog says M0-006 `BLOCKED` and the M0 milestone says `READY`.
- `b5215f6` and `249ff42` add/fix a CubeCobra adapter, but the backlog says
  M1-004 `BLOCKED` and the M1 milestone says `READY`.
- `4abc206` and `249ff42` add an allocation helper although M1-010 remains
  canonically `BLOCKED` on M1-008. It is treated as unaccepted partial
  implementation, not as a completed or dependency-satisfying task.

No state transition will be made from commit presence alone. Independent
acceptance audits must establish whether M0-006 and M1-004 meet their issue
requirements, preserve accepted boundaries, and have adequate tests. Until
then, neither code path is used to unlock downstream work.

## Alpha-relevant DAG

| Work package | Canonical state / suitability | Dependencies | Alpha capability / likely boundary | Parallel position |
|---|---|---|---|---|
| M0-006 | conflicting (`BLOCKED` backlog, `READY` milestone); `agent::safe` | M0-004, M0-005 complete | Checkpoint A aggregate commands and local health slice; `Makefile`, `cubeai.api`, CubeUI status | audit only in wave 1 |
| M0-007 | `BLOCKED`; `agent::safe` | M0-006 | CI repeats aggregate validation; secondary foundation | after M0-006 acceptance |
| M0-009 | `READY`; `agent::safe` | M0-002, M0-003 complete | reproducible dependency/license inventory; unlocks M1-005 research | wave 1 implementation |
| M0-010 | `READY`; `agent::safe` | none | GitHub issue/proposal templates; no Alpha-path capability | deferred |
| M0-011 | `BLOCKED`; `agent::safe` | M0-006 | local orchestration for the health slice; supports Checkpoint A | after M0-006 acceptance |
| M0-012 | `BLOCKED`; `agent::supervised` | M0-007..M0-011 as recorded | clean-clone evidence; foundation acceptance | not Alpha critical path |
| M1-004 | conflicting (`BLOCKED` backlog, `READY` milestone); `agent::supervised` | M1-003 complete | Checkpoint B CubeCobra read adapter; `cubeai.lab.adapters` | audit only in wave 1 |
| M1-005 | `BLOCKED`; `human::decision` | M0-009 | Scryfall identity/metadata/cache decision | bounded research only after M0-009 |
| M1-006 | `BLOCKED`; `agent::supervised` | M1-002, M1-005 | resolver port and approved Scryfall adapter | hard-blocked by human adoption of M1-005 |
| M1-007 | `BLOCKED`; `agent::safe` | M1-004, M1-006 | Checkpoint C immutable reviewable `CubeVersion` | after M1-004 acceptance + M1-006 |
| M1-008 | `BLOCKED`; `agent::safe` | M1-007 | validation before allocation | after M1-007 |
| M1-009 | `COMPLETE`; `agent::safe` | M1-002 | draft configuration, lifecycle, seat/pack/pick vocabulary | available foundation |
| M1-010 | `BLOCKED`; `agent::safe` | M1-008, M1-009 | Checkpoint D seeded pack allocation; current helper is not accepted completion | after M1-008 |
| M1-011 | `BLOCKED`; `agent::safe` | M1-010 | Checkpoint E deterministic pick/rotation state machine | after M1-010 |
| M1-012 / M1-013 | `BLOCKED`; M1-012 `human::decision`, M1-013 `agent::safe` | M1-009 / M1-011, M1-012 | bot policy and execution; not required for controlled/manual Alpha draft core | defer |
| M1-014 / M1-015 | `BLOCKED`; `agent::supervised` | M1-007, M1-013 / M1-008, M1-013, M1-014 | persistence and API/UI path | outside narrow Alpha core |

Shortest canonical Alpha path:

```text
M0-009 → M1-005 research → human policy decision → M1-006
M1-003 → M1-004 acceptance
M1-004 + M1-006 → M1-007 → M1-008 → M1-010 → M1-011
```

## Wave 1

1. M0-009 implementation: dependency/license reporting only; must evaluate any
   added dependency rather than hide policy in a tool default.
2. M0-006 read-only acceptance/tracking audit against the current issue,
   M0 exit criteria, and existing implementation/tests.
3. M1-004 read-only acceptance/tracking audit against ADR-0004, the frozen
   contract, fixture policy, and existing implementation/tests.

The three streams do not share files or interfaces. The audits do not alter
source or canonical state; their findings determine whether a later tracking
task is justified. Every implementation and any corrective change receives an
independent review before integration.

## Wave 1 evidence

- Baseline at `7dc1964`: locked backend sync plus pytest, Ruff format/check,
  mypy, and Import Linter passed (`84 passed`); clean frontend install plus
  format, lint, typecheck, Vitest (`2 passed`), and production build passed.
- M0-006 audit verdict: `REPAIR_REQUIRED`. The health handler is valid, but the
  Makefile-only root runner is unavailable on the declared Windows path, lacks
  `format`, does not start/proxy the frontend, omits required aggregate checks
  and controlled-failure tests, and is contradicted by root/workspace docs.
  M0-006 has complete listed dependencies and is an `agent::safe` targeted
  repair candidate; it is not `COMPLETE`.
- M1-004 audit verdict: `REPAIR_REQUIRED`. The current adapter maps narrow
  happy paths but collapses failure codes, retries 404, loses Oracle/provenance
  evidence, accepts unknown source shapes, exposes raw provider exceptions,
  uses a non-injectable clock, and lacks adapter-contract tests. M1-004 stays
  canonically blocked and requires a human-authorized supervised repair before
  it can unlock M1-007.
- M0-009 was independently reviewed, repaired in `b2de88f`, rereviewed, and
  integrated into this orchestration branch in `2a11129`. It adds no dependency
  or lockfile change. In the locked Python 3.14 toolchain, its three backend
  report tests passed; the report intentionally exited 1 after surfacing eight
  packages for human license review. The frontend report tests passed (four
  tests), with all locked frontend packages allowed. This is visible review
  evidence rather than automatic legal approval of the eight backend packages.

## Wave 2

1. M0-006 targeted `agent::safe` repair: replace the Windows-incompatible and
   incomplete aggregate-command surface with documented, cross-platform-enough
   workspace entry points; complete the health-view connectivity proof and its
   focused tests without changing product architecture.
2. M1-005 bounded research: record authoritative Scryfall API/bulk-data facts
   and a decision-ready cache/metadata policy proposal. It may not adopt the
   policy, implement an adapter, or mark the issue complete; human approval is
   the hard stop before M1-006.

The streams have separate source areas and may proceed in parallel. Wave 2
cannot unlock M1-006 without a human decision, and M1-004 remains blocked
pending explicit supervised-repair authorization.

## Wave 2 evidence and DAG recalculation

- M0-006 implementation `69ad9eb` was independently reviewed as
  `REPAIR_REQUIRED` only for missing nested `uv run --locked` guards. The
  original implementer repaired that in `88b26f2`; focused re-review approved
  it. The integration commits are `40227c3` (M0-006) and `a96b6af` (M1-005).
  On this orchestration branch, locked setup succeeded; aggregate check passed
  Ruff format/check, strict source mypy, Import Linter, Prettier, ESLint, and
  TypeScript; aggregate test passed 93 backend and 3 frontend tests. Direct
  and Vite-proxied `GET /health` smoke evidence and controlled nonzero-child
  propagation were reviewed before integration.
- M1-005 research `ec408e2` was independently reviewed as `REPAIR_REQUIRED`
  only for a new strict-mypy test error. `a1d0a89` fixed it; focused re-review
  approved it. The report is decision support, not an adopted provider/cache
  policy: M1-005 remains `READY`/`human::decision`, and M1-006 remains
  `BLOCKED`.
- Checkpoint A is now reached: a developer can run one documented locked root
  command for validation and another to start the local health/status slice.
  M0-007 and M0-011 are dependency-ready secondary foundation tasks, but M0-007
  cannot satisfy its required remote-run evidence without a permitted push, and
  M0-011 should not duplicate the deliberately minimal M0-006 runner without a
  distinct need.
- The shortest Alpha path remains:

  ```text
  human decision on M1-005 -> M1-006 (supervised)
  M1-004 supervised repair/acceptance
  M1-004 + M1-006 -> M1-007 -> M1-008 -> M1-010 -> M1-011
  ```

## Wave 3 authorization and sequencing ruling

- On 2026-09-03, human Alpha-0 authorization adopted M1-005's exact
  printing-ID, durable-local-cache policy; it forbids automatic fuzzy/name
  fallback and bulk-data-first architecture. M1-005 is now complete, and
  M1-006 is canonically ready.
- The same authorization permits a bounded supervised M1-004 repair and
  acceptance pass against ADR-0004 and the frozen contract. M1-004 is now
  canonically ready.
- M1-004 and M1-006 are both on the critical path but are not dispatched in
  parallel: they share the provider-neutral import model. M1-004 must first
  repair its loss of printing/Oracle/provenance evidence and its diagnostics;
  M1-006 then consumes that stabilized contract. This is an execution-order
  ruling, not a new dependency.

## Wave 3 evidence

- M1-004 was repaired in `c7950a1` and `b1be034`, then independently approved;
  `966cd39` integrated it. It now maps the frozen public CubeCobra contract
  through structured provider-neutral outcomes without leaking provider errors.
- M1-006 was implemented in `452b078`, repaired in `65a8b1b`, and independently
  approved; `7c4cc21` integrated it. It supplies exact printing-ID resolution,
  a caller-selected durable SQLite cache, explicit outcomes, and no fallback or
  bulk behavior. Its 150-test default backend suite remains offline.
- M1-007 is now the next Alpha-path task; it must assemble the reviewed import
  and resolution snapshots into immutable, diagnosable CubeVersions.

## Wave 4 — immutable version integration

- M1-007 implementation `786df60` was independently reviewed as
  `REPAIR_REQUIRED`: matching a membership key and source snapshot did not
  establish that the resolved record belonged to the exact imported candidate.
  The repair `1964005` makes that equality a construction precondition and
  adds a custom-versus-resolved substitution regression. Independent re-review
  approved the repair.
- The integrated default-offline backend suite passed with `157 passed` after
  the repair. M1-007 is complete, so M1-008 is now the only ready Alpha-path
  work package. M1-010 and M1-011 remain blocked.

Updated Alpha path:

```text
M1-008 validation → M1-010 deterministic allocation → M1-011 draft state
```

## Wave 5 — validation integration and stop

- M1-008 implementation `355ddac` was independently reviewed as
  `REPAIR_REQUIRED` because capacity diagnostics did not identify the affected
  draft geometry. The focused repair `ca773e0` adds stable seats,
  packs-per-seat, and cards-per-pack context for both insufficient and excess
  diagnostics; independent re-review approved it.
- The integrated default-offline backend suite passed with `165 passed` after
  the repair. M1-008 is complete; M1-010 is now ready because M1-009 was
  already complete. M1-011 remains blocked on M1-010. No M1-010 or M1-011
  implementation occurred in this wave.
- The requested opt-in live CORE smoke attempted CubeCobra identifier
  `modovintage` without retaining its payload. With external network access,
  the source adapter returned `UNSUPPORTED` because the current public source
  has a nonempty `basics` board. Under the frozen M1-004 contract, that
  condition blocks source-to-resolution assembly rather than yielding a
  mainboard-only import with a visible diagnostic. The live chain therefore
  did not reach CubeVersion validation; changing that accepted source behavior
  is outside M1-007/M1-008 and requires human direction.

Updated Alpha path:

```text
validated CubeVersion boundary
    ↓
M1-010 deterministic allocation (READY)
    ↓
M1-011 draft state (BLOCKED on M1-010)
```
