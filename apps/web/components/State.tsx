// Job: ALLinONE Frontend. Purpose: Operational loading, error, empty, and status badge UI helpers.
export function Loading() {
  return (
    <div className="skeleton" role="status" aria-label="Loading">
      {[0, 1, 2, 3].map((i) => <div key={i} className="sk-row" />)}
    </div>
  );
}
export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="notice error" role="alert">
      <span className="dot bad" /><strong>Request failed</strong><span className="muted">{message}</span>
      {onRetry && <button className="ghost sm" onClick={onRetry}>Retry</button>}
    </div>
  );
}
export function Empty({ text }: { text: string }) { return <div className="notice"><span className="dot" /><span className="muted">{text}</span></div>; }
export function Badge({ value }: { value: string }) { return <span className={`badge ${value}`}><i />{value.replace(/_/g, " ")}</span>; }
export const fmt = (d?: string) => (d ? new Date(d).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "-");
