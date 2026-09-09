# Proposal: Roles, Macro Paths, and Packages for Vintage Cube

**Status:** ACCEPTED on 2026-09-09. The approved contract is recorded in
[`M2-015 Strategic Vocabulary Contract`](../M2-015-STRATEGIC-VOCABULARY-CONTRACT.md).
This proposal remains the supporting decision record; it does not alter Bot v0.

## Problem

The accepted v0 flat keys mix three semantic levels: `aggro`, `control`, and
`midrange` are broad deck shapes; `reanimator` and `artifacts` are overlapping
engines; and `ramp` mixes a card contribution with a possible big-mana deck.
Recent MTGO curator material describes these engines as hybrid and rotating.
The supporting evidence is kept separate in
[Vintage Cube Archetype and Package Evidence](vintage-cube-archetype-package-evidence.md).

## Models considered

| Model | Strength | Loss / cost |
| --- | --- | --- |
| A. Current flat six | Small and already implemented. | Makes shells, engines, and acceleration answer the same question; cannot explain an artifact-control or cheat-control pool cleanly. |
| B. Expanded flat list | Represents more named plans. | A single namespace becomes a mixture of deck shapes and narrow engines; grows curation cells and makes rotating packages look permanent. |
| C. Roles + macro paths + packages | Separates what a card does, broad deck direction, and optional engines; naturally supports overlap. | Requires a new vocabulary version and exact migration statement before use. |

## Recommendation

Adopt **Model C** as a new, human-approved vocabulary version before any
large-scale curation. It is the smallest model that expresses the evidence
without building an ontology: one closed macro namespace and one closed package
namespace, both multi-valued and both using the existing categorical affinity
scale.

### Proposed v1 vocabulary for decision

**Macro paths:** `aggro`, `control`, `midrange_value`, `big_mana`.

**Packages:** `reanimator`, `artifacts`, `cheat_creatures`, `lands_depths`.

This deliberately does **not** add `combo`, `generic_blue`, `madness`,
`self_mill`, `storm`, `high_tide`, `painter`, `kiki_twin`, or every possible
engine. Current evidence proves that some spell-combo candidates exist, but
does not establish one stable and cohesive curation unit; retain them as
evidence candidates until a later exact-version decision. Painter/Grindstone is
initially evidence under `artifacts`; this can be reconsidered only if
human review finds that its distinction changes drafting decisions.

## Migration and curation impact

- **M2-006:** v0 remains immutable and historical. A successor issue defines
  v1 namespaces, concise definitions, and migration/no-migration rules; no
  v0 key silently changes level.
- **M2-014:** needs a versioned extension that records whether an affinity
  target is a `macro_path` or `package`; it can reuse `none`/`supports`/
  `strong` and `UNKNOWN` semantics. It must not create a weight mapping.
- **Current artifact:** it has zero assignments, so migration cost is minimal:
  regenerate an all-UNKNOWN v1 artifact for the same exact CubeVersion after
  the new contract is approved. Do not edit the v0 artifact in place.
- **Contextual-v1:** a later strategy could maintain separate macro and package
  support vectors plus opening priors. That is a downstream scoring decision,
  not authorized here.
- **Inspector:** a future candidate ledger may explain both kinds of reviewed
  evidence, but no Inspector change is proposed now.

## Human curation process

1. Pin an exact CubeVersion with a complete enough identity/list capture.
2. Present a reviewer with a small evidence record and one candidate relation:
   macro or package, `none`/`supports`/`strong`, scope, rationale, source, and
   source currentness.
3. The reviewer accepts, changes, rejects, or leaves it `UNKNOWN`.
4. Only accepted `curator_defined` or `human_annotated` records become active.

This keeps the expected workload sparse: macro review is broad but finite;
package review focuses on cards with a credible evidence lead. It does not
pretend every card needs every package decision up front.

## Deferred decision

Whether a future exact-version evidence review warrants a dedicated
`spell-combo` package remains deferred. It is not needed for current curation.

## Proposed backlog follow-up

M2-015 is complete. A later successor, if evidence warrants one, may consider
an additional narrow package without changing this v1 contract in place.
