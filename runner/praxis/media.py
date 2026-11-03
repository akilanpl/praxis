"""Bounded inert uploads. Content determines MIME; executable payloads stay text."""
import base64
import binascii
import hashlib
import io
import json
import struct
import wave
from pathlib import Path
from .server import APIError

LIMIT=1024*1024

def ingest(store, owner, body):
    filename=Path(str(body.get('filename','artifact.txt'))).name[:150]
    try:
        raw=base64.b64decode(body.get('content_base64',''),validate=True)
    except (ValueError,TypeError,binascii.Error): raise APIError(400,'Artifact must contain valid base64 bytes')
    if not raw or len(raw)>LIMIT: raise APIError(413,'Artifact must contain 1 byte to 1 MiB')
    mime='application/octet-stream'; metadata={}; content=None
    if raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw)>=33 and raw[12:16]==b'IHDR':
        width,height=struct.unpack('>II',raw[16:24])
        if not 0<width<=16384 or not 0<height<=16384: raise APIError(400,'PNG dimensions exceed inspection limits')
        mime='image/png'; metadata={'width':width,'height':height}
    elif raw.startswith(b'\xff\xd8\xff') and raw.endswith(b'\xff\xd9'): mime='image/jpeg'
    elif raw[:6] in (b'GIF87a',b'GIF89a') and len(raw)>=13:
        mime='image/gif'; width,height=struct.unpack('<HH',raw[6:10]); metadata={'width':width,'height':height}
    elif raw.startswith(b'RIFF') and raw[8:12]==b'WAVE':
        try:
            with wave.open(io.BytesIO(raw),'rb') as clip:
                metadata={'duration_seconds':clip.getnframes()/clip.getframerate(),'channels':clip.getnchannels(),'sample_rate':clip.getframerate()}
            mime='audio/wav'
        except (wave.Error,EOFError,ZeroDivisionError): raise APIError(400,'Invalid WAV structure')
    elif len(raw)>=12 and raw[4:8]==b'ftyp':
        mime='video/mp4'; metadata={'duration_seconds':None,'codec':'uninspected; no ffprobe configured'}
    elif raw.startswith(b'\x1aE\xdf\xa3'):
        mime='video/webm'; metadata={'duration_seconds':None,'codec':'uninspected; no ffprobe configured'}
    else:
        try: content=raw.decode('utf-8')
        except UnicodeDecodeError: raise APIError(415,'Supported uploads: UTF-8 text/JSON/HTML, PNG/JPEG/GIF, WAV, MP4/WebM. Executables are rejected.')
        if '\x00' in content: raise APIError(415,'Binary content is not supported as text')
        mime='text/plain'
        try: json.loads(content); mime='application/json'
        except ValueError: pass
    sha=hashlib.sha256(raw).hexdigest(); folder=Path(store.path).parent/'objects';folder.mkdir(exist_ok=True)
    dest=folder/sha
    if not dest.exists(): dest.write_bytes(raw)
    item={'filename':filename,'mime':mime,'sha256':sha,'size':len(raw),'trust':'self-reported','public':False,'inspection':'signature and bounded metadata only; no perceptual quality claim',**metadata}
    if content is not None: item['content']=content
    else: item['data_url']='data:'+mime+';base64,'+base64.b64encode(raw).decode()
    return store.create('artifact',owner,item)
