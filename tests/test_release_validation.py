"""Release regressions for observed API type/permission and replay boundaries."""
import copy
import math
import uuid
import pytest
from praxis.server import ControlPlane, APIError

@pytest.fixture
def local(tmp_path):
    api=ControlPlane(tmp_path/'workspace.sqlite')
    account=api.request('POST','/api/auth/register',{'username':'release-owner','password':'local-test-password'},'')
    def call(method,path,body=None):return api.request(method,path,body or {},'Bearer '+account['token'])
    yield api,call
    api.pool.shutdown(wait=True)

@pytest.mark.parametrize('field,value',[
 ('name',None),('name',{}),('name',[]),('name',''),('name',' '*4),('name','x'*121),
 ('endpoint',[]),('endpoint',True),('endpoint','http://host:badport'),
 ('model',{}),('model',12),('capabilities','text'),('capabilities',['unknown']),
 ('max_tokens',0),('max_tokens',8193),('max_tokens',True),('max_tokens',1.5),
 ('temperature',-0.1),('temperature',2.1),('temperature',math.nan),('temperature','zero'),
 ('timeout',0),('timeout',121),('timeout',math.inf),('allow_mutation','true'),
],ids=lambda value:str(value)[:30])
def test_invalid_target_has_no_persisted_side_effect(local,field,value):
    api,call=local
    data={'name':'valid','kind':'model','provider':'demo','capabilities':['text']}
    data[field]=value
    with pytest.raises(APIError) as exc:call('POST','/api/targets',data)
    assert exc.value.status==400
    assert call('GET','/api/targets')==[]

@pytest.mark.parametrize('body',[
 {'max_level':0},{'max_level':4},{'max_level':True},{'max_level':1.5},
 {'seed':True},{'seed':2147483648},{'seed':-2147483649},{'seed':'73'},
 {'domain':'unknown'},{'domain':{}},{'name':''},{'name':{}},
])
def test_world_contract_rejects_unreplayable_inputs(local,body):
    api,call=local
    with pytest.raises(APIError) as exc:call('POST','/api/worlds',dict(name='world',domain='support',max_level=3,seed=73,**{})|body)
    assert exc.value.status==400
    assert call('GET','/api/worlds')==[]

def test_suite_clone_cannot_reuse_persisted_record_id(local):
    api,call=local
    suite=copy.deepcopy(next(s for s in call('GET','/api/suites') if s['slug']=='structured-agent'))
    suite['slug']='private-source'
    original=call('POST','/api/suites',suite)
    clone=call('POST','/api/suites',dict(original,slug='private-copy'))
    assert clone['id']!=original['id']
    assert call('GET','/api/suites/private-copy')['tasks']==original['tasks']

def test_idempotency_key_cannot_change_request(local):
    api,call=local
    t=call('POST','/api/targets',{'name':'demo','kind':'model','provider':'demo'})
    body={'target_id':t['id'],'suite_slug':'structured-agent','seed':73,'idempotency_key':str(uuid.uuid4())}
    first=call('POST','/api/runs',body)
    with pytest.raises(APIError) as e:call('POST','/api/runs',dict(body,seed=74))
    assert e.value.status==409
    assert call('GET','/api/runs/'+first['id'])['seed']==73

def test_auth_requires_bearer_scheme(local):
    api,call=local
    account=api.request('POST','/api/auth/register',{'username':'raw-token-user','password':'local-test-password'},'')
    with pytest.raises(APIError) as e:api.request('GET','/api/me',{},account['token'])
    assert e.value.status==401

@pytest.mark.parametrize('slug',['with/slash','../traversal','with space','UPPERCASE'])
def test_suite_slug_safe_for_ui_routes(local,slug):
    api,call=local
    suite=copy.deepcopy(call('GET','/api/suites')[0]);suite['slug']=slug
    with pytest.raises(APIError) as e:call('POST','/api/suites',suite)
    assert e.value.status==400
