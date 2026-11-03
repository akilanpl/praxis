-- Run after schema.sql in a throwaway Supabase database, as postgres.
-- No production database should be used for authorization tests.
begin;
insert into auth.users(id,email) values
 ('00000000-0000-4000-8000-000000000001','owner@praxis.invalid'),
 ('00000000-0000-4000-8000-000000000002','other@praxis.invalid');
insert into public.model_revisions(id,user_id,name,kind,provider) values
 ('00000000-0000-4000-8000-000000000003','00000000-0000-4000-8000-000000000001','private','model','demo');
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000002',true);
do $$ begin
 if exists(select 1 from public.model_revisions) then raise exception 'RLS leaked another owner target';end if;
 begin
  insert into public.model_revisions(user_id,name,kind,provider) values ('00000000-0000-4000-8000-000000000001','forged','model','demo');
  raise exception 'Ownership forgery succeeded';
 exception when insufficient_privilege then null;end;
 begin
  insert into public.run_requests(user_id,target_id,suite_slug,suite_version,idempotency_key,trust) values
  ('00000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000003','test','1',gen_random_uuid(),'verified');
  raise exception 'Trust forgery succeeded';
 exception when insufficient_privilege then null;end;
 begin
  insert into public.run_requests(user_id,target_id,suite_slug,suite_version,idempotency_key) values
  ('00000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000003','test','1',gen_random_uuid());
  raise exception 'Cross-owner parent reference succeeded';
 exception when foreign_key_violation then null;end;
 if has_table_privilege('anon','public.model_revisions','SELECT') then raise exception 'Anonymous read grant remains';end if;
 if has_table_privilege('authenticated','public.run_requests','UPDATE') then raise exception 'User may promote immutable trust';end if;
 if has_table_privilege('authenticated','public.votes','INSERT') then raise exception 'Unreviewed cloud voting is writable';end if;
 if has_table_privilege('authenticated','public.runner_registrations','INSERT') then raise exception 'Runner approval is client writable';end if;
end $$;
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000001',true);
do $$ begin
 if (select count(*) from public.model_revisions)<>1 then raise exception 'Owner cannot read target';end if;
end $$;
rollback;
