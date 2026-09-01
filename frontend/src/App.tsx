import './App.css';

export default function App() {
  return (
    <main className="app-shell">
      <section aria-labelledby="foundation-heading" className="foundation">
        <p className="foundation-mark" aria-hidden="true">
          □
        </p>
        <h1 id="foundation-heading">CubeAI foundation</h1>
        <p className="status" role="status">
          Backend connected
        </p>
      </section>
    </main>
  );
}
