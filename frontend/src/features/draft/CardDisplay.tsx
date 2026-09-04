import { useLayoutEffect, useRef } from 'react';

import type { DraftCard, DraftReviewPick } from './draftApi';
import './CardDisplay.css';

export type CardDetails = Omit<DraftCard, 'instance_id' | 'cube_card_id'>;

type CardArtProps = {
  card: CardDetails;
  compact?: boolean;
};

export function CardArt({ card, compact = false }: CardArtProps) {
  return (
    <div
      aria-label={`Card image preview unavailable locally for ${card.name}`}
      className={`card-art card-art--fallback${compact ? ' card-art--compact' : ''}`}
      role="img"
    >
      <span>{card.name}</span>
      {card.mana_cost !== null ? <small>{card.mana_cost}</small> : null}
    </div>
  );
}

type CardDetailDialogProps = {
  card: CardDetails | null;
  onClose: () => void;
};

export function CardDetailDialog({ card, onClose }: CardDetailDialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const openerRef = useRef<HTMLElement | null>(null);

  useLayoutEffect(() => {
    if (card !== null) {
      openerRef.current =
        document.activeElement instanceof HTMLElement
          ? document.activeElement
          : null;
      closeButtonRef.current?.focus();
    }
  }, [card]);

  if (card === null) {
    return null;
  }
  const close = () => {
    onClose();
    window.setTimeout(() => openerRef.current?.focus(), 0);
  };
  const characteristics = [
    card.power !== null || card.toughness !== null
      ? ['Power / toughness', `${card.power ?? '?'} / ${card.toughness ?? '?'}`]
      : null,
    card.loyalty !== null ? ['Loyalty', card.loyalty] : null,
  ].filter((value): value is [string, string] => value !== null);

  return (
    <div className="card-detail__backdrop" role="presentation">
      <section
        aria-labelledby="card-detail-title"
        aria-modal="true"
        className="card-detail"
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            event.preventDefault();
            close();
          }
          if (event.key === 'Tab') {
            event.preventDefault();
            closeButtonRef.current?.focus();
          }
        }}
        role="dialog"
      >
        <button
          aria-label="Close card details"
          className="card-detail__close"
          onClick={close}
          ref={closeButtonRef}
          type="button"
        >
          Close
        </button>
        <CardArt card={card} />
        <div className="card-detail__content">
          <h2 id="card-detail-title">{card.name}</h2>
          {card.mana_cost !== null ? <p>{card.mana_cost}</p> : null}
          {card.type_line !== null ? <p>{card.type_line}</p> : null}
          {card.oracle_text !== null ? (
            <p className="card-detail__oracle">{card.oracle_text}</p>
          ) : (
            <p className="card-detail__unavailable">
              Rules details are unavailable in this local card cache.
            </p>
          )}
          {characteristics.length > 0 ? (
            <dl>
              {characteristics.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          ) : null}
          <p className="card-detail__source">
            Card metadata: Scryfall. Image preview unavailable locally.
          </p>
        </div>
      </section>
    </div>
  );
}

export function reviewCard(pick: DraftReviewPick): CardDetails {
  return pick.card;
}
