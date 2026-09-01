# CubeUI

CubeUI is CubeAI's single web-first frontend codebase. Local/offline delivery
technology is deliberately deferred; this workspace does not implement it.

## Requirements

- Node `>=24,<25`
- npm `11.19.1`

## Commands

Run these commands from `frontend/`.

```sh
corepack npm install
corepack npm run dev
corepack npm test
corepack npm run typecheck
corepack npm run build
```

`npm install` uses the committed `package-lock.json` to reproduce the resolved
dependency tree. The development server prints its local URL when it starts.
