"""Real inference against an explicitly user-owned loopback endpoint, no mocks."""
import json
import os
from pathlib import Path
import secrets
import time
import urllib.request
from urllib.parse import urlparse
from praxis.cli import report_html
ROOT=Path(__file__).resolve().parents[1]
FOLDER=Path(os.environ.get('PRAXIS_EVIDENCE_DIR',str(ROOT/'evidence/release')));FOLDER.mkdir(parents=True,exist_ok=True)
BASE=os.environ.get('PRAXIS_ACCEPTANCE_URL','http://127.0.0.1:8787')
ENDPOINT=os.environ.get('PRAXIS_INFERENCE_ENDPOINT','http://127.0.0.1:8788/v1')
MODEL=os.environ.get('PRAXIS_INFERENCE_MODEL','onnx-community/SmolLM2-135M-Instruct-ONNX')
for url in (BASE,ENDPOINT):
 if urlparse(url).hostname not in ('127.0.0.1','localhost') or urlparse(url).scheme!='http':raise SystemExit('Acceptance mutates only explicit loopback test services')
token=''
def call(method,path,body=None):
 request=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
 with urllib.request.urlopen(request,timeout=120) as response:return json.load(response)
account=call('POST','/api/auth/register',{'username':'real-inference-'+secrets.token_hex(4),'password':secrets.token_urlsafe(24)})
token=account['token']
target=call('POST','/api/targets',{'name':MODEL+' CPU q4','kind':'model','provider':'openai','endpoint':ENDPOINT,'model':MODEL,'max_tokens':128,'timeout':30,'temperature':0,'capabilities':['text','json']})
diagnostic=call('POST','/api/targets/'+target['id']+'/diagnostics',{})
assert diagnostic['ok'] and not diagnostic['demo'],diagnostic
run=call('POST','/api/runs',{'target_id':target['id'],'suite_slug':'structured-agent','suite_version':'1.0.0','seed':73,'idempotency_key':secrets.token_hex(16)})
deadline=time.monotonic()+180
while time.monotonic()<deadline:
 run=call('GET','/api/runs/'+run['id'])
 if run['status'] not in ('queued','running'):break
 time.sleep(.3)
assert run['status']=='completed',run
assert run['trust']=='self-reported' and run['result']['trust']=='self-reported'
rows=run['result']['tasks']
assert len(rows)==8
assert all(row['output'] and row['latency_ms']>0 and not row['error'] for row in rows),rows
assert all(row['usage']['completion_tokens']>0 for row in rows)
assert all(row.get('provider_metadata',{}).get('model')==MODEL for row in rows)
name='real-'+MODEL.split('/')[-1]
(FOLDER/(name+'.json')).write_text(json.dumps({k:v for k,v in run.items() if k!='idempotency_key'},indent=2)+'\n')
(FOLDER/(name+'.html')).write_text(report_html(run['result']))
result={'status':'passed','acceptance':'real HTTP model invocation, persisted raw outputs, per-assertion grading and usage; no score threshold assumed','model':MODEL,'run_id':run['id'],'url':BASE+'/runs/'+run['id'],'tasks':len(rows),'benchmark_passed':run['result']['summary']['passed'],'benchmark_total':8,'cost':'local CPU; no paid model API used','trust':'self-reported','evidence_hash':run['result']['evidence_hash']}
(FOLDER/(name+'-acceptance.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
