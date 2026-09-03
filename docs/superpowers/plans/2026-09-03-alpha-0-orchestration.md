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
