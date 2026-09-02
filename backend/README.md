# CubeLab backend workspace

## Prerequisites

- Python `>=3.14,<3.15`
- [uv 0.12.7](https://docs.astral.sh/uv/)

## Local commands

Install the locked project and development dependencies:

```powershell
uv --directory backend sync --locked --all-groups
```

Run the tests:

```powershell
uv --directory backend run pytest -q tests
```

Run the backend quality and architecture checks:

```powershell
uv --directory backend run ruff format --check .
uv --directory backend run ruff check .
uv --directory backend run mypy --strict src
uv --directory backend run lint-imports
```

Build the source distribution and wheel:

```powershell
uv --directory backend build
```

FastAPI and health endpoints, external adapters, persistence, and product
workflow automation are deliberately deferred to later milestones. The
architecture check keeps `cubeai.lab.domain` independent from API, adapter,
persistence, and framework modules.
