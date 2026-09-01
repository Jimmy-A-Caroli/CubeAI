# Fixture and Test-Data Policy

M0-008 establishes a small, offline-first rulebook for data committed solely
to protect CubeAI behavior. It does not define a CubeCobra import contract or
turn the Reference Cube Corpus into a dataset.

## Rules

1. **Default to synthetic data.** Domain and application tests use small,
   hand-authored, CubeAI-owned data with obvious synthetic names and IDs.
2. **Every committed fixture states its purpose and provenance.** It must say
   what behavior it protects and record source plus license. The repository
   license is `MIT` for CubeAI-authored data; do not infer a third-party license.
3. **Keep fixtures local unless a boundary genuinely shares them.** Test-owned
   data stays beside its tests; `fixtures/synthetic/` is only for small shared
   synthetic examples. Do not create a registry or fixture framework.
4. **Provider data is exceptional.** A sanitized provider-derived fixture may
   be committed only when a concrete adapter contract needs it and review
   records its provider, retrieval date, source shape, license/terms context,
   sanitization, and protected behavior.
5. **Provider fixtures are excerpts, not datasets.** Retain only fields and
   rows needed by the contract; remove user, private, session, tracking, image,
   and other unnecessary content. Do not refresh a fixture merely because its
   upstream source changed.
6. **The default suite is network-independent.** Fixtures are checked in,
   tests must not fetch live providers, and mutable external sources are opt-in
   research/smoke evidence rather than ordinary test input.
7. **Preserve determinism.** Commit stable ordering and explicit values. Any
   future generated data must keep its generator and fixed seed under review;
   tests load fresh data and must not mutate shared fixture state.
8. **Never commit sensitive or private data.** Credentials, tokens, passwords,
   authorization/session material, private Cubes, personal data, and private
   API responses are prohibited.
9. **Reference sources are not fixtures.** The public references in
   [Reference Cube Corpus Discovery](research/reference-cube-corpus.md) guide
   later fixture selection but their complete lists must not be copied here.
10. **Change fixtures only with the behavior.** A fixture update needs the
    protected behavior, provenance, sanitization, and the validating test to
    be reviewed together. This is a technical policy, not legal advice.

## Fixture categories and locations

| Category | Use | Location | M0-008 state |
|---|---|---|---|
| Synthetic | Default domain/application/UI behavior | Test-local data, or `fixtures/synthetic/` when shared | One example committed |
| Sanitized contract | A reviewed external adapter shape | Future `fixtures/contracts/<provider>/` | Deferred to the owning contract issue |
| Reference source | Research/reproducibility pointer | `docs/research/` | Existing research only |
| Generated | Later property/scale input with fixed seed and code | Near its owning test | No generator created |

## Current synthetic example

[`duplicate-membership-unresolved-custom.json`](../fixtures/synthetic/duplicate-membership-unresolved-custom.json)
is deliberately not a production Cube. It has three distinct memberships:
two share one clearly synthetic printing/Oracle pair, and one is explicitly
`unresolved_custom` with no fabricated provider identity. Its test validates
the declared shape and scans committed JSON fixtures for common secret markers.

Run the focused check from the repository root:

```powershell
uv --directory backend run pytest -q tests/test_fixture_policy.py
```

M1-001 may decide whether and how to create actual CubeCobra contract fixtures.
Until then, no CubeCobra/Scryfall response, CubeCon list, card dataset, or live
network call belongs in `fixtures/`.
