/*
 * FILE: frontend/src/components/InfoPage.tsx
 *
 * WHAT THIS DOES:
 * Renders the simple static pages the footer links to: About, How it works,
 * Disclaimer, Privacy Policy, Terms of Use, and Contact. Shown in place (no
 * router needed) with a back button. Copy is plain language, no jargon.
 *
 * CHANGES THIS SESSION:
 * - Created the info pages with real Privacy and Disclaimer copy.
 *
 * WHERE IT FITS:
 * Opened from the footer links. Purely presentational.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Used by src/App.tsx.
 */
export type InfoKey =
  | "about"
  | "how"
  | "disclaimer"
  | "privacy"
  | "terms"
  | "contact";

interface Props {
  page: InfoKey;
  onBack: () => void;
}

function P({ children }: { children: React.ReactNode }) {
  return <p style={{ color: "var(--text-muted)", marginTop: 0 }}>{children}</p>;
}

const CONTENT: Record<InfoKey, { title: string; body: React.ReactNode }> = {
  about: {
    title: "About Smart Price Advisor",
    body: (
      <>
        <P>
          Smart Price Advisor helps Indian shoppers answer one question: buy now,
          or wait? You enter a branded product and how long you can wait, and we
          weigh the live price against price history, upcoming sales, and market
          news to give a clear verdict, backed by evidence, never a guess.
        </P>
        <P>
          Confidence is shown as a band (High, Medium, Low), not a false-precise
          percentage, because honest guidance beats fake certainty.
        </P>
      </>
    ),
  },
  how: {
    title: "How it works",
    body: (
      <>
        <P>
          Six independent checks each vote Buy Now or Wait: a real-discount check,
          the best price across trusted stores, the price-history trend, the days
          to the next sale, how much the category actually moves in sales, and a
          news check for shocks like a new model or an import ban.
        </P>
        <P>
          The verdict combines these, and the confidence band reflects how
          strongly they agree. Prices come only from trusted Indian marketplaces
          and brand stores.
        </P>
      </>
    ),
  },
  disclaimer: {
    title: "Disclaimer",
    body: (
      <>
        <P>
          Prices shown are indicative and are gathered from third-party sources.
          They can change at any time and may differ from the seller's site.
          Always confirm the final price, offers, and availability on the
          retailer's own page before buying.
        </P>
        <P>
          The Buy Now or Wait verdict is guidance based on the data available at
          the time. It is not a guarantee that a price will rise or fall, and it
          is not financial or investment advice. You make your own purchase
          decision.
        </P>
        <P>
          Store names and trademarks belong to their respective owners. We are not
          affiliated with, and not endorsed by, the marketplaces listed.
        </P>
      </>
    ),
  },
  privacy: {
    title: "Privacy Policy",
    body: (
      <>
        <P>
          We keep this simple. There are no accounts and we do not collect
          personal data such as your name, email, or address.
        </P>
        <P>
          Your watchlist is tied to a random ID stored only in your browser. If
          you clear your browser data, your watchlist is gone. We do not link it
          to you.
        </P>
        <P>
          To produce a verdict we send the product you type to third-party
          services (price and shopping data, news, and an AI model) so they can
          return live results. We do not send them any personal information.
        </P>
        <P>
          We do not sell data and we do not run advertising trackers.
        </P>
      </>
    ),
  },
  terms: {
    title: "Terms of Use",
    body: (
      <>
        <P>
          Smart Price Advisor is provided as is, for personal, non-commercial use,
          to help you decide when to buy. Use the information as guidance and
          verify details with the seller before you purchase.
        </P>
        <P>
          We do our best to keep prices and advice accurate, but we cannot
          guarantee they are complete or error-free, and we are not liable for
          decisions made based on them. Please see the Disclaimer.
        </P>
      </>
    ),
  },
  contact: {
    title: "Contact",
    body: (
      <>
        <P>
          Questions, feedback, or a store you think we should add? A direct
          contact option is coming soon. Thank you for your patience.
        </P>
      </>
    ),
  },
};

export default function InfoPage({ page, onBack }: Props) {
  const { title, body } = CONTENT[page];
  return (
    <section style={{ maxWidth: 640, margin: "0 auto" }}>
      <button
        className="btn interactive"
        style={{ marginBottom: "var(--sp-6)" }}
        onClick={onBack}
      >
        ‹ Back to search
      </button>

      <p className="section-label">Smart Price Advisor</p>
      <h2
        className="display"
        style={{
          fontSize: "var(--fs-2xl)",
          margin: "var(--sp-2) 0 var(--sp-6)",
        }}
      >
        {title}
      </h2>

      <div className="card" style={{ lineHeight: 1.65 }}>
        {body}
      </div>
    </section>
  );
}
