import { loadReplayEvents, replayHash } from "@/lib/ops/reference-data";

function eventTypeCounts(events: Array<Record<string, unknown>>): Array<{ event_type: string; count: number }> {
  const counts = new Map<string, number>();
  for (const row of events) {
    const key = String(row.event_type ?? "unknown");
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([event_type, count]) => ({ event_type, count }))
    .sort((left, right) => right.count - left.count || left.event_type.localeCompare(right.event_type));
}

export default function ReplayPage() {
  const events = loadReplayEvents(240);
  const counts = eventTypeCounts(events);
  const hash = replayHash(events);

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <article className="card">
        <h2 style={{ marginTop: 0 }}>Deterministic Replay Timeline</h2>
        <p style={{ margin: "0 0 8px", color: "var(--muted)" }}>
          Replay hash: <code>{hash}</code>
        </p>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Events loaded: {events.length}
        </p>
      </article>

      <article className="card">
        <h3 style={{ marginTop: 0 }}>Event Type Distribution</h3>
        {counts.length === 0 ? (
          <p style={{ margin: 0, color: "var(--muted)" }}>No replay events found in latest reference bundle.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Event Type</th>
                <th align="right">Count</th>
              </tr>
            </thead>
            <tbody>
              {counts.map((row) => (
                <tr key={row.event_type}>
                  <td>{row.event_type}</td>
                  <td align="right">{row.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </article>

      <article className="card">
        <h3 style={{ marginTop: 0 }}>Timeline</h3>
        {events.length === 0 ? (
          <p style={{ margin: 0, color: "var(--muted)" }}>No timeline entries available.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Cycle</th>
                <th align="left">Event</th>
                <th align="left">Market</th>
                <th align="left">Strategy</th>
                <th align="left">Run ID</th>
              </tr>
            </thead>
            <tbody>
              {events.slice(0, 150).map((event, index) => (
                <tr key={`${String(event.event_id ?? index)}:${index}`}>
                  <td>{String(event.cycle ?? "-")}</td>
                  <td>{String(event.event_type ?? "unknown")}</td>
                  <td>{String(event.market ?? "-")}</td>
                  <td>{String(event.strategy ?? "-")}</td>
                  <td>{String(event.run_id ?? "-")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </article>
    </section>
  );
}
