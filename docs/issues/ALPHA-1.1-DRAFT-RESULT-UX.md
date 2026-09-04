# Alpha-1.1 — Make local drafts visual and reviewable

**State:** `READY` — directly authorized after hands-on Alpha feedback.

**Dependencies:** M1-015 and M1-017 are complete. This focused product pass
does not complete M1-018 or authorize M2.

## Goal

Turn a completed local draft into a compact, understandable result without
changing deterministic draft behavior, Bot v0 behavior, or the existing
provider/persistence boundaries.

## Scope

- Project useful already-resolved card details and canonical image URLs through
  the existing backend → API → React path. The explicit Alpha-1 stabilization
  decision permits normal browser rendering of the cached Scryfall image URL;
  it does not authorize image downloading, mirroring, proxying, or offline
  caching.
- Make cards visual and inspectable in the current pack and pool.
- Use the existing exact-printing cache to show source-backed card colour,
  mana, type, rules, and face-level details when available. Do not infer an
  archetype: Cube archetypes require an explicit source and provenance model.
- Remove draft-instance and Cube-membership identifiers from the normal UI.
- Add a result-first completed-draft view: actual draft configuration, visual
  pool, one primary review action, human-pick review, and post-completion Bot
  pick/provenance review. Make each recorded Bot seat directly selectable and
  describe only its persisted raw-ranking decision evidence, not invented Bot
  reasoning.
- Keep a dense, responsive pack/review grid suitable for a 15-card pack;
  visual hierarchy must not depend on oversized cards.
- Retain active-draft hidden-information rules and expose no provider payloads
  or raw persistence records.

## Out of scope

Bot changes, drafting advice, analytics, wheels, decks, archetypes, color or
curve analysis, ML, browser API identity resolution, image proxy/mirroring,
new services, and M2 implementation.

## Acceptance evidence

- Focused backend/API tests prove cached detail/image URL projection and that
  active views remain seat-safe.
- Focused React tests prove visual cards/fallbacks, keyboard-accessible detail,
  no normal-UI internal IDs, result summary, human review, and completion-only
  Bot review.
- Rendered browser review covers desktop, narrow viewport, keyboard/focus,
  image and fallback states, completion, history, and Bot review.
- The existing deterministic full-draft tests remain green.
