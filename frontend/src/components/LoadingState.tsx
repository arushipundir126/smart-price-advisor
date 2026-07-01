/*
 * FILE: frontend/src/components/LoadingState.tsx
 *
 * WHAT THIS DOES:
 * The loading view shown while a check runs. A useful message plus a skeleton
 * verdict card, so the screen is never blank.
 *
 * CHANGES THIS SESSION:
 * - Created the skeleton loading card with a plain message.
 *
 * WHERE IT FITS:
 * Shown between pressing Analyse and the verdict arriving.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Used by src/App.tsx.
 */
interface Props {
  message?: string;
}

export default function LoadingState({
  message = "Checking live prices across stores...",
}: Props) {
  return (
    <div className="card" role="status" aria-live="polite">
      <p style={{ marginTop: 0, color: "var(--text-muted)" }}>{message}</p>
      <div
        className="skeleton"
        style={{ height: 44, width: "60%", marginBottom: "var(--sp-4)" }}
      />
      <div
        className="skeleton"
        style={{ height: 16, width: "90%", marginBottom: "var(--sp-2)" }}
      />
      <div className="skeleton" style={{ height: 16, width: "75%" }} />
    </div>
  );
}
