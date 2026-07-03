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
 * - Landing structure: bold hero, features grid, footer with Product/Company/
 *   Legal links, in-app info pages (About, Disclaimer, Privacy, Terms, Contact),
 *   and a light/dark theme toggle that overrides the system setting.
 * - Sign-in: watchlist now needs an account (AuthPage), searched products are
 *   auto-added to the signed-in user's watchlist, sign-out in the header, and
 *   entrance/stagger animations on the main screens.
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
import AuthPage from "./components/AuthPage";
import ErrorState from "./components/ErrorState";
import FeatureGrid from "./components/FeatureGrid";
import Footer from "./components/Footer";
import InfoPage from "./components/InfoPage";
import type { InfoKey } from "./components/InfoPage";
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
import { useAuth } from "./hooks/useAuth";
import { useWatchlist } from "./hooks/useWatchlist";
import { formatInr, safeHttpUrl } from "./utils/formatting";

const RECENT_KEY = "spa_recent_searches";
const THEME_KEY = "spa_theme";

type Theme = "light" | "dark";

// Effective starting theme: a saved choice wins, else follow the system setting.
function initialTheme(): Theme {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

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
  const [infoPage, setInfoPage] = useState<InfoKey | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>(initialTheme);

  const { loading, data, error, analyse, reset } = useAnalyse();
  const auth = useAuth();
  const watchlist = useWatchlist();

  // Apply the theme to the document root; the CSS reads [data-theme].
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () =>
    setTheme((t) => (t === "dark" ? "light" : "dark"));

  const openInfo = useCallback((page: InfoKey) => {
    setInfoPage(page);
    window.scrollTo({ top: 0 });
  }, []);

  // On app open (and whenever sign-in state settles), re-check watched prices.
  // Signed out this is a silent no-op; signed in, the server only re-checks
  // items whose adaptive interval has elapsed, so it never over-checks.
  const { checkPrices } = watchlist;
  const { signedIn } = auth;
  useEffect(() => {
    if (signedIn) checkPrices();
  }, [checkPrices, signedIn]);

  const openPanel = useCallback(() => {
    if (!signedIn) {
      setAuthOpen(true); // the watchlist needs an account
      return;
    }
    setPanelOpen(true);
    checkPrices(); // opening is an explicit intent, so read the latest
  }, [checkPrices, signedIn]);

  // Every product a signed-in user analyses lands on their watchlist
  // automatically (without touching any target price they may have set).
  const productId = data?.product_id ?? null;
  useEffect(() => {
    if (signedIn && productId) {
      watchlist.add(productId, null, waitDays);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId, signedIn]);

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
    setInfoPage(null);
    setScreen("search");
    reset();
  }

  return (
    <main className="page">
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--sp-3)",
          marginBottom: "var(--sp-6)",
        }}
      >
        <h1
          className="interactive"
          style={{
            fontSize: "var(--fs-xl)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "var(--sp-2)",
          }}
          onClick={backToSearch}
        >
          <span
            aria-hidden="true"
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: "var(--accent-grad)",
              display: "inline-block",
            }}
          />
          Smart Price Advisor
        </h1>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--sp-2)" }}>
          <button
            className="icon-btn"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={theme === "dark" ? "Light mode" : "Dark mode"}
          >
            {theme === "dark" ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z" />
              </svg>
            )}
          </button>
          <button className="btn interactive" onClick={openPanel}>
            Watchlist{watchlist.items.length ? ` (${watchlist.items.length})` : ""}
          </button>
          {auth.signedIn && (
            <button
              className="btn interactive"
              onClick={() => auth.signOut()}
              title={auth.email ?? undefined}
            >
              Sign out
            </button>
          )}
        </div>
      </header>

      {authOpen && !auth.signedIn ? (
        <AuthPage
          onSignIn={auth.signIn}
          onSignUp={auth.signUp}
          onDone={() => {
            setAuthOpen(false);
            setPanelOpen(true);
          }}
          onBack={() => setAuthOpen(false)}
        />
      ) : infoPage ? (
        <InfoPage page={infoPage} onBack={backToSearch} />
      ) : (
        <>
      <AlertBanner items={watchlist.items} onOpen={openPanel} />

      {screen === "search" && (
        <>
          <div
            className="rise-in"
            style={{
              margin: "var(--sp-8) auto var(--sp-6)",
              maxWidth: 760,
              textAlign: "center",
            }}
          >
            <h2 className="display">
              Buy smarter. <span className="accent">Save more.</span>
            </h2>
            <p
              style={{
                marginTop: "var(--sp-4)",
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
          <section className="card container-narrow">
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
          <FeatureGrid />
        </>
      )}

      {screen === "result" && (
        <section className="container-mid">
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
            <div className="stagger">
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
                onAdd={async (productIdIn, target) => {
                  if (!auth.signedIn) {
                    setAuthOpen(true);
                    return {
                      ok: false,
                      message: "Please sign in to set a price alert.",
                    };
                  }
                  return watchlist.add(productIdIn, target, waitDays);
                }}
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
            </div>
          )}
        </section>
      )}

          <Footer onOpenInfo={openInfo} onOpenWatchlist={openPanel} />
        </>
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
