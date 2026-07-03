/*
 * FILE: frontend/src/components/AuthPage.tsx
 *
 * WHAT THIS DOES:
 * The sign-in / create-account screen. Email and password only, with a toggle
 * between the two modes, inline plain-language errors, and a loading state on
 * the button. Shown when a signed-out user tries to use the watchlist.
 *
 * CHANGES THIS SESSION:
 * - Created the screen with sign-in and create-account modes.
 *
 * WHERE IT FITS:
 * Rendered by App when the watchlist is opened while signed out.
 *
 * CALLED BY / IMPORTS FROM:
 * Receives signIn/signUp from useAuth via props. Used by src/App.tsx.
 */
import { useState } from "react";

import type { AuthResult } from "../hooks/useAuth";

interface Props {
  onSignIn: (email: string, password: string) => Promise<AuthResult>;
  onSignUp: (email: string, password: string) => Promise<AuthResult>;
  onDone: () => void;
  onBack: () => void;
}

export default function AuthPage({ onSignIn, onSignUp, onDone, onBack }: Props) {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const isSignup = mode === "signup";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setError(null);
    setBusy(true);
    const action = isSignup ? onSignUp : onSignIn;
    const result = await action(email, password);
    setBusy(false);
    if (result.ok) {
      onDone();
    } else {
      setError(result.message ?? "Please try again in a moment.");
    }
  }

  return (
    <section className="container-narrow rise-in">
      <button
        className="btn interactive"
        style={{ marginBottom: "var(--sp-6)" }}
        onClick={onBack}
      >
        Back
      </button>

      <div className="card" style={{ padding: "var(--sp-8) var(--sp-6)" }}>
        <h2 style={{ fontSize: "var(--fs-2xl)", marginBottom: "var(--sp-2)" }}>
          {isSignup ? "Create your account" : "Welcome back"}
        </h2>
        <p style={{ marginTop: 0, color: "var(--text-muted)" }}>
          Sign in to keep a watchlist that follows you on any device, and get an
          alert here when a price falls.
        </p>

        <form onSubmit={submit}>
          <label
            htmlFor="auth-email"
            className="section-label"
            style={{ display: "block", marginBottom: "var(--sp-1)" }}
          >
            Email
          </label>
          <input
            id="auth-email"
            className="input"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label
            htmlFor="auth-password"
            className="section-label"
            style={{
              display: "block",
              margin: "var(--sp-4) 0 var(--sp-1)",
            }}
          >
            Password
          </label>
          <input
            id="auth-password"
            className="input"
            type="password"
            autoComplete={isSignup ? "new-password" : "current-password"}
            placeholder={
              isSignup ? "At least 8 characters, one letter and one number" : ""
            }
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />

          {error && (
            <p style={{ color: "var(--wait)", marginBottom: 0 }}>{error}</p>
          )}

          <button
            className="btn btn-primary btn-block"
            style={{ marginTop: "var(--sp-6)" }}
            type="submit"
            disabled={busy}
          >
            {busy
              ? "One moment"
              : isSignup
                ? "Create account"
                : "Sign in"}
          </button>
        </form>

        <button
          className="link-btn"
          style={{ marginTop: "var(--sp-4)" }}
          onClick={() => {
            setMode(isSignup ? "signin" : "signup");
            setError(null);
          }}
        >
          {isSignup
            ? "Already have an account? Sign in"
            : "New here? Create an account"}
        </button>
      </div>
    </section>
  );
}
