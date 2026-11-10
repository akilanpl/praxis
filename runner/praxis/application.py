"""HTTP application evaluation, executed only by a user-controlled local runner."""
import json
from http.client import HTTPException, RemoteDisconnected
import time
import urllib.error
import urllib.parse
import urllib.request
from .adapters import AdapterError, NoRedirect, read_bounded, number

def invoke_application(target,task,seed=73):
    request=task.get('api_request')
    if not isinstance(request,dict):
        raise AdapterError('unsupported_application','Application targets require an HTTP contract suite, not model inference tasks')
    if target.get('authorized') is not True:
        raise AdapterError('permission_denied','Acknowledge ownership or authorization with authorized:true before application requests')
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
    if method=='POST' and target.get('allow_mutation') is not True:
        raise AdapterError('permission_denied','POST application tests require explicit allow_mutation on the local target')
    headers={'Accept':'application/json'}
    data=None
    if 'json' in request:
        headers['Content-Type']='application/json'
        data=json.dumps(request['json']).encode()
    start=time.monotonic()
    timeout=number(target.get('timeout',20),.1,120)
    req=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try:
        try:
            response=urllib.request.build_opener(NoRedirect).open(req,timeout=timeout)
        except urllib.error.HTTPError as exc:
            response=exc
        with response:
            raw=read_bounded(response,start+timeout)
            content_type=response.headers.get('Content-Type','').split(';')[0].strip().lower()
            try:
                body=json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON')))
            except (ValueError,UnicodeError):
                if content_type=='application/json' or content_type.endswith('+json'):
                    raise AdapterError('invalid_response','Application returned malformed JSON') from None
                body=raw.decode('utf-8',errors='replace')
            output={'status':response.code,'content_type':content_type,'body':body,'latency_ms':round((time.monotonic()-start)*1000,3)}
            return {'output':output,'usage':None,'adapter':'application-http-contract-v1','tool_trace':[{'type':'http_request','method':method,'path':path,'status':response.code}]}
    except RemoteDisconnected:
        raise AdapterError('connection_error','Application disconnected before a response') from None
    except HTTPException:
        raise AdapterError('invalid_response','Application returned malformed HTTP') from None
    except urllib.error.URLError as exc:
        raise AdapterError('timeout' if isinstance(exc.reason,TimeoutError) else 'connection_error','Application request failed or timed out') from None
    except (OSError,TimeoutError) as exc:
        raise AdapterError('timeout' if isinstance(exc,TimeoutError) else 'connection_error','Application request failed or timed out') from None
