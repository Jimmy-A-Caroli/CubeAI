# M2-015 Strategic Vocabulary Contract

**Status:** ACCEPTED v1 successor vocabulary; no card assignments are implied.

**Vocabulary identifier:** `vintage-cube-strategic-v1`

## Approved model

Vintage Cube v1 separates three non-interchangeable concepts:

- **roles** remain the closed M2-006 v0 card-contribution vocabulary;
- **macro paths** describe a broad deck direction; and
- **packages** describe an overlapping engine or module.

Both macro paths and packages are explicit affinity target types. An affinity
record names exactly one target type and one key, but a membership or identity
may hold several positive relations across both types. No exclusivity is
implied.

### Macro paths

`aggro`, `control`, `midrange_value`, `big_mana`

### Packages

`reanimator`, `artifacts`, `cheat_creatures`, `lands_depths`

The active v1 vocabulary deliberately excludes `combo`, `generic_blue`,
`storm`, `high_tide`, `madness`, `self_mill`, `painter`, and other narrow or
rotating structures. They remain research evidence only and require a future
versioned human decision before becoming keys.

## Affinity and provenance

Both target types reuse the approved categorical `none` / `supports` / `strong`
scale. `UNKNOWN` is no assignment, never a serialized `none`. v1 remains
non-negative. Only `curator_defined` and `human_annotated` records may become
active; no source tag, Oracle text, or inferred relationship is active input.

## Versioning and migration

`vintage-cube-archetypes-v0` remains immutable. It is not reinterpreted:
`reanimator` and `artifacts` in v0 stay historical flat-archetype keys, and
`ramp` is not silently renamed to `big_mana`.

The successor artifact uses the separate
`cubeai.strategic-affinity-assignment-set` envelope. The existing v0 artifact
remains preserved, and the regenerated all-UNKNOWN v1 artifact is bound to the
same exact CubeVersion. No card relation migrated because v0 had none.

## Non-goals

This contract adds no scoring weights, pool-state mechanics, openness schedule,
candidate ledger, Bot behavior, UI, API, auto-tagging, or card-wide curation.
