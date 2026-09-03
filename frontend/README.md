# CubeUI

CubeUI is CubeAI's single web-first frontend codebase. Its M0 status component
requests the local `/health` endpoint and displays `Backend connected` only
after the expected response. Vite proxies that path to the local health server
when started through the repository root `dev` command. Routing,
authentication, offline/PWA/sync, global state, and a design system remain
deferred.

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

When running the frontend directly, also start the backend health server in a
second terminal (`uv --directory backend run --locked python -m cubeai.api`).
The root `dev` command starts both processes for the M0 connectivity proof.

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
