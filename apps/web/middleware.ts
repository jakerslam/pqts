import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE_NAME, hasSessionToken } from "@/lib/auth/session";

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const protectedRoute = pathname.startsWith("/dashboard");

  if (!protectedRoute) {
    return NextResponse.next();
  }

  const session = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (hasSessionToken(session)) {
    return NextResponse.next();
  }

  const redirectUrl = new URL("/login", request.url);
  redirectUrl.searchParams.set("next", `${pathname}${search}`);
  return NextResponse.redirect(redirectUrl);
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
