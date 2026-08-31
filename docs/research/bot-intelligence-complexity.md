# Draft bot intelligence complexity

## Question

What information may a fair CubeAI draft bot use, how does complexity increase
from transparent rules to learned context, and what evidence is required before
the project can claim that one strategy performs better rather than merely acts
differently?

## Methodology

This report maps the seat-safe draft boundary in the product definition,
architecture, M1/M2 milestones, and initial backlog onto four strategy stages.
It also interprets the synthetic draft, bot, analytics, and storage experiments
without treating their non-production models as future interfaces or quality
benchmarks.

The classification is decision-relative: an input is classified according to
what the acting seat may know immediately before one pick. The benchmark runner
may hold complete draft truth to advance and score a scenario, but possession by
the runner does not make that truth a legal strategy input. The four classes are:

- **Observable:** part of the acting seat's declared, player-safe state.
- **Derived:** reproducibly computed only from observable state available by
  that decision; it contains no later or hidden facts.
- **Unknown/private:** belongs to another seat or has not been revealed.
- **Simulation-only:** runner metadata or hidden world state needed to generate,
  replay, or audit a scenario, but excluded from the strategy input.

These classes define an information contract, not a production DTO. M1-012 must
still define the actual bot port after the draft domain exists.

## Observable state

The minimum bot input is a seat-safe snapshot. “Known” never means “present
somewhere in the process”; it means disclosed to the acting seat by the draft
rules and scenario contract at that decision.

| Input | Class at decision time | Fair-benchmark treatment |
|---|---|---|
| Current pack | Observable | Supply the exact card instances currently offered to the acting seat, before removal of its choice. Do not include any other seat's current pack. |
| Previous picks | Observable for the acting seat; unknown/private for other seats | Supply the acting seat's ordered chosen instances if the strategy version declares that history. Public pick counts may be supplied separately. Never supply another seat's exact choices merely because the runner recorded them. |
| Drafted pool | Observable for the acting seat; unknown/private for other seats | Supply only the acting seat's pool as of the decision. It is equivalent to that seat's completed picks, not a later final pool. |
| Pack/pick number | Observable | Supply current pack number, pick number, seat, draft geometry, and public passing direction using explicit, consistently indexed fields. |
| Cards previously seen | Derived | Reconstruct only from packs previously exposed to this seat and immutable events at or before the decision. This is M2 history, not a Bot v0 requirement. |
| Wheels | Derived | Detect from a card instance returning to the same seat under a documented seat-count-aware definition. Never infer a wheel from later events during an earlier decision. |
| Known Cube list | Observable scenario context when declared | A benchmark may disclose the immutable Cube version and card metadata equally to all strategies. This reveals possible contents, not the shuffled allocation, future order, or exact location of remaining instances. Private or blind-list formats must instead declare the list unavailable. |
| Other pools | Unknown/private | Other seats' exact drafted pools are prohibited inputs, including when all seats are bots controlled by one process. Aggregate public progress is not an exact pool. |
| Future order | Simulation-only | Pack allocation, future pack contents/order, future passes, and future choices are hidden runner state. A strategy may know rotation rules, but must not inspect the realized future. |
| Strategy internals | Simulation-only and strategy-private | The runner records the acting strategy ID, version, configuration, and RNG provenance for reproducibility. A strategy may use its own configured state, but competitors' weights, memory, scores, and random state are not draft observations or legal cross-strategy inputs. |
| Card metadata and declared ratings/tags | Observable scenario context when versioned | Give every compared strategy the same declared snapshot it is entitled to use. Missing values and custom cards must have explicit behavior; no live refresh may differ between paired runs. |
| Public draft geometry and rotation rules | Observable | Seats, packs per seat, pack size, current direction, and rules are shared configuration. Exact pack locations beyond the current seat-safe view remain hidden. |
| Other seats' current packs and exact previous picks | Unknown/private | Exclude them even if an offline replay can reconstruct them. A returned card reveals only what the acting seat has actually seen. |
| Allocation seed, runner RNG state, and unopened packs | Simulation-only | Record them for replay, but do not expose a seed or RNG stream that lets a strategy reconstruct hidden allocations. Strategy randomness must use a separately derived, recorded stream. |
| Later picks, final pools, decks, and game results | Unknown/private at the decision; post-run evaluation data later | They may label or evaluate a completed example only after the decision trace is frozen. They must never be backfilled into that decision's feature vector. |

