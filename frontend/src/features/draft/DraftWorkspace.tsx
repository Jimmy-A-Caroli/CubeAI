import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  type DraftApi,
  type DraftInspector,
  type DraftInspectorDecision,
  type DraftCard,
  type DraftReview,
  type DraftReviewPick,
  type DraftView,
  type PickReview,
  DraftApiError,
  localDraftApi,
} from './draftApi';
import {
  CardArt,
  CardColours,
  CardDetailDialog,
  reviewCard,
  type CardDetails,
} from './CardDisplay';
import './DraftWorkspace.css';

type DraftWorkspaceProps = {
  draftId: string;
  initialView?: DraftView;
  api?: DraftApi;
  onNewDraft?: () => void;
};

function readableError(error: unknown): string {
  if (error instanceof DraftApiError) {
    return error.message;
  }
  return 'The draft could not be updated. Your saved draft has not been changed.';
}

function pickLabel(pick: DraftReviewPick): string {
  return `Pack ${pick.round_number} · Pick ${pick.pick_number}`;
}

function inspectorLabel(decision: DraftInspectorDecision): string {
  return `Seat ${decision.seat_number + 1} · Pack ${decision.round_number} · Pick ${decision.pick_number}`;
}

export default function DraftWorkspace({
  draftId,
  initialView,
  api = localDraftApi,
  onNewDraft,
}: DraftWorkspaceProps) {
  const [view, setView] = useState<DraftView | null>(initialView ?? null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [inspectedCard, setInspectedCard] = useState<CardDetails | null>(null);
  const [review, setReview] = useState<DraftReview | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [inspector, setInspector] = useState<DraftInspector | null>(null);
  const [inspectorLoading, setInspectorLoading] = useState(false);
  const [inspectorError, setInspectorError] = useState<string | null>(null);
  const [selectedDecisionSequence, setSelectedDecisionSequence] = useState<
    number | null
  >(null);
  const [pickReview, setPickReview] = useState<PickReview | null>(null);
  const [reviewAssessment, setReviewAssessment] = useState('reasonable');
  const [reviewNote, setReviewNote] = useState('');
  const [reviewRating, setReviewRating] = useState('');
  const [botSeat, setBotSeat] = useState<number | null>(null);
  const [trackedCardIds, setTrackedCardIds] = useState<string[]>([]);
  const [trackingCardId, setTrackingCardId] = useState<string | null>(null);
  const [trackingError, setTrackingError] = useState<string | null>(null);
  const [loading, setLoading] = useState(initialView === undefined);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const operationRef = useRef(0);
  const currentDraftIdRef = useRef(draftId);
  const inspectorRef = useRef<HTMLElement | null>(null);
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
      if (!isCurrent()) return;
      setView(refreshed);
      setSelectedId((previous) =>
        refreshed.current_pack.some((card) => card.instance_id === previous)
          ? previous
          : null,
      );
    } catch (requestError) {
      if (isCurrent()) setError(readableError(requestError));
    } finally {
      if (isCurrent()) setLoading(false);
    }
  }, [api, draftId]);

  useEffect(() => {
    if (selectedDecisionSequence === null || inspector === null) return;
    setPickReview(null);
    if (!api.loadPickReview) return;
    void api
      .loadPickReview(draftId, selectedDecisionSequence)
      .then((loaded) => {
        setPickReview(loaded);
        if (loaded) {
          setReviewAssessment(loaded.assessment);
          setReviewNote(loaded.note ?? '');
          setReviewRating(loaded.suggested_rating?.toString() ?? '');
        }
      });
  }, [api, draftId, inspector, selectedDecisionSequence]);

  useEffect(() => {
    operationRef.current += 1;
    setSelectedId(null);
    setInspectedCard(null);
    setReview(null);
    setReviewError(null);
    setInspector(null);
    setInspectorError(null);
    setSelectedDecisionSequence(null);
    setBotSeat(null);
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

  useEffect(() => {
    let active = true;
    setTrackedCardIds([]);
    setTrackingError(null);
    void api
      .loadTracking(draftId)
      .then((tracking) => {
        if (active) setTrackedCardIds(tracking.tracked_card_instance_ids);
      })
      .catch((requestError: unknown) => {
        if (active) setTrackingError(readableError(requestError));
      });
    return () => {
      active = false;
    };
  }, [api, draftId]);

  useEffect(() => {
    if (inspector === null || inspectorRef.current === null) return;
    inspectorRef.current.scrollIntoView?.({
      behavior: 'smooth',
      block: 'start',
    });
    inspectorRef.current.focus({ preventScroll: true });
  }, [inspector]);

  const currentView = view?.draft_id === draftId ? view : null;
  const selectedCard = currentView?.current_pack.find(
    (card) => card.instance_id === selectedId,
  );
  const completed = currentView?.status === 'completed';
  const allBotDraft = currentView?.mode === 'all_bot';
  const botSeats = useMemo(
    () =>
      review === null
        ? []
        : [...new Set(review.bot_picks.map((pick) => pick.seat_number))].sort(
            (left, right) => left - right,
          ),
    [review],
  );
  const selectedBotPicks = useMemo(
    () =>
      review === null || botSeat === null
        ? []
        : review.bot_picks.filter((pick) => pick.seat_number === botSeat),
    [review, botSeat],
  );
  const selectedDecision = useMemo(
    () =>
      inspector === null || selectedDecisionSequence === null
        ? null
        : (inspector.decisions.find(
            (decision) => decision.sequence === selectedDecisionSequence,
          ) ?? null),
    [inspector, selectedDecisionSequence],
  );
  const inspectorSeats = useMemo(
    () =>
      [...new Set(inspector?.decisions.map((d) => d.seat_number) ?? [])].sort(
        (a, b) => a - b,
      ),
    [inspector],
  );
  const seatDecisions = useMemo(
    () =>
      inspector?.decisions.filter(
        (d) =>
          d.seat_number ===
          (selectedDecision?.seat_number ?? inspectorSeats[0]),
      ) ?? [],
    [inspector, inspectorSeats, selectedDecision],
  );
  const inspectorPacks = useMemo(
    () =>
      [...new Set(seatDecisions.map((d) => d.round_number))].sort(
        (a, b) => a - b,
      ),
    [seatDecisions],
  );
  const packDecisions = useMemo(
    () =>
      seatDecisions.filter(
        (d) =>
          d.round_number ===
          (selectedDecision?.round_number ?? inspectorPacks[0]),
      ),
    [inspectorPacks, seatDecisions, selectedDecision],
  );
  const moveDecision = (offset: number) => {
    if (inspector === null || selectedDecision === null) return;
    const index = inspector.decisions.findIndex(
      (d) => d.sequence === selectedDecision.sequence,
    );
    const next = inspector.decisions[index + offset];
    if (next !== undefined) setSelectedDecisionSequence(next.sequence);
  };
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.matches('input, textarea, select, [contenteditable="true"]'))
        return;
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        moveDecision(-1);
      }
      if (event.key === 'ArrowRight') {
        event.preventDefault();
        moveDecision(1);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  });

  const toggleTracking = async (cardInstanceId: string, cardName: string) => {
    if (trackingCardId !== null) return;
    const requestedDraftId = draftId;
    const wasTracked = trackedCardIds.includes(cardInstanceId);
    setTrackingCardId(cardInstanceId);
    setTrackingError(null);
    try {
      const tracking = wasTracked
        ? await api.untrackCard(requestedDraftId, cardInstanceId)
        : await api.trackCard(requestedDraftId, cardInstanceId);
      if (currentDraftIdRef.current !== requestedDraftId) return;
      setTrackedCardIds(tracking.tracked_card_instance_ids);
      setNotice(
        wasTracked
          ? `${cardName} is no longer tracked.`
          : `${cardName} is tracked for later attention.`,
      );
    } catch (requestError) {
      if (currentDraftIdRef.current === requestedDraftId) {
        setTrackingError(readableError(requestError));
      }
    } finally {
      if (currentDraftIdRef.current === requestedDraftId) {
        setTrackingCardId(null);
      }
    }
  };

  const submitPick = async () => {
    if (selectedId === null || currentView === null || submitting || completed)
      return;
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
      if (!isCurrent()) return;
      setView(updated);
      setSelectedId(null);
      setNotice(
        updated.status === 'completed'
          ? 'Your pick was recorded. This draft is complete.'
          : 'Your pick was recorded. Your next legal pick is ready.',
      );
    } catch (requestError) {
      if (!isCurrent()) return;
      setError(readableError(requestError));
      try {
        const refreshed = await api.loadDraft(requestedDraftId);
        if (!isCurrent()) return;
        setView(refreshed);
        setSelectedId(null);
      } catch {
        // Preserve the command error and leave the user an explicit refresh.
      }
    } finally {
      if (isCurrent()) setSubmitting(false);
    }
  };

  const openReview = async () => {
    if (currentView === null || reviewLoading) return;
    setReviewLoading(true);
    setReviewError(null);
    try {
      const loaded = await api.loadReview(currentView.draft_id);
      setReview(loaded);
      setBotSeat(loaded.bot_picks[0]?.seat_number ?? null);
    } catch (requestError) {
      setReviewError(readableError(requestError));
    } finally {
      setReviewLoading(false);
    }
  };

  const openInspector = async () => {
    if (currentView === null || inspectorLoading) return;
    setInspectorLoading(true);
    setInspectorError(null);
    try {
      const loaded = await api.loadInspector(currentView.draft_id);
      setInspector(loaded);
      setSelectedDecisionSequence(
        loaded.decisions.find((decision) => decision.actor_origin === 'bot')
          ?.sequence ??
          loaded.decisions[0]?.sequence ??
          null,
      );
    } catch (requestError) {
      setInspectorError(readableError(requestError));
    } finally {
      setInspectorLoading(false);
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
    <main
      className="draft-workspace"
      aria-busy={submitting || loading || trackingCardId !== null}
    >
      <header className="draft-workspace__header">
        <p className="draft-workspace__eyebrow">
          {completed ? 'Draft result' : 'Local draft'}
        </p>
        <h1>
          {completed
            ? allBotDraft
              ? 'Fast draft complete'
              : 'Draft complete'
            : 'Make your pick'}
        </h1>
        <p className="draft-workspace__progress" aria-label="Draft progress">
          {completed
            ? currentView.cube_name
            : `Seat ${currentView.seat_number + 1} · Pack ${currentView.pack_number} · Pick ${currentView.pick_number}`}
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

      {trackingError !== null ? <p role="alert">{trackingError}</p> : null}

      {completed ? (
        <section
          className="draft-workspace__completion"
          aria-labelledby="draft-complete"
        >
          <h2 id="draft-complete">{currentView.cube_name}</h2>
          <p>
            {currentView.configuration.seats} players ·{' '}
            {currentView.configuration.packs_per_seat} packs ×{' '}
            {currentView.configuration.pack_size} cards ·{' '}
            {currentView.pool.length} cards drafted
          </p>
          {allBotDraft ? (
            <p>
              Eight Bot v0 seats drafted this cube deterministically. Use the
              Inspector for factual decision context and recorded Bot evidence.
            </p>
          ) : null}
          <p>Seed: {currentView.configuration.seed}</p>
          <div className="draft-workspace__result-actions">
            <button
              type="button"
              onClick={() => void openReview()}
              disabled={reviewLoading}
            >
              {reviewLoading ? 'Opening review…' : 'Review draft'}
            </button>
            <button
              className="draft-workspace__secondary-action"
              type="button"
              onClick={() => void openInspector()}
              disabled={inspectorLoading}
            >
              {inspectorLoading ? 'Opening inspector…' : 'Inspect decisions'}
            </button>
            {onNewDraft !== undefined ? (
              <button
                className="draft-workspace__secondary-action"
                type="button"
                onClick={onNewDraft}
              >
                New draft
              </button>
            ) : null}
          </div>
          {reviewError !== null ? <p role="alert">{reviewError}</p> : null}
          {inspectorError !== null ? (
            <p role="alert">{inspectorError}</p>
          ) : null}
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
            <p>
              {currentView.current_pack.length} cards available ·{' '}
              {trackedCardIds.length} tracked
            </p>
          </div>
          <ul
            className="draft-workspace__card-grid"
            aria-label="Current legal cards"
          >
            {currentView.current_pack.map((card) => {
              const selected = card.instance_id === selectedId;
              const tracked = trackedCardIds.includes(card.instance_id);
              return (
                <li key={card.instance_id}>
                  <button
                    aria-label={`Select ${card.name}`}
                    aria-pressed={selected}
                    className="draft-workspace__card"
                    disabled={submitting || loading}
                    onClick={() => setSelectedId(card.instance_id)}
                    type="button"
                  >
                    <CardArt card={card} />
                    <span>{card.name}</span>
                    {card.mana_cost !== null ? (
                      <small>{card.mana_cost}</small>
                    ) : null}
                    <CardColours card={card} />
                  </button>
                  <button
                    aria-pressed={tracked}
                    className="draft-workspace__tracking-control"
                    disabled={trackingCardId !== null || submitting || loading}
                    onClick={() =>
                      void toggleTracking(card.instance_id, card.name)
                    }
                    type="button"
                  >
                    {tracked ? `Untrack ${card.name}` : `Track ${card.name}`}
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
              <div>
                <p>
                  Selected: <strong>{selectedCard.name}</strong>
                </p>
                <button
                  className="draft-workspace__text-action"
                  onClick={() => setInspectedCard(selectedCard)}
                  type="button"
                >
                  Inspect card
                </button>
              </div>
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
            <p className="draft-workspace__eyebrow">
              {allBotDraft ? 'Seat 1 pool' : 'My pool'}
            </p>
            <h2 id="my-pool-heading">
              {allBotDraft ? 'First Bot seat cards' : 'Drafted cards'}
            </h2>
          </div>
          <p>{currentView.pool.length} picked</p>
        </div>
        {currentView.pool.length === 0 ? (
          <p className="draft-workspace__empty-pool">
            {allBotDraft
              ? 'The first Bot seat has no picks.'
              : 'Your picks will appear here.'}
          </p>
        ) : (
          <ul
            className="draft-workspace__pool-grid"
            aria-label={
              allBotDraft
                ? 'First Bot seat drafted cards'
                : 'Your drafted cards'
            }
          >
            {currentView.pool.map((card) => (
              <li key={card.instance_id}>
                <button
                  aria-label={`Inspect ${card.name}`}
                  onClick={() => setInspectedCard(card)}
                  type="button"
                >
                  <CardArt card={card} compact />
                  <span>{card.name}</span>
                </button>
                <button
                  aria-pressed={trackedCardIds.includes(card.instance_id)}
                  className="draft-workspace__tracking-control"
                  disabled={trackingCardId !== null || submitting || loading}
                  onClick={() =>
                    void toggleTracking(card.instance_id, card.name)
                  }
                  type="button"
                >
                  {trackedCardIds.includes(card.instance_id)
                    ? `Untrack ${card.name}`
                    : `Track ${card.name}`}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {review !== null ? (
        <section
          className="draft-workspace__review"
          aria-labelledby="draft-review-heading"
        >
          <div className="draft-workspace__section-heading">
            <div>
              <p className="draft-workspace__eyebrow">Review draft</p>
              <h2 id="draft-review-heading">Your picks</h2>
            </div>
            <button
              className="draft-workspace__text-action"
              onClick={() => setReview(null)}
              type="button"
            >
              Close review
            </button>
          </div>
          <ReviewPickList
            picks={review.human_picks}
            onInspect={setInspectedCard}
          />
          <div className="draft-workspace__bot-review">
            <fieldset>
              <legend>Bot draft histories</legend>
              <div className="draft-workspace__bot-tabs">
                {botSeats.map((seat) => (
                  <button
                    aria-pressed={botSeat === seat}
                    key={seat}
                    onClick={() => setBotSeat(seat)}
                    type="button"
                  >
                    Bot {seat + 1}
                  </button>
                ))}
              </div>
            </fieldset>
            {botSeat !== null ? (
              <>
                <h3>Bot {botSeat + 1} draft history</h3>
                <p className="draft-workspace__bot-explanation">
                  Bot v0 selected each listed card from its raw ranking. Ratings
                  and deterministic tie-break evidence are shown per pick; it
                  does not evaluate archetypes or predict gameplay.
                </p>
              </>
            ) : null}
            <ReviewPickList
              picks={selectedBotPicks}
              onInspect={setInspectedCard}
            />
          </div>
        </section>
      ) : null}

      {inspector !== null ? (
        <section
          className="draft-workspace__inspector"
          aria-labelledby="draft-inspector-heading"
          ref={inspectorRef}
          tabIndex={-1}
        >
          <div className="draft-workspace__section-heading">
            <div>
              <p className="draft-workspace__eyebrow">Draft Inspector</p>
              <h2 id="draft-inspector-heading">Decision context</h2>
            </div>
            <button
              className="draft-workspace__text-action"
              onClick={() => setInspector(null)}
              type="button"
            >
              Close inspector
            </button>
          </div>
          <p className="draft-workspace__inspector-note">
            This view replays only recorded facts. It does not score
            alternatives, infer a human reason, or provide draft advice.
          </p>
          {selectedDecision !== null ? (
            <div
              className="draft-workspace__inspector-controls"
              aria-label="Inspector navigation"
            >
              <label>
                Seat / Bot
                <select
                  value={selectedDecision.seat_number}
                  onChange={(event) => {
                    const seat = Number(event.target.value);
                    const next = inspector.decisions.find(
                      (d) => d.seat_number === seat,
                    );
                    if (next) setSelectedDecisionSequence(next.sequence);
                  }}
                >
                  {inspectorSeats.map((seat) => (
                    <option key={seat} value={seat}>
                      Seat {seat + 1}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Pack
                <select
                  value={selectedDecision.round_number}
                  onChange={(event) => {
                    const next = seatDecisions.find(
                      (d) => d.round_number === Number(event.target.value),
                    );
                    if (next) setSelectedDecisionSequence(next.sequence);
                  }}
                >
                  {inspectorPacks.map((pack) => (
                    <option key={pack} value={pack}>
                      Pack {pack}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Pick
                <select
                  value={selectedDecision.sequence}
                  onChange={(event) =>
                    setSelectedDecisionSequence(Number(event.target.value))
                  }
                >
                  {packDecisions.map((decision) => (
                    <option key={decision.sequence} value={decision.sequence}>
                      Pick {decision.pick_number}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                onClick={() => moveDecision(-1)}
                disabled={
                  inspector.decisions[0]?.sequence === selectedDecision.sequence
                }
              >
                Previous pick
              </button>
              <button
                type="button"
                onClick={() => moveDecision(1)}
                disabled={
                  inspector.decisions.at(-1)?.sequence ===
                  selectedDecision.sequence
                }
              >
                Next pick
              </button>
            </div>
          ) : null}
          {selectedDecision !== null ? (
            <>
              <InspectorDecision
                decision={selectedDecision}
                onInspect={setInspectedCard}
              />
              <section aria-labelledby="human-review-heading">
                <h3 id="human-review-heading">Human review</h3>
                <fieldset>
                  <legend>Assessment</legend>
                  {['reasonable', 'debatable', 'bad'].map((value) => (
                    <label key={value}>
                      <input
                        type="radio"
                        name="assessment"
                        checked={reviewAssessment === value}
                        onChange={() => setReviewAssessment(value)}
                      />{' '}
                      {value}
                    </label>
                  ))}
                </fieldset>
                <label>
                  Notes
                  <textarea
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                  />
                </label>
                <label>
                  Suggested rating
                  <input
                    type="number"
                    value={reviewRating}
                    onChange={(e) => setReviewRating(e.target.value)}
                  />
                </label>
                <button
                  type="button"
                  onClick={() =>
                    selectedDecisionSequence !== null &&
                    api.savePickReview &&
                    void api
                      .savePickReview(draftId, {
                        id: pickReview?.id ?? crypto.randomUUID(),
                        author: 'local-human',
                        sequence: selectedDecisionSequence,
                        seat_number: selectedDecision.seat_number,
                        pack_number: selectedDecision.physical_pack_number - 1,
                        pick_number: selectedDecision.pick_number - 1,
                        card_instance_id:
                          selectedDecision.chosen_card.instance_id,
                        assessment: reviewAssessment,
                        reasons: [],
                        note: reviewNote || null,
                        suggested_rating: reviewRating
                          ? Number(reviewRating)
                          : null,
                      })
                      .then(setPickReview)
                  }
                >
                  Save review
                </button>
                {pickReview ? (
                  <button
                    type="button"
                    onClick={() =>
                      selectedDecisionSequence !== null &&
                      api.deletePickReview &&
                      void api
                        .deletePickReview(draftId, selectedDecisionSequence)
                        .then(() => setPickReview(null))
                    }
                  >
                    Delete review
                  </button>
                ) : null}
              </section>
            </>
          ) : (
            <p>No decision is available.</p>
          )}
        </section>
      ) : null}

      <CardDetailDialog
        card={inspectedCard}
        onClose={() => setInspectedCard(null)}
      />
    </main>
  );
}

function ReviewPickList({
  picks,
  onInspect,
}: {
  picks: DraftReviewPick[];
  onInspect: (card: CardDetails) => void;
}) {
  if (picks.length === 0) return <p>No picks are available.</p>;
  return (
    <ol className="draft-workspace__review-list">
      {picks.map((pick) => (
        <li
          key={`${pick.seat_number}-${pick.round_number}-${pick.pick_number}`}
        >
          <button onClick={() => onInspect(reviewCard(pick))} type="button">
            <CardArt card={reviewCard(pick)} compact />
            <span>
              <strong>{pickLabel(pick)}</strong>
              {pick.card.name}
            </span>
          </button>
          {pick.bot_provenance !== null ? (
            <p>
              Bot v0 decision · Strategy: {pick.bot_provenance.strategy_id}@
              {pick.bot_provenance.strategy_version} · Selected rating:{' '}
              {pick.bot_provenance.selected_rating} · Tie-break:{' '}
              {pick.bot_provenance.tie_break_reason}
            </p>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

function InspectorDecision({
  decision,
  onInspect,
}: {
  decision: DraftInspectorDecision;
  onInspect: (card: CardDetails) => void;
}) {
  const alternatives = decision.cards_seen.filter(
    (card) => card.instance_id !== decision.chosen_card.instance_id,
  );
  return (
    <article className="draft-workspace__decision-detail">
      <h3>{inspectorLabel(decision)}</h3>
      <p>
        Sequence {decision.sequence + 1} · Physical pack{' '}
        {decision.physical_pack_number} (provenance)
      </p>
      <section>
        <h4>Chosen card</h4>
        <InspectorCardList
          cards={[decision.chosen_card]}
          onInspect={onInspect}
        />
        <p>
          This exact instance was seen {decision.seen_before_pick_count} time
          {decision.seen_before_pick_count === 1 ? '' : 's'} before selection.
        </p>
      </section>
      <section>
        <h4>Cards seen</h4>
        <InspectorCardList cards={decision.cards_seen} onInspect={onInspect} />
      </section>
      <section>
        <h4>Available alternatives</h4>
        {alternatives.length === 0 ? (
          <p>No alternative was available.</p>
        ) : (
          <InspectorCardList cards={alternatives} onInspect={onInspect} />
        )}
        <p>
          No alternative scores or rankings were recorded for this decision.
        </p>
      </section>
      <section>
        <h4>Pool before this pick</h4>
        {decision.pool_before.length === 0 ? (
          <p>This seat had not drafted a card yet.</p>
        ) : (
          <InspectorCardList
            cards={decision.pool_before}
            onInspect={onInspect}
          />
        )}
      </section>
      {decision.bot_provenance !== null ? (
        <section>
          <h4>Recorded Bot v0 evidence</h4>
          <dl className="draft-workspace__inspector-facts">
            <div>
              <dt>Strategy</dt>
              <dd>
                {decision.bot_provenance.strategy_id}@
                {decision.bot_provenance.strategy_version}
              </dd>
            </div>
            <div>
              <dt>Selected rating</dt>
              <dd>{decision.bot_provenance.selected_rating}</dd>
            </div>
            <div>
              <dt>Rating artifact</dt>
              <dd>
                {decision.bot_provenance.rating_artifact_id}@
                {decision.bot_provenance.rating_artifact_version}
              </dd>
            </div>
            <div>
              <dt>Lookup / tie-break</dt>
              <dd>
                {decision.bot_provenance.rating_lookup_outcome} /{' '}
                {decision.bot_provenance.tie_break_reason}
              </dd>
            </div>
          </dl>
        </section>
      ) : null}
      {decision.wheel_facts.length > 0 ? (
        <section>
          <h4>Wheel evidence</h4>
          <ul>
            {decision.wheel_facts.map((fact) => (
              <li key={`${fact.card.instance_id}-${fact.role}`}>
                {fact.card.name}:{' '}
                {fact.role === 'first_seen'
                  ? `first seen at this decision; returned at sequence ${fact.returned_sequence + 1}`
                  : `returned after first appearing at sequence ${fact.first_seen_sequence + 1}`}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </article>
  );
}

function InspectorCardList({
  cards,
  onInspect,
}: {
  cards: DraftCard[];
  onInspect: (card: CardDetails) => void;
}) {
  return (
    <ul className="draft-workspace__inspector-card-list">
      {cards.map((card) => (
        <li key={card.instance_id}>
          <button onClick={() => onInspect(card)} type="button">
            <CardArt card={card} compact />
            <span>{card.name}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
