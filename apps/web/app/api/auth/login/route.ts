import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SESSION_COOKIE_NAME, hasSessionToken } from "@/lib/auth/session";

export async function POST(request: Request) {
  const form = await request.formData();
  const token = String(form.get("token") ?? "").trim();
  const nextPathRaw = String(form.get("next") ?? "/dashboard");
  const nextPath = nextPathRaw.startsWith("/") ? nextPathRaw : "/dashboard";

  if (!hasSessionToken(token)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const jar = await cookies();
  jar.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
    maxAge: 60 * 60 * 8,
  });

  return NextResponse.redirect(new URL(nextPath, request.url));
}
