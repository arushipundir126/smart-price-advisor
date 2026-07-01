/*
 * FILE: frontend/src/components/ErrorState.tsx
 *
 * WHAT THIS DOES:
 * Shows a plain-language error (vague query, product not found, service down)
 * and always offers a next action: direct Amazon and Flipkart search links so
 * the user is never stuck.
 *
 * CHANGES THIS SESSION:
 * - Created the error card with fallback search links.
 *
 * WHERE IT FITS:
 * Shown on the search/verdict flow when analyse cannot return a verdict.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Used by src/App.tsx.
 */
interface Props {
  message: string;
  product?: string;
}

export default function ErrorState({ message, product }: Props) {
  const q = encodeURIComponent(product ?? "");
  const showLinks = Boolean(product && product.trim());

  return (
    <div className="card">
      <p style={{ marginTop: 0 }}>{message}</p>
      {showLinks && (
        <div>
          <div className="section-label" style={{ marginBottom: "var(--sp-2)" }}>
            Search directly
          </div>
          <div style={{ display: "flex", gap: "var(--sp-2)", flexWrap: "wrap" }}>
            <a
              className="btn interactive"
              href={`https://www.amazon.in/s?k=${q}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Amazon
            </a>
            <a
              className="btn interactive"
              href={`https://www.flipkart.com/search?q=${q}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Flipkart
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
