/*
 * FILE: frontend/src/components/SearchBar.tsx
 *
 * WHAT THIS DOES:
 * The product input and the primary Analyse button, plus recent searches. The
 * button is disabled until the input has text, and shows a busy label while a
 * check is running.
 *
 * CHANGES THIS SESSION:
 * - Created the input, submit button, and recent-search chips.
 *
 * WHERE IT FITS:
 * The top of the search screen. Submitting triggers the analyse flow in App.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Used by src/App.tsx.
 */
interface Props {
  product: string;
  onProductChange: (value: string) => void;
  onSubmit: () => void;
  busy: boolean;
  recent: string[];
  onSelectRecent: (term: string) => void;
}

export default function SearchBar({
  product,
  onProductChange,
  onSubmit,
  busy,
  recent,
  onSelectRecent,
}: Props) {
  const canSubmit = product.trim().length > 0 && !busy;

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && canSubmit) onSubmit();
  }

  return (
    <div>
      <label
        htmlFor="product"
        className="section-label"
        style={{ display: "block", marginBottom: "var(--sp-2)" }}
      >
        Enter a product
      </label>
      <input
        id="product"
        className="input"
        autoFocus
        value={product}
        placeholder="e.g. Samsung Galaxy S24"
        onChange={(e) => onProductChange(e.target.value)}
        onKeyDown={handleKeyDown}
      />

      <button
        className="btn btn-primary btn-block interactive"
        style={{ marginTop: "var(--sp-4)" }}
        disabled={!canSubmit}
        onClick={onSubmit}
      >
        {busy ? "Checking prices..." : "Analyse"}
      </button>

      {recent.length > 0 && (
        <div style={{ marginTop: "var(--sp-6)" }}>
          <div className="section-label" style={{ marginBottom: "var(--sp-2)" }}>
            Recent
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--sp-2)" }}>
            {recent.map((term) => (
              <button
                key={term}
                className="chip interactive"
                onClick={() => onSelectRecent(term)}
              >
                {term}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
