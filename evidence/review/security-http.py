"""Actual loopback HTTP security acceptance against a NEW disposable workspace."""
import base64
import json
from pathlib import Path
import tempfile
import threading
import time
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from praxis.server import ControlPlane,Handler
ROOT=Path(__file__).resolve().parents[2]
checks=[]
with tempfile.TemporaryDirectory(dir=ROOT/'work',prefix='security-http-') as folder:
 app=ControlPlane(Path(folder)/'db');server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.app=app;server.web_root=ROOT/'apps/web/dist';base=f'http://127.0.0.1:{server.server_port}';server.origins={base};thread=threading.Thread(target=server.serve_forever);thread.start()
 def request(method,path,body=None,token='',headers=None):
  req=urllib.request.Request(base+path,method=method,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+token,**(headers or {})})
  try:response=urllib.request.urlopen(req,timeout=5)
  except urllib.error.HTTPError as e:response=e
  with response:
   raw=response.read();data=json.loads(raw) if response.headers.get('Content-Type','').startswith('application/json') else raw.decode()
   return response.status,data,response.headers
 def check(name,condition):
  checks.append({'name':name,'passed':bool(condition)})
  if not condition:raise RuntimeError(name)
 try:
  code,body,headers=request('GET','/api/health');check('actual loopback health and CSP',code==200 and "frame-ancestors 'none'" in headers['Content-Security-Policy'])
  check('untrusted browser origin rejected',request('GET','/api/health',headers={'Origin':'https://evil.invalid'})[0]==403)
  check('rebinding Host rejected',request('GET','/api/health',headers={'Host':'evil.invalid'})[0]==403)
  check('unauthenticated records rejected',request('GET','/api/targets')[0]==401)
  a=request('POST','/api/auth/register',{'username':'security-owner','password':'synthetic-test-password'})[1]['token']
  b=request('POST','/api/auth/register',{'username':'security-other','password':'synthetic-test-password'})[1]['token']
  target=request('POST','/api/targets',{'name':'owned fixture','kind':'model','provider':'demo','trust':'verified'},a)[1]
  check('client trust metadata cannot escalate target','trust' not in target)
  check('foreign diagnostics denied',request('POST','/api/targets/'+target['id']+'/diagnostics',{},b)[0]==404)
  run=request('POST','/api/runs',{'target_id':target['id'],'suite_slug':'structured-agent','trust':'verified','idempotency_key':'security-owned-request'},a)[1]
  for _ in range(100):
   run=request('GET','/api/runs/'+run['id'],token=a)[1]
   if run['status']not in ('queued','running'):break
   time.sleep(.02)
  check('fixture provenance remains demo',run['status']=='completed' and run['result']['trust']=='demo')
  check('foreign run denied',request('GET','/api/runs/'+run['id'],token=b)[0]==404)
  upload=request('POST','/api/artifacts',{'filename':'inert.html','content_base64':base64.b64encode(b'<script>inert</script>').decode(),'public':True},a)[1]
  check('HTML upload is inert and private',upload['mime']=='text/plain' and upload['public'] is False and 'data_url' not in upload)
  check('other owner cannot list private artifacts',request('GET','/api/artifacts',token=b)[1]==[])
  check('revocation succeeds',request('POST','/api/auth/logout',{},a)[0]==200 and request('GET','/api/me',token=a)[0]==401)
  check('other account session unaffected',request('GET','/api/me',token=b)[0]==200)
 finally:server.shutdown();server.server_close();thread.join();app.pool.shutdown(wait=True)
result={'status':'PASS','scope':'Actual HTTP -> Handler -> SQLite on disposable loopback service; no public deployment or paid calls','checks':checks}
(ROOT/'evidence/review/security-http.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks)}))
