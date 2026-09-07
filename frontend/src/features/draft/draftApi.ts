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
  mode?: 'human_seat' | 'all_bot';
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

export type InspectorCard = DraftCard & {
  printing_id: string | null;
  oracle_id: string | null;
};

export type InspectorWheelFact = {
  role: 'first_seen' | 'returned';
  card: InspectorCard;
  first_seen_sequence: number;
  returned_sequence: number;
};

export type DraftInspectorDecision = {
  sequence: number;
  seat_number: number;
  actor_origin: 'human' | 'bot';
  actor_id: string;
  round_number: number;
  pick_number: number;
  physical_pack_number: number;
  chosen_card: InspectorCard;
  cards_seen: InspectorCard[];
  pool_before: InspectorCard[];
  seen_before_pick_count: number;
  bot_provenance: DraftReviewPick['bot_provenance'];
  wheel_facts: InspectorWheelFact[];
};

export type DraftInspector = {
  draft_id: string;
  cube_version_id: string;
  cube_name: string;
  configuration: DraftConfiguration;
  decisions: DraftInspectorDecision[];
};

export type DraftTracking = {
  draft_id: string;
  observer_seat: number;
  tracked_card_instance_ids: string[];
};
export type PickReview = {
  id: string;
  author: string;
  cube_version_id: string;
  draft_id: string;
  sequence: number;
  seat_number: number;
  pack_number: number;
  pick_number: number;
  card_instance_id: string;
  strategy_ref: string | null;
  assessment: string;
  reasons: string[];
  note: string | null;
  suggested_rating: number | null;
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
  loadInspector(draftId: string): Promise<DraftInspector>;
  loadTracking(draftId: string): Promise<DraftTracking>;
  trackCard(draftId: string, cardInstanceId: string): Promise<DraftTracking>;
  untrackCard(draftId: string, cardInstanceId: string): Promise<DraftTracking>;
  loadPickReview?: (
    draftId: string,
    sequence: number,
  ) => Promise<PickReview | null>;
  savePickReview?: (
    draftId: string,
    review: Omit<PickReview, 'cube_version_id' | 'draft_id' | 'strategy_ref'>,
  ) => Promise<PickReview>;
  deletePickReview?: (draftId: string, sequence: number) => Promise<void>;
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
  loadInspector(draftId) {
    return requestDraft<DraftInspector>(
      `/v1/drafts/${encodeURIComponent(draftId)}/inspector`,
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
  async loadPickReview(draftId, sequence) {
    try {
      return await requestDraft<PickReview>(
        `/v1/drafts/${encodeURIComponent(draftId)}/inspector/annotations/${sequence}`,
      );
    } catch (error) {
      if (error instanceof DraftApiError && error.code === 'REVIEW_NOT_FOUND')
        return null;
      throw error;
    }
  },
  savePickReview(draftId, review) {
    return requestDraft<PickReview>(
      `/v1/drafts/${encodeURIComponent(draftId)}/inspector/annotations`,
      {
        method: 'PUT',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(review),
      },
    );
  },
  async deletePickReview(draftId, sequence) {
    await requestDraft<unknown>(
      `/v1/drafts/${encodeURIComponent(draftId)}/inspector/annotations/${sequence}`,
      { method: 'DELETE' },
    );
  },
};
