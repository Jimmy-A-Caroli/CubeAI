# M2 Draft Position & Metrics Contract

## Status and problem statement

**Status: FROZEN — READY FOR A FUTURE METRIC IMPLEMENTATION.** The human
approved the five M2 draft-metrics decisions on 2026-09-04. This is the
binding contract for that future work. It defines factual draft-position
vocabulary; it does not add analytics, a metric store, a dashboard, strategy
interpretation, or Bot behavior.

The completed-draft review currently can show a label such as `Pack 24 · Pick
1` to a drafter in an eight-seat, three-round draft. That is misleading. A
drafter's normal vocabulary is `Pack 1 · Pick 1` through `Pack 3 · Pick 15`.
The number 24 is a distinct technical identity for one of the 24 allocated
physical packs, not a draft round.

The governing distinction is:

```text
pack round (the drafter's position) != physical pack (an allocated object)
```

Both values are real, stable facts. Neither is a strategic conclusion.

## Current semantic mismatch

The domain already distinguishes the concepts.

| Layer | Current field | Actual meaning | Result |
|---|---|---|---|
| `DraftState` | `pack_round` | Zero-based user-facing round | Correct separate state. |
| `DraftState` | `pick_number` | Zero-based pick within that round | Correct separate state. |
| `DraftPack` / `PickEvent` | `pack_number` | Zero-based physical allocated-pack identity | Required technical provenance. |
| active `DraftViewDto` | `pack_number = pack_round + 1` | One-based user-facing round | Correct for the active-draft UI. |
| completed `DraftReviewPickDto` | `pack_number = event.pack_number + 1` | One-based physical pack identity | Ambiguous API projection. |
| `DraftWorkspace.pickLabel` | `Pack {pick.pack_number}` | Treats the review's physical ID as a user-facing round | Misleading review label. |

Allocation assigns contiguous physical pack numbers `0..(seats *
packs_per_seat - 1)` and stores an initial `owner_seat`. Packs rotate through
seats within a round; their physical identity does not become a round. The
event persists that identity for replay and provenance. SQLite serializes the
same allocation and event fields unchanged.

Therefore this is primarily **B: an API projection with an ambiguous field,
followed by a UI interpretation error**. It is not evidence that the event
model lacks a round: `DraftState.pack_round` is the existing authoritative
round state. M2-001 observations and M2-002 wheels retain event physical-pack
identity, as they should.

## Canonical vocabulary

| Concept | Proposed definition | Human decision? |
|---|---|---|
| Draft | One deterministic drafting session, identified by `draft_id`, with immutable configuration, allocation, and ordered events. | No |
| Seat | One numbered participant position in that draft. | No |
| **Pack round** | The zero-based state-machine round `DraftState.pack_round`; display it one-based as **Pack 1..N**. This is the canonical user-facing term. | No |
| Physical pack | One allocated `DraftPack`, identified by `(draft_id, pack_number)`; it starts with `owner_seat` and circulates. | No |
| Pick number | The zero-based `DraftState.pick_number` / `PickEvent.pick_number` within a pack round; display it one-based as **Pick 1..pack_size**. | No |
| Cards available before pick | The cardinality of the acting seat's M2-001 `cards_seen` candidate tuple immediately before its event. | No |
| Actor | The event's explicit origin, actor ID, and, for a Bot, recorded strategy/rating/tie-break provenance. | No |
| Card instance | One immutable `DraftCardInstance`, identified by its complete value: draft ID plus instance ID and Cube-membership reference. | No |

Use **pack round** in domain and API contracts. The normal product label may
say **Pack** because drafters conventionally understand “Pack 2, Pick 4”; it
must mean *pack round* in that surface. Avoid introducing a second canonical
term such as “draft round.”

### Position model and notation

The canonical facts for a decision are:

```text
(draft_id, seat_number, pack_round, pick_number,
 cards_available_before_pick, physical_pack_identity, actor, chosen_instance)
```

Stored `pack_round` and `pick_number` counters are zero-based. Presentation
`round_number` and displayed `pick_number` counters are one-based. This does
not renumber every field: `seat_number`, global event `sequence`, and
physical-pack identity retain their separately specified bases. Compact
notation is recommended for Inspector or analytics surfaces: `P<round>P<pick>`,
for example `P1P1`, `P1P15`, `P2P1`, and `P3P15`.
Document the notation wherever it is first used; normal UI should prefer
`Pack 2 · Pick 4`.

`PickEvent.sequence` remains a useful global chronological index. It is not a
replacement for `(pack_round, pick_number)` in a user-facing or metric
contract. For current simultaneous-seat scheduling, the round of an event is
deterministically derivable as:

```text
floor(sequence / (configuration.seats * configuration.pack_size))
```

Replay is the preferred implementation source because it also validates the
event schedule. No new persistent event field is needed merely to correct a
projection.

## Physical-pack identity

`DraftPack(draft_id, pack_number, owner_seat)` and `PickEvent.pack_number`
are the stable physical-pack provenance. They must remain unchanged for:

