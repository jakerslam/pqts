import fs from "node:fs";
import path from "node:path";

import { resolveRepoRoot } from "@/lib/ops/repo-root";

interface IntegrationRow {
  id: string;
  provider: string;
  market_classes?: string[];
  surface?: string;
  status?: string;
  last_reviewed?: string;
  repo_url?: string;
}

function loadIntegrations(): IntegrationRow[] {
  const filePath = path.join(resolveRepoRoot(), "config", "integrations", "official_integrations.json");
  try {
    const rows = JSON.parse(fs.readFileSync(filePath, "utf-8")) as IntegrationRow[];
    return Array.isArray(rows) ? rows : [];
  } catch {
    return [];
  }
}

export default function SettingsPage() {
  const integrations = loadIntegrations();
  return (
    <section style={{ display: "grid", gap: 16 }}>
      <article className="card">
        <h2 style={{ marginTop: 0 }}>Settings and Integrations</h2>
        <p style={{ marginTop: 0, color: "var(--muted)" }}>
          Canonical integration index and deployment context for Studio/Core parity.
        </p>
      </article>
      <article className="card">
        {integrations.length === 0 ? (
          <p style={{ margin: 0, color: "var(--muted)" }}>No integration metadata found.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Provider</th>
                <th align="left">Markets</th>
                <th align="left">Surface</th>
                <th align="left">Status</th>
                <th align="left">Last Reviewed</th>
                <th align="left">Repo</th>
              </tr>
            </thead>
            <tbody>
              {integrations.map((row) => (
                <tr key={row.id}>
                  <td>{row.provider}</td>
                  <td>{(row.market_classes ?? []).join(", ") || "-"}</td>
                  <td>{row.surface || "-"}</td>
                  <td>{row.status || "-"}</td>
                  <td>{row.last_reviewed || "-"}</td>
                  <td>
                    {row.repo_url ? (
                      <a href={row.repo_url} target="_blank" rel="noreferrer">
                        {row.repo_url}
                      </a>
                    ) : (
                      "-"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </article>
    </section>
  );
}

