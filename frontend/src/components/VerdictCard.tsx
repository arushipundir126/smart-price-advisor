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
  const tint = isBuy ? "var(--buy-bg)" : "var(--wait-bg)";

  return (
    <div
      className="card"
      style={{ background: tint, borderColor: accent, borderWidth: 2 }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--sp-3)",
        }}
      >
        <span
          style={{ fontSize: "var(--fs-2xl)", fontWeight: 700, color: accent }}
        >
          {verdict}
        </span>
        <span
          className="chip"
          style={{ background: accent, color: "#ffffff" }}
          title="How strongly the signals agree"
        >
          {confidence} confidence
        </span>
      </div>
      <p style={{ marginBottom: 0, marginTop: "var(--sp-3)" }}>{summaryReason}</p>
    </div>
  );
}