- deterministic allocation and alternating pass topology;
- replay validation that a pick came from the active pack;
- M2-002 instance-return/wheel provenance; and
- explaining where a particular instance circulated.

Physical identity is not normal drafter-facing information. It belongs in an
optional Inspector/debug/provenance surface, explicitly labelled **Physical
pack** (for example, `Physical pack 24`), never under the bare label `Pack`.

## First, last, and cards-available semantics

All definitions refer to one actor's legal decision observation, before the
selected card is removed.

| Term | Exact factual definition |
|---|---|
| First pick | `pick_number == 0` within that seat's pack round (display Pick 1). |
| Last pick | `cards_available_before_pick == 1`. |
| Second-to-last pick | `cards_available_before_pick == 2`. |
| General late-position primitive | `cards_available_before_pick`, derived as `len(observation.cards_seen)`. |

The first-pick definition is independent of physical pack ID. Last and
second-to-last are deliberately structural rather than hard-coded to picks 15
and 14: they remain correct for every valid positive `pack_size`. “Late pick”
is not yet a band or a quality claim; any threshold broader than these exact
categories requires a future approved consumer and definition.

## Wheel relationship

M2-002 is unchanged. A wheel is a first verified return of the **same complete
`DraftCardInstance`** to the **same seat** after that seat saw and passed it,
then had a later same-seat observation where it was absent, then saw it again.
It is neither a card-quality label nor a synonym for a late pick.

When presented with positional context, a wheel should carry both endpoints:

```text
first seen: round 1, pick 2, cards available 14
returned:   round 1, pick 10, cards available 6
physical pack: 7 (provenance only)
```

Current `WheelObservation` already preserves endpoint event sequence,
physical-pack number, and pick number. A future projection derives the
endpoint round and candidate count from the associated ordered M2-001
observations; it must not guess a round from the physical pack number.

## Identity, actor, Cube, configuration, and completion scopes

Identity scopes must never be silently substituted:

| Purpose | Required identity scope |
|---|---|
| Replaying a chosen card and detecting a wheel | Complete `DraftCardInstance`. |
| Preserving a distinct Cube slot, including duplicates | Cube membership ID within its immutable `CubeVersion`. |
| Printing-specific reporting | Exact printing ID, only when present. |
| Oracle/card roll-up | Oracle ID, only as an explicitly requested aggregate and only for resolved identities. |

The smallest defensible initial aggregate should be **Cube-membership scoped**:
each draft instance contributes to the membership from which it was allocated.
That preserves duplicate copies and exact Cube construction. An Oracle-ID roll-up
may be added later as a separately labelled view; it must exclude or visibly
separate unresolved identities and never replace membership-level evidence.

Every metric query must require an explicit actor filter. Defaults must not mix
human and Bot events. For the current local product, **local human** means
`actor_origin == HUMAN` and `seat_number == 0`. A Bot population means
`actor_origin == BOT` plus an exact recorded
`(bot_provenance.strategy_id, bot_provenance.strategy_version)` pair. A
combined population must enumerate the selectors it includes. Recorded Bot v0
behavior is not human behavior.

Round derivation always uses the global persisted event sequence (or validated
replay), never an index created after filtering events to an actor population.

Initial metrics should be scoped to one exact immutable `CubeVersion` and one
exact configuration tuple `(seats, packs_per_seat, pack_size)`. Global card or
source-wide comparisons require a future normalization decision. The initial
population is completed drafts only. If incomplete-history metrics are ever
needed, they must be a separately labelled population rather than being
silently blended with completed drafts.

## Candidate metric contracts

These are proposed schemas, not calculated values or an implementation
authorization. Unless a row says otherwise, its population is completed
drafts in one CubeVersion/configuration/actor scope, and duplicate memberships
remain distinct.

| Metric | Numerator / value | Denominator or sample | Identity scope | Recommendation / decision |
|---|---|---|---|---|
| Mean / median pick | One-based `pick_number` of each selected instance | Selected-event sample count; report `n` | Cube membership | Approved descriptive position distribution, not card quality. |
| Pick rate | Selections of instances from membership M | Legal M2-001 candidate appearances of instances from M | Cube membership | Approved opportunity-based definition; an Oracle roll-up remains separate. |
| First-pick rate | Selections from M where `pick_number == 0` | First-pick candidate appearances of M | Cube membership | Approved definition, distinct from “share of M's picks that were first picks.” |
| First-pick share (different metric) | Selections from M at first pick | All selections from M | Cube membership initially | Do not call this first-pick rate if both are shown. |
| Seen-before-pick count | For a selected `(seat, instance)`, number of prior legal M2-001 appearances of that exact instance to that seat | Selected `(seat, instance)` sample; report distribution and `n` | Draft instance | Approved M2-009 definition. It is 0 when selected at first sight. |
| Last-pick rate | Selections from M where cards available is 1 | Candidate appearances of M where cards available is 1 | Cube membership | Exact structural category. |
| Second-to-last rate | Selections from M where cards available is 2 | Candidate appearances of M where cards available is 2 | Cube membership | Exact structural category. |
| Wheel return rate | M2-002 first-return facts | Completed pass opportunities; see below | Draft instance, aggregated only after mapping to membership | Approved denominator. |

