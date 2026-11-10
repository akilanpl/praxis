"""Application adapter request/response contracts; mocked network, no execution claims."""
import io
import unittest
from unittest.mock import patch
from praxis.application import invoke_application
from praxis.adapters import AdapterError

class Response(io.BytesIO):
    code=200
    headers={'Content-Type':'application/json'}

class ApplicationTests(unittest.TestCase):
    def test_actual_response_is_graded_not_a_model_answer(self):
        with patch('praxis.application.urllib.request.OpenerDirector.open',return_value=Response(b'{"status":"ok"}')) as call:
            response=invoke_application({'authorized':True,'endpoint':'http://localhost:9000'}, {'api_request':{'method':'GET','path':'/health'}})
            self.assertEqual(response['output']['status'],200)
            self.assertEqual(response['output']['body'],{'status':'ok'})
            self.assertEqual(call.call_args.args[0].full_url,'http://localhost:9000/health')
            self.assertEqual(response['tool_trace'][0]['method'],'GET')
    def test_mutation_requires_opt_in(self):
        with self.assertRaises(AdapterError) as e: invoke_application({'authorized':True,'endpoint':'http://localhost:9000'}, {'api_request':{'method':'POST','path':'/orders','json':{}}})
        self.assertEqual(e.exception.category,'permission_denied')
    def test_untrusted_paths_and_credentials_rejected(self):
        for path in ('//evil.test','/../secret','/test\\secret','https://evil.test'):
            with self.assertRaises(AdapterError): invoke_application({'authorized':True,'endpoint':'http://localhost'}, {'api_request':{'path':path}})
        with self.assertRaises(AdapterError): invoke_application({'authorized':True,'endpoint':'http://name:secret@localhost'}, {'api_request':{'path':'/'}})

class ApplicationDiagnosticsTests(unittest.TestCase):
    def test_application_connection_uses_get_health_not_model_inference(self):
        from praxis.adapters import diagnose
        with patch('praxis.application.urllib.request.OpenerDirector.open',return_value=Response(b'{"status":"ok"}')) as call:
            result=diagnose({'authorized':True,'kind':'application','provider':'custom','endpoint':'http://localhost:9000','model':''})
            self.assertTrue(result['ok'])
            self.assertEqual(call.call_args.args[0].method,'GET')
            self.assertEqual(call.call_args.args[0].full_url,'http://localhost:9000/health')
            self.assertFalse(result['demo'])
