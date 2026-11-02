-- GODMODE runtime schema, generated from apps/api/app/models.py. This is what the running API uses.
-- The API applies it automatically at startup (idempotent create_all).
CREATE TABLE IF NOT EXISTS agents (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	role VARCHAR(100) NOT NULL, 
	description TEXT NOT NULL, 
	tools JSON NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
	id SERIAL NOT NULL, 
	actor VARCHAR(255) NOT NULL, 
	action VARCHAR(100) NOT NULL, 
	entity VARCHAR(100) NOT NULL, 
	entity_id INTEGER, 
	detail JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS roles (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	permissions JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS users (
	id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(role) REFERENCES roles (name)
);

CREATE TABLE IF NOT EXISTS tasks (
	id SERIAL NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	prompt TEXT NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	requires_approval INTEGER NOT NULL, 
	created_by INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS memories (
	id SERIAL NOT NULL, 
	scope VARCHAR(100) NOT NULL, 
	key VARCHAR(255) NOT NULL, 
	content TEXT NOT NULL, 
	task_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);

CREATE TABLE IF NOT EXISTS plans (
	id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	summary TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);

CREATE TABLE IF NOT EXISTS reports (
	id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	body TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);

CREATE TABLE IF NOT EXISTS runs (
	id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	current_stage VARCHAR(30), 
	mock_llm INTEGER NOT NULL, 
	error_summary TEXT NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);

CREATE TABLE IF NOT EXISTS approvals (
	id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	run_id INTEGER, 
	gate VARCHAR(50) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	reason TEXT NOT NULL, 
	decided_by INTEGER, 
	decided_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id), 
	FOREIGN KEY(run_id) REFERENCES runs (id), 
	FOREIGN KEY(decided_by) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS stage_events (
	id SERIAL NOT NULL, 
	run_id INTEGER NOT NULL, 
	stage VARCHAR(30) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	detail JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(run_id) REFERENCES runs (id)
);

CREATE TABLE IF NOT EXISTS steps (
	id SERIAL NOT NULL, 
	plan_id INTEGER NOT NULL, 
	position INTEGER NOT NULL, 
	phase VARCHAR(30) NOT NULL, 
	agent_name VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	output TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(plan_id) REFERENCES plans (id)
);

