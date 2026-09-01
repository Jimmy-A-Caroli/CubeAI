import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import App from './App';

describe('App', () => {
  it('renders the accessible foundation heading and backend connection status', () => {
    render(<App />);

    expect(
      screen.getByRole('heading', { level: 1, name: 'CubeAI foundation' }),
    ).toBeTruthy();
    expect(screen.getByRole('status').textContent).toBe('Backend connected');
  });
});
