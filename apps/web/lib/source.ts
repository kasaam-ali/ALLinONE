// Job: ALLinONE Frontend. Purpose: Live-first data loader that falls back to fixtures and flags fixture mode for the shell badge.
"use client";
const KEY = "gm_fixture_mode";
export const forcedFixtures = () =>
  process.env.NEXT_PUBLIC_USE_FIXTURES === "1" || process.env.GODMODE_USE_FIXTURES === "1" ||
  (typeof window !== "undefined" && window.localStorage.getItem(KEY) === "1");

export function enableFixtureSession() { window.localStorage.setItem(KEY, "1"); }
export function clearFixtureSession() { window.localStorage.removeItem(KEY); }

function flagFixture() { if (typeof window !== "undefined") window.dispatchEvent(new Event("gm:fixture")); }
function flagLive() { if (typeof window !== "undefined") window.dispatchEvent(new Event("gm:live")); }

/** Try the live API first. Fall back to fixture only when forced or the API is unreachable/5xx. Auth and 4xx errors surface. */
export async function liveOr<T>(live: () => Promise<T>, fixture: () => T): Promise<T> {
  if (forcedFixtures()) { flagFixture(); return fixture(); }
  try {
    const v = await live();
    flagLive();
    return v;
  } catch (e) {
    const s = (e as { status?: number }).status ?? 0;
    if (s === 0 || s >= 500) { flagFixture(); return fixture(); }
    throw e;
  }
}
