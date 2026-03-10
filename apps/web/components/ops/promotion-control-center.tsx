"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { PromotionAction, PromotionRecord } from "@/lib/ops/promotion-store";

interface PromotionResponse {
  records: PromotionRecord[];
}

const ACTIONS: PromotionAction[] = ["advance", "hold", "rollback", "halt"];

export function PromotionControlCenter() {
  const [rows, setRows] = useState<PromotionRecord[]>([]);
  const [actor, setActor] = useState("web_operator");
  const [note, setNote] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    const response = await fetch("/api/promotion", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to load promotion records (${response.status})`);
    }
    const payload = (await response.json()) as PromotionResponse;
    setRows(payload.records);
  }, []);

  useEffect(() => {
    load().catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to load promotion records.");
    });
  }, [load]);

  const sortedRows = useMemo(
    () => rows.slice().sort((left, right) => left.strategy_id.localeCompare(right.strategy_id)),
    [rows],
  );

  async function runAction(strategyId: string, action: PromotionAction) {
    setIsLoading(true);
    setError("");
    try {
      const response = await fetch("/api/promotion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_id: strategyId,
          action,
          actor,
          note,
        }),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => ({}))) as { error?: string };
        throw new Error(payload.error ?? `Promotion action failed (${response.status})`);
      }
      const payload = (await response.json()) as PromotionResponse;
      setRows(payload.records);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Promotion action failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <article className="card" style={{ display: "grid", gap: 10 }}>
        <h2 style={{ margin: 0 }}>Promotion Control Center</h2>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Stage transitions stay explicit: backtest -&gt; paper -&gt; shadow -&gt; canary -&gt; live.
        </p>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <label style={{ display: "grid", gap: 4 }}>
            <span>Actor</span>
            <input value={actor} onChange={(event) => setActor(event.target.value)} style={{ minWidth: 180 }} />
          </label>
          <label style={{ display: "grid", gap: 4, minWidth: 280 }}>
            <span>Note</span>
            <input value={note} onChange={(event) => setNote(event.target.value)} placeholder="reason / ticket" />
          </label>
          <button type="button" onClick={() => load()} disabled={isLoading}>
            Refresh
          </button>
        </div>
        {error ? <p style={{ margin: 0, color: "#c1121f" }}>{error}</p> : null}
      </article>

      <article className="card">
        {sortedRows.length === 0 ? (
          <p style={{ margin: 0, color: "var(--muted)" }}>No promotion records available.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th align="left">Strategy</th>
                <th align="left">Stage</th>
                <th align="right">Capital %</th>
                <th align="left">Rollback Trigger</th>
                <th align="left">Last Action</th>
                <th align="left">Controls</th>
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row) => {
                const latest = row.history[0];
                return (
                  <tr key={row.strategy_id}>
                    <td>{row.strategy_id}</td>
                    <td>{row.stage}</td>
                    <td align="right">{row.capital_allocation_pct.toFixed(2)}</td>
                    <td>{row.rollback_trigger}</td>
                    <td>{latest ? `${latest.action} @ ${latest.at}` : "none"}</td>
                    <td>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {ACTIONS.map((action) => (
                          <button
                            key={action}
                            type="button"
                            disabled={isLoading}
                            onClick={() => runAction(row.strategy_id, action)}
                          >
                            {action}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </article>
    </section>
  );
}
