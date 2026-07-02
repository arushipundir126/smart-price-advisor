/*
 * FILE: frontend/src/components/Footer.tsx
 *
 * WHAT THIS DOES:
 * The site footer: the app name and tagline, plus three link columns (Product,
 * Company, Legal). Legal includes the Disclaimer and Privacy Policy, which matter
 * for an app that gives purchase guidance. Links open the in-app info pages.
 *
 * CHANGES THIS SESSION:
 * - Created the footer with Product, Company, and Legal columns.
 *
 * WHERE IT FITS:
 * Bottom of every screen. Purely presentational.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Used by src/App.tsx, which handles opening info pages and the panel.
 */
import type { InfoKey } from "./InfoPage";

interface Props {
  onOpenInfo: (page: InfoKey) => void;
  onOpenWatchlist: () => void;
}

const GITHUB_URL = "https://github.com/arushipundir126/smart-price-advisor";

export default function Footer({ onOpenInfo, onOpenWatchlist }: Props) {
  return (
    <footer className="footer">
      <div className="footer__cols">
        <div>
          <h4 style={{ color: "var(--text)", fontSize: "var(--fs-lg)", textTransform: "none", letterSpacing: 0 }}>
            Smart Price Advisor
          </h4>
          <p style={{ margin: 0, fontSize: "var(--fs-sm)", maxWidth: 320 }}>
            Buy now or wait? Evidence-based shopping advice for Indian shoppers,
            backed by live prices, never a guess.
          </p>
        </div>

        <div>
          <h4>Product</h4>
          <button className="link-btn" onClick={() => onOpenInfo("how")}>
            How it works
          </button>
          <button className="link-btn" onClick={onOpenWatchlist}>
            Watchlist
          </button>
          <button className="link-btn" onClick={() => onOpenInfo("about")}>
            About
          </button>
        </div>

        <div>
          <h4>Company</h4>
          <button className="link-btn" onClick={() => onOpenInfo("contact")}>
            Contact
          </button>
          <a
            className="link-btn"
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            Source code
          </a>
        </div>

        <div>
          <h4>Legal</h4>
          <button className="link-btn" onClick={() => onOpenInfo("disclaimer")}>
            Disclaimer
          </button>
          <button className="link-btn" onClick={() => onOpenInfo("privacy")}>
            Privacy Policy
          </button>
          <button className="link-btn" onClick={() => onOpenInfo("terms")}>
            Terms of Use
          </button>
        </div>
      </div>

      <p style={{ fontSize: "var(--fs-xs)", marginTop: "var(--sp-6)" }}>
        Prices are indicative and gathered from third parties. Always confirm on
        the seller's site. This is guidance, not financial advice.
      </p>
    </footer>
  );
}
