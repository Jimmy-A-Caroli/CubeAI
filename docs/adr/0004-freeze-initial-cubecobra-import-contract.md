# ADR-0004: Freeze the initial CubeCobra import contract

- **Status:** Accepted
- **Date:** 2026-09-02

## Context

CubeAI needs an explicit, replaceable external-source boundary before adapter
work begins. M1-001 established bounded public-response evidence, sanitization
rules, and the detailed field contract in
[CubeCobra Import Contract](../research/cubecobra-import-contract.md).

## Decision

For the initial CubeCobra import contract, CubeAI accepts only a current public
source addressed by a full ID or nonempty `shortId`. It imports `mainboard`
only and returns an explicit diagnostic for every nonempty supplementary board.

One mainboard array occurrence is one membership. Duplicate occurrences remain
distinct even when provider, printing, or Oracle evidence matches. Printing
evidence and Oracle/card evidence remain distinct source scopes.

Custom, unresolved, and voucher-like source shapes fail closed: no identity is
fabricated, no name is fuzzy-matched, and the synthetic custom fixture does not
define a CubeCobra payload shape. Source provenance is retained but is not
CubeAI version history.

The checked-in provider excerpts remain minimal, sanitized contract evidence.
CubeCobra software licensing does not establish a license for response data;
response-data licensing is not established, and this ADR makes no broader
reuse or licensing conclusion.

## Consequences

- M1-003 and M1-004 must use the detailed contract as their external-source
  authority when separately authorized.
- Unlisted/private input, page URL parsing, named boards, historical snapshots,
  and custom/unresolved resolution are not silently accepted.
- Tests remain offline and use only the reviewed excerpts plus separate
  CubeAI-authored synthetic data.

## Revisit when

Revisit only with evidence and an approved contract extension for a deferred
source behavior. Any change must retain explicit diagnostics, provenance, and
the identity distinction recorded here.
