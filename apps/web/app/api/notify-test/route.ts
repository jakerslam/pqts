import { NextResponse } from "next/server";

import { runPython } from "@/lib/ops/exec";

export const runtime = "nodejs";

interface NotifyBody {
  channel?: "stdout" | "telegram" | "discord";
  message?: string;
  telegram_token?: string;
  telegram_chat_id?: string;
  discord_webhook?: string;
  execute?: boolean;
}

function buildNotifyCommand(payload: NotifyBody): string[] {
  const channel = payload.channel ?? "stdout";
  const message = payload.message ?? "[PQTS TEST] Notifications channel check from web.";
  const command = [
    "main.py",
    "notify",
    "test",
    "--channel",
    channel,
    "--message",
    message,
    "--output",
    "json",
  ];
  if (channel === "telegram") {
    command.push("--telegram-token", payload.telegram_token ?? "", "--telegram-chat-id", payload.telegram_chat_id ?? "");
  }
  if (channel === "discord") {
    command.push("--discord-webhook", payload.discord_webhook ?? "");
  }
  return command;
}

function parseJsonLine(stdout: string): Record<string, unknown> | null {
  const lines = stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    try {
      const parsed = JSON.parse(lines[index]);
      if (parsed && typeof parsed === "object") {
        return parsed as Record<string, unknown>;
      }
    } catch {
      continue;
    }
  }
  return null;
}

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => ({}))) as NotifyBody;
  const command = buildNotifyCommand(payload);
  if (!payload.execute) {
    return NextResponse.json({
      dry_run: true,
      command: ["python3", ...command],
    });
  }

  const result = await runPython(command, { timeoutMs: 90_000 });
  return NextResponse.json({
    dry_run: false,
    ...result,
    parsed: parseJsonLine(result.stdout),
  });
}
