"""Meaningful positive/negative decisions at local evaluation boundaries."""
import base64
import copy
import io
import json
import math
import os
import struct
import subprocess
import sys
import threading
import time
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from praxis import adapters
from praxis.adapters import AdapterError,invoke,diagnose,read_bounded
from praxis.application import invoke_application
from praxis.agent import invoke_agent
from praxis.engine import execute_run,grade,list_suites,validate_suite
from praxis.server import ControlPlane,Store,APIError,Handler
from praxis.media import ingest
from praxis.artifact_checks import inspect_artifact,check_owned_website
from praxis.worlds import run_world
from test_http_boundary import SocketBuffer

def sample(slug='structured-agent'):return copy.deepcopy(next(s for s in list_suites() if s['slug']==slug))

@pytest.mark.parametrize('op,actual,expected,passed',[
 ('equals',1,1,True),('equals',True,1,False),('contains',[1,2],1,True),('contains','abc','z',False),('not_contains','abc','z',True),('not_contains',[1],1,False),('subset',[1,2],[2],True),('subset',[1],[2],False),('gte',3,2,True),('gte',True,1,False),('lte',2,3,True),('lte',4,3,False),('contains',None,'a',False)])
def test_assertion_operator_decisions(op,actual,expected,passed):
 checks=grade({'assertions':[{'path':'nested.0','op':op,'expected':expected}]},{'nested':[actual]})
 assert checks[1]['passed']==passed
 assert grade({'assertions':[{'path':'nested.8','op':op,'expected':expected}]},{'nested':[actual]})[1]['passed'] is False

@pytest.mark.parametrize('mutate',[
 lambda s:s.update(title=''),lambda s:s.update(slug='BAD'),lambda s:s.update(version='bad/path'),lambda s:s.update(tasks='not an array'),lambda s:s.update(tasks=[False]),lambda s:s['tasks'][0].update(id=s['tasks'][1]['id']),lambda s:s['tasks'][0].update(prompt=''),lambda s:s['tasks'][0].update(max_steps=True),lambda s:s['tasks'][0].update(allowed_tools='refund'),lambda s:s['tasks'][0].update(environment=[]),lambda s:s['tasks'][0].update(output_schema={'type':'invalid'}),lambda s:s['tasks'][0].update(assertions='none'),lambda s:s['tasks'][0].update(assertions=[]),lambda s:s['tasks'][0].update(assertions=[{'op':'equals','path':'x','expected':0,'weight':math.inf}]),lambda s:s.update(execution=[]),lambda s:s.update(execution={'max_wall_seconds':0})])
def test_invalid_suite_decisions(mutate):
 s=sample();mutate(s);assert not validate_suite(s)['valid']
 assert not validate_suite(None)['valid']

@pytest.mark.parametrize('response,expected',[(b'\xff','invalid_response'),(b'NaN','invalid_response'),(b'{}','invalid_response')])
def test_custom_invalid_wire_output(response,expected):
 with patch('praxis.adapters.urllib.request.OpenerDirector.open',return_value=io.BytesIO(response)):
  with pytest.raises(AdapterError) as e:invoke({'provider':'custom','endpoint':'http://localhost','model':'owned'}, {'prompt':'test'})
 assert e.value.category==expected

@pytest.mark.parametrize('provider,response',[
 ('openai',{}),('ollama',{}),('ollama',{'message':{'content':'{}'},'eval_count':-1}),('ollama',{'message':{'content':'{}'},'eval_count':True})])
def test_provider_missing_or_invalid_usage(provider,response):
 with patch('praxis.adapters.urllib.request.OpenerDirector.open',return_value=io.BytesIO(json.dumps(response).encode())):
  with pytest.raises(AdapterError) as e:invoke({'provider':provider,'endpoint':'http://localhost','model':'owned'},{'prompt':'test'})
 assert e.value.category=='invalid_response'

@pytest.mark.parametrize('error,category',[(urllib.error.URLError(TimeoutError()),'timeout'),(urllib.error.URLError('offline'),'connection_error'),(OSError('unavailable'),'connection_error')])
def test_provider_transport_errors_are_safe(error,category):
 with patch('praxis.adapters.urllib.request.OpenerDirector.open',side_effect=error):
  r=diagnose({'provider':'custom','endpoint':'http://localhost','model':'owned'})
 assert r['category']==category and 'unavailable' not in r['error']


