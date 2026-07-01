/*
 * FILE: frontend/src/components/PriceSparkline.tsx
 *
 * WHAT THIS DOES:
 * A tiny inline SVG line of the product's price history, with the median drawn as
 * a dashed reference line. No chart library, so it stays light on slow 4G. When
 * there is not enough history, it shows a friendly "tracking starts now" note.
 *
 * CHANGES THIS SESSION:
 * - Created the SVG sparkline with a median reference line and empty state.
 *
 * WHERE IT FITS:
 * Bottom of the verdict screen.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Consumes price_history and price_median. Used by src/App.tsx.
 */
interface Props {
  prices: number[];
  median: number | null;
}

const W = 300;
const H = 60;
const PAD = 4;

export default function PriceSparkline({ prices, median }: Props) {
  if (prices.length < 2) {
    return (
      <div className="card" style={{ marginTop: "var(--sp-4)" }}>
        <div className="section-label">Price history</div>
        <p style={{ marginBottom: 0, color: "var(--text-muted)" }}>
          This is the first time we have seen this product. We are tracking it now,
          so check back tomorrow for a price trend.
        </p>
      </div>
    );
  }

  const min = Math.min(...prices, median ?? Infinity);
  const max = Math.max(...prices, median ?? -Infinity);
  const range = max - min || 1;

  const x = (i: number) => PAD + (i / (prices.length - 1)) * (W - 2 * PAD);
  const y = (v: number) => H - PAD - ((v - min) / range) * (H - 2 * PAD);

  const line = prices.map((p, i) => `${x(i)},${y(p)}`).join(" ");
  const medianY = median != null ? y(median) : null;

  return (
    <div className="card" style={{ marginTop: "var(--sp-4)" }}>
      <div className="section-label" style={{ marginBottom: "var(--sp-2)" }}>
        Price history
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        height={H}
        preserveAspectRatio="none"
        role="img"
        aria-label="Price history sparkline"
      >
        {medianY != null && (
          <line
            x1={PAD}
            x2={W - PAD}
            y1={medianY}
            y2={medianY}
            stroke="var(--text-muted)"
            strokeDasharray="4 4"
            strokeWidth={1}
          />
        )}
        <polyline
          points={line}
          fill="none"
          stroke="var(--primary)"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      </svg>
      {median != null && (
        <p
          style={{
            margin: "var(--sp-2) 0 0",
            fontSize: "var(--fs-xs)",
            color: "var(--text-muted)",
          }}
        >
          Dashed line is the usual (median) price.
        </p>
      )}
    </div>
  );
}
