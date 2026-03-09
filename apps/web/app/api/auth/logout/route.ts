import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SESSION_COOKIE_NAME } from "@/lib/auth/session";

export async function POST(request: Request) {
  const jar = await cookies();
  jar.delete(SESSION_COOKIE_NAME);
  return NextResponse.redirect(new URL("/login", request.url));
}
