// React hook: loads an API resource on mount and exposes loading, error, and reload.
"use client";
import { useCallback, useEffect, useState } from "react";

export function useApi<T>(load: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(() => {
    setLoading(true); setError("");
    load().then(setData).catch((e: Error) => setError(e.message)).finally(() => setLoading(false));
  }, deps);
  useEffect(run, [run]);
  return { data, error, loading, reload: run };
}
