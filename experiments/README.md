# CubeAI experiments

**Non-production research code.** These standard-library-only probes use fixed
synthetic inputs and have no network, credentials, or private Cube data. They
are isolated from future production packages and do not establish production
interfaces or performance guarantees.

Run the retained-size probe:

```bash
python3 -m experiments.data_footprint --seed 20260828 --output experiments/results/data-footprint.json
```

Run the deterministic mechanics benchmark:

```bash
python3 -m experiments.draft_engine --seed 20260828 --repetitions 7 --output experiments/results/draft-engine.json
```

The draft engine uses integer-card mechanics. A chooser receives the visible
synthetic cards and the current pool, then returns an ID from that pack. Its
default chooser is deliberately mechanical (`max(card_id)`), while later
experiments may provide attribute-aware strategies.
