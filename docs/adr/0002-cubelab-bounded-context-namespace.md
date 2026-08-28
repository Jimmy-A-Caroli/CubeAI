# ADR-0002: Use the CubeLab bounded-context namespace

Status: Accepted
Date: 2026-08-28

## Context

ADR-0001 accepts a modular monorepo for CubeAI, but its initial package layout named generic `cubeai.domain` and `cubeai.application` packages. CubeLab needs an explicit first-class bounded-context namespace so that its domain and application logic remain independent of delivery, persistence, external providers, and the future CubeGame workstream. The project must retain the approved modular-monorepo direction and avoid creating empty package trees before M0 supplies working contents.

## Decision

Use `cubeai.lab` as the conceptual namespace for CubeLab within the Python workspace:

```text
backend/src/cubeai/
├── lab/
│   ├── domain/
│   └── application/
├── api/
└── adapters/
```

`cubeai.lab.domain` owns framework-independent CubeLab domain behavior. `cubeai.lab.application` coordinates CubeLab use cases and ports. `cubeai.api` and `cubeai.adapters` are outer boundaries and must not become dependencies of the Lab domain. CubeLab remains useful independently of CubeGame and any chosen game engine.

This ADR fixes the conceptual namespace and boundary direction. M0-001 may still select tooling details, and M0 implementation issues create directories only with working configuration, tests, and commands.

## Alternatives considered

### `cubeai.domain`

This flatter namespace is concise, but it makes CubeLab look like the whole product domain and leaves less room to express CubeGame as an independent bounded context without conflating their concerns.

### Top-level `cubelab`

This makes the name visible but separates it from the shared `cubeai` namespace and weakens the package-level expression of the accepted modular monorepo.

### `cubeai.lab`

This preserves the shared product namespace while making CubeLab's boundary explicit. It is the selected alternative.

## Consequences

- M0 package and boundary checks target `cubeai.lab.domain` and `cubeai.lab.application`.
- API and adapter code remain outer boundaries at `cubeai.api` and `cubeai.adapters`.
- CubeLab can evolve and remain useful without CubeGame, Forge, or any other game engine.
- Future bounded contexts can use the `cubeai` namespace without redefining CubeLab as the entire product domain.
- Existing documentation and M0 backlog language must use the new conceptual namespace.

## Revisit when

Revisit this decision only if evidence from implemented M0/M1 package boundaries, a separately justified CubeGame bounded context, or a supported multi-language packaging constraint shows that `cubeai.lab` prevents clear ownership or replaceable boundaries. Any change must preserve CubeLab's framework independence and be recorded in a superseding ADR.
