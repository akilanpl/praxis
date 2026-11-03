"""Loopback-only local control plane. Inference stays on this user-owned runner."""
import base64
import concurrent.futures
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[2]
MAX_BODY = 2 * 1024 * 1024

class APIError(Exception):
    def __init__(self, status, message): self.status, self.message = status, message

def uid(): return str(uuid.uuid4())
def encoded(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
def digest(value): return hashlib.sha256(encoded(value).encode()).hexdigest()
def conditions(suite,target,seed):
    return digest({'suite':suite,'seed':seed,'target_kind':target.get('kind','model'),'max_tokens':target.get('max_tokens',1024),'temperature':target.get('temperature',0),'timeout':target.get('timeout',20)})

class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,kind TEXT NOT NULL,owner TEXT NOT NULL REFERENCES users(id),data TEXT NOT NULL,created REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS records_owner_kind ON records(owner,kind,created);
            CREATE TABLE IF NOT EXISTS votes(match_id TEXT NOT NULL,voter TEXT NOT NULL REFERENCES users(id),choice TEXT NOT NULL,created REAL NOT NULL,PRIMARY KEY(match_id,voter));
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT,action TEXT NOT NULL,subject TEXT,created REAL NOT NULL);
            ''')
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db
    def audit(self, actor, action, subject):
        with self.connect() as db: db.execute('INSERT INTO audit(actor,action,subject,created) VALUES(?,?,?,?)',(actor,action,subject,time.time()))
    def create(self, kind, owner, data):
        data = dict(data, id=data.get('id',uid()), created_at=time.time())
        with self.connect() as db: db.execute('INSERT INTO records VALUES(?,?,?,?,?)',(data['id'],kind,owner,encoded(data),data['created_at']))
        return data
    def update(self, item_id, data):
        with self.connect() as db: db.execute('UPDATE records SET data=? WHERE id=?',(encoded(data),item_id))
    def get(self, kind, item_id, owner=None):
        with self.connect() as db: row=db.execute('SELECT * FROM records WHERE id=? AND kind=?',(item_id,kind)).fetchone()
        if not row or (owner is not None and row['owner'] != owner): raise APIError(404,'Record not found')
        return json.loads(row['data'])
    def owner(self, item_id):
        with self.connect() as db: row=db.execute('SELECT owner FROM records WHERE id=?',(item_id,)).fetchone()
        return row['owner'] if row else None
    def all(self, kind, owner=None):
        with self.connect() as db:
            rows=db.execute('SELECT data FROM records WHERE kind=?'+(' AND owner=?' if owner else '')+' ORDER BY created DESC LIMIT 500', (kind,owner) if owner else (kind,)).fetchall()
        return [json.loads(r['data']) for r in rows]

class ControlPlane:
    def __init__(self, path):
        self.store=Store(path)
        self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.cancel={}
        self.auth_attempts=[]
        self.rate={}
        # Interrupted processes never leave a run pretending to be active.
        for run in self.store.all('run'):
            if run['status'] in ('queued','running'):
                run.update(status='interrupted',error='Runner restarted; launch a new attempt. Evidence already recorded is preserved.')
                self.store.update(run['id'],run)
    def auth(self, authorization):
        token=authorization.removeprefix('Bearer ') if hasattr(authorization,'removeprefix') else authorization[7:]
        with self.store.connect() as db: row=db.execute('SELECT user_id FROM sessions WHERE token=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()
        if not row: raise APIError(401,'Sign in to the local workspace')
        return row['user_id']
    def account(self, path, body):
        name=str(body.get('username','')).strip().lower(); password=body.get('password','')
        if not 3<=len(name)<=80 or not isinstance(password,str) or not 10<=len(password)<=256: raise APIError(400,'Use a username of 3–80 characters and a password of 10–256 characters')
        with self.store.connect() as db:
            if path.endswith('register'):
                salt=secrets.token_hex(16); user_id=uid()
                try: db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(user_id,name,salt,hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),240000).hex(),time.time()))
                except sqlite3.IntegrityError: raise APIError(409,'Username already exists')
            row=db.execute('SELECT * FROM users WHERE username=?',(name,)).fetchone()
            if not row or not hmac.compare_digest(row['password'],hashlib.pbkdf2_hmac('sha256',password.encode(),row['salt'].encode(),240000).hex()): raise APIError(401,'Invalid username or password')
            token=secrets.token_urlsafe(32)
            db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],time.time()+86400))
        return {'token':token,'user':{'id':row['id'],'username':name},'mode':'secure local'}
    def suites(self, user):
        from .engine import list_suites
        return list_suites()+self.store.all('suite',user)
    def execute(self, run, target, suite):
        from .engine import execute_run
        run.update(status='running'); self.store.update(run['id'],run)
        events=[]
        def event(e):
            events.append(dict(e) if isinstance(e,dict) else {'message':str(e)})
            run['events']=events[:2000]; self.store.update(run['id'],run)
        try:
            result=execute_run(target,suite,seed=run['seed'],on_event=event,cancelled=self.cancel[run['id']].is_set)
            result['trust']='demo' if target['provider'].startswith('demo') else 'self-reported'
            run.update(result=result,status='cancelled' if self.cancel[run['id']].is_set() else result.get('status','completed'),finished_at=time.time())
            for task in result.get('tasks',[]):
                content=task.get('output','')
                if not isinstance(content,str): content=encoded(content)
                self.store.create('artifact',self.store.owner(run['id']),{'run_id':run['id'],'task_id':task.get('id'), 'target_id':target['id'],'suite_slug':suite['slug'],'suite_version':suite['version'],'conditions':conditions(suite,target,run['seed']),'content':content,'mime':'application/json' if content.lstrip().startswith(('{','[')) else 'text/plain','sha256':hashlib.sha256(content.encode()).hexdigest(),'size':len(content.encode()),'trust':result['trust'],'public':run.get('public',False)})
        except Exception as exc:
            run.update(status='failed',error=type(exc).__name__+': '+str(exc)[:300],finished_at=time.time())
        self.store.update(run['id'],run)
    def matchup(self, user):
        # A persisted blind assignment is reused until voted; no self voting.
        for match in self.store.all('match',user):
            with self.store.connect() as db: voted=db.execute('SELECT 1 FROM votes WHERE match_id=? AND voter=?',(match['id'],user)).fetchone()
            if not voted: return self.blind(match)
        artifacts=[a for a in self.store.all('artifact') if a.get('public') and a.get('conditions') and self.store.owner(a['id'])!=user]
        import random
        random.SystemRandom().shuffle(artifacts)
        for a in artifacts:
            for b in artifacts:
                if a['target_id']==b['target_id'] or (a['task_id'],a['conditions'],a['mime'],a['trust']) != (b['task_id'],b['conditions'],b['mime'],b['trust']): continue
                pair=sorted([a['id'],b['id']])
                if any(sorted([m['a_id'],m['b_id']])==pair for m in self.store.all('match',user)): continue
                m=self.store.create('match',user,{'a_id':a['id'],'b_id':b['id'],'condition':{'task':a['task_id'],'suite':a['suite_slug'],'version':a['suite_version']},'demo':a['trust']=='demo'})
                return self.blind(m)
        return {'empty':True,'reason':'No eligible pair. Two other-owned, consented outputs must share the exact task, suite, seed and artifact type, and use different targets.'}
    def blind(self,m):
        return {'id':m['id'],'a':{k:self.store.get('artifact',m['a_id'])[k] for k in ('content','mime')},'b':{k:self.store.get('artifact',m['b_id'])[k] for k in ('content','mime')},'condition':m['condition'],'demo':m['demo']}
    def rankings(self):
        ratings={}; counts={}
        matches={m['id']:m for m in self.store.all('match')}
        with self.store.connect() as db: votes=db.execute('SELECT * FROM votes ORDER BY created').fetchall()
        for v in votes:
            m=matches.get(v['match_id'])
            if not m or v['choice']=='both_bad': continue
            a=self.store.get('artifact',m['a_id']); b=self.store.get('artifact',m['b_id'])
            # Ratings are scoped to conditions and trust; no universal rank.
            group=a['conditions']+':'+a['trust']
            ka=(group,a['target_id']); kb=(group,b['target_id'])
            ra=ratings.get(ka,1000.0); rb=ratings.get(kb,1000.0)
            score={'a':1,'b':0,'tie':.5}[v['choice']]; change=24*(score-1/(1+10**((rb-ra)/400)))
            ratings[ka]=ra+change; ratings[kb]=rb-change
            counts[ka]=counts.get(ka,0)+1; counts[kb]=counts.get(kb,0)+1
        preference=[]
        for key,rating in ratings.items():
            t=self.store.get('target',key[1]); n=counts[key]
            preference.append({'target_id':t['id'],'name':t['name'],'rating':round(rating,2),'votes':n,'sample_size':n,'group':key[0],'trust':key[0].split(':')[-1],'status':'insufficient evidence' if n<20 else 'community preference; non official','uncertainty':'Not a confidence interval; sparse Elo ratings are descriptive only'})
        return {'objective':[],'preference':sorted(preference,key=lambda r:-r['rating']),'note':'No operator-controlled trusted runners are configured. Local and demo runs never enter official objective rankings.'}
    def request(self, method, path, body, authorization):
        if (method=='POST' and path=='/api/runs') or (method=='GET' and path=='/api/arena'):
            with self.store.lock: return self._request(method,path,body,authorization)
        return self._request(method,path,body,authorization)
    def _request(self, method, path, body, authorization):
        parts=path.strip('/').split('/')
        if method=='GET' and path=='/api/health': return {'ok':True,'mode':'secure local','inference':'user-owned runner','version':'0.1.0'}
        if path in ('/api/auth/register','/api/auth/login') and method=='POST':
            with self.store.lock:
                now=time.monotonic(); self.auth_attempts=[t for t in self.auth_attempts if now-t<60]
                if len(self.auth_attempts)>=30: raise APIError(429,'Authentication rate exceeded; retry in a minute')
                self.auth_attempts.append(now)
                return self.account(path,body)
        user=self.auth(authorization)
        now=time.monotonic(); recent=[t for t in self.rate.get(user,[]) if now-t<60]
        if len(recent)>=180: raise APIError(429,'Local request quota exceeded. Retry in one minute.')
        self.rate[user]=recent+[now]
        if path=='/api/me':
            with self.store.connect() as db: r=db.execute('SELECT id,username FROM users WHERE id=?',(user,)).fetchone()
            return dict(r)
        if path=='/api/auth/logout' and method=='POST':
            with self.store.connect() as db: db.execute('DELETE FROM sessions WHERE user_id=?',(user,))
            return {'ok':True}
        if path=='/api/dashboard':
            runs=self.store.all('run',user)
            return {'runs':len(runs),'targets':len(self.store.all('target',user)),'artifacts':len(self.store.all('artifact',user)),'failures':sum(r['status']=='failed' for r in runs),'recent_runs':runs[:8],'spend':None,'mode':'secure local'}
        if path=='/api/targets':
            if method=='GET': return self.store.all('target',user)
            if method=='POST':
                if any(k.lower() in ('key','api_key','token','password','secret') for k in body): raise APIError(400,'Keep credentials in runner environment variables, never registry metadata')
                if body.get('kind') not in ('model','agent','application') or body.get('provider') not in ('demo','demo-failing','openai','ollama','custom'): raise APIError(400,'Unsupported target kind or provider')
                if not str(body.get('name','')).strip(): raise APIError(400,'Target name is required')
                endpoint=body.get('endpoint','')
                if endpoint:
                    p=urlparse(endpoint)
                    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or p.query or p.fragment: raise APIError(400,'Endpoint must be HTTP(S) without embedded credentials or query parameters')
                allowed={k:body[k] for k in ('name','kind','provider','endpoint','model','capabilities','max_tokens','temperature','timeout','allow_mutation') if k in body}
                target=self.store.create('target',user,dict(allowed,revision=1,config_hash=digest(allowed)))
                self.store.audit(user,'target.create',target['id']); return target
        if len(parts)==4 and parts[1]=='targets' and parts[3]=='diagnostics' and method=='POST':
            target=self.store.get('target',parts[2],user)
            from .adapters import diagnose
            return diagnose(target)
        if path=='/api/suites':
            if method=='GET': return self.suites(user)
            if method=='POST':
                from .engine import validate_suite
                try:
                    validation=validate_suite(body)
                    if not validation["valid"]: raise ValueError("; ".join(validation["errors"]))
                except Exception as exc: raise APIError(400,str(exc)[:500])
                if any(s['slug']==body['slug'] and s['version']==body['version'] for s in self.suites(user)): raise APIError(409,'Suite slug and version already exist. Create a new version.')
                return self.store.create('suite',user,body)
        if len(parts)==3 and parts[1]=='suites' and method=='GET':
            suite=next((s for s in self.suites(user) if s['slug']==parts[2]),None)
            if not suite: raise APIError(404,'Suite not found')
            return suite
        if path=='/api/runs':
            if method=='GET': return self.store.all('run',user)
            if method=='POST':
                with self.store.lock:
                    if body.get('idempotency_key'):
                        for existing in self.store.all('run',user):
                            if existing.get('idempotency_key')==body['idempotency_key']: return existing
                target=self.store.get('target',body.get('target_id',''),user)
                suites=[s for s in self.suites(user) if s['slug']==body.get('suite_slug') and (not body.get('suite_version') or s['version']==body['suite_version'])]
                if not suites: raise APIError(400,'Suite not found')
                if target['kind']=='application' and suites[0]['slug']!='http-application' and not all(t.get('api_request') for t in suites[0].get('tasks',[])): raise APIError(422,'Application targets require an HTTP contract suite or the isolated artifact checker')
                if sum(r['status'] in ('queued','running') for r in self.store.all('run',user))>=2: raise APIError(429,'At most two active runs per account')
                seed=body.get('seed',73)
                if not isinstance(seed,int) or abs(seed)>2**31: raise APIError(400,'Seed must be a 32 bit integer')
                run=self.store.create('run',user,{'target_id':target['id'],'target_name':target['name'],'suite_slug':suites[0]['slug'],'suite_version':suites[0]['version'],'suite_hash':digest(suites[0]),'config_hash':target['config_hash'],'conditions_hash':conditions(suites[0],target,seed),'seed':seed,'status':'queued','trust':'demo' if target['provider'].startswith('demo') else 'self-reported','public':body.get('public') is True,'idempotency_key':str(body.get('idempotency_key',''))[:100],'events':[]})
                self.cancel[run['id']]=threading.Event(); self.pool.submit(self.execute,run,target,suites[0]); self.store.audit(user,'run.create',run['id']); return run
        if len(parts)>=3 and parts[1]=='runs':
            run=self.store.get('run',parts[2],user)
            if method=='GET': return run
            if method=='POST' and len(parts)==4 and parts[3]=='cancel':
                if run['status'] not in ('queued','running'): raise APIError(409,'Run already finished')
                self.cancel[run['id']].set(); return {'ok':True,'status':'cancellation requested'}
        if path=='/api/worlds':
            if method=='GET': return self.store.all('world',user)
            if method=='POST':
                level=body.get('max_level',3)
                if not isinstance(level,int) or not 1<=level<=5: raise APIError(400,'World max_level must be 1–5')
                return self.store.create('world',user,{'name':str(body.get('name','Support operations'))[:100],'domain':'customer-support' if body.get('domain','support')=='support' else body.get('domain'),'max_level':level,'seed':body.get('seed',73)})
        if len(parts)>=3 and parts[1]=='worlds':
            world=self.store.get('world',parts[2],user)
            if method=='GET': return world
            if method=='POST' and len(parts)==4 and parts[3]=='replay':
                from .worlds import run_world
                replay=run_world({k:world[k] for k in ('domain','max_level','seed')},seed=world['seed'])
                world['replay']=replay; self.store.update(world['id'],world); return replay
        if path=='/api/artifacts' and method=='GET': return self.store.all('artifact',user)
        if path=='/api/artifacts' and method=='POST':
            from .media import ingest
            return ingest(self.store,user,body)
        if path=='/api/artifacts/check-website' and method=='POST':
            from .artifact_checks import check_owned_website
            from .media import ingest
            folder=Path(self.store.path).parent/'website-checks'/uid()
            proof=check_owned_website(folder)
            artifacts=[]
            for filename in ('website-390.png','website-1280.png','website.html','website-checks.json'):
                item=ingest(self.store,user,{'filename':filename,'content_base64':base64.b64encode((folder/filename).read_bytes()).decode()})
                item.update(trust='demo',fixture='Source-controlled owned website; not generated model output')
                self.store.update(item['id'],item); artifacts.append(item)
            return {'checks':proof,'artifacts':artifacts}

        if path=='/api/arena' and method=='GET':
            with self.store.lock: return self.matchup(user)
        if len(parts)==4 and parts[1]=='arena' and parts[3]=='vote' and method=='POST':
            m=self.store.get('match',parts[2],user); choice=body.get('choice')
            if choice not in ('a','b','tie','both_bad'): raise APIError(400,'Vote must be a, b, tie or both_bad')
            for k in ('a_id','b_id'):
                if self.store.owner(m[k])==user: raise APIError(403,'Self voting is prohibited')
            try:
                with self.store.connect() as db: db.execute('INSERT INTO votes VALUES(?,?,?,?)',(m['id'],user,choice,time.time()))
            except sqlite3.IntegrityError: raise APIError(409,'This matchup already has your vote')
            a=self.store.get('artifact',m['a_id']); b=self.store.get('artifact',m['b_id'])
            self.store.audit(user,'arena.vote',m['id'])
            return {'choice':choice,'a':self.store.get('target',a['target_id'])['name'],'b':self.store.get('target',b['target_id'])['name'],'ratings':self.rankings()['preference'],'demo':m['demo']}
        if path=='/api/leaderboards' and method=='GET': return self.rankings()
        if path=='/api/admin' and method=='GET': return {'trusted_runners':[],'mode':'local','message':'No hosted operator privileges. Trusted runner enrollment requires a reviewed deployment policy.'}
        raise APIError(404,'API route not found')

class Handler(BaseHTTPRequestHandler):
    server_version='Praxis/0.1'
    def log_message(self, fmt,*args): pass  # Never log credentials or request bodies.
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def do_OPTIONS(self): self.handle_request()
    def handle_request(self):
        request_id=uid(); status=200
        try:
            host=self.headers.get('Host','').split(':')[0]
            if host not in ('localhost','127.0.0.1'): raise APIError(403,'Local API accepts loopback hosts only')
            origin=self.headers.get('Origin')
            if origin and origin not in self.server.origins: raise APIError(403,'Origin denied')
            if self.command=='OPTIONS': data={'ok':True}
            else:
                length=int(self.headers.get('Content-Length','0'))
                if length<0 or length>MAX_BODY: raise APIError(413,'Request exceeds 2 MB limit')
                body={}
                if length:
                    if 'application/json' not in self.headers.get('Content-Type',''): raise APIError(415,'Expected application/json')
                    try: body=json.loads(self.rfile.read(length))
                    except (ValueError,UnicodeDecodeError): raise APIError(400,'Invalid JSON')
                    if not isinstance(body,dict): raise APIError(400,'JSON object required')
                path=urlparse(self.path).path
                if not path.startswith('/api/'):
                    static=self.server.web_root
                    rel=path.lstrip('/') or 'index.html'
                    file=(static/rel).resolve()
                    if not file.is_relative_to(static.resolve()): raise APIError(403,'Invalid path')
                    if not file.is_file(): file=static/'index.html'
                    if not file.is_file(): raise APIError(503,'Web build missing. Run npm run build --workspace apps/web')
                    import mimetypes
                    raw=file.read_bytes(); self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(str(file))[0] or 'application/octet-stream'); self.send_header('Content-Length',str(len(raw))); self.security_headers(); self.end_headers(); self.wfile.write(raw); return
                data=self.server.app.request(self.command,path,body,self.headers.get('Authorization',''))
        except APIError as e: status=e.status; data={'error':e.message,'request_id':request_id}
        except Exception: status=500; data={'error':'Internal local runner error; inspect local tests or logs','request_id':request_id}
        raw=encoded(data).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.send_header('X-Request-ID',request_id)
        if self.headers.get('Origin') in self.server.origins:
            self.send_header('Access-Control-Allow-Origin',self.headers['Origin']); self.send_header('Vary','Origin'); self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type'); self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.security_headers(); self.end_headers(); self.wfile.write(raw)
    def security_headers(self):
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','no-referrer'); self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' data:; font-src 'self'; connect-src 'self' http://localhost:8787 http://127.0.0.1:8787; frame-src 'none'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")

def serve(path=None,port=8787):
    db=path or (os.environ.get('PRAXIS_DB') or str(ROOT/'.praxis'/'praxis.sqlite'))
    app=ControlPlane(db); server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.app=app; server.web_root=ROOT/'apps'/'web'/'dist'; server.origins={f'http://localhost:{port}',f'http://127.0.0.1:{port}','http://localhost:5173','http://127.0.0.1:5173'}
    print(f'Praxis secure local workspace: http://127.0.0.1:{port}',flush=True)
    try: server.serve_forever()
    finally: app.pool.shutdown(wait=True); server.server_close()

if __name__=='__main__': serve()
