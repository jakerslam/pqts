import Link from "next/link";
import { StreamTurnPreview } from "@/components/stream/stream-turn-preview";
import { ToolEventRenderer } from "@/components/tool-renderers/tool-event-renderer";
import { getRegisteredToolTypes } from "@/lib/tools/registry";

export default function DashboardHomePage() {
  const knownTypes = getRegisteredToolTypes();
  return (
    <section style={{ display: "grid", gap: 16 }}>
      <div className="grid">
        <article className="card">
          <h3>Onboarding</h3>
          <p>Generate CLI-first setup plans for beginner and pro operator profiles.</p>
          <Link href="/onboarding">Open onboarding wizard</Link>
        </article>
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
          <h3>Execution Quality</h3>
          <p>Reference-bundle slippage, alpha, and venue quality tape.</p>
          <Link href="/dashboard/execution-quality">Open quality dashboard</Link>
        </article>
        <article className="card">
          <h3>Order Truth</h3>
          <p>Signal-to-fill lineage and block/execution explanation per order.</p>
          <Link href="/dashboard/order-truth">Open order truth drilldown</Link>
        </article>
        <article className="card">
          <h3>Replay Timeline</h3>
          <p>Deterministic event-replay digest with hash and event-type stats.</p>
          <Link href="/dashboard/replay">Open replay timeline</Link>
        </article>
        <article className="card">
          <h3>Risk</h3>
          <p>Kill-switch events, drawdown, and guardrails.</p>
          <Link href="/dashboard/risk">Open risk view</Link>
        </article>
        <article className="card">
          <h3>Promotion</h3>
          <p>Stage-transition control center with explicit promotion actions.</p>
          <Link href="/dashboard/promotion">Open promotion control center</Link>
        </article>
        <article className="card">
          <h3>Templates</h3>
          <p>Generated template-run artifacts, config snapshots, and diffs.</p>
          <Link href="/dashboard/templates">Open template gallery</Link>
        </article>
        <article className="card">
          <h3>Notifications</h3>
          <p>Preview and execute stdout/Telegram/Discord channel checks.</p>
          <Link href="/dashboard/notifications">Open notifications check</Link>
        </article>
      </div>

      <article className="card">
        <h3 style={{ marginTop: 0 }}>Tool Renderer Registry</h3>
        <p>Registered tool types: {knownTypes.join(", ")}</p>
      </article>

      <ToolEventRenderer
        event={{
          toolType: "risk_state",
          status: "complete",
          payload: { kill_switch_active: false, kill_switch_reason: "" },
        }}
      />
      <ToolEventRenderer
        event={{
          toolType: "unknown_tool",
          status: "complete",
          payload: { sample: true },
        }}
      />
      <StreamTurnPreview />
    </section>
  );
}
