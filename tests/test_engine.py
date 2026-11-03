import copy
import json
import tempfile
import time
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from praxis.adapters import AdapterError, diagnose, invoke
from praxis.engine import digest, execute_run, grade, list_suites, validate_suite
from praxis.worlds import run_world
from praxis.artifact_checks import execute_untrusted_code, check_owned_website, inspect_artifact
from praxis.cli import report_html

class EngineTests(unittest.TestCase):
    def test_at_least_30_distinct_valid_scenarios(self):
        suites=list_suites()
        self.assertGreaterEqual(sum(len(s['tasks']) for s in suites),30)
        ids=[t['id'] for s in suites for t in s['tasks']]
        self.assertEqual(len(ids),len(set(ids)))
        for suite in suites:
            self.assertTrue(validate_suite(suite)['valid'])

    def test_every_passing_and_failing_regression_fixture(self):
        for suite in list_suites():
            for task in suite['tasks']:
                with self.subTest(task=task['id']):
                    self.assertTrue(all(a['passed'] for a in grade(task,task['passing_fixture'])))
                    self.assertFalse(all(a['passed'] for a in grade(task,task['failing_fixture'])))

    def test_demo_end_to_end(self):
        for suite in list_suites():
            result=execute_run({'provider':'demo','kind':'agent' if suite['slug']=='agent-workflows' else 'model'},suite)
            self.assertEqual(result['summary']['passed'],0 if suite['slug']=='http-application' else len(suite['tasks']))
            self.assertEqual(result['trust'],'demo')
            self.assertEqual(result['status'],'completed')
            self.assertEqual(result['cost']['status'],'unknown')
            self.assertTrue(result['events'])
            self.assertEqual(result['evidence_hash'],digest({k:v for k,v in result.items() if k!='evidence_hash'}))

    def test_failing_demo_never_passes(self):
        result=execute_run({'provider':'demo-failing'},next(s for s in list_suites() if s['slug']=='structured-agent'))
        self.assertEqual(result['summary']['passed'],0)
        self.assertEqual(result['summary']['failed'],8)

    def test_cancel_denominator_includes_not_run(self):
        result=execute_run({'provider':'demo'},next(s for s in list_suites() if s['slug']=='structured-agent'),cancelled=lambda:True)
        self.assertEqual(result['status'],'cancelled')
        self.assertEqual(result['summary']['not_run'],8)
        self.assertEqual(result['summary']['pass_rate'],0)

    def test_cancel_during_run(self):
        seen=[]
        result=execute_run({'provider':'demo'},next(s for s in list_suites() if s['slug']=='structured-agent'),on_event=lambda e:seen.append(e),cancelled=lambda:any(e['type']=='task_completed' for e in seen))
        self.assertEqual(result['status'],'cancelled')
        self.assertEqual(result['summary']['executed'],1)

    def test_invalid_and_unsafe_dsl_rejected(self):
        suite=copy.deepcopy(next(s for s in list_suites() if s['slug']=='structured-agent'))
        suite['tasks'][0]['assertions'][0]['op']='eval'
        self.assertFalse(validate_suite(suite)['valid'])
        with self.assertRaises(ValueError):
            execute_run({'provider':'demo','kind':'agent' if suite['slug']=='agent-workflows' else 'model'},suite)

    def test_schema_ref_rejected(self):
        suite=copy.deepcopy(next(s for s in list_suites() if s['slug']=='structured-agent'))
        suite['tasks'][0]['output_schema']={'$ref':'https://invalid.example/secret'}
        self.assertFalse(validate_suite(suite)['valid'])

    def test_numeric_schema_boolean_separation(self):
        task={'output_schema':{'type':'object','properties':{'n':{'type':'integer'}},'required':['n']},'assertions':[{'name':'n','path':'n','op':'equals','expected':1}]}
        self.assertFalse(all(a['passed'] for a in grade(task,{'n':True})))

    def test_bad_json_fails(self):
        task=next(s for s in list_suites() if s['slug']=='structured-agent')['tasks'][0]
        self.assertFalse(all(a['passed'] for a in grade(task,'not json')))

    def test_unknown_provider_fails_with_evidence(self):
        result=execute_run({'provider':'unknown','endpoint':'http://localhost','model':'test'},next(s for s in list_suites() if s['slug']=='structured-agent'))
        self.assertEqual(result['summary']['passed'],0)
        self.assertEqual(result['tasks'][0]['error']['category'],'unsupported_provider')

    def test_application_not_treated_as_model(self):
        result=execute_run({'provider':'demo','kind':'application'},next(s for s in list_suites() if s['slug']=='structured-agent'))
        self.assertEqual(result['summary']['passed'],0)
        self.assertEqual(result['tasks'][0]['error']['category'],'unsupported_application')

    def test_report_escapes_html(self):
        result=execute_run({'provider':'demo'},next(s for s in list_suites() if s['slug']=='structured-agent'))
        result['tasks'][0]['output']='<script>alert(1)</script>'
        report=report_html(result)
        self.assertNotIn('<script>',report)
        self.assertIn('&lt;script&gt;',report)

    def test_untrusted_code_and_html_denied(self):
        with self.assertRaises(RuntimeError):
            execute_untrusted_code('import os')
        with self.assertRaises(RuntimeError):
            check_owned_website('/tmp/unused',html='<script>evil()</script>')

    def test_artifact_hash_and_wav(self):
        import wave
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'clip.wav'
            with wave.open(str(path),'wb') as clip:
                clip.setnchannels(1)
                clip.setsampwidth(2)
                clip.setframerate(8000)
                clip.writeframes(b'\x00\x00'*8000)
            metadata=inspect_artifact(path)
            self.assertEqual(metadata['duration_seconds'],1)
            self.assertEqual(metadata['channels'],1)
            self.assertEqual(len(metadata['sha256']),64)

