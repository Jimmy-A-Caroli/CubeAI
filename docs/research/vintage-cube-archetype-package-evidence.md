# Vintage Cube Archetype and Package Evidence

**Status:** research evidence for a human vocabulary decision. It creates no
CubeAI card assignment, changes no accepted vocabulary, and implements no Bot
behavior.

## Scope and currentness

The historical baseline remains
`sha256:25eb8419430fc1ef659723c388caf17697c80054fd7e74a7e73fbb9411242c12`:
540 memberships, 240 resolved identities, and 300 unresolved identities. It
is preserved as historical evidence. Recovery produced successor
`sha256:17a9b63fd0a596760fa1205b24b93216e89e899811f7e4c105ea4e3ca3acac70`:
540 memberships and 540 resolved identities. Exact membership is now checked
against that successor before a source-assisted proposal is recorded; source
claims still never become active strategic assignments automatically.

Method: prefer dated MTGO curator material, use the official card list as a
live membership cross-check, then use expert and community sources only to
corroborate terminology or describe drafting practice. A historical article is
not silently transferred to the August list. Links were checked on 2026-09-08.

## Source record

| Evidence type | Source and date | Paraphrased strategic claim | Currentness |
| --- | --- | --- | --- |
| Curator | [The Hobbit Vintage Cube Update](https://www.mtgo.com/news/hob-vintage-cube-update), MTGO, 2026-08-14 | Welder was expanded with small artifacts and Painter/Grindstone; Depths/Stage returned with tutors; High Tide returned because combo support increased; Madness/self-mill/graveyard remains but was reduced. | CURRENT |
| Curator/list | [Vintage Cube Card List](https://www.mtgo.com/vintage-cube-cardlist), MTGO, updated 2026-08-14/effective 2026-08-19 | The live list contains representative cards for Reanimator, Tinker/Academy artifacts, Sneak/Breach/Show and Tell, High Tide, Depths/Stage, and Painter/Grindstone. | CURRENT-BUT-NOT-EXACT |
| Curator | [Vintage Cube: A Beginner's Guide](https://www.mtgo.com/news/beginners-guide-vintage-cube), MTGO, undated page | Strategies can be pure or hybrid; Reanimator can be a main theme or a small package; artifact plans have cross-colour support; fixing keeps options open. | RECENT-BUT-NOT-EXACT |
| Curator | [Centering the Magic Online Vintage Cube](https://www.mtgo.com/news/vintage-cube-update-may-2024), Ryan Spain and Chris Wolf, 2024-05-03 | Narrow packages rotate; Dark Depths is a recurring guest, and Storm is intentionally narrow. | HISTORICAL policy/context |
| Expert | [Ramp It Up](https://www.tcgplayer.com/content/article/Ramp-It-Up-%7C-Luis-Scott-Vargas-%7C-Vintage-Cube/e1c54107-b21e-4eca-a4ea-c082e7711e63), Luis Scott-Vargas, updated 2025-02-13 | Green/blue ramp can support large-threat strategies. | RECENT-BUT-NOT-EXACT |
| Expert | [Ultimate Guide to Vintage Cube Draft](https://draftsim.com/mtg-vintage-cube/), Draftsim, updated 2025-07-30 | Reanimator and artifact drafting have recognisable requirements. | RECENT-BUT-NOT-EXACT |
| Community | [Find archetypes](https://www.reddit.com/r/mtgcube/comments/1v78ntm/find_archetypes/), r/mtgcube, 2026-07 | Describes macro shells plus overlapping combo packages rather than retail-Limited colour-pair lanes. | COMMUNITY corroboration only |

## Current strategic-structure map

Representative cards are evidence examples, not exhaustive lists or proposed
assignments. “Current” below means the August official source; it does not
prove presence in CubeAI's immutable captured list.

| Structure | Kind tested | Support | Representative anchors / enablers / payoffs | Overlap and evidence conclusion |
| --- | --- | --- | --- | --- |
| Aggro | macro path | CURRENT-BUT-NOT-EXACT | low-curve white/red threats and removal in the live list | Broad shell; can overlap with artifacts or sacrifice. No separate package needed from this evidence. |
| Control | macro path | CURRENT-BUT-NOT-EXACT | blue interaction/card advantage, sweepers, long-game finishers | Broad shell; official guidance says hybrids exist. Generic blue is an open-shell state, not an affinity label. |
| Midrange/value | macro path | CURRENT-BUT-NOT-EXACT | efficient threats, interaction, fixing | Broad default shell, not a named synergy engine. |
| Big mana | macro path | CURRENT-BUT-NOT-EXACT | Channel, Gaea's Cradle, fast mana, large threats | LSV corroborates the deck pattern. `mana_acceleration` remains a role; `big_mana` is the deck-level destination. |
| Reanimator | package | CURRENT-BUT-NOT-EXACT | Entomb, Reanimate, Animate Dead, Shallow Grave; Archon of Cruelty and Griselbrand | Official guide says it can be a main theme or a small package. It can combine with control, discard, or cheat-creature plans. |
| Artifacts / Welder | package | CURRENT-BUT-NOT-EXACT | Goblin Welder/Engineer, cheap artifacts, Tinker, Tolarian Academy, Painter/Grindstone | August curator update explicitly expands it; it can be aggressive, controlling, mana-oriented, or combo-oriented. |
| Cheat creatures | package | CURRENT-BUT-NOT-EXACT | Sneak Attack, Through the Breach, Show and Tell, Channel; large creature targets | Related to but distinct from Reanimator because it can bypass the graveyard. |
| Lands / Depths | package | CURRENT-BUT-NOT-EXACT | Dark Depths, Thespian's Stage, Crop Rotation, Knight/Wight of the Reliquary | August update explicitly reintroduced the package. It overlaps with green fixing/ramp and value lands. |
| Spell-combo candidates | uncertain package family | CURRENT-BUT-NOT-EXACT | High Tide, Underworld Breach, Tendrils, Yawgmoth's Will, Doomsday/Oracle, Chain of Smog | Curators say combo support increased, but the mechanisms are heterogeneous. Evidence does not yet justify one active `combo` affinity or one shared package label. |
| Madness / self-mill / graveyard | uncertain package family | CURRENT-BUT-NOT-EXACT | Survival, Bazaar, Rootwallas, Vengevine | Curators group these terms but are reducing the footprint. Keep them distinct from Reanimator until an exact-version review confirms density and boundaries. |
| Painter / Grindstone | narrow subpackage | CURRENT-BUT-NOT-EXACT | Painter's Servant, Grindstone, Goblin Engineer | Explicitly added inside the Welder expansion. Best represented initially as evidence beneath artifacts, not a separate namespace key. |

## Classification findings

- **Reanimator:** a package, not an exclusive macro path. Its existing v0 key
  conflates a deck destination with a reusable module.
- **Artifacts:** a package/engine, not one deck shape. The current curator
  evidence explicitly describes both artifact density and a Welder combo.
- **Ramp:** split the concept. Existing `mana_acceleration` remains a card role;
  a future `big_mana` macro path describes the deck it enables.
- **Combo:** not a useful single macro. The current list supports multiple
  engines, but High Tide, Painter, Depths, cheat creatures, and A+B spell
  lines do not share one curation question.
- **Generic blue:** belongs in later pool/open-path state, not a card affinity.
  It describes retained optionality, not a stable strategic package.
- **Kiki/Twin:** historical/unclear for this wave: Kiki-Jiki was not found on
  the current official list. It must not be added from older guides.

## Implications for a reviewer

The same `none` / `supports` / `strong` scale can describe a reviewed relation
to either a macro path or a package. It does not describe whether a package is
complete, whether a card is a role, or whether a seat should pick that card.
For each future relation, preserve source URL/date/currentness and a concise
anchor, enabler, payoff, bridge, or narrow rationale as **evidence**. A human
then accepts, modifies, or rejects it before creating a `curator_defined` or
`human_annotated` assignment. No article produces one automatically.

## Uncertainty

The successor has a successful full identity capture, but current-source
examples remain intentionally small and are proposals, not 540-card coverage.
MTGO rotates narrow packages, so a future CubeVersion must repeat this
currentness check.