The recommended pick-rate denominator counts every legal opportunity, not
merely every drafted copy. Thus two duplicate Cube memberships can each
contribute independently. This answers “when this Cube slot was available to
this actor, how often was it chosen?” It does not claim intrinsic power or
compare different Cube environments.

The approved wheel-rate denominator is a **completed pass
opportunity**: a `(draft_id, seat, DraftCardInstance)` first observed by that
seat and not selected, with a later same-seat observation in the same pack
round where the instance is absent. Its numerator is the M2-002 first return
for that same tuple. This excludes a last opportunity with no later seat turn
and preserves M2-002's required evidence that the card left the seat. The
rejected alternative is all unchosen first-seen instances; it is simpler but
answers a weaker question because many cases had no structural opportunity to
return. Do not use all times seen: it confounds repeated observations with
opportunity.

Every future metric result must carry its exact CubeVersion, configuration,
identity, actor, and completion selectors along with its numerator and
denominator (or `sample_n`). A zero denominator/sample has an **undefined**
metric value, never `0%` or a fabricated zero. This keeps “zero selections
from legal opportunities” distinct from “no legal opportunities,” and applies
equally to mean and median position when `sample_n == 0`.

## Approved human decisions

| Decision | Recommendation | Strongest alternative | Consequence of choosing incorrectly |
|---|---|---|---|
| Initial aggregate card identity | Cube membership within an exact CubeVersion. | Oracle-ID roll-up. | Collapsing duplicates can hide different slots, printings, or unresolved identity. |
| “Seen-to-pick” meaning | Exact-instance prior-appearances count above. | Omit it until a user-facing question is specified. | A vague label could be mistaken for pick rate or strategic delay. |
| Wheel-rate denominator | Completed pass opportunities. | All unchosen first-seen instances. | The reported percentage describes different populations and cannot be compared honestly if unnamed. |
| Default actor population | Separate human and each Bot strategy/version. | Explicitly labelled combined population. | Mixing Bot v0 and human history makes the result falsely look like human evidence. |
| Initial inclusion of incomplete drafts | Completed drafts only. | A separately labelled partial-history population. | Mixing abandoned histories changes opportunity and position denominators. |

These binding choices complete the M2 metrics contract. They do not authorize
metric calculation, storage, analytics views, or an Oracle-level roll-up. The
semantic facts in the vocabulary table require no further decision.

## UI correction required

The smallest follow-on correctness change is limited to completed review
surfaces:

1. Derive and expose an explicit one-based `round_number` from replayed draft
   position for each review pick.
2. Have `DraftWorkspace.pickLabel` display `Pack {round_number} · Pick
   {pick_number}` for human and Bot histories.
3. Do not expose review physical-pack identity in normal UI. Preserve it only
   in a future optional Inspector/debug/provenance DTO, with an explicit label.
4. Rename or remove the ambiguous review DTO `pack_number` rather than
   retaining a field whose transport meaning differs from the active draft
   view. The active view's current displayed `pack_number` is already a
   one-based pack round and is not the bug.

The M2-001 observations endpoint currently also presents event physical-pack
identity under `pack_number`. Any later consumer must receive either a clearly
named `physical_pack_number` or a separately derived `round_number`; it must
not infer one from the other. This closeout intentionally corrects only the
completed-review DTO/UI surface identified in the problem statement.

## Deterministic validation probes

Using the existing state machine and first-legal-card selection:

- In an 8-seat × 3-round × 15-card draft, seat 0 produced 45 positions
  exactly `P1P1..P1P15`, `P2P1..P2P15`, and `P3P1..P3P15`. The same history's
  physical-pack labels were `1, 2, ..., 8, 1, ..., 8` in round 1; `9, 16,
  15, ..., 10, 9, ...` in round 2; and `17, 18, ..., 24, 17, ...` in round
  3. For example, seat 0's first round-2 pick is `P2P1` from physical pack 9,
  proving the values are independent.
- In a 4-seat × 2-round × 5-card draft, seat 0 produced exactly
  `P1P1..P1P5` and `P2P1..P2P5`; its final pick in each round had exactly one
  candidate. This confirms that the last-pick definition derives from cards
  available, not an eight-seat/15-card assumption.

Both probes were synthetic, offline, and used only existing deterministic
domain behavior. They add no permanent fixture or test complexity.

## Deferred interpretation and implementation consequences

This contract does not infer that a card is weak, unwanted, open, synergistic,
or a good/bad Bot pick. It does not define archetypes, colors, mana, ratings,
signals, gameplay performance, or training data.

The Pack/Pick review correction is implemented with this closeout: review DTOs
expose `round_number`, and normal review UI labels it as `Pack`. Physical-pack
identity remains intact in domain events and allocations. A future, separately
authorized M2-009 implementation may add pure metric calculations and their
synthetic hand-calculated reference tests using the frozen scopes above.
