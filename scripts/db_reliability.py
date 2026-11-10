"""Actual PostgreSQL transaction/concurrency/restart checks on owned disposable DBs."""
import subprocess

def check_reliability(command,run,env,restart):
    owner='30000000-0000-4000-8000-000000000001'
    other='30000000-0000-4000-8000-000000000002'
    target='30000000-0000-4000-8000-000000000003'
    run(command,input=f"insert into auth.users(id,email) values ('{owner}','owner@fixture.invalid'),('{other}','other@fixture.invalid'); insert into model_revisions(id,user_id,name,kind,provider) values ('{target}','{owner}','owned reliability fixture','model','demo');")
    auth=f"set role authenticated;select set_config('request.jwt.claim.sub','{owner}',false);"
    insert=auth+f"insert into run_requests(user_id,target_id,suite_slug,suite_version,idempotency_key) values ('{owner}','{target}','structured-agent','1','30000000-0000-4000-8000-000000000004');"
    processes=[subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env) for _ in range(2)]
    # Send both requests before collecting either result: database uniqueness must arbitrate.
    for process in processes:process.stdin.write(insert);process.stdin.close();process.stdin=None
    outcomes=[process.communicate(timeout=30) for process in processes]
    if sorted(p.returncode for p in processes)!=[0,3] or not any('duplicate key' in err for _,err in outcomes):raise RuntimeError('Concurrent idempotency uniqueness failed')
    rollback="begin;insert into model_revisions(id,user_id,name,kind,provider) values ('30000000-0000-4000-8000-000000000005','"+owner+"','rollback fixture','model','demo');insert into model_revisions(id,user_id,name,kind,provider) values ('"+target+"','"+owner+"','duplicate','model','demo');commit;"
    failed=subprocess.run(command,input=rollback,text=True,capture_output=True,env=env,timeout=30)
    if failed.returncode==0:raise RuntimeError('Rollback failure was not rejected')
    count=run(command,input="select count(*) from model_revisions where id='30000000-0000-4000-8000-000000000005';").strip().splitlines()[-1]
    if count!='0':raise RuntimeError('Partial transaction persisted')
    foreign=run(command,input=f"set role authenticated;select set_config('request.jwt.claim.sub','{other}',false);select count(*) from run_requests;").strip().splitlines()[-1]
    if foreign!='0':raise RuntimeError('RLS leaked persisted run')
    restart()
    persisted=run(command,input=auth+"select count(*) from run_requests;").strip().splitlines()[-1]
    if persisted!='1':raise RuntimeError('Committed run lost across PostgreSQL restart')
    return [{'name':name,'passed':True} for name in ('concurrent request idempotency enforced by PostgreSQL uniqueness','failed transaction rolls back all partial writes','foreign role cannot read persisted run','committed data and owner policy survive database restart')]
