# M0-001: Initial toolchain decision — ACCEPTED

## Executive recommendation

**Accepted decision:** establish a native-first modular
monorepo with a Python 3.14 backend and a Node 24 frontend. Use `uv` 0.12.7
with a standard `backend/pyproject.toml`, Hatchling build backend, and committed
`backend/uv.lock`; use npm 11.19.1 with committed
`frontend/package-lock.json`. The backend quality stack is FastAPI/Pydantic only
at the HTTP boundary, pytest, Ruff, mypy in strict mode, and Import Linter. The
frontend stack is React 19.2, **TypeScript 5.9**, Vite 8.2, Vitest 4.1, React
Testing Library, ESLint/typescript-eslint, and Prettier 3.9.

The human decision was recorded on 2026-09-01 in [ADR-0003](../adr/0003-initial-toolchain-and-web-first-local-capable.md). This accepts the documented toolchain and architectural constraint only; it neither creates the workspaces nor authorizes implementation within this decision record.

## Current repository constraints

- The accepted architecture is one modular monorepo, not independent services
  or separate repositories (ADR-0001).
- `cubeai.lab` is the accepted conceptual Python namespace. Its domain is
  framework- and adapter-independent (ADR-0002).
- The repository is documentation and experiments only: no backend,
  frontend, lockfile, CI workflow, container setup, or application source yet
  exists. This proposal must therefore describe future commands without
  claiming they currently run.
- M0 requires one reproducible setup path, native commands, Linux CI, a
  feasible Windows path, strict quality gates, deterministic tests, and a
  future health/status smoke slice. Docker cannot be a prerequisite for native
  tests.
- CubeLab must remain useful independently of CubeGame and any game engine;
  Forge remains a later research candidate, not a toolchain dependency.

## Evidence boundaries

- **Repository facts** are the stated constraints above and the accepted ADRs.
- **Upstream facts** are the version, lifecycle, platform, command, and license
  observations linked in this report; they were refreshed on 2026-09-01.
- **Engineering judgment** is the trade-off, migration-cost, version-range, and
  update-policy analysis. The final toolchain and web-first/local-capable
  constraint are now accepted; deferred technologies remain non-decisions.

## Question

Which initial development toolchain should CubeAI adopt for M0 so that the backend and frontend are reproducible, strict, cross-platform, inexpensive to run, and easy for humans and coding agents to validate without committing to production infrastructure? This report supplied the evidence for the accepted M0-001 decision; it records no workspace implementation.

## Methodology

The evaluation applies the constraints in `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, ADR-0001, ADR-0002, the M0 milestone, and backlog item M0-001. Tasks 1–5 were confirmed complete from their committed research artifacts and experiment tests before this evaluation. All ecosystem evidence below comes from official project documentation, release notes, or project-owned repositories and was refreshed on **2026-09-01**. Version numbers are deliberately identified as a minimum floor, a compatible declaration range, or an exact resolved/tool lock.

No software was installed. The plan's exact environment commands produced:

```text
uname -a
Darwin Jimmys-MacBook-Air.local 25.5.0 Darwin Kernel Version 25.5.0: Tue Jun  9 22:26:22 PDT 2026; root:xnu-12377.121.10~1/RELEASE_ARM64_T8132 arm64

sw_vers
ProductName: macOS
ProductVersion: 26.5.2
BuildVersion: 25F84

sysctl -n machdep.cpu.brand_string
Apple M4

sysctl -n hw.memsize
17179869184

python3 --version
Python 3.14.0

node --version
v22.23.2

npm --version
10.9.8

docker --version
not installed

docker compose version
not installed