def test_response_byte_limit_and_expired_deadline():
 with pytest.raises(AdapterError) as e:read_bounded(io.BytesIO(b'x'*(adapters.MAX_RESPONSE_BYTES+1)),time.monotonic()+2)
 assert e.value.category=='response_limit'
 with pytest.raises(AdapterError) as e:read_bounded(io.BytesIO(b'{}'),time.monotonic()-1)
 assert e.value.category=='timeout'


def test_retry_failure_and_numeric_configuration_recorded():
 s=sample();s['tasks']=s['tasks'][:1];s['execution']['max_retries']=2
 with patch('praxis.engine.invoke',side_effect=[AdapterError('timeout','bounded timeout'),{'output':s['tasks'][0]['passing_fixture']}]) as call:
  r=execute_run({'provider':'custom'},s)
 assert call.call_count==2 and r['tasks'][0]['attempts']==2
 with patch('praxis.engine.invoke',side_effect=ValueError('secret numeric detail')):
  r=execute_run({'provider':'custom'},s)
 assert r['tasks'][0]['error']['category']=='configuration' and 'secret numeric detail' not in json.dumps(r)


def test_wall_budget_before_first_task_and_between_attempts():
 s=sample();s['execution']['max_wall_seconds']=1
 with patch('praxis.engine.time.monotonic',side_effect=[0,0,2,2,2,2]):r=execute_run({'provider':'demo'},s)
 assert r['status']=='budget_exceeded' and r['summary']['not_run']==8

@pytest.mark.parametrize('actions',[
 [{'tool':'refund','arguments':{'id':'P1'}},{'final':{'status':'done'}}],
 [{'tool':'lookup_policy'},{'tool':'lookup_purchase','arguments':{'id':'P1'}},{'tool':'refund','arguments':{'id':'P1'}},{'tool':'refund','arguments':{'id':'P1'}},{'final':{'status':'done'}}],
 [{'tool':'lookup_policy'},{'tool':'lookup_purchase','arguments':{'id':'P1'}},{'tool':'refund','arguments':{'id':'P1'}},{'final':{'status':'done'}}],
 [{'tool':'refund','arguments':[]},{'tool':'lookup_purchase','arguments':{'id':[]}},{'final':{'status':'done'}}],
])
def test_agent_tool_observations_and_policy_decisions(actions):
 t=sample('agent-workflows')['tasks'][0];t['demo_actions']=actions
 if len(actions)==4:t['environment']['purchases']['P1']['amount']=100
 r=invoke_agent({'provider':'demo'},t)
 observations=[e.get('observation',{}) for e in r['tool_trace']]
 assert observations
 assert all(e['state_before']==e['state_after'] for e in r['tool_trace'] if e.get('observation',{}).get('error') in ('invalid_arguments','missing_authorization_evidence','policy_denied','purchase_not_found'))

@pytest.mark.parametrize('output',['not JSON',[],{'final':None},{'final':{},'tool':'refund'}])
def test_agent_invalid_model_actions_fail_with_prior_trace(output):
 t=sample('agent-workflows')['tasks'][0]
 with patch('praxis.agent.invoke',return_value={'output':output}):
  with pytest.raises(AdapterError) as e:invoke_agent({'provider':'custom'},t)
 assert e.value.category=='invalid_agent_action' and hasattr(e.value,'evidence')


def test_agent_timeout_preserves_trace():
 with patch('praxis.agent.time.monotonic',side_effect=[0,2]):
  with pytest.raises(AdapterError) as e:invoke_agent({'provider':'demo','timeout':1},sample('agent-workflows')['tasks'][0])
 assert e.value.category=='timeout'

@pytest.fixture
def api(tmp_path):
 a=ControlPlane(tmp_path/'db');account=a.account('/api/auth/register',{'username':'decision-owner','password':'test-password-123'});auth='Bearer '+account['token']
 yield a,lambda m,p,b=None:a.request(m,p,b or {},auth),account
 a.pool.shutdown(wait=True)


def test_session_expiry_revocation_and_quota(api):
 a,call,account=api
 assert call('GET','/api/me')['id']==account['user']['id']
 a.rate[account['user']['id']]=[time.monotonic()]*180
 with pytest.raises(APIError) as e:call('GET','/api/dashboard')
 assert e.value.status==429;a.rate.clear()
 a.auth_attempts=[time.monotonic()]*30
 with pytest.raises(APIError) as e:call('POST','/api/auth/login',{'username':'decision-owner','password':'test-password-123'})
 assert e.value.status==429
 with a.store.connect() as db:db.execute('UPDATE sessions SET expires=0')
 with pytest.raises(APIError) as e:call('GET','/api/me')
 assert e.value.status==401


