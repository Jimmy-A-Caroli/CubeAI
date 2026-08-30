# CubeCobra import reconnaissance

Accessed 2026-08-30. This report distinguishes current official source-code
behavior from one deliberately selected public response. CubeCobra does not
publish a versioned public API contract or compatibility policy for this
endpoint. Source-defined behavior therefore remains changeable implementation
evidence, not a stability guarantee.

## Question

What is the smallest plausible CubeCobra import boundary for M1 that accepts a
public cube URL or identifier, preserves Cube and printing identities, handles
duplicate memberships and boards deterministically, and fails diagnostically
when the upstream shape cannot be mapped safely?

## Methodology

The review used only the official CubeCobra repository and one deliberately
selected public cube. It inspected the current route, router, data-access,
Cube/Card datatype, and CSV-export source without credentials, enumeration, or
broad HTML scraping:

- [CubeCobra official repository](https://github.com/dekkerglen/CubeCobra)
- [cube JSON route](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/router/routes/cube/api/cubeJSON.ts)
- [filesystem route construction](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/router/router.ts)
- [Cube data access](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/dynamo/dao/CubeDynamoDao.ts)
- [Cube datatype](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Cube.ts)
- [Card and CardDetails datatypes](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Card.ts)
- [CSV download route](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/router/routes/cube/download.ts)
- [CSV field writer](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/serverutils/cube.ts)
- selected public example: [Beginner's Tavern](https://cubecobra.com/cube/about/BeginnersTavern)

Exactly one cube-data GET was made, to
`https://cubecobra.com/cube/api/cubeJSON/BeginnersTavern`. No historical
snapshots, private cubes, alternate identifiers, error cases, CSV downloads,
or other public cubes were requested.

## Documented behavior

Here, “documented” includes behavior expressed by CubeCobra's official source.
It does not imply that the project promises backward compatibility.

### URL and identifier handling

The filesystem router maps the route source to
`GET /cube/api/cubeJSON/:id`. The data-access layer resolves `:id` as either a
Cube UUID or the user-facing `shortId`. The same repository exposes cube page
routes and a CSV download route, but the JSON route is the narrowest structured
source for an adapter. The JSON route permits cross-origin requests and accepts
an optional `date` query containing a Unix timestamp in milliseconds for a
historical snapshot.

The JSON route currently applies a limit of 100 requests per 60-second window.
It has explicit failures for a missing ID (`400`), invalid `date` (`400`), a
missing or non-viewable cube (`404`), rate limiting (`429`), and an unhandled
retrieval error (`500`). The source provides no client retry, caching, or
version-negotiation contract.

### Cube metadata and card boards

The Cube datatype separates the full Cube `id` from `shortId` and includes
`name`, `visibility`, `dateCreated`, `dateLastUpdated`, `cardCount`, and
`version`, plus owner/display metadata. Visibility values are source-defined as
public (`pu`), private (`pr`), and unlisted (`un`). Cube card storage is an
object of named board arrays. `mainboard` is required by the source model;
`maybeboard`, `basics`, and additional named boards are possible. The current
data-access implementation populates card details and annotates each card with
its `board` and `index` before the route serializes it.

The repository's Card datatype exposes the following import-relevant fields:

| Layer | Current source fields | Meaning for CubeAI |
| --- | --- | --- |
| Cube source identity | `id`, `shortId` | Provider identity and user-facing alias; neither is a CubeAI domain ID. |
| Cube version metadata | `version`, `dateLastUpdated`, `cardCount` | Snapshot/change evidence; not membership identity. |
| Membership position | board key, `board`, `index`, array order | One upstream occurrence and its board placement. |
| Membership annotations | `tags`, `notes`, `status`, `finish`, `addedTmsp` | Provider observations to preserve without treating them as Oracle facts. |
| Provider card reference | `cardID` | Required by CubeCobra's Card type, but custom-card semantics are not specified as a stable external contract. |
| Exact printing evidence | `details.scryfall_id`, `details.set`, `details.collector_number`, `details.language` | Candidate Scryfall printing identity and corroborating printing attributes. |
| Oracle evidence | `details.oracle_id` | Candidate Oracle identity, distinct from a printing. |
| Display overrides | `custom_name`, `imgUrl`, `imgBackUrl` | Membership/provider display overrides, not canonical card facts. |
| Special content | `voucher_cards` | A source relationship that needs an explicit product decision before import. |

The CSV route defaults to the mainboard and can select all or named boards. Its
current header includes name, set, collector number, board, maybeboard, image
URLs, tags, notes, Custom, Voucher, finish, and status-related fields. CSV is
less attractive for M1 because it omits the structured identity relationship
available from `details.scryfall_id` and `details.oracle_id`, and its header is
also unversioned.

### Duplicates, printings, and custom cards

Boards are arrays, so repeated elements are retained rather than collapsed by
the route. CubeCobra's `cardID`, the nested Scryfall/Oracle IDs, and the board
position are different concepts. No current source field is documented as a
globally stable identity for one membership occurrence across cube edits.

The source supports `custom_name`, image overrides, a CSV `Custom` marker, and
voucher relationships. It does not define an external guarantee that a custom
card has a valid Scryfall printing or Oracle ID. A CubeAI adapter must therefore
not manufacture either identity, fold a custom card into a same-named Oracle
card, or silently discard it.

## Observed behavior

The single public GET returned HTTP JSON for a public 360-card cube when using
its short ID. The selected fields were:

| Observation | Value |
| --- | --- |
| Cube full ID | `2803c489-4b60-4639-a952-b1964c4996a2` |
| Short ID | `BeginnersTavern` |
| Name / visibility | `Beginner's Tavern` / `pu` |
| Version / last updated | `9` / `1744647520782` |
| Declared card count | `360` |
| Mainboard / maybeboard / basics lengths | `360` / `0` / `5` |
| First mainboard position | `board: mainboard`, `index: 0` |
| First provider card ID | `f632be90-9e7f-41f8-a52e-a2952354d730` |
| First nested Scryfall printing ID | `f632be90-9e7f-41f8-a52e-a2952354d730` |
| First nested Oracle ID | `ca773c52-ca64-463c-99cf-e71b59d2cff7` |
| First printing coordinates | set `tdm`, collector number `8`, language `en` |

The response's `cards` object also contained a non-board `id` value, so an
adapter must validate named board values as arrays instead of assuming every
property is a board. `dateCreated` was `null` despite its non-null appearance in
the current datatype, showing that production data can be older or looser than
the TypeScript declaration. The example did not exercise duplicate cards,
custom cards, additional user boards, unavailable cubes, rate limiting, or
history.

## Assumptions and unknowns

- A raw short ID and UUID are plausible supported inputs, but no public naming
  grammar or permanence guarantee was found for `shortId`.
- Current page URL paths may change independently of the JSON route. Which page
  forms M1 accepts is a human-owned product contract, not something to infer
  from arbitrary CubeCobra URLs.
- A normal card's `cardID` equaled `details.scryfall_id` in the one example, but
  this is not evidence that equality holds for every printing, legacy record,
  custom card, or voucher.
- `dateLastUpdated` and `version` appear suitable for snapshot provenance and
  change detection, but no monotonicity or concurrency guarantee was found.
- Board array order is usable as deterministic input order for one snapshot;
  stability across edits is unknown.
- The endpoint's operational availability, long-term route stability, and
  acceptable polling frequency are not guaranteed. The source rate limiter is
  a ceiling, not a recommended client schedule.
- Historical `date` imports, unlisted/private access, custom cards, vouchers,
  and non-mainboard board semantics remain explicitly outside the proposed M1
  baseline until humans accept a contract.

## Evidence classification

| Claim | Documented | Observed | Assumption | Source | M1 contract impact |
| --- | --- | --- | --- | --- | --- |
| JSON data is currently served at `/cube/api/cubeJSON/:id`. | Yes, in official source | Yes, for one short ID | No | [JSON route](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/router/routes/cube/api/cubeJSON.ts), [router](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/router/router.ts) | Normalize accepted inputs to this endpoint inside the adapter; do not expose its payload to domain code. |
| A Cube UUID or `shortId` can resolve a cube. | Yes, in official source | Short ID only | UUID live behavior untested | [Cube data access](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/dynamo/dao/CubeDynamoDao.ts) | Treat both as provider identifiers and preserve the returned full ID. |
| Cards are organized into named board arrays. | Yes, in official source | Mainboard, maybeboard, and basics | Additional board semantics unknown | [Cube datatype](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Cube.ts) | Validate arrays; import only a human-approved board set and diagnose nonempty unsupported boards. |
| Duplicate array entries can represent duplicate cube memberships. | Arrays retain entries | Not tested | Cross-edit row identity is unavailable | [Cube datatype](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Cube.ts) | Create one local `CubeMembership` per occurrence; never deduplicate by printing or Oracle ID. |
| Nested Scryfall and Oracle IDs distinguish printing and Oracle identity. | Yes, in CardDetails type | Both present on one normal card | Completeness and custom-card behavior unknown | [Card datatype](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Card.ts) | Keep exact printing, Oracle identity, and membership separate; missing/inconsistent identity becomes a diagnostic. |
| Membership annotations and display overrides are present. | Yes, in Card type and CSV source | Some null/default values observed | Their durability is unknown | [Card datatype](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Card.ts), [CSV writer](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/serverutils/cube.ts) | Preserve raw provider values with provenance; do not promote them to canonical Scryfall facts. |
| Custom/voucher content can appear. | Yes, fields and CSV flags exist | Not tested | Resolution semantics are unknown | [Card datatype](https://github.com/dekkerglen/CubeCobra/blob/master/packages/utils/src/datatypes/Card.ts), [CSV writer](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/serverutils/cube.ts) | Return a structured unsupported/unresolved result in the baseline; never invent provider IDs. |
| The route limits requests and returns diagnosable HTTP statuses. | Yes, in route source | Successful response only | Infrastructure failures beyond source branches unknown | [JSON route](https://github.com/dekkerglen/CubeCobra/blob/master/packages/server/src/router/routes/cube/api/cubeJSON.ts) | Map `400`, `404`, `429`, and `5xx` separately; do not retry validation/not-found failures. |
| This shape is a stable public API contract. | No | Only one current response | No stability can be assumed | [official repository](https://github.com/dekkerglen/CubeCobra) | Keep the boundary fixture-driven and replaceable; additive fields may be ignored, required-field drift must fail visibly. |

## Measurements

The reconnaissance made one live cube-data request and zero broad listings,
HTML scrapes, authenticated requests, CSV exports, or history requests. That
response contained 360 mainboard occurrences and five basics entries. This is
shape reconnaissance, not availability or performance benchmarking.

## Limitations

The official repository reflects current implementation, not necessarily the
deployed revision at the instant of the GET. One public cube cannot establish
behavior for duplicates, custom cards, old data, arbitrary boards, alternate
page URLs, UUID lookup, failure responses, or longitudinal stability. No live
load, retry, cache, or rate-limit test was attempted.

## Risks

The largest risk is treating an unversioned implementation as a promised API.
Other material risks are collapsing duplicate memberships, conflating
CubeCobra `cardID` with a guaranteed Scryfall printing ID, silently importing
non-mainboard content, and assigning fabricated Oracle identities to custom or
unresolved cards. Any of those would violate CubeAI's provenance and identity
rules.

## Recommendation

Submit the following smallest plausible M1 contract for human acceptance in
M1-001/M1-005; this report does not accept it on their behalf:

1. Accept a raw CubeCobra UUID/short ID or an explicit allowlist of public
   `https://cubecobra.com/cube/<page>/<id>` URL forms. Reject other hosts,
   credentials, fragments, empty IDs, and ambiguous path shapes. The human
   contract should enumerate the accepted `<page>` values rather than accept
   arbitrary paths.
2. Fetch exactly one current JSON snapshot from
   `/cube/api/cubeJSON/<percent-encoded-id>` with bounded timeouts and response
   size. Do not use the historical `date` option, crawl, or authenticate in the
   M1 baseline.
3. Require a returned Cube full ID, name, and array-valued mainboard. Preserve
   `shortId`, `version`, `dateLastUpdated`, source URL, retrieval time, and raw
   board metadata as provider provenance. Treat `cardCount` as a consistency
   check, not as membership truth.
4. Import only `mainboard` for baseline draft membership. Report every nonempty
   maybeboard, basics, or custom board as an explicit skipped-board diagnostic
   until the product contract assigns semantics.
5. Create one local Cube membership per mainboard array occurrence, including
   duplicates. Use source `index` when valid and otherwise deterministic array
   order; local membership identity must not be derived solely from card IDs.
6. Offer `details.scryfall_id` as the exact-printing candidate, with set,
   collector number, language, and `details.oracle_id` as corroborating but
   distinct evidence. A human-approved resolution contract may use exact
   set/collector/language coordinates when the printing ID is absent. It must
   never silently fall back to fuzzy name matching.
7. Preserve tags, notes, status, finish, timestamps, and image/name overrides
   as source-attributed observations. Return structured per-card diagnostics
   for missing/malformed/conflicting identity, custom content, and vouchers;
   never create a fake Oracle or printing ID.
8. Map input, transport, HTTP, payload-shape, and per-card resolution failures
   to separate diagnosable errors. A `429` may be retried only with bounded
   backoff; `400`/`404` must not be retried automatically.

Contract tests should use small, sanitized checked-in fixtures for: one normal
cube, duplicate printings, empty/nonempty maybeboard and named boards, null
legacy metadata, a custom/unresolved row, conflicting IDs, and representative
`400`/`404`/`429`/`5xx` adapter responses. Assertions should prove duplicate
conservation, board order, identity separation, and diagnostic stability. The
parser should tolerate unknown additive fields but fail on missing or invalid
accepted-contract fields. An opt-in, low-frequency live smoke check may compare
the current route with fixtures; ordinary tests must remain offline. Fixture
updates should record the retrieval date and reviewed CubeCobra source revision
so upstream drift becomes an explicit human review rather than a silent parser
change.

## Roadmap/backlog impact

- **R-001:** evidence supports a public JSON adapter, while API stability,
  supported URL/page forms, boards, and custom-card policy remain open.
- **R-002:** exact printing candidates exist, but fallback precedence and
  unresolved/custom behavior still require the M1-005 human contract.
- **R-004:** the JSON route is more identity-preserving than CSV; CSV remains a
  fallback option only if the public JSON route proves unsuitable.
- **M1-001:** this evidence narrows the public-mainboard option, but a human
  must still approve the supported CubeCobra URL/ID, board, custom-card, and
  stability contract.
- **M1-002 / M1-003:** the evidence reinforces separate Cube, membership,
  printing, and Oracle identities and enumerates the candidate fields and
  diagnostics that the provider-neutral source port must retain.
- **M1-004:** URL parsing, bounded HTTP behavior, fixture mapping, and opt-in
  live drift detection belong in the CubeCobra adapter only after M1-001 is
  accepted.
- **M1-005 / M1-006:** printing fallback and unresolved/custom behavior remain
  part of the human-owned Scryfall policy and subsequent resolver contract.
- **M1-007 / M1-008:** no production slice or milestone acceptance should begin
  until M1-005 records the supported custom-card, board, and resolution policy.