git --version
git version 2.52.0
```

Local absence of Docker is only a machine observation, not evidence against Docker Compose. The existing experiment baseline was also checked with `python3 -m unittest discover -s experiments/tests -v`: 20 tests passed.

## Backend evaluation

The “trade-off” and “migration” entries are project-specific analysis based on the linked primary evidence, not claims made by the upstream projects.

| Concern | Recommended candidate | Alternative considered | Trade-off and migration assessment |
|---|---|---|---|
| Python runtime | Python 3.14 bugfix series | Python 3.13 bugfix series | Both are supported; 3.14 has one additional year of scheduled support and is already present locally. Moving back to 3.13 is low cost before M0-002 and moderate after lockfiles and CI exist. [Python status](https://devguide.python.org/versions/) |
| Python environment and dependency resolution | uv project workflow rooted at `backend/`, with committed `backend/uv.lock` | stdlib `venv` plus pip's `pip lock`/`pylock.toml` | uv provides a universal cross-platform lock and exact sync. Pip's lock command is documented as experimental and locks only for the current Python/platform, so a multi-platform policy would require additional lock maintenance. Both retain standard `pyproject.toml`, keeping later migration moderate. [uv lockfile](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile), [pip lock](https://pip.pypa.io/en/stable/cli/pip_lock/), [venv](https://docs.python.org/3/library/venv.html) |
| Python build/package configuration | Standard PEP 621 `pyproject.toml`, `src/` layout, and Hatchling build backend | uv build backend or setuptools | Hatchling is a maintained, conventional PEP 517 backend with minimal configuration. `uv` remains the environment/lock tool rather than becoming the package boundary; setuptools is viable but adds legacy configuration surface. Moving build backends is low-to-moderate cost before publication because application imports and package layout are unchanged. [Hatch build configuration](https://hatch.pypa.io/latest/config/build/), [PyPA build-system specification](https://packaging.python.org/en/latest/specifications/declaring-build-dependencies/) |
| HTTP/API boundary | FastAPI with Pydantic v2 | Starlette directly or a different Python web framework | FastAPI supplies typed validation and OpenAPI ergonomics with limited glue; it remains confined to the outer API layer. Replacing it is moderate cost if domain/application code stays framework-independent. [FastAPI releases](https://fastapi.tiangolo.com/release-notes/), [Pydantic changelog](https://docs.pydantic.dev/latest/changelog/) |
| Backend lint/format | Ruff for linting and formatting | Separate Black, isort, and lint tools | One fast tool reduces configuration and agent command surface. Ruff is still pre-1.0 and documents minor-version breaking changes, so its compatible range must be narrow. [Ruff overview](https://docs.astral.sh/ruff/), [Ruff formatter](https://docs.astral.sh/ruff/formatter/), [Ruff versioning](https://docs.astral.sh/ruff/versioning/) |
| Backend type checking | mypy strict mode | ty | mypy is the mature, conservative choice and supports Python 3.14. ty is promising but was announced only four days before this access date and does not yet have a plugin system; reassessment after M0 is low cost because annotations remain standard Python. [mypy changelog](https://mypy.readthedocs.io/en/stable/changelog.html), [ty overview](https://docs.astral.sh/ty/), [ty typing FAQ](https://docs.astral.sh/ty/reference/typing-faq/) |
| Import boundaries | Import Linter contracts | A repository-specific AST test | A layers contract can enforce application-to-domain direction and forbidden contracts can keep framework/API/adapter imports out of domain. A custom test has fewer dependencies but more CubeAI-owned edge cases. Migration between them is low cost because the architecture rule is unchanged. [Import Linter](https://import-linter.readthedocs.io/en/stable/), [layers contracts](https://import-linter.readthedocs.io/en/stable/contract_types/layers/) |

## Frontend evaluation
| Frontend runtime/build | React client application, strict TypeScript, and Vite | Create React App or a full-stack React framework | React deprecated Create React App for new applications and names build tools such as Vite; a client-only Vite application fits M0 without importing server-framework decisions. Moving to a full-stack framework later is moderate-to-high cost and should require a separate decision. [React versions](https://react.dev/versions), [Create React App deprecation](https://react.dev/blog/2025/02/14/sunsetting-create-react-app), [Vite 8](https://vite.dev/blog/announcing-vite8) |
| Frontend tests | Vitest plus React Testing Library | Jest plus a separate Vite transform setup | Vitest shares Vite configuration; Testing Library emphasizes user-observable DOM behavior. Replacing Vitest is moderate cost, while most Testing Library tests can remain. [Vitest guide](https://vitest.dev/guide/), [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) |
| Frontend lint/format | ESLint plus typescript-eslint for correctness; Prettier solely for formatting | ESLint formatting rules | typescript-eslint explicitly recommends against using ESLint for formatting. Separating responsibilities makes failures diagnosable and avoids rule conflicts. [typescript-eslint formatting guidance](https://typescript-eslint.io/users/what-about-formatting/), [Prettier install guidance](https://prettier.io/docs/install/) |

The TypeScript 5.9 line is the deliberate recommendation. TypeScript 6.0 is
maintained and compatible with the other proposed tools, but was released on
2026-08-28; selecting the established 5.9 series is the lower-churn choice for
an initial, documentation-only repository. Re-evaluate TypeScript 6 after the
first frontend workspace has a passing locked toolchain. [TypeScript 6.0 release
notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html)

## Repository / CI / tooling evaluation
| Local persistence | Python stdlib `sqlite3`, with SQLite STRICT capability required | PostgreSQL or another server database | SQLite is serverless and keeps M0 native-first. A server database adds operations before demonstrated need. Repository interfaces preserve a later migration path, which would still be a major persistence decision requiring human direction. [Python sqlite3](https://docs.python.org/3/library/sqlite3.html), [SQLite STRICT tables](https://www.sqlite.org/stricttables.html) |
| Local orchestration | Native backend/frontend commands first; a useful optional Compose slice later | Compose required for all development | Native commands work on the observed machine where Docker is absent. Compose remains useful for an opt-in integrated slice once services exist, without making Docker a prerequisite for unit work. [Compose install options](https://docs.docker.com/compose/install/), [Compose overview](https://docs.docker.com/compose/) |
| CI | GitHub Actions invoking the same root validation command | CI-specific command graph | GitHub recommends setup actions for consistent Python/Node versions and supports lockfile-derived caches. A single repository command keeps local and CI behavior aligned. [Python CI](https://docs.github.com/en/actions/tutorials/build-and-test-code/python), [Node.js CI](https://docs.github.com/en/actions/tutorials/build-and-test-code/nodejs), [dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) |

## Alternatives considered

The evaluation tables above record the detailed alternatives and migration cost.
The important rejected choices are summarized here so this proposal does not
leave an implicit toolchain menu:

| Alternative | Why it is not selected for M0 | Migration cost if revisited |
|---|---|---|
| Python 3.13 | Still supported, but gives one less year of scheduled support than the already-stable 3.14 line. | Low before lockfiles/CI; moderate afterward. |
| `venv` + `pip lock` | Retains standard metadata but `pip lock` remains experimental and locks a single platform, adding multi-platform maintenance. | Moderate; `pyproject.toml` and source layout remain standard. |
| `uv_build` or setuptools | Either adds tighter resolver/build coupling or more legacy configuration than a small Hatchling PEP 517 setup needs. | Low-to-moderate before publishing a distribution. |
| TypeScript 6.0 | Technically compatible, but too recent for the requested boring foundation. | Low through a reviewed dependency/lockfile upgrade. |
| pnpm, Create React App, full-stack React framework, or Jest transform setup | Each adds a package-manager decision, deprecated/scoped framework commitment, or configuration not needed for the local client application. | Moderate for package manager/test runner; moderate-to-high for a framework. |
| Required Docker Compose or CI-specific scripts | Creates a second prerequisite/path before native workflows and the M0 smoke slice exist. | Low for an optional later Compose slice; CI continues to invoke the root validator. |

## Compatibility and support matrix

The declaration range permits reviewed updates; committed lockfiles resolve exact transitive versions. Floors are not permission for automated major upgrades.

| Component | Role | Minimum floor | Compatible declaration or tool pin | Exact resolution mechanism and current-source evidence |
|---|---|---:|---|---|
| Python | Runtime | 3.14.0 | `>=3.14,<3.15`; pin major/minor `3.14` in developer and CI setup | The installed patch is selected by the platform/setup tool, not `backend/uv.lock`. Python 3.14 is the current bugfix series; 3.15 is pre-release. [Python downloads](https://www.python.org/downloads/), [support status](https://devguide.python.org/versions/) |
| uv | Python project/lock tool | 0.12.7 | Exact tool pin `0.12.7` in bootstrap and CI | `backend/uv.lock` resolves application/dev dependencies exactly. uv documents possible breaking changes, including lock schema changes, at minor releases. [installation](https://github.com/astral-sh/uv/blob/main/docs/getting-started/installation.md), [versioning](https://docs.astral.sh/uv/reference/policies/versioning/) |
| Hatchling | Python build backend | 1.28.0 | `>=1.28,<2` | Hatchling is declared under `[build-system]`; `uv build` invokes that standard PEP 517 backend. The backend version is resolved exactly in `backend/uv.lock`. [Hatch build configuration](https://hatch.pypa.io/latest/config/build/), [PyPA build-system specification](https://packaging.python.org/en/latest/specifications/declaring-build-dependencies/) |
| FastAPI | HTTP boundary | 0.141.1 | `>=0.141.1,<1` | Exact package and transitive versions in `backend/uv.lock`; 0.141.1 is the current release in official release notes. [releases](https://fastapi.tiangolo.com/release-notes/) |
| Pydantic | Boundary validation | 2.12.5 | `>=2.12.5,<3` | Exact resolution in `backend/uv.lock`; use it only for transport validation at the outer HTTP boundary. [changelog](https://docs.pydantic.dev/latest/changelog/) |
| pytest | Backend tests | 9.1.1 | `>=9.1.1,<10` | Exact resolution in `backend/uv.lock`. [release announcements](https://docs.pytest.org/en/stable/announce/index.html), [compatibility policy](https://docs.pytest.org/en/stable/backwards-compatibility.html) |
| Ruff | Backend lint/format | 0.16.0 | `>=0.16.0,<0.17` | Exact resolution in `backend/uv.lock`; the narrow range reflects Ruff's documented pre-1.0 minor-version policy. [releases](https://github.com/astral-sh/ruff/releases), [versioning](https://docs.astral.sh/ruff/versioning/) |
| mypy | Backend type checker | 2.3.1 | `>=2.3.1,<3` | Exact resolution in `backend/uv.lock`; run in strict mode. [changelog](https://mypy.readthedocs.io/en/stable/changelog.html) |
| Import Linter | Import boundaries | 2.14 | `>=2.14,<3` | Exact resolution in `backend/uv.lock`; 2.14 is the current release and the project documents Python 3.14 support. [release notes](https://import-linter.readthedocs.io/en/stable/release_notes/) |
| SQLite | Embedded database capability | 3.37.0 | Runtime assertion `sqlite3.sqlite_version_info >= (3, 37, 0)` | Resolved by the selected CPython distribution rather than a package lockfile. 3.37.0 introduced STRICT tables; current upstream is 3.53.4, but M0 should require the capability floor rather than a separately installed latest library. [STRICT tables](https://www.sqlite.org/stricttables.html), [changes](https://sqlite.org/changes.html) |
| Node.js | Frontend runtime | 24.0.0 | `>=24,<25`; pin major `24` in developer and CI setup | Node 24 is LTS; Node recommends Active or Maintenance LTS for production applications. Local Node 22 remains LTS but is below this proposed floor. [release status](https://nodejs.org/en/about/previous-releases) |
| npm | Frontend package/lock tool | 11.19.1 | Exact tool pin `11.19.1`; engine range `>=11,<12` | `package-lock.json` resolves exact dependencies and `npm ci` refuses manifest/lock mismatches. [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/), [package-lock](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/) |
| React and React DOM | UI | 19.2.7 | `>=19.2.7,<20` | Exact resolution in `package-lock.json`; 19.2.7 is the current patched 19.2 release. [versions](https://react.dev/versions) |
| TypeScript | Static typing | 5.9.3 | `>=5.9.3,<6` | Exact resolution in `package-lock.json`; configure `strict: true`. TypeScript 6.0 is intentionally deferred until the locked M0 frontend is proven. [5.9 release notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html), [strict](https://www.typescriptlang.org/tsconfig/strict) |
| Vite | Frontend dev/build | 8.2.2 | `>=8.2.2,<8.3` | Exact resolution in `package-lock.json`; the minor-bounded range limits unreviewed TypeScript-definition churn. [Vite 8](https://vite.dev/blog/announcing-vite8), [releases](https://github.com/vitejs/vite/releases), [release policy](https://github.com/vitejs/vite/blob/main/docs/releases.md) |
| Vitest | Frontend test runner | 4.1.11 | `>=4.1.11,<5` | Exact resolution in `package-lock.json`; Vitest 5 is not yet stable. [guide](https://vitest.dev/guide/), [releases](https://github.com/vitest-dev/vitest/releases) |
| React Testing Library | Component tests | 16.3.2 | `>=16.3.2,<17` | Exact resolution in `package-lock.json`, together with its DOM peer and lock-resolved DOM environment. [releases](https://github.com/testing-library/react-testing-library/releases), [intro](https://testing-library.com/docs/react-testing-library/intro/) |
| ESLint | Frontend lint | 10.9.1 | `>=10.9.1,<11` | Exact resolution in `package-lock.json`; ESLint 10 uses flat configuration and supports the proposed Node line. [10.0 release](https://eslint.org/blog/2026/02/eslint-v10.0.0-released/), [releases](https://github.com/eslint/eslint/releases) |
| typescript-eslint | Type-aware ESLint rules | 8.67.0 | `>=8.67.0,<9` | Exact resolution in `package-lock.json`; official compatibility includes ESLint 10, Node 24, and TypeScript `<6.1.0`. [dependency versions](https://typescript-eslint.io/users/dependency-versions/), [releases](https://github.com/typescript-eslint/typescript-eslint/releases) |
| Prettier | Frontend formatting only | 3.9.6 | Exact dependency pin `3.9.6` | Also resolved in `package-lock.json`. Prettier recommends an exact local version because even patch releases can change formatting. [install guidance](https://prettier.io/docs/install/) |
| Docker Compose | Optional integrated local slice | 5.5.0 | Host tool floor `>=5.5.0,<6`; do not vendor or lock it as an application dependency | Compose is not required until a useful slice exists; the official plugin installation page identifies 5.5.0 as current and the standalone path as legacy. [plugin install](https://docs.docker.com/compose/install/linux/), [install overview](https://docs.docker.com/compose/install/) |

## Package layout

The proposed modular-monorepo layout is conceptual only; this task creates none of these directories:

```text
backend/
  pyproject.toml
  uv.lock
  src/
    cubeai/
      lab/
        domain/
        application/
      api/
      adapters/
  tests/
