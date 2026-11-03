"""HTTP request contract tests with a mocked transport, never inference evidence."""
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runner'))
from praxis.adapters import AdapterError, NoRedirect, invoke


class ConnectorProtocolTests(unittest.TestCase):
    def setUp(self):
        self.task = {'prompt': 'Return readiness JSON', 'output_schema': {'type': 'object'}}
        self.transport = patch('praxis.adapters.urllib.request.OpenerDirector.open')
        self.open = self.transport.start()
        self.addCleanup(self.transport.stop)

    def response(self, data):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.open.return_value = io.BytesIO(raw)

    def request(self):
        args = self.open.call_args.args
        return args[0], json.loads(args[0].data)

    def test_openai_request_and_usage(self):
        self.response({'choices': [{'message': {'content': '{"ready":true}'}}], 'usage': {'completion_tokens': 3}})
        response = invoke({'provider': 'openai', 'endpoint': 'http://localhost:11434/v1', 'model': 'protocol-fixture', 'max_tokens': 17}, self.task, seed=91)
        request, body = self.request()
        self.assertEqual(request.full_url, 'http://localhost:11434/v1/chat/completions')
        self.assertEqual(body['max_tokens'], 17)
        self.assertNotIn('seed', body)
        self.assertEqual(json.loads(response['output']), {'ready': True})
        self.assertEqual(response['usage']['completion_tokens'], 3)

    def test_supported_seed_is_explicit(self):
        self.response({'choices': [{'message': {'content': '{}'}}]})
        invoke({'provider': 'openai', 'endpoint': 'http://localhost/v1', 'model': 'protocol-fixture', 'supports_seed': True}, self.task, seed=91)
        self.assertEqual(self.request()[1]['seed'], 91)

    def test_ollama_protocol_and_usage(self):
        self.response({'message': {'content': '{}'}, 'prompt_eval_count': 4, 'eval_count': 3})
        response = invoke({'provider': 'ollama', 'endpoint': 'http://localhost:11434', 'model': 'protocol-fixture'}, self.task, seed=91)
        request, body = self.request()
        self.assertEqual(request.full_url, 'http://localhost:11434/api/chat')
        self.assertFalse(body['stream'])
        self.assertEqual(body['options']['seed'], 91)
        self.assertEqual(response['usage'], {'prompt_tokens': 4, 'completion_tokens': 3})

    def test_custom_protocol(self):
        self.response({'output': {'ready': True}})
        response = invoke({'provider': 'custom', 'endpoint': 'http://localhost/custom', 'model': 'protocol-fixture'}, self.task)
        self.assertEqual(self.request()[1]['protocol'], 'praxis.model.v1')
        self.assertEqual(response['output'], {'ready': True})

    def test_redirect_handler_rejects(self):
        with self.assertRaises(AdapterError) as caught:
            NoRedirect().redirect_request(None, None, 302, 'redirect', {}, 'http://localhost/other')
        self.assertEqual(caught.exception.category, 'redirect_denied')

    def test_malformed_response_classified(self):
        self.response(b'not JSON')
        with self.assertRaises(AdapterError) as caught:
            invoke({'provider': 'custom', 'endpoint': 'http://localhost/custom', 'model': 'protocol-fixture'}, self.task)
        self.assertEqual(caught.exception.category, 'invalid_response')

    def test_http_failure_does_not_leak_response_body(self):
        self.open.side_effect = urllib.error.HTTPError('http://localhost/custom', 401, 'sensitive detail', {}, None)
        with self.assertRaises(AdapterError) as caught:
            invoke({'provider': 'custom', 'endpoint': 'http://localhost/custom', 'model': 'protocol-fixture'}, self.task)
        self.assertEqual(caught.exception.category, 'http_error')
        self.assertNotIn('sensitive detail', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
