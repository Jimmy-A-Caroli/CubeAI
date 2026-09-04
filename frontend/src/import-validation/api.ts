export type DiagnosticSeverity = 'error' | 'warning' | 'info';

export interface Diagnostic {
  code: string;
  severity: DiagnosticSeverity;
  message: string;
}

export interface DraftConfiguration {
  seats: number;
  packs_per_seat: number;
  pack_size: number;
  seed: number;
}

export interface CubeImportResult {
  outcome: string;
  cube_version_id: string | null;
  usable: boolean | null;
  diagnostics: Diagnostic[];
  supplementary_boards: string[];
}

export interface CubeValidationResult {
  draftable: boolean;
  usable_membership_count: number;
  diagnostics: Diagnostic[];
}

export interface DraftCard {
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
}

export interface DraftView {
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
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(status: number, code: string, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

interface ErrorPayload {
  code?: unknown;
  detail?: unknown;
}

async function request<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      0,
      'NETWORK_ERROR',
      'The local CubeAI service could not be reached.',
    );
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    // A malformed response is handled with the same safe error presentation.
  }

  if (!response.ok) {
    const error = isErrorPayload(payload) ? payload : {};
    throw new ApiError(
      response.status,
      typeof error.code === 'string' ? error.code : 'REQUEST_FAILED',
      typeof error.detail === 'string'
        ? error.detail
        : 'CubeAI could not complete that request.',
    );
  }
  return payload as T;
}

function isErrorPayload(payload: unknown): payload is ErrorPayload {
  return typeof payload === 'object' && payload !== null;
}

export function importCube(
  identifier: string,
  cubeName: string,
): Promise<CubeImportResult> {
  return request<CubeImportResult>('/v1/cube-imports', {
    identifier,
    cube_name: cubeName,
    offline: false,
  });
}

export function validateCube(
  cubeVersionId: string,
  configuration: DraftConfiguration,
): Promise<CubeValidationResult> {
  return request<CubeValidationResult>(
    `/v1/cube-versions/${encodeURIComponent(cubeVersionId)}/validation`,
    configuration,
  );
}

export function startDraft(
  draftId: string,
  cubeVersionId: string,
  configuration: DraftConfiguration,
): Promise<DraftView> {
  return request<DraftView>('/v1/drafts', {
    draft_id: draftId,
    cube_version_id: cubeVersionId,
    configuration,
  });
}
