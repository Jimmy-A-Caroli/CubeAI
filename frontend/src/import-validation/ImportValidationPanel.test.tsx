import axe from 'axe-core';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import ImportValidationPanel from './ImportValidationPanel';

const successfulImport = {
  outcome: 'usable',
  cube_version_id: 'cube-version-1',
  usable: true,
  diagnostics: [
    {
      code: 'SOURCE_WARNING',
      severity: 'warning',
      message: 'One note was retained.',
    },
  ],
  supplementary_boards: ['Maybeboard'],
};

const draftableValidation = {
  draftable: true,
  usable_membership_count: 360,
  diagnostics: [],
};

function jsonResponse(payload: unknown, ok = true, status = 200) {
  return { ok, status, json: () => Promise.resolve(payload) };
}

describe('ImportValidationPanel', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('imports, validates, presents the non-blocking supplementary-board warning, and starts a draft', async () => {
    const onDraftStarted = vi.fn();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(successfulImport))
      .mockResolvedValueOnce(jsonResponse(draftableValidation))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            draft_id: 'draft-1',
            cube_version_id: 'cube-version-1',
            status: 'in_progress',
            pack_number: 1,
            pick_number: 1,
            current_pack: [],
            pool: [],
          },
          true,
          201,
        ),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<ImportValidationPanel onDraftStarted={onDraftStarted} />);

    fireEvent.change(screen.getByLabelText('CubeCobra ID'), {
      target: { value: 'https://cubecobra.com/cube/overview/modovintage' },
    });
    fireEvent.change(screen.getByLabelText('Local cube name'), {
      target: { value: 'Vintage Cube' },
    });
    fireEvent.submit(
      screen.getByRole('button', { name: 'Import Cube' }).closest('form')!,
    );

    await screen.findByRole('heading', { name: 'Import result' });
    expect(
      screen.getByLabelText('Supplementary board warning').textContent,
    ).toContain('Maybeboard remains available at the source');
    expect(screen.getByText('SOURCE_WARNING')).toBeTruthy();
    expect(
      screen
        .getByRole('button', { name: 'Start draft' })
        .hasAttribute('disabled'),
    ).toBe(false);
    expect(fetchMock.mock.calls[0]).toEqual([
      '/v1/cube-imports',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          identifier: 'modovintage',
          cube_name: 'Vintage Cube',
          offline: false,
        }),
      }),
    ]);
    expect(fetchMock.mock.calls[1][0]).toBe(
      '/v1/cube-versions/cube-version-1/validation',
    );

    fireEvent.click(screen.getByRole('button', { name: 'Start draft' }));

    await screen.findByText(/Draft draft-1 started/);
    expect(onDraftStarted).toHaveBeenCalledWith(
      expect.objectContaining({ draft_id: 'draft-1' }),
    );
    expect(fetchMock.mock.calls[2][0]).toBe('/v1/drafts');
  });

  it('keeps draft start unavailable when capacity validation fails and groups its error', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(successfulImport))
      .mockResolvedValueOnce(
        jsonResponse({
          draftable: false,
          usable_membership_count: 90,
          diagnostics: [
            {
              code: 'INSUFFICIENT_MEMBERSHIPS',
              severity: 'error',
              message: 'The draft needs 360 memberships.',
            },
          ],
        }),
      );
    vi.stubGlobal('fetch', fetchMock);
    render(<ImportValidationPanel />);

    fireEvent.change(screen.getByLabelText('CubeCobra ID'), {
      target: { value: 'small-cube' },
    });
    fireEvent.change(screen.getByLabelText('Local cube name'), {
      target: { value: 'Small Cube' },
    });
    fireEvent.submit(
      screen.getByRole('button', { name: 'Import Cube' }).closest('form')!,
    );

    await screen.findByText('INSUFFICIENT_MEMBERSHIPS');
    expect(
      screen
        .getByRole('button', { name: 'Start draft' })
        .hasAttribute('disabled'),
    ).toBe(true);
    expect(screen.getByLabelText('error diagnostics').textContent).toContain(
      'The draft needs 360 memberships.',
    );
  });

  it('requires a fresh validation when draft configuration changes', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(successfulImport))
        .mockResolvedValueOnce(jsonResponse(draftableValidation)),
    );
    render(<ImportValidationPanel />);
    fireEvent.change(screen.getByLabelText('CubeCobra ID'), {
      target: { value: 'modovintage' },
    });
    fireEvent.change(screen.getByLabelText('Local cube name'), {
      target: { value: 'Vintage Cube' },
    });
    fireEvent.submit(
      screen.getByRole('button', { name: 'Import Cube' }).closest('form')!,
    );

    await screen.findByRole('heading', { name: 'Draft validation' });
    expect(
      screen
        .getByRole('button', { name: 'Start draft' })
        .hasAttribute('disabled'),
    ).toBe(false);

    fireEvent.change(screen.getByLabelText('Cards per pack'), {
      target: { value: '16' },
    });

    expect(screen.queryByRole('button', { name: 'Start draft' })).toBeNull();
    expect(
      screen.queryByRole('heading', { name: 'Draft validation' }),
    ).toBeNull();
  });

  it('ignores a superseded in-flight validation after draft configuration changes', async () => {
    const delayedValidation = deferred<ReturnType<typeof jsonResponse>>();
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(successfulImport))
        .mockImplementationOnce(() => delayedValidation.promise),
    );
    render(<ImportValidationPanel />);
    fireEvent.change(screen.getByLabelText('CubeCobra ID'), {
      target: { value: 'modovintage' },
    });
    fireEvent.change(screen.getByLabelText('Local cube name'), {
      target: { value: 'Vintage Cube' },
    });
    fireEvent.submit(
      screen.getByRole('button', { name: 'Import Cube' }).closest('form')!,
    );

    await screen.findByRole('heading', { name: 'Import result' });
    fireEvent.change(screen.getByLabelText('Cards per pack'), {
      target: { value: '16' },
    });
    delayedValidation.resolve(jsonResponse(draftableValidation));

    await waitFor(() => {
      expect(
        screen.queryByRole('heading', { name: 'Draft validation' }),
      ).toBeNull();
    });
    expect(screen.queryByRole('button', { name: 'Start draft' })).toBeNull();
  });

  it('shows a structured API error without exposing a failed request implementation', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(
          jsonResponse(
            {
              code: 'SOURCE_UNAVAILABLE',
              detail: 'CubeCobra is temporarily unavailable.',
            },
            false,
            503,
          ),
        )
        .mockResolvedValueOnce(jsonResponse(successfulImport))
        .mockResolvedValueOnce(jsonResponse(draftableValidation)),
    );
    render(<ImportValidationPanel />);

    fireEvent.change(screen.getByLabelText('CubeCobra ID'), {
      target: { value: 'unavailable' },
    });
    fireEvent.change(screen.getByLabelText('Local cube name'), {
      target: { value: 'Unavailable Cube' },
    });
    fireEvent.submit(
      screen.getByRole('button', { name: 'Import Cube' }).closest('form')!,
    );

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('SOURCE_UNAVAILABLE');
    expect(alert.textContent).toContain(
      'CubeCobra is temporarily unavailable.',
    );

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    await screen.findByRole('heading', { name: 'Draft validation' });
  });

  it('has no baseline axe accessibility violations', async () => {
    vi.stubGlobal('fetch', vi.fn());
    const view = render(<ImportValidationPanel />);

    const result = await axe.run(view.container);

    expect(result.violations).toEqual([]);
  });

  it('reports network failure with a retryable local-service message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    render(<ImportValidationPanel />);

    fireEvent.change(screen.getByLabelText('CubeCobra ID'), {
      target: { value: 'offline' },
    });
    fireEvent.change(screen.getByLabelText('Local cube name'), {
      target: { value: 'Offline Cube' },
    });
    fireEvent.submit(
      screen.getByRole('button', { name: 'Import Cube' }).closest('form')!,
    );

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toContain('NETWORK_ERROR');
    });
  });
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}
