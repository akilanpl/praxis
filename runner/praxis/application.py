"""HTTP application evaluation, executed only by a user-controlled local runner."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from .adapters import AdapterError, MAX_RESPONSE_BYTES, NoRedirect

def invoke_application(target,task,seed=73):
    request=task.get('api_request')
    if not isinstance(request,dict):
        raise AdapterError('unsupported_application','Application targets require an HTTP contract suite, not model inference tasks')
    base=target.get('endpoint','').rstrip('/')
    parsed=urllib.parse.urlparse(base)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise AdapterError('invalid_endpoint','Application endpoint must be HTTP(S) without embedded credentials, query or fragment')
    path=request.get('path','/')
    if not isinstance(path,str) or not path.startswith('/') or path.startswith('//') or '..' in path or '\\' in path or urllib.parse.urlparse(path).scheme:
        raise AdapterError('invalid_request','Application paths must be relative origin paths')
    method=request.get('method','GET')
    if method not in ('GET','POST'):
        raise AdapterError('invalid_request','Only bounded GET and POST contract checks are allowed')
    if method=='POST' and not target.get('allow_mutation',False):
        raise AdapterError('permission_denied','POST application tests require explicit allow_mutation on the local target')
    headers={'Accept':'application/json'}
    data=None
    if 'json' in request:
        headers['Content-Type']='application/json'
        data=json.dumps(request['json']).encode()
    start=time.monotonic()
    req=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        try:
            response=urllib.request.build_opener(NoRedirect).open(req,timeout=min(max(float(target.get('timeout',20)),.1),120))
        except urllib.error.HTTPError as exc:
            response=exc
        with response:
            raw=response.read(MAX_RESPONSE_BYTES+1)
            if len(raw)>MAX_RESPONSE_BYTES:
                raise AdapterError('response_limit','Application response exceeds 2 MiB')
            content_type=response.headers.get('Content-Type','').split(';')[0]
            try:
                body=json.loads(raw)
            except (ValueError,UnicodeError):
                body=raw.decode('utf-8',errors='replace')
            output={'status':response.code,'content_type':content_type,'body':body,'latency_ms':round((time.monotonic()-start)*1000,3)}
            return {'output':output,'usage':None,'adapter':'application-http-contract-v1','tool_trace':[{'type':'http_request','method':method,'path':path,'status':response.code}]}
    except urllib.error.URLError as exc:
        raise AdapterError('timeout' if isinstance(exc.reason,TimeoutError) else 'connection_error','Application request failed or timed out') from None
    except (OSError,TimeoutError) as exc:
        raise AdapterError('timeout' if isinstance(exc,TimeoutError) else 'connection_error','Application request failed or timed out') from None
