import { useEffect, useMemo, useState } from 'react';

import { CardArt, CardColours } from '../draft/CardDisplay';
import {
  type StrategicCurationApi,
  type StrategicCurationSession,
  type StrategicDecision,
  type StrategicProposal,
  type SupportLevel,
  localStrategicCurationApi,
} from './strategicCurationApi';
import './StrategicCurationPage.css';

type Props = { api?: StrategicCurationApi };
type Decisions = Record<string, SupportLevel>;

const supportLevels: SupportLevel[] = ['none', 'supports', 'strong'];

function proposalKey(
  proposal: Pick<
    StrategicProposal,
    'target_id' | 'identity_scope' | 'target_type' | 'target'
  >,
): string {
  return [
    proposal.target_id,
    proposal.identity_scope,
    proposal.target_type,
    proposal.target,
  ].join('|');
}

function draftKey(session: StrategicCurationSession): string {
  return `cubeai.strategic-curation.draft.v1:${session.cube_version_id}:${session.proposal_set_id}`;
}

function loadDraft(session: StrategicCurationSession): Decisions {
  const initial: Decisions = Object.fromEntries(
    session.cards.flatMap((card) =>
      card.relations.flatMap((relation) =>
        relation.current_support_level
          ? [[proposalKey(relation), relation.current_support_level]]
          : [],
      ),
    ),
  );
  try {
    const raw = window.localStorage.getItem(draftKey(session));
    if (!raw) return initial;
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed))
      return initial;
    const allowed = new Set(
      session.cards.flatMap((card) => card.relations.map(proposalKey)),
    );
    return {
      ...initial,
      ...Object.fromEntries(
        Object.entries(parsed).filter(
          ([key, value]) =>
            allowed.has(key) && supportLevels.includes(value as SupportLevel),
        ),
      ),
    };
  } catch {
    return initial;
  }
}

