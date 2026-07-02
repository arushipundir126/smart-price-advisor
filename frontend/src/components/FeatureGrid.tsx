/*
 * FILE: frontend/src/components/FeatureGrid.tsx
 *
 * WHAT THIS DOES:
 * The "How it works" section on the search screen. Six cards, one per signal the
 * engine uses, each with a small inline SVG icon, a title, and a plain-language
 * line. Explains what the app does at a glance, like a landing-page features grid.
 *
 * CHANGES THIS SESSION:
 * - Created the six-signal features grid with inline icons (no image assets, to
 *   stay light on slow 4G).
 *
 * WHERE IT FITS:
 * Below the search box on the search screen. Purely presentational.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Used by src/App.tsx.
 */
import type { ReactNode } from "react";

interface Feature {
  icon: ReactNode;
  title: string;
  text: string;
}

// Small stroked line icons, sized to the feature badge.
const svg = (path: ReactNode) => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    {path}
  </svg>
);

const FEATURES: Feature[] = [
  {
    icon: svg(<><path d="M12 2v20" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></>),
    title: "Real discount check",
    text: "We compare the live price to the MRP and to the product's own usual price, so a fake sale cannot fool you.",
  },
  {
    icon: svg(<><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></>),
    title: "Best price, everywhere",
    text: "We scan trusted Indian stores at once and point you to the cheapest genuine seller right now.",
  },
  {
    icon: svg(<><path d="M3 3v18h18" /><path d="m19 9-5 5-4-4-4 4" /></>),
    title: "Price history",
    text: "Every check is saved, so we can show the price trend and whether it is rising or falling.",
  },
  {
    icon: svg(<><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></>),
    title: "Sale calendar",
    text: "We know the big Indian sales and the bank offers that come with them, so you never miss a real deal.",
  },
  {
    icon: svg(<><path d="M3 3v18h18" /><rect x="7" y="12" width="3" height="6" /><rect x="12" y="8" width="3" height="10" /><rect x="17" y="5" width="3" height="13" /></>),
    title: "Category smarts",
    text: "Phones fall a lot in sales, staples barely move. We factor in how much each category really changes.",
  },
  {
    icon: svg(<><path d="M4 22V4a2 2 0 0 1 2-2h9l5 5v15a1 1 0 0 1-1 1H4Z" /><path d="M8 8h5M8 12h8M8 16h8" /></>),
    title: "Market news",
    text: "A new model, an import ban, or a price cut can change the timing. We watch the news that matters.",
  },
];

export default function FeatureGrid() {
  return (
    <section style={{ marginTop: "var(--sp-8)" }}>
      <p className="section-label" style={{ textAlign: "center" }}>
        How it works
      </p>
      <h3
        style={{
          fontSize: "var(--fs-2xl)",
          textAlign: "center",
          margin: "var(--sp-2) 0 var(--sp-6)",
        }}
      >
        Six checks behind every verdict.
      </h3>
      <div className="feature-grid">
        {FEATURES.map((f) => (
          <div className="card interactive" key={f.title}>
            <span className="feature-icon">{f.icon}</span>
            <h4 style={{ margin: "0 0 var(--sp-2)", fontSize: "var(--fs-lg)" }}>
              {f.title}
            </h4>
            <p style={{ margin: 0, color: "var(--text-muted)", fontSize: "var(--fs-sm)" }}>
              {f.text}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
