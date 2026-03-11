"use client";

import { useEffect, useMemo, useState } from "react";

import { webEnv } from "@/lib/env";

type StreamHealth = "connected" | "reconnecting" | "degraded" | "stale";

interface Props {
  channel: "orders" | "fills" | "positions" | "pnl" | "risk";
  accountId?: string;
  token?: string;
}

export function LiveStreamStatus({ channel, accountId = "paper-main", token }: Props) {
  const [health, setHealth] = useState<StreamHealth>("reconnecting");
  const [lastEventAt, setLastEventAt] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    const wsBase = webEnv.NEXT_PUBLIC_WS_BASE_URL.replace(/^http/i, "ws").replace(/\/$/, "");
    const apiToken = String(token ?? webEnv.NEXT_PUBLIC_API_TOKEN ?? "pqts-dev-viewer-token").trim();
    const url = `${wsBase}/ws/${channel}?account_id=${encodeURIComponent(accountId)}&token=${encodeURIComponent(apiToken)}`;
    let socket: WebSocket | null = null;
    let pingTimer: ReturnType<typeof setInterval> | null = null;
    let staleTimer: ReturnType<typeof setInterval> | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let alive = true;
    let lastMessageMs = 0;

    const cleanup = () => {
      if (pingTimer) clearInterval(pingTimer);
      if (staleTimer) clearInterval(staleTimer);
      if (retryTimer) clearTimeout(retryTimer);
      if (socket) socket.close();
      pingTimer = null;
      staleTimer = null;
      retryTimer = null;
      socket = null;
    };

    const connect = () => {
      if (!alive) return;
      setHealth("reconnecting");
      setErrorMessage("");
      socket = new WebSocket(url);
      socket.onopen = () => {
        lastMessageMs = Date.now();
        setHealth("connected");
        pingTimer = setInterval(() => {
          try {
            socket?.send("ping");
          } catch {
            // no-op; close event will trigger reconnect
          }
        }, 1500);
        staleTimer = setInterval(() => {
          const age = Date.now() - lastMessageMs;
          if (age > 6000) {
            setHealth((current) => (current === "degraded" ? current : "stale"));
          }
        }, 1000);
      };
      socket.onmessage = () => {
        lastMessageMs = Date.now();
        setLastEventAt(new Date(lastMessageMs).toISOString());
        setHealth("connected");
      };
      socket.onerror = () => {
        setHealth("degraded");
        setErrorMessage("stream_error");
      };
      socket.onclose = (event) => {
        if (pingTimer) clearInterval(pingTimer);
        if (staleTimer) clearInterval(staleTimer);
        pingTimer = null;
        staleTimer = null;
        if (!alive) {
          return;
        }
        setHealth("degraded");
        setErrorMessage(`closed_${event.code}`);
        retryTimer = setTimeout(connect, 1500);
      };
    };

    connect();
    return () => {
      alive = false;
      cleanup();
    };
  }, [accountId, channel, token]);

  const label = useMemo(() => {
    if (health === "connected") return "connected";
    if (health === "reconnecting") return "reconnecting";
    if (health === "stale") return "stale";
    return "degraded";
  }, [health]);

  return (
    <div className={`status-chip status-chip-${health}`} title={errorMessage || "stream_ok"}>
      stream:{label}
      {lastEventAt ? <span style={{ color: "var(--muted)" }}> @ {lastEventAt}</span> : null}
    </div>
  );
}

