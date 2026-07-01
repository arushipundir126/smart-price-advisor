/*
 * FILE: frontend/src/components/StackableDiscounts.tsx
 *
 * WHAT THIS DOES:
 * A collapsible "Save more" section listing bank offers, coupons, and gift-card
 * routes that lower the effective price. Collapsed by default. Renders nothing
 * when there are no offers.
 *
 * CHANGES THIS SESSION:
 * - Created the collapsible offers list using native details/summary.
 *
 * WHERE IT FITS:
 * Below the action strip on the verdict screen.
 *
 * CALLED BY / IMPORTS FROM:
 * Imports formatInr and the Discount type. Used by src/App.tsx.
 */
import type { Discount } from "../hooks/useAnalyse";
import { formatInr } from "../utils/formatting";

interface Props {
  discounts: Discount[];
}

export default function StackableDiscounts({ discounts }: Props) {
  if (!discounts.length) return null;

  return (
    <details className="card interactive" style={{ marginTop: "var(--sp-4)" }}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>
        Save more: tap to see offers ({discounts.length})
      </summary>
      <ul style={{ margin: "var(--sp-4) 0 0", paddingLeft: "var(--sp-4)" }}>
        {discounts.map((d, i) => (
          <li key={i} style={{ marginBottom: "var(--sp-2)" }}>
            {d.description}
            {d.estimated_saving_inr > 0 && (
              <span className="mono" style={{ color: "var(--buy)" }}>
                {" "}
                (save up to {formatInr(d.estimated_saving_inr)})
              </span>
            )}
          </li>
        ))}
      </ul>
    </details>
  );
}
