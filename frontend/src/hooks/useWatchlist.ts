/*
 * FILE: frontend/src/hooks/useWatchlist.ts
 *
 * WHAT THIS DOES:
 * Talks to the watchlist endpoints for the signed-in user: list, price
 * re-check on open, add or update, remove, and mark bought. Every call carries
 * the sign-in token; identity is decided server-side from that token. When the
 * user is signed out, calls are skipped and needsAuth is flagged so the app can
 * show the sign-in screen. All failures become plain-language messages.
 *
 * CHANGES THIS SESSION:
 * - Created the hook, the WatchlistItem type, and the four actions.
 * - add() now sends the wait window, and checkPrices() calls the on-open refresh
 *   endpoint that re-checks due items at an adaptive, per-item interval.
 * - Auth-aware: Bearer token on every call, needsAuth flag when signed out.
 *
 * WHERE IT FITS:
 * Backs the watchlist side panel and the "alert me" button.
 *
 * CALLED BY / IMPORTS FROM:
 * Reads VITE_API_BASE_URL and lib/supabase getAccessToken. Called by App.
 */
import { useCallback, useState } from "react";

import { getAccessToken } from "../lib/supabase";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface WatchlistItem {
  id: string;
  product_id: string;
  name: string | null;
  category: string | null;
  target_price: number | null;
  notified: boolean;
  purchased: boolean;
  purchased_at: string | null;
  wait_tolerance_days: number | null;
  latest_price: number | null;
  latest_platform: string | null;
  last_checked: string | null;
}

const FRIENDLY_ERROR =
  "We could not reach your watchlist just now. Please try again in a moment.";
const SIGN_IN_MESSAGE = "Please sign in to use your watchlist.";

export function useWatchlist() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);

  const call = useCallback(
    async (path: string, init?: RequestInit): Promise<Response | null> => {
      const token = await getAccessToken();
      if (!token) {
        setNeedsAuth(true);
        return null;
      }
      setNeedsAuth(false);
      return fetch(`${API_BASE}${path}`, {
        ...init,
        headers: {
          ...(init?.headers ?? {}),
          Authorization: `Bearer ${token}`,
        },
      });
    },
    []
  );

  // Quick list, no price re-fetch. Used after add/remove/mark to update the UI.
  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await call("/api/watchlist/me");
      if (!resp) {
        setItems([]);
        return;
      }
      const json = await resp.json();
      if (resp.status === 401) {
        setNeedsAuth(true);
        setItems([]);
        return;
      }
      if (!resp.ok || json.error) {
        setError(json.message ?? FRIENDLY_ERROR);
        return;
      }
      setItems(json.items ?? []);
    } catch {
      setError(FRIENDLY_ERROR);
    } finally {
      setLoading(false);
    }
  }, [call]);

  // On app open: re-check prices for items whose adaptive interval has elapsed.
  // The server decides which items are due, so calling this on every open is
  // safe and never over-checks. Silently does nothing when signed out.
  const checkPrices = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await call("/api/watchlist/me/refresh", { method: "POST" });
      if (!resp) {
        setItems([]);
        return;
      }
      const json = await resp.json();
      if (resp.status === 401) {
        setNeedsAuth(true);
        setItems([]);
        return;
      }
      if (!resp.ok || json.error) {
        setError(json.message ?? FRIENDLY_ERROR);
        return;
      }
      setItems(json.items ?? []);
    } catch {
      setError(FRIENDLY_ERROR);
    } finally {
      setLoading(false);
    }
  }, [call]);

  async function add(
    productId: string,
    targetPrice: number | null,
    waitToleranceDays: number | null = null
  ) {
    try {
      const resp = await call("/api/watchlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: productId,
          target_price: targetPrice,
          wait_tolerance_days: waitToleranceDays,
        }),
      });
      if (!resp) return { ok: false, message: SIGN_IN_MESSAGE };
      const json = await resp.json();
      if (!resp.ok || json.error) {
        return { ok: false, message: json.message ?? FRIENDLY_ERROR };
      }
      await refresh();
      return { ok: true };
    } catch {
      return { ok: false, message: FRIENDLY_ERROR };
    }
  }

  async function remove(productId: string) {
    try {
      await call(`/api/watchlist/me/${productId}`, { method: "DELETE" });
      await refresh();
    } catch {
      setError(FRIENDLY_ERROR);
    }
  }

  async function markBought(productId: string) {
    try {
      await call(`/api/watchlist/me/${productId}/purchased`, { method: "POST" });
      await refresh();
    } catch {
      setError(FRIENDLY_ERROR);
    }
  }

  return {
    items,
    loading,
    error,
    needsAuth,
    refresh,
    checkPrices,
    add,
    remove,
    markBought,
  };
}
