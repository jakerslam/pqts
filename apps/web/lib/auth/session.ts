export const SESSION_COOKIE_NAME = "pqts_session";

export function hasSessionToken(token?: string | null): boolean {
  if (!token) return false;
  return token.trim().length > 0;
}
