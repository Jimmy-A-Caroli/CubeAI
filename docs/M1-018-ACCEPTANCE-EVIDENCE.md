# M1-018 acceptance evidence

## Decision

**M1-018 is COMPLETE.** The controlled local acceptance, deterministic replay,
restart/resume, public-source smoke, supervised browser acceptance, and the
required repository validation together verify the M1 local deterministic draft
MVP. This record does not make production-scale, hosted-service, gameplay, or
advanced-analysis claims.

## Environment and clean local workflow

Acceptance was run on 2026-09-04 from a clean `main` baseline on Windows
PowerShell, using the locked backend and frontend toolchains. The documented
root commands were run from the repository root:

```powershell
uv --directory backend run --locked python ../scripts/cubeai.py setup
uv --directory backend run --locked python ../scripts/cubeai.py check
uv --directory backend run --locked python ../scripts/cubeai.py test
uv --directory backend run --locked python ../scripts/cubeai.py dev
```

The first literal `uv` invocation reported that `uv` was absent from the
machine `PATH`. The required executable was already installed at
`C:\Users\jcaroli\.local\bin\uv.exe`; adding that directory to the current
PowerShell process `PATH` allowed the unmodified documented root runner to
complete `setup`, `check`, and `test`. This is a machine environment discovery
issue, not a project or lockfile change.

`setup` completed a locked backend sync and `corepack npm --prefix frontend ci`
with 196 frontend packages installed and no vulnerabilities reported. `check`
reported 51 formatted backend files, Ruff success, strict mypy success for 28
source files, one preserved Import Linter contract, Prettier success, ESLint
success, and TypeScript success. `test` reported `224 passed, 1 deselected` for
the backend and `4` Vitest files / `16` tests passed for the frontend. The
frontend test environment printed its known non-fatal canvas implementation
notice but exited successfully.

The documented `dev` runner started the local FastAPI process and Vite at
`http://127.0.0.1:5173/`; `GET /health` returned `{"status":"ok"}` and the
Vite root returned HTTP 200.

## Controlled deterministic scenario, replay, and restart

`uv --directory backend run --locked pytest -q
tests/test_local_api.py -k m1_acceptance_replays_the_fixed_fixture_through_restart`
passed (`1 passed, 10 deselected`). The canonical synthetic scenario exercises
the public local API with a reviewed four-membership fixture, a two-seat,
one-pack, two-card configuration, seed `13`, one legal human choice, and the
recorded Bot v0 strategy. It proves this sequence:

```text
import -> validate -> start -> human pick -> Bot turn -> persist
       -> complete -> fresh-directory replay -> restart -> resume
```

The test compares complete API-visible outcomes from independent SQLite
directories: first human pack, pool, completion state, and final empty pack.
It then recreates the application against the first SQLite directory and
asserts a completed, resumable human-safe view. Equality is the replay
comparison mechanism for that fixed input, seed, strategy/version, and legal
human choice. The wider backend suite also covers immutable ordered events,
actor origin, Bot strategy/rating/tie-break provenance, allocation, and
deterministic state transitions.

## Opt-in public-source smoke

The explicit read-only public smoke was run with:

```powershell
uv --directory backend run --locked python ../scripts/alpha_checkpoint_e.py
```

The sandboxed first attempt returned `source_unavailable`; the single retry
outside that network sandbox completed. No provider response body or card list
is retained here. The aggregate checkpoint for CubeCobra identifier
`modovintage` was:

| Check | Result |
| --- | --- |
| Import | 540 mainboard memberships; `supported_with_optional_data_absent` |
| Supplementary board | non-blocking `unsupported_non_mainboard` diagnostic |
| Exact Scryfall resolution | 540 resolved |
| Cache replay | 540 `cached_fresh` offline resolutions |
| Validation | draftable; 540 usable memberships; `excess_usable_memberships` diagnostic |
| Allocation | 24 packs, 360 card instances |
| Draft | completed; 360 events; eight pools of 45 cards |
| Image presentation | 540 usable resolved image URLs; zero metadata fallbacks |

The deterministic output recorded cube-version fingerprint
`17a9b63fd0a596760fa1205b24b93216e89e899811f7e4c105ea4e3ca3acac70` and
event fingerprint
`f2388fff7d57e6a31305acb10f17bcfb2ccddda157fef581ec90a859d4d6ba86`.
Only mainboard memberships entered allocation. This validates the public
source/provider boundary and direct-domain completion; it does not replace the
controlled API/persistence test above.

## Browser, accessibility, and review acceptance

The task author manually exercised the current local Alpha and confirmed it is
usable. That supervised browser acceptance closes the prior rendered UI gap.
The current Vite page was also opened against the running local API: it exposed
the connected status, labelled CubeCobra and configuration controls, the
standard 8/3/15 defaults, and an Import Cube action in the browser accessibility
tree.

The manual acceptance disposition for the current production UI is:

| Area | Result |
| --- | --- |
| Wide desktop | PASS — compact image-enabled pack, clear current action, card details, and meaningful completion/review were accepted; the 15-card pack uses the documented ten-column desktop grid (10 + 5). |
| Narrow viewport | PASS — responsive grid, reachable controls, usable details, and readable completion/review were accepted. |
| Accessibility | PASS — component coverage verifies keyboard card activation, visible focus, dialog initial focus, Escape dismissal, focus restoration, descriptive image alt text, and missing/load-error fallback. |
| Human review | PASS — completed pool, human pick history, and completion summary are exposed only after completion. |
| Bot review | PASS — completed review selects recorded Bot seats and shows each history plus raw-ranking strategy/version, selected rating, rating lookup outcome, and deterministic tie-break evidence. |
| Hidden information | PASS — active draft remains a human-seat view; API review contract tests reject internal allocation/instance identifiers from the rendered payload. |

The available automation surface can open and inspect the browser accessibility
tree but cannot itself operate controls or set viewports. The human's physical
acceptance is therefore the visual wide/narrow authority; automated component,
API, and accessibility-tree checks provide repeatable supporting evidence.

## Required quality gates

All required checks passed on the acceptance branch before integration:

```text
backend: Ruff format check, Ruff lint, strict mypy, Import Linter, pytest, build
frontend: locked npm ci, Prettier check, ESLint, strict TypeScript, Vitest, production build
repository: git diff --check
```

The backend build produced the source distribution and wheel successfully. The
frontend production build completed successfully.

## Known limitations and scope check

- The metadata cache stores resolved remote image URLs, not image bytes; offline
  image caching is not implemented.
- Bot v0 is a deterministic static raw-ranking baseline, not human-like
  drafting.
- Archetype inference is not implemented.
- Analytics and simulation batches are future work.
- Multiplayer, gameplay, cloud hosting, and authentication are future work.

No M2 feature, Bot intelligence change, UI redesign, provider expansion, or
architecture change was introduced by M1-018 acceptance. CubeCobra and
Scryfall remain adapter boundaries; CubeVersion snapshots remain immutable;
draft transitions remain deterministic; persistence remains caller-local
SQLite; the API remains human-seat-safe; and Bot v0 remains replaceable.
