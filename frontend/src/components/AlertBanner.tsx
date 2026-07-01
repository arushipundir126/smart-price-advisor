/*
 * FILE: frontend/src/components/AlertBanner.tsx
 *
 * WHAT THIS DOES:
 * The in-app price-drop notification. When any watched item has fallen to or
 * below its target and is not yet bought, it shows a short banner that opens the
 * watchlist. Renders nothing when there is nothing to announce.
 *
 * CHANGES THIS SESSION:
 * - Created the banner with drop detection and an open-watchlist action.
 *
 * WHERE IT FITS:
 * At the top of the app, above the current screen.
 *
 * CALLED BY / IMPORTS FROM:
 * Imports formatInr and the WatchlistItem type. Used by src/App.tsx.
 */
import type { WatchlistItem } from "../hooks/useWatchlist";
import { formatInr } from "../utils/formatting";

interface Props {
  items: WatchlistItem[];
  onOpen: () => void;
}

export default function AlertBanner({ items, onOpen }: Props) {
  const dropped = items.filter(
    (i) =>
      !i.purchased &&
      i.latest_price != null &&
      i.target_price != null &&
      i.latest_price <= i.target_price
  );
  if (dropped.length === 0) return null;

  const first = dropped[0];
  const extra = dropped.length - 1;

  return (
    <button
      className="card interactive"
      onClick={onOpen}
      style={{
        display: "block",
        width: "100%",
        textAlign: "left",
        background: "var(--buy-bg)",
        borderColor: "var(--buy)",
        marginBottom: "var(--sp-4)",
      }}
    >
      <span style={{ fontWeight: 600, color: "var(--buy)" }}>Good news. </span>
      {first.name ?? "A tracked product"} dropped to {formatInr(first.latest_price)}
      {extra > 0 && <> and {extra} more</>}. Tap to view your watchlist.
    </button>
  );
}
