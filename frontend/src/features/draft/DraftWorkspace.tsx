import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  type DraftApi,
  type DraftCard,
  type DraftView,
  DraftApiError,
  localDraftApi,
} from './draftApi';
import './DraftWorkspace.css';

type DraftWorkspaceProps = {
  draftId: string;
  initialView?: DraftView;
  api?: DraftApi;
};

type PoolGroup = {
  name: string;
  cards: DraftCard[];
};

function poolGroups(pool: DraftCard[]): PoolGroup[] {
  const grouped = new Map<string, DraftCard[]>();
  for (const card of pool) {
    const cards = grouped.get(card.name) ?? [];
    cards.push(card);
    grouped.set(card.name, cards);
  }

  return [...grouped.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, cards]) => ({
      name,
      cards: [...cards].sort((left, right) =>
        left.instance_id.localeCompare(right.instance_id),
      ),
    }));
}

function readableError(error: unknown): string {
  if (error instanceof DraftApiError) {
    return error.message;
  }
  return 'The draft could not be updated. Your saved draft has not been changed.';
}

export default function DraftWorkspace({
  draftId,
  initialView,
  api = localDraftApi,
}: DraftWorkspaceProps) {
  const [view, setView] = useState<DraftView | null>(initialView ?? null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(initialView === undefined);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const operationRef = useRef(0);
  const currentDraftIdRef = useRef(draftId);
  currentDraftIdRef.current = draftId;

  const refresh = useCallback(async () => {
    const operation = ++operationRef.current;
    const requestedDraftId = draftId;
    const isCurrent = () =>
      operationRef.current === operation &&
      currentDraftIdRef.current === requestedDraftId;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const refreshed = await api.loadDraft(requestedDraftId);
      if (!isCurrent()) {
        return;
      }
      setView(refreshed);
      setSelectedId((previous) =>
        refreshed.current_pack.some((card) => card.instance_id === previous)
          ? previous
          : null,
      );
    } catch (requestError) {
      if (isCurrent()) {
        setError(readableError(requestError));
      }
    } finally {
      if (isCurrent()) {
        setLoading(false);
      }
    }
  }, [api, draftId]);

  useEffect(() => {
    // Invalidate every pending response from the previously rendered draft.
    operationRef.current += 1;
    setSelectedId(null);
    setError(null);
    setNotice(null);
    setSubmitting(false);
    if (initialView !== undefined) {
      setView(initialView);
      setLoading(false);
      return;
    }

    setView(null);
    void refresh();
  }, [initialView, refresh]);

  // Never render or act on a saved view while a different draft identity is
  // being supplied by the parent. The effect below replaces it after render.
  const currentView = view?.draft_id === draftId ? view : null;
  const selectedCard = currentView?.current_pack.find(
    (card) => card.instance_id === selectedId,
  );
  const groups = useMemo(
    () => poolGroups(currentView?.pool ?? []),
    [currentView?.pool],
  );
  const completed = currentView?.status === 'completed';

  const submitPick = async () => {
    if (
      selectedId === null ||
      currentView === null ||
      submitting ||
      completed
    ) {
      return;
    }

    const operation = ++operationRef.current;
    const requestedDraftId = draftId;
    const isCurrent = () =>
      operationRef.current === operation &&
      currentDraftIdRef.current === requestedDraftId;
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await api.submitPick(requestedDraftId, selectedId);
      if (!isCurrent()) {
        return;
      }
      setView(updated);
      setSelectedId(null);
      setNotice(
        updated.status === 'completed'
          ? 'Your pick was recorded. This draft is complete.'
          : 'Your pick was recorded. Your next legal pick is ready.',
      );
    } catch (requestError) {
      if (!isCurrent()) {
        return;
      }
      setError(readableError(requestError));
      // A rejected pick can be stale after the saved draft changed. Refreshing
      // only this seat-safe view removes no-longer-legal choices.
      try {
        const refreshed = await api.loadDraft(requestedDraftId);
        if (!isCurrent()) {
          return;
        }
        setView(refreshed);
        setSelectedId(null);
      } catch {
        // Keep the original command error; recovery remains available below.
      }
    } finally {
      if (isCurrent()) {
        setSubmitting(false);
      }
    }
  };

  if (loading && currentView === null) {
    return (
      <main className="draft-workspace" aria-busy="true">
        <p role="status">Loading your saved draft…</p>
      </main>
    );
  }

  if (currentView === null) {
    return (
      <main className="draft-workspace">
        <section
          className="draft-workspace__recovery"
          aria-labelledby="draft-load-error"
        >
          <h1 id="draft-load-error">Your draft is unavailable</h1>
          <p role="alert">{error ?? 'The draft could not be loaded.'}</p>
          <button type="button" onClick={() => void refresh()}>
            Retry loading draft
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="draft-workspace" aria-busy={submitting || loading}>
      <header className="draft-workspace__header">
        <p className="draft-workspace__eyebrow">Local draft</p>
        <h1>Make your pick</h1>
        <p className="draft-workspace__progress" aria-label="Draft progress">
          Seat {currentView.seat_number + 1} · Pack {currentView.pack_number} ·
          Pick {currentView.pick_number}
        </p>
      </header>

      {error !== null ? (
        <section
          className="draft-workspace__error"
          role="alert"
          aria-live="assertive"
        >
          <p>{error}</p>
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={loading}
          >
            Refresh draft
          </button>
        </section>
      ) : null}

      {notice !== null ? (
        <p className="draft-workspace__notice" role="status">
          {notice}
        </p>
      ) : null}

      {completed ? (
        <section
          className="draft-workspace__completion"
          aria-labelledby="draft-complete"
        >
          <p className="draft-workspace__eyebrow">Draft complete</p>
          <h2 id="draft-complete">Your pool is ready to review.</h2>
          <p>All available picks have been recorded in this local draft.</p>
        </section>
      ) : (
        <section
          className="draft-workspace__pack"
          aria-labelledby="current-pack-heading"
        >
          <div className="draft-workspace__section-heading">
            <div>
              <p className="draft-workspace__eyebrow">Current pack</p>
              <h2 id="current-pack-heading">Choose one legal card</h2>
            </div>
            <p>{currentView.current_pack.length} cards available</p>
          </div>

          <ul
            className="draft-workspace__card-grid"
            aria-label="Current legal cards"
          >
            {currentView.current_pack.map((card) => {
              const selected = card.instance_id === selectedId;
              return (
                <li key={card.instance_id}>
                  <button
                    aria-pressed={selected}
                    className="draft-workspace__card"
                    type="button"
                    disabled={submitting || loading}
                    onClick={() => setSelectedId(card.instance_id)}
                  >
                    <span>{card.name}</span>
                    <small>Instance {card.instance_id}</small>
                  </button>
                </li>
              );
            })}
          </ul>

          <section className="draft-workspace__pick-action" aria-live="polite">
            {selectedCard === undefined ? (
              <p>
                Select a card from the current pack, then confirm your pick.
              </p>
            ) : (
              <>
                <p>
                  Selected: <strong>{selectedCard.name}</strong>
                </p>
                <details>
                  <summary>Card details</summary>
                  <dl>
                    <div>
                      <dt>Draft instance</dt>
                      <dd>{selectedCard.instance_id}</dd>
                    </div>
                    <div>
                      <dt>Cube membership</dt>
                      <dd>{selectedCard.cube_card_id}</dd>
                    </div>
                  </dl>
                </details>
              </>
            )}
            <button
              className="draft-workspace__confirm"
              type="button"
              onClick={() => void submitPick()}
              disabled={selectedCard === undefined || submitting || loading}
            >
              {submitting ? 'Recording pick…' : 'Make pick'}
            </button>
          </section>
        </section>
      )}

      <section
        className="draft-workspace__pool"
        aria-labelledby="my-pool-heading"
      >
        <div className="draft-workspace__section-heading">
          <div>
            <p className="draft-workspace__eyebrow">My pool</p>
            <h2 id="my-pool-heading">Drafted cards</h2>
          </div>
          <p>{currentView.pool.length} picked</p>
        </div>
        {groups.length === 0 ? (
          <p className="draft-workspace__empty-pool">
            Your picks will appear here.
          </p>
        ) : (
          <ul className="draft-workspace__pool-groups">
            {groups.map((group) => (
              <li key={group.name}>
                <h3>
                  {group.name} <span>×{group.cards.length}</span>
                </h3>
                <ul>
                  {group.cards.map((card) => (
                    <li key={card.instance_id}>Instance {card.instance_id}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
