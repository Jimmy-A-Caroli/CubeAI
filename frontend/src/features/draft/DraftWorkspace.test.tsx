import axe from 'axe-core';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import DraftWorkspace from './DraftWorkspace';
import type { DraftApi, DraftCard, DraftReview, DraftView } from './draftApi';

const noDetails = {
  image_url: null,
  mana_cost: null,
  type_line: null,
  oracle_text: null,
  power: null,
  toughness: null,
  loyalty: null,
  colors: [],
};

const card = (
  instance_id: string,
  cube_card_id: string,
  name: string,
): DraftCard => ({
  instance_id,
  cube_card_id,
  name,
  ...noDetails,
});

const firstView: DraftView = {
  draft_id: 'draft-7',
  cube_version_id: 'version-1',
  status: 'active',
  seat_number: 0,
  pack_number: 1,
  pick_number: 1,
  cube_name: 'Synthetic Cube',
  configuration: { seats: 2, packs_per_seat: 1, pack_size: 2, seed: 13 },
  current_pack: [
    card('instance-a', 'cube-a', 'Lightning Bolt'),
    card('instance-b', 'cube-b', 'Lightning Bolt'),
    card('instance-c', 'cube-c', 'Counterspell'),
  ],
  pool: [],
};

const review: DraftReview = {
  draft_id: 'draft-7',
  cube_name: 'Synthetic Cube',
  configuration: { seats: 2, packs_per_seat: 1, pack_size: 2, seed: 13 },
  human_picks: [
    {
      seat_number: 0,
      round_number: 1,
      pick_number: 1,
      card: { name: 'Lightning Bolt', ...noDetails },
      bot_provenance: null,
    },
  ],
  bot_picks: [
    {
      seat_number: 1,
      round_number: 1,
      pick_number: 1,
      card: { name: 'Counterspell', ...noDetails },
      bot_provenance: {
        strategy_id: 'raw-ranking-v0',
        strategy_version: '1',
        rating_artifact_id: 'raw-ranking-v0',
        rating_artifact_version: '1',
        selected_rating: 5,
        rating_lookup_outcome: 'found',
        tie_break_reason: 'highest_rating',
      },
    },
  ],
};

function apiWith(overrides: Partial<DraftApi> = {}): DraftApi {
  return {
    loadDraft: vi.fn().mockResolvedValue(firstView),
    submitPick: vi.fn().mockResolvedValue(firstView),
    loadReview: vi.fn().mockResolvedValue(review),
    loadTracking: vi.fn().mockResolvedValue({
      draft_id: 'draft-7',
      observer_seat: 0,
      tracked_card_instance_ids: [],
    }),
    trackCard: vi.fn().mockResolvedValue({
      draft_id: 'draft-7',
      observer_seat: 0,
      tracked_card_instance_ids: ['instance-b'],
    }),
    untrackCard: vi.fn().mockResolvedValue({
      draft_id: 'draft-7',
      observer_seat: 0,
      tracked_card_instance_ids: [],
    }),
    ...overrides,
  };
}

