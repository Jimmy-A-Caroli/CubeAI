# M1-005 Scryfall metadata and cache policy

**Status:** Accepted for M1 implementation by explicit human Alpha-0
authorization on 2026-09-03. M1-005 is complete and M1-006 is unblocked. The
accepted scope is exact Scryfall printing-ID resolution with a durable local
cache, network lookup only when a cache result is required, and explicit
unavailable/custom/unresolved outcomes. Automatic fuzzy/name fallback and
bulk-data-first architecture are prohibited. This document still introduces no
client, adapter, cache implementation, bulk download, or production fixture.

**Accessed:** 2026-09-03. The detailed evidence and calculations remain in
[Scryfall resolution reconnaissance](scryfall-resolution-reconnaissance.md).
This proposal refreshes the decision framing against the current official
documentation and a one-time metadata-shape observation. It is not legal
advice.

## Scope and evidence boundary

The review covers the M1-005 scope: official API and bulk guidance,
identifiers, headers, pacing, retry and cache expectations, offline behavior,
custom cards, images/attribution, and data-use implications. It did not
download a bulk archive, fetch card images, resolve a live card, copy provider
data into Git, or inspect a private Cube.

Primary sources consulted on the access date:

- [Scryfall API overview and data/image-use rules](https://scryfall.com/docs/api)
- [`POST /cards/collection`](https://scryfall.com/docs/api/cards/collection)
- [rate limits and caching guidance](https://scryfall.com/docs/api/rate-limits)
- [Card object fields](https://scryfall.com/docs/api/cards)
- [bulk data](https://scryfall.com/docs/api/bulk-data)
- [card imagery](https://scryfall.com/docs/api/images)
- [structured API errors](https://scryfall.com/docs/api/errors)
- [official API-access FAQ](https://scryfall.com/docs/faqs/i-m-having-trouble-accessing-the-scryfall-api-or-i-m-blocked-17)

The documentation pages themselves rejected the research browser's generic
fetch on this date. The official FAQ remained accessible in that browser, and
a one-time direct request to `https://api.scryfall.com/bulk-data` with a
descriptive `User-Agent` and `Accept` header succeeded. That observation
verified only the top-level list shape and the documented bulk-item fields
(`id`, `type`, `updated_at`, `compressed_size`, `jsonl_download_uri`, and
`uri`). It returned current offering types including `oracle_cards`,
`default_cards`, and `all_cards`; no download URI was followed and no response
data is committed here.

## Verified provider facts

| Topic | Verified fact | CubeAI consequence |
| --- | --- | --- |
| Request headers | Scryfall requires a meaningful `User-Agent` and `Accept`; its FAQ gives `Accept: application/json;q=0.9,*/*;q=0.8` as a suitable value. Collection `POST` also uses JSON content. | A future adapter must set these explicitly rather than accept HTTP-library defaults. |
| Exact batch lookup | `POST /cards/collection` accepts up to 75 identifiers. Missing identifiers move to `not_found`, so response positions cannot be used for correlation. | Batch only deduplicated provider references; map each returned or missing reference back to every original Cube membership by identifier, not list index. |
| Pacing and overload | Collection is documented at 2 requests/second; the general API guidance asks clients to stay below 10 requests/second. A `429` must cause the caller to reduce load rather than retry until success. | A provider-wide rate limiter belongs at the adapter boundary; M1 must not issue parallel per-card loops or hide repeated throttling. |
| Cache guidance | Scryfall asks clients to cache/process downloaded data locally for at least 24 hours. | A refresh policy may be more conservative, but must not cause more frequent upstream refreshes than this guidance. |
| Identity layers | A Card `id` identifies a Scryfall card object/printing; `oracle_id` is the rules identity shared across printings. Some reversible layouts put Oracle IDs on faces. | Preserve Scryfall printing ID and Oracle identity separately, retain face structure, and never turn a Cube membership into either provider identity. |
| Bulk data | The bulk list exposes types and dated download metadata; archives are daily JSON Lines gzip files. Oracle Cards selects one card per Oracle ID, while Default/All Cards represent printing-level data at different language coverage. | Read current manifest metadata when and only when a human-approved bulk option is implemented. Do not hard-code a URL, size, or timestamp, and do not use Oracle Cards for exact-printing preservation. |
| Images and attribution | Image URIs can be on a parent card or its faces. The use rules prohibit misleading presentation and require users to be able to identify artist/source for imagery. | M1 should retain source/image provenance but not mirror an image corpus. A UI decision must cover face images, artist/source presentation, and a source link. |
| Custom cards | The documented lookup API resolves records already in Scryfall; it does not define creation/upload of arbitrary custom cards. | Preserve custom/unavailable input as an explicit unresolved/custom result. Never manufacture an Oracle or Scryfall printing ID, or silently accept a same-name match. |

## Alternatives considered before acceptance

| Alternative | Benefits | Costs and risks | M1 suitability |
| --- | --- | --- | --- |
| Live collection requests only | Smallest implementation; exact Scryfall IDs can be resolved in batches; no local database/archive lifecycle. | No offline resolution; repeated imports repeat provider work; rate scheduling and multi-batch availability remain. | Viable only for a deliberately online local MVP with clear failure behavior. |
| Full bulk-data resolver | Local and offline-capable printing lookup after ingest; avoids repeated live lookups at scale. | A manifest, large download, gzip streaming, indexing, atomic refresh, disk budget, language contract, and data-use review are all required. | Too much scope for the smallest M1 path unless offline-first operation is a product requirement. |
| Hybrid exact-ID live resolver with durable local cache | Makes only cache misses live, supports offline reuse of previously resolved cards, preserves exact-printing references, and avoids mandatory archive ingest. | Still needs cache storage, freshness rules, provider pacing, snapshot provenance, and an explicit stale/offline rule. | **Accepted** as the smallest responsible M1 option. Bulk remains a later implementation behind the same resolver boundary. |

## Accepted M1 policy

The following is the accepted implementation direction. It is not current
repository behavior until M1-006 implements it.

1. **Resolution input and precedence.** Accept an exact Scryfall Card UUID as
   the only automatic M1 printing-resolution key. A CubeCobra-provided exact
   ID may be validated against set/collector/language/Oracle hints, but a
   disagreement yields a diagnostic rather than replacement. Do not choose a
   printing from `oracle_id`, name, fuzzy name, or set/collector fallback
   automatically. Those possible fallbacks are outside the accepted M1 scope.
2. **Live client behavior.** Use HTTPS and one shared adapter-level scheduler.
   Send `User-Agent: CubeAI/<version> (<maintainer contact or repository URL>)`,
   `Accept: application/json;q=0.9,*/*;q=0.8`, and
   `Content-Type: application/json` for collection requests. Deduplicate exact
   IDs only for lookup, chunk at 75, and start collection requests at least
   500 ms apart. Each transport attempt has a proposed 10-second timeout.
3. **Failures and retries.** Validate identifiers before the request. Return
   structured `invalid_reference`, `not_found`, `custom_or_unresolved`,
   `provider_rate_limited`, `provider_unavailable`, `network_failure`, or
   `provider_contract_failure` outcomes; never leak provider exceptions.
   Do not retry invalid input or a resolved `not_found`. On `429`, stop new
   work for at least 30 seconds and return a rate-limited result; do not retry
   automatically. At most one retry after a bounded delay is proposed for a
   connection failure or `5xx`, provided the scheduler still permits it.
4. **Cache record and freshness.** Key the cache by the exact Scryfall Card
   UUID. Store the provider name, provider printing ID, Oracle ID or explicit
   face-level Oracle IDs, set, collector number, language, layout, necessary
   card/face display fields, image URIs, original lookup reference,
   `fetched_at`, and a response/schema version. Use an injectable clock. A
   fresh record is reusable without a network request for at least 24 hours;
   later refresh replaces only the cache record, never an existing CubeVersion
   snapshot.
5. **Offline behavior.** An explicit offline mode performs no network I/O. It
   returns cached records with freshness status where available and structured
   unavailable results for misses. It does not reinterpret an unresolved card
   as a different printing. The application layer—not the adapter—later owns
   whether unresolved cards prevent CubeVersion creation.
6. **Snapshot and provenance.** For an import, retain the resolution retrieval
   window, cache-record references, provider identifiers, and outcome
   diagnostics in a resolution snapshot. Freeze that snapshot into the
   immutable CubeVersion path so a later refresh cannot rewrite draft inputs.
   Cube membership identity remains separate even when duplicate memberships
   resolve to one printing.
7. **Images and data boundary.** Store validated provider image URIs and
   face structure only; do not download or mirror images in M1. A future UI
   presents an accessible provider/source link and artist/copyright information
   where image rules require it, without claiming Scryfall endorsement. Do not
   redistribute a bulk dataset or treat the public API as an unrestricted data
   license without legal/product review.
8. **Later bulk option.** If approved later, retrieve the current bulk manifest
   no more often than allowed by provider guidance, select a human-approved
   offering/language scope, stream JSONL gzip, record manifest ID/type/
   `updated_at`, and atomically replace a local derived index. The proposed M1
   baseline does not download a bulk archive.

## Offline validation prepared by this research

[`scryfall-metadata-examples.json`](../../fixtures/synthetic/scryfall-metadata-examples.json)
is CubeAI-authored synthetic data, not a Scryfall response. It exercises the
documented collection request envelope and a minimal bulk-list/bulk-item shape
without an API call or provider card data. Its focused offline test validates:

- exact UUID identifier examples, the `identifiers` envelope, and the 75-item
  batch ceiling;
- that bulk-list and bulk-item discriminators/required fields are present;
- parseable `updated_at`, non-negative compressed size, and HTTPS metadata
  URIs; and
- explicit CubeAI-authored/MIT provenance and absence of secret-like JSON keys
  through the existing fixture-policy scan.

This is documentation-contract preparation, not an adapter conformance suite.
The eventual M1-006 implementation must add reviewed, sanitized provider
fixtures and fake-HTTP tests for 1/75/76 identifiers, duplicate memberships,
mixed `not_found`, set/collector conflicts, language policy, multi-face cards,
images, custom records, cache freshness, `400`, `404`, `429`, `5xx`, and
network failures.

## Deferred product and legal questions

The acceptance above is sufficient for M1-006. It does not decide future
image presentation, attribution UX, legal compatibility conclusions, expanded
language coverage, automatic set/collector or Oracle/name fallback, or a
threshold for bulk-data adoption. Those are explicitly deferred and must not
block or broaden the exact-ID M1 resolver.
