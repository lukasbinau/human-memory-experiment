create extension if not exists pgcrypto;

create table if not exists sessions (
	id uuid primary key default gen_random_uuid(),
	participant_code text not null,
	protocol_version text not null,
	random_seed bigint not null,
	consent_given boolean not null default false,
	status text not null default 'started',
	started_at timestamptz not null default now(),
	completed_at timestamptz
);

create table if not exists trials (
	id uuid primary key default gen_random_uuid(),
	session_id uuid not null references sessions(id) on delete cascade,
	experiment_type text not null,
	experiment_part text not null,
	condition text not null,
	trial_number integer not null,
	presented_sequence jsonb not null,
	raw_response text,
	normalized_response text,
	score jsonb,
	timing jsonb,
	task_data jsonb,
	completed boolean not null default false,
	created_at timestamptz not null default now(),
	unique (session_id, trial_number)
);

alter table sessions enable row level security;
alter table trials enable row level security;
