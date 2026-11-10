"""Observed release boundary regressions; no paid model calls."""
import copy
import io
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
import pytest
from praxis.adapters import AdapterError, invoke
from praxis.application import invoke_application
from praxis.engine import digest, execute_run, list_suites, validate_suite
from praxis.server import APIError, ControlPlane

@pytest.mark.parametrize('value',[None,[],1,True,'text',{'output':{},'usage':'invalid'}, {'output':{},'usage':{'total_tokens':-1}}])
def test_provider_nonobject_and_invalid_usage_classified(value):
    with patch('praxis.adapters.urllib.request.OpenerDirector.open',return_value=io.BytesIO(json.dumps(value).encode())):
        with pytest.raises(AdapterError) as e:
            invoke({'provider':'custom','endpoint':'http://localhost/custom','model':'fixture'}, {'prompt':'test'})
    assert e.value.category=='invalid_response'

@pytest.mark.parametrize('provider,response',[('openai',{'choices':[{'message':{'content':None}}]}),('ollama',{'message':{'content':[]}})])
def test_protocol_content_requires_text(provider,response):
    with patch('praxis.adapters.urllib.request.OpenerDirector.open',return_value=io.BytesIO(json.dumps(response).encode())):
        with pytest.raises(AdapterError) as e:invoke({'provider':provider,'endpoint':'http://localhost','model':'fixture'},{'prompt':'test'})
    assert e.value.category=='invalid_response'

def test_reflected_credential_redacted_and_evidence_integrity(monkeypatch):
    monkeypatch.setenv('PRAXIS_MODEL_API_KEY','private-provider-credential')
    suite=copy.deepcopy(list_suites()[0]);suite['tasks']=suite['tasks'][:1]
    with patch('praxis.engine.invoke',return_value={'output':'private-provider-credential','usage':{'total_tokens':3}}):
        run=execute_run({'provider':'custom','endpoint':'http://localhost','model':'fixture'},suite)
    assert 'private-provider-credential' not in json.dumps(run)
    assert run['usage']=={'total_tokens':3}
    assert run['evidence_hash']==digest({k:v for k,v in run.items() if k!='evidence_hash'})
    assert run['tasks'][0]['artifact']['hash']==digest(run['tasks'][0]['output'])

def test_bounded_partial_run_preserves_named_unexecuted_tasks():
    suite=copy.deepcopy(next(s for s in list_suites() if s['slug']=='structured-agent'));suite['execution']['max_scenario_count']=1
    run=execute_run({'provider':'demo','api_key':'secret'},suite)
    assert len(run['not_run_tasks'])==len(suite['tasks'])-1
    assert run['summary']['total']==len(suite['tasks'])
    assert run['summary']['pass_rate']==1/len(suite['tasks'])
    assert 'secret' not in json.dumps(run['configuration'])

@pytest.mark.parametrize('key,value',[('max_retries',1.5),('max_scenario_count',1.5),('max_output_tokens',True)])
def test_execution_integer_bounds(key,value):
    suite=copy.deepcopy(list_suites()[0]);suite['execution'][key]=value
    assert not validate_suite(suite)['valid']

def test_suite_revision_explicit_and_concurrent_duplicate_rejected(tmp_path):
    api=ControlPlane(tmp_path/'db')
    account=api.account('/api/auth/register',{'username':'test-owner','password':'test-password-123'})
    def call(method,path,body=None):return api.request(method,path,body or {},'Bearer '+account['token'])
    try:
        suite=copy.deepcopy(list_suites()[0]);suite['version']='2.0.0'
        call('POST','/api/suites',suite)
        assert call('GET','/api/suites/'+suite['slug']+'@2.0.0')['version']=='2.0.0'
        with pytest.raises(APIError) as e:call('GET','/api/suites/'+suite['slug'])
        assert e.value.status==409
        target=call('POST','/api/targets',{'kind':'model','provider':'demo','name':'test'})
        with pytest.raises(APIError) as e:call('POST','/api/runs',{'target_id':target['id'],'suite_slug':suite['slug']})
        assert e.value.status==409
        with pytest.raises(APIError) as e:call('POST','/api/suites',suite)
        assert e.value.status==409
    finally:api.pool.shutdown(wait=True)

class OwnedApplication(BaseHTTPRequestHandler):
    failing=False
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/redirect':
            self.send_response(302);self.send_header('Location','http://127.0.0.1:1/unauthorized');self.end_headers();return
        output={'status':'wrong' if self.failing else 'ok'}
        data=json.dumps(output).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

