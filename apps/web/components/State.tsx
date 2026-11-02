// Job: GODMODE Frontend. Purpose: Shared loading and error UI helpers for empty or failed API calls.
export function Loading() { return <p className="muted" role="status">Loading...</p>; }
export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card error" role="alert">
      <strong>Could not load data.</strong> <span>{message}</span>
      {onRetry && <button className="ghost" onClick={onRetry}>Retry</button>}
    </div>
  );
}
export function Empty({ text }: { text: string }) { return <p className="muted empty">{text}</p>; }
export function Badge({ value }: { value: string }) { return <span className={`badge ${value}`}>{value}</span>; }
export const fmt = (d?: string) => (d ? new Date(d).toLocaleString() : "-");
