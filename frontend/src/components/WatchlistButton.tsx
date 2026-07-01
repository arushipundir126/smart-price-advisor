/*
 * FILE: frontend/src/components/WatchlistButton.tsx
 *
 * WHAT THIS DOES:
 * "Alert me when price drops" with a target-price input that defaults to the
 * current best price. On save it calls the watchlist add action and confirms.
 * When there is no product id yet (database not connected), it disables with a
 * plain note instead of failing.
 *
 * CHANGES THIS SESSION:
 * - Created the target input, save action, and saved/error feedback.
 *
 * WHERE IT FITS:
 * On the verdict screen, between the action strip and the offers.
 *
 * CALLED BY / IMPORTS FROM:
 * No direct API; calls the onAdd prop from App (which wraps useWatchlist).
 */
import { useState } from "react";

interface Props {
  productId: string | null;
  defaultTarget: number | null;
  onAdd: (
    productId: string,
    target: number | null
  ) => Promise<{ ok: boolean; message?: string }>;
}

export default function WatchlistButton({ productId, defaultTarget, onAdd }: Props) {
  const [target, setTarget] = useState<string>(
    defaultTarget != null ? String(Math.round(defaultTarget)) : ""
  );
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [message, setMessage] = useState<string>("");

  if (!productId) {
    return (
      <div className="card" style={{ marginTop: "var(--sp-4)" }}>
        <p style={{ margin: 0, color: "var(--text-muted)" }}>
          Price alerts will be available once tracking is set up for this product.
        </p>
      </div>
    );
  }

  async function save() {
    setStatus("saving");
    const t = target.trim() ? Number(target) : null;
    const res = await onAdd(productId as string, t);
    if (res.ok) {
      setStatus("saved");
      setMessage("We will alert you here when the price drops.");
    } else {
      setStatus("error");
      setMessage(res.message ?? "Could not save. Please try again.");
    }
  }

  return (
    <div className="card" style={{ marginTop: "var(--sp-4)" }}>
      <label
        htmlFor="target-price"
        className="section-label"
        style={{ display: "block", marginBottom: "var(--sp-2)" }}
      >
        Alert me when price drops to
      </label>
      <div style={{ display: "flex", gap: "var(--sp-2)" }}>
        <input
          id="target-price"
          type="number"
          min={1}
          className="input mono"
          value={target}
          placeholder="Target price"
          onChange={(e) => setTarget(e.target.value)}
        />
        <button
          className="btn btn-primary interactive"
          style={{ whiteSpace: "nowrap" }}
          disabled={status === "saving"}
          onClick={save}
        >
          {status === "saving" ? "Saving..." : "Alert me"}
        </button>
      </div>
      {message && (
        <p
          style={{
            margin: "var(--sp-2) 0 0",
            fontSize: "var(--fs-sm)",
            color: status === "error" ? "var(--wait)" : "var(--buy)",
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}