An openly published Cube list permits uncertainty-aware deductions such as
“these instances could still be available.” It does not permit subtraction of
other exact pools, inspection of unopened packs, or reconstruction of a hidden
allocation seed. Benchmarks must state whether the Cube list and each metadata
snapshot are disclosed so that strategies are compared under the same rules.

## Derived features

Derived inputs must be deterministic functions of the acting seat's observable
history truncated at the current decision. Candidate M2/M3 features include:

- color counts, color share, color commitment, mana-value curve, mana
  requirements, and possible sources from the current pool;
- cards-seen history and instance-aware wheel indicators from prior visible
  packs;
- rating, curve, color, tag, archetype, synergy, and pool-fit contributions for
  each legal current-pack choice;
- uncertainty-aware signals such as the frequency of a color in packs already
  seen by this seat, without interpreting unseen cards as evidence; and
- the strategy's prior scores or declared memory, provided that state was built
  only from legal earlier inputs and is included in strategy versioning and
  replay.

M2 establishes definitions and projections for several of these features. It
does not make them empirical measures of card quality. Advice must keep power,
openness, curve, synergy, and pool fit separate and expose missing data,
definitions, contributions, and uncertainty.

Feature computation must preserve instance identity. Duplicate names do not
prove that the same `DraftCardInstance` returned, and a known `CubeVersion`
membership is not interchangeable with a pick, drafted instance, or game
object. Human, bot, simulation, and later gameplay origins remain explicit
dimensions and are not blended by default.

## Unknown and private information

A live or replayed decision must exclude other seats' exact current packs,
picks, drafted pools, private annotations, and strategy state. It must also
exclude the realized contents and order of packs that the seat has not yet
seen. The runner may retain all of this to execute the draft, verify
conservation, and calculate post-run metrics; the strategy receives only a
seat-safe projection.

The following are prohibited in a fair benchmark:

- **look-ahead** into later pick events, final pools, deck builds, game results,
  unopened packs, or the realized future pack order;
- access to **other exact pools**, exact opponent picks, or another seat's
  current pack, even in all-bot simulation;
- use of allocation seeds or shared RNG state to reconstruct hidden order;
- features calculated over the complete draft and then attached to an earlier
  decision without point-in-time truncation; and
- training/test overlap through the same draft, Cube version snapshot, near-
  duplicate replay, player identity, or future revision where that overlap
  lets the model recover the held-out choice or outcome.

Unknown is not equivalent to zero or absent. Missing ratings, tags, histories,
or outcomes require an explicit unknown representation and diagnosable
fallback rather than silent imputation from hidden data.

## Fair benchmark contract

A fixed scenario should materialize one decision trace per seat containing
only the observable snapshot and derived features valid at that time. The
runner owns the full draft state and validates a returned choice against the
current pack. For paired strategy comparisons it holds constant the immutable
Cube version, draft geometry, seat assignment policy, metadata snapshots, and
seed set. If strategy randomness is allowed, each named strategy gets a stable,
independent RNG derivation that cannot reveal allocation state.

Every result records Cube version, scenario/seed set, seat, strategy ID and
version, configuration, rating/tag snapshot, feature-schema version, code/result
schema version, and origin. Benchmarks first verify legal choices,
deterministic replay, visibility, and explanations. They may then compare
declared draft proxies such as curve or archetype coherence, but those proxies
must be named as strategy-dependent measurements rather than win rate,
human-likeness, or objective card quality.

Historical replay uses the same boundary: construct features only from facts
available before the recorded choice. Time-based and grouped splits must keep
one draft and materially duplicated scenarios in one partition. Human, bot,
and simulation decisions are separate populations unless an explicit
comparison requests otherwise.

