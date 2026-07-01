/*
 * FILE: frontend/src/hooks/useAnalyse.ts
 *
 * WHAT THIS DOES:
 * Calls POST /api/analyse and exposes {loading, data, error, analyse}. Turns any
 * failure (network, rate limit, server) into a plain-language message, and
 * surfaces the backend's vague-query message as a friendly error too.
 *
 * CHANGES THIS SESSION:
 * - Created the hook, the Verdict type, and friendly error mapping.
 *
 * WHERE IT FITS:
 * Backs the search-to-verdict flow. Consumed by App and the verdict components.
 *
 * CALLED BY / IMPORTS FROM:
 * Reads VITE_API_BASE_URL. Called by src/App.tsx.
 */
import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export interface SignalSummary {
  signal: string;
  vote: "buy_now" | "wait" | null;
  plain_reason: string;
}

export interface Discount {
  type: string;
  description: string;
  estimated_saving_inr: number;
}

export interface NextSale {
  name: string;
  start_date: string;
  platform: string;
}

export interface Verdict {
  product: string;
  category: string | null;
  verdict: "Buy Now" | "Wait";
  confidence: "High" | "Medium" | "Low";
  summary_reason: string;
  wait_estimate_days: number | null;
  best_price: number | null;
  best_platform: string | null;
  buy_link: string | null;
  price_vs_median: number | null;
  price_history: number[];
  price_median: number | null;
  next_sale: NextSale | null;
  stackable_discounts: Discount[];
  signal_summaries: SignalSummary[];
  product_id: string | null;
}

interface AnalyseState {
  loading: boolean;
  data: Verdict | null;
  error: string | null;
}

export function useAnalyse() {
  const [state, setState] = useState<AnalyseState>({
    loading: false,
    data: null,
    error: null,
  });

  async function analyse(product: string, waitToleranceDays: number) {
    setState({ loading: true, data: null, error: null });
    try {
      const resp = await fetch(`${API_BASE}/api/analyse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product,
          wait_tolerance_days: waitToleranceDays,
        }),
      });

      if (resp.status === 429) {
        setState({
          loading: false,
          data: null,
          error: "You are checking a bit too fast. Please wait a minute and try again.",
        });
        return;
      }
      if (!resp.ok) {
        setState({
          loading: false,
          data: null,
          error:
            "We could not check prices just now. Please try again in a moment.",
        });
        return;
      }

      const json = await resp.json();
      // The backend returns a friendly message for vague or unbranded queries.
      if (json.error) {
        setState({ loading: false, data: null, error: json.message });
        return;
      }
      setState({ loading: false, data: json as Verdict, error: null });
    } catch {
      setState({
        loading: false,
        data: null,
        error:
          "We could not reach the service. Please check your connection and try again.",
      });
    }
  }

  function reset() {
    setState({ loading: false, data: null, error: null });
  }

  return { ...state, analyse, reset };
}
