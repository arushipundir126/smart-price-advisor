/*
 * FILE: frontend/src/App.tsx
 *
 * WHAT THIS DOES:
 * The app shell and screen controller. Holds the search screen (product input,
 * wait picker, recent searches) and the result screen (verdict card, action
 * strip, discounts, signal breakdown, watchlist button, sparkline), plus the
 * slide-in watchlist panel and the drop-alert banner. On open it re-checks
 * watched prices at an adaptive, per-item interval (server-throttled).
 *
 * CHANGES THIS SESSION:
 * - Replaced the placeholder shell with the full search-to-verdict flow, the
 *   watchlist panel toggle, recent searches, and the alert banner.
 * - Added the cross-platform price comparison list, passed the wait window when
 *   adding to the watchlist, and switched on-open refresh to the adaptive
 *   price re-check endpoint.
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
import { formatInr, safeHttpUrl } from "./utils/formatting";

const RECENT_KEY = "spa_recent_searches";

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

  // On app open, re-check watched prices. The server only re-checks items whose
  // adaptive interval has elapsed, so opening many times a day does not overcheck.
  const { checkPrices } = watchlist;
  useEffect(() => {
    checkPrices();
  }, [checkPrices]);

  const openPanel = useCallback(() => {
    setPanelOpen(true);
    checkPrices(); // opening is an explicit intent, so read the latest
  }, [checkPrices]);

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
        <>
          <div style={{ margin: "var(--sp-6) 0 var(--sp-6)" }}>
            <h2 className="display">
              Buy smarter. <span className="accent">Save more.</span>
            </h2>
            <p
              style={{
                marginTop: "var(--sp-3)",
                marginBottom: 0,
                fontSize: "var(--fs-lg)",
                color: "var(--text-muted)",
              }}
            >
              Name a product and how long you can wait. We check the live price,
              its history, and upcoming sales, then say Buy Now or Wait, backed by
              evidence, never a guess.
            </p>
          </div>
          <section className="card">
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
        </>
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
                onAdd={(productId, target) =>
                  watchlist.add(productId, target, waitDays)
                }
              />
              {data.platform_prices && data.platform_prices.length > 1 && (
                <div className="card">
                  <p className="section-label" style={{ marginTop: 0 }}>
                    Prices across platforms
                  </p>
                  <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
                    {data.platform_prices.map((p, i) => {
                      const href = safeHttpUrl(p.buy_link);
                      const row = (
                        <>
                          <span>{p.platform}</span>
                          <span className="mono" style={{ fontWeight: 600 }}>
                            {formatInr(p.price)}
                          </span>
                        </>
                      );
                      return (
                        <li key={`${p.platform}-${i}`}>
                          {href ? (
                            <a
                              className="row-link"
                              href={href}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {row}
                            </a>
                          ) : (
                            <div className="row-link" style={{ cursor: "default" }}>
                              {row}
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}
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
