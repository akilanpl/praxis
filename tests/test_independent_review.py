"""Regressions for defects independently reproduced at original release HEAD."""
import base64
import copy
import io
import json
import os
import threading
from pathlib import Path
from unittest.mock import patch
import pytest
from praxis.adapters import AdapterError
from praxis.application import invoke_application
from praxis.engine import execute_run,list_suites,validate_suite,digest
from praxis.media import ingest
from praxis.server import ControlPlane,APIError

def suite(slug):return copy.deepcopy(next(s for s in list_suites() if s['slug']==slug))

def test_mutating_http_timeout_never_retried():
    s=suite('http-application');s['tasks']=s['tasks'][-1:];s['execution']['max_retries']=2
    with patch('praxis.engine.invoke_application',side_effect=AdapterError('timeout','test timeout')) as call:
        result=execute_run({'kind':'application','provider':'custom'},s)
    assert call.call_count==1
    assert result['tasks'][0]['error']['category']=='timeout'

def test_agent_without_final_action_cannot_pass():
    s=suite('agent-workflows');s['tasks']=s['tasks'][:1]
    s['tasks'][0].update(max_steps=1,assertions=[],output_schema={'type':'object'},state_assertions=[{'path':'auto_refund_limit','op':'equals','expected':50}])
    result=execute_run({'kind':'agent','provider':'demo'},s)
    assert not result['tasks'][0]['passed']
    assert result['tasks'][0]['error']['category']=='step_budget_exceeded'
    assert result['tasks'][0]['tool_trace']

@pytest.mark.parametrize('value',['false',1,[],{},None,False])
def test_adapter_requires_literal_mutation_consent(value):
    with patch('praxis.application.urllib.request.OpenerDirector.open') as call:
        with pytest.raises(AdapterError) as e:invoke_application({'endpoint':'http://localhost','authorized':True,'allow_mutation':value},{'api_request':{'path':'/orders','method':'POST'}})
    assert e.value.category=='permission_denied' and not call.called

@pytest.mark.parametrize('credential',['tasks','passed','status','completed','demo','a'])
def test_redaction_preserves_envelope_and_hash(monkeypatch,credential):
    monkeypatch.setenv('PRAXIS_MODEL_API_KEY',credential)
    s=suite('structured-agent');s['tasks']=s['tasks'][:1]
    r=execute_run({'provider':'demo'},s)
    assert isinstance(r['tasks'],list) and isinstance(r['summary']['passed'],int)
    assert r['status']=='completed' and r['trust']=='demo'
    assert len(r['model_config_hash'])==64 and all(c in '0123456789abcdef' for c in r['model_config_hash'])
    assert r['evidence_hash']==digest({k:v for k,v in r.items() if k!='evidence_hash'})


def test_redaction_does_not_collapse_payload_keys_or_grade_hidden_original(monkeypatch):
    monkeypatch.setenv('PRAXIS_MODEL_API_KEY','synthetic-credential')
    s=suite('structured-agent');s['tasks']=s['tasks'][:1]
    s['tasks'][0].update(output_schema={'type':'object'},assertions=[{'path':'synthetic-credential','op':'equals','expected':1}])
    with patch('praxis.engine.invoke',return_value={'output':{'synthetic-credential':1,'[REDACTED]':2}}):r=execute_run({'provider':'custom'},s)
    assert r['summary']['passed']==0
    assert 'synthetic-credential' not in json.dumps(r)

@pytest.mark.parametrize('field,value',[('category',[]),('assertions',[{'path':'','op':[]}]),('assertions',[{'path':'x','op':'gte','expected':{}}])])
def test_malformed_suite_rejected_before_execution(field,value):
    s=suite('structured-agent');s['tasks'][0][field]=value
    assert not validate_suite(s)['valid']

@pytest.fixture
def local(tmp_path):
    api=ControlPlane(tmp_path/'db');account=api.account('/api/auth/register',{'username':'review-owner','password':'review-test-password'})
    def call(method,path,body=None):return api.request(method,path,body or {},'Bearer '+account['token'])
    yield api,call,account['user']['id']
    api.pool.shutdown(wait=True)

def test_duplicate_old_suite_cannot_bypass_list_cap(local):
    api,call,owner=local
    s=suite('structured-agent');s['slug']='old-custom';call('POST','/api/suites',s)
    for i in range(501):api.store.create('suite',owner,dict(s,slug=f'filler-{i}'))
    with pytest.raises(APIError) as e:call('POST','/api/suites',s)
    assert e.value.status==409
    assert call('GET','/api/suites/old-custom@1.0.0')['slug']=='old-custom'


def test_corrupt_existing_upload_repaired_atomically(local):
    api,call,owner=local
    raw=b'owned upload';body={'filename':'test.txt','content_base64':base64.b64encode(raw).decode()}
    first=ingest(api.store,owner,body);obj=Path(api.store.path).parent/'objects'/first['sha256'];obj.write_bytes(b'truncated')
    ingest(api.store,owner,body)
    assert obj.read_bytes()==raw

@pytest.mark.parametrize('value',[None,[],{'method':'DELETE'},{'path':[]}])
def test_malformed_application_request_rejected_before_retry_dispatch(value):
    s=suite('http-application');s['tasks'][0]['api_request']=value
    assert not validate_suite(s)['valid']
