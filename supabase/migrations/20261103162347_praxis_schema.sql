-- Reviewed schema source, not an applied migration. Generate a migration with the CLI.
-- No service-role key is used by the public Worker. All client tables default deny.
begin;
create extension if not exists pgcrypto;
create table public.organizations (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id),
 name text not null check(length(name) between 1 and 120), created_at timestamptz not null default now(), unique(id,user_id)
);
create table public.memberships (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id),
 organization_id uuid not null references public.organizations(id), role text not null check(role in ('owner','member','reviewer')),
 created_at timestamptz not null default now(), unique(organization_id,user_id)
);
create table public.projects (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id),
 organization_id uuid, name text not null, created_at timestamptz not null default now(), unique(id,user_id),
 foreign key(organization_id,user_id) references public.organizations(id,user_id)
);
create table public.provider_profiles (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id),
 name text not null, provider text not null, created_at timestamptz not null default now(),unique(id,user_id)
 -- Secrets intentionally excluded: credentials stay on the user's local runner.
);
create table public.model_revisions (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),
 name text not null check(length(name) between 1 and 120),kind text not null check(kind in ('model','agent','application')),
 provider text not null check(provider in ('demo','demo-failing','openai','ollama','custom')),
 endpoint text,model text not null default '',capabilities jsonb not null default '["text"]',
 created_at timestamptz not null default now(),unique(id,user_id)
);
create table public.suite_definitions (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),slug text not null,
 visibility text not null default 'private' check(visibility in ('public','private')),created_at timestamptz not null default now(),
 unique(id,user_id),unique(user_id,slug)
);
create table public.suite_versions (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),suite_id uuid not null,
 version text not null,digest text not null check(digest ~ '^[a-f0-9]{64}$'),definition jsonb not null,
 created_at timestamptz not null default now(),unique(id,user_id),unique(suite_id,version),
 foreign key(suite_id,user_id) references public.suite_definitions(id,user_id)
);
create table public.task_templates (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),suite_version_id uuid not null,
 definition jsonb not null,created_at timestamptz not null default now(),unique(id,user_id),
 foreign key(suite_version_id,user_id) references public.suite_versions(id,user_id)
);
create table public.world_specs (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),name text not null,
 seed integer not null,definition jsonb not null,created_at timestamptz not null default now(),unique(id,user_id)
);
create table public.world_snapshots (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),world_id uuid not null,
 step integer not null check(step>=0),state jsonb not null,digest text not null,
 created_at timestamptz not null default now(),unique(id,user_id),unique(world_id,step),
 foreign key(world_id,user_id) references public.world_specs(id,user_id)
);
create table public.world_transitions (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),world_id uuid not null,
 step integer not null,action jsonb not null,outcome jsonb not null,created_at timestamptz not null default now(),unique(id,user_id),
 foreign key(world_id,user_id) references public.world_specs(id,user_id)
);
create table public.run_requests (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),target_id uuid not null,
 suite_slug text not null,suite_version text not null,seed integer not null default 73,
 idempotency_key uuid not null,status text not null default 'queued' check(status in ('queued','running','completed','failed','cancelled')),
 trust text not null default 'self-reported' check(trust in ('demo','self-reported','verified')),
 created_at timestamptz not null default now(),unique(id,user_id),unique(user_id,idempotency_key),
 foreign key(target_id,user_id) references public.model_revisions(id,user_id)
);
create table public.run_evidence (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),run_id uuid not null,
 manifest_sha256 text not null check(manifest_sha256 ~ '^[a-f0-9]{64}$'),runner_version text not null,tasks jsonb not null,
 trust text not null default 'self-reported' check(trust in ('demo','self-reported','verified')),
 created_at timestamptz not null default now(),unique(id,user_id),unique(run_id,manifest_sha256),
 foreign key(run_id,user_id) references public.run_requests(id,user_id)
);
create table public.run_attempts (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),run_id uuid not null,
 attempt integer not null check(attempt>0),status text not null,created_at timestamptz not null default now(),unique(id,user_id),
 foreign key(run_id,user_id) references public.run_requests(id,user_id),unique(run_id,attempt)
);
create table public.task_instances (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),run_id uuid not null,
 task_key text not null,input jsonb not null,created_at timestamptz not null default now(),unique(id,user_id),
 foreign key(run_id,user_id) references public.run_requests(id,user_id),unique(run_id,task_key)
);
create table public.run_events (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),run_id uuid not null,
 sequence integer not null,event jsonb not null,created_at timestamptz not null default now(),unique(id,user_id),
 foreign key(run_id,user_id) references public.run_requests(id,user_id),unique(run_id,sequence)
);
create table public.artifacts (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),run_id uuid not null,
 sha256 text not null check(sha256 ~ '^[a-f0-9]{64}$'),mime text not null,size_bytes bigint not null check(size_bytes between 0 and 20971520),
 object_key text not null,consent_public boolean not null default false,created_at timestamptz not null default now(),unique(id,user_id),
 foreign key(run_id,user_id) references public.run_requests(id,user_id),unique(user_id,sha256)
);
create table public.assertions (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),run_id uuid not null,
 task_key text not null,name text not null,passed boolean not null,evidence jsonb not null,
 created_at timestamptz not null default now(),unique(id,user_id),foreign key(run_id,user_id) references public.run_requests(id,user_id)
);
create table public.scorecards (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),run_id uuid not null,
 metrics jsonb not null,created_at timestamptz not null default now(),unique(id,user_id),unique(run_id),
 foreign key(run_id,user_id) references public.run_requests(id,user_id)
);
-- These operator-owned records have SELECT policies only. They cannot be promoted or
-- mutated by users through PostgREST, including requests bypassing the Worker.
create table public.runner_registrations (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),
 name text not null,approved boolean not null default false,created_at timestamptz not null default now(),unique(id,user_id)
);
create table public.attestations (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),run_id uuid not null,
 runner_id uuid not null references public.runner_registrations(id),manifest_sha256 text not null,signature text not null,
 created_at timestamptz not null default now(),foreign key(run_id,user_id) references public.run_requests(id,user_id)
);
create table public.matchups (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),
 artifact_a uuid not null references public.artifacts(id),artifact_b uuid not null references public.artifacts(id),
 condition_digest text not null,eligible boolean not null default false,expires_at timestamptz not null,
 created_at timestamptz not null default now(),check(artifact_a<>artifact_b)
);
create table public.votes (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),matchup_id uuid not null references public.matchups(id),
 choice text not null check(choice in ('a','b','tie','both_bad')),rationale text,
 created_at timestamptz not null default now(),unique(user_id,matchup_id)
);
create table public.preference_ratings (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),target_id uuid not null references public.model_revisions(id),
 condition_digest text not null,rating double precision not null,sample_count integer not null check(sample_count>=0),
 created_at timestamptz not null default now(),unique(target_id,condition_digest)
);
create table public.rating_snapshots (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),ratings jsonb not null,
 created_at timestamptz not null default now()
);
create table public.quotas (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),resource text not null,
 maximum bigint not null check(maximum>=0),used bigint not null default 0 check(used>=0),
 created_at timestamptz not null default now(),unique(user_id,resource)
);
create table public.audit_events (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),action text not null,
 detail jsonb not null,created_at timestamptz not null default now()
);
create table public.moderation_actions (
 id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users(id),subject_id uuid not null,
 reason text not null,action text not null,created_at timestamptz not null default now()
);
-- Exact per-user isolation. Organization membership storage is present, but shared
-- organization mutation is intentionally not enabled until membership tests pass.
do $$ declare t text; begin
 for t in select tablename from pg_tables where schemaname='public' and tablename in
 ('organizations','memberships','projects','provider_profiles','model_revisions','suite_definitions','suite_versions','task_templates','world_specs','world_snapshots','world_transitions','run_requests','run_evidence','run_attempts','task_instances','run_events','artifacts','assertions','scorecards','runner_registrations','attestations','matchups','votes','preference_ratings','rating_snapshots','quotas','audit_events','moderation_actions') loop
 execute format('alter table public.%I enable row level security',t);
 execute format('revoke all on table public.%I from anon, authenticated',t);
 execute format('grant select on table public.%I to authenticated',t);
 execute format('create policy owner_read on public.%I for select to authenticated using ((select auth.uid())=user_id)',t);
 execute format('create index %I on public.%I (user_id,created_at desc)',t||'_owner_time',t);
 end loop;
 -- Metadata and evidence are append-only. No UPDATE grant means immutable revisions.
 foreach t in array array['organizations','projects','provider_profiles','model_revisions','suite_definitions','suite_versions','task_templates','world_specs','world_snapshots','world_transitions','run_attempts','task_instances','run_events','artifacts','assertions','scorecards'] loop
 execute format('grant insert on table public.%I to authenticated',t);
 execute format('create policy owner_insert on public.%I for insert to authenticated with check ((select auth.uid())=user_id)',t);
 end loop;
end $$;
grant insert on public.run_requests,public.run_evidence to authenticated;
create policy unverified_requests on public.run_requests for insert to authenticated with check ((select auth.uid())=user_id and trust='self-reported' and status='queued');
create policy unverified_evidence on public.run_evidence for insert to authenticated with check ((select auth.uid())=user_id and trust='self-reported');
-- Voting deliberately has no client INSERT grant: eligible matched pairing checks
-- need a transactional operator-owned function before cloud voting may be enabled.
commit;
