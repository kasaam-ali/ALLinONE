<!--
Job: GODMODE Database
Purpose: Explain how to apply ordered Postgres migrations for GODMODE MVP.
-->

# migrations

Ordered SQL for the Architect-locked schema.

1. `001_init.sql` - tables, constraints, indexes, triggers
2. `002_seed.sql` - demo `agent_definitions` (admin user via app seed)

Run in order against an empty database. Do not claim production readiness from these files alone.