def test_cancel_decisions_and_invalid_run_configuration(api):
 a,call,account=api
 for status,cancel in [('completed',True),('running',False),('running',True)]:
  run=a.store.create('run',account['user']['id'],{'status':status})
  if cancel:a.cancel[run['id']]=threading.Event()
  if status=='running' and cancel:assert call('POST',f'/api/runs/{run["id"]}/cancel')['ok']
  else:
   with pytest.raises(APIError) as e:call('POST',f'/api/runs/{run["id"]}/cancel')
   assert e.value.status==409
 for previous in a.store.all('run'):
  previous['status']='completed';a.store.update(previous['id'],previous)
 t=call('POST','/api/targets',{'name':'test','kind':'model','provider':'demo'})
 for extra,status in [({'suite_slug':'missing'},400),({'seed':True},400),({'idempotency_key':['bad']},400)]:
  with pytest.raises(APIError) as e:call('POST','/api/runs',{'target_id':t['id'],'suite_slug':'structured-agent',**extra})
  assert e.value.status==status


def test_active_run_limit_independent_of_presentation_cap(api):
 a,call,account=api;owner=account['user']['id']
 for _ in range(2):a.store.create('run',owner,{'status':'queued'})
 with a.store.connect() as db:
  for i in range(501):db.execute('INSERT INTO records VALUES(?,?,?,?,?)',(str(i),'run',owner,json.dumps({'status':'completed'}),time.time()+i))
 t=call('POST','/api/targets',{'name':'test','kind':'model','provider':'demo'})
 with pytest.raises(APIError) as e:call('POST','/api/runs',{'target_id':t['id'],'suite_slug':'structured-agent'})
 assert e.value.status==429


def test_upload_failed_replace_leaves_no_record_or_temporary(api):
 a,call,account=api
 with patch('praxis.media.os.replace',side_effect=OSError('disk failure')):
  with pytest.raises(OSError):ingest(a.store,account['user']['id'],{'filename':'safe.txt','content_base64':base64.b64encode(b'safe').decode()})
 assert a.store.all('artifact')==[] and list((Path(a.store.path).parent/'objects').iterdir())==[]

@pytest.mark.parametrize('raw',[
 b'\x89PNG\r\n\x1a\n'+b'\x00'*4+b'IHDR'+struct.pack('>II',0,1)+b'\x00'*9,
 b'RIFF'+b'\x00'*4+b'WAVEinvalid',
])
def test_invalid_media_metadata_rejected(api,raw):
 a,call,account=api
 with pytest.raises(APIError):ingest(a.store,account['user']['id'],{'content_base64':base64.b64encode(raw).decode()})

@pytest.mark.parametrize('raw,mime',[(b'\xff\xd8\xffDATA\xff\xd9','image/jpeg'),(b'GIF89a'+struct.pack('<HH',1,1)+b'\x00'*3,'image/gif'),(b'\x00\x00\x00\x10ftypisom','video/mp4'),(b'\x1aE\xdf\xa3fixture','video/webm'),(b'{"ok":true}','application/json')])
def test_supported_signature_and_metadata_inspection(api,raw,mime):
 a,call,account=api;r=ingest(a.store,account['user']['id'],{'content_base64':base64.b64encode(raw).decode()});assert r['mime']==mime and r['public'] is False


def test_artifact_size_png_and_world_invalid_domain(tmp_path):
 p=tmp_path/'owned.png';p.write_bytes(b'\x89PNG\r\n\x1a\n'+b'\x00'*8+struct.pack('>II',4,5));assert inspect_artifact(p)['width']==4
 with patch('praxis.artifact_checks.MAX_BYTES',1):
  with pytest.raises(ValueError):inspect_artifact(p)
 for spec in ({'domain':'unknown'},{'increase_on_success_rate_at_least':2}):
  with pytest.raises(ValueError):run_world(spec)


def test_actual_owned_browser_fixture_contract(tmp_path):
 result=check_owned_website(tmp_path)
 assert result['passed'] and len(result['assertions'])==7 and len(result['screenshots'])==2


def test_installed_module_entrypoint():
 r=subprocess.run([sys.executable,'-m','praxis','suites','list'],capture_output=True,text=True)
 assert r.returncode==0 and len(json.loads(r.stdout))==6


def test_module_entrypoint_in_process(monkeypatch,capsys):
 import runpy
 monkeypatch.setattr(sys,'argv',['praxis','suites','list'])
 with pytest.raises(SystemExit) as e:runpy.run_module('praxis',run_name='__main__')
 assert e.value.code==0 and len(json.loads(capsys.readouterr().out))==6

