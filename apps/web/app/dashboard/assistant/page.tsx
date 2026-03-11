import { AssistantConsole } from "@/components/chat/assistant-console";
import Link from "next/link";

export default function AssistantPage() {
  return (
    <section style={{ display: "grid", gap: 16 }}>
      <article className="card">
        <h2 style={{ marginTop: 0 }}>Assistant (Additive Surface)</h2>
        <p style={{ marginTop: 0, color: "var(--muted)" }}>
          Assistant responses accelerate workflows, but capital-affecting actions must still flow through execution/risk/promotion controls.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Link href="/dashboard/execution">Execution console</Link>
          <Link href="/dashboard/risk">Risk controls</Link>
          <Link href="/dashboard/promotion">Promotion gates</Link>
        </div>
      </article>
      <AssistantConsole />
    </section>
  );
}
