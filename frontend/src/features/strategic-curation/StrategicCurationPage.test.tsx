import axe from 'axe-core';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import StrategicCurationPage from './StrategicCurationPage';
import type {
  StrategicCurationApi,
  StrategicCurationSession,
} from './strategicCurationApi';

const session: StrategicCurationSession = {
  proposal_set_id: 'proposals-1',
  cube_version_id: 'version-1',
  vocabulary_version: 'vintage-cube-strategic-v1',
  target_cell_count: 8,
  cards: [
    {
      target_id: 'member-1',
      card: {
        name: 'Entomb',
        image_url: null,
        mana_value: 1,
        colors: ['B'],
        type_line: 'Instant',
      },
      relations: [
        {
          target_id: 'member-1',
          identity_scope: 'cube_membership',
          target_type: 'package',
          target: 'reanimator',
          proposed_support_level: 'strong',
          rationale: 'Explicit evidence.',
          evidence_sources: [
            {
              id: 'guide',
              kind: 'official',
              url: 'https://example.test/guide',
              published_on: 'undated',
              currentness: 'current',
            },
          ],
          current_support_level: null,
        },
      ],
    },
  ],
};

function api(
  submit = vi.fn().mockResolvedValue({
    assignment_artifact: {},
    coverage_report: {},
    artifact_filename: 'assignments.json',
    coverage_filename: 'coverage.json',
    reviewed_count: 1,
    unknown_remaining: 3,
  }),
): StrategicCurationApi {
  return { loadSession: vi.fn().mockResolvedValue(session), submit };
}

describe('StrategicCurationPage', () => {
  it('persists, clears, and submits only explicit human decisions', async () => {
    const submit = vi.fn().mockResolvedValue({
      assignment_artifact: {},
      coverage_report: {},
      artifact_filename: 'assignments.json',
      coverage_filename: 'coverage.json',
      reviewed_count: 1,
      unknown_remaining: 3,
    });
    const client = api(submit);
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:test'),
      revokeObjectURL: vi.fn(),
    });
    const view = render(<StrategicCurationPage api={client} />);
    await screen.findByRole('heading', { name: 'Entomb' });
    fireEvent.click(screen.getByRole('button', { name: 'strong' }));
    await waitFor(() =>
      expect(
        window.localStorage.getItem(
          'cubeai.strategic-curation.draft.v1:version-1:proposals-1',
        ),
      ).toContain('strong'),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }));
    expect(
      screen.getByText('0 reviewed / 8 reviewed target cells'),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'none' }));
    fireEvent.click(
      screen.getByRole('button', { name: 'Generate reviewed artifacts' }),
    );
    await waitFor(() => expect(submit).toHaveBeenCalled());
    expect(
      window.localStorage.getItem(
        'cubeai.strategic-curation.draft.v1:version-1:proposals-1',
      ),
    ).toContain('none');
    view.unmount();
  });

  it('has no baseline accessibility violations', async () => {
    const view = render(<StrategicCurationPage api={api()} />);
    await screen.findByRole('heading', { name: 'Entomb' });
    const result = await axe.run(view.container);
    expect(result.violations).toEqual([]);
  });
});
