# CubeCobra Import Contract

**Status:** Accepted and frozen for the initial import contract on 2026-09-02.
This authorizes no adapter or downstream implementation. **Consumers when
separately authorized:** M1-003's provider-neutral import candidates and
M1-004's CubeCobra adapter. M1-002 continues to own domain types; this
document specifies source semantics only.

## 1. Scope and evidence

The frozen supported subset is one current, unauthenticated, public
CubeCobra JSON snapshot. It does not cover write access, HTML scraping,
historical snapshots, CubeCobra draft/pick data, Scryfall resolution, or an
archetype model.

The fixed population was used without adding sources: the nine CORE/EDGE cubes
and the Fifteen Card Highlander, 1UP Convention, and Curated by Kiwi stress
cases in the [reference corpus](reference-cube-corpus.md). All twelve returned
HTTP 200 on 2026-09-02. They confirmed `mainboard`, `maybeboard`, and
`basics`; public and unlisted visibility; nonempty supplementary boards; real
mainboard duplicates; and one public result with `shortId: ""`.

Evidence labels below mean: **observed** in that bounded live corpus,
**source-defined** in CubeCobra's current official implementation, or
**inference** where CubeAI must choose a conservative behavior. CubeCobra does
not publish a versioned compatibility guarantee for this route, so its source
is implementation evidence, not a stability promise. The relevant sources are
the [JSON route](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/router/routes/cube/api/cubeJSON.ts),
[Cube type](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Cube.ts),
[Card type](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Card.ts),
and [prior reconnaissance](cubecobra-reconnaissance.md).

## 2. FROZEN / SUPPORTED source

Accept one nonempty CubeCobra full ID or nonempty `shortId`, fetch exactly
`GET /cube/api/cubeJSON/:id`, and accept only a JSON object whose returned
`visibility` is `"pu"`. Preserve the returned full ID even when lookup used a
short ID. Empty short IDs are valid *returned optional data*, never valid
input. UI page URLs are not supported input in this frozen contract; the
adapter must not infer an ID from arbitrary URLs.

The future adapter must distinguish these outcomes:

| Outcome | Meaning |
| --- | --- |
| `SUPPORTED` | All required source fields and supported memberships are valid. |
| `SUPPORTED_WITH_OPTIONAL_DATA_ABSENT` | Required data is valid; one or more optional fields are absent or `null` where allowed below. |
| `UNSUPPORTED` | A known excluded condition, such as non-public visibility or a nonempty non-mainboard. |
| `INVALID_SOURCE` | A successful response lacks or malforms a required field. |
| `UNKNOWN_SOURCE_SHAPE` | A relevant but unestablished condition, such as custom/voucher semantics or missing identity evidence. |

HTTP/input/transport failures are separate from those outcomes: malformed
input or invalid `date` is `SOURCE_REQUEST_INVALID`; a 404 is
`SOURCE_INACCESSIBLE`; 429 is `SOURCE_RATE_LIMITED`; 5xx and network failure
are `SOURCE_UNAVAILABLE`. None is a successful empty Cube.

## 3. Cube-level field contract

| Source field | Classification | Required shape and CubeAI meaning | Missing/malformed behavior |
| --- | --- | --- | --- |
| `id` | REQUIRED | Nonempty string; provider snapshot identity/provenance, not a local Cube ID. | `INVALID_SOURCE`. |
| `name` | REQUIRED | Nonempty string; source display label only. | `INVALID_SOURCE`. |
| `visibility` | REQUIRED | String exactly `"pu"` for this frozen contract. | Missing/malformed: `INVALID_SOURCE`; any other value: `UNSUPPORTED`. |
| `cards.mainboard` | REQUIRED | Array; every array occurrence is a candidate membership, in response-array order. | Missing/non-array: `INVALID_SOURCE`; empty: `UNSUPPORTED` (`EMPTY_MAINBOARD`), not proof that CubeCobra is malformed. |
| `shortId` | OPTIONAL | Nonempty string is a returned alias. `""`, `null`, or absence has no alias meaning. | Import continues; retain the exact absence state in provenance. |
| `cardCount` | OPTIONAL | Numeric source assertion; compare to mainboard length only as a diagnostic. | Absence/null: continue. A numeric mismatch is diagnostic only; nonnumeric value is preserved as an optional-shape diagnostic. |
| `version`, `dateLastUpdated` | PRESERVED | Source change markers for provenance/change detection only. | Preserve value or absence; do not infer immutability, ordering, or historical retrieval semantics. |
| `dateCreated` | IGNORED | Not needed for the first import meaning. | No effect. |
| `cards.maybeboard`, `cards.basics`, other keys | See board policy | Array-valued boards are inspected only to diagnose policy; non-array keys are not boards. | See below. |
| owner, display/theme, descriptions, curator format settings, categories | IGNORED | Not needed to represent the supported Cube membership. | No effect; do not create CubeAI archetypes or draft rules. |

