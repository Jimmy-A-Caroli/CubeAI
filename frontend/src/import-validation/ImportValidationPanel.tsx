import { type FormEvent, useId, useRef, useState } from 'react';

import {
  ApiError,
  type CubeImportResult,
  type CubeValidationResult,
  type Diagnostic,
  type DiagnosticSeverity,
  type DraftConfiguration,
  type DraftView,
  importCube,
  startDraft,
  validateCube,
} from './api';
import './ImportValidationPanel.css';

export interface ImportValidationPanelProps {
  onDraftStarted?: (draft: DraftView) => void;
}

const defaultConfiguration: DraftConfiguration = {
  seats: 8,
  packs_per_seat: 3,
  pack_size: 15,
  seed: 20260903,
};

type PendingAction = 'importing' | 'starting' | null;
type RetryAction = Exclude<PendingAction, null>;

export default function ImportValidationPanel({
  onDraftStarted,
}: ImportValidationPanelProps) {
  const identifierHintId = useId();
  const [identifier, setIdentifier] = useState('');
  const [cubeName, setCubeName] = useState('');
  const [configuration, setConfiguration] =
    useState<DraftConfiguration>(defaultConfiguration);
  const [importResult, setImportResult] = useState<CubeImportResult | null>(
    null,
  );
  const [validation, setValidation] = useState<CubeValidationResult | null>(
    null,
  );
  const [draft, setDraft] = useState<DraftView | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [retryAction, setRetryAction] = useState<RetryAction>('importing');
  const validationRevision = useRef(0);

  const canStart =
    pendingAction === null &&
    importResult?.usable === true &&
    importResult.cube_version_id !== null &&
    validation?.draftable === true;

  function changeConfiguration(key: keyof DraftConfiguration, value: number) {
    setConfiguration((current) => ({ ...current, [key]: value }));
    validationRevision.current += 1;
    setValidation(null);
    setDraft(null);
  }

  function changeIdentifier(value: string) {
    setIdentifier(value);
    invalidateImportedState();
  }

  function changeCubeName(value: string) {
    setCubeName(value);
    invalidateImportedState();
  }

  function invalidateImportedState() {
    validationRevision.current += 1;
    setError(null);
    setImportResult(null);
    setValidation(null);
    setDraft(null);
  }

  async function importAndValidate() {
    const requestRevision = validationRevision.current + 1;
    validationRevision.current = requestRevision;
    setPendingAction('importing');
    setError(null);
    setImportResult(null);
    setValidation(null);
    setDraft(null);
    try {
      const imported = await importCube(
        cubeCobraIdentifier(identifier),
        cubeName.trim(),
      );
      if (requestRevision !== validationRevision.current) return;
      setImportResult(imported);
      if (imported.cube_version_id !== null) {
        const nextValidation = await validateCube(
          imported.cube_version_id,
          configuration,
        );
        if (requestRevision === validationRevision.current) {
          setValidation(nextValidation);
        }
      }
    } catch (reason) {
      if (requestRevision === validationRevision.current) {
        setError(toApiError(reason));
        setRetryAction('importing');
      }
    } finally {
      setPendingAction(null);
    }
  }

  function handleImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void importAndValidate();
  }

  async function handleStart() {
    if (!canStart || importResult?.cube_version_id === null) return;
    setPendingAction('starting');
    setError(null);
    try {
      const started = await startDraft(
        createDraftId(),
        importResult.cube_version_id,
        configuration,
      );
      setDraft(started);
      onDraftStarted?.(started);
    } catch (reason) {
      setError(toApiError(reason));
      setRetryAction('starting');
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <section
      className="import-validation"
      aria-labelledby="cube-import-heading"
    >
      <div className="import-validation__intro">
        <p className="import-validation__eyebrow">New local draft</p>
        <h2 id="cube-import-heading">Import a CubeCobra Cube</h2>
        <p>
          Enter a CubeCobra short ID, full ID, or Cube URL. CubeAI will resolve
          and validate its mainboard before a draft can begin.
        </p>
      </div>

      <form className="import-validation__form" onSubmit={handleImport}>
        <label htmlFor="cube-identifier">CubeCobra ID</label>
        <input
          aria-describedby={identifierHintId}
          autoComplete="off"
          id="cube-identifier"
          minLength={1}
          name="cube-identifier"
          onChange={(event) => changeIdentifier(event.target.value)}
          placeholder="modovintage"
          required
          value={identifier}
        />
        <p className="import-validation__hint" id={identifierHintId}>
          A URL is accepted for convenience. Only its final CubeCobra identifier
          is sent to the local API.
        </p>

        <label htmlFor="cube-name">Local cube name</label>
        <input
          id="cube-name"
          minLength={1}
          name="cube-name"
          onChange={(event) => changeCubeName(event.target.value)}
          placeholder="My Cube"
          required
          value={cubeName}
        />

        <fieldset className="import-validation__configuration">
          <legend>Draft configuration</legend>
          <p className="import-validation__hint">
            Standard eight-seat, three-pack, fifteen-card drafting is prefilled.
          </p>
          <ConfigurationField
            label="Seats"
            name="seats"
            value={configuration.seats}
            onChange={(value) => changeConfiguration('seats', value)}
          />
          <ConfigurationField
            label="Packs per seat"
            name="packs-per-seat"
            value={configuration.packs_per_seat}
            onChange={(value) => changeConfiguration('packs_per_seat', value)}
          />
          <ConfigurationField
            label="Cards per pack"
            name="pack-size"
            value={configuration.pack_size}
            onChange={(value) => changeConfiguration('pack_size', value)}
          />
          <ConfigurationField
            label="Draft seed"
            name="seed"
            value={configuration.seed}
            onChange={(value) => changeConfiguration('seed', value)}
          />
        </fieldset>

        <button disabled={pendingAction !== null} type="submit">
          {pendingAction === 'importing'
            ? 'Importing and validating…'
            : 'Import Cube'}
        </button>
      </form>

      <WorkflowStatus pendingAction={pendingAction} />
      {error !== null ? (
        <RequestError
          error={error}
          onRetry={() =>
            retryAction === 'starting'
              ? void handleStart()
              : void importAndValidate()
          }
        />
      ) : null}
      {importResult !== null ? <ImportSummary result={importResult} /> : null}
      {validation !== null ? (
        <ValidationSummary validation={validation} />
      ) : null}

      {importResult !== null && validation !== null ? (
        <section
          className="import-validation__start"
          aria-labelledby="start-draft-heading"
        >
          <h3 id="start-draft-heading">Start local draft</h3>
          <p>
            {canStart
              ? 'This Cube is draftable with the selected configuration.'
              : 'Resolve the errors above or import a different Cube before starting.'}
          </p>
          <button
            disabled={!canStart}
            onClick={() => void handleStart()}
            type="button"
          >
            {pendingAction === 'starting' ? 'Starting draft…' : 'Start draft'}
          </button>
        </section>
      ) : null}

      {draft !== null ? (
        <p className="import-validation__success" role="status">
          Draft {draft.draft_id} started. Your first pack is ready.
        </p>
      ) : null}
    </section>
  );
}