## Model progression and data requirements

The intended progression is **heuristic → weighted → learned ranking → contextual**; each stage adds data, validation, and governance obligations rather than replacing the information boundary.

| Stage | Required labels/data | Minimum evaluation | Explainability | Compute expectation | Leakage risks | Licensing and provenance risks | Are gameplay outcomes required? |
|---|---|---|---|---|---|---|---|
| Heuristic | Versioned card ratings and deterministic fallback/tie rules; no training labels | Unit and golden scenarios for legal ordering, ties, missing values, duplicate instances, visibility, and replay; fixed Cube/seed benchmark against itself and named baselines | High: emit rating, fallback, tie-break, and chosen-card reason | Low local inference; no training | Hidden cards accidentally present in a broad state object; mutable/live rating refresh; global RNG revealing allocation | Rating source, license, allowed redistribution/derivation, snapshot date, and custom-card policy must be approved | No for operation or reproducibility. Yes before claiming better draft/game performance. |
| Weighted features | Versioned ratings plus point-in-time M2 features and human-authored weights; labels are unnecessary unless weights are tuned | All heuristic checks plus fixed feature scenarios, contribution/ablation checks, paired Cube/seed comparisons, and sensitivity to missing tags/ratings | High when each normalized feature, weight, contribution, cap, and uncertainty is emitted | Low for the simple bounded features measured so far; recomputation and large tag sets need measurement | Hindsight wheels, final-pool curve, later tags, other pools, or full-draft aggregates entering an earlier score | Rating and tag vocabularies need source, version, confidence, override, and license; tuned weights inherit dataset provenance | No for feature correctness or proxy comparison. Yes before claiming stronger decks or gameplay performance. |
| Learned ranking | Point-in-time choice sets, chosen card/rank labels, legal alternatives, and context with Cube, actor, origin, strategy, and time provenance; optional outcome labels kept distinct | Compare with heuristic/weighted baselines on grouped and time-held-out Cubes/drafts; ranking metrics, calibration where applicable, slice/error analysis, reproducibility, and visibility audit | Medium: candidate scores, feature/schema/model versions, examples, and attribution can be shown, but attribution is not a causal explanation | Training and local inference are unmeasured; expect materially more storage/tooling and measure latency, memory, artifact size, and retraining cost before adoption | Same-draft rows across splits, later picks/final pool, data generated by the evaluated bot, duplicate Cubes, player memorization, and post-period metadata | Historical draft availability, consent/privacy, redistribution, rating/tag licenses, generated labels, model-artifact license, and human/bot/simulation separation are unresolved | Historical picks can train and measure behavior imitation, not performance. Gameplay outcomes are required for performance claims. |
| Contextual model | Ordered point-in-time trajectories and masks; potentially card text/tags, prior visible packs, own pool, deck construction, and separately proven gameplay outcomes | All learned-ranking checks plus trajectory-grouped/time/Cube holdouts, strict causal masks, paired online/simulation evaluation, ablations, robustness, and eventual independent gameplay evaluation | Medium to low: disclose model/data/schema versions, inputs, masks, confidence, counterfactual tests, and limitations; do not call attention causal | Highest and unmeasured: sequence training, artifact storage, inference budget, and reproducible local execution all need a dedicated spike | Future-token/trajectory leakage, final deck or outcome leakage, other seats' state, outcome-conditioned preprocessing, and simulator-policy feedback loops | All ranking risks plus card-text embeddings/models, pretrained weights, engine/game logs, deck builders, and outcome dataset terms/provenance | No for a narrowly stated behavior model. Yes for any claim of strategic or gameplay performance and for outcome-optimized training claims. |

Historical picks measure behavior: they can test whether a model predicts or
resembles the choices represented in a defined historical population. They do
not establish that those choices create stronger pools, better decks, or more
wins. Even agreement with expert picks remains a behavioral or preference
claim unless the label itself has a separately validated outcome meaning.

