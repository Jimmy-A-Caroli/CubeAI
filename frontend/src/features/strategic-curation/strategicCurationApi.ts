export type SupportLevel = 'none' | 'supports' | 'strong';

export type StrategicProposal = {
  target_id: string;
  identity_scope: 'cube_membership';
  target_type: 'macro_path' | 'package';
  target: string;
  proposed_support_level: SupportLevel | null;
  current_support_level: SupportLevel | null;
  rationale: string | null;
  evidence_sources: Array<{
    id: string;
    kind: string;
    url: string;
    published_on: string;
    currentness: string;
  }>;
  card: {
    name: string;
    image_url: string | null;
    mana_value: number | null;
    colors: string[];
    type_line: string | null;
  };
};

export type StrategicCurationCard = {
  target_id: string;
  card: StrategicProposal['card'];
  relations: Array<Omit<StrategicProposal, 'card'>>;
};

export type StrategicCurationSession = {
  proposal_set_id: string;
  cube_version_id: string;
  vocabulary_version: string;
  target_cell_count: number;
  cards: StrategicCurationCard[];
};

export type StrategicDecision = Pick<
  StrategicProposal,
  'target_id' | 'identity_scope' | 'target_type' | 'target'
> & { support_level: SupportLevel };

export type StrategicSubmission = {
  assignment_artifact: object;
  coverage_report: object;
  artifact_filename: string;
  coverage_filename: string;
  reviewed_count: number;
  unknown_remaining: number;
};

type ErrorPayload = { code?: unknown; detail?: unknown };

export class StrategicCurationApiError extends Error {
  constructor(
    message: string,
    readonly code = 'REQUEST_FAILED',
  ) {
    super(message);
    this.name = 'StrategicCurationApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: init?.body ? { 'content-type': 'application/json' } : undefined,
    ...init,
  });
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new StrategicCurationApiError(
      'The local curation service returned an invalid response.',
    );
  }
  if (!response.ok) {
    const error = payload as ErrorPayload;
    throw new StrategicCurationApiError(
      typeof error.detail === 'string'
        ? error.detail
        : 'The curation request failed.',
      typeof error.code === 'string' ? error.code : undefined,
    );
  }
  return payload as T;
}

export type StrategicCurationApi = {
  loadSession(): Promise<StrategicCurationSession>;
  submit(
    session: StrategicCurationSession,
    decisions: StrategicDecision[],
  ): Promise<StrategicSubmission>;
};

export const localStrategicCurationApi: StrategicCurationApi = {
  loadSession: () =>
    request<StrategicCurationSession>('/v1/strategic-curation'),
  submit: (session, decisions) =>
    request<StrategicSubmission>('/v1/strategic-curation/submissions', {
      method: 'POST',
      body: JSON.stringify({
        cube_version_id: session.cube_version_id,
        vocabulary_version: session.vocabulary_version,
        proposal_set_id: session.proposal_set_id,
        decisions,
      }),
    }),
};
