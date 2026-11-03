// Job: ALLinONE Frontend. Purpose: Reusable resource wrapper for loading, error, and empty states.
"use client";
import type { ReactNode } from "react";
import { Empty, ErrorBox, Loading } from "./State";

export function Resource<T>({ r, empty, children }: {
  r: { data: T | null; error: string; loading: boolean; reload: () => void };
  empty?: string;
  children: (d: T) => ReactNode;
}) {
  if (r.loading) return <Loading />;
  if (r.error) return <ErrorBox message={r.error} onRetry={r.reload} />;
  if (r.data == null || (Array.isArray(r.data) && r.data.length === 0)) return <Empty text={empty || "Nothing here yet."} />;
  return <>{children(r.data)}</>;
}
