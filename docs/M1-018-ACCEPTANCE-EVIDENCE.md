# M1-018 acceptance evidence

## Current scope

M1-016 and M1-017 are complete. M1-018 is now `READY`; this record captures
the evidence gathered before its supervised exit review. It does not claim
that a public-provider import succeeded in every execution environment.

## Deterministic local scenario

`backend/tests/test_local_api.py::test_m1_acceptance_replays_the_fixed_fixture_through_restart`
uses the reviewed synthetic fixture boundary and exercises the public local
API in this order:

1. import a four-membership fixture and freeze a usable Cube version;
2. validate a fixed two-seat, one-pack, two-card, seed-13 configuration;
3. start, complete, and persist the one-human-seat draft;
4. repeat the identical scenario in a fresh SQLite directory and compare the
   first human pack, human pool, completion state, and empty final pack; and
5. recreate the API against the first SQLite directory and resume the completed
   human-safe view.

The test deliberately keeps provider payloads out of the fixture. Existing
domain, Bot, and SQLite tests cover exact event replay plus human/Bot actor and
strategy provenance; the API still exposes only the human-safe projection.

## Local UI review

On 2026-09-04, the integrated Vite UI was inspected against the local API at
1440px and 390px. The entry workflow rendered without horizontal overflow, the
CubeCobra ID field had a visible keyboard focus state, and Vite forwarded both
`/health` and `/v1` requests. The public source error path rendered grouped
`source_unavailable` diagnostics and did not enable draft start.

## Opt-in public-source smoke

The opt-in `modovintage` smoke was attempted through the local UI/API on
2026-09-04. CubeCobra could not be reached from that execution environment, so
the bounded adapter returned the expected `source_unavailable` diagnostic. No
provider response body was retained. This is a known external limitation, not
a successful public-Cube acceptance result; M1-018 must repeat the smoke from
an environment that can reach CubeCobra before the M1 exit review is closed.

## Non-goals checked

The flow adds no authentication, hosted services, analytics, cards-seen
history, draft advice, gameplay, multi-seat views, or client-side copies of
hidden draft state.
