-- Disposable database only. The transaction rolls back all synthetic data.
begin;
insert into auth.users(id,email) values
 ('10000000-0000-4000-8000-000000000001','alice@praxis.invalid'),
 ('10000000-0000-4000-8000-000000000002','bob@praxis.invalid');
set local role authenticated;
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
insert into model_revisions(id,user_id,name,kind,provider) values
 ('10000000-0000-4000-8000-000000000003',auth.uid(),'actual owner','model','openai');
insert into run_requests(id,user_id,target_id,suite_slug,suite_version,idempotency_key) values
 ('10000000-0000-4000-8000-000000000004',auth.uid(),'10000000-0000-4000-8000-000000000003','structured-agent','1.0.0','10000000-0000-4000-8000-000000000005');
insert into run_evidence(run_id,user_id,manifest_sha256,runner_version,tasks) values
 ('10000000-0000-4000-8000-000000000004',auth.uid(),repeat('a',64),'acceptance','[{"output":"persisted evidence"}]');
do $$begin
 if (select tasks->0->>'output' from run_evidence)<>'persisted evidence' then raise exception 'Evidence persistence failed';end if;
 begin
  insert into run_evidence(run_id,user_id,manifest_sha256,runner_version,tasks) values
  ('10000000-0000-4000-8000-000000000004',auth.uid(),repeat('a',64),'acceptance','[]');
  raise exception 'Duplicate manifest accepted';
 exception when unique_violation then null;end;
 begin
  update run_requests set trust='verified'; raise exception 'Trust modification accepted';
 exception when insufficient_privilege then null;end;
end$$;
select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000002',true);
do $$begin
 if exists(select 1 from run_requests) or exists(select 1 from run_evidence) then raise exception 'Foreign run/evidence leaked';end if;
 begin
  insert into votes(user_id,matchup_id,choice) values(auth.uid(),'10000000-0000-4000-8000-000000000099','a');
  raise exception 'Cloud client vote bypassed eligibility';
 exception when insufficient_privilege then null;end;
end$$;
reset role;
-- Verify database uniqueness independently of the denied client insertion path.
insert into artifacts(id,user_id,run_id,sha256,mime,size_bytes,object_key) values
 ('10000000-0000-4000-8000-000000000010','10000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000004',repeat('b',64),'text/plain',1,'a'),
 ('10000000-0000-4000-8000-000000000011','10000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000004',repeat('c',64),'text/plain',1,'b');
insert into matchups(id,user_id,artifact_a,artifact_b,condition_digest,eligible,expires_at) values
 ('10000000-0000-4000-8000-000000000012','10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000010','10000000-0000-4000-8000-000000000011',repeat('d',64),true,now()+interval '1 hour');
insert into votes(user_id,matchup_id,choice) values('10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000012','a');
do $$begin
 begin
  insert into votes(user_id,matchup_id,choice) values('10000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000012','b');
  raise exception 'Duplicate vote accepted';
 exception when unique_violation then null;end;
 if (select count(*) from votes)<>1 then raise exception 'Vote integrity failed';end if;
end$$;
rollback;
