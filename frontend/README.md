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
corepack npm --prefix frontend test
corepack npm --prefix frontend run typecheck
corepack npm --prefix frontend run build
```

`ci` uses the committed `package-lock.json` to reproduce the dependency tree.
The development server prints its local URL when it starts.