Gameplay outcomes are required for performance claims. That evidence must link
point-in-time draft decisions through a documented deck-construction policy to
games with engine/version, opponent, seat/play-draw, randomness, configuration,
and outcome provenance. Paired or otherwise controlled comparisons are needed
to reduce deck builder, opponent policy, and game-engine effects. Pick-rate,
wheel, utilization, curve, and coherence metrics are not substitutes for such
outcomes.

## Observations

The major complexity boundary is data validity, not choosing a sophisticated
algorithm. Bot v0 and manually weighted features can be deterministic functions
of a small player-safe input. Learned ranking introduces historical choice
availability, point-in-time reconstruction, representative sampling, grouped
splits, licensing, and behavior-only interpretation. Contextual models add
trajectory masks, substantially larger artifacts, more difficult explanations,
and feedback between simulator policy and evaluation.

The current architecture already supplies the right guardrails: bot decisions
depend on visible state plus a named version/configuration/RNG state; API views
are seat-safe; immutable events preserve what a seat saw; and origins remain
queryable. The main implementation risk is bypassing those boundaries by
handing a strategy a convenient in-process draft aggregate containing private
runner state.

The known Cube list is not itself unfair when it is a declared part of the
format and equally available. The unfair step is converting complete runner
knowledge into exact depletion, pack-location, or future-order features that a
seat could not calculate from its own observations.

## Measurements

This task adds no new executable benchmark. The complexity ratings below are
qualitative planning measurements grounded where possible in the committed
synthetic experiments; they are not production estimates or model-quality
results.

| Stage | Data readiness | Inference compute | Training compute | Evaluation complexity | Evidence status |
|---|---|---|---|---|---|
| Heuristic | Medium risk: a licensed rating source remains a human decision | Low | None | Low | Measured only for synthetic raw ratings: `bot0` averaged 394.8 standard drafts/s at 10,000 drafts. |
| Weighted | Medium-high risk: M2 features/tags do not yet exist and require versioned definitions | Low for currently tested bounded features | None unless weights are fitted | Medium | Synthetic color and curve strategies averaged 148.2 and 130.5 drafts/s at 10,000 drafts; the slowest repetition finished in 78.43 s. |
| Learned ranking | High risk: no approved representative choice dataset | Unknown | Unknown, likely material relative to heuristics | High | Not implemented or measured. Historical dataset availability and licensing remain R-003/R-005 questions. |
| Contextual | Very high risk: trajectories, masks, deck/game linkage, and valid outcomes are unavailable | Unknown | Unknown and highest of the four stages | Very high | Not implemented or measured; gameplay and deck construction are later independent workstreams. |

The bot experiment measured transparent scoring on synthetic card IDs in one
sequential CPython process. It did not measure real card parsing, tags, model
quality, training, persistence, UI work, or total process memory. Its result
supports keeping early strategies sequential and explainable, not a claim that
all weighted features will be cheap.

The draft-engine probe measured 111.9 standard 8 × 3 × 15 drafts/s without the
three bot scorers. The analytics probe showed that simple derived metrics can
be computed reproducibly, but its 10,000-case result used a 1-seat × 1-pack ×
3-card micro-workload and cannot size a production feature service. The storage
probe found that seen-card rows dominated its standard-draft compact event
sample (about 79% of NDJSON bytes), a warning that trajectory datasets can be
substantially larger than chosen-card labels alone. None of these probes
measured learned or contextual training/inference.

## Limitations

This is a boundary and complexity map, not a bot design, dataset approval,
model proposal, or production interface. It does not select a rating source,
feature normalization, archetype vocabulary, learning objective, library,
model family, storage system, deck builder, or gameplay engine. The fair-state
rules may need format-specific refinement for drafts that intentionally reveal
different information, but any exception must be explicit and consistent for
all strategies.

The measured bots use synthetic rating, color, mana-value, and archetype fields
with deliberately simple scanning. Their throughput does not project to card
text models, embeddings, large tag graphs, training, or gameplay. Historical
pick and gameplay datasets have not been inspected, so availability,
representativeness, consent, retention, and legal usability remain unknown.

