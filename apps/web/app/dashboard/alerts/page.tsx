import { LiveStreamStatus } from "@/components/stream/live-stream-status";
import { NotificationsCheck } from "@/components/ops/notifications-check";

export default function AlertsPage() {
  return (
    <section style={{ display: "grid", gap: 16 }}>
      <article className="card" style={{ display: "grid", gap: 8 }}>
        <h2 style={{ margin: 0 }}>Alerts and Stream Health</h2>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Stream states fail loudly: connected, reconnecting, stale, or degraded.
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <LiveStreamStatus channel="risk" />
          <LiveStreamStatus channel="orders" />
          <LiveStreamStatus channel="fills" />
        </div>
      </article>
      <NotificationsCheck />
    </section>
  );
}