function download(document: object, filename: string): void {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(document, null, 2)], { type: 'application/json' }),
  );
  const link = window.document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function StrategicCurationPage({
  api = localStrategicCurationApi,
}: Props) {
  const [session, setSession] = useState<StrategicCurationSession | null>(null);
  const [decisions, setDecisions] = useState<Decisions>({});
  const [targetFilter, setTargetFilter] = useState('all');
  const [stateFilter, setStateFilter] = useState('all');
  const [cardIndex, setCardIndex] = useState(0);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let current = true;
    void api
      .loadSession()
      .then((loaded) => {
        if (!current) return;
        setSession(loaded);
        setDecisions(loadDraft(loaded));
      })
      .catch((requestError: unknown) => {
        if (current)
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Curation could not be loaded.',
          );
      });
    return () => {
      current = false;
    };
  }, [api]);

  useEffect(() => {
    if (!session) return;
    window.localStorage.setItem(draftKey(session), JSON.stringify(decisions));
  }, [decisions, session]);

  const relations = useMemo(
    () =>
      session?.cards.flatMap((card) =>
        card.relations.map((relation) => ({ ...relation, card: card.card })),
      ) ?? [],
    [session],
  );
  const filteredCards = useMemo(
    () =>
      session?.cards.filter((card) => {
        const fullyReviewed = card.relations.every(
          (relation) => decisions[proposalKey(relation)] !== undefined,
        );
        return (
          (targetFilter === 'all' ||
            card.relations.some(
              (relation) => relation.target === targetFilter,
            )) &&
          (stateFilter === 'all' ||
            (stateFilter === 'reviewed'
              ? fullyReviewed
              : stateFilter === 'unreviewed'
                ? !fullyReviewed
                : true))
        );
      }) ?? [],
    [decisions, session, stateFilter, targetFilter],
  );
  const targets = useMemo(
    () => [...new Set(relations.map((item) => item.target))],
    [relations],
  );
  const reviewed = Object.keys(decisions).length;

  const select = (
    proposal: Omit<StrategicProposal, 'card'>,
    level: SupportLevel | null,
  ) => {
    const key = proposalKey(proposal);
    setDecisions((previous) => {
      const next = { ...previous };
      if (level === null) delete next[key];
      else next[key] = level;
      return next;
    });
    setNotice(
      level === null
        ? 'Selection cleared; this proposal remains UNKNOWN.'
        : 'Unsent review saved in this browser.',
    );
  };

  const submit = async () => {
    if (!session) return;
    setSubmitting(true);
    setError('');
    const submitted: StrategicDecision[] = relations.flatMap((proposal) => {
      const support_level = decisions[proposalKey(proposal)];
      return support_level
        ? [
            {
              target_id: proposal.target_id,
              identity_scope: proposal.identity_scope,
              target_type: proposal.target_type,
              target: proposal.target,
              support_level,
            },
          ]
        : [];
    });
    try {
      const result = await api.submit(session, submitted);
      download(result.assignment_artifact, result.artifact_filename);
      download(result.coverage_report, result.coverage_filename);
      setNotice(
        `${result.reviewed_count} reviewed assignments; ${result.unknown_remaining} memberships remain UNKNOWN. Both JSON artifacts were downloaded and this browser draft remains saved.`,
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Submission failed; your local draft is retained.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (error && !session)
    return (
      <section className="curation" aria-labelledby="curation-title">
        <h1 id="curation-title">Strategic curation review</h1>
        <p role="alert">{error}</p>
      </section>
    );
  if (!session)
    return (
      <section className="curation" aria-labelledby="curation-title">
        <h1 id="curation-title">Strategic curation review</h1>
        <p role="status">Loading fixed review session…</p>
      </section>
    );

  return (
    <section className="curation" aria-labelledby="curation-title">
      <header>
        <p className="app-shell__eyebrow">Human review only</p>
        <h1 id="curation-title">Strategic curation review</h1>
        <p>
          Proposals are evidence, not assignments. Select only relationships you
          have reviewed; Skip leaves the relationship UNKNOWN.
        </p>
      </header>
      <div className="curation__filters">
        <label>
          Target{' '}
          <select
            value={targetFilter}
            onChange={(event) => setTargetFilter(event.target.value)}
          >
            <option value="all">All targets</option>
            {targets.map((target) => (
              <option key={target} value={target}>
                {target}
              </option>
            ))}
          </select>
        </label>
        <label>
          Review state{' '}
          <select
            value={stateFilter}
            onChange={(event) => setStateFilter(event.target.value)}
          >
            <option value="all">All</option>
            <option value="unreviewed">Needs review</option>
            <option value="reviewed">Fully reviewed</option>
          </select>
        </label>
        <p>
          {reviewed} reviewed / {session.target_cell_count - reviewed} reviewed
          target cells
        </p>
      </div>
      <p aria-live="polite" className="curation__notice">
        {notice}
      </p>
      {error ? <p role="alert">{error}</p> : null}
      <div className="curation__list">
        {filteredCards.length === 0 ? (
          <p>No cards match these filters.</p>
        ) : (
          [filteredCards[Math.min(cardIndex, filteredCards.length - 1)]].map(
            (card) => {
              const proposal = { ...card.relations[0], card: card.card };
              return (
                <article className="curation-card" key={card.target_id}>
                  <CardArt
                    card={{
                      ...proposal.card,
                      mana_cost:
                        proposal.card.mana_value === null
                          ? null
                          : `{${proposal.card.mana_value}}`,
                      oracle_text: null,
                      power: null,
                      toughness: null,
                      loyalty: null,
                    }}
                    compact
                  />
                  <div>
                    <h2>{proposal.card.name}</h2>
                    <CardColours
                      card={{
                        ...proposal.card,
                        mana_cost: null,
                        oracle_text: null,
                        power: null,
                        toughness: null,
                        loyalty: null,
                      }}
                    />
                    <p>{proposal.card.type_line}</p>
                    {(['macro_path', 'package'] as const).map((targetType) => {
                      const relations = card.relations.filter(
                        (relation) =>
                          relation.target_type === targetType &&
                          (targetFilter === 'all' ||
                            relation.target === targetFilter),
                      );
                      if (relations.length === 0) return null;
                      return (
                        <section
                          className="curation-target-group"
                          key={targetType}
                          aria-labelledby={`${card.target_id}-${targetType}`}
                        >
                          <h3 id={`${card.target_id}-${targetType}`}>
                            {targetType === 'macro_path'
                              ? 'Macro paths'
                              : 'Packages'}
                          </h3>
                          <div className="curation-target-grid">
                            {relations.map((relation) => {
                              const relationKey = proposalKey(relation);
                              const selected = decisions[relationKey];
                              return (
                                <section
                                  className={`curation-target${selected ? ` curation-target--${selected}` : ''}`}
                                  key={relationKey}
                                >
                                  <div className="curation-target__heading">
                                    <h4>{relation.target.replace('_', ' ')}</h4>
                                    <span className="curation-target__state">
                                      {selected ?? 'UNKNOWN'}
                                    </span>
                                  </div>
                                  {relation.proposed_support_level ? (
                                    <div className="curation-evidence">
                                      <span>Evidence proposal</span>
                                      <strong>
                                        {relation.proposed_support_level}
                                      </strong>
                                      <p>{relation.rationale}</p>
                                      {relation.evidence_sources.map(
                                        (source) => (
                                          <a
                                            key={source.id}
                                            href={source.url}
                                            rel="noreferrer"
                                            target="_blank"
                                          >
                                            View evidence
                                          </a>
                                        ),
                                      )}
                                    </div>
                                  ) : (
                                    <p className="curation-target__hint">
                                      Independent human review
                                    </p>
                                  )}
                                  <div
                                    className="curation-choice-row"
                                    role="group"
                                    aria-label={`Review ${card.card.name} for ${relation.target}`}
                                  >
                                    {supportLevels.map((level) => (
                                      <button
                                        aria-pressed={selected === level}
                                        className={`curation-choice${selected === level ? ' curation-choice--selected' : ''}`}
                                        key={level}
                                        onClick={() => select(relation, level)}
                                        type="button"
                                      >
                                        {level}
                                      </button>
                                    ))}
                                    <button
                                      className="curation-clear"
                                      disabled={!selected}
                                      onClick={() => select(relation, null)}
                                      type="button"
                                    >
                                      Clear
                                    </button>
                                  </div>
                                </section>
                              );
                            })}
                          </div>
                        </section>
                      );
                    })}
                  </div>
                </article>
              );
            },
          )
        )}
      </div>
      <div className="curation__navigation">
        <button
          disabled={cardIndex === 0}
          onClick={() => setCardIndex((value) => Math.max(0, value - 1))}
          type="button"
        >
          Previous card
        </button>
        <span>
          Card{' '}
          {filteredCards.length === 0
            ? 0
            : Math.min(cardIndex + 1, filteredCards.length)}{' '}
          of {filteredCards.length}
        </span>
        <button
          disabled={cardIndex >= filteredCards.length - 1}
          onClick={() =>
            setCardIndex((value) =>
              Math.min(filteredCards.length - 1, value + 1),
            )
          }
          type="button"
        >
          Next card
        </button>
      </div>
      <button
        className="curation__submit"
        disabled={submitting || reviewed === 0}
        onClick={() => void submit()}
        type="button"
      >
        {submitting ? 'Generating artifacts…' : 'Generate reviewed artifacts'}
      </button>
    </section>
  );
}
