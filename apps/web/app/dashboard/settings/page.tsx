import { getConnectors } from "@/lib/api/client";
import type { Connector } from "@/lib/api/types";

export const revalidate = 0;

async function loadConnectorRows(): Promise<Connector[]> {
  try {
    return await getConnectors();
  } catch {
    return [];
  }
}

function renderRepoLinks(repos?: string[]) {
  if (!repos || repos.length === 0) return "-";
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {repos.slice(0, 3).map((url) => (
        <a key={url} href={url} target="_blank" rel="noreferrer">
          {url}
        </a>
      ))}
      {repos.length > 3 ? <span style={{ color: "var(--muted)" }}>+{repos.length - 3} more</span> : null}
    </div>
  );
}

function renderSurfaces(surfaces?: string[]) {
  if (!surfaces || surfaces.length === 0) return "-";
  return surfaces.join(", ");
}

function renderMarkets(markets?: string[]) {
  if (!markets || markets.length === 0) return "-";
  return markets.join(", ");
}

export default async function SettingsPage() {
  const connectors = await loadConnectorRows();
  const sorted = connectors.sort((a, b) => (a.provider || "").localeCompare(b.provider || ""));

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <article className="card">
        <h2 style={{ marginTop: 0 }}>Settings and Integrations</h2>
        <p style={{ marginTop: 0, color: "var(--muted)" }}>
          Canonical connector registry for venues, brokers, data feeds, filings, and alt-data providers.
        </p>
      </article>
      <article className="card">
        {sorted.length === 0 ? (
          <p style={{ margin: 0, color: "var(--muted)" }}>No connector metadata available.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Provider</th>
                <th align="left">Class</th>
                <th align="left">Markets</th>
                <th align="left">Status</th>
                <th align="left">Surfaces</th>
                <th align="left">Last Reviewed</th>
                <th align="left">Repos</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <tr key={row.connector_id}>
                  <td>{row.display_name || row.provider}</td>
                  <td>{row.connector_class || "-"}</td>
                  <td>{renderMarkets(row.market_classes)}</td>
                  <td>{row.status || "-"}</td>
                  <td>{renderSurfaces(row.surfaces)}</td>
                  <td>{row.last_reviewed || "-"}</td>
                  <td>{renderRepoLinks(row.repo_urls)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </article>
    </section>
  );
}
