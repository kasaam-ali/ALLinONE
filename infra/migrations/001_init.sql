-- Job: ALLinONE Database
-- Purpose: Canonical Postgres DDL for the Architect-locked MVP domain model (G2).

-- GODMODE Postgres schema. Architect LOCKED model (CTO 2026-11-03).
-- Source of truth for migrations: also copied to /workspace/godmode/repo/infra/migrations/
-- Entities: users, agent_definitions, tasks, runs, stage_events, artifacts,
--           approvals, audit_logs, memory_items, reports
-- AgentInstance CUT for MVP. SoT = Postgres. Local MVP schema, not a production claim.
-- Approval gates ONLY: after_plan | before_publish.
-- Report publish links via publish_approval_id -> approvals(before_publish).
-- Updated: 2026-11-03 Asia/Karachi. Owner: GODMODE Database

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- users (role embedded: admin | operator | viewer)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL,
    email_norm      TEXT NOT NULL,
    display_name    TEXT NOT NULL DEFAULT '',
    role            TEXT NOT NULL DEFAULT 'operator',
    password_hash   TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT users_email_norm_unique UNIQUE (email_norm),
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'operator', 'viewer'))
);

CREATE INDEX idx_users_role ON users (role);
CREATE INDEX idx_users_active ON users (is_active) WHERE is_active = TRUE;

-- agent_definitions (workforce catalog; AgentInstance cut)
CREATE TABLE agent_definitions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug             TEXT NOT NULL,
    name             TEXT NOT NULL,
    role_prompt      TEXT NOT NULL DEFAULT '',
    tools_allowlist  JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_config     JSONB NOT NULL DEFAULT '{}'::jsonb,
    status           TEXT NOT NULL DEFAULT 'active',
    version          INTEGER NOT NULL DEFAULT 1,
    created_by       UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT agent_definitions_slug_unique UNIQUE (slug),
    CONSTRAINT agent_definitions_status_check CHECK (status IN ('active', 'disabled'))
);

CREATE INDEX idx_agent_definitions_status ON agent_definitions (status);

-- tasks
CREATE TABLE tasks (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title                   TEXT NOT NULL,
    description             TEXT NOT NULL DEFAULT '',
    priority                SMALLINT NOT NULL DEFAULT 0,
    status                  TEXT NOT NULL DEFAULT 'draft',
    created_by              UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_orchestrator   UUID REFERENCES agent_definitions(id) ON DELETE SET NULL,
    parent_task_id          UUID REFERENCES tasks(id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT tasks_status_check CHECK (status IN (
        'draft', 'queued', 'running', 'awaiting_approval',
        'succeeded', 'failed', 'cancelled'
    ))
);

CREATE INDEX idx_tasks_status_created_at ON tasks (status, created_at DESC);
CREATE INDEX idx_tasks_created_by_created_at ON tasks (created_by, created_at DESC);
CREATE INDEX idx_tasks_parent ON tasks (parent_task_id) WHERE parent_task_id IS NOT NULL;

-- runs (one orchestration attempt per task)
CREATE TABLE runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'queued',
    current_stage   TEXT,
    mock_llm        BOOLEAN NOT NULL DEFAULT TRUE,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    error_summary   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT runs_status_check CHECK (status IN (
        'draft', 'queued', 'running', 'awaiting_approval',
        'succeeded', 'failed', 'cancelled'
    )),
    CONSTRAINT runs_stage_check CHECK (
        current_stage IS NULL OR current_stage IN (
            'plan', 'research', 'execute', 'verify', 'report'
        )
    )
);

CREATE INDEX idx_runs_task_id ON runs (task_id, created_at DESC);
CREATE INDEX idx_runs_status ON runs (status) WHERE status IN ('queued', 'running', 'awaiting_approval');

-- stage_events
CREATE TABLE stage_events (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    stage                 TEXT NOT NULL,
    status                TEXT NOT NULL,
    agent_definition_id   UUID REFERENCES agent_definitions(id) ON DELETE SET NULL,
    input_ref             TEXT,
    output_ref            TEXT,
    detail                JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at            TIMESTAMPTZ,
    finished_at           TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT stage_events_stage_check CHECK (stage IN (
        'plan', 'research', 'execute', 'verify', 'report'
    )),
    CONSTRAINT stage_events_status_check CHECK (status IN (
        'started', 'succeeded', 'failed', 'skipped'
    ))
);

CREATE INDEX idx_stage_events_run_id ON stage_events (run_id, created_at);
CREATE INDEX idx_stage_events_run_stage ON stage_events (run_id, stage);

