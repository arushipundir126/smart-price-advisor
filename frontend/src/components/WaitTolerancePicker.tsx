/*
 * FILE: frontend/src/components/WaitTolerancePicker.tsx
 *
 * WHAT THIS DOES:
 * Lets the user say how long they will wait: a dropdown of presets (1 week to
 * 1 year) plus a custom number of days. Emits the value as wait_tolerance_days.
 *
 * CHANGES THIS SESSION:
 * - Created the picker with presets and a custom-days input.
 *
 * WHERE IT FITS:
 * Part of the search screen; its value feeds POST /api/analyse.
 *
 * CALLED BY / IMPORTS FROM:
 * No API. Used by src/App.tsx (search screen).
 */
import { useState } from "react";

interface Props {
  valueDays: number;
  onChange: (days: number) => void;
}

const PRESETS: { label: string; days: number }[] = [
  { label: "1 week", days: 7 },
  { label: "1 month", days: 30 },
  { label: "3 months", days: 90 },
  { label: "6 months", days: 180 },
  { label: "1 year", days: 365 },
];

const CUSTOM = "custom";

export default function WaitTolerancePicker({ valueDays, onChange }: Props) {
  const isPreset = PRESETS.some((p) => p.days === valueDays);
  const [mode, setMode] = useState<string>(isPreset ? String(valueDays) : CUSTOM);

  function handleSelect(next: string) {
    setMode(next);
    if (next !== CUSTOM) onChange(Number(next));
  }

  function handleCustom(raw: string) {
    const n = Math.max(1, Math.min(365, Number(raw) || 1));
    onChange(n);
  }

  return (
    <div>
      <label
        htmlFor="wait-tolerance"
        className="section-label"
        style={{ display: "block", marginBottom: "var(--sp-2)" }}
      >
        How long can you wait?
      </label>
      <select
        id="wait-tolerance"
        className="input interactive"
        value={mode}
        onChange={(e) => handleSelect(e.target.value)}
      >
        {PRESETS.map((p) => (
          <option key={p.days} value={String(p.days)}>
            {p.label}
          </option>
        ))}
        <option value={CUSTOM}>Custom (days)</option>
      </select>

      {mode === CUSTOM && (
        <input
          type="number"
          min={1}
          max={365}
          className="input mono"
          style={{ marginTop: "var(--sp-2)" }}
          placeholder="Number of days (1 to 365)"
          defaultValue={isPreset ? "" : valueDays}
          onChange={(e) => handleCustom(e.target.value)}
          aria-label="Custom number of days to wait"
        />
      )}
    </div>
  );
}
