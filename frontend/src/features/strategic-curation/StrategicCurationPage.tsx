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
  try {
    const raw = window.localStorage.getItem(draftKey(session));
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed))
      return {};
    const allowed = new Set(session.proposals.map(proposalKey));
    return Object.fromEntries(
      Object.entries(parsed).filter(
        ([key, value]) =>
          allowed.has(key) && supportLevels.includes(value as SupportLevel),
      ),
    );
  } catch {
    return {};
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

  const filtered = useMemo(
    () =>
      session?.proposals.filter((proposal) => {
        const selected = decisions[proposalKey(proposal)] !== undefined;
        return (
          (targetFilter === 'all' || proposal.target === targetFilter) &&
          (stateFilter === 'all' || (stateFilter === 'reviewed') === selected)
        );
      }) ?? [],
    [decisions, session, stateFilter, targetFilter],
  );
  const targets = useMemo(
    () => [...new Set(session?.proposals.map((item) => item.target) ?? [])],
    [session],
  );
  const reviewed = Object.keys(decisions).length;

  const select = (proposal: StrategicProposal, level: SupportLevel | null) => {
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
    const submitted: StrategicDecision[] = session.proposals.flatMap(
      (proposal) => {
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
      },
    );
    try {
      const result = await api.submit(session, submitted);
      download(result.assignment_artifact, result.artifact_filename);
      download(result.coverage_report, result.coverage_filename);
      window.localStorage.removeItem(draftKey(session));
      setDecisions({});
      setNotice(
        `${result.reviewed_count} reviewed assignments; ${result.unknown_remaining} memberships remain UNKNOWN. Both JSON artifacts were downloaded.`,
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
            <option value="unreviewed">Unreviewed</option>
            <option value="reviewed">Reviewed</option>
          </select>
        </label>
        <p>
          {reviewed} reviewed / {session.proposals.length - reviewed} unreviewed
          proposals
        </p>
      </div>
      <p aria-live="polite" className="curation__notice">
        {notice}
      </p>
      {error ? <p role="alert">{error}</p> : null}
      <div className="curation__list">
        {filtered.map((proposal) => {
          const key = proposalKey(proposal);
          const selected = decisions[key];
          return (
            <article className="curation-card" key={key}>
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
                <h3>
                  {proposal.target_type}: {proposal.target}
                </h3>
                <p>
                  Current proposal:{' '}
                  <strong>{proposal.proposed_support_level}</strong>
                </p>
                <p>{proposal.rationale}</p>
                <p>
                  {proposal.evidence_sources.map((source) => (
                    <a
                      key={source.id}
                      href={source.url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      {source.id}
                    </a>
                  ))}
                </p>
                <fieldset>
                  <legend>
                    Review {proposal.card.name} for {proposal.target}
                  </legend>
                  {supportLevels.map((level) => (
                    <label key={level}>
                      <input
                        checked={selected === level}
                        name={key}
                        onChange={() => select(proposal, level)}
                        type="radio"
                        value={level}
                      />
                      {level.toUpperCase()}
                    </label>
                  ))}
                  <button onClick={() => select(proposal, null)} type="button">
                    Skip / clear
                  </button>
                </fieldset>
              </div>
            </article>
          );
        })}
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
