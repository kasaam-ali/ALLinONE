# lib

- `api.ts` single typed client for the `/api/v1` contract, token storage, refresh on 401.
- `types.ts` domain types: Task, Run, StageEvent, Artifact, Approval, Agent, Report, AuditEntry, DashboardSummary.
- `useApi.ts` React hook returning `{ data, error, loading, reload }`.
