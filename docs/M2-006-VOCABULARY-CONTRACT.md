# M2-006 Vocabulary Contract

**Status:** ACCEPTED v0 vocabulary; no card assignments are implied.

**Issue:** M2-006 — Define a versioned archetype/tag vocabulary

**Vocabulary identifier:** `vintage-cube-archetypes-v0`

## Decision and boundary

This record accepts a closed, Cube-specific v0 vocabulary for the Vintage Cube
context. It defines labels only. It does not classify a card, activate a
provider tag, implement a scoring rule, alter Bot v0, or infer strategy from
CardFacts. A later reviewed assignment set is the only bridge from a card or
Cube membership to an archetype path.

Role means a useful card contribution. Archetype means a broader Cube-specific
draft plan. A role never implies an archetype affinity by itself.

## Closed role vocabulary

| Role | Meaning and includes | Excludes / ambiguity guidance |
|---|---|---|
| `threat` | A material route to winning or sustained board pressure. | Do not tag every creature or planeswalker automatically. |
| `removal` | Primary function answers a creature or permanent. | Incidental interaction and combat tricks need review. |
| `sweeper` | Ordinarily removes or resets multiple opposing permanents. | It is not inferred from `removal`. |
| `spell_counter` | Primarily counters a spell or relevant stack object. | Taxes, protection, permanent counters, and delays are excluded. |
| `card_advantage` | Produces material net card advantage. | Mana, tempo, filtering, and one-for-one replacement do not qualify alone. |
| `card_selection` | Materially filters, tutors, surveils, or improves access to desired cards. | Ordinary draw without selection need not qualify. |
| `hand_disruption` | Proactively removes or constrains cards in an opponent's hand. | Self-discard is not included unless separately reviewed as a reanimation enabler. |
| `mana_acceleration` | Increases available mana ahead of normal land development. | Color production alone is not acceleration. |
| `fixing` | Materially improves access to one or more required colors. | Card color and color identity do not imply fixing. |
| `reanimation_enabler` | Sets up a practical reanimation plan by placing, finding, or discarding a target. | Generic graveyard interaction is excluded. |
| `reanimation_payoff` | A deliberately desirable target to return early or efficiently. | High mana value alone is insufficient. |
| `artifact_enabler` | Materially supplies artifacts, artifact count, or artifact-dependent setup. | Being an artifact is insufficient. |
| `artifact_payoff` | Materially improves with artifact support. | A generally strong artifact is not automatically a payoff. |

`unknown` is not a role key. An absent role assignment means unassigned under
this vocabulary and evidence; it does not prove the card lacks that function.

## Closed archetype vocabulary

| Archetype | Cube-specific draft-plan meaning |
|---|---|
| `aggro` | Low-curve pressure intended to end the game quickly. |
| `control` | Interaction and card advantage supporting a longer game. |
| `midrange` | Efficient threats and interaction without aggro's speed or control's inevitability assumptions. |
| `reanimator` | Graveyard setup plus effects that return high-impact targets. |
| `artifacts` | A plan materially dependent on artifact density, artifact mana, enablers, or payoffs. |
| `ramp` | Acceleration used to deploy high-cost or otherwise accelerated threats. |

The keys do not encode color, named packages, tempo, combo, lands, tokens,
spells, or tribal themes. Additions require a new reviewed vocabulary version,
not an edit to v0.

## Provenance and strategic activity

The vocabulary recognizes `source_provided`, `curator_defined`,
`human_annotated`, `rule_derived`, and `model_inferred` provenance.
Only `curator_defined` and `human_annotated` associations may be marked
`active` for a future contextual strategy. Provider tags remain retained
evidence only; they do not silently become strategy input. `rule_derived` and
`model_inferred` are inactive until separately approved.

## Versioning and downstream boundary

The identifier above is immutable. A future label or semantic change creates a
new vocabulary identifier and a reviewed migration statement; historical
assignment sets retain their recorded vocabulary version. The contract values
live in `cubeai.lab.domain.archetypes`, but they are not a Bot interface and
do not supply a score.

The next dependent issue is M2-014, which defines reviewed, exact-CubeVersion
affinity assignments. M2-007 remains blocked: its eventual explainable
draft-fit work must consume accepted CardFacts, this vocabulary, and an
accepted assignment set rather than treating this label list as scoring data.
