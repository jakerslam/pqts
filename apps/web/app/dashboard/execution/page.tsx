import { getFills, getOrders } from "@/lib/api/client";
import { LiveStreamStatus } from "@/components/stream/live-stream-status";
import Link from "next/link";

export default async function ExecutionPage() {
  const [orders, fills] = await Promise.all([getOrders(), getFills()]).catch(() => [[], []]);

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <article className="card">
        <h2 style={{ marginTop: 0 }}>Execution Analytics</h2>
        <p style={{ marginTop: 0, color: "var(--muted)" }}>
          Deep-dive surfaces for transaction-cost quality and order truth lineage.
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
          <LiveStreamStatus channel="orders" />
          <LiveStreamStatus channel="fills" />
        </div>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Link href="/dashboard/execution-quality">Execution Quality Dashboard</Link>
          <Link href="/dashboard/order-truth">Per-Order Truth Drilldown</Link>
          <Link href="/dashboard/replay">Deterministic Replay Timeline</Link>
        </div>
      </article>

      <article className="card">
        <h2 style={{ marginTop: 0 }}>Orders</h2>
        {orders.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>
            No orders available from API. This is an explicit empty/disconnected state, not synthetic demo data.
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Order ID</th>
                <th align="left">Symbol</th>
                <th align="left">Side</th>
                <th align="right">Qty</th>
                <th align="left">Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 25).map((row) => (
                <tr key={row.order_id}>
                  <td>{row.order_id}</td>
                  <td>{row.symbol}</td>
                  <td>{row.side}</td>
                  <td align="right">{row.quantity.toFixed(4)}</td>
                  <td>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </article>

      <article className="card">
        <h2 style={{ marginTop: 0 }}>Recent Fills</h2>
        {fills.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>
            No fills available from API. This is an explicit empty/disconnected state, not synthetic demo data.
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Fill ID</th>
                <th align="left">Order ID</th>
                <th align="left">Symbol</th>
                <th align="right">Qty</th>
                <th align="right">Price</th>
                <th align="left">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {fills.slice(0, 25).map((row) => (
                <tr key={row.fill_id}>
                  <td>{row.fill_id}</td>
                  <td>{row.order_id}</td>
                  <td>{row.symbol}</td>
                  <td align="right">{row.quantity.toFixed(4)}</td>
                  <td align="right">{row.price.toFixed(4)}</td>
                  <td>{row.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </article>
    </section>
  );
}
