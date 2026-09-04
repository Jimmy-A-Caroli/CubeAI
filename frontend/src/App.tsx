import { useEffect, useState } from 'react';

import DraftWorkspace from './features/draft/DraftWorkspace';
import ImportValidationPanel from './import-validation/ImportValidationPanel';
import type { DraftView } from './import-validation/api';
import './App.css';

export default function App() {
  const [connected, setConnected] = useState(false);
  const [draft, setDraft] = useState<DraftView | null>(null);
  useEffect(() => {
    if (typeof fetch !== 'function') return;
    void fetch('/health')
      .then((response) => (response.ok ? response.json() : null))
      .then((payload: unknown) => {
        const healthy =
          typeof payload === 'object' &&
          payload !== null &&
          'status' in payload &&
          payload.status === 'ok';
        setConnected(healthy);
      })
      .catch(() => setConnected(false));
  }, []);

  return (
    <main className="app-shell">
      <header className="app-shell__header">
        <div>
          <p className="app-shell__mark" aria-hidden="true">
            □
          </p>
          <p className="app-shell__eyebrow">CubeAI local draft</p>
          <h1>Draft a Cube, locally</h1>
        </div>
        <p className="status" role="status" aria-live="polite">
          {connected ? 'Backend connected' : 'Backend unavailable'}
        </p>
      </header>

      {draft === null ? (
        <ImportValidationPanel onDraftStarted={setDraft} />
      ) : (
        <section className="app-shell__draft" aria-label="Active local draft">
          <div className="app-shell__draft-actions">
            <p>
              Your draft is saved locally. You can resume it after a refresh.
            </p>
            <button type="button" onClick={() => setDraft(null)}>
              Start another draft
            </button>
          </div>
          <DraftWorkspace draftId={draft.draft_id} initialView={draft} />
        </section>
      )}
    </main>
  );
}