@pytest.mark.parametrize('field,value',[('timeout',math.nan),('temperature',True),('max_tokens',1.5)])
def test_nonfinite_or_wrong_type_adapter_budget(field,value):
 with pytest.raises(AdapterError) as e:invoke({'provider':'custom','endpoint':'http://localhost','model':'owned',field:value},{'prompt':'test'})
 assert e.value.category=='configuration'


def test_missing_provider_config_and_query_rejected():
 for target,category in [({'provider':'custom'},'configuration'),({'provider':'custom','model':'owned','endpoint':'http://localhost?key=fixture'},'invalid_endpoint')]:
  with pytest.raises(AdapterError) as e:invoke(target,{'prompt':'test'})
  assert e.value.category==category


def test_agent_external_json_actions_and_usage():
 t=sample('agent-workflows')['tasks'][0]
 with patch('praxis.agent.invoke',return_value={'output':'{"final":{"status":"fixture"}}','usage':{'completion_tokens':2}}):r=invoke_agent({'provider':'custom'},t)
 assert r['usage']['completion_tokens']==2 and r['output']['status']=='fixture'

@pytest.mark.parametrize('error,category',[(urllib.error.URLError(TimeoutError()),'timeout'),(OSError('offline'),'connection_error')])
def test_application_network_errors(error,category):
 with patch('praxis.application.urllib.request.OpenerDirector.open',side_effect=error):
  with pytest.raises(AdapterError) as e:invoke_application({'endpoint':'http://localhost','authorized':True},{'api_request':{'path':'/health'}})
 assert e.value.category==category


def test_application_non_json_response_and_invalid_method():
 from praxis.application import invoke_application
 class Response(io.BytesIO):code=200;headers={'Content-Type':'text/plain'}
 with patch('praxis.application.urllib.request.OpenerDirector.open',return_value=Response(b'plain response')):r=invoke_application({'endpoint':'http://localhost','authorized':True},{'api_request':{'path':'/'}})
 assert r['output']['body']=='plain response'
 with pytest.raises(AdapterError) as e:invoke_application({'endpoint':'http://localhost','authorized':True},{'api_request':{'method':'DELETE','path':'/'}})
 assert e.value.category=='invalid_request'

@pytest.mark.parametrize('headers,body,status',[
 ('Content-Length: bad\r\n',b'',400),('Content-Length: -1\r\n',b'',413),('Origin: https://evil.example\r\nOrigin: http://localhost:5173\r\n',b'',400),('Content-Type: application/json-evil\r\nContent-Length: 2\r\n',b'{}',415),('Content-Type: application/json\r\nContent-Length: 2\r\n',b'[]',400),('Content-Type: application/json\r\nContent-Length: 3\r\n',b'NaN',400)])
def test_http_negative_wire_decisions(api,tmp_path,headers,body,status):
 a,call,account=api;sock=SocketBuffer(('POST /api/auth/login HTTP/1.0\r\nHost: localhost\r\n'+headers+'\r\n').encode()+body)
 Handler(sock,('127.0.0.1',1),SimpleNamespace(app=a,origins=set(),web_root=tmp_path))
 assert f' {status} ' in sock.output.getvalue().decode().split('\r\n')[0]


def test_http_static_security_errors_and_options(api,tmp_path):
 a,call,account=api;server=SimpleNamespace(app=a,origins={'http://localhost:5173'},web_root=tmp_path)
 def request(path,method='GET'):
  sock=SocketBuffer(f'{method} {path} HTTP/1.0\r\nHost: localhost\r\nOrigin: http://localhost:5173\r\n\r\n'.encode());Handler(sock,('127.0.0.1',1),server);return sock.output.getvalue().decode()
 assert ' 200 ' in request('/api/health','OPTIONS').split('\r\n')[0]
 assert ' 503 ' in request('/page').split('\r\n')[0]
 assert ' 403 ' in request('/../not-owned').split('\r\n')[0]
 (tmp_path/'index.html').write_text('<h1>Owned production shell</h1>')
 assert '<h1>Owned production shell</h1>' in request('/route')
 with patch.object(a,'request',side_effect=APIError(429,'quota')):assert 'Retry-After: 60' in request('/api/me')
 with patch.object(a,'request',side_effect=RuntimeError('never disclose this')):
  r=request('/api/me');assert ' 500 ' in r.split('\r\n')[0] and 'never disclose' not in r


