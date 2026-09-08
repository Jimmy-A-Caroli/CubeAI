# Existing MTG Draft Intelligence: Evidence Review

**Status: research evidence for a future human decision.** This is not an
accepted Bot v1 design, a data-use approval, or a licence opinion. It records
publicly described methods so CubeAI can independently design the smallest
credible contextual Bot without copying source code or ingesting data.

## Scope and method

This review uses repository code/readmes, author-written material, and the
original Ward et al. paper. Source URLs were checked on 2026-09-08. A public
repository, dataset URL, or model export is not treated as a reuse grant. In
particular, *algorithm*, *source code*, *training data*, and *weights* are
separate assets.

CubeAI's current baseline is materially simpler than every contextual source:
`raw-ranking-v0` chooses the highest static Oracle-ID prior in the legal pack;
an unlisted card receives the declared fallback; equal scores use stable
instance-ID order. It records the selected score, artifact, lookup outcome,
and tie-break, but no candidate score vector or pool-context contribution.
See [the Bot v0 policy](m1-012-bot-v0-rating-policy.md).

## Sources investigated

| Source | Algorithmic contribution | Code/data/model availability and rights posture | CubeAI lesson |
|---|---|---|---|
| [MagicDraftBot](https://github.com/RyanSaxe/MagicDraftBot) and [Saxe's technical article](https://draftsim.com/ryan-saxe-bot-model/) | Learns card-by-archetype ranks from clustered final pools; current pool supplies archetype pull; a learned monotone time term keeps all paths viable early. | Repository has no licence file: **CAN STUDY / REIMPLEMENT INDEPENDENTLY**, not copy. The author says the draft data and trained model cannot be shared: **unavailable/UNKNOWN**. | Pool-derived multi-path preference plus an explicit openness schedule is the clearest evidence for avoiding premature commitment. |
| [Draftsim methodology](https://draftsim.com/methodology/) | Simple static 0--5 rating with small early colour bias and later two-colour commitment bonus. | Method prose may be cited; it is not a code/data licence. **CAN STUDY / REIMPLEMENT INDEPENDENTLY**. | A deliberately staged heuristic can be valuable before a learned ranker, but colour-only commitment is a lower-fidelity baseline. |
| [madrury/mtg-draftbot](https://github.com/madrury/mtg-draftbot) | Explicit card-by-archetype weight matrix and a drafter preference vector updated by selected cards. | `setup.py` declares BSD but no repository licence text was found ([metadata](https://raw.githubusercontent.com/madrury/mtg-draftbot/master/setup.py)): **UNKNOWN / NEEDS_PERMISSION**. No reusable data/weights identified. | Explicit vectors make state and candidate contributions inspectable. |
| [Ward et al.](https://arxiv.org/abs/2009.00655) and [associated repository](https://github.com/khakhalin/MTG) | Compares rarity, expert colour-commitment heuristic, Naive Bayes, and a pack-masked neural chooser. | Paper/associated README identify Draftsim M19 data as CC BY 4.0; that still needs attribution and a separate provenance/format decision. Repository has no clear licence; **study only**. No reusable checkpoint found. | Interpretable heuristic and Bayes baselines are worth evaluating before neural work; agreement with recorded picks is not deck strength. |
| [CubeCobraML](https://github.com/dekkerglen/CubeCobraML) | Sparse multi-hot shared encoder with cube, draft, deckbuild, and correlation heads; draft head consumes pool and offered pack. | No repository licence found: code **UNKNOWN / NEEDS_PERMISSION**. Public CubeCobra exports and any weights have no established CubeAI use/redistribution grant: **UNKNOWN**. | Cube-native learned reference, but its full-cube context did not measurably help that draft head and it has no human-readable rationale. |
| [Draft Omen](https://github.com/andreagrandi/draftomen), [scoring specification](https://github.com/andreagrandi/draftomen/blob/master/docs/pick-scoring.md), [audit log](https://github.com/andreagrandi/draftomen/blob/master/docs/draft-audit-log.md) | Deterministic rating plus bounded pool, colour, role, urgency, redundancy, payoff, fixing, and tie-break terms; immutable candidate rationale ledger. | Code is [MIT](https://raw.githubusercontent.com/andreagrandi/draftomen/master/LICENSE): **CAN_REUSE** only with required notices and an independent dependency review. Its Scryfall/17Lands inputs retain their own terms; no data/model grant follows from the code. | Best explainability and provenance pattern: record every candidate factor and missing-data fallback at decision time. |
| [RyanSaxe/mtg](https://github.com/RyanSaxe/mtg) | Later Transformer-era drafter/deckbuilder research. | Code is [Apache-2.0](https://github.com/RyanSaxe/mtg/blob/main/LICENSE): potentially reusable only with notices and an independent review. It ships no pretrained draft model and no training-data grant. | A possible experimental learned track, not an explainable production baseline. |

### Rights matrix

| Source asset | Code licence / reuse | Dataset licence / reuse | Model-artifact rights / reuse | Present CubeAI classification |
|---|---|---|---|---|
| MagicDraftBot | no `LICENSE` in reviewed repository; no copy | author says data cannot be shared | author says trained model cannot be shared | **CAN_STUDY / REIMPLEMENT INDEPENDENTLY** |
| Draftsim methodology prose | no software grant | none conveyed | none conveyed | **CAN_STUDY / REIMPLEMENT INDEPENDENTLY** |
| madrury code | BSD declaration in setup metadata but no licence text; do not treat as settled | no grant identified | none identified | **UNKNOWN** |
| Ward associated code | no licence found in reviewed repository | n/a | no reusable checkpoint found | **UNKNOWN** |
| Ward/Draftsim M19 dataset | n/a | CC BY 4.0 is stated by [the associated README](https://github.com/khakhalin/MTG) and [paper](https://ieee-cog.org/2021/assets/papers/paper_27.pdf); attribution/use review still required | n/a | **NEEDS_PERMISSION** before CubeAI ingestion decision |
| CubeCobraML code | no `LICENSE` found in reviewed repository | n/a | n/a | **UNKNOWN** |
| CubeCobraML exports/data | n/a | accessibility is not a documented reuse grant | model/export terms not stated | **UNKNOWN** |
| Draft Omen code | MIT; notices and dependency review required | n/a | no learned model | **CAN_REUSE** for code only |
| Draft Omen upstream data | n/a | Scryfall/17Lands terms apply separately | n/a | **UNKNOWN** |
| RyanSaxe/mtg code | Apache-2.0; notices and independent review required | no grant | no pretrained draft model supplied | **CAN_REUSE** for code only |
| RyanSaxe/mtg data/model | n/a | bring-your-own, no grant | no supplied checkpoint | **UNKNOWN** |

This is a conservative engineering classification, not legal advice. Magic card
names, rules, images, and provider metadata are likewise outside all of these
software licences.

## How the principal approaches work

### Saxe: learned archetype ranks plus decaying openness

For one Limited format, Saxe clusters completed final pools into archetypes,
learns a card-by-archetype rank matrix from later picks, and lets the current
pool produce an archetype pull. A non-negative, monotone-decreasing opening
term is added to every archetype pull, intentionally damping early commitment.
It is not a table-signal model.

An independent abstraction is:

```text
fit(final pools, later observed picks):
  A = cluster(final-pool features)
  R[card, archetype] = learn relative observed-pick preference per A
  lambda[t] = constrained decreasing openness schedule

choose(pool D, legal pack P, pick t):
  pull[a] = max(0, sum(R[d, a] for d in D)) + lambda[t]
  score[c] = max(0, sum(pull[a] * R[c, a] for a in archetypes))
  return stable_argmax(score[c] for c in P)
```

The reported data were over 80,000 Throne of Eldraine simulator drafts, reduced
to roughly 45,000 usable drafts / two million picks; evaluation was whole-draft
80/20 split agreement with recorded picks (reported 63% exact and 83% top-two),
not game outcomes. The article reports the openness version reduced first-pick
castability relative to the no-openness version, which is evidence of behavior
in that experiment, not a Vintage Cube quality result. The source explicitly
does not model direct card-pair synergy, curve/deck construction, or table
signals. [Article](https://draftsim.com/ryan-saxe-bot-model/),
[model](https://raw.githubusercontent.com/RyanSaxe/MagicDraftBot/master/models.py),
[preprocessing](https://raw.githubusercontent.com/RyanSaxe/MagicDraftBot/master/preprocessing.py).

### madrury: explicit preference-vector simulator

The simulator makes the latent state unusually legible. Let `W[c,a]` be a
static card-to-archetype matrix and `q[a]` a drafter preference vector:

```text
q = ones(archetypes)
for each selected card d:
  score[c] = dot(W[c], q) for c in offered pack
  choose from a defined distribution/ranking
  q = q + W[selected]
```

Its learning formulation consumes a pack availability vector and own-pool
counts, derives a preference vector from pool counts, masks unavailable cards,
and optimizes observed-pick likelihood. It retains options and picks in the
simulated history, but has no explicit opponent/signalling state. This supports
the *representation* idea, not reuse of its code or training setup. [Repository
and model code](https://github.com/madrury/mtg-draftbot).

### Ward et al.: useful interpretable baselines before neural work

The paper studies 107,949 human Draftsim M19 drafts (80/20 whole-draft split;
265-card set) and measures top-1 imitation, not match or deck quality. The
agents see legal pack plus own prior collection:

| Agent | Core rule | Reported bot accuracy |
|---|---|---|
| Random | uniform legal candidate | 22.15% |
| Rarity | highest rarity | 30.53% |
| DraftsimBot | expert 0--5 strength plus staged colour commitment | 44.54% |
| Naive Bayes | conditional pick relations to pack/pool cards | 43.35% |
| Neural network | collection count vector to masked card logits | 48.67% |

The neural model has three dense 265-wide layers with masked legal choice;
it is not evidence that a neural model is required. Its separately reported
unmasked prediction figure must not be confused with the legal-choice bot
accuracy. None of these agents models opponents, future packs, deck games, or
Cube transfer. [Paper](https://ieee-cog.org/2021/assets/papers/paper_27.pdf).

### CubeCobraML: cube-native learned pool-and-pack model

CubeCobraML describes a shared sparse multi-hot encoder (`embedding -> 512 ->
256 ReLU -> 128`) with cube recommender, draft, deckbuild, and correlation
heads. The draft head scores a pool encoding against a pack mask. The project
documents that a supplied full-cube context did not add measurable value and
was removed for stability; it retains no explicit sequence encoder beyond the
accumulated pool. Its reported top-1/top-3 figures are author-reported
imitation diagnostics, not outcome evidence. Its public exports include cubes,
picks, decks, and metadata, but availability does not settle consent or reuse.
[Architecture and data documentation](https://github.com/dekkerglen/CubeCobraML#architecture).
Maintenance/status is **UNKNOWN as of 2026-09-08**: this review verified public
documentation, not a release/support commitment or a pinned activity history.

### Draft Omen: a modern explainable heuristic

Draft Omen is an important counterexample to "context requires ML." Its base
score uses observed-format statistics; bounded context adds colour commitment,
role need, late urgency, package support, redundancy, unsupported payoff, and
fixing. It preserves a pre-pick pool ledger and append-only audit evidence for
every candidate, including source versions, fallbacks, contributions, rank,
and tie-break. It explicitly calls its trophy-pick benchmark calibration, not
proof of objective correctness. This audit style is directly useful; its
17Lands-driven Limited assumptions are not Vintage Cube evidence. [Scoring
contract](https://github.com/andreagrandi/draftomen/blob/master/docs/pick-scoring.md),
[audit contract](https://github.com/andreagrandi/draftomen/blob/master/docs/draft-audit-log.md),
and [benchmark boundary](https://github.com/andreagrandi/draftomen/blob/master/docs/benchmarking.md#default-ranking-decision).

### Draftgoblin and additional-source limit

[Draftgoblin](https://github.com/andreagrandi/draftgoblin) is a public,
read-only terminal Arena Quick Draft assistant. Its README documents live pack
recognition, raw 17Lands win-rate/grade plus a pool-aware score, and a suggested
deck; it uses Scryfall and 17Lands inputs. The reviewed README does not provide
the factor-level scoring/audit specification that Draft Omen does, and its
code/data/model rights were not independently established in this wave:
**UNKNOWN**. It is therefore a corroborating explainability lead, not a second
architecture-evidence row. No unlimited repository survey was conducted.

## Comparison matrix

`Yes` means a described mechanism, not quality. `—` means absent/not documented.

| Dimension | CubeAI v0 | Draftsim heuristic | Saxe | madrury | Ward expert | Ward Bayes | Ward neural | CubeCobraML | Draft Omen |
|---|---|---|---|---|---|---|---|
| Static power | Yes | Yes | learned ranks | W matrix | expert | relations | learned | learned | statistical base |
| Current pool | — | colour only | Yes | Yes | colour | Yes | Yes | Yes | Yes |
| Pick position | — | staged | lambda(t) | not central | staged | — | — | not explicit | urgency term |
| Staying open / commitment | — | simple stages | decaying global openness | accumulating q | stages | — | — | implicit only | colour/splash rules |
| Colours | — | Yes | implicit clusters | W dependent | Yes | — | implicit | learned | Yes |
| Archetypes / roles | — | — | learned clusters | explicit latent W | — | — | — | latent embedding | authored roles/packages |
| Curve / fixing | — | — | — | — | — | — | — | — | bounded deck/need terms |
| Direct card-pair synergy | — | — | — | only through W | — | conditional relation | — | embedding correlation | package evidence |
| Seen cards / table signals | — | — | — | — | — | — | — | — | open-pick tiebreak only |
| Pack context | legal candidates | legal candidates | mask | options | pack | pack | mask | pack mask | pack |
| Cube-specific context | raw artifact only | format rating | set-specific | format matrix | set-specific | set-specific | set-specific | training cube; removed from draft head | set profile |
| Learned parameters / data | static artifact | no | Yes / required | optional | no | required | required | Yes / required | source stats required |
| Explainability | selected score only | simple rule | matrix/pull | high | high | medium | low | diagnostics, not rationale | high ledger |
| Determinism / reproducibility | Yes | can be | can be | simulator samples | yes | yes | seed-sensitive | trained model | Yes |
| Code/data reuse rights | CubeAI-owned | method only | code/data/weights unavailable | unclear | code unclear | code unclear | code unclear | unclear / unknown | MIT code / external data terms |
| Vintage Cube applicability | direct baseline | weak transfer | needs retraining | needs Cube matrix | Limited-only | Limited-only | Limited-only | Cube-native but rights/model risk | Limited-only evidence |
| Complexity | low | low | high | medium | low | medium | high | high | medium |

## Findings relevant to CubeAI

1. **Staying open is best represented explicitly.** The strongest direct
   precedent is Saxe's decreasing all-path prior. It preserves a distribution
   of plausible paths until pool evidence overwhelms it; it is simpler and more
   inspectable than entropy tuning or inferred table beliefs.
2. **Use multiple paths, not one selected archetype.** A non-negative,
   versioned vector over reviewed Cube-specific archetypes can represent
   `reanimator plausible; artifacts plausible; control plausible` without
   claiming a factual archetype identity.
3. **Archetype affinity and direct synergy are different.** Bot v1 can use
   reviewed role/archetype associations. Pairwise synergy matrices should be a
   later experiment because they need stronger evidence and create explanation
   and rights complexity.
4. **Signals should be deferred.** M2-001/M2-002 show only seat-visible facts,
   but a trustworthy closed-archetype/signalling policy requires its own
   definition, calibration, and tests. No required Bot v1 mechanism needs it.
5. **Curve/fixing should be deferred.** They require accepted M2-004 facts and
   M2-005 semantics. Adding them now would turn a contextual baseline into an
   unreviewed deckbuilder.
6. **Imitation is not quality.** Use human review and controlled comparisons as
   calibration, never as a training pipeline or proof of better gameplay.

## References

- Saxe, [Bot Drafting the Hard Way](https://draftsim.com/ryan-saxe-bot-model/);
  [MagicDraftBot README](https://github.com/RyanSaxe/MagicDraftBot/blob/master/README.md).
- Ward et al., [AI solutions for drafting in Magic: the Gathering](https://arxiv.org/abs/2009.00655).
- [CubeCobraML README](https://github.com/dekkerglen/CubeCobraML#how-training-works).
- [Draft Omen scoring](https://github.com/andreagrandi/draftomen/blob/master/docs/pick-scoring.md) and [benchmark boundary](https://github.com/andreagrandi/draftomen/blob/master/docs/benchmarking.md#default-ranking-decision).

### Traceability note

External repository citations above identify the exact repository and
file/section checked on 2026-09-08. They are intentionally not treated as
immutable implementation dependencies: before any code, data, or model reuse,
a separate approval must capture the then-current commit SHA, licence text, and
applicable upstream terms. That is necessary because no external asset is being
adopted by this proposal.