-- artifacts
CREATE TABLE artifacts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id       UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    stage        TEXT NOT NULL,
    kind         TEXT NOT NULL,
    body_text    TEXT,
    storage_uri  TEXT,
    mime         TEXT NOT NULL DEFAULT 'text/plain',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT artifacts_stage_check CHECK (stage IN (
        'plan', 'research', 'execute', 'verify', 'report'
    )),
    CONSTRAINT artifacts_kind_check CHECK (kind IN (
        'plan', 'research', 'result', 'verification', 'report', 'other'
    )),
    CONSTRAINT artifacts_body_or_uri CHECK (body_text IS NOT NULL OR storage_uri IS NOT NULL)
);

CREATE INDEX idx_artifacts_run_id ON artifacts (run_id, stage);

-- approvals (gates ONLY: after_plan | before_publish; Architect G2)
CREATE TABLE approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    gate            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    decided_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    decision_note   TEXT,
    decided_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT approvals_gate_check CHECK (gate IN (
        'after_plan', 'before_publish'
    )),
    CONSTRAINT approvals_status_check CHECK (status IN (
        'pending', 'approved', 'rejected', 'cancelled'
    ))
);

CREATE INDEX idx_approvals_pending ON approvals (status, created_at)
    WHERE status = 'pending';
CREATE INDEX idx_approvals_run_id ON approvals (run_id, created_at DESC);
CREATE UNIQUE INDEX idx_approvals_one_pending_per_gate
    ON approvals (run_id, gate)
    WHERE status = 'pending';

-- audit_logs (append-only)
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       UUID,
    before          JSONB NOT NULL DEFAULT '{}'::jsonb,
    after           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_logs_entity ON audit_logs (entity_type, entity_id, created_at DESC);
CREATE INDEX idx_audit_logs_actor ON audit_logs (actor_user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs (action, created_at DESC);

-- memory_items
CREATE TABLE memory_items (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope        TEXT NOT NULL,
    scope_id     UUID,
    key          TEXT NOT NULL,
    content      TEXT NOT NULL,
    content_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    importance   SMALLINT NOT NULL DEFAULT 0,
    expires_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT memory_items_scope_check CHECK (scope IN ('global', 'user', 'task', 'agent')),
    CONSTRAINT memory_items_scope_key_unique UNIQUE (scope, scope_id, key)
);

CREATE INDEX idx_memory_items_scope ON memory_items (scope, scope_id);
CREATE INDEX idx_memory_items_expires ON memory_items (expires_at) WHERE expires_at IS NOT NULL;

-- reports
CREATE TABLE reports (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id               UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    task_id              UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title                TEXT NOT NULL,
    body_md              TEXT NOT NULL DEFAULT '',
    status               TEXT NOT NULL DEFAULT 'draft',
    publish_approval_id  UUID REFERENCES approvals(id) ON DELETE SET NULL,
    published_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    published_at         TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT reports_status_check CHECK (status IN ('draft', 'published')),
    CONSTRAINT reports_published_fields_check CHECK (
        (status = 'draft' AND published_at IS NULL AND publish_approval_id IS NULL)
        OR
        (status = 'published' AND published_at IS NOT NULL AND publish_approval_id IS NOT NULL AND published_by IS NOT NULL)
    )
);

CREATE INDEX idx_reports_task_id ON reports (task_id, created_at DESC);
CREATE INDEX idx_reports_run_id ON reports (run_id);
CREATE INDEX idx_reports_publish_approval ON reports (publish_approval_id)
    WHERE publish_approval_id IS NOT NULL;

-- App rule: set status=published only when approvals has
-- (run_id, gate=before_publish, status=approved); store that id in publish_approval_id.

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_agent_definitions_updated_at BEFORE UPDATE ON agent_definitions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_runs_updated_at BEFORE UPDATE ON runs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_approvals_updated_at BEFORE UPDATE ON approvals
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_memory_items_updated_at BEFORE UPDATE ON memory_items
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;

-- SEED NOTES (see also 002_seed.sql)
-- Admin demo (local MVP only):
--   email / email_norm: admin@godmode.local
--   display_name: GODMODE Admin
--   role: admin
--   password: from env GODMODE_ADMIN_PASSWORD or SEED_ADMIN_PASSWORD (hash at seed time)
--   NEVER commit a plaintext password.
-- AgentDefinition demos (slugs): planner, researcher, executor, verifier, reporter
-- Env vars: see repo .env.example (DATABASE_URL, REDIS_URL, GODMODE_ADMIN_*).
