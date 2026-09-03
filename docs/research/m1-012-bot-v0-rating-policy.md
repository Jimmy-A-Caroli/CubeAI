# M1-012 Bot v0 rating-policy decision

**Status:** `COMPLETE`

**Issue:** M1-012 — Define the bot port and Bot v0 rating policy

**Date:** 2026-09-03

## Accepted human decision

The human approved the Bot v0 behavior and the following durable data-rights
policy on 2026-09-03:

- Bot v0 is `raw-ranking-v0`, a transparent baseline card-strength prior. It
  is not human-like and does not model draft context, archetypes, synergy,
  signals, or human behavior.
- Ratings use Oracle-ID lookup; a missing rating has an explicit `0.0` value;
  equal ratings choose the ascending `DraftCardInstance.id`.
- Every bot decision must retain a strategy identifier and version together
  with rating-source/version provenance, selected instance, score, and any
  tie-break or missing-rating result required by the approved milestones.
- CubeCobra-derived rankings or datasets must not be incorporated, embedded,
  redistributed, or made a Bot v0 dependency unless CubeCobra gives explicit
  reusable-data licensing or written permission sufficient for the intended
  use. CubeCobra's software repository license and public CubeCobraML exports
  do not establish those data rights.
- CubeCobraML remains a high-priority future research candidate for
  context-rich draft evidence only after its data rights are resolved. 17Lands
  remains a methodological/future-environment candidate, not a Vintage Cube
  ranking substitute or Bot v0 dependency.

The human approved the first artifact class: a small, CubeAI-owned, versioned
curated artifact. The committed `cubeai-raw-ranking-v0@2026.09.03.1` JSON
artifact is intentionally limited to two synthetic acceptance-path Oracle IDs.
It is repository-authored, not a copy of a third-party dataset; all other
Oracle IDs receive the accepted `0.0` fallback. The accepted policy must not
be represented as approval to use CubeCobra, CubeCobraML, 17Lands, Scryfall,
EDHREC, or a newly invented third-party source.

## Accepted Bot v0 contract

Bot v0 applies the committed, pinned artifact snapshot as follows:

| Concern | Accepted policy | Rationale |
|---|---|---|
| Strategy input | Current legal `DraftCardInstance`s in the acting bot's pack, their membership IDs, their approved Oracle-ID rating keys, and the declared strategy/snapshot identity. No `DraftState`, other seats' packs or pools, allocation seed, unopened packs, future order, or later events. | Keeps the strategy inside the existing seat-visible information boundary. |
| Rating identity | Look up one rating per Oracle ID. | Exact printing identities remain distinct for provenance, while one card rules identity has one declared raw ranking. |
| Duplicate memberships | Choose among distinct draft instances even when their Oracle IDs or printings match. | Membership and draft-instance identity must not be silently combined. |
| Missing rating | Assign `0.0` and emit `missing-rating-fallback`; do not fuzzy-match names or infer a score. | Every legal choice remains comparable and the data gap is diagnosable. |
| Ordering | Highest numeric rating first; equal scores choose the lowest stable `DraftCardInstance.id`. | Deterministic across replay without hidden state or randomization. |
| Decision meaning | A score represents only the declared static card-strength prior, not universal card power, human draft quality, human-likeness, or expected game performance. | Prevents an unsupported quality claim. |
| Overrides | Defer Cube-specific overrides. | Overrides need a separate authored-data, versioning, and provenance policy. |

The existing draft core offers a narrow legal-card projection and validates a
chosen instance through its immutable pick transition. It must not hand its
complete runner state to a strategy. M1-012 adds the typed
`BotDecisionProvenance` record to every Bot-origin `PickEvent`, retaining
strategy ID/version, artifact ID/version, finite selected rating, lookup
outcome, and tie-break reason. External-source snapshots, derivation revisions,
and checksums remain deferred until a rights-cleared external artifact is
separately approved; the CubeAI-owned package-local artifact needs none.

## Source candidates and evidence

