setup:
	uv --directory backend run --locked python ../scripts/cubeai.py setup
format:
	uv --directory backend run --locked python ../scripts/cubeai.py format
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
	uv --directory backend run --locked python ../scripts/cubeai.py check
test:
	uv --directory backend run --locked python ../scripts/cubeai.py test
dev:
	uv --directory backend run --locked python ../scripts/cubeai.py dev
