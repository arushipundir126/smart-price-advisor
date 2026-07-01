/*
 * FILE: frontend/src/components/SignalBreakdown.tsx
 *
 * WHAT THIS DOES:
 * A collapsible "How we decided" section. Lists each signal with its vote in
 * plain words and a short reason, so the verdict is transparent, not a black box.
 *
 * CHANGES THIS SESSION:
 * - Created the collapsible signal list with plain vote labels.
 *
 * WHERE IT FITS:
 * Below the discounts on the verdict screen, collapsed by default.
 *
 * CALLED BY / IMPORTS FROM:
 * Imports the SignalSummary type. Used by src/App.tsx.
 */
import type { SignalSummary } from "../hooks/useAnalyse";

interface Props {
  signals: SignalSummary[];
}

function voteLabel(vote: SignalSummary["vote"]): { text: string; color: string } {
  if (vote === "buy_now") return { text: "Buy now", color: "var(--buy)" };
  if (vote === "wait") return { text: "Wait", color: "var(--wait)" };
  return { text: "No strong signal", color: "var(--text-muted)" };
}

// Turn a raw signal key like "days_to_next_sale" into "Days to next sale".
function prettyName(name: string): string {
  const s = name.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export default function SignalBreakdown({ signals }: Props) {
  if (!signals.length) return null;

  return (
    <details className="card interactive" style={{ marginTop: "var(--sp-4)" }}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>
        How we decided ({signals.length} signals)
      </summary>
      <ul style={{ listStyle: "none", margin: "var(--sp-4) 0 0", padding: 0 }}>
        {signals.map((s, i) => {
          const label = voteLabel(s.vote);
          return (
            <li
              key={i}
              style={{
                paddingBottom: "var(--sp-3)",
                marginBottom: "var(--sp-3)",
                borderBottom:
                  i < signals.length - 1 ? "1px solid var(--border)" : "none",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "var(--sp-3)",
                }}
              >
                <span style={{ fontWeight: 600 }}>{prettyName(s.signal)}</span>
                <span
                  className="chip"
                  style={{ color: label.color, whiteSpace: "nowrap" }}
                >
                  {label.text}
                </span>
              </div>
              <p
                style={{
                  margin: "var(--sp-1) 0 0",
                  fontSize: "var(--fs-sm)",
                  color: "var(--text-muted)",
                }}
              >
                {s.plain_reason}
              </p>
            </li>
          );
        })}
      </ul>
    </details>
  );
}
