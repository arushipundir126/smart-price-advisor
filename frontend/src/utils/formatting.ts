/*
 * FILE: frontend/src/utils/formatting.ts
 *
 * WHAT THIS DOES:
 * Formats money and dates in plain Indian style (Rs 61,499 and 3 Oct 2026).
 * Uses the browser's Intl, so no libraries are needed.
 *
 * CHANGES THIS SESSION:
 * - Created formatInr() and formatDate().
 *
 * WHERE IT FITS:
 * Used across the verdict, action strip, and watchlist components.
 *
 * CALLED BY / IMPORTS FROM:
 * No imports. Called by the display components.
 */
const inr = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const dateFmt = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

export function formatInr(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Price not available";
  }
  return inr.format(value);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return dateFmt.format(d);
}

/**
 * Return the url only if it is a plain http/https link. Buy links come from
 * external sources, so this blocks javascript: or data: URLs from ever reaching
 * an href.
 */
export function safeHttpUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:" ? url : null;
  } catch {
    return null;
  }
}
