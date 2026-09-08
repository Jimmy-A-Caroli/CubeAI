# M2-004 CardFacts Foundation

## Current implementation boundary

The implemented `CardFacts` foundation normalizes immutable, provider-neutral
top-level printing facts. It preserves the provider's layout string and never
parses mana-cost notation. A valid top-level record is retained even when the
provider layout has not yet received reviewed semantics or a face lacks colour
or type facts.

`completeness` and `deferred_semantics` make that boundary explicit:

- `complete`: reviewed layout and complete face semantics;
- `partial`: reviewed layout, but one or more face colours or type flags are
  unavailable; and
- `deferred`: the provider layout is retained in `provider_layout`, but its
  normalized layout semantics are not reviewed.

No projection may silently treat deferred or partial facts as complete.

## Current layout status

| Provider/layout form | CardFacts status | Current treatment |
| --- | --- | --- |
| `normal` | complete | Normalized as `single` from top-level facts. This includes ordinary Class cards when supplied as `normal`; class-specific rules are not interpreted. |
| `split` | complete | Normalized as `split`; ordered complete faces are retained. |
| `adventure` | complete | Normalized as `adventure`; ordered complete faces are retained. |
| `transform` | complete | Normalized as `transform`; ordered complete faces are retained. |
| `modal_dfc` | complete | Normalized as `modal_dfc`; land/nonland face facts remain explicit. |
| `prepare` | deferred | Top-level facts and ordered faces are retained, but no projection semantics are assigned. |
| `meld` | deferred | Top-level facts and ordered faces are retained, but no projection semantics are assigned. |
| `leveler` | deferred | Top-level facts are retained; level-band rules and projection semantics are deferred. |
| `saga` | deferred | Top-level facts are retained; chapter rules and projection semantics are deferred. |
| Class card reported through another unreviewed provider layout | deferred | The exact provider layout is retained pending review. |

Incomplete face colour or type data produces `partial` regardless of an
otherwise reviewed layout. The unknown facts remain `None`; the foundation
does not infer them from names, mana costs, or parent card text.

## Remaining M2-004 work

This foundation does not implement mana-curve or colour-distribution
projections, their projection definitions, API, UI, inclusion toggles, or UI
rendering tests. Those remaining issue outcomes stay blocked on a reviewed
projection contract for complete, partial, and deferred records.
