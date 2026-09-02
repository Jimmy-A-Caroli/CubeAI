# Shared Test Fixtures

This directory holds only small, reviewable data intentionally shared across a
meaningful test or future contract boundary. The policy is
[Fixture and test-data policy](../docs/FIXTURE-TEST-DATA-POLICY.md).

- `synthetic/` contains CubeAI-authored, network-independent examples.
- `contracts/cubecobra/` contains the M1-001 reviewed, sanitized public-source
  excerpts for the frozen contract. They are not full payloads or an implemented
  adapter. See that directory's README for provenance, data-use limitations,
  and the update procedure.
