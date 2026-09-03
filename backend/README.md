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

## CubeCobra adapter checks

The default suite uses only the reviewed, sanitized CubeCobra contract excerpts
and never performs external requests. It covers identifier-only input, public
mainboard mapping, separate provider/printing/Oracle evidence, duplicate
occurrences, provenance, supplementary-board diagnostics, and bounded failure
outcomes.

One low-frequency live smoke check is deliberately excluded from normal test
runs. It sends no response body to fixtures or logs. Run it only when an
intentional network check against the reference-corpus CORE identifier is
appropriate:

```powershell
$env:CUBEAI_LIVE_SMOKE = "1"
uv --directory backend run pytest -q -o addopts='' -m live_smoke tests/test_cubecobra_live_smoke.py
```

## Scryfall metadata resolver checks

The M1 resolver is a provider-neutral application port with a Scryfall adapter
that accepts only an exact Scryfall printing UUID from `ImportCandidate`.
Callers compose it with an explicit local SQLite cache path; it has no implicit
global database location:

```python
from pathlib import Path

from cubeai.lab.adapters.scryfall import SQLiteScryfallCache, ScryfallMetadataResolver

resolver = ScryfallMetadataResolver(
    SQLiteScryfallCache(Path("local/scryfall-cache.sqlite3"))
)
```

The cache is keyed by the provider printing UUID and stores only the approved
metadata subset, cache timestamp, and response schema version. It is fresh for
24 hours. Offline mode never sends requests: it returns fresh or stale cached
records when present and a structured unavailable result for a miss. Online
resolution uses only cache misses/stale refreshes, deduplicates provider
requests without merging Cube memberships, and returns one result per original
membership occurrence.

The default test suite is fully offline and covers cache semantics, exact
printing/Oracle mismatch diagnostics, duplicate memberships, collection
`not_found`, malformed and unavailable provider responses, and pacing/retry
limits. It uses only the CubeAI-authored synthetic collection fixture; it does
not download Scryfall bulk data or images.
