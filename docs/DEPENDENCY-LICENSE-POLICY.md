# Dependency and license review policy

This policy makes dependency review repeatable. It is a review aid, not legal
advice and not an automated license-compatibility guarantee. In particular, it
does not decide whether Forge, card data, ratings, images, or other external
content may be used, redistributed, or used to train a model. Those decisions
need their own source, attribution, and license review.

## Before adding or upgrading a dependency

Every proposed direct dependency or lockfile upgrade must state:

1. the concrete capability it enables and why the standard library or existing
   dependency is insufficient;
2. the maintained version, support status, and expected upgrade burden;
3. its declared license and the licenses newly introduced transitively; and
4. simpler alternatives considered, including no new dependency.

The proposal must identify the affected workspace and preserve the boundaries
in the architecture and ADR-0003. New data packages additionally need a source
and provenance/license decision. Do not add a package merely to generate this
report.

## Reproducible reports

Run the locked installs first when package metadata is not already available:

```powershell
uv --directory backend sync --locked --all-groups
corepack npm --prefix frontend ci
```

From the repository root, inventory all direct and transitive packages from the
committed locks:

```powershell
uv --directory backend tree --locked
corepack npm --prefix frontend ls --package-lock-only --all
```

The backend command is `uv tree --locked`; the frontend command is `npm ls
--package-lock-only --all`. Neither changes either lockfile.

Then produce license review tables:

```powershell
uv --directory backend run --locked python ../scripts/report_backend_licenses.py
node scripts/report_frontend_licenses.mjs
```

The backend reader uses the locked environment's installed distribution
metadata, because `uv.lock` does not record license expressions. The frontend
reader uses the committed `package-lock.json`, which does record them. Both
outputs are tab-separated, sorted deterministically, and label every package
`ALLOWED`, `ALLOWLISTED`, or `REVIEW_REQUIRED`. Reports are review artifacts;
do not commit generated output unless a later issue explicitly requests it.

Run the offline reader guardrails, including a controlled package with no
license, with:

```powershell
uv --directory backend run --locked pytest -q tests/test_dependency_license_reports.py
node --test scripts/report_frontend_licenses.test.mjs
```

On hosts with Make available, `make dependency-inventory`, `make
license-report`, and `make dependency-license-test` mirror these native
commands; Make is optional.

## Failure and allowlist policy

`config/dependency-license-policy.json` contains the exact SPDX expressions
accepted for the current review. A missing, malformed, or unlisted expression
is visible as `REVIEW_REQUIRED` and causes the license-report commands to fail.
Fixing it requires a human review; changing a package's displayed name or
version does not silence the failure.

The `allowlist` is intentionally empty by default. A temporary exception must
be keyed as `backend:<normalized-name>@<version>` or
`frontend:<package-name>@<version>` and include the observed `license`, a
specific `reason`, `reviewed_by`, and an ISO-8601 `expires_on` date. The report
validates that information and prints `ALLOWLISTED`, but an expired exception
still fails. Remove an exception after a license is corrected or a package is
removed. Do not use an allowlist entry for an unreviewed package, a source/data
license decision, or a broad name/version pattern.

The current accepted expressions are permissive licenses already present in the
locked frontend tree. Adding an expression to the policy is a review decision,
not evidence of compatibility for every future use.
