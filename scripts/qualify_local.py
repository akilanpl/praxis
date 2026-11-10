"""Disposable local-first lifecycle acceptance. Never reads an existing workspace."""
import argparse
import base64
import functools
import hashlib
from evidence_identity import source_identity
import http.server
import json
import os
from pathlib import Path
import platform
import secrets
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from backup_workspace import backup, restore, verify
from praxis.cli import report_html
from praxis.engine import digest

ROOT=Path(__file__).resolve().parents[1]

def require(condition,message):
    if not condition:raise RuntimeError(message)

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));return sock.getsockname()[1]

class Owned(http.server.BaseHTTPRequestHandler):
    requests=[]
    def log_message(self,*args):pass
    def reply(self,status,body):
        raw=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        self.requests.append(('GET',self.path));self.reply(200 if self.path=='/health' else 404,{'status':'ok'})
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        require(self.path=='/orders' and body=={'quantity':0},'Unexpected owned HTTP mutation')
        self.requests.append(('POST',self.path));self.reply(422,{'field':'quantity'})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--fixture-only',action='store_true');args=parser.parse_args()
    out=Path(args.output).resolve();require(not out.exists(),'Acceptance output must be a new directory');out.mkdir(parents=True,mode=0o700)
    result={'status':'FAIL','platform':platform.platform(),'python':platform.python_version(),'scope':'fresh disposable workspace, real HTTP and browser; no existing workspace access','mode':'explicit fixture inference' if args.fixture_only else 'real local CPU model inference','checks':[]}
    identity=source_identity()
    result.update({k:v for k,v in identity.items() if k!='source_files'})
    result['source_files']=[{'path':k,'sha256':v} for k,v in identity['source_files'].items()]
    processes=[];servers=[];logs=[];token='';base='';runs=[]
    def check(name,condition=True,**details):
        require(condition,name);result['checks'].append({'name':name,'status':'PASS',**details})
    def request(method,path,body=None,authorization=None):
        request=urllib.request.Request(base+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','Authorization':'Bearer '+(token if authorization is None else authorization)})
        with urllib.request.urlopen(request,timeout=120) as response:return json.load(response)
    def stop(process):
        if process.poll() is None:
            process.send_signal(signal.SIGINT) if os.name=='posix' else process.terminate()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait();raise RuntimeError('Shutdown deadline exceeded')
    def start(database):
        nonlocal base
        port=free_port();base='http://127.0.0.1:'+str(port)
        env=dict(os.environ,PRAXIS_DB=str(database),PRAXIS_PORT=str(port),PYTHONPATH=str(ROOT/'runner'))
        log=open(out/('server-'+str(port)+'.log'),'w');logs.append(log)
        proc=subprocess.Popen([sys.executable,'-m','praxis.server'],cwd=ROOT,env=env,stdout=log,stderr=log);processes.append(proc)
        for _ in range(100):
            require(proc.poll() is None,'Disposable server exited')
            try:
                if request('GET','/api/health')['ok']:return proc
            except OSError:time.sleep(.1)
        raise RuntimeError('Startup deadline exceeded')
    def execute(target,suite):
        body={'target_id':target['id'],'suite_slug':suite,'suite_version':'1.0.0','seed':73,'idempotency_key':secrets.token_hex(16)}
        run=request('POST','/api/runs',body);duplicate=request('POST','/api/runs',body);check('Duplicate run request returns same persisted run',run['id']==duplicate['id'])
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            run=request('GET','/api/runs/'+run['id'])
            if run['status'] not in ('queued','running'):break
            time.sleep(.5)
        check('Execution completes: '+suite,run['status']=='completed')
        data=run['result'];check('Evidence digest: '+suite,data['evidence_hash']==digest({k:v for k,v in data.items() if k!='evidence_hash'}))
        check('Assertions and execution events: '+suite,bool(run['events']) and all(t['assertions'] for t in data['tasks']))
        (out/(suite+'-'+str(len(runs))+'.json')).write_text(json.dumps(run,indent=2)+'\n')
        (out/(suite+'-'+str(len(runs))+'.html')).write_text(report_html(data))
        runs.append(run);return run
    try:
        result['node']=subprocess.check_output(['node','--version'],text=True).strip()
        app=start(out/'source workspace #1'/'praxis.sqlite')
        username='qualification-'+secrets.token_hex(4);password=secrets.token_urlsafe(24)
        account=request('POST','/api/auth/register',{'username':username,'password':password});token=account['token'];owner=account['user']['id']
        check('Account registration and ownership',request('GET','/api/me')['id']==owner)
        endpoint='';model='demo'
        if not args.fixture_only:
            port=free_port();model='onnx-community/SmolLM2-135M-Instruct-ONNX';endpoint='http://127.0.0.1:'+str(port)+'/v1'
            log=open(out/'cpu-model.log','w');logs.append(log)
            proc=subprocess.Popen(['node','scripts/local_model_server.mjs'],cwd=ROOT,env=dict(os.environ,PRAXIS_MODEL_PORT=str(port),PRAXIS_LOCAL_MODEL=model),stdout=log,stderr=log);processes.append(proc)
            deadline=time.monotonic()+180
            while time.monotonic()<deadline:
                require(proc.poll() is None,'Local CPU model exited')
                try:
                    with urllib.request.urlopen(endpoint.removesuffix('/v1')+'/health',timeout=2) as response:health=json.load(response)
                    if health.get('real_inference') and health.get('model')==model:break
                except OSError:time.sleep(.2)
            else:raise RuntimeError('CPU model startup deadline')
        target=request('POST','/api/targets',{'name':'CPU model' if endpoint else 'Explicit model fixture','kind':'model','provider':'openai' if endpoint else 'demo','endpoint':endpoint,'model':model,'max_tokens':128,'temperature':0,'timeout':30})
        model_run=execute(target,'structured-agent')
        if endpoint:check('Genuine inference metadata and usage',all(t['provider_metadata'].get('model')==model and t['usage']['completion_tokens']>0 and not t['error'] for t in model_run['result']['tasks']))
        result['model']={'name':model,'tasks':8,'passed':model_run['result']['summary']['passed'],'real_inference':bool(endpoint)}
        # A second condition-matched row verifies the comparison UI without inventing inference.
        comparison=request('POST','/api/targets',{'name':'Explicit comparison fixture','kind':'model','provider':'demo','max_tokens':128,'temperature':0,'timeout':30})
        comparison_run=execute(comparison,'structured-agent');check('Condition-matched comparison',model_run['conditions_hash']==comparison_run['conditions_hash'])
        agent=request('POST','/api/targets',{'name':'Explicit agent fixture','kind':'agent','provider':'demo'})
        agent_run=execute(agent,'agent-workflows');check('Agent execution traces and passing assertions',agent_run['result']['summary']['passed']==4 and any(t['tool_trace'] for t in agent_run['result']['tasks']))
        owned=http.server.ThreadingHTTPServer(('127.0.0.1',0),Owned);thread=threading.Thread(target=owned.serve_forever);thread.start();servers.append((owned,thread))
        application=request('POST','/api/targets',{'name':'Owned HTTP fixture','kind':'application','provider':'custom','endpoint':'http://127.0.0.1:'+str(owned.server_port),'authorized':True,'allow_mutation':True})
        app_run=execute(application,'http-application');check('Owned HTTP contracts execute actual requests',app_run['result']['summary']['passed']==4 and ('POST','/orders') in Owned.requests)
        artifact=request('POST','/api/artifacts',{'filename':'private evidence.txt','content_base64':base64.b64encode(b'local-first recovery evidence').decode()})
        check('Artifact byte hash',artifact['sha256']==hashlib.sha256(b'local-first recovery evidence').hexdigest())
        other=request('POST','/api/auth/register',{'username':'other-'+secrets.token_hex(4),'password':secrets.token_urlsafe(24)})
        try:request('GET','/api/runs/'+runs[0]['id'],authorization=other['token']);raise RuntimeError('Foreign owner read accepted')
        except urllib.error.HTTPError as error:check('Cross-owner run read rejected',error.code==404)
        from playwright.sync_api import sync_playwright,expect
        with sync_playwright() as p:
            browser=p.chromium.launch();context=browser.new_context();page=context.new_page()
            page.goto(base+'/settings');page.get_by_label('Account name').fill(username);page.get_by_label('Password').fill(password);page.get_by_label('Action').select_option('login');page.get_by_role('button',name='Continue',exact=True).click();page.wait_for_url('**/dashboard')
            page.goto(base+'/compare');expect(page.get_by_role('link',name='Explicit comparison fixture',exact=True)).to_be_visible();check('Browser comparison workflow')
            page.goto(base+'/artifacts');page.get_by_label('Search records').fill(artifact['id'])
            expect(page.get_by_text('local-first recovery evidence',exact=True)).to_be_visible();check('Uploaded artifact inspected through actual browser')
            page.goto(base+'/runs/'+agent_run['id']);expect(page.get_by_role('heading',name='Execution timeline')).to_be_visible()
            with page.expect_download() as download:page.get_by_role('button',name='Export evidence').click()
            download.value.save_as(str(out/'browser-export.json'));check('Browser JSON export',json.loads((out/'browser-export.json').read_text())['id']==agent_run['id'])
            for width in (390,768,1280):
                page.set_viewport_size({'width':width,'height':900});check('Report no overflow '+str(width),not page.evaluate('document.documentElement.scrollWidth>innerWidth'));page.screenshot(path=str(out/('report-'+str(width)+'.png')))
            context.close();browser.close()
        stop(app)
        database=out/'source workspace #1'/'praxis.sqlite'
        before=hashlib.sha256(database.read_bytes()).hexdigest()
        snapshot=out/'private backup';manifest=backup(database,snapshot);check('Complete backup verified',verify(snapshot)==manifest and artifact['sha256'] in manifest['objects'])
        restore(snapshot,out/'restored workspace #2');check('Backup leaves stopped source unchanged',hashlib.sha256(database.read_bytes()).hexdigest()==before)
        for restart in range(2):
            restored=start(out/'restored workspace #2'/'praxis.sqlite')
            check('Restored account session ownership '+str(restart),request('GET','/api/me')['id']==owner)
            restored_runs=request('GET','/api/runs');check('Restored runs and evidence '+str(restart),{r['id'] for r in restored_runs}=={r['id'] for r in runs} and all(r['result']['evidence_hash']==next(old['result']['evidence_hash'] for old in runs if old['id']==r['id']) for r in restored_runs))
            items=request('GET','/api/artifacts');check('Restored artifact records '+str(restart),any(i['sha256']==artifact['sha256'] for i in items))
            require(hashlib.sha256((out/'restored workspace #2'/'objects'/artifact['sha256']).read_bytes()).hexdigest()==artifact['sha256'],'Restored artifact bytes differ')
            stop(restored)
        check('Read-only restored inspections preserve source',hashlib.sha256(database.read_bytes()).hexdigest()==before)
        if os.name=='posix':check('Private workspace permissions',(database.stat().st_mode&0o777)==0o600 and (database.parent.stat().st_mode&0o777)==0o700)
        result['status']='PASS'
    except Exception as error:
        result['error_type']=type(error).__name__;result['error']=str(error)[:250];raise
    finally:
        for proc in reversed(processes):
            if proc.poll() is None:stop(proc)
        for server,thread in servers:server.shutdown();server.server_close();thread.join()
        for log in logs:log.close()
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))

if __name__=='__main__':main()
