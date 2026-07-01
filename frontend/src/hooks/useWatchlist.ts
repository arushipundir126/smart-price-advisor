/*
 * FILE: frontend/src/hooks/useWatchlist.ts
 *
 * WHAT THIS DOES:
 * Talks to the four watchlist endpoints using this browser's session id: list,
 * add or update, remove, and mark bought. Exposes items, loading, error, and the
 * actions. All failures become plain-language messages.
 *
 * CHANGES THIS SESSION:
 * - Created the hook, the WatchlistItem type, and the four actions.
 *
 * WHERE IT FITS:
 * Backs the watchlist side panel and the "alert me" button.
 *
 * CALLED BY / IMPORTS FROM:
 * Reads VITE_API_BASE_URL and getSessionId. Called by the watchlist components.
 */
import { useCallback, useState } from "react";

import { getSessionId } from "../utils/session";

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
  latest_price: number | null;
  latest_platform: string | null;
}

const FRIENDLY_ERROR =
  "We could not reach your watchlist just now. Please try again in a moment.";

export function useWatchlist() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionId = getSessionId();

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/watchlist/${sessionId}`);
      const json = await resp.json();
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
  }, [sessionId]);

  async function add(productId: string, targetPrice: number | null) {
    try {
      const resp = await fetch(`${API_BASE}/api/watchlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          product_id: productId,
          target_price: targetPrice,
        }),
      });
      const json = await resp.json();
      if (!resp.ok || json.error) return { ok: false, message: json.message ?? FRIENDLY_ERROR };
      await refresh();
      return { ok: true };
    } catch {
      return { ok: false, message: FRIENDLY_ERROR };
    }
  }

  async function remove(productId: string) {
    try {
      await fetch(`${API_BASE}/api/watchlist/${sessionId}/${productId}`, {
        method: "DELETE",
      });
      await refresh();
    } catch {
      setError(FRIENDLY_ERROR);
    }
  }

  async function markBought(productId: string) {
    try {
      await fetch(
        `${API_BASE}/api/watchlist/${sessionId}/${productId}/purchased`,
        { method: "POST" }
      );
      await refresh();
    } catch {
      setError(FRIENDLY_ERROR);
    }
  }

  return { items, loading, error, refresh, add, remove, markBought };
}
