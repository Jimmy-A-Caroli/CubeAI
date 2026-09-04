export type DraftCard = {
  instance_id: string;
  cube_card_id: string;
  name: string;
};

export type DraftView = {
  draft_id: string;
  cube_version_id: string;
  status: string;
  seat_number: number;
  pack_number: number;
  pick_number: number;
  current_pack: DraftCard[];
  pool: DraftCard[];
};

type ErrorPayload = {
  code?: unknown;
  detail?: unknown;
};

export class DraftApiError extends Error {
  readonly code: string;

  constructor(message: string, code = 'REQUEST_FAILED') {
    super(message);
    this.name = 'DraftApiError';
    this.code = code;
  }
}

export type DraftApi = {
  loadDraft(draftId: string): Promise<DraftView>;
  submitPick(draftId: string, cardInstanceId: string): Promise<DraftView>;
};

async function responseJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new DraftApiError(
      'The local draft service returned an invalid response.',
    );
  }
}

function errorFromPayload(payload: unknown): DraftApiError {
  const parsed = payload as ErrorPayload | null;
  const code =
    typeof parsed?.code === 'string' ? parsed.code : 'REQUEST_FAILED';
  const detail =
    typeof parsed?.detail === 'string'
      ? parsed.detail
      : 'The local draft service could not complete that request.';
  return new DraftApiError(detail, code);
}

async function requestDraft(
  path: string,
  init?: RequestInit,
): Promise<DraftView> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new DraftApiError(
      'Cannot reach the local CubeAI service. Try again after it is running.',
    );
  }

  const payload = await responseJson(response);
  if (!response.ok) {
    throw errorFromPayload(payload);
  }
  return payload as DraftView;
}

export const localDraftApi: DraftApi = {
  loadDraft(draftId) {
    return requestDraft(`/v1/drafts/${encodeURIComponent(draftId)}`);
  },
  submitPick(draftId, cardInstanceId) {
    return requestDraft(`/v1/drafts/${encodeURIComponent(draftId)}/picks`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ card_instance_id: cardInstanceId }),
    });
  },
};
