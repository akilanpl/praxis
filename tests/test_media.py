import base64
import io
import tempfile
import unittest
import wave
from pathlib import Path
from praxis.media import ingest
from praxis.server import Store, APIError

class MediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.store=Store(Path(self.tmp.name)/'db')
        with self.store.connect() as db: db.execute('INSERT INTO users VALUES(?,?,?,?,?)',('owner','owner','salt','hash',0))
    def tearDown(self): self.tmp.cleanup()
    def upload(self,raw,name): return ingest(self.store,'owner',{'filename':name,'content_base64':base64.b64encode(raw).decode(),'public':True})
    def test_html_inert_and_public_consent_not_inferred(self):
        a=self.upload(b'<script>alert(1)</script>','malicious.png')
        self.assertEqual(a['mime'],'text/plain'); self.assertNotIn('data_url',a); self.assertFalse(a['public'])
    def test_wav_real_duration(self):
        out=io.BytesIO()
        with wave.open(out,'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(b'\x00\x00'*8000)
        a=self.upload(out.getvalue(),'clip.wav')
        self.assertEqual(a['duration_seconds'],1); self.assertEqual(a['mime'],'audio/wav')
    def test_binary_rejected_and_boundaries(self):
        for raw in (b'\x00\x01\x02',b'\xff\x80\x90',b'x'*(1024*1024+1),b''):
            with self.assertRaises(APIError): self.upload(raw,'unsafe.exe')
    def test_hash_dedup_storage(self):
        a=self.upload(b'example','a.txt'); b=self.upload(b'example','b.txt')
        self.assertEqual(a['sha256'],b['sha256']); self.assertEqual(len(list((Path(self.tmp.name)/'objects').iterdir())),1)
