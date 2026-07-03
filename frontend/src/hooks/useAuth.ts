/*
 * FILE: frontend/src/hooks/useAuth.ts
 *
 * WHAT THIS DOES:
 * Sign-in state for the whole app. Exposes the signed-in user's email, sign up
 * (via our backend, which validates the email and skips verification mail),
 * sign in, sign out, and getToken() for authenticated API calls. All failures
 * become plain-language messages.
 *
 * CHANGES THIS SESSION:
 * - Created the hook with signUp, signIn, signOut, and token access.
 *
 * WHERE IT FITS:
 * Backs the AuthPage and the watchlist gating in App.
 *
 * CALLED BY / IMPORTS FROM:
 * Uses lib/supabase and VITE_API_BASE_URL. Called by src/App.tsx and AuthPage.
 */
import { useEffect, useState } from "react";

import { supabase } from "../lib/supabase";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

const WRONG_CREDENTIALS =
  "That email and password do not match. Please try again.";
const GENERIC_AUTH_ERROR =
  "We could not sign you in just now. Please try again in a moment.";

export interface AuthResult {
  ok: boolean;
  message?: string;
}

export function useAuth() {
  const [email, setEmail] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setEmail(data.session?.user?.email ?? null);
      setReady(true);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      setEmail(session?.user?.email ?? null);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  async function signIn(emailIn: string, password: string): Promise<AuthResult> {
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: emailIn.trim(),
        password,
      });
      if (error) return { ok: false, message: WRONG_CREDENTIALS };
      return { ok: true };
    } catch {
      return { ok: false, message: GENERIC_AUTH_ERROR };
    }
  }

  async function signUp(emailIn: string, password: string): Promise<AuthResult> {
    try {
      const resp = await fetch(`${API_BASE}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailIn.trim(), password }),
      });
      const json = await resp.json();
      if (!resp.ok || json.error) {
        return { ok: false, message: json.message ?? GENERIC_AUTH_ERROR };
      }
      // Account created; sign straight in (no verification mail needed).
      return signIn(emailIn, password);
    } catch {
      return { ok: false, message: GENERIC_AUTH_ERROR };
    }
  }

  async function signOut() {
    try {
      await supabase.auth.signOut();
    } catch {
      // Ignore; local session is cleared regardless.
    }
  }

  async function getToken(): Promise<string | null> {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }

  return { email, signedIn: email !== null, ready, signIn, signUp, signOut, getToken };
}
