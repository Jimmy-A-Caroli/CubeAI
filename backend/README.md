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

Build the source distribution and wheel:

```powershell
uv --directory backend build
```

FastAPI and health endpoints, adapters, persistence, and quality or boundary
automation are deliberately deferred to later milestones.