## 4. Membership field contract

| Source field | Classification | Required shape and meaning | Missing/malformed behavior |
| --- | --- | --- | --- |
| mainboard array occurrence | REQUIRED | One distinct source membership candidate per array element. Its local identity must be allocated by CubeAI, never derived solely from card IDs. | No deduplication. |
| response-array position | REQUIRED | Deterministic source order inside this retrieved snapshot. | Derived from array position; source stability across edits is not claimed. |
| `cardID` | REQUIRED | Nonempty provider card reference retained separately from printing and Oracle evidence. | `INVALID_SOURCE`; it does not become a replacement printing ID. |
| `details.scryfall_id` | REQUIRED for a supported normal membership | Nonempty string used only as an exact-printing candidate. | `UNKNOWN_SOURCE_SHAPE`; do not name-match or fabricate a printing. |
| `details.oracle_id` | REQUIRED for a supported normal membership | Nonempty string used only as Oracle/rules-identity evidence. | `UNKNOWN_SOURCE_SHAPE`; do not derive or fabricate an Oracle ID. |
| `details.set`, `details.collector_number`, `details.language` | PRESERVED | Optional printing corroboration, not a fallback resolver in this contract. | Preserve absence/null/value; later metadata policy decides resolution precedence. |
| `board`, `index` on the row | PRESERVED | Provider annotations retained for diagnostics/provenance; response-array position is the contract's order. | Do not reject an otherwise valid row solely for absence. |
| `tags`, `notes`, `status`, `finish`, `addedTmsp`, `custom_name`, `imgUrl`, `imgBackUrl` | PRESERVED when structurally valid | Source-attributed membership annotations/display overrides, never Oracle/card facts or CubeAI archetypes. | Absence/null/empty are distinct source states and do not invalidate a normal membership. A relevant wrong type is diagnostic. |
| `voucher_cards` or a nonempty custom/unresolved marker | UNKNOWN | No selected public row established its interoperable representation. | `UNKNOWN_SOURCE_SHAPE`; fail closed without creating a fake identity. |

## 5. Identity and duplicates

`cardID`, `details.scryfall_id`, `details.oracle_id`, one Cube membership, and
a CubeAI local identity are different scopes. The source currently exposes
separate printing and Oracle fields; neither may be collapsed into the other,
even when the provider card reference happens to equal the Scryfall ID.

Duplicates are supported evidence, not an error: aquaone, HeatherCube, Hackett
Cube, and game zones had repeated mainboard `cardID` values in the corpus. Two
equal printing/Oracle pairs in the mainboard remain two memberships, each with
its own response-array position and source annotations. There is no evidence
of a stable source membership ID across cube edits, so no such guarantee is
claimed.

## 6. Board and optional-data semantics

**FROZEN:** import `mainboard` only.
For every other nonempty array-valued board, retain its name and count in
source provenance and return a non-blocking `UNSUPPORTED_NON_MAINBOARD`
warning; do not merge, discard silently, or assign draft/sideboard semantics.
The valid mainboard import continues. Empty known boards are recorded without a
diagnostic. A non-array `cards` property is ignored as a non-board (an `id`
property was observed in prior reconnaissance).

The corpus established `maybeboard` and `basics`, not their CubeAI semantics,
and did not establish other board names. Therefore a nonempty unknown named
board is likewise `UNSUPPORTED_NON_MAINBOARD`, not a new supported shape.

For optional membership data, absence, `null`, empty string, and empty array
must be retained as distinguishable provider observations when the field is
present; the importer must not invent a default. Only a required field's
absence or malformed shape makes the snapshot invalid or unknown as specified
above.

## 7. Provenance and change detection

For every accepted snapshot retain: normalized request identifier; exact JSON
endpoint URL; retrieval time; returned full ID; returned nonempty short ID if
any; visibility; `version`; `dateLastUpdated`; `cardCount` value/absence; and
per-membership board, response position, provider IDs, and preserved metadata.

`version` and `dateLastUpdated` are source provenance, not a CubeAI
`CubeVersion`, a complete historical record, an ETag, or proof of monotonic
ordering. The `date` query is source-defined but **unsupported** here; a
future historical contract needs independent evidence and approval.

Change detection is intentionally review-driven: ordinary tests replay the
checked-in excerpts offline. An opt-in, low-frequency smoke check may compare
the current route's required shapes with the excerpt contract. Any drift or
fixture refresh must record retrieval date, source URL, observed behavior,
sanitization, and a reviewer decision; it must not silently replace fixtures.

## 8. FROZEN / UNSUPPORTED conditions

