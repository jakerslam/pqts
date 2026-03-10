"use client";

import { useMemo, useState } from "react";

type Channel = "stdout" | "telegram" | "discord";

interface NotifyResponse {
  dry_run: boolean;
  ok?: boolean;
  command: string[];
  exit_code?: number;
  stdout?: string;
  stderr?: string;
  parsed?: Record<string, unknown> | null;
}

export function NotificationsCheck() {
  const [channel, setChannel] = useState<Channel>("stdout");
  const [message, setMessage] = useState("[PQTS TEST] Notifications channel check from dashboard.");
  const [telegramToken, setTelegramToken] = useState("");
  const [telegramChatId, setTelegramChatId] = useState("");
  const [discordWebhook, setDiscordWebhook] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<NotifyResponse | null>(null);
  const [error, setError] = useState("");

  const requestBody = useMemo(
    () => ({
      channel,
      message,
      telegram_token: telegramToken,
      telegram_chat_id: telegramChatId,
      discord_webhook: discordWebhook,
    }),
    [channel, message, telegramToken, telegramChatId, discordWebhook],
  );

  async function run(execute: boolean) {
    setIsRunning(true);
    setError("");
    try {
      const response = await fetch("/api/notify-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...requestBody, execute }),
      });
      const payload = (await response.json()) as NotifyResponse & { error?: string };
      if (!response.ok) {
        throw new Error(payload.error ?? `Notify call failed (${response.status})`);
      }
      setResult(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Notification check failed.");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <article className="card" style={{ display: "grid", gap: 10 }}>
        <h2 style={{ margin: 0 }}>Notifications Channel Check</h2>
        <p style={{ margin: 0, color: "var(--muted)" }}>
          Dry-run first to inspect command payload, then execute bounded test delivery.
        </p>
        <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
          <label style={{ display: "grid", gap: 4 }}>
            <span>Channel</span>
            <select value={channel} onChange={(event) => setChannel(event.target.value as Channel)}>
              <option value="stdout">stdout</option>
              <option value="telegram">telegram</option>
              <option value="discord">discord</option>
            </select>
          </label>
          <label style={{ display: "grid", gap: 4 }}>
            <span>Message</span>
            <input value={message} onChange={(event) => setMessage(event.target.value)} />
          </label>
        </div>

        {channel === "telegram" ? (
          <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            <label style={{ display: "grid", gap: 4 }}>
              <span>Telegram Token</span>
              <input value={telegramToken} onChange={(event) => setTelegramToken(event.target.value)} />
            </label>
            <label style={{ display: "grid", gap: 4 }}>
              <span>Telegram Chat ID</span>
              <input value={telegramChatId} onChange={(event) => setTelegramChatId(event.target.value)} />
            </label>
          </div>
        ) : null}

        {channel === "discord" ? (
          <label style={{ display: "grid", gap: 4 }}>
            <span>Discord Webhook</span>
            <input value={discordWebhook} onChange={(event) => setDiscordWebhook(event.target.value)} />
          </label>
        ) : null}

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button type="button" disabled={isRunning} onClick={() => run(false)}>
            Preview Command
          </button>
          <button type="button" disabled={isRunning} onClick={() => run(true)}>
            Execute Test
          </button>
        </div>

        {error ? <p style={{ margin: 0, color: "#c1121f" }}>{error}</p> : null}
      </article>

      {result ? (
        <article className="card" style={{ display: "grid", gap: 8 }}>
          <h3 style={{ margin: 0 }}>Result</h3>
          <p style={{ margin: 0 }}>
            Mode: <strong>{result.dry_run ? "dry_run" : "execute"}</strong>
          </p>
          <pre className="pqts-code-block" style={{ margin: 0 }}>
            <code>{JSON.stringify(result.command, null, 2)}</code>
          </pre>
          {result.parsed ? (
            <pre className="pqts-code-block" style={{ margin: 0 }}>
              <code>{JSON.stringify(result.parsed, null, 2)}</code>
            </pre>
          ) : null}
          {result.stderr ? (
            <pre className="pqts-code-block" style={{ margin: 0 }}>
              <code>{result.stderr}</code>
            </pre>
          ) : null}
        </article>
      ) : null}
    </section>
  );
}
