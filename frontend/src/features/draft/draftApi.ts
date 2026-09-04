export type DraftCard = {
  instance_id: string;
  cube_card_id: string;
  name: string;
  image_url: string | null;
  mana_cost: string | null;
  type_line: string | null;
  oracle_text: string | null;
  power: string | null;
  toughness: string | null;
  loyalty: string | null;
  colors: string[];
};

export type DraftConfiguration = {
  seats: number;
  packs_per_seat: number;
  pack_size: number;
  seed: number;
};

export type DraftView = {
  draft_id: string;
  cube_version_id: string;
  status: string;
  seat_number: number;
  pack_number: number;
  pick_number: number;
  cube_name: string;
  configuration: DraftConfiguration;
  current_pack: DraftCard[];
  pool: DraftCard[];
};

export type DraftReviewPick = {
  seat_number: number;
  round_number: number;
  pick_number: number;
  card: Omit<DraftCard, 'instance_id' | 'cube_card_id'>;
  bot_provenance: {
    strategy_id: string;
    strategy_version: string;
    rating_artifact_id: string;
    rating_artifact_version: string;
    selected_rating: number;
    rating_lookup_outcome: string;
    tie_break_reason: string;
  } | null;
};

export type DraftReview = {
  draft_id: string;
  cube_name: string;
  configuration: DraftConfiguration;
  human_picks: DraftReviewPick[];
  bot_picks: DraftReviewPick[];
};

export type DraftTracking = {
  draft_id: string;
  observer_seat: number;
  tracked_card_instance_ids: string[];
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
  loadReview(draftId: string): Promise<DraftReview>;
  loadTracking(draftId: string): Promise<DraftTracking>;
  trackCard(draftId: string, cardInstanceId: string): Promise<DraftTracking>;
  untrackCard(draftId: string, cardInstanceId: string): Promise<DraftTracking>;
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

async function requestDraft<T>(path: string, init?: RequestInit): Promise<T> {
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
  return payload as T;
}

export const localDraftApi: DraftApi = {
  loadDraft(draftId) {
    return requestDraft<DraftView>(`/v1/drafts/${encodeURIComponent(draftId)}`);
  },
  submitPick(draftId, cardInstanceId) {
    return requestDraft<DraftView>(
      `/v1/drafts/${encodeURIComponent(draftId)}/picks`,
      {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ card_instance_id: cardInstanceId }),
      },
    );
  },
  loadReview(draftId) {
    return requestDraft<DraftReview>(
      `/v1/drafts/${encodeURIComponent(draftId)}/review`,
    );
  },
  loadTracking(draftId) {
    return requestDraft<DraftTracking>(
      `/v1/drafts/${encodeURIComponent(draftId)}/tracking`,
    );
  },
  trackCard(draftId, cardInstanceId) {
    return requestDraft<DraftTracking>(
      `/v1/drafts/${encodeURIComponent(draftId)}/tracking/${encodeURIComponent(cardInstanceId)}`,
      { method: 'PUT' },
    );
  },
  untrackCard(draftId, cardInstanceId) {
    return requestDraft<DraftTracking>(
      `/v1/drafts/${encodeURIComponent(draftId)}/tracking/${encodeURIComponent(cardInstanceId)}`,
      { method: 'DELETE' },
    );
  },
};
