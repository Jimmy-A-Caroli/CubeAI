# M1-018 acceptance evidence

## Current scope

M1-016 and M1-017 are complete. M1-018 is now `READY`; this record captures
the evidence gathered before its supervised exit review. It does not claim
that a public-provider import succeeded in every execution environment.

## Deterministic local scenario

`backend/tests/test_local_api.py::test_m1_acceptance_replays_the_fixed_fixture_through_restart`
uses the reviewed synthetic fixture boundary and exercises the public local
API in this order:

1. import a four-membership fixture and freeze a usable Cube version;
2. validate a fixed two-seat, one-pack, two-card, seed-13 configuration;
3. start, complete, and persist the one-human-seat draft;
4. repeat the identical scenario in a fresh SQLite directory and compare the
   first human pack, human pool, completion state, and empty final pack; and
5. recreate the API against the first SQLite directory and resume the completed
   human-safe view.

The test deliberately keeps provider payloads out of the fixture. Existing
domain, Bot, and SQLite tests cover exact event replay plus human/Bot actor and
strategy provenance; the API still exposes only the human-safe projection.

## Browser and accessibility review

On 2026-09-04, the local Vite page rendered and exposed the import workflow,
healthy backend status, keyboard-labelled inputs, and the standard 8/3/15
configuration in a real browser. Component-level checks cover accessible card
alt text, absent-image and load-error fallback, keyboard selection, visible
focus styling, detail-dialog initial focus, Escape dismissal, and focus
restoration.

The currently available browser automation surface cannot operate controls or
set a viewport. Therefore it could not execute the image-enabled draft flow at
wide and narrow dimensions, count actual browser image-load failures, or
record the required rendered pack/pool observations. This is an evidence gap,
not a claim that the product passed those checks. M1-018 remains `READY` until
a human or browser-capable runner records that final review.

## Opt-in public-source smoke

On 2026-09-04, the bounded read-only `modovintage` checkpoint completed after
the live source boundary was corrected to accept an explicitly empty optional
`mana_cost` as absent display metadata. It imported 540 memberships with the
expected non-blocking `unsupported_non_mainboard` warning, resolved all 540
exact Scryfall printings, and found 540 usable retained image URLs with zero
metadata fallbacks. The fixed 8-seat, 3-pack, 15-card, seed-20260903 draft
allocated 24 packs / 360 instances, completed 360 events, and produced eight
45-card pools. An offline cached replay resolved all 540 records as
`cached_fresh` and matched the same deterministic result. No provider payload
or card list was retained in this report.

This direct-domain checkpoint supports source, metadata, image-URL, and
determinism evidence. It does not replace the outstanding API/persistence/UI
wide-and-narrow rendered acceptance described above, and it cannot observe
browser image-load failures.

## Non-goals checked

The flow adds no authentication, hosted services, analytics, cards-seen
history, draft advice, gameplay, multi-seat views, or client-side copies of
hidden draft state.
