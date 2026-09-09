import { useEffect, useState } from 'react';

import DraftWorkspace from './features/draft/DraftWorkspace';
import StrategicCurationPage from './features/strategic-curation/StrategicCurationPage';
import ImportValidationPanel from './import-validation/ImportValidationPanel';
import type { DraftView } from './import-validation/api';
import './App.css';

export default function App() {
  const [connected, setConnected] = useState(false);
  const [draft, setDraft] = useState<DraftView | null>(null);
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);
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
        <nav aria-label="Local tools">
          <a href="/">Draft</a>{' '}
          <a href="/curation/strategic">Strategic curation</a>
        </nav>
      </header>

      {path === '/curation/strategic' ? (
        <StrategicCurationPage />
      ) : draft === null ? (
        <ImportValidationPanel onDraftStarted={setDraft} />
      ) : (
        <section className="app-shell__draft" aria-label="Active local draft">
          <p className="app-shell__draft-note">
            Your draft is saved locally. You can resume it after a refresh.
          </p>
          <DraftWorkspace
            draftId={draft.draft_id}
            initialView={draft}
            onNewDraft={() => setDraft(null)}
          />
        </section>
      )}
    </main>
  );
}
