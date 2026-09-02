import './App.css';
import { useEffect, useState } from 'react';

export default function App() {
  const [connected, setConnected] = useState(true);
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
      <section aria-labelledby="foundation-heading" className="foundation">
        <p className="foundation-mark" aria-hidden="true">
          □
        </p>
        <h1 id="foundation-heading">CubeAI foundation</h1>
        <p className="status" role="status">
          {connected ? 'Backend connected' : 'Backend unavailable'}
        </p>
      </section>
    </main>
  );
}
