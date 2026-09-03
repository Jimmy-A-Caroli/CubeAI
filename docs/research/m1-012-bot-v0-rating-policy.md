# M1-012 Bot v0 rating-policy decision

**Status:** `REQUIRES HUMAN APPROVAL`

**Issue:** M1-012 — Define the bot port and Bot v0 rating policy

**Date:** 2026-09-03

## Decision requested

Approve or decline the conditional Bot v0 policy in this document. It does not
adopt a data source, license, dataset, provider integration, or domain
interface. M1-012 remains blocked until the two approvals below are recorded.

1. **Data rights:** May CubeAI use a CubeCobra public-export-derived ranking
   only after CubeCobra provides an explicit reusable-data license or written
   permission covering the intended local use and derived artifact?
2. **Deterministic fallback:** Is the proposed missing-rating score of `0.0`
   and ascending `DraftCardInstance.id` tie-break acceptable for Bot v0?

The recommendation is conditional because the available CubeCobra source-code
license does not establish rights to hosted/exported draft data.

## Bounded Bot v0 policy proposed for approval

If the data-rights decision is affirmative, Bot v0 would be named
`raw-ranking-v0` and would apply one approved, pinned rating snapshot as
follows:

| Concern | Proposed policy | Rationale |
|---|---|---|
| Strategy input | Current legal `DraftCardInstance`s in the acting bot's pack, their membership IDs, their approved Oracle-ID rating keys, and the declared strategy/snapshot identity. No `DraftState`, other seats' packs or pools, allocation seed, unopened packs, future order, or later events. | Keeps the strategy inside the existing seat-visible information boundary. |
| Rating identity | Look up one rating per Oracle ID. | Exact printing identities remain distinct for provenance, while one card rules identity has one declared raw ranking. |
| Duplicate memberships | Choose among distinct draft instances even when their Oracle IDs or printings match. | Membership and draft-instance identity must not be silently combined. |
| Missing rating | Assign `0.0` and emit `missing-rating-fallback`; do not fuzzy-match names or infer a score. | Every legal choice remains comparable and the data gap is diagnosable. |
| Ordering | Highest numeric rating first; equal scores choose the lowest stable `DraftCardInstance.id`. | Deterministic across replay without hidden state or randomization. |
| Decision meaning | A score represents observed CubeCobra pick-preference/ELO-like evidence from the declared derivation, not universal card power, human draft quality, or expected game performance. | Prevents an unsupported quality claim. |
| Overrides | Defer Cube-specific overrides. | Overrides need a separate authored-data, versioning, and provenance policy. |

The existing draft core already offers a narrow legal-card projection and
validates a chosen instance through its immutable pick transition. It must not
hand its complete runner state to a strategy. The current `PickEvent` has only
an opaque `strategy_ref`, so it cannot yet satisfy Bot v0's explanation
requirement. After approval, M1-012 must decide and test a typed decision
record (on the event or a linked immutable record) containing at least strategy
ID/version, source snapshot and derivation revision, checksum, rating lookup
outcome, numeric score or fallback, and tie-break reason. This document does
not preselect that data shape.

## Source candidates and evidence

| Candidate | License / rights evidence | Coverage and semantics | Versioning / cadence | Fit and disposition |
|---|---|---|---|---|
| CubeCobra public export with a derived `elos.json`-style ranking | CubeCobra's repository describes an ISC source-code license, but that does not expressly license hosted/exported data. CubeCobraML documents a public export, including Oracle mappings, cubes, picks, decks, and derived ELO output. | Cube-draft observations with Oracle-level mappings are the closest found fit for the selected cross-cube corpus. This remains pick-preference evidence, not card-power truth. | CubeCobraML documents quarterly export updates. A later approved use must pin export object/version, retrieval date, checksum, derivation code revision/configuration, and output checksum; never refresh during a draft. | **Conditional recommendation.** Do not use, copy, commit, scrape, or redistribute data until an explicit reusable-data license or permission is confirmed. |
| 17Lands public datasets | Its public-data page says datasets are normally CC BY 4.0, subject to stated exceptions. Its usage guidance prefers public datasets over scraping and warns that API stability is not guaranteed. | Arena Limited, expansion/event-specific observations. It lacks a justified cross-format normalization and will not cover many powered, older, or paper-only Cube cards. | Public datasets expose a last-updated value; a hypothetical future use would still pin URL, update value, retrieval date, and content checksum. | **Reject for Bot v0.** The rights posture is clearer, but the coverage and semantic mismatch would fabricate a universal cube ranking. |
| Scryfall / EDHREC-derived popularity | No new source was investigated or approved for rating reuse. Existing CubeAI policy limits Scryfall to exact printing metadata. | Metadata and Commander popularity are not Cube-draft raw rankings. | Not applicable. | **Reject.** Using either would expand policy and conflate unrelated signals. |

Primary evidence: [CubeCobraML export documentation](https://github.com/dekkerglen/CubeCobraML),
[CubeCobra source repository](https://github.com/dekkerglen/CubeCobra),
[17Lands public datasets](https://debug.17lands.com/public_datasets),
[17Lands usage guidance](https://www.17lands.com/usage_guidelines), and
[17Lands terms](https://www.17lands.com/terms_of_service).

## Required provenance and operational limits after approval

An approved implementation must keep the rating artifact outside the repository
unless its license explicitly permits inclusion. Each accepted snapshot must
record source location/identifier, source terms or permission reference,
retrieval timestamp, source and derived-artifact checksums, derivation revision
and configuration, and the Bot v0 strategy version. Updating ratings is a
separate deliberate snapshot operation, never a live provider call or implicit
mid-draft refresh.

The bot explanation for every decision must identify the same snapshot and
strategy version, the selected instance, Oracle-ID lookup result, score or
missing fallback, and the stable tie-break result. Tests after approval must
cover ordered scores, equal scores, missing ratings, duplicate names/printings,
input visibility, stable version/config serialization, and rejected illegal
choices.

## Dependency result and next action

M1-013 depends on M1-012; M1-014 depends on M1-013; M1-015 depends on
M1-013/M1-014; and the import/draft UI issues depend on M1-015. There is no
agent-safe Alpha-1 implementation to start without prematurely adopting this
policy or violating those dependencies.

**Checkpoint:** E — decision-ready M1-012 research complete; no source or
interface adopted.

**Next action:** Human records the two decisions above (including any written
CubeCobra permission/license). Only then can M1-012 be made ready and its
minimal bot-port/provenance implementation planned.
