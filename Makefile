setup:
	uv --directory backend sync --locked --all-groups
	corepack npm --prefix frontend ci
dependency-inventory:
	uv --directory backend tree --locked
	corepack npm --prefix frontend ls --package-lock-only --all
license-report:
	uv --directory backend run --locked python ../scripts/report_backend_licenses.py
	node scripts/report_frontend_licenses.mjs
dependency-license-test:
	uv --directory backend run --locked pytest -q tests/test_dependency_license_reports.py
	node --test scripts/report_frontend_licenses.test.mjs
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
