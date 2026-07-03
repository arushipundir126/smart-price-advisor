/*
 * FILE: frontend/src/lib/supabase.ts
 *
 * WHAT THIS DOES:
 * Creates the one Supabase browser client used for sign-in. Uses the anon key,
 * which is client-safe by design (it can only do what signed-in users are
 * allowed to do). Session persistence and token refresh are handled for us.
 *
 * CHANGES THIS SESSION:
 * - Created the shared client.
 *
 * WHERE IT FITS:
 * The auth foundation. useAuth builds on this.
 *
 * CALLED BY / IMPORTS FROM:
 * Reads VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY. Used by hooks/useAuth.ts.
 */
import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL ?? "";
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ?? "";

export const supabase = createClient(url, anonKey);

export const authConfigured = Boolean(url && anonKey);

/** Current access token, or null when signed out. Used for API calls. */
export async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}
