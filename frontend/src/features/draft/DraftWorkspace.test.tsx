import axe from 'axe-core';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import DraftWorkspace from './DraftWorkspace';
import type { DraftApi, DraftView } from './draftApi';

const firstView: DraftView = {
  draft_id: 'draft-7',
  cube_version_id: 'version-1',
  status: 'active',
  seat_number: 0,
  pack_number: 1,
  pick_number: 1,
  current_pack: [
    {
      instance_id: 'instance-a',
      cube_card_id: 'cube-a',
      name: 'Lightning Bolt',
    },
    {
      instance_id: 'instance-b',
      cube_card_id: 'cube-b',
      name: 'Lightning Bolt',
    },
    { instance_id: 'instance-c', cube_card_id: 'cube-c', name: 'Counterspell' },
  ],
  pool: [],
};

function apiWith(overrides: Partial<DraftApi> = {}): DraftApi {
  return {
    loadDraft: vi.fn().mockResolvedValue(firstView),
    submitPick: vi.fn().mockResolvedValue(firstView),
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
  it('keeps duplicate card instances distinct and submits only the selected legal instance', async () => {
    const updated: DraftView = {
      ...firstView,
      pick_number: 2,
      current_pack: [firstView.current_pack[2]],
      pool: [firstView.current_pack[1]],
    };
    const submitPick = vi.fn().mockResolvedValue(updated);
    const api = apiWith({ submitPick });

    render(
      <DraftWorkspace draftId="draft-7" initialView={firstView} api={api} />,
    );

    expect(screen.getAllByText('Lightning Bolt')).toHaveLength(2);
    fireEvent.click(
      screen.getByRole('button', {
        name: /lightning bolt.*instance instance-b/i,
      }),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Make pick' }));

    await waitFor(() => {
      expect(submitPick).toHaveBeenCalledWith('draft-7', 'instance-b');
    });
    expect(screen.getByText('Seat 1 · Pack 1 · Pick 2')).toBeTruthy();
    expect(
      screen.getByRole('heading', { name: /lightning bolt ×1/i }),
    ).toBeTruthy();
    expect(screen.getByText('Instance instance-b')).toBeTruthy();
    expect(screen.getByRole('status').textContent).toContain(
      'Your next legal pick is ready',
    );
  });

  it('loads its seat-safe view and provides explicit retry recovery on an unavailable draft', async () => {
    const loadDraft = vi.fn().mockRejectedValue(new Error('offline'));
    const api = apiWith({ loadDraft });

    render(<DraftWorkspace draftId="draft-7" api={api} />);

    expect(
      await screen.findByRole('heading', { name: 'Your draft is unavailable' }),
    ).toBeTruthy();
    expect(screen.getByRole('alert').textContent).toContain(
      'draft could not be updated',
    );
    fireEvent.click(
      screen.getByRole('button', { name: 'Retry loading draft' }),
    );
    await waitFor(() => expect(loadDraft).toHaveBeenCalledTimes(2));
  });

  it('refreshes a stale pick view and clears the obsolete selection', async () => {
    const refreshed: DraftView = {
      ...firstView,
      pick_number: 2,
      current_pack: [firstView.current_pack[2]],
      pool: [firstView.current_pack[0]],
    };
    const loadDraft = vi.fn().mockResolvedValue(refreshed);
    const api = apiWith({
      submitPick: vi.fn().mockRejectedValue(new Error('stale pick')),
      loadDraft,
    });

    render(
      <DraftWorkspace draftId="draft-7" initialView={firstView} api={api} />,
    );
    fireEvent.click(
      screen.getByRole('button', {
        name: /counterspell.*instance instance-c/i,
      }),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Make pick' }));

    expect((await screen.findByRole('alert')).textContent).toContain(
      'draft could not be updated',
    );
    await waitFor(() => expect(loadDraft).toHaveBeenCalledWith('draft-7'));
    const pickButton = screen.getByRole('button', { name: 'Make pick' });
    expect((pickButton as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText('Seat 1 · Pack 1 · Pick 2')).toBeTruthy();
  });

  it('resets to a replacement draft and never submits a pick to the previous draft', async () => {
    const secondView: DraftView = {
      ...firstView,
      draft_id: 'draft-8',
      current_pack: [
        {
          instance_id: 'instance-d',
          cube_card_id: 'cube-d',
          name: 'Swords to Plowshares',
        },
      ],
    };
    const submitPick = vi.fn().mockResolvedValue(secondView);
    const api = apiWith({ submitPick });
    const rendered = render(
      <DraftWorkspace draftId="draft-7" initialView={firstView} api={api} />,
    );

    rendered.rerender(
      <DraftWorkspace draftId="draft-8" initialView={secondView} api={api} />,
    );
    fireEvent.click(
      screen.getByRole('button', {
        name: /swords to plowshares.*instance instance-d/i,
      }),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Make pick' }));

    await waitFor(() => {
      expect(submitPick).toHaveBeenCalledWith('draft-8', 'instance-d');
    });
    expect(screen.queryByText('Counterspell')).toBeNull();
  });

  it('ignores a late response from a draft that was replaced before loading completed', async () => {
    const lateFirstDraft = deferred<DraftView>();
    const secondView: DraftView = {
      ...firstView,
      draft_id: 'draft-8',
      current_pack: [
        {
          instance_id: 'instance-d',
          cube_card_id: 'cube-d',
          name: 'Swords to Plowshares',
        },
      ],
    };
    const api = apiWith({
      loadDraft: vi.fn().mockReturnValue(lateFirstDraft.promise),
    });
    const rendered = render(<DraftWorkspace draftId="draft-7" api={api} />);

    rendered.rerender(
      <DraftWorkspace draftId="draft-8" initialView={secondView} api={api} />,
    );
    lateFirstDraft.resolve(firstView);

    expect(await screen.findByText('Swords to Plowshares')).toBeTruthy();
    await Promise.resolve();
    expect(screen.queryByText('Counterspell')).toBeNull();
  });

  it('makes the completed draft and full pool clear without a pick action', () => {
    render(
      <DraftWorkspace
        draftId="draft-7"
        initialView={{
          ...firstView,
          status: 'completed',
          current_pack: [],
          pool: firstView.current_pack,
        }}
        api={apiWith()}
      />,
    );

    expect(
      screen.getByRole('heading', { name: 'Your pool is ready to review.' }),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Make pick' })).toBeNull();
    expect(screen.getByText('3 picked')).toBeTruthy();
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
