/*
 * FILE: frontend/src/utils/session.ts
 *
 * WHAT THIS DOES:
 * Creates and remembers a random, unguessable session id in localStorage. The
 * watchlist is tied to this id, so no login is needed. The id is a UUID.
 *
 * CHANGES THIS SESSION:
 * - Created getSessionId() with a crypto.randomUUID fallback.
 *
 * WHERE IT FITS:
 * Used by the watchlist hook to identify this browser to the backend.
 *
 * CALLED BY / IMPORTS FROM:
 * No imports. Called by src/hooks/useWatchlist.ts.
 */
const STORAGE_KEY = "spa_session_id";

function generateUuid(): string {
  // Read through an untyped reference so the fallback stays reachable in TS.
  const c: { randomUUID?: () => string; getRandomValues: (a: Uint8Array) => Uint8Array } =
    globalThis.crypto as never;
  if (typeof c.randomUUID === "function") {
    return c.randomUUID();
  }
  // Fallback: build a UUID from random bytes.
  const bytes = new Uint8Array(16);
  c.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0"));
  return (
    hex.slice(0, 4).join("") +
    "-" +
    hex.slice(4, 6).join("") +
    "-" +
    hex.slice(6, 8).join("") +
    "-" +
    hex.slice(8, 10).join("") +
    "-" +
    hex.slice(10, 16).join("")
  );
}

export function getSessionId(): string {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = generateUuid();
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
