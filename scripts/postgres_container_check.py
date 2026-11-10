"""Disposable real PostgreSQL in the managed Docker daemon, isolated from network."""
import json
import os
from pathlib import Path
import subprocess
import time
import uuid
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('PRAXIS_EVIDENCE_DIR',str(ROOT/'evidence/final')));OUT.mkdir(parents=True,exist_ok=True)
IMAGE=os.environ.get('PRAXIS_POSTGRES_IMAGE','postgres:17-alpine')
NAME='praxis-rls-'+uuid.uuid4().hex[:10]
DOCKER=['docker','--host=unix:///var/run/docker.sock']
result={'status':'running','scope':'real PostgreSQL; local auth.uid/JWT claim fixture, NOT hosted Supabase Auth','network':'none','checks':[]}
logs=[];started=False
# Explicit local daemon, preserving registry config but never selecting a remote context.
env={k:v for k,v in os.environ.items() if k not in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH')}
def run(args,input=None):
    p=subprocess.run(args,input=input,text=True,capture_output=True,env=env,timeout=180)
    logs.append('$ '+' '.join(args)+'\n'+p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(p.stderr[-2000:])
    return p.stdout
try:
    run(DOCKER+['run','--rm','-d','--name',NAME,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE]);started=True
    sql=DOCKER+['exec','-i',NAME,'psql','-X','-v','ON_ERROR_STOP=1','-U','postgres','-At']
    for _ in range(100):
        p=subprocess.run(DOCKER+['exec',NAME,'pg_isready','-U','postgres'],capture_output=True,env=env)
        logs_ready=subprocess.run(DOCKER+['logs',NAME],capture_output=True,text=True,env=env)
        if p.returncode==0 and 'PostgreSQL init process complete' in logs_ready.stdout:break
        time.sleep(.1)
    else:raise RuntimeError('Disposable PostgreSQL startup deadline')
    result['version']=run(sql,input='select version();').strip()
    result['image']=run(DOCKER+['image','inspect',IMAGE,'--format','{{index .RepoDigests 0}}']).strip()
    run(sql,input="""create role anon nologin; create role authenticated nologin;
create schema auth; create table auth.users(id uuid primary key,email text);
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth,public to authenticated,anon;""")
    schema=ROOT/'supabase/schema.sql';migration=ROOT/'supabase/migrations/20261103162347_praxis_schema.sql'
    assert schema.read_bytes()==migration.read_bytes(),'Schema and migration differ'
    run(sql,input=schema.read_text());result['checks'].append({'name':'tracked migration matches schema and applies to empty database','passed':True})
    for file in ('ownership.sql','persistence.sql'):
        run(sql,input=(ROOT/'supabase/tests'/file).read_text());result['checks'].append({'name':file,'passed':True})
    tables=int(run(sql,input="select count(*) from pg_tables where schemaname='public' and rowsecurity;").strip())
    assert tables==28,tables
    result['checks'].append({'name':'RLS enabled on all 28 tables','passed':True})
    result['status']='passed'
except Exception as e:
    result.update(status='failed',error=str(e));raise
finally:
    if started:
        run(DOCKER+['stop','--time','10',NAME]);result['server_stopped']=True
    (OUT/'postgres.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'postgres.log').write_text('\n'.join(logs))
    print(json.dumps(result,indent=2))
