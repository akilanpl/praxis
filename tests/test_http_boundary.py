"""Exercise the real HTTP parser without creating network sockets."""
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from praxis.server import ControlPlane, Handler

class SocketBuffer:
    def __init__(self,request): self.input=io.BytesIO(request); self.output=io.BytesIO()
    def makefile(self,*args,**kwargs): return self.input
    def sendall(self,data): self.output.write(data)
    def settimeout(self,value): self.timeout=value

class HTTPBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.app=ControlPlane(Path(self.tmp.name)/'db')
        self.server=SimpleNamespace(app=self.app,origins={'http://localhost:5173'},web_root=Path(self.tmp.name))
    def tearDown(self): self.app.pool.shutdown(); self.tmp.cleanup()
    def request(self,method='GET',path='/api/health',headers='',body=b''):
        sock=SocketBuffer((method+' '+path+' HTTP/1.0\r\n'+headers+'\r\n').encode()+body)
        Handler(sock,('127.0.0.1',1),self.server)
        return sock.output.getvalue().decode()
    def test_dns_rebinding_host_rejected(self):
        self.assertIn('403',self.request(headers='Host: evil.test\r\n').split('\r\n')[0])
    def test_origin_rejected(self):
        text=self.request(headers='Host: localhost:8787\r\nOrigin: https://evil.test\r\n')
        self.assertIn('403',text.split('\r\n')[0]); self.assertNotIn('Access-Control-Allow-Origin:',text)
    def test_health_security_headers(self):
        text=self.request(headers='Host: localhost:8787\r\nOrigin: http://localhost:5173\r\n')
        self.assertIn('200',text.split('\r\n')[0]); self.assertIn('X-Content-Type-Options: nosniff',text)
        self.assertIn("frame-src 'none'",text); self.assertIn('Access-Control-Allow-Origin: http://localhost:5173',text)
    def test_oversize_rejected_before_read(self):
        text=self.request('POST','/api/auth/login','Host: localhost\r\nContent-Type: application/json\r\nContent-Length: 3000000\r\n')
        self.assertIn('413',text.split('\r\n')[0])
    def test_invalid_json_and_content_type(self):
        text=self.request('POST','/api/auth/login','Host: localhost\r\nContent-Type: application/json\r\nContent-Length: 3\r\n',b'bad')
        self.assertIn('400',text.split('\r\n')[0])
        text=self.request('POST','/api/auth/login','Host: localhost\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n',b'bad')
        self.assertIn('415',text.split('\r\n')[0])

    def test_ambiguous_http_framing_rejected(self):
        for headers in ('Transfer-Encoding: chunked\r\n','Content-Length: 0\r\nContent-Length: 1\r\n'):
            self.assertIn('400',self.request('POST','/api/auth/login','Host: localhost\r\n'+headers).split('\r\n')[0])

    def test_truncated_body_and_total_read_deadline(self):
        from unittest.mock import patch
        from praxis.server import APIError
        text=self.request('POST','/api/auth/login','Host: localhost\r\nContent-Type: application/json\r\nContent-Length: 20\r\n',b'{}')
        self.assertIn('400',text.split('\r\n')[0])
        handler=Handler.__new__(Handler);handler.connection=SocketBuffer(b'');handler.rfile=io.BytesIO(b'{}')
        with patch('praxis.server.time.monotonic',side_effect=[0,16]):
            with self.assertRaises(APIError) as e:handler.read_body(2)
        self.assertEqual(e.exception.status,408)
