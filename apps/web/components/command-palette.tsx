"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

interface CommandEntry {
  label: string;
  href: string;
  description: string;
  minMode?: "guided" | "pro";
}

interface Props {
  commands: CommandEntry[];
  densityMode: "guided" | "pro";
}

function modeRank(mode: "guided" | "pro"): number {
  return mode === "pro" ? 2 : 1;
}

export function CommandPalette({ commands, densityMode }: Props) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const wantsPalette = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
      if (!wantsPalette) {
        return;
      }
      event.preventDefault();
      setOpen((current) => !current);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return commands.filter((row) => {
      const minMode = row.minMode ?? "guided";
      if (modeRank(densityMode) < modeRank(minMode)) {
        return false;
      }
      if (!q) {
        return true;
      }
      return `${row.label} ${row.description} ${row.href}`.toLowerCase().includes(q);
    });
  }, [commands, densityMode, query]);

  function navigate(href: string) {
    setOpen(false);
    setQuery("");
    router.push(href);
  }

  return (
    <>
      <button type="button" className="inline-link-button" onClick={() => setOpen(true)}>
        command palette
      </button>
      {open ? (
        <div className="palette-overlay" role="dialog" aria-modal="true" aria-label="Command palette">
          <article className="palette-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0 }}>Command Palette</h3>
              <button type="button" onClick={() => setOpen(false)}>
                Close
              </button>
            </div>
            <input
              autoFocus
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search pages and operator actions..."
              aria-label="Search commands"
            />
            <div style={{ display: "grid", gap: 8, maxHeight: 320, overflowY: "auto" }}>
              {filtered.length === 0 ? (
                <p style={{ margin: 0, color: "var(--muted)" }}>No matching commands.</p>
              ) : (
                filtered.map((row) => (
                  <button
                    key={`${row.label}:${row.href}`}
                    type="button"
                    className="palette-row"
                    onClick={() => navigate(row.href)}
                  >
                    <span style={{ fontWeight: 700 }}>{row.label}</span>
                    <span style={{ color: "var(--muted)" }}>{row.description}</span>
                    <code>{row.href}</code>
                  </button>
                ))
              )}
            </div>
          </article>
        </div>
      ) : null}
    </>
  );
}

