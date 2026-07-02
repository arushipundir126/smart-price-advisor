/*
 * FILE: frontend/src/components/VerdictCard.tsx
 *
 * WHAT THIS DOES:
 * The headline card: Buy Now (green) or Wait (amber), the confidence band chip
 * (High/Medium/Low), and the one-line reason. Colour is paired with the word and
 * the band label, so it never relies on colour alone.
 *
 * CHANGES THIS SESSION:
 * - Created the verdict card with colour theming and the confidence chip.
 * - Reworked into a gradient hero with a stronger headline and a confidence
 *   chip variant (High/Medium/Low), for a premium, high-presence look.
 *
 * WHERE IT FITS:
 * Top of the verdict screen, the single most important element.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Consumes fields from the Verdict type. Used by src/App.tsx.
 */
interface Props {
  verdict: "Buy Now" | "Wait";
  confidence: "High" | "Medium" | "Low";
  summaryReason: string;
}

export default function VerdictCard({ verdict, confidence, summaryReason }: Props) {
  const isBuy = verdict === "Buy Now";
  const accent = isBuy ? "var(--buy)" : "var(--wait)";
  const chipClass = `chip chip--${confidence.toLowerCase()}`;

  return (
    <div className={`hero ${isBuy ? "hero--buy" : "hero--wait"}`}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--sp-3)",
          marginBottom: "var(--sp-3)",
        }}
      >
        <span className="section-label" style={{ color: accent }}>
          Our verdict
        </span>
        <span className={chipClass} title="How strongly the signals agree">
          {confidence} confidence
        </span>
      </div>
      <div
        style={{
          fontSize: "var(--fs-3xl)",
          fontWeight: 800,
          lineHeight: 1.1,
          letterSpacing: "-0.02em",
          color: accent,
        }}
      >
        {verdict}
      </div>
      <p
        style={{
          marginBottom: 0,
          marginTop: "var(--sp-3)",
          fontSize: "var(--fs-lg)",
          color: "var(--text)",
        }}
      >
        {summaryReason}
      </p>
    </div>
  );
}