interface ConfigurationFieldProps {
  label: string;
  name: string;
  value: number;
  onChange: (value: number) => void;
}

function ConfigurationField({
  label,
  name,
  value,
  onChange,
}: ConfigurationFieldProps) {
  return (
    <label
      className="import-validation__number-field"
      htmlFor={`configuration-${name}`}
    >
      <span>{label}</span>
      <input
        id={`configuration-${name}`}
        min="1"
        name={name}
        onChange={(event) => onChange(Number(event.target.value))}
        required
        type="number"
        value={value}
      />
    </label>
  );
}

function WorkflowStatus({ pendingAction }: { pendingAction: PendingAction }) {
  if (pendingAction === null) return null;
  return (
    <p className="import-validation__progress" role="status">
      {pendingAction === 'importing'
        ? 'Importing the CubeCobra source, resolving cards, and validating the draft.'
        : 'Creating and saving the local draft.'}
    </p>
  );
}

function RequestError({
  error,
  onRetry,
}: {
  error: ApiError;
  onRetry: () => void;
}) {
  return (
    <section
      className="import-validation__error"
      role="alert"
      aria-labelledby="request-error-heading"
    >
      <h3 id="request-error-heading">{error.code}</h3>
      <p>{error.message}</p>
      <button onClick={onRetry} type="button">
        Retry
      </button>
    </section>
  );
}

