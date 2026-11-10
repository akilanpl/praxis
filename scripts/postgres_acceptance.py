"""Disposable PostgreSQL migration/RLS acceptance. Never connects to an existing DB."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path(os.environ.get('PRAXIS_EVIDENCE_DIR',str(ROOT/'evidence/release')))
EVIDENCE.mkdir(parents=True, exist_ok=True)
work = ROOT / 'work'
work.mkdir(exist_ok=True)
folder = Path(tempfile.mkdtemp(prefix='postgres-acceptance-', dir=str(work)))
cluster = folder / 'data'
# Unix sockets must stay below macOS's 103-byte pathname limit.
socket = Path(tempfile.mkdtemp(prefix='praxis-pg-', dir='/private/tmp' if Path('/private/tmp').exists() else '/tmp'))
os.chmod(socket,0o700)
started = False
result = {'status':'running','production_access':False,'engine':'native PostgreSQL','auth_scope':'RLS with local auth.uid/JWT-claim compatibility fixture, not hosted Supabase Auth','checks':[]}
log = []
def run(args, **kwargs):
    p = subprocess.run(args,cwd=ROOT,capture_output=True,text=True,**kwargs)
    log.append('$ '+' '.join(str(a) for a in args)+'\n'+p.stdout+p.stderr)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-1600:])
    return p.stdout

def binary(name):
    path=shutil.which(name)
    if not path and shutil.which('pg_config'):
        candidate=Path(subprocess.check_output(['pg_config','--bindir'],text=True).strip())/name
        if candidate.is_file():path=str(candidate)
    if not path: raise RuntimeError('Required PostgreSQL binary unavailable: '+name)
    return path
try:
    initdb,pg_ctl,psql=[binary(x) for x in ('initdb','pg_ctl','psql')]
    result['version']=run([psql,'--version']).strip()
    run([initdb,'-D',str(cluster),'--auth-local=trust','--auth-host=scram-sha-256','--no-locale','-E','UTF8','-U','praxis_test'])
    run([pg_ctl,'-D',str(cluster),'-l',str(folder/'postgres.log'),'-o',"-k "+str(socket)+" -h '' -p 55439",'-w','start'])
    started=True
    base=[psql,'-X','-v','ON_ERROR_STOP=1','-h',str(socket),'-p','55439','-U','praxis_test','-d','postgres']
    def sql(text):return run(base+['-At'],input=text)
    sql('''create role anon nologin; create role authenticated nologin;
create schema auth;
create table auth.users(id uuid primary key, email text);
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth,public to authenticated,anon;
''')
    run(base+['-f',str(ROOT/'supabase/schema.sql')])
    result['checks'].append({'name':'schema applies to empty PostgreSQL database','passed':True})
    run(base+['-f',str(ROOT/'supabase/tests/ownership.sql')])
    result['checks'].append({'name':'ownership, trust forgery, foreign-parent and immutable grants regression','passed':True})
    tables=int(sql("select count(*) from pg_tables where schemaname='public' and rowsecurity").strip())
    assert tables==28,tables
    result['checks'].append({'name':'RLS enabled on every application table','passed':True,'tables':tables})
    run(base+['-f',str(ROOT/'supabase/tests/persistence.sql')])
    result['checks'].append({'name':'run/evidence persistence, duplicate votes and write denial','passed':True})
    result['status']='passed'
except Exception as exc:
    result.update(status='blocked' if 'Operation not permitted' in str(exc) or 'unavailable' in str(exc) else 'failed',error=str(exc))
finally:
    if started:
        try:run([pg_ctl,'-D',str(cluster),'-m','fast','-w','stop'])
        except Exception as exc:result['cleanup_error']=str(exc);result['status']='failed'
    if not started or 'cleanup_error' not in result: shutil.rmtree(socket)
    result['server_stopped']=not started or 'cleanup_error' not in result
    previous=EVIDENCE/'postgres.json'
    if previous.exists() and json.loads(previous.read_text()).get('status')=='passed':
        (EVIDENCE/'postgres-host-passed.json').write_text(previous.read_text())
    (EVIDENCE/'postgres.json').write_text(json.dumps(result,indent=2)+'\n')
    (EVIDENCE/'postgres.log').write_text('\n'.join(log))
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='passed' else 1)