## Risks

- A broad domain or persistence object passed directly to a strategy can leak
  other pools, unopened packs, allocation seeds, or later events despite a
  seat-safe UI.
- Point-in-time errors can make offline ranking results look strong through
  final-pool, wheel, later-pick, metadata-revision, or outcome leakage.
- Self-play data can reward agreement with the generating bot and then be
  mislabeled as human behavior or independent performance.
- Historical choices may overrepresent particular Cubes, players, rating eras,
  or platforms and may be impossible to redistribute or use for training.
- Explanatory feature attribution for a learned model may appear authoritative
  without being causal, stable, or actionable.
- Draft proxies can optimize visibly tidy pools while reducing actual deck or
  gameplay performance; outcome pipelines can also confound the draft bot with
  deck construction and game policy.
- Learned/contextual tooling can create an incidental major dependency,
  artifact license, privacy obligation, or local resource requirement before
  the product has justified it.

## Recommendation

Keep M1 Bot v0 as a deterministic raw-rating heuristic behind a visible-state
strategy port. Its required data is a versioned rating snapshot with an
approved source/license, missing-rating fallback, score explanation, and stable
tie-breaking; it needs no training dataset. Tests should construct a minimal
seat-safe input so hidden runner fields cannot enter by convenience.

Use M2 to define and verify point-in-time derived features and their provenance,
not to optimize bots or assert performance. M3 may then implement and benchmark
named heuristic and manually weighted strategies over fixed Cube versions and
paired seed sets, with explanations and strict visibility tests. Retain
sequential execution until a realistic strategy misses a measured requirement.

Defer learned ranking and contextual ML to a separate human-reviewed proposal
after R-003/R-005 resolve dataset availability, provenance, consent/privacy,
redistribution/training/model licenses, and representative coverage. That
proposal must name the objective (behavior imitation versus performance),
point-in-time schema, split policy, baselines, evaluation slices, compute and
artifact budgets, reproducibility contract, explanation limits, and—if it
makes a performance claim—the deck/game outcome design. No ML dependency or
training artifact should enter M1–M3 incidentally.

## Roadmap/backlog impact

- **M1:** M1-012 remains a human-owned rating source/license decision. Bot v0
  needs ratings and deterministic policy data but no training data. M1-013
  keeps decisions reproducible and seat-safe; cards-seen analysis, wheels,
  advanced features, and ML remain out of scope.
- **M2:** M2-001/M2-002 provide instance-aware seen-card and wheel derivations;
  M2-004 through M2-007 define explainable pool/curve/mana/tag/fit features;
  M2-009/M2-010 preserve origins and metric denominators. These are feature and
  analysis foundations, not optimized-bot or win-rate work.
- **M3:** Benchmark externalized ratings, color, curve/mana, and then
  archetype/synergy strategies behind the existing bot port. Compare named
  versions on fixed scenarios and paired seed sets without human-likeness or
  gameplay-performance claims.
- **M4 and later:** Simulation can scale reproducible strategy comparison while
  keeping human and simulated evidence separate. Deck construction and
  gameplay outcomes are later prerequisites for performance claims, not reasons
  to pull a game engine into the bot milestones.
- **ML proposal:** Remains deferred until R-003 and R-005 resolve data
  provenance/licensing and a later proposal passes human review. This report
  does not make an issue ready, select a dataset, or change milestone scope.

Related evidence: [product definition](../PRODUCT.md),
[architecture](../ARCHITECTURE.md), [roadmap](../ROADMAP.md),
[M1 milestone](../milestones/M1-LOCAL-DRAFT-MVP.md),
[M2 milestone](../milestones/M2-DRAFT-INTELLIGENCE.md),
[bot simulation baseline](bot-simulation-baseline.md),
[draft-engine spike](draft-engine-spike.md),
[analytics compute spike](analytics-compute-spike.md), and
[simulation data-volume spike](simulation-data-volume.md).
