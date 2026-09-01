# Reference Cube Corpus Discovery

Accessed 2026-09-01. This bounded discovery identifies real public Cubes that
should keep future CubeCobra contract work grounded. It is evidence for
M1-001, not a supported import contract, fixture set, or domain-model decision.

## Executive conclusion

The proposed corpus is **sufficient for the next M1-001 discovery phase**:
nine CubeCobra representations cover a conventional 432--540-card mainboard,
nonempty `maybeboard` and `basics` arrays, duplicate memberships, membership
tags and notes, non-default finishes, image fields, and optional/sparse source
fields. It combines the MTGO Vintage Cube anchor with eight CubeCon 2026
entries. None of the nine needs a special draft/game rule to explain its
observed source shape.

The corpus does *not* establish custom-card, voucher, unresolved-identity,
historical-snapshot, private-source, or pick-history behavior. No selected
mainboard row lacked its observed nested Scryfall or Oracle identifier, so
those cases remain `UNKNOWN`, not implicitly supported. M0-008 must define the
sanitized fixture policy before M1-001 turns these observations into fixtures.

Sources examined were the [CubeCon 2026 roster](https://cubecon.org/cubes/2026),
the public CubeCobra JSON representation for the selected examples, and the
repository's [CubeCobra reconnaissance](cubecobra-reconnaissance.md). The
existing reconnaissance supplies the official-source route analysis; this
report adds a deliberately diverse real-cube population.

## Selection methodology

- **CORE** means a Cube is suitable to shape the first general-purpose import
  model. Its card environment can be unusual, but its observed representation
  is an ordinary CubeCobra cube with a usable `mainboard`.
- **EDGE** means a Cube is still a legitimate early contract test but adds a
  structural variation that should be handled visibly rather than become the
  default assumption.
- **STRESS** means a source or format challenges draft rules, visibility, or
  data-validity assumptions. It is retained for later investigation, not used
  to define the first model.

Selection favors a new observed structural case over popularity. CubeCon tags
are recorded as event classifications, not as CubeAI facts about card power,
archetypes, or intended gameplay.

## Population overview

The rendered CubeCon 2026 roster had **70 CubeCobra-linked entries** on the
access date. This was a shallow pass: each roster entry was counted once even
though the page displays separate image and title links. CubeCon displayed the
following nonexclusive event-tag counts:

| Event tag | Entries |
|---|---:|
| Mechanics Focused | 26 |
| Thematic | 17 |
| Eternal | 12 |
| Color Restricted | 11 |
| Format Themed | 11 |
| Desert | 8 |
| Rarity Restricted | 3 |
| Powered | 2 |
| No displayed event tag | 11 |

The roster is structurally diverse enough to avoid using several near-identical
powered Cubes as the whole sample. It also includes deliberately narrow,
thematic, and mechanics-led formats; those are useful signals for the stress
watchlist, not a reason to broaden the initial general-purpose model.

## Proposed reference corpus

The CubeCobra facts below are live observations from one current JSON response
per listed source. `mainboard`, `maybeboard`, and `basics` are response-array
lengths; duplicate counts are repeated `cardID` values *within mainboard*.

| Cube | Source and broad category | Tier | Why selected | Observed structural contribution | Caveat |
|---|---|---|---|---|---|
| MTGO Vintage Cube | [CubeCobra `modovintage`](https://cubecobra.com/cube/api/cubeJSON/modovintage); conventional powered anchor | CORE | High-profile baseline outside the CubeCon population. | 540 mainboard, 0 maybeboard, 5 basics; public full and short IDs; 30 tagged memberships; no duplicate `cardID` values. | Current list/version is a snapshot, not an official MTGO publication or stable CubeCobra contract. |
| Good Clean Magic | [CubeCobra `GoodCleanMagic`](https://cubecobra.com/cube/api/cubeJSON/7ee389d9-61c7-45ab-9078-97ebfe2e9d9a); CubeCon entry with no displayed event tag | CORE | Conventional 450-card contrast to the MTGO anchor. | 450 mainboard, 66 maybeboard, 5 basics; no duplicate `cardID`; no tagged mainboard rows; 11 non-default finishes. | Absence of an event tag is not evidence of an unrestricted design. |
| The Peasant+ Cube | [CubeCobra `airbornemoxen`](https://cubecobra.com/cube/api/cubeJSON/airbornemoxen); CubeCon Rarity Restricted | CORE | Shows a restriction can remain structurally ordinary. | 450 mainboard, 0 maybeboard, 5 basics; 107 tagged memberships; no duplicate `cardID`. | Rarity restriction is a CubeCon classification, not a CubeAI validation rule. |
| Sammich's Peasant Cube | [CubeCobra `sammich_peasant`](https://cubecobra.com/cube/api/cubeJSON/sammich_peasant); CubeCon Rarity Restricted / Mechanics Focused | CORE | Metadata-rich standard-list representation. | 450 mainboard, 186 maybeboard, 5 basics; 437 tagged rows and 438 non-default finishes; no duplicate `cardID`. | Tags and finish are provider membership data, not inferred archetype or card-quality data. |
| aquaone powered | [CubeCobra `aquaone`](https://cubecobra.com/cube/api/cubeJSON/5fc9e578bada5f7f15feb582); CubeCon Powered | EDGE | Combines conventional drafting content with dense membership annotation. | 432 mainboard, 187 maybeboard, 11 basics; 3 duplicate `cardID`; 404 tagged rows, 76 notes, and 251 image fields. | Image fields are source display values; their semantics and licensing are outside this discovery. |
| HeatherCube | [CubeCobra `HeatherCube`](https://cubecobra.com/cube/api/cubeJSON/6c078fb9-5559-4296-a57b-5d86ed19ae90); CubeCon entry with no displayed event tag | EDGE | Exercises duplicates plus a sparse outer membership field set. | 450 mainboard, 12 maybeboard, 5 basics; 20 duplicate `cardID`; its outer card rows omit several convenience fields present in other examples. | The nested identity fields were present in this snapshot; missing-field behavior is still untested. |
| Hackett Cube | [CubeCobra `sd4`](https://cubecobra.com/cube/api/cubeJSON/5fca9a5abada5f7f150c8c2e); CubeCon entry with no displayed event tag | EDGE | Concentrates duplicates, annotations, finish, and image values in one normal-sized cube. | 540 mainboard, 0 maybeboard, 5 basics; 15 duplicate `cardID`; 91 tagged rows, 36 non-default finishes, 23 image fields. | Do not assume a nonempty image field represents a custom card. |
| Old Border Foil Cube 450 | [CubeCobra `obf450`](https://cubecobra.com/cube/api/cubeJSON/203c4a53-1a5c-47dc-8752-9a6886a51905); CubeCon Format Themed | EDGE | Tests printing/finish-heavy source evidence without special draft rules. | 450 mainboard, 160 maybeboard, 5 basics; 239 non-default finishes; 18 tagged rows; no duplicate `cardID`. | A finish is neither a rules identity nor a reason to choose a different Oracle identity. |
| game zones cube | [CubeCobra `gamezones`](https://cubecobra.com/cube/api/cubeJSON/acf0bb88-6a3d-4990-af63-026e8e5f3caf); CubeCon Mechanics Focused / Thematic | EDGE | Adds a 500-card list with substantial duplicate membership and nondefault finish use while remaining a normal card list. | 500 mainboard, 84 maybeboard, 6 basics; 30 duplicate `cardID`; 9 tagged rows, 1 note, 441 non-default finishes. | Its curator describes a synergy environment; that claim must not become an imported CubeAI archetype. |

## Stress-case watchlist

These sources are valuable later, but should not decide the first
general-purpose contract.

| Cube | Why it is excluded now | Assumption it challenges |
|---|---|---|
| Fifteen Card Highlander ([`fus`](https://cubecobra.com/cube/api/cubeJSON/5ee84f3e7c9901100bc212d1)) | Its curator-declared formats use two ten-card packs, an exact fifteen-card deck, and a stated exception to normal empty-library loss. | Standard M1 8/3/15 draft geometry and ordinary game assumptions. |
| 1UP Cube, Convention Edition ([`1upconvention`](https://cubecobra.com/cube/api/cubeJSON/81a7639f-fe0f-4ad2-9bbd-2f3dc35cf484)) | The accessible response reports `visibility: "un"` rather than `"pu"`. | Whether a known unlisted source is ever accepted by a deliberately public-only M1 import contract. |
| Curated by Kiwi ([full ID](https://cubecobra.com/cube/api/cubeJSON/73dc76ca-f2c1-4020-903c-d8e3bf624e60)) | The response reports one mainboard card and an empty `shortId`, despite being listed by CubeCon. | Import input validation: a reachable source is not necessarily a draftable cube, and short IDs cannot be assumed nonempty. |

## CubeCobra observations

### Confirmed observations in this sample

1. Every inspected response provided a full `id`; user-facing `shortId` values
   also appeared, but one stress response had an empty short ID.
2. The selected responses represent card collections as a `cards` object with
   array-valued `mainboard`, `maybeboard`, and `basics` entries. `cardCount`
   equaled the observed mainboard length in all twelve inspected responses.
3. Duplicate `cardID` values occur in real mainboards (3 in aquaone, 20 in
   HeatherCube, 15 in Hackett Cube, and 30 in game zones cube). Each occurrence
   must remain a distinct Cube membership.
4. Every inspected selected mainboard row had both `details.scryfall_id` and
   `details.oracle_id`. Those IDs are different identity evidence and must not
   be collapsed merely because both were present in this sample.
5. Membership-level fields varied substantially: tags, notes, status, finish,
   and image fields could be present, empty, or omitted. HeatherCube's outer
   rows were notably sparser than those of several other selected Cubes.
6. The inspected cube-level fields varied too (for example `brief`,
   `categoryPrefixes`, and draft-format settings). `version` and
   `dateLastUpdated` are useful snapshot provenance candidates, not a promised
   history/version contract.
7. Fifteen Card Highlander exposed source format configuration; no inspected
   JSON response exposed pick events or draft-history records. This does *not*
   prove that CubeCobra has no other draft/pick surfaces.

### Uncertain or deliberately untested

- No selected mainboard exercised a missing Scryfall ID, missing Oracle ID,
  custom name, voucher relationship, or unresolved card. Their real-world
  import representation remains `UNKNOWN` here.
- The selected data used only `mainboard`, `maybeboard`, and `basics`; semantics
  of other named boards remain unestablished.
- The public JSON route may expose a current snapshot, but this discovery did
  not test historical `date` imports, errors, rate limiting, UUID/short-ID
  longevity, private cubes, or unlisted access policy.
- Pick/deck counts or curator format settings are not observed draft behavior.

### Questions retained for M1-001

M1-001 should investigate supported source identifiers and URL forms; a
mainboard-only versus multi-board policy; required versus optional fields;
duplicate occurrence preservation; `cardID` versus Scryfall-printing versus
Oracle identity; source snapshot provenance; and diagnosable treatment of
missing/custom/unresolved data. It should not accept source display fields or
curator format settings as domain truth without an approved policy.

## Metadata boundary

| Layer | What belongs there | What this discovery does not do |
|---|---|---|
| Source facts | CubeCon roster link and event tag; CubeCobra full/short IDs, visibility, array lengths, membership order/fields, nested ID evidence, and source version/timestamps. | Does not convert a source tag or card field into a CubeAI rule. |
| Curator-declared metadata | CubeCobra descriptions, named formats, and claims about intended archetypes, gameplay, restrictions, or design philosophy. | Does not treat those claims as verified gameplay behavior. |
| Future CubeAI-derived metadata | Archetype inference, color balance, power level, synergy, first-pick ranking, pick order, and analytical summaries. | Does not derive or store any of them as authoritative metadata. |

Archetype labels must remain curator-declared or later explicitly derived.
Likewise, no observed JSON field in this sample is evidence of human pick data;
future analytics must distinguish declared design intent, observed draft events,
and CubeAI-derived analysis.

## Coverage matrix

`✓` means the feature was directly observed in that Cube's current JSON
response; `—` means it was not selected for coverage, not that the feature is
impossible.

| Cube | Conventional mainboard | Nonempty maybeboard | Mainboard duplicates | Membership tags/notes | Finish or image variation | Sparse optional outer fields |
|---|---:|---:|---:|---:|---:|---:|
| MTGO Vintage Cube | ✓ | — | — | ✓ | — | — |
| Good Clean Magic | ✓ | ✓ | — | — | ✓ | — |
| The Peasant+ Cube | ✓ | — | — | ✓ | — | — |
| Sammich's Peasant Cube | ✓ | ✓ | — | ✓ | ✓ | — |
| aquaone powered | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| HeatherCube | ✓ | ✓ | ✓ | — | — | ✓ |
| Hackett Cube | ✓ | — | ✓ | ✓ | ✓ | — |
| Old Border Foil Cube 450 | ✓ | ✓ | — | ✓ | ✓ | — |
| game zones cube | ✓ | ✓ | ✓ | ✓ | ✓ | — |

## Recommendation for M1-001

Use all nine primary Cubes during contract discovery, but phase the work:

1. Start the ordinary-current-snapshot boundary with MTGO Vintage Cube and
   Good Clean Magic.
2. Validate metadata/board variation with The Peasant+ Cube and Sammich's
   Peasant Cube.
3. Exercise duplicate membership, optional fields, finish, annotations, and
   image values with the five EDGE Cubes.

The first contract investigation should explicitly cover full/short identifier
handling, `mainboard` membership order, separate printing/Oracle evidence,
nonempty other boards, duplicate conservation, optional source fields, and
snapshot provenance. It should defer special draft formats, unlisted/private
access, non-mainboard membership semantics, historical snapshots, custom and
voucher admission, pick/draft-history import, and all archetype/pick analytics.

## Open human decisions

1. Should M1 accept only `visibility: "pu"` Cubes, or can an explicitly
   supplied unlisted Cube be a supported source?
2. Is the first import contract mainboard-only with diagnostics for other
   boards, or should a named-board policy be accepted before implementation?
3. After M0-008 defines sanitization and licensing, which real structural cases
   should become small reviewed contract fixtures—especially custom/unresolved
   rows that this corpus did not observe?

No architecture, milestone state, domain model, or external-provider contract
is changed by this report.
