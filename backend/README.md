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

The M0 connectivity proof exposes a minimal WSGI health endpoint. Start it
directly when developing the backend alone:

```powershell
uv --directory backend run --locked python -m cubeai.api
```

It binds to `http://127.0.0.1:8000` and responds to `GET /health` with
`{"status": "ok"}`. The root `dev` command also starts CubeUI and is the
recommended way to verify the full M0 status view.

External adapters, persistence, and product workflow automation remain outside
this health proof. The architecture check keeps `cubeai.lab.domain` independent
from API, adapter, persistence, and framework modules.
