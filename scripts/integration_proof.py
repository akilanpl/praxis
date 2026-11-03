"""Execute persisted local infrastructure proof; no model inference is represented."""
import base64
import io
import json
import secrets
import time
import wave
from pathlib import Path
from praxis.server import ControlPlane, APIError
from praxis.cli import report_html
root=Path(__file__).resolve().parents[1]
folder=root/'evidence';folder.mkdir(exist_ok=True)
suffix=secrets.token_hex(4)
app=ControlPlane(root/'.praxis'/('proof-'+suffix+'.sqlite'))
def register(name): return app.request('POST','/api/auth/register',{'username':name+suffix,'password':secrets.token_urlsafe(24)},'')
owner=register('proof-owner-'); voter=register('proof-voter-')
def call(method,path,body=None,who=owner): return app.request(method,path,body or {},'Bearer '+who['token'])
proof={'mode':'in-process control-plane API with SQLite; HTTP transport/browser unverified','inference':'none; labeled deterministic fixture providers','runs':[]}
try:
 for provider,kind,suite in [('demo','model','structured-agent'),('demo-failing','model','structured-agent'),('demo','agent','agent-workflows')]:
  target=call('POST','/api/targets',{'name':provider+' '+kind,'kind':kind,'provider':provider})
  run=call('POST','/api/runs',{'target_id':target['id'],'suite_slug':suite,'seed':73,'public':kind=='model'})
  for _ in range(500):
   run=call('GET','/api/runs/'+run['id'])
   if run['status'] not in ('running','queued'): break
   time.sleep(.01)
  assert run['status']=='completed',run
  expected=0 if provider=='demo-failing' else run['result']['summary']['total']
  assert run['result']['summary']['passed']==expected
  proof['runs'].append({'id':run['id'],'provider':provider,'kind':kind,'suite':suite,'summary':run['result']['summary'],'evidence_hash':run['result']['evidence_hash']})
  filename='agent-run' if kind=='agent' else provider+'-run'
  (folder/(filename+'.json')).write_text(json.dumps(run,indent=2))
  (folder/(filename+'.html')).write_text(report_html(run['result']))
 world=call('POST','/api/worlds',{'domain':'support','name':'Proof support world','max_level':3,'seed':73})
 a=call('POST','/api/worlds/'+world['id']+'/replay');b=call('POST','/api/worlds/'+world['id']+'/replay')
 assert a==b;assert [x['entities'] for x in a['levels']]==[1,5,12]
 proof['world']={'replay_hash':a['replay_hash'],'entities':[x['entities'] for x in a['levels']],'identical_replay':True}
 (folder/'world-replay.json').write_text(json.dumps(a,indent=2))
 match=call('GET','/api/arena',who=voter);assert match.get('id')
 assert 'target_id' not in json.dumps(match)
 vote=call('POST','/api/arena/'+match['id']+'/vote',{'choice':'a'},voter)
 try:call('POST','/api/arena/'+match['id']+'/vote',{'choice':'a'},voter);raise AssertionError('duplicate accepted')
 except APIError as e:assert e.status==409
 board=call('GET','/api/leaderboards');assert not board['objective'];assert len(board['preference'])==2
 proof['arena']={'match':match,'vote':vote,'duplicate_vote_status':409,'official_objective_entries':0}
 wav=io.BytesIO()
 with wave.open(wav,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*8000)
 clip=call('POST','/api/artifacts',{'filename':'one-second-silence.wav','content_base64':base64.b64encode(wav.getvalue()).decode()})
 assert clip['duration_seconds']==1
 proof['media']={k:clip[k] for k in ('mime','duration_seconds','size','sha256')}
 proof['status']='passed'
 (folder/'integration-proof.json').write_text(json.dumps(proof,indent=2))
 print(json.dumps({'status':'passed','runs':len(proof['runs']),'world_levels':3,'vote_duplicate':409,'media_duration':1,'evidence':'evidence/integration-proof.json'}))
finally:app.pool.shutdown(wait=True)