class AgentTests(unittest.TestCase):
    def test_actual_tool_state_mutation(self):
        suite=next(s for s in list_suites() if s['slug']=='agent-workflows')
        result=execute_run({'provider':'demo','kind':'agent'},suite)
        self.assertEqual(result['summary']['passed'],4)
        trace=result['tasks'][0]['tool_trace']
        self.assertEqual(trace[2]['state_before']['purchases']['P1']['status'],'open')
        self.assertEqual(trace[2]['state_after']['purchases']['P1']['status'],'refunded')
        self.assertEqual(trace[2]['state_after']['refund_total'],25)

    def test_unauthorized_action_and_no_evidence_refund_fail(self):
        suite=next(s for s in list_suites() if s['slug']=='agent-workflows')
        result=execute_run({'provider':'demo-failing','kind':'agent'},suite)
        self.assertEqual(result['summary']['passed'],0)
        for row in result['tasks']:
            self.assertFalse(row['tool_trace'][0]['authorized'])
            self.assertEqual(row['tool_trace'][0]['state_before'],row['tool_trace'][0]['state_after'])
            self.assertTrue(any(a['name']=='actual purchase state' and not a['passed'] for a in row['assertions']))

    def test_plain_model_cannot_pass_executable_agent_suite(self):
        suite=next(s for s in list_suites() if s['slug']=='agent-workflows')
        result=execute_run({'provider':'demo','kind':'model'},suite)
        self.assertEqual(result['summary']['passed'],0)

    def test_task_without_environment_fails_as_agent(self):
        suite=next(s for s in list_suites() if s['slug']=='structured-agent')
        result=execute_run({'provider':'demo','kind':'agent'},suite)
        self.assertEqual(result['tasks'][0]['error']['category'],'capability_mismatch')

class WorldTests(unittest.TestCase):
    def test_all_domain_growth_and_replay(self):
        for domain in ('customer-support','research','workflow','web-product'):
            with self.subTest(domain=domain):
                first=run_world({'domain':domain},73)
                second=run_world({'domain':domain},73)
                self.assertEqual(first['replay_hash'],second['replay_hash'])
                self.assertEqual([l['entities'] for l in first['levels']],[1,5,12])
                self.assertEqual(first['evaluation']['entities_completed'],18)
                self.assertTrue(any(t['outcome']=='transient_failure_retry_scheduled' for t in first['transitions']))
                for t in first['transitions']:
                    self.assertNotEqual(t['before_hash'],t['after_hash'])

    def test_seed_changes_world(self):
        self.assertNotEqual(run_world({},73)['replay_hash'],run_world({},74)['replay_hash'])

    def test_permission_denial_prevents_growth(self):
        result=run_world({'deny_tool':'resolve_ticket'})
        self.assertEqual(len(result['levels']),1)
        self.assertEqual(result['evaluation']['entities_completed'],0)
        self.assertEqual(result['transitions'][0]['before_hash'],result['transitions'][0]['after_hash'])

    def test_policy_conflict_refused(self):
        result=run_world({'unsafe_refunds':True})
        self.assertTrue(any(t['outcome']=='policy_denied' for t in result['transitions']))
        self.assertTrue(any(not a['passed'] for l in result['levels'] for a in l['assertions']))

    def test_world_budget(self):
        result=run_world({'max_steps':2})
        self.assertEqual(result['steps'],2)
        self.assertEqual(result['status'],'budget_exceeded')

    def test_static_comparison_mode(self):
        result=run_world({'mode':'static'})
        self.assertEqual(len(result['levels']),1)