function ImportSummary({ result }: { result: CubeImportResult }) {
  return (
    <section
      className="import-validation__summary"
      aria-labelledby="import-summary-heading"
    >
      <h3 id="import-summary-heading">Import result</h3>
      <p>
        {result.usable === true
          ? 'The source was imported and can be checked for this draft.'
          : 'CubeAI could not create a usable Cube version from this source.'}
      </p>
      {result.cube_version_id !== null ? (
        <p className="import-validation__version">
          Cube version: <code>{result.cube_version_id}</code>
        </p>
      ) : null}
      {result.supplementary_boards.length > 0 ? (
        <aside
          className="import-validation__warning"
          aria-label="Supplementary board warning"
        >
          <strong>Supplementary board not imported.</strong>{' '}
          {result.supplementary_boards.join(', ')} remains available at the
          source, but only the CubeCobra mainboard is used for this draft.
        </aside>
      ) : null}
      <DiagnosticGroups diagnostics={result.diagnostics} />
    </section>
  );
}

function ValidationSummary({
  validation,
}: {
  validation: CubeValidationResult;
}) {
  return (
    <section
      className="import-validation__summary"
      aria-labelledby="validation-summary-heading"
    >
      <h3 id="validation-summary-heading">Draft validation</h3>
      <p>
        {validation.draftable
          ? `${validation.usable_membership_count} usable memberships meet the selected draft capacity.`
          : `${validation.usable_membership_count} usable memberships do not meet the selected draft capacity.`}
      </p>
      <DiagnosticGroups diagnostics={validation.diagnostics} />
    </section>
  );
}

function DiagnosticGroups({ diagnostics }: { diagnostics: Diagnostic[] }) {
  if (diagnostics.length === 0) {
    return <p className="import-validation__clean">No diagnostics reported.</p>;
  }
  const grouped = groupDiagnostics(diagnostics);
  return (
    <div className="import-validation__diagnostics">
      {(['error', 'warning', 'info'] as const).map((severity) => {
        const items = grouped[severity];
        if (items.length === 0) return null;
        return (
          <section key={severity} aria-label={`${severity} diagnostics`}>
            <h4>{severity === 'info' ? 'Information' : `${severity}s`}</h4>
            <ul>
              {items.map((item) => (
                <li key={`${item.code}:${item.message}`}>
                  <code>{item.code}</code> {item.message}
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}

function groupDiagnostics(
  diagnostics: Diagnostic[],
): Record<DiagnosticSeverity, Diagnostic[]> {
  return diagnostics.reduce<Record<DiagnosticSeverity, Diagnostic[]>>(
    (groups, item) => {
      groups[item.severity].push(item);
      return groups;
    },
    { error: [], warning: [], info: [] },
  );
}

function toApiError(reason: unknown): ApiError {
  return reason instanceof ApiError
    ? reason
    : new ApiError(
        0,
        'REQUEST_FAILED',
        'CubeAI could not complete that request.',
      );
}

function createDraftId(): string {
  return `draft-${globalThis.crypto.randomUUID()}`;
}

function cubeCobraIdentifier(value: string): string {
  const trimmed = value.trim();
  if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
    return trimmed;
  }
  try {
    const url = new URL(trimmed);
    if (url.hostname !== 'cubecobra.com') {
      throw new Error('unsupported host');
    }
    const identifier = url.pathname.split('/').filter(Boolean).at(-1);
    if (identifier === undefined || identifier.length === 0) {
      throw new Error('missing identifier');
    }
    return identifier;
  } catch {
    throw new ApiError(
      0,
      'INVALID_SOURCE_INPUT',
      'Enter a CubeCobra ID or a complete cubecobra.com Cube URL.',
    );
  }
}
