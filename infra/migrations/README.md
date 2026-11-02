<!--
Job: GODMODE Database
Purpose: Explain how to apply ordered Postgres migrations for GODMODE MVP.
-->

# migrations

Ordered SQL for the Architect-locked schema (G2).

1. `001_init.sql` - tables, constraints, indexes, triggers
2. `002_seed.sql` - demo `agent_definitions` (admin user via app seed)

Gates: `after_plan` and `before_publish` only. Report publish links via `reports.publish_approval_id`.
