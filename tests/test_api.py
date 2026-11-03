import concurrent.futures
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runner'))
from praxis.server import ControlPlane, APIError

class LocalAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.api=ControlPlane(Path(self.tmp.name)/'db.sqlite')
        self.alice=self.call('POST','/api/auth/register',{'username':'alice','password':'test-password-123'})
        self.bob=self.call('POST','/api/auth/register',{'username':'bob','password':'test-password-123'})
        self.token=self.alice['token']
    def tearDown(self): self.api.pool.shutdown(wait=True); self.tmp.cleanup()
    def call(self,m,p,b=None,token=None): return self.api.request(m,p,b or {},'Bearer '+(token or getattr(self,'token','')))
    def target(self,provider='demo'):
        return self.call('POST','/api/targets',{'name':provider,'provider':provider,'kind':'model'})
    def test_auth_and_revocation(self):
        with self.assertRaises(APIError): self.call('GET','/api/me',token='bad')
        with self.assertRaises(APIError): self.call('POST','/api/auth/login',{'username':'alice','password':'wrong-password'})
        self.call('POST','/api/auth/logout')
        with self.assertRaises(APIError): self.call('GET','/api/me')
    def test_owner_isolation_and_secret_policy(self):
        target=self.target()
        with self.assertRaises(APIError) as e: self.call('POST','/api/targets/'+target['id']+'/diagnostics',token=self.bob['token'])
        self.assertEqual(e.exception.status,404)
        for extra in ({'api_key':'secret'},{'endpoint':'https://name:password@example.com'},{'endpoint':'file:///etc/passwd'}):
            with self.assertRaises(APIError): self.call('POST','/api/targets',dict(name='bad',provider='openai',kind='model',**extra))
        self.assertEqual(self.call('GET','/api/targets',token=self.bob['token']),[])
    def test_persisted_run_and_evidence(self):
        target=self.target(); suite=next(s for s in self.call('GET','/api/suites') if s['slug']=='structured-agent')
        run=self.call('POST','/api/runs',{'target_id':target['id'],'suite_slug':suite['slug'],'seed':73})
        for _ in range(300):
            current=self.call('GET','/api/runs/'+run['id'])
            if current['status'] not in ('queued','running'): break
            time.sleep(.01)
        self.assertEqual(current['status'],'completed',current)
        self.assertEqual(current['trust'],'demo')
        self.assertTrue(current['result']['tasks'])
        self.assertTrue(self.call('GET','/api/artifacts'))
        with self.assertRaises(APIError): self.call('GET','/api/runs/'+run['id'],token=self.bob['token'])
        self.assertEqual(self.call('GET','/api/leaderboards')['objective'],[])
        self.assertEqual(self.call('GET','/api/arena')['empty'],True) # own outputs never eligible
    def seed_artifacts(self):
        t1=self.target(); t2=self.target('demo-failing')
        for target in (t1,t2):
            self.api.store.create('artifact',self.alice['user']['id'],{'target_id':target['id'],'task_id':'test','conditions':'same','suite_slug':'suite','suite_version':'1','mime':'text/plain','content':target['provider'],'trust':'demo','public':True})
    def test_blinding_duplicate_vote_and_ratings(self):
        self.seed_artifacts(); bob=self.bob['token']
        m=self.call('GET','/api/arena',token=bob)
        self.assertNotIn('target_id',json.dumps(m)); self.assertNotIn('name',m['a'])
        def vote(_):
            try: return self.call('POST','/api/arena/'+m['id']+'/vote',{'choice':'a'},bob)
            except APIError as e: return e.status
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: outcomes=list(pool.map(vote,range(4)))
        self.assertEqual(sum(isinstance(x,dict) for x in outcomes),1)
        self.assertEqual(outcomes.count(409),3)
        board=self.call('GET','/api/leaderboards')
        self.assertEqual(len(board['preference']),2)
        self.assertTrue(all(x['status']=='insufficient evidence' for x in board['preference']))
        self.assertEqual(board['objective'],[])
    def test_noncomparable_and_private_excluded(self):
        self.seed_artifacts()
        a=self.api.store.all('artifact')[0]; a['conditions']='different'; self.api.store.update(a['id'],a)
        self.assertTrue(self.call('GET','/api/arena',token=self.bob['token'])['empty'])
        a['conditions']='same'; a['public']=False; self.api.store.update(a['id'],a)
        self.assertTrue(self.call('GET','/api/arena',token=self.bob['token'])['empty'])
    def test_application_cannot_be_model_and_invalid_seed(self):
        t=self.call('POST','/api/targets',{'name':'app','provider':'custom','kind':'application'})
        with self.assertRaises(APIError) as e: self.call('POST','/api/runs',{'target_id':t['id'],'suite_slug':'structured-agent'})
        self.assertEqual(e.exception.status,422)
    def test_world_replay(self):
        world=self.call('POST','/api/worlds',{'name':'test','domain':'support','seed':73,'max_level':3})
        a=self.call('POST','/api/worlds/'+world['id']+'/replay'); b=self.call('POST','/api/worlds/'+world['id']+'/replay')
        self.assertEqual(a,b)
        with self.assertRaises(APIError): self.call('POST','/api/worlds/'+world['id']+'/replay',token=self.bob['token'])

if __name__=='__main__': unittest.main()

class ConcurrencyTests(unittest.TestCase):
    setUp=LocalAPITests.setUp
    tearDown=LocalAPITests.tearDown
    call=LocalAPITests.call
    target=LocalAPITests.target
    seed_artifacts=LocalAPITests.seed_artifacts
    def test_concurrent_match_assignment_reuses_one_pair(self):
        self.seed_artifacts()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            matches=list(pool.map(lambda _:self.call('GET','/api/arena',token=self.bob['token']),range(4)))
        self.assertEqual(len({m['id'] for m in matches}),1)
    def test_idempotent_run_request(self):
        target=self.target(); payload={'target_id':target['id'],'suite_slug':'structured-agent','idempotency_key':'retry-1'}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            runs=list(pool.map(lambda _:self.call('POST','/api/runs',payload),range(4)))
        self.assertEqual(len({r['id'] for r in runs}),1)
    def test_invalid_suite_rejected(self):
        with self.assertRaises(APIError) as error: self.call('POST','/api/suites',{'slug':'bad','version':'1','title':'bad','tasks':[]})
        self.assertEqual(error.exception.status,400)
