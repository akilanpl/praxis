"""User-controlled model connections. Credentials never enter results or configuration."""
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict

MAX_RESPONSE_BYTES = 2 * 1024 * 1024

class AdapterError(RuntimeError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category = category

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AdapterError("redirect_denied", "Provider redirects are not accepted")

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
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=timeout) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise AdapterError("response_limit", "Provider response exceeds 2 MiB")
            return json.loads(data)
    except urllib.error.HTTPError as exc:
        raise AdapterError("http_error", "Provider returned HTTP %s" % exc.code) from None
    except urllib.error.URLError as exc:
        timeout_error=isinstance(exc.reason,(TimeoutError,socket.timeout))
        raise AdapterError("timeout" if timeout_error else "connection_error", "Provider connection failed or timed out") from None
    except (TimeoutError, OSError) as exc:
        raise AdapterError("timeout" if isinstance(exc, (TimeoutError, socket.timeout)) else "connection_error", "Provider connection failed or timed out") from None
    except (ValueError, KeyError):
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
    timeout = min(max(float(target.get("timeout", 20)), 0.1), 120)
    max_tokens = min(max(int(target.get("max_tokens", 1024)), 1), 8192)
    key_name = target.get("key_env", "PRAXIS_MODEL_API_KEY")
    key = os.environ.get(key_name)
    if provider == "openai":
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": float(target.get("temperature", 0))}
        if target.get("supports_seed") is True:
            payload["seed"] = seed
        data = _post(endpoint + "/chat/completions", payload, key, timeout)
        try:
            output = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise AdapterError("invalid_response", "OpenAI-compatible response lacks choices.message.content")
        return {"output": output, "usage": data.get("usage"), "adapter": "openai-compatible-v1", "tool_trace": [], "provider_metadata": {k:data[k] for k in ("model","model_revision","runtime") if k in data}}
    if provider == "ollama":
        data = _post(endpoint + "/api/chat", {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False, "format": "json", "options": {"temperature": float(target.get("temperature", 0)), "seed": seed, "num_predict": max_tokens}}, key, timeout)
        try:
            output = data["message"]["content"]
        except (KeyError, TypeError):
            raise AdapterError("invalid_response", "Ollama response lacks message.content")
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
