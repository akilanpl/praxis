"""User-controlled model connections. Credentials never enter results or configuration."""
import json
from http.client import HTTPException, RemoteDisconnected
import math
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict

MAX_RESPONSE_BYTES = 2 * 1024 * 1024

def strict_json_loads(data):
    def finite(text):
        value=float(text)
        if not math.isfinite(value):raise ValueError('Non-finite JSON number')
        return value
    try:
        value=json.loads(data,parse_float=finite,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON')))
        def bounded(item,depth=0):
            if depth>64:raise ValueError('JSON nesting exceeds 64 levels')
            if isinstance(item,dict):
                for child in item.values():bounded(child,depth+1)
            elif isinstance(item,list):
                for child in item:bounded(child,depth+1)
        bounded(value)
        json.dumps(value,allow_nan=False,ensure_ascii=False).encode('utf-8')
    except (RecursionError,UnicodeError):raise ValueError('JSON cannot be represented safely') from None
    return value

class AdapterError(RuntimeError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category = category

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AdapterError("redirect_denied", "Provider redirects are not accepted")

def number(value, lower, upper, integer=False):
    if type(value) not in (int,float) or not math.isfinite(value) or (integer and type(value) is not int):
        raise AdapterError("configuration","Adapter budgets must be finite numbers of the expected type")
    return min(max(value,lower),upper)

def valid_usage(item):
    return item is None or (isinstance(item,dict) and all(valid_usage(v) for v in item.values())) or (type(item) in (int,float) and math.isfinite(item) and 0<=item<=2**53-1)

def read_bounded(response, deadline):
    """Bound both total bytes and elapsed read time, including trickled responses."""
    chunks=[]
    size=0
    while True:
        remaining=deadline-time.monotonic()
        if remaining<=0:
            raise AdapterError("timeout", "HTTP response exceeded its deadline")
        sock=getattr(getattr(getattr(response,"fp",None),"raw",None),"_sock",None)
        if sock is not None:
            sock.settimeout(remaining)
        chunk=getattr(response,"read1",response.read)(min(65536,MAX_RESPONSE_BYTES+1-size))
        if not chunk:
            return b"".join(chunks)
        size+=len(chunk)
        if size>MAX_RESPONSE_BYTES:
            raise AdapterError("response_limit", "HTTP response exceeds 2 MiB")
        chunks.append(chunk)

def _post(url, payload, key=None, timeout=20):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise AdapterError("invalid_endpoint", "Endpoint must be HTTP(S), without embedded credentials")
    if parsed.query or parsed.fragment:
        raise AdapterError("invalid_endpoint", "Endpoint must not contain query parameters or fragments")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    deadline=time.monotonic()+timeout
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=timeout) as response:
            data = read_bounded(response,deadline)
            value = strict_json_loads(data)
            if not isinstance(value, dict):
                raise AdapterError("invalid_response", "Provider response must be a JSON object")
            usage=value.get("usage")
            if usage is not None and (not isinstance(usage,dict) or not valid_usage(usage)):
                raise AdapterError("invalid_response", "Provider usage must contain nonnegative finite numbers")
            return value
    except urllib.error.HTTPError as exc:
        raise AdapterError("http_error", "Provider returned HTTP %s" % exc.code) from None
    except RemoteDisconnected:
        raise AdapterError("connection_error","Provider disconnected before a response") from None
    except HTTPException:
        raise AdapterError("invalid_response","Provider returned malformed HTTP") from None
    except urllib.error.URLError as exc:
        timeout_error=isinstance(exc.reason,(TimeoutError,socket.timeout))
        raise AdapterError("timeout" if timeout_error else "connection_error", "Provider connection failed or timed out") from None
    except (TimeoutError, OSError) as exc:
        raise AdapterError("timeout" if isinstance(exc, (TimeoutError, socket.timeout)) else "connection_error", "Provider connection failed or timed out") from None
    except (ValueError, KeyError, UnicodeError, RecursionError):
        raise AdapterError("invalid_response", "Provider returned invalid JSON") from None

def invoke(target: Dict[str, Any], task: Dict[str, Any], seed=73):
    provider = target.get("provider", "demo")
    if target.get("kind", "model") == "application":
        raise AdapterError("unsupported_application", "Application targets require browser or API contract checks, not model inference")
    if provider in ("demo", "demo-failing"):
        # Deliberate infrastructure fixture: no inference and no capability claim.
        output = task["passing_fixture"] if provider == "demo" else task["failing_fixture"]
        return {"output": output, "usage": None, "adapter": provider, "tool_trace": []}
    endpoint = target.get("endpoint", "").rstrip("/")
    model = target.get("model", "")
    if not endpoint or not model:
        raise AdapterError("configuration", "Model identifier and endpoint are required")
    prompt = task["prompt"] + "\nReturn only JSON matching this schema: " + json.dumps(task.get("output_schema", {}))
    timeout = number(target.get("timeout",20),0.1,120)
    max_tokens = number(target.get("max_tokens",1024),1,8192,integer=True)
    temperature = number(target.get("temperature",0),0,2)
    key_name = target.get("key_env", "PRAXIS_MODEL_API_KEY")
    key = os.environ.get(key_name)
    if provider == "openai":
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": temperature}
        if target.get("supports_seed") is True:
            payload["seed"] = seed
        data = _post(endpoint + "/chat/completions", payload, key, timeout)
        try:
            output = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise AdapterError("invalid_response", "OpenAI-compatible response lacks choices.message.content")
        if not isinstance(output, str):
            raise AdapterError("invalid_response", "OpenAI-compatible content must be text")
        return {"output": output, "usage": data.get("usage"), "adapter": "openai-compatible-v1", "tool_trace": [], "provider_metadata": {k:data[k] for k in ("model","model_revision","runtime") if k in data}}
    if provider == "ollama":
        data = _post(endpoint + "/api/chat", {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False, "format": "json", "options": {"temperature": temperature, "seed": seed, "num_predict": max_tokens}}, key, timeout)
        try:
            output = data["message"]["content"]
        except (KeyError, TypeError):
            raise AdapterError("invalid_response", "Ollama response lacks message.content")
        if not isinstance(output, str):
            raise AdapterError("invalid_response", "Ollama content must be text")
        if not valid_usage({k:data.get(k) for k in ("prompt_eval_count","eval_count")}):
            raise AdapterError("invalid_response","Ollama usage must contain nonnegative finite numbers")
        return {"output": output, "usage": {"prompt_tokens": data.get("prompt_eval_count"), "completion_tokens": data.get("eval_count")}, "adapter": "ollama-chat-v1", "tool_trace": []}
    if provider == "custom":
        data = _post(endpoint, {"protocol": "praxis.model.v1", "model": model, "input": prompt, "seed": seed, "max_tokens": max_tokens}, key, timeout)
        if "output" not in data:
            raise AdapterError("invalid_response", "Custom response requires output")
        return {"output": data["output"], "usage": data.get("usage"), "adapter": "custom-http-v1", "tool_trace": []}
    raise AdapterError("unsupported_provider", "Unsupported provider")

def diagnose(target):
    start = time.monotonic()
    task = {"prompt": 'Return {"ready":true}.', "output_schema": {"type": "object", "required": ["ready"]}, "passing_fixture": {"ready": True}, "failing_fixture": {"ready": False}}
    try:
        if target.get("kind")=="application":
            from .application import invoke_application
            response=invoke_application(target,{"api_request":{"path":"/health","method":"GET"}})
            if not 200<=response["output"]["status"]<400:
                return {"ok":False,"category":"application_http","error":"Owned application health endpoint did not succeed"}
        else:
            response = invoke(target, task)
        return {"ok": True, "provider": target.get("provider"), "demo": target.get("provider", "").startswith("demo"), "latency_ms": round((time.monotonic() - start) * 1000, 3), "adapter": response["adapter"]}
    except AdapterError as exc:
        return {"ok": False, "category": exc.category, "error": str(exc)}
