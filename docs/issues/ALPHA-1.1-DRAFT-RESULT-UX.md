# Alpha-1.1 — Make local drafts visual and reviewable

**State:** `READY` — directly authorized after hands-on Alpha feedback.

**Dependencies:** M1-015 and M1-017 are complete. This focused product pass
does not complete M1-018 or authorize M2.

## Goal

Turn a completed local draft into a compact, understandable result without
changing deterministic draft behavior, Bot v0 behavior, or the existing
provider/persistence boundaries.

## Scope

- Project useful already-resolved card details through the existing backend →
  API → React path. The cache stores provider image URLs, not local bytes, so
  the UI must use an accessible local visual fallback rather than request them.
- Make cards visual and inspectable in the current pack and pool.
- Remove draft-instance and Cube-membership identifiers from the normal UI.
- Add a result-first completed-draft view: actual draft configuration, visual
  pool, one primary review action, human-pick review, and post-completion Bot
  pick/provenance review.
- Retain active-draft hidden-information rules and expose no provider payloads
  or raw persistence records.

## Out of scope

Bot changes, drafting advice, analytics, wheels, decks, archetypes, color or
curve analysis, ML, provider calls from the browser, image proxy/mirroring,
new services, and M2 implementation.

## Acceptance evidence

- Focused backend/API tests prove cached detail projection, no forwarded remote
  image URL, and that active views remain seat-safe.
- Focused React tests prove visual cards/fallbacks, keyboard-accessible detail,
  no normal-UI internal IDs, result summary, human review, and completion-only
  Bot review.
- Rendered browser review covers desktop, narrow viewport, keyboard/focus,
  image and fallback states, completion, history, and Bot review.
- The existing deterministic full-draft tests remain green.