| Candidate | License / rights evidence | Coverage and semantics | Versioning / cadence | Fit and disposition |
|---|---|---|---|---|
| CubeAI-owned `cubeai-raw-ranking-v0` artifact | Repository-authored and CubeAI-owned; it contains no third-party rating dataset. | Two synthetic acceptance-path Oracle IDs; all other cards are intentionally unrated and receive `0.0`. It is a product baseline, not a representative Vintage Cube ranking. | Versioned JSON packaged with CubeLab. Changes require review and a new artifact version. | **Approved for Bot v0.** Small by design and replaceable without changing strategy logic. |
| CubeCobra public export with a derived `elos.json`-style ranking | CubeCobra's repository describes an ISC source-code license, but that does not expressly license hosted/exported data. CubeCobraML documents a public export, including Oracle mappings, cubes, picks, decks, and derived ELO output. | Cube-draft observations with Oracle-level mappings are a high-priority future research candidate. This remains pick-preference evidence, not card-power truth. | CubeCobraML documents quarterly export updates. A later rights-cleared proposal would pin export object/version, retrieval date, checksum, derivation code revision/configuration, and output checksum; never refresh during a draft. | **Not approved for use.** Do not use, copy, commit, scrape, redistribute, or make it a Bot v0 dependency until explicit reusable-data rights are confirmed. |
| 17Lands public datasets | Its public-data page says datasets are normally CC BY 4.0, subject to stated exceptions. Its usage guidance prefers public datasets over scraping and warns that API stability is not guaranteed. | Arena Limited, expansion/event-specific observations. It lacks a justified cross-format normalization and will not cover many powered, older, or paper-only Cube cards. | Public datasets expose a last-updated value; a future use would pin URL, update value, retrieval date, and content checksum. | **Not approved for Bot v0.** It remains a methodological and future-environment candidate, but is not a defensible direct Vintage Cube ranking. |
| Scryfall / EDHREC-derived popularity | No new source was investigated or approved for rating reuse. Existing CubeAI policy limits Scryfall to exact printing metadata. | Metadata and Commander popularity are not Cube-draft raw rankings. | Not applicable. | **Reject.** Using either would expand policy and conflate unrelated signals. |

Primary evidence: [CubeCobraML export documentation](https://github.com/dekkerglen/CubeCobraML),
[CubeCobra source repository](https://github.com/dekkerglen/CubeCobra),
[17Lands public datasets](https://debug.17lands.com/public_datasets),
[17Lands usage guidance](https://www.17lands.com/usage_guidelines), and
[17Lands terms](https://www.17lands.com/terms_of_service).

## Artifact provenance and operational limits

The first artifact is package-local at
`backend/src/cubeai/lab/resources/raw-ranking-v0.json`. It names its ID,
version, creation date, CubeAI ownership, basis, rights statement, coverage,
and Oracle-ID ratings. Future non-CubeAI artifacts must remain outside the
repository unless their rights explicitly permit inclusion. Every future
accepted snapshot must record source location/identifier, source terms or
permission reference, retrieval timestamp, source and derived-artifact
checksums, derivation revision and configuration, and the Bot v0 strategy
version. Updating ratings is a deliberate reviewed snapshot operation, never a
live provider call or implicit mid-draft refresh.

The bot explanation for every decision must identify the same snapshot and
strategy version, the selected instance, Oracle-ID lookup result, score or
missing fallback, and the stable tie-break result. Tests after rating-artifact approval must
cover ordered scores, equal scores, missing ratings, duplicate names/printings,
input visibility, stable version/config serialization, and rejected illegal
choices.

## Explicitly deferred

CubeCobra-derived raw ranking ingestion, CubeCobraML data ingestion,
human-like claims, contextual drafting, color/archetype/synergy reasoning,
learned models, ML, and human-annotation infrastructure are not part of Bot
v0 and are not authorized by this decision.

## Dependency result and next action

M1-013 depends on M1-012; M1-014 depends on M1-013; M1-015 depends on
M1-013/M1-014; and the import/draft UI issues depend on M1-015. There is no
agent-safe Alpha-1 implementation to start without prematurely adopting a
rating artifact or bot implementation, or violating those dependencies.

**Completion evidence:** `70d621f` — independently reviewed; focused Bot v0,
draft-vocabulary, and draft-state tests passed.

**Checkpoint:** E — policy accepted; rating artifact and pure Bot v0 strategy
port complete.

**Next action:** Implement M1-013 deterministic bot turns through the approved
visible-state port.
