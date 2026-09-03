import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the accessible foundation heading and connected backend status', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: () => ({ status: 'ok' }) }),
    );

    render(<App />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'CubeAI foundation' }),
    ).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByRole('status').textContent).toBe('Backend connected');
    });
  });

  it('renders backend unavailable when the health request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByRole('status').textContent).toBe(
        'Backend unavailable',
      );
    });
  });
});
