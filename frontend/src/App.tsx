/*
 * FILE: frontend/src/App.tsx
 *
 * WHAT THIS DOES:
 * The app shell and screen controller. Holds the search screen (product input,
 * wait picker, recent searches) and the result screen (verdict card, action
 * strip, discounts, signal breakdown, watchlist button, sparkline), plus the
 * slide-in watchlist panel and the drop-alert banner. Refreshes the watchlist
 * at most once a day, and immediately when the panel is opened.
 *
 * CHANGES THIS SESSION:
 * - Replaced the placeholder shell with the full search-to-verdict flow, the
 *   watchlist panel toggle, recent searches, and the alert banner.
 *
 * WHERE IT FITS:
 * The root component. Wires the hooks to the components.
 *
 * CALLED BY / IMPORTS FROM:
 * Imports useAnalyse, useWatchlist, and every component. Mounted by main.tsx.
 */
import { useCallback, useEffect, useState } from "react";

import ActionStrip from "./components/ActionStrip";
import AlertBanner from "./components/AlertBanner";
import ErrorState from "./components/ErrorState";
import LoadingState from "./components/LoadingState";
import PriceSparkline from "./components/PriceSparkline";
import SearchBar from "./components/SearchBar";
import SignalBreakdown from "./components/SignalBreakdown";
import StackableDiscounts from "./components/StackableDiscounts";
import VerdictCard from "./components/VerdictCard";
import WaitTolerancePicker from "./components/WaitTolerancePicker";
import WatchlistButton from "./components/WatchlistButton";
import WatchlistPanel from "./components/WatchlistPanel";
import { useAnalyse } from "./hooks/useAnalyse";
import { useWatchlist } from "./hooks/useWatchlist";

const RECENT_KEY = "spa_recent_searches";
const REFRESH_KEY = "spa_watchlist_refreshed_at";
const DAY_MS = 24 * 60 * 60 * 1000;

function loadRecent(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) ?? "[]");
  } catch {
    return [];
  }
}

export default function App() {
  const [product, setProduct] = useState("");
  const [waitDays, setWaitDays] = useState(30);
  const [screen, setScreen] = useState<"search" | "result">("search");
  const [recent, setRecent] = useState<string[]>(loadRecent);
  const [panelOpen, setPanelOpen] = useState(false);

  const { loading, data, error, analyse, reset } = useAnalyse();
  const watchlist = useWatchlist();

  // Refresh the watchlist at most once a day on load (for the alert banner).
  const { refresh } = watchlist;
  useEffect(() => {
    const last = Number(localStorage.getItem(REFRESH_KEY) ?? 0);
    if (Date.now() - last > DAY_MS) {
      refresh();
      localStorage.setItem(REFRESH_KEY, String(Date.now()));
    }
  }, [refresh]);

  const openPanel = useCallback(() => {
    setPanelOpen(true);
    refresh(); // opening is an explicit intent, so read the latest
  }, [refresh]);

  function rememberRecent(term: string) {
    const next = [term, ...recent.filter((r) => r !== term)].slice(0, 5);
    setRecent(next);
    localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  }

  function runAnalyse(term?: string) {
    const q = (term ?? product).trim();
    if (!q) return;
    if (term) setProduct(term);
    rememberRecent(q);
    setScreen("result");
    analyse(q, waitDays);
  }

  function backToSearch() {
    setScreen("search");
    reset();
  }

  return (
    <main style={{ maxWidth: 560, margin: "0 auto", padding: "var(--sp-4)" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "var(--sp-6)",
        }}
      >
        <h1
          className="interactive"
          style={{ fontSize: "var(--fs-xl)", cursor: "pointer" }}
          onClick={backToSearch}
        >
          Smart Price Advisor
        </h1>
        <button className="btn interactive" onClick={openPanel}>
          Watchlist{watchlist.items.length ? ` (${watchlist.items.length})` : ""}
        </button>
      </header>

      <AlertBanner items={watchlist.items} onOpen={openPanel} />

      {screen === "search" && (
        <section className="card">
          <h2 style={{ fontSize: "var(--fs-lg)", marginBottom: "var(--sp-4)" }}>
            Buy now or wait?
          </h2>
          <SearchBar
            product={product}
            onProductChange={setProduct}
            onSubmit={() => runAnalyse()}
            busy={loading}
            recent={recent}
            onSelectRecent={(term) => runAnalyse(term)}
          />
          <div style={{ marginTop: "var(--sp-4)" }}>
            <WaitTolerancePicker valueDays={waitDays} onChange={setWaitDays} />
          </div>
        </section>
      )}

      {screen === "result" && (
        <section>
          <button
            className="btn interactive"
            style={{ marginBottom: "var(--sp-4)" }}
            onClick={backToSearch}
          >
            Search again
          </button>

          {loading && <LoadingState />}
          {!loading && error && <ErrorState message={error} product={product} />}
          {!loading && data && (
            <>
              <VerdictCard
                verdict={data.verdict}
                confidence={data.confidence}
                summaryReason={data.summary_reason}
              />
              <ActionStrip
                verdict={data.verdict}
                bestPrice={data.best_price}
                bestPlatform={data.best_platform}
                buyLink={data.buy_link}
                waitEstimateDays={data.wait_estimate_days}
              />
              <WatchlistButton
                productId={data.product_id}
                defaultTarget={data.best_price}
                onAdd={watchlist.add}
              />
              <StackableDiscounts discounts={data.stackable_discounts} />
              <SignalBreakdown signals={data.signal_summaries} />
              <PriceSparkline prices={data.price_history} median={data.price_median} />
            </>
          )}
        </section>
      )}

      <WatchlistPanel
        open={panelOpen}
        onClose={() => setPanelOpen(false)}
        items={watchlist.items}
        loading={watchlist.loading}
        error={watchlist.error}
        onRemove={watchlist.remove}
        onMarkBought={watchlist.markBought}
      />
    </main>
  );
}