def test_application_real_http_pass_fail_and_authorization():
    server=ThreadingHTTPServer(('127.0.0.1',0),OwnedApplication)
    thread=threading.Thread(target=server.serve_forever);thread.start()
    target={'kind':'application','provider':'custom','endpoint':f'http://127.0.0.1:{server.server_port}'}
    task={'id':'http','prompt':'health','api_request':{'path':'/health'},'output_schema':{'type':'object'},'assertions':[{'path':'status','op':'equals','expected':200},{'path':'content_type','op':'equals','expected':'application/json'},{'path':'body.status','op':'equals','expected':'ok'}]}
    suite={'slug':'owned-http','title':'Owned HTTP','version':'1','tasks':[task]}
    try:
        assert execute_run(target,suite)['tasks'][0]['error']['category']=='permission_denied'
        target['authorized']=True
        OwnedApplication.failing=False
        assert execute_run(target,suite)['summary']['passed']==1
        OwnedApplication.failing=True
        assert execute_run(target,suite)['summary']['passed']==0
        with pytest.raises(AdapterError) as e:invoke_application(target,{'api_request':{'path':'/redirect'}})
        assert e.value.category=='redirect_denied'
    finally:
        OwnedApplication.failing=False;server.shutdown();server.server_close();thread.join()

def test_restart_recovers_active_runs_beyond_list_cap(tmp_path):
    api=ControlPlane(tmp_path/'db')
    user=api.account('/api/auth/register',{'username':'restart-owner','password':'test-password-123'})['user']['id']
    original=api.store.create('run',user,{'status':'running','events':[{'sequence':0,'type':'task_started'}]})
    for i in range(501):api.store.create('run',user,{'status':'completed'})
    api.pool.shutdown(wait=True)
    restarted=ControlPlane(tmp_path/'db')
    try:
        record=restarted.store.get('run',original['id'],user)
        assert record['status']=='interrupted'
        assert record['events']==original['events']
    finally:restarted.pool.shutdown(wait=True)


def test_suite_token_limit_reaches_adapter():
    suite=copy.deepcopy(next(s for s in list_suites() if s['slug']=='structured-agent'))
    suite['tasks']=suite['tasks'][:1];suite['execution']['max_output_tokens']=17
    with patch('praxis.engine.invoke',return_value={'output':suite['tasks'][0]['passing_fixture']}) as call:
        run=execute_run({'provider':'custom','max_tokens':100},suite)
    assert call.call_args.args[0]['max_tokens']==17
    assert run['summary']['passed']==1


def test_trickled_response_respects_total_deadline():
    from praxis.adapters import read_bounded
    class Trickle:
        def read(self,n):time.sleep(.03);return b'x'
    start=time.monotonic()
    with pytest.raises(AdapterError) as e:read_bounded(Trickle(),start+.08)
    assert e.value.category=='timeout' and time.monotonic()-start<.2


def test_agent_provider_failure_retains_executed_state_trace():
    suite=copy.deepcopy(next(s for s in list_suites() if s['slug']=='agent-workflows'));suite['tasks']=suite['tasks'][:1]
    responses=[{'output':{'tool':'lookup_policy','arguments':{}}},AdapterError('invalid_response','Provider returned invalid JSON')]
    with patch('praxis.agent.invoke',side_effect=responses):
        run=execute_run({'provider':'custom','kind':'agent'},suite)
    assert run['summary']['passed']==0
    assert len(run['tasks'][0]['tool_trace'])==1
    assert run['tasks'][0]['error']['category']=='invalid_response'


def test_run_artifacts_rollback_together_on_storage_failure(tmp_path):
    api=ControlPlane(tmp_path/'db')
    account=api.account('/api/auth/register',{'username':'atomic-owner','password':'test-password-123'})
    owner=account['user']['id']
    target=api.store.create('target',owner,{'name':'fixture','provider':'demo','kind':'model'})
    suite=next(s for s in list_suites() if s['slug']=='structured-agent')
    run=api.store.create('run',owner,{'seed':73,'status':'queued'})
    api.cancel[run['id']]=threading.Event()
    original=api.store.create;calls=[]
    def storage(kind,owner,data,**kwargs):
        if kind=='artifact':
            calls.append(kind)
            if len(calls)==2:raise RuntimeError('simulated storage interruption')
        return original(kind,owner,data,**kwargs)
    try:
        with patch.object(api.store,'create',side_effect=storage):api.execute(run,target,suite)
        assert api.store.all('artifact',owner)==[]
        assert api.store.get('run',run['id'],owner)['status']=='failed'
    finally:api.pool.shutdown(wait=True)
