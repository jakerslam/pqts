import { z } from "zod";

const EnvSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z.string().url().default("http://localhost:8000"),
  NEXT_PUBLIC_WS_BASE_URL: z.string().url().default("ws://localhost:8000"),
  NEXT_PUBLIC_API_TOKEN: z.string().min(1).default("pqts-dev-viewer-token"),
});

const parsed = EnvSchema.safeParse({
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_WS_BASE_URL: process.env.NEXT_PUBLIC_WS_BASE_URL,
  NEXT_PUBLIC_API_TOKEN: process.env.NEXT_PUBLIC_API_TOKEN,
});

if (!parsed.success) {
  throw new Error(`Invalid web env: ${parsed.error.message}`);
}

export const webEnv = parsed.data;
