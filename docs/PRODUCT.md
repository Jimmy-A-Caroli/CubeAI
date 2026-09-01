# CubeAI Product Definition

## Vision

CubeAI is a web-first, local-capable workbench for people who design, draft, study, and iterate on Magic: The Gathering Cubes. Its primary frontend is a web application; online operation is the default and primary deployment model. It should connect Cube definition, drafting, analysis, simulation, deck construction, eventual gameplay, and Cube revision into one reproducible loop.

The first useful product is a web draft application that can be run locally for the initial slice: provide a CubeCobra URL or identifier, validate the imported Cube, and complete an eight-seat draft against basic bots. The same frontend codebase must preserve a future path to appropriate local/offline capability without selecting that implementation now. Each later capability should deepen Cube understanding rather than broaden CubeAI into a generic Magic client.

## Target users

- Cube designers testing balance, archetype support, and card utilization.
- Cube drafters who want a fast local draft and a clear post-draft review.
- Researchers and bot authors comparing transparent, benchmarkable draft strategies.
- Open-source contributors building reusable Cube tooling.

The initial user is technically comfortable enough to run or access a web application. A public hosted consumer experience is not an early requirement.

## Primary use cases

1. Import and inspect a Cube without losing source identities, printings, tags, or duplicate entries.
2. Validate whether a Cube can support a configured draft and explain invalid data.
3. Run a seeded draft with one human and seven bots.
4. Review packs seen, picks, wheels, pool shape, colors, curve, and archetype signals.
5. Compare bot strategies using the same Cube and seeds.
6. Run large reproducible batches and analyze card and archetype behavior.
7. Compare Cube versions as experiments while retaining their inputs and provenance.
8. Eventually build decks and play games through a replaceable gameplay engine boundary.

## Product principles

### Cube first

Every major feature must strengthen the Cube design-and-draft loop. Generic collection management, tournament infrastructure, and unrelated constructed formats are outside the core mission.

### Clean surface, depth on demand

The UI should make the current decision obvious while keeping detailed signals close at hand. It should be faster and clearer than a raw table without relying on spectacle or excessive animation.

### Evidence with provenance

Human picks, bot picks, simulations, and game outcomes answer different questions. CubeAI must label their origin and must never present bot assumptions as observed human behavior.

### Reproducibility

Cube versions, seeds, bot versions, configurations, and data-source snapshots are part of an experiment. A useful result can be reproduced and explained.

### Web-first, local-capable

Early versions should run with a small number of local commands and no account, while the primary frontend remains web-first. Frontend and application boundaries must permit future local storage and local adapters where justified, without creating a second frontend. PWA technology, service workers, browser storage, synchronization, replication, and desktop wrappers remain deferred until a working vertical slice establishes concrete requirements.

### Replaceable boundaries

External imports, metadata providers, persistence, bot strategies, and game engines sit behind explicit interfaces. CubeLab remains valuable even if gameplay integration is delayed or rejected.

## Non-goals

Early CubeAI will not provide:

- a general-purpose replacement for Arena, Magic Online, or Cockatrice;
- authentication, billing, social feeds, public matchmaking, or hosted accounts;
- production-grade cloud deployment or distributed services;
- ML-first draft bots;
- a custom comprehensive Magic rules engine;
- a commitment to Forge before feasibility and licensing research;
- authoritative conclusions that silently blend human and simulated data.

## Success progression

CubeAI succeeds incrementally when a user can first complete a correct local draft, then understand it, then simulate it, then evaluate Cube changes, and only later play games. Each milestone must leave a demonstrable, testable capability rather than only infrastructure.
