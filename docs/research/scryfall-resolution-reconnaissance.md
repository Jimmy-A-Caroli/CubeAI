# Scryfall resolution reconnaissance

Accessed 2026-08-30. This report uses only Scryfall's official API
documentation. It did not call a Scryfall API method, download a bulk archive,
or fetch card images.

## Question

What is the smallest plausible M1 Scryfall resolution contract that preserves
Oracle and printing identities, resolves CubeCobra-sized imports within current
request expectations, supports deterministic local snapshots, and treats
images, attribution, bulk data, and custom cards safely?

## Methodology

The review inspected these official Scryfall pages:

- [API overview, required headers, and data/image-use rules](https://scryfall.com/docs/api)
- [`POST /cards/collection`](https://scryfall.com/docs/api/cards/collection)
- [API rate limits and cache expectations](https://scryfall.com/docs/api/rate-limits)
- [Card objects](https://scryfall.com/docs/api/cards)
- [Card imagery](https://scryfall.com/docs/api/images)
- [daily bulk data](https://scryfall.com/docs/api/bulk-data)
- [structured API errors](https://scryfall.com/docs/api/errors)

Request counts were calculated for 360-, 540-, and 720-card cubes using the
documented 75-identifiers-per-collection-request limit. Counts intentionally
assume every membership references a different printing; deduplicating exact
provider references may reduce real traffic without collapsing Cube
memberships.

## Documented behavior

### Requests, batching, and failures

The API is served over HTTPS with TLS 1.2 or better and UTF-8 responses. Every
request must contain an accurate application `User-Agent` and an `Accept`
header. `POST /cards/collection` additionally requires
`Content-Type: application/json`, accepts at most 75 card references per
request, and is currently limited to 2 requests per second with 500 ms spacing.

Collection identifiers may use Scryfall `id`, `mtgo_id`, `multiverse_id`,
`oracle_id`, `illustration_id`, `name`, set plus name, or set plus
`collector_number`. Each identifier returns at most one card. An `oracle_id`
lookup returns a newest edition, so it cannot preserve an already-selected
printing. Set and collector number are accepted together, but `lang` is not a
documented collection identifier field; exact foreign-language resolution
therefore requires an exact Scryfall `id` or a separately accepted lookup path.

Returned cards retain request order, but unresolved identifiers are moved to
the response's `not_found` array. Scryfall explicitly warns that this makes
positional correlation unsafe. An adapter must match returned identities and
`not_found` entries back to its request records rather than zip arrays by
index.

Current limits are 2/second for search, named, random, and collection;
10/minute for the manifest; and 10/second for other API methods. Direct file
origins under `*.scryfall.io` are not API-rate-limited. A `429` limits access
for 30 seconds; ignoring it or continuing to overload the service can cause a
temporary or permanent block. Scryfall asks clients to cache/process downloaded
data locally for at least 24 hours and requires bulk data for rapid resolution
of large numbers of names, prices, or card images.

### Oracle identity, printing identity, and updates

A Card object's `id` is a unique Scryfall database UUID for that card object.
Its printing-level fields include `set`, string-valued `collector_number`,
`lang`, and `released_at`. For CubeAI, that UUID is the provider's exact
printing reference; it is not a Cube membership identity.

`oracle_id` is consistent across reprinted editions and distinguishes different
cards that happen to share a name. It is therefore the provider evidence for a
CubeAI Oracle identity, not for a printing. The documented exception is the
`reversible_card` layout: the parent may omit `oracle_id`, with Oracle IDs on
the faces instead. Multi-face layouts are represented by one parent Card
object and a `card_faces` array; they must not be split into independent Cube
memberships merely because faces contain fields.

The Card object documents `released_at`, which is a release date, but no
per-card last-updated timestamp. A live-resolution snapshot must record a
CubeAI-controlled retrieval time. Bulk metadata does expose `updated_at`, and
bulk download URLs change their timestamp each day. Gameplay data changes less
frequently than price data; Scryfall says gameplay-only refreshes once a week
or after releases are most likely sufficient, while prices are updated daily
and should be considered stale after 24 hours.

### Bulk data offerings

Scryfall provides daily gzipped JSON Lines (`.jsonl.gz`) archives. They can be
streamed without loading the entire decompressed file into memory. The current
bulk-data object exposes a unique ID/type, `updated_at`, `jsonl_download_uri`,
and `compressed_size`.

The official bulk page listed these card-relevant offerings on the access date:

| Offering | Current compressed size | Current update shown | Resolution suitability |
| --- | ---: | --- | --- |
| Oracle Cards | 23.4 MB | 2026-08-30 09:01 UTC | One chosen Card per Oracle ID; insufficient to preserve an arbitrary exact printing. |
| Unique Artwork | 35.9 MB | 2026-08-30 09:02 UTC | Artwork coverage, not complete printing resolution. |
| Default Cards | 74.4 MB | 2026-08-30 09:05 UTC | Every card in English, or its printed language when only one language exists; the smallest plausible bulk source for common printing resolution. |
| All Cards | 374 MB | 2026-08-30 09:17 UTC | Every card in every language; needed only if the accepted contract requires complete language coverage. |
| Rulings | 5.12 MB | 2026-08-30 09:00 UTC | Rulings keyed to `oracle_id`; not a printing-resolution dataset. |

These are a dated observation of the official listing, not capacity constants.
An implementation must read current manifest metadata rather than embed sizes,
timestamps, or download URLs. This reconnaissance did not download any archive.

### Images and usage rules

Card objects expose `image_uris`; double-sided cards can instead expose
`image_uris` on each Card Face. Image availability and quality can vary, and
`art_crop` is not guaranteed to be perfect. The API provides standard image
variants and redirects to the image file origins; the Card response does not
embed image bytes.

Scryfall allows its card data and image database for additional Magic software,
research, and community content under the stated rules. A consumer must not
imply Scryfall endorsement, paywall access to Scryfall data, use the data to
create a different game, or merely repackage/proxy it without adding value.
Card images must not have copyright/artist information clipped, be distorted or
color-altered, receive added watermarks, or be presented as another creator's
work. If `art_crop` is used, the same interface must expose artist/copyright or
a full card image so users can identify artist and source.

The overview does not prescribe one universal text attribution string. A
visible source link and retained provider provenance are a conservative CubeAI
product recommendation, not a quoted Scryfall requirement; UI/legal acceptance
remains human-owned.

### Custom cards and unresolved references

The collection endpoint resolves identifiers to Card objects present in
Scryfall and returns misses in `not_found`. The official docs do not describe
an API for uploading or creating arbitrary custom cards. It follows that a
CubeCobra custom card without a resolvable Scryfall record cannot acquire a
Scryfall printing or Oracle ID through this boundary. CubeAI must retain the
source observation separately or return a structured unresolved/custom
diagnostic; it must not manufacture an ID or resolve by same-name guesswork.

## Observed behavior

No live API response was observed. The only observed dynamic provider state was
the official bulk-data page's dated 2026-08-30 archive listing, with the sizes
and timestamps in the table above. Collection limits and endpoint-specific rate
limits are documented behavior, not runtime observations. This reconnaissance
is not an availability, latency, or response-shape measurement.

## Assumptions and unknowns

- CubeCobra's `details.scryfall_id` is expected to be an exact Scryfall Card
  `id` for normal cards, but Scryfall documentation cannot establish the
  correctness of another provider's payload.
- Whether M1 accepts set/collector fallback, language fallback, Oracle-only
  lookup, or name lookup is a human-owned M1-005 decision. Exact Scryfall ID is
  the least ambiguous baseline.
- The API docs do not provide a per-card update timestamp or a transactional
  consistency guarantee across multiple collection batches. One import should
  therefore record its own retrieval window and freeze resolved responses into
  a local snapshot.
- A 24-hour cache is the documented minimum expectation, not a guarantee that
  every field remains unchanged for exactly that duration.
- Bulk `Default Cards` appears sufficient for common English printing IDs, but
  accepted language requirements determine whether `All Cards` is necessary.
- Image URL durability and offline image-mirroring policy are not specified as
  an M1 requirement. The smallest contract can retain validated provider URIs
  and render on demand without downloading a local image corpus.
- Custom-card storage and whether one unresolved occurrence rejects an entire
  import are product/domain decisions. The adapter can report complete
  diagnostics without silently creating a partially valid Cube.

## Evidence classification

| Claim | Documented | Observed | Assumption | Source | M1 contract impact |
| --- | --- | --- | --- | --- | --- |
| A collection request accepts at most 75 identifiers and runs at 2/second. | Yes | No live response | No | [`POST /cards/collection`](https://scryfall.com/docs/api/cards/collection), [rate limits](https://scryfall.com/docs/api/rate-limits) | Batch exact IDs into at most 75, schedule starts at least 500 ms apart, and cache results. |
| Missing collection entries appear in `not_found` and disrupt positional mapping. | Yes | No live response | No | [`POST /cards/collection`](https://scryfall.com/docs/api/cards/collection) | Correlate by requested/returned identities; never zip request and result arrays. |
| Card `id` and `oracle_id` represent different identity layers. | Yes | No live response | Mapping to CubeAI terminology is architectural | [Card objects](https://scryfall.com/docs/api/cards) | Store provider printing ID separately from Oracle identity and membership. |
| `oracle_id` lookup preserves the caller's selected printing. | No; it returns a newest edition | No live response | No | [`POST /cards/collection`](https://scryfall.com/docs/api/cards/collection) | Do not use Oracle lookup as exact-printing resolution. |
| Live Card objects include a last-updated timestamp. | No such Card field is documented | No live response | Absence may change later | [Card objects](https://scryfall.com/docs/api/cards) | Record adapter `fetched_at`; do not mislabel `released_at` as update time. |
| Bulk items publish daily download metadata including `updated_at`. | Yes | Current dated listing observed | Future size is unknown | [bulk data](https://scryfall.com/docs/api/bulk-data) | Record manifest identity/update time with a bulk-derived snapshot; never hard-code dated URLs. |
| Parent or face-level `image_uris` locate imagery. | Yes | No image fetched | URL longevity unknown | [Card objects](https://scryfall.com/docs/api/cards), [card imagery](https://scryfall.com/docs/api/images) | Preserve face structure and source URI; avoid modifying or ambiguously attributing imagery. |
| Arbitrary custom cards can be created through the API. | No such operation is documented | Not tested | Treat as unsupported unless official docs add a contract | [`POST /cards/collection`](https://scryfall.com/docs/api/cards/collection), [Card objects](https://scryfall.com/docs/api/cards) | Return unresolved/custom diagnostics and never fabricate Scryfall/Oracle IDs. |
| A universal “Powered by Scryfall” label is required. | No universal wording is documented | Not applicable | A visible source link is a conservative recommendation | [API data/image-use rules](https://scryfall.com/docs/api) | Human review should approve UI attribution and image presentation before M1 acceptance. |

## Measurements

For a collection limit of 75, the worst-case request counts are:

| Cube memberships | Collection batches, `ceil(n / 75)` | Individual lookup upper bound | Minimum collection start-to-start span, excluding network |
| ---: | ---: | ---: | ---: |
| 360 | 5 | 360 | 2.0 seconds between first and fifth start |
| 540 | 8 | 540 | 3.5 seconds between first and eighth start |
| 720 | 10 | 720 | 4.5 seconds between first and tenth start |

The individual upper bound is the request count if every membership is unique
and no collection batching or cache is used. Exact `/cards/:id` calls fall
under the documented “other methods” 10/second category, but name-based calls
use the slower 2/second named endpoint. These spans are scheduling lower bounds,
not latency promises. Deduplicating identical resolution references before
lookup reduces provider requests while mapping the one resolved printing back
to every distinct Cube membership.

### Live, bulk, and hybrid comparison

| Strategy | First import | Repeat import | Offline operation | Staleness evidence | Disk | Implementation complexity |
| --- | --- | --- | --- | --- | --- | --- |
| Live collection | 5/8/10 calls for 360/540/720 unique references | Same calls again without a cache | Unavailable | Local `fetched_at`; no per-card upstream update time | Only current process/snapshot data | Lowest parser/storage surface; availability, multi-batch drift, and rate scheduling remain. |
| Bulk | Download and stream Default Cards, or All Cards for every language | Local lookup until the next refresh | Full printing lookup from the retained archive/index | Manifest `updated_at` and daily URL | At least 74.4 MB compressed for Default Cards or 374 MB for All Cards on the access date, plus index/storage | Highest: manifest refresh, gzip/JSONL streaming, indexing, atomic snapshot replacement, and language scope. Oracle Cards cannot preserve arbitrary printings. |
| Hybrid live plus durable cache | Bounded collection calls only for unique cache misses | Local hits; live calls only for missing/stale entries | Cached subset only | `fetched_at` per cached record/snapshot; optional later manifest comparison | Proportional to resolved subset; no mandatory bulk archive | Moderate: adds cache keys/TTL/snapshot freezing while avoiding bulk ingestion and reducing provider load. |

## Limitations

This is documentation reconnaissance, not an API conformance test. No live
cards, errors, images, manifests, or bulk records were retrieved. Current bulk
sizes change as Scryfall grows, and documented limits/policies can change. The
request calculation does not model latency, retries, cache hits, duplicate
printing references, or CubeCobra identity errors.

## Risks

Material risks are resolving an Oracle ID to a newer but incorrect printing,
using response position after a `not_found` entry, treating `released_at` as an
update timestamp, splitting multi-face cards into memberships, hiding custom
cards behind a same-name match, or exceeding request expectations during bulk
resolution. Image presentation can also violate the documented rules even when
data resolution itself is correct.

## Recommendation

Submit a **hybrid exact-ID collection resolver with a durable local cache** as
the smallest plausible M1 option for human acceptance in M1-005. This report
does not make that decision on the issue owner's behalf:

1. Accept exact Scryfall Card UUIDs as the baseline resolution input. Batch
   unique IDs in groups of at most 75 while retaining a deterministic mapping
   from each request ID to all source memberships. Do not use Oracle or name
   lookup to choose a printing.
2. Send accurate `User-Agent`, `Accept`, and JSON content headers; start
   collection requests at least 500 ms apart. Apply bounded timeouts and stop on
   `429`, honoring at least the documented 30-second limitation before any
   bounded retry. Do not retry malformed or definitively unresolved inputs.
3. Correlate by returned Scryfall ID and `not_found` identifiers, not position.
   Validate any CubeCobra set/collector/language/Oracle evidence against the
   returned Card and emit a conflict diagnostic rather than silently replacing
   source evidence.
4. Persist a resolution snapshot/cache containing provider Card ID, Oracle ID
   (including face exceptions), printing coordinates, required gameplay/display
   fields, image URIs, `fetched_at`, source, and the original provider reference.
   Make the clock injectable. Retain distinct Cube memberships outside this
   cache.
5. Reuse cached provider records for at least 24 hours. Any human-approved
   cache/freshness decision must be equally or more conservative toward
   Scryfall, such as longer reuse or less frequent refresh; it must never cause
   upstream refresh more often than the documented expectation. Freeze one
   import to the responses gathered in its bounded retrieval window so later
   refreshes cannot rewrite an already-started draft.
6. Return a complete structured result for invalid IDs, `not_found`, ID/printing
   conflicts, reversible-card Oracle identity, missing images, transport/API
   errors, and custom cards. The application layer must apply the human-owned
   all-or-nothing or unresolved-card admission rule; the adapter must not
   construct silently partial domain objects.
7. Store image URIs and face structure without pre-downloading a corpus in M1.
   UI acceptance must preserve full-card copyright/artist information, handle
   face-level images, follow the official image-use rules, and expose a clear
   provider/source link without implying endorsement.
8. Keep a bulk resolver behind the same adapter boundary as a later/offline
   option. If accepted, read the current bulk manifest, stream JSONL gzip, pin
   the manifest type and `updated_at` in the snapshot, and select Default versus
   All Cards from an explicit language contract. Do not adopt Oracle Cards for
   exact-printing resolution.

Contract tests should use small checked-in official-shape fixtures, free of
credentials and private data, for: 1/75/76 identifiers; mixed identifier order
with `not_found`; duplicate references mapped to multiple memberships; printing
versus Oracle IDs; set/collector mismatch; foreign language; reversible and
multi-face cards; absent parent/face images; custom/unresolved input; and
structured `400`, `404`, `429`, and `5xx` errors. Cache tests need an injected
clock at just before/after the accepted TTL. A tiny synthetic bulk-manifest and
JSONL fixture can verify streaming without checking in or downloading a large
archive. Ordinary tests must remain offline; an opt-in smoke test may resolve a
single durable ID with the required headers and conservative pacing. Changes to
required fields, limits, attribution rules, or fixture shape should trigger a
human-reviewed contract update rather than a permissive fallback.

## Roadmap/backlog impact

- **R-001:** Scryfall's official contract is documented, but CubeCobra's
  printing evidence still needs adapter validation before it is trusted.
- **R-002:** exact-ID collection plus a local cache is the smallest measured
  option; set/collector/language fallback, custom cards, and bulk scope remain
  human decisions for M1-005.
- **R-004:** the 5/8/10 collection-batch counts make live resolution plausible
  for M1 cube sizes without adopting a 74-374 MB bulk dependency immediately.
- **M1-002:** the documented identities reinforce separate Oracle,
  CardPrinting, CubeMembership, and draft-instance models.
- **M1-005:** remains human-owned. It must accept exact supported identifiers,
  fallback precedence, cache freshness, unresolved/custom admission, language,
  image use, and attribution before implementation.
- **M1-006 / M1-007 / M1-008:** adapter fixtures and diagnostics can follow the
  accepted contract, but no production slice or milestone acceptance should
  precede that decision.