function deferred<T>() {
  let resolve: (value: T) => void = () => undefined;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

describe('DraftWorkspace', () => {
  it('keeps duplicate memberships selectable without showing implementation IDs', async () => {
    const updated: DraftView = {
      ...firstView,
      pick_number: 2,
      current_pack: [firstView.current_pack[2]],
      pool: [firstView.current_pack[1]],
    };
    const submitPick = vi.fn().mockResolvedValue(updated);

    render(
      <DraftWorkspace
        draftId="draft-7"
        initialView={firstView}
        api={apiWith({ submitPick })}
      />,
    );

    fireEvent.click(
      screen.getAllByRole('button', { name: 'Select Lightning Bolt' })[1],
    );
    fireEvent.click(screen.getByRole('button', { name: 'Make pick' }));

    await waitFor(() => {
      expect(submitPick).toHaveBeenCalledWith('draft-7', 'instance-b');
    });
    expect(screen.getByText('Seat 1 · Pack 1 · Pick 2')).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Inspect Lightning Bolt' }),
    ).toBeTruthy();
    expect(screen.queryByText(/instance-b|cube-b/i)).toBeNull();
  });

  it('tracks the exact current instance and restores its visual marker', async () => {
    const trackCard = vi.fn().mockResolvedValue({
      draft_id: 'draft-7',
      observer_seat: 0,
      tracked_card_instance_ids: ['instance-b'],
    });
    render(
      <DraftWorkspace
        draftId="draft-7"
        initialView={firstView}
        api={apiWith({ trackCard })}
      />,
    );

    fireEvent.click(
      screen.getAllByRole('button', { name: 'Track Lightning Bolt' })[1],
    );

    await waitFor(() =>
      expect(trackCard).toHaveBeenCalledWith('draft-7', 'instance-b'),
    );
    expect(
      screen.getByRole('button', { name: 'Untrack Lightning Bolt' }),
    ).toBeTruthy();
    expect(screen.getByText('3 cards available · 1 tracked')).toBeTruthy();
    expect(screen.queryByText(/instance-b|cube-b/i)).toBeNull();
  });

  it('renders a cached image, falls back cleanly on failure, and keeps details keyboard-accessible', async () => {
    const detailed: DraftView = {
      ...firstView,
      current_pack: [
        {
          ...firstView.current_pack[0],
          image_url: 'https://images.example.invalid/lightning-bolt.jpg',
          mana_cost: '{R}',
          type_line: 'Instant',
          oracle_text: 'Lightning Bolt deals 3 damage to any target.',
          colors: ['R'],
        },
      ],
    };
    render(
      <DraftWorkspace
        draftId="draft-7"
        initialView={detailed}
        api={apiWith()}
      />,
    );

    const image = screen.getByAltText('Lightning Bolt');
    expect(image.getAttribute('src')).toBe(
      'https://images.example.invalid/lightning-bolt.jpg',
    );
    fireEvent.click(
      screen.getByRole('button', { name: 'Select Lightning Bolt' }),
    );
    const inspectButton = screen.getByRole('button', { name: 'Inspect card' });
    inspectButton.focus();
    fireEvent.click(inspectButton);
    expect(screen.getByRole('dialog').textContent).toContain(
      'Lightning Bolt deals 3 damage',
    );
    expect(screen.getAllByText('Colours: Red')).toHaveLength(2);
    expect(screen.getByRole('button', { name: 'Close card details' })).toBe(
      document.activeElement,
    );
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Tab' });
    expect(screen.getByRole('button', { name: 'Close card details' })).toBe(
      document.activeElement,
    );
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    await waitFor(() => expect(inspectButton).toBe(document.activeElement));

    fireEvent.error(image);
    expect(
      screen.getByRole('img', {
        name: 'Card image unavailable for Lightning Bolt',
      }),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Make pick' })).toBeTruthy();
  });

  it('loads its seat-safe view and provides explicit retry recovery on an unavailable draft', async () => {
    const loadDraft = vi.fn().mockRejectedValue(new Error('offline'));
    render(<DraftWorkspace draftId="draft-7" api={apiWith({ loadDraft })} />);

    expect(
      await screen.findByRole('heading', { name: 'Your draft is unavailable' }),
    ).toBeTruthy();
    fireEvent.click(
      screen.getByRole('button', { name: 'Retry loading draft' }),
    );
    await waitFor(() => expect(loadDraft).toHaveBeenCalledTimes(2));
  });

  it('ignores a late response from a replaced draft', async () => {
    const lateFirstDraft = deferred<DraftView>();
    const secondView: DraftView = {
      ...firstView,
      draft_id: 'draft-8',
      current_pack: [card('instance-d', 'cube-d', 'Swords to Plowshares')],
    };
    const api = apiWith({
      loadDraft: vi.fn().mockReturnValue(lateFirstDraft.promise),
    });
    const rendered = render(<DraftWorkspace draftId="draft-7" api={api} />);

    rendered.rerender(
      <DraftWorkspace draftId="draft-8" initialView={secondView} api={api} />,
    );
    lateFirstDraft.resolve(firstView);

    expect(
      await screen.findByRole('button', {
        name: 'Select Swords to Plowshares',
      }),
    ).toBeTruthy();
    await Promise.resolve();
    expect(
      screen.queryByRole('button', { name: 'Select Counterspell' }),
    ).toBeNull();
  });

  it('shows completed pool, human history, and recorded bot provenance only after review is requested', async () => {
    const loadReview = vi.fn().mockResolvedValue(review);
    render(
      <DraftWorkspace
        draftId="draft-7"
        initialView={{
          ...firstView,
          status: 'completed',
          current_pack: [],
          pool: firstView.current_pack,
        }}
        api={apiWith({ loadReview })}
        onNewDraft={vi.fn()}
      />,
    );

    expect(
      screen.getByRole('heading', { name: 'Draft complete' }),
    ).toBeTruthy();
    expect(
      screen.getByText('2 players · 1 packs × 2 cards · 3 cards drafted'),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Make pick' })).toBeNull();
    expect(screen.getByRole('button', { name: 'New draft' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Review draft' }));

    await waitFor(() => expect(loadReview).toHaveBeenCalledWith('draft-7'));
    expect(screen.getByRole('heading', { name: 'Your picks' })).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Bot 2', pressed: true }),
    ).toBeTruthy();
    expect(
      screen.getByRole('heading', { name: 'Bot 2 draft history' }),
    ).toBeTruthy();
    expect(
      screen.getByText(/Bot v0 decision · Strategy: raw-ranking-v0@1/),
    ).toBeTruthy();
  });

  it('labels review picks with their draft round rather than a physical pack ID', async () => {
    const loadReview = vi.fn().mockResolvedValue({
      ...review,
      human_picks: [
        {
          ...review.human_picks[0],
          round_number: 2,
          pick_number: 1,
        },
      ],
      bot_picks: [
        {
          ...review.bot_picks[0],
          round_number: 2,
          pick_number: 1,
        },
      ],
    });
    render(
      <DraftWorkspace
        draftId="draft-7"
        initialView={{ ...firstView, status: 'completed', current_pack: [] }}
        api={apiWith({ loadReview })}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Review draft' }));

    expect(await screen.findAllByText('Pack 2 · Pick 1')).toHaveLength(2);
    expect(screen.queryByText('Pack 3 · Pick 1')).toBeNull();
  });

  it('has no basic accessibility violations in the selectable pack state', async () => {
    const rendered = render(
      <DraftWorkspace
        draftId="draft-7"
        initialView={firstView}
        api={apiWith()}
      />,
    );
    const result = await axe.run(rendered.container);
    expect(result.violations).toEqual([]);
  });
});
