# CubeUI

CubeUI is CubeAI's single web-first frontend codebase. The current status is
static: API fetching, routing, authentication, offline/PWA/sync, global state,
and a design system are deliberately deferred.

## Requirements

- Node `>=24,<25`
- npm `11.19.1`

## Commands

Run these commands from the repository root.

```sh
corepack npm --prefix frontend ci
corepack npm --prefix frontend run dev
corepack npm --prefix frontend run format
corepack npm --prefix frontend run format:check
corepack npm --prefix frontend run lint
corepack npm --prefix frontend test
corepack npm --prefix frontend run typecheck
corepack npm --prefix frontend run build
```

`ci` uses the committed `package-lock.json` to reproduce the dependency tree.
The development server prints its local URL when it starts.

## Quality checks

- `format` applies Prettier's project-default formatting; `format:check` reports
  formatting drift without writing files.
- `lint` runs ESLint correctness checks, including type-aware TypeScript rules
  for `src/**/*.ts` and `src/**/*.tsx`; it does not format code.
- `typecheck` runs TypeScript's strict project check.
- `test` runs the Vitest unit suite, and `build` runs the production TypeScript
  and Vite build.

The focused axe accessibility unit test is not a substitute for later browser
accessibility coverage requested by product features.
