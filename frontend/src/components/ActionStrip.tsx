/*
 * FILE: frontend/src/components/ActionStrip.tsx
 *
 * WHAT THIS DOES:
 * Shows the best price now, the platform, and a Buy button that opens the seller
 * in a new tab. When the verdict is Wait, it also shows how long the best deal is
 * expected to take and where.
 *
 * CHANGES THIS SESSION:
 * - Created the action strip with best price, buy link, and wait estimate.
 * - Larger price, green buy button (buy affordance), and the new button style.
 *
 * WHERE IT FITS:
 * Directly under the verdict card on the verdict screen.
 *
 * CALLED BY / IMPORTS FROM:
 * Imports formatInr. Consumes Verdict fields. Used by src/App.tsx.
 */
import { formatInr, safeHttpUrl } from "../utils/formatting";

interface Props {
  verdict: "Buy Now" | "Wait";
  bestPrice: number | null;
  bestPlatform: string | null;
  buyLink: string | null;
  waitEstimateDays: number | null;
}

export default function ActionStrip({
  verdict,
  bestPrice,
  bestPlatform,
  buyLink,
  waitEstimateDays,
}: Props) {
  return (
    <div className="card" style={{ marginTop: "var(--sp-4)" }}>
      <div className="section-label">Best price now</div>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: "var(--sp-3)",
          marginTop: "var(--sp-1)",
        }}
      >
        <span className="mono" style={{ fontSize: "var(--fs-2xl)", fontWeight: 800 }}>
          {formatInr(bestPrice)}
        </span>
        {bestPlatform && (
          <span style={{ color: "var(--text-muted)" }}>on {bestPlatform}</span>
        )}
      </div>

      {safeHttpUrl(buyLink) && bestPlatform && (
        <a
          className="btn btn-buy btn-block"
          style={{ marginTop: "var(--sp-4)", display: "block", textAlign: "center" }}
          href={safeHttpUrl(buyLink) as string}
          target="_blank"
          rel="noopener noreferrer"
        >
          Buy on {bestPlatform}
        </a>
      )}

      {verdict === "Wait" && waitEstimateDays != null && (
        <p style={{ marginBottom: 0, marginTop: "var(--sp-4)", color: "var(--text-muted)" }}>
          Best deal expected in about {waitEstimateDays} days
          {bestPlatform ? ` on ${bestPlatform}` : ""}.
        </p>
      )}
    </div>
  );
}
