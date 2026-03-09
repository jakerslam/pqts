import Link from "next/link";

export default function DashboardHomePage() {
  return (
    <section className="grid">
      <article className="card">
        <h3>Portfolio</h3>
        <p>Account equity, exposure, and attribution panels.</p>
        <Link href="/dashboard/portfolio">Open portfolio view</Link>
      </article>
      <article className="card">
        <h3>Execution</h3>
        <p>Orders, fills, and execution quality telemetry.</p>
        <Link href="/dashboard/execution">Open execution view</Link>
      </article>
      <article className="card">
        <h3>Risk</h3>
        <p>Kill-switch events, drawdown, and guardrails.</p>
        <Link href="/dashboard/risk">Open risk view</Link>
      </article>
    </section>
  );
}
