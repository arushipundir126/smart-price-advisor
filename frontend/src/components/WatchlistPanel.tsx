/*
 * FILE: frontend/src/components/WatchlistPanel.tsx
 *
 * WHAT THIS DOES:
 * The Claude-style watchlist panel that slides in from the right. Lists each
 * watched item with its current price, target, and status (Tracking, Price
 * dropped, or Bought), each with Remove and Bought actions. Shows a friendly
 * empty state and plain error/loading views.
 *
 * CHANGES THIS SESSION:
 * - Created the panel, item rows, status logic, and empty/loading/error states.
 *
 * WHERE IT FITS:
 * Toggled from the header on every screen. Backed by the watchlist hook in App.
 *
 * CALLED BY / IMPORTS FROM:
 * Imports formatInr and the WatchlistItem type. Used by src/App.tsx.
 */
import type { WatchlistItem } from "../hooks/useWatchlist";
import { formatInr } from "../utils/formatting";

interface Props {
  open: boolean;
  onClose: () => void;
  items: WatchlistItem[];
  loading: boolean;
  error: string | null;
  onRemove: (productId: string) => void;
  onMarkBought: (productId: string) => void;
}

function status(item: WatchlistItem): { text: string; color: string } {
  if (item.purchased) return { text: "Bought", color: "var(--text-muted)" };
  const dropped =
    item.latest_price != null &&
    item.target_price != null &&
    item.latest_price <= item.target_price;
  if (dropped) return { text: "Price dropped", color: "var(--buy)" };
  return { text: "Tracking", color: "var(--text-muted)" };
}

export default function WatchlistPanel({
  open,
  onClose,
  items,
  loading,
  error,
  onRemove,
  onMarkBought,
}: Props) {
  return (
    <>
      <div
        className={`backdrop${open ? " open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={`side-panel${open ? " open" : ""}`}
        aria-hidden={!open}
        aria-label="Watchlist"
      >
        <div className="side-panel__header">
          <h2 style={{ fontSize: "var(--fs-lg)" }}>Watchlist</h2>
          <button
            className="btn interactive"
            style={{ padding: "6px 12px" }}
            onClick={onClose}
            aria-label="Close watchlist"
          >
            Close
          </button>
        </div>

        <div className="side-panel__body">
          {loading && (
            <div className="skeleton" style={{ height: 80, marginBottom: "var(--sp-3)" }} />
          )}

          {!loading && error && (
            <p style={{ color: "var(--text-muted)" }}>{error}</p>
          )}

          {!loading && !error && items.length === 0 && (
            <p style={{ color: "var(--text-muted)" }}>
              Nothing here yet. Search a product and tap "Alert me when price
              drops" to start tracking it.
            </p>
          )}

          {!loading &&
            !error &&
            items.map((item) => {
              const st = status(item);
              return (
                <div
                  key={item.id}
                  className="card"
                  style={{
                    padding: "var(--sp-4)",
                    marginBottom: "var(--sp-3)",
                    opacity: item.purchased ? 0.6 : 1,
                  }}
                >
                  <div style={{ fontWeight: 600 }}>
                    {item.name ?? "Tracked product"}
                  </div>
                  <div
                    className="mono"
                    style={{ marginTop: "var(--sp-1)", color: "var(--text-muted)" }}
                  >
                    Now {formatInr(item.latest_price)}
                    {item.target_price != null && (
                      <> · target {formatInr(item.target_price)}</>
                    )}
                  </div>
                  <span
                    className="chip"
                    style={{ color: st.color, marginTop: "var(--sp-2)" }}
                  >
                    {st.text}
                  </span>
                  <div style={{ display: "flex", gap: "var(--sp-2)", marginTop: "var(--sp-3)" }}>
                    {!item.purchased && (
                      <button
                        className="btn interactive"
                        style={{ padding: "6px 12px", fontSize: "var(--fs-sm)" }}
                        onClick={() => onMarkBought(item.product_id)}
                      >
                        Bought
                      </button>
                    )}
                    <button
                      className="btn interactive"
                      style={{ padding: "6px 12px", fontSize: "var(--fs-sm)" }}
                      onClick={() => onRemove(item.product_id)}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              );
            })}
        </div>
      </aside>
    </>
  );
}
