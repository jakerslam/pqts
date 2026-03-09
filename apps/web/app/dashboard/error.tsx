"use client";

export default function DashboardError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <main>
      <section className="card">
        <h2>Dashboard Error</h2>
        <p>{error.message}</p>
        <button type="button" onClick={reset}>
          Retry
        </button>
      </section>
    </main>
  );
}