def test_server_loopback_configuration_and_cleanup(tmp_path):
 from praxis.server import serve
 fake=SimpleNamespace(serve_forever=lambda:None,server_close=lambda:None)
 with patch('praxis.server.ThreadingHTTPServer',return_value=fake) as factory:
  serve(tmp_path/'serve.sqlite',port=0)
 assert factory.call_args.args[0]==('127.0.0.1',0)
 assert 'http://127.0.0.1:0' in fake.origins and fake.web_root.name=='dist'


def test_real_http_mutation_disconnect_is_not_replayed():
 from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
 class Owned(BaseHTTPRequestHandler):
  mutations=0
  def log_message(self,*args):pass
  def do_POST(self):
   self.rfile.read(int(self.headers['Content-Length']));type(self).mutations+=1
   self.close_connection=True  # The mutation committed, but no response was delivered.
 server=ThreadingHTTPServer(('127.0.0.1',0),Owned);thread=threading.Thread(target=server.serve_forever);thread.start()
 s=sample('http-application');s['tasks']=s['tasks'][-1:];s['execution']['max_retries']=2
 try:
  result=execute_run({'kind':'application','provider':'custom','authorized':True,'allow_mutation':True,'endpoint':f'http://127.0.0.1:{server.server_port}'},s)
  assert Owned.mutations==1 and result['summary']['passed']==0
  assert result['tasks'][0]['attempts']==1 and result['tasks'][0]['error']['category']=='connection_error'
 finally:server.shutdown();server.server_close();thread.join()


def test_cancellation_stops_pending_retry():
 s=sample();s['tasks']=s['tasks'][:1];s['execution']['max_retries']=2;cancel=threading.Event()
 def fail(*args):cancel.set();raise AdapterError('timeout','bounded timeout')
 with patch('praxis.engine.invoke',side_effect=fail) as call:result=execute_run({'provider':'custom'},s,cancelled=cancel.is_set)
 assert call.call_count==1 and result['status']=='cancelled' and result['tasks'][0]['error']['category']=='cancelled'

@pytest.mark.parametrize('raw',[b'NaN',b'not json',b'\xff'])
def test_application_declared_json_cannot_be_nonfinite_or_malformed(raw):
 class Response(io.BytesIO):code=200;headers={'Content-Type':'application/json'}
 with patch('praxis.application.urllib.request.OpenerDirector.open',return_value=Response(raw)):
  with pytest.raises(AdapterError) as e:invoke_application({'endpoint':'http://localhost','authorized':True},{'api_request':{'path':'/'}})
 assert e.value.category=='invalid_response'


def test_malformed_chunked_http_classified_for_both_adapters():
 from http.client import IncompleteRead
 for invoke_call,path in [(lambda:invoke({'provider':'custom','endpoint':'http://localhost','model':'owned'},{'prompt':'test'}),'praxis.adapters.urllib.request.OpenerDirector.open'),(lambda:invoke_application({'endpoint':'http://localhost','authorized':True},{'api_request':{'path':'/'}}),'praxis.application.urllib.request.OpenerDirector.open')]:
  with patch(path,side_effect=IncompleteRead(b'partial')):
   with pytest.raises(AdapterError) as e:invoke_call()
  assert e.value.category=='invalid_response'

@pytest.mark.parametrize('raw',[b'{"score":1e309}',b'{"value":"\\ud800"}',b'{"score":NaN}'])
def test_provider_json_cannot_overflow_or_corrupt_persisted_json(raw):
 with patch('praxis.adapters.urllib.request.OpenerDirector.open',return_value=io.BytesIO(raw)):
  with pytest.raises(AdapterError) as e:invoke({'provider':'custom','endpoint':'http://localhost','model':'owned'},{'prompt':'test'})
 assert e.value.category=='invalid_response'


def test_overflowing_model_content_and_suite_cannot_pass_numeric_contract():
 task={'output_schema':{'type':'number'},'assertions':[{'path':'','op':'gte','expected':0}]}
 assert not all(x['passed'] for x in grade(task,'1e309'))
 s=sample();s['tasks'][0]['passing_fixture']=math.inf
 assert not validate_suite(s)['valid']


def test_deep_provider_output_fails_closed_before_grading():
 raw=('['*70+'0'+']'*70).encode()
 with patch('praxis.adapters.urllib.request.OpenerDirector.open',return_value=io.BytesIO(raw)):
  with pytest.raises(AdapterError) as e:invoke({'provider':'custom','endpoint':'http://localhost','model':'owned'},{'prompt':'test'})
 assert e.value.category=='invalid_response'