frontend/
  package.json
  package-lock.json
  src/
scripts/
  validate.py
```

`backend/` is the sole uv project root: its `pyproject.toml`, `uv.lock`, and `.venv` belong together, and the repository root has no competing Python project metadata. Commands documented below are invoked from the repository root with uv's global `--directory backend` option, which changes working directory before project discovery and makes relative command arguments resolve from `backend/`. [uv CLI `--directory`](https://docs.astral.sh/uv/reference/cli/#uv--directory), [uv project structure](https://docs.astral.sh/uv/concepts/projects/layout/)

`backend/src/cubeai/lab/domain` is the dependency-free domain center. `backend/src/cubeai/lab/application` may depend on domain, but domain must not import application, FastAPI, Pydantic transport models, persistence adapters, UI types, or external-service payloads. `api` and `adapters` are outer packages. Import Linter should encode both the application-to-domain layer direction and explicit forbidden imports from domain. The `src` layout avoids accidentally importing an uninstalled checkout and retains the ADR-0002 `cubeai.lab` namespace. No API endpoint, persistence schema, frontend component, or production package is created or implied here.

## Web-first, local-capable boundary

**Accepted architectural requirement:** CubeAI's primary frontend is a web
application. It must preserve a future path to supported local/offline use in
the same React/TypeScript codebase. The future frontend/application boundary
must not unnecessarily assume permanent connectivity and must permit local
storage or local implementations of selected application ports/adapters when a
later milestone justifies them.

```text
                 CubeAI Frontend
                       |
               Application layer
                       |
                 Domain / Ports
                       |
             +---------+---------+
             |                   |
       Local adapters       Remote adapters