class MockModelHandler(BaseHTTPRequestHandler):
    calls=[]
    def log_message(self,*args): pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        type(self).calls.append((self.path,body,self.headers.get('Authorization')))
        if self.path=='/slow':
            time.sleep(0.2)
        if self.path=='/agent':
            prior=json.loads(body['input'].split('Previous actions: ')[1].split('\nReturn only JSON')[0])
            actions=[{'tool':'lookup_policy','arguments':{}},{'tool':'lookup_purchase','arguments':{'id':'P1'}},{'tool':'refund','arguments':{'id':'P1'}},{'final':{'status':'refunded'}}]
            payload={'output':actions[len(prior)]}
        elif self.path=='/v1/chat/completions':
            payload={'choices':[{'message':{'content':'{"ready":true}'}}],'usage':{'prompt_tokens':4,'completion_tokens':2}}
        elif self.path=='/api/chat':
            payload={'message':{'content':'{"ready":true}'},'prompt_eval_count':4,'eval_count':2}
        else:
            payload={'output':{'ready':True},'usage':{'total_tokens':6}}
        data=json.dumps(payload).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except BrokenPipeError:
            pass

class AdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=HTTPServer(('127.0.0.1',0),MockModelHandler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base='http://127.0.0.1:%d'%cls.server.server_port
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
    def test_openai_adapter_protocol_real_http(self):
        target={'provider':'openai','endpoint':self.base+'/v1','model':'fixture'}
        result=diagnose(target)
        self.assertTrue(result['ok'])
        path,body,_=MockModelHandler.calls[-1]
        self.assertEqual(path,'/v1/chat/completions')
        self.assertNotIn('seed',body)
        self.assertIn('messages',body)
    def test_ollama_adapter_protocol_real_http(self):
        result=diagnose({'provider':'ollama','endpoint':self.base,'model':'fixture'})
        self.assertTrue(result['ok'])
        path,body,_=MockModelHandler.calls[-1]
        self.assertEqual(path,'/api/chat')
        self.assertFalse(body['stream'])
        self.assertIn('seed',body['options'])
    def test_custom_adapter_protocol_real_http(self):
        result=diagnose({'provider':'custom','endpoint':self.base+'/custom','model':'fixture'})
        self.assertTrue(result['ok'])
        self.assertEqual(MockModelHandler.calls[-1][1]['protocol'],'praxis.model.v1')
    def test_url_credentials_rejected(self):
        result=diagnose({'provider':'custom','endpoint':'http://secret:password@localhost/x','model':'fixture'})
        self.assertFalse(result['ok'])
        self.assertEqual(result['category'],'invalid_endpoint')
    def test_agent_real_http_decision_loop(self):
        suite=copy.deepcopy(next(s for s in list_suites() if s['slug']=='agent-workflows'))
        suite['tasks']=suite['tasks'][:1]
        result=execute_run({'provider':'custom','endpoint':self.base+'/agent','model':'fixture','kind':'agent'},suite)
        self.assertEqual(result['trust'],'self-reported')
        self.assertEqual(result['summary']['passed'],1)
        self.assertEqual(result['tasks'][0]['tool_trace'][2]['state_after']['refund_total'],25)
    def test_deadline_enforced(self):
        task={'prompt':'hello','output_schema':{}}
        start=time.monotonic()
        with self.assertRaises(AdapterError) as caught:
            invoke({'provider':'custom','endpoint':self.base+'/slow','model':'fixture','timeout':0.1},task)
        self.assertEqual(caught.exception.category,'timeout')
        self.assertLess(time.monotonic()-start,0.5)
    def test_secrets_excluded_from_evidence(self):
        result=execute_run({'provider':'demo','api_key':'super-secret','token':'secret-token'},next(s for s in list_suites() if s['slug']=='structured-agent'))
        self.assertNotIn('super-secret',json.dumps(result))
        self.assertNotIn('secret-token',json.dumps(result))

if __name__=='__main__':
    unittest.main()