| Condition | Evidence | Initial behavior |
| --- | --- | --- |
| Unlisted (`"un"`) or private/non-public visibility | `"un"` was observed for 1UP; official source hides non-viewable cubes. | Reject as `UNSUPPORTED_VISIBILITY`; do not bypass access control. |
| Unavailable/private source (404) | Official route and live missing-ID response. | `SOURCE_INACCESSIBLE`; no retry or access workaround. |
| Nonempty maybeboard, basics, or another board | Observed across primary corpus; semantics unestablished. | `UNSUPPORTED_NON_MAINBOARD` diagnostic; mainboard policy above applies. |
| Historical `date` query | Official route accepts it; no corpus history investigation. | `UNSUPPORTED_HISTORICAL_SNAPSHOT`. |
| CSV, HTML, write access, authentication, crawl/bulk import | Out of M1-001 scope. | Reject/not implemented. |
| Draft, pick, deck, game, and analytics data | No selected response established it; not needed for Cube definition import. | Deferred, not an import field. |

## 9. UNKNOWN source behavior

- CubeCobra's public representation of a custom card, voucher, unresolved
  identity, or a normal card missing either nested identity remains unknown.
- Additional named-board semantics, source membership ID stability, short-ID
  longevity, and URL page grammar remain unknown.
- `version`/timestamps do not establish historical completeness, monotonicity,
  cache validation, or concurrency semantics.
- The source route's 100-per-minute limiter is a source-defined ceiling, not
  an approved polling/retry policy. Live 429 and 500 bodies were not induced.

## 10. Frozen fixtures and deterministic research probes

The reviewed, network-independent excerpts are in
[`fixtures/contracts/cubecobra/`](../../fixtures/contracts/cubecobra/): one
normal public membership, one real duplicate pair, and observed 400/404 error
bodies. Each contains only IDs and fields required to prove this contract—no
card name, full list, image, owner, user content, or private/unlisted payload.
The existing [synthetic custom/unresolved fixture](../../fixtures/synthetic/duplicate-membership-unresolved-custom.json)
remains CubeAI-authored and is explicitly not provider evidence.

The research probe must deterministically prove: (1) a required public
mainboard excerpt can be projected; (2) optional fields may be absent; (3) two
equal printing/Oracle pairs remain two occurrences; (4) custom/unresolved
testing has no invented IDs; and (5) 400 and 404 remain distinguishable. It is
not an adapter or a promise that the excerpts are complete payloads.

## 11. Frozen human decisions

- **Public-only:** accept only returned `"pu"` sources. Explicitly supplied
  unlisted, private, and inaccessible sources are unsupported.
- **Identifier-only:** accept a full ID or nonempty `shortId`; page URL parsing
  is outside this provider/application contract.
- **Mainboard-only:** import `mainboard`; diagnose every nonempty
  supplementary board without merging or assigning domain semantics. The
  diagnostic is non-blocking for an otherwise supported mainboard import.
- **Membership occurrence:** one mainboard array element is one membership;
  equal provider, printing, or Oracle identifiers never collapse occurrences.
- **Identity scopes:** retain printing and Oracle evidence separately.
- **Custom/unresolved:** fail closed; no fabricated IDs, fuzzy matching, or
  synthetic-fixture inference about CubeCobra shape.
- **Provenance:** source markers are not CubeAI version history.
- **Provider excerpts:** retain the existing minimal, sanitized excerpts. Their
  response-data licensing is not established; CubeCobra software licensing
  makes no response-data licensing conclusion.

## 12. DEFERRED extensions

Explicitly supplied unlisted sources, supported Cube page-URL parsing, named
boards, historical snapshots, custom/unresolved resolution, printing fallback,
and draft/pick data need their own evidence and approved contract extension.

## 13. Downstream guidance (not design)

- M1-002 must keep Cube, membership, printing, and Oracle identities distinct.
- M1-003 must represent the five outcomes and preserve source provenance; no
  CubeCobra type enters a domain entity.
- M1-004 may implement only with separate authorization, using these fixtures
  offline, bounded HTTP behavior, and no undocumented fallback scraping.
- M1-005/M1-006 own any printing fallback and custom/unresolved resolution;
  this contract does not authorize fuzzy matching.

## Acceptance evidence

| M1-001 criterion | Evidence in this change |
| --- | --- |
| Distinguish guarantees from observations | Scope/evidence labels, field tables, and unknown list. |
| Fixtures for normal, duplicate, custom/unresolved, and errors where available | Two sanitized public excerpts, two live error excerpts, and the separate existing synthetic custom/unresolved fixture. |
| Change-detection/update procedure | Provenance and change-detection section. |
| Fixture schema and replayable research probe | `backend/tests/test_cubecobra_contract_research.py`. |
| Human approval | The frozen decisions above and ADR-0004. |
| Official verification | `uv --directory backend run pytest -q tests` passed with 14 tests under uv 0.12.7 and Python 3.14.7. |