```

This is a boundary constraint, not an implementation selection. M0-001 does
not introduce a second frontend, desktop wrapper, PWA framework or plugin,
service worker, IndexedDB/browser storage, offline cache policy, synchronization
protocol, conflict-resolution semantics, or local/remote replication design.
Each remains deferred until a working vertical slice supplies concrete evidence.

## Recommended development commands

M0-002 through M0-006 should expose the following native commands and scripts. Names are recommendations for human review, not commands available in the repository today.

| Scope | Command | Responsibility |
|---|---|---|
| Backend install | `uv --directory backend sync --locked --all-groups` | Select `backend/pyproject.toml`, reproduce `backend/uv.lock`, and fail on a stale lockfile. |
| Backend format | `uv --directory backend run ruff format --check .` | Check backend formatting without edits. |
| Backend lint | `uv --directory backend run ruff check .` | Run static lint checks across the backend project. |
| Backend types | `uv --directory backend run mypy --strict src tests` | Strict static type check. Prefer storing equivalent strict settings in `backend/pyproject.toml` as well. |
| Backend boundaries | `uv --directory backend run lint-imports` | Enforce domain/application/outer-layer import contracts from the backend project configuration. |
| Backend tests | `uv --directory backend run pytest -q tests` | Run deterministic backend unit and contract tests. |
| Backend package | `uv --directory backend build` | Build the Hatchling-configured backend project without relying on checkout import leakage. |
| Frontend install | `npm --prefix frontend ci` | Reproduce `package-lock.json` and reject drift. |
| Frontend format | `npm --prefix frontend run format:check` | Run `prettier --check .`; formatting only. |
| Frontend lint | `npm --prefix frontend run lint` | Run ESLint correctness rules, not formatting rules. |
| Frontend types | `npm --prefix frontend run typecheck` | Run `tsc --noEmit` with `strict: true`. |
| Frontend tests | `npm --prefix frontend test` | Run a package script that executes `vitest run`, using Testing Library for user-visible behavior. |
| Frontend build | `npm --prefix frontend run build` | Produce the Vite production bundle as a compatibility check. |
| Whole repository | `uv --directory backend run python ../scripts/validate.py` | Use the locked backend interpreter to run the same ordered repository checks locally and in CI, returning the first diagnosable failure. |

The root validator should derive the repository root from `scripts/validate.py`, set each subprocess working directory explicitly to that root, and use the exact `uv --directory backend ...` argument lists above for backend children. It should use Python's subprocess API with explicit argument lists rather than shell-specific syntax, so the same entry point works on macOS, Linux, and Windows. It should print each child command and elapsed time, preserve exit codes, avoid network access after locked installation, and never mutate formatting. M0-006 should be the first task to create that script.

## Lockfiles and upgrade policy

Commit `backend/pyproject.toml` plus `backend/uv.lock` for the backend and `frontend/package.json` plus `frontend/package-lock.json` for the frontend. uv describes `uv.lock` as a universal cross-platform lockfile with exact resolved versions and says it should be committed; from the repository root, `uv --directory backend sync --locked` selects that project, validates lock freshness, and refuses to change the lock. `--frozen` is not the CI default because it can use the lock without checking whether project metadata changed. uv documents `--directory` as changing to the given directory before running the command. [uv lockfile](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile), [uv sync](https://docs.astral.sh/uv/concepts/projects/sync/), [uv CLI `--directory`](https://docs.astral.sh/uv/reference/cli/#uv--directory)

Pin uv itself to `0.12.7` in documented bootstrap and CI configuration because uv's minor versions can change behavior and the lock schema. Keep dependency declaration ranges in `backend/pyproject.toml` for compatibility intent while allowing only explicit, reviewed `uv --directory backend lock --upgrade...` changes to rewrite resolutions. The standards-based escape hatch is `uv --directory backend export --format pylock.toml`; the fallback pip workflow would use a `venv` and the experimental `pip lock`, with separate lock output where platforms differ. [uv export](https://docs.astral.sh/uv/concepts/projects/export/), [pip lock](https://pip.pypa.io/en/stable/cli/pip_lock/), [pyproject specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)

Commit `frontend/package-lock.json`, declare `packageManager: "npm@11.19.1"` in `frontend/package.json`, and use only `npm --prefix frontend ci` in CI. npm documents that `npm ci` requires an existing lock, removes a pre-existing `node_modules`, fails when the manifest and lock disagree, and never writes the lock. Commit any project-affecting npm flags in `frontend/.npmrc` so CI uses the same tree-building settings. [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/), [package-lock format](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/)

Lockfiles pin resolution, not trust. Updates still require diff review, license/security checks, and CI. Generated artifacts, virtual environments, `node_modules`, caches, databases, and secrets remain ignored.

## Cross-platform/CI

Use GitHub-hosted Ubuntu as the required fast CI job, then add a small macOS/Windows smoke matrix when M0-002/M0-003 have reproducible installs. GitHub recommends `setup-python` and `setup-node` for consistent runtime versions, while uv's official GitHub guide recommends `astral-sh/setup-uv`, exact uv version selection, and locked sync. CubeAI's nested topology adds the explicit `--directory backend` selection to those uv commands. [Python setup](https://docs.github.com/en/actions/tutorials/build-and-test-code/python), [Node setup](https://docs.github.com/en/actions/tutorials/build-and-test-code/nodejs), [uv GitHub integration](https://docs.astral.sh/uv/guides/integration/github/), [uv CLI `--directory`](https://docs.astral.sh/uv/reference/cli/#uv--directory)

CI policy for M0-007 should be:

- Explicit top-level `permissions: contents: read`; no secrets, write token, service credentials, or deployment permissions in validation jobs. GitHub recommends minimum explicit permissions. [secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- Pin every action to a reviewed full-length commit SHA and retain the release tag in a comment. GitHub identifies a full SHA as the only immutable action reference. [secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- Pin Python `3.14`, Node `24`, npm `11.19.1`, and uv `0.12.7`; then run `uv --directory backend sync --locked --all-groups`, `npm --prefix frontend ci`, and only after both locked installs succeed, `uv --directory backend run python ../scripts/validate.py`.
- Cache download/package-manager data, not `backend/.venv` or `frontend/node_modules`. Key uv cache entries by runner OS, architecture, Python line, uv version, and `hashFiles('backend/uv.lock')`; key npm cache entries by runner OS, architecture, Node/npm lines, and `hashFiles('frontend/package-lock.json')`. Official guidance demonstrates lockfile hashes in cache keys and warns that cache content can be executable. [GitHub cache reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching), [cache security](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching), [uv caching](https://docs.astral.sh/uv/guides/integration/github/#caching)
- Run `uv --directory backend run python ../scripts/validate.py` unchanged across local and CI environments. Platform smoke jobs must use the same locked install ordering plus that root command; they must not have privileged Docker or deployment access.
- Keep Compose outside the required unit-test path. When M0-011 adds it, use the Compose v2-style `docker compose` command (the current major is 5; “v2-style” refers to the CLI integration, not a version constraint), health checks, explicit project names, and disposable synthetic data. Docker documents standalone Compose as legacy. [Compose install overview](https://docs.docker.com/compose/install/)

This design preserves native macOS ARM64 development, Linux CI, and a feasible Windows smoke path. The current machine's Node/npm versions are below the proposed floor, so M0-003 must document a version-manager/bootstrap path rather than assuming global tools.

## Agent friendliness

The proposal gives an agent one read-only root validation command, small workspace-specific commands, deterministic lockfiles, and errors attributable to one check. Standard `pyproject.toml`, npm scripts, and direct subprocess arguments minimize hidden shell or IDE state. Strict type checks and import-boundary contracts turn architectural expectations into fast feedback; synthetic fixed-seed tests preserve provenance and reproducibility.

Agent instructions should say which commands mutate lockfiles or formatting and should reserve those commands for explicit dependency/format changes. CI and local validation must use locked installs, print tool versions, and avoid silent network fallback. A coding agent must not generate an API model inside domain, merge datasets of different provenance, or add a service merely because Compose is available. The proposed layout makes these boundaries visible without creating a distributed architecture.

## Resource estimate

The observed baseline is Apple M4, 16 GiB memory, macOS ARM64, with Python present and Docker absent. No packages were installed, so this task did **not** measure clean-install size, dependency-sync duration, test duration for the future applications, frontend bundle size, or service idle memory. Those measurements belong in M0-002, M0-003, M0-006, and M0-012.

For planning only, not as measured evidence, reserve **0.5–1.5 GiB of working disk** for the Python environment, uv/npm caches, and `frontend/node_modules` after both workspaces exist, and expect the native unit/type/lint toolchain to fit comfortably on an **8 GiB developer or CI machine**. Set an initial validation target of **under 5 minutes on a cold 2-core CI runner and under 2 minutes warm locally**, then replace these estimates with recorded results. Vite 8 itself reports approximately 15 MB more install size than Vite 7 due to its Rust toolchain; that is acceptable within the planning reserve. [Vite 8 announcement](https://vite.dev/blog/announcing-vite8)

Compose adds a Docker daemon, images, and duplicated build context, so it should remain optional and receive a separate measured disk/memory/startup budget in M0-011. The current machine cannot validate that path because Docker is not installed. Cache retention should be bounded; uv specifically documents `uv cache prune --ci` for CI cache efficiency. [uv cache guidance](https://docs.astral.sh/uv/concepts/cache/#caching-in-continuous-integration)

## License and platform observations

This section records technical observations only. It is not a legal opinion or
a transitive dependency audit; M0-009 remains responsible for reproducible
dependency inventory and review policy.

| Scope | Technical observation | Implication |
|---|---|---|
| Repository | CubeAI is MIT licensed. | The proposed direct components need their own review; repository licensing does not decide dependency compatibility. |
| Backend | Python uses the PSF License; uv is Apache-2.0 and MIT dual licensed; FastAPI, Pydantic, pytest, Ruff, mypy, and Hatchling are MIT; Import Linter is BSD-2-Clause. | These are permissive direct-project licenses, subject to human/legal review of the resolved transitive tree. [Python license](https://docs.python.org/3/license.html), [uv licenses](https://github.com/astral-sh/uv/tree/main), [Hatch license](https://github.com/pypa/hatch/blob/hatch-v1/LICENSE.txt) |
| Frontend | Node is MIT with bundled notices; npm is Artistic-2.0; React, Vite, Vitest, ESLint, typescript-eslint, Prettier, and React Testing Library are MIT; TypeScript is Apache-2.0. | The npm lockfile will make the complete tree inspectable, but does not make a compatibility determination. [Node license](https://github.com/nodejs/node/blob/main/LICENSE), [npm license](https://github.com/npm/cli/blob/latest/LICENSE), [TypeScript license](https://github.com/microsoft/TypeScript/blob/main/LICENSE.txt) |
| Runtime platforms | CPython, uv, Node, npm, and Vite support the intended macOS, Linux, and Windows developer/CI path. Linux CI is the initial required job; Windows and macOS remain explicit later smoke targets. | Do not claim cross-platform clean-install proof until M0-002/M0-003 and M0-007 run it. [uv platform support](https://docs.astral.sh/uv/reference/policies/platforms/), [Node installation methods](https://nodejs.org/en/about/previous-releases) |
| Persistence | SQLite core is public domain and comes through CPython's `sqlite3`; no separate database package is proposed. | The selected Python distribution must expose SQLite 3.37+ for STRICT-table capability. [SQLite licensing](https://sqlite.org/purchase/license) |

## Risks and migration considerations

- **Deferred TypeScript major:** TypeScript 6.0 is compatible with the proposed tooling, but its 2026-08-28 release is too fresh for this foundation decision. The selected 5.9 line avoids an immediate migration; revisit 6.0 only through a reviewed lockfile update after M0 frontend validation. [TypeScript 6.0](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html), [typescript-eslint compatibility](https://typescript-eslint.io/users/dependency-versions/)
- **Pre-1.0 tools:** FastAPI and Ruff are maintained but have not declared 1.0 stability. Narrow ranges, exact lock resolution, release-note review, and a lock-update CI run contain the risk. Ruff explicitly reserves breaking changes for minor releases before 1.0. [FastAPI releases](https://fastapi.tiangolo.com/release-notes/), [Ruff versioning](https://docs.astral.sh/ruff/versioning/)
- **uv tool/lock coupling:** uv may change lock schema at a minor release. An exact uv tool pin is therefore part of reproducibility, not merely developer preference. The standards-based export path lowers but does not eliminate migration work. [uv versioning](https://docs.astral.sh/uv/reference/policies/versioning/)
- **Bundled SQLite variance:** the Python build selects the SQLite library. M0-002 must fail clearly below 3.37.0 rather than silently omitting STRICT behavior. A server database remains outside M0 scope. [Python sqlite3](https://docs.python.org/3/library/sqlite3.html), [STRICT tables](https://www.sqlite.org/stricttables.html)
- **Platform drift:** only macOS ARM64 was observed locally. Linux is covered only after M0-007 CI exists; Windows remains a smoke target. Native-extension wheels, paths, and subprocess behavior need empirical checks.
- **Optional Compose unverified:** Docker and Compose are not installed locally. Compose cannot be a prerequisite until a human accepts it and a useful service slice is measured.
- **Supply chain:** lockfiles and caches reproduce bytes selected by dependency resolution but do not establish trust. Pin action SHAs, minimize permissions, review lock diffs, and add the M0-009 scanning policy before releases. GitHub warns that caches and mutable action references can expose trusted jobs. [secure use](https://docs.github.com/en/actions/reference/security/secure-use), [cache security](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching)

## Accepted toolchain

The following is the accepted initial M0 toolchain.

1. Python 3.14 with uv 0.12.7, a standard PEP 621 `backend/pyproject.toml`, Hatchling, committed `backend/uv.lock`, explicit root-level `uv --directory backend ...` commands, FastAPI/Pydantic only at the HTTP boundary, pytest, Ruff, mypy strict mode, and Import Linter.
2. Node 24 with npm 11.19.1, committed `frontend/package-lock.json`, React 19.2, strict TypeScript 5.9, Vite 8.2, Vitest 4.1, React Testing Library, ESLint/typescript-eslint for correctness, and exact Prettier 3.9.6 for formatting.
3. Python stdlib `sqlite3` with a SQLite 3.37.0 STRICT-capability floor; no ORM, server database, production schema, or migration framework in M0-001.
4. Conceptual `backend/src/cubeai/lab/{domain,application}` package roots, with domain independent of frameworks and adapters; do not create them until M0-002 is authorized.
5. Native local commands first, a single cross-platform root validator, least-privilege SHA-pinned GitHub Actions, and Docker Compose 5.5+ only as an optional useful slice after native workflows exist.

The human has approved: (a) the exact Python/uv/Hatchling and Node/npm/React/TypeScript/Vite toolchain stated above; (b) committed `uv.lock` and `package-lock.json` with reviewed explicit upgrades only; (c) native commands plus one future root Python validator, least-privilege CI, and optional—not required—Compose; (d) the SQLite 3.37 STRICT capability floor; and (e) the web-first, local-capable architectural requirement. ADR-0003 is the durable accepted record.

## M0-001 acceptance checklist

- [x] Official current sources are linked directly and carry the common refresh date 2026-09-01.
- [x] Exact runtime/tool/dependency versions are labeled as floors, compatible ranges, or resolved locks.
- [x] uv and pip/venv lock-capable workflows are compared, including migration implications.
- [x] Backend and frontend quality responsibilities, strict checks, import boundaries, and native/root commands are specified.
- [x] Local macOS ARM64 versions and resources are recorded without installing software; unavailable Docker commands are recorded as `not installed`.
- [x] Direct-project licenses and supply-chain limitations are documented.
- [x] Conceptual package layout preserves `cubeai.lab` and keeps domain/application boundaries framework-independent.
- [x] Human approval recorded for the toolchain, lockfile/update policy, native-first workflow, optional Compose posture, SQLite capability floor, and web-first/local-capable requirement.
- [x] The approved decision is recorded in ADR-0003 before dependent scaffolding begins.
- [ ] Follow-on M0-002/M0-003 work validates clean locked installation on supported platforms and replaces planning resource estimates with measurements; this is not an M0-001 completion condition.

## Roadmap/backlog impact

This accepted decision adds the web-first, local-capable boundary without selecting offline technology. M0-001 is **COMPLETE**. M0-002 and M0-003 are **READY** because M0-001 was their only blocker; they remain unstarted. M0-004/M0-005 remain blocked on those workspace issues, followed by M0-006, M0-007, M0-009, M0-011, and M0-012 according to their existing dependencies.

There is no Task 9 decision here, no Forge adoption, no game-protocol change, no production deployment choice, and no effect on M1 scope. Any accepted deviation—especially a server persistence strategy, full-stack frontend framework, mandatory container workflow, or replacement of the modular monorepo—requires separate human direction and, where durable, an ADR.
