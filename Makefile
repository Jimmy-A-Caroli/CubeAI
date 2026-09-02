setup:
	uv --directory backend sync --locked --all-groups
	corepack npm --prefix frontend ci
check:
	uv --directory backend run ruff format --check .
	uv --directory backend run ruff check .
	uv --directory backend run mypy --strict src
	uv --directory backend run lint-imports
	corepack npm --prefix frontend run format:check
	corepack npm --prefix frontend run lint
	corepack npm --prefix frontend run typecheck
test:
	uv --directory backend run pytest -q tests
	corepack npm --prefix frontend test
dev:
	uv --directory backend run python -m cubeai.api
