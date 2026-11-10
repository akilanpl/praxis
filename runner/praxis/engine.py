"""Versioned, bounded evaluation with independent assertions and replay metadata."""
import copy
import hashlib
import json
import math
import os
import re
import sys
import time
import uuid
from urllib.parse import urlparse
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator, ValidationError
from . import __version__
from .adapters import AdapterError, invoke
from .agent import invoke_agent
from .application import invoke_application

SCENARIOS = Path(__file__).resolve().parents[2] / "packages" / "scenarios"
if not SCENARIOS.is_dir():
    SCENARIOS = Path(sys.prefix) / "share" / "praxis" / "scenarios"
OPERATORS = {"equals", "contains", "not_contains", "subset", "gte", "lte"}

def redact_payload(value, credential):
    """Redact untrusted values/keys without silently collapsing distinct keys."""
    if not credential: return value
    if isinstance(value,str): return value.replace(credential,"[REDACTED]")
    if isinstance(value,list): return [redact_payload(v,credential) for v in value]
    if isinstance(value,dict):
        keys=[str(k).replace(credential,"[REDACTED]") for k in value]
        if len(set(keys))!=len(keys): return "[REDACTED: colliding object keys]"
        return {k:redact_payload(v,credential) for k,v in zip(keys,value.values())}
    return value

def redact_values(value, credential):
    """Keep the report protocol's structural field names stable."""
    if not credential: return value
    if isinstance(value,str): return value.replace(credential,"[REDACTED]")
    if isinstance(value,list): return [redact_values(v,credential) for v in value]
    if isinstance(value,dict):
        protocol={"status":{"running","completed","cancelled","budget_exceeded"},"trust":{"demo","self-reported"},"target_kind":{"model","agent","application"}}
        hashes={"hash","sha256","model_config_hash","suite_hash"}
        return {k:v if k in hashes or (k in protocol and isinstance(v,str) and v in protocol[k]) else redact_values(v,credential) for k,v in value.items()}
    return value

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def list_suites():
    return [json.loads(p.read_text()) for p in sorted(SCENARIOS.glob("*-v1.json"))]

def validate_suite(suite):
    errors = []
    if not isinstance(suite,dict):
        return {"valid":False,"errors":["suite must be an object"]}
    for key in ("slug", "version", "title"):
        if not isinstance(suite.get(key), str) or not suite[key] or len(suite[key]) > 120:
            errors.append("%s must be a nonempty string <=120 characters" % key)
    if isinstance(suite.get("slug"),str) and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}",suite["slug"]): errors.append("slug must use lowercase letters, digits and hyphens, at most 100 characters")
    if isinstance(suite.get("version"),str) and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,39}",suite["version"]): errors.append("version must be a route-safe identifier of at most 40 characters")
    tasks = suite.get("tasks", [])
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 64:
        errors.append("tasks must contain 1..64 scenarios")
        return {"valid": False, "errors": errors}
    ids = set()
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append("task %d must be an object" % i)
            continue
        tid = task.get("id")
        if not isinstance(tid,str) or not tid or tid in ids:
            errors.append("task IDs must be nonempty unique strings")
        ids.add(str(tid))
        if not isinstance(task.get("prompt"),str) or not task["prompt"] or len(task["prompt"]) > 100000:
            errors.append("task %s prompt invalid" % tid)
        if not isinstance(task.get("category","correctness"),str) or not 1<=len(task.get("category","correctness"))<=120:
            errors.append("task category must be a nonempty string of at most 120 characters")
        if "max_steps" in task and (type(task["max_steps"]) is not int or not 1 <= task["max_steps"] <= 16):
            errors.append("agent max_steps must be an integer in 1..16")
        if "allowed_tools" in task and (not isinstance(task["allowed_tools"],list) or any(not isinstance(t,str) for t in task["allowed_tools"])):
            errors.append("allowed_tools must be an array of names")
        if "environment" in task and not isinstance(task["environment"],dict):
            errors.append("environment must be an object")
        if "api_request" in task:
            request=task["api_request"]
            if not isinstance(request,dict) or request.get("method","GET") not in ("GET","POST") or not isinstance(request.get("path","/"),str):
                errors.append("api_request requires an object, GET/POST method and string path")
        schema = task.get("output_schema", {})
        try:
            Draft202012Validator.check_schema(schema)
        except Exception:
            errors.append("task %s invalid JSON schema" % tid)
        if "$ref" in json.dumps(schema):
            errors.append("external/schema references are not accepted")
        checks = task.get("assertions", [])
        state_checks=task.get("state_assertions", [])
        if not isinstance(checks,list) or not isinstance(state_checks,list):
            errors.append("task %s assertions must be arrays" % tid)
            continue
        checks=checks+state_checks
        if not isinstance(checks, list) or not 1 <= len(checks) <= 32:
            errors.append("task %s requires 1..32 assertions" % tid)
        else:
            for check in checks:
                if not isinstance(check,dict) or not isinstance(check.get("op"),str) or check.get("op") not in OPERATORS or not isinstance(check.get("path", ""),str) or len(check.get("path", "")) > 256:
                    errors.append("task %s assertion outside bounded DSL" % tid)
                elif "expected" not in check or (check["op"] in ("gte","lte") and (type(check["expected"]) not in (int,float) or not math.isfinite(check["expected"]))):
                    errors.append("assertions require expected; numeric comparisons require finite numbers")
                elif isinstance(check.get("weight",1),bool) or not isinstance(check.get("weight",1),(int,float)) or not math.isfinite(check.get("weight",1)) or not 0 < check.get("weight",1) <= 100:
                    errors.append("task %s assertion weight must be finite and positive" % tid)
    execution=suite.get("execution",{})
    if not isinstance(execution,dict):
        errors.append("execution must be an object")
    else:
        for key,low,high in (("max_wall_seconds",1,600),("max_scenario_count",1,64),("max_output_tokens",1,8192),("max_retries",0,2)):
            if key in execution and (isinstance(execution[key],bool) or not isinstance(execution[key],(int,float)) or not math.isfinite(execution[key]) or not low<=execution[key]<=high or (key != "max_wall_seconds" and type(execution[key]) is not int)):
                errors.append("execution %s must be in %s..%s"%(key,low,high))
    return {"valid": not errors, "errors": errors}

def _lookup(output, path):
    value = output
    for key in path.split(".") if path else []:
        if isinstance(value,list) and key.isdigit():
            value = value[int(key)]
        else:
            value = value[key]
    return value

def grade(task, output):
    if isinstance(output,str):
        try:
            parsed = json.loads(output)
        except ValueError:
            parsed = output
    else:
        parsed = output
    assertions = []
    schema_errors = list(Draft202012Validator(task.get("output_schema",{})).iter_errors(parsed))
    assertions.append({"name":"JSON schema", "passed":not schema_errors,"expected":task.get("output_schema",{}),"actual": parsed if schema_errors else "valid", "weight":1})
    for check in task.get("assertions",[]):
        expected = check.get("expected")
        try:
            actual = _lookup(parsed, check.get("path", ""))
            op = check["op"]
            if op == "equals":
                passed = type(actual) is type(expected) and actual == expected
            elif op == "contains":
                passed = expected in actual
            elif op == "not_contains":
                passed = expected not in actual
            elif op == "subset":
                passed = all(v in actual for v in expected)
            elif op == "gte":
                passed = isinstance(actual,(int,float)) and not isinstance(actual,bool) and actual >= expected
            else:
                passed = isinstance(actual,(int,float)) and not isinstance(actual,bool) and actual <= expected
        except (KeyError,IndexError,TypeError,ValueError):
            actual, passed = None, False
        assertions.append({"name":check.get("name",check.get("path","assertion")),"passed":bool(passed),"expected":expected,"actual":actual,"weight":check.get("weight",1)})
    return assertions

def _wilson(passed,total):
    if not total:
        return [0,1]
    z=1.96
    p=passed/total
    mid=(p+z*z/(2*total))/(1+z*z/total)
    half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/(1+z*z/total)
    return [round(max(0,mid-half),4),round(min(1,mid+half),4)]

def execute_run(target:Dict[str,Any],suite:Dict[str,Any],seed:int=73,on_event=None,cancelled=None):
    validation = validate_suite(suite)
    if not validation["valid"]:
        raise ValueError("Invalid suite: " + "; ".join(validation["errors"]))
    started=time.monotonic()
    credential=os.environ.get(target.get("key_env","PRAXIS_MODEL_API_KEY"))
    events=[]
    def emit(kind, **fields):
        event={"sequence":len(events),"type":kind,"elapsed_ms":round((time.monotonic()-started)*1000,3),**fields}
        events.append(event)
        if on_event:
            on_event(event)
    safe_target={k:v for k,v in target.items() if k in ("id","name","kind","provider","model","capabilities","max_tokens","temperature","timeout","allow_mutation","authorized","supports_seed")}
    endpoint=target.get("endpoint","")
    try:
        parsed=urlparse(endpoint)
        safe_target["endpoint"]=endpoint if parsed.scheme in ("http","https") and parsed.hostname and not (parsed.username or parsed.password or parsed.query or parsed.fragment) else "[invalid or absent endpoint]"
    except (ValueError,TypeError): safe_target["endpoint"]="[invalid endpoint]"
    result={"id":str(uuid.uuid4()),"runner_version":__version__,"adapter_version":"1","target_id":target.get("id"),"target_name":target.get("name",target.get("model","Demo fixture")),"target_kind":target.get("kind","model"),"model_config_hash":digest(safe_target),"suite_slug":suite["slug"],"suite_version":suite["version"],"suite_hash":digest(suite),"seed":seed,"trust":"demo" if target.get("provider","demo").startswith("demo") else "self-reported","tasks":[],"events":events,"cost":{"status":"unknown","estimated_usd":None},"usage":{},"status":"running"}
    result["configuration"]={"target":safe_target,"execution":copy.deepcopy(suite.get("execution",{}))}
    emit("run_started",suite=suite["slug"],seed=seed)
    limits=suite.get("execution",{})
    wall=min(max(float(limits.get("max_wall_seconds",120)),1),600)
    for task in suite["tasks"][:min(int(limits.get("max_scenario_count",64)),64)]:
        if cancelled and cancelled():
            result["status"]="cancelled"
            emit("run_cancelled")
            break
        if time.monotonic()-started > wall:
            result["status"]="budget_exceeded"
            emit("budget_exceeded",budget="wall_seconds")
            break
        begin=time.monotonic()
        emit("task_started",task_id=task["id"])
        error=None
        response={"output":None,"usage":None,"tool_trace":[]}
        attempts=0
        retries=min(max(int(limits.get("max_retries",0)),0),2)
        if target.get("kind")=="application" and task.get("api_request",{}).get("method","GET")!="GET":
            retries=0  # A timed-out POST may already have mutated the owned service.
        for attempt in range(retries+1):
            if (cancelled and cancelled()) or time.monotonic()-started >= wall:
                error={"category":"cancelled" if cancelled and cancelled() else "timeout","message":"Execution stopped before another attempt"}
                break
            attempts=attempt+1
            try:
                bounded_target={**target,"timeout":min(float(target.get("timeout",20)),max(0.1,wall-(time.monotonic()-started)))}
                bounded_target["max_tokens"]=min(int(target.get("max_tokens",1024)),int(limits.get("max_output_tokens",8192)))
                response=invoke_application(bounded_target,task,seed) if target.get("kind")=="application" else invoke_agent(bounded_target,task,seed) if target.get("kind")=="agent" else invoke(bounded_target,task,seed)
                error=None
                break
            except AdapterError as exc:
                response.update(getattr(exc,"evidence",{}))
                error={"category":exc.category,"message":str(exc)}
                emit("attempt_failed",task_id=task["id"],attempt=attempts,category=exc.category)
                if exc.category not in ("timeout","connection_error","http_error"):
                    break
            except (TypeError,ValueError) as exc:
                error={"category":"configuration","message":"Invalid numeric adapter configuration"}
                break
        for key in ("output","provider_metadata","final_state","usage"):
            if key in response: response[key]=redact_payload(response[key],credential)
        for event in response.get("tool_trace",[]):
            for key in ("arguments","observation","state_before","state_after","output"):
                if key in event: event[key]=redact_payload(event[key],credential)
        assertions=grade(task,response["output"]) if error is None else [{"name":"Provider execution","passed":False,"expected":"successful output","actual":error,"weight":1}]
        if error is None and task.get("api_request") and target.get("kind")!="application":
            assertions.append({"name":"Executable application required","passed":False,"expected":"application HTTP execution","actual":"model output only","weight":1})
        if error is None and task.get("environment"):
            if target.get("kind")!="agent":
                assertions.append({"name":"Executable agent required","passed":False,"expected":"agent tool execution","actual":"model output only","weight":1})
            else:
                state_checks=grade({"output_schema":{"type":"object"},"assertions":task.get("state_assertions",[])},response.get("final_state",{}))[1:]
                assertions.extend(state_checks)
                unauthorized=[t for t in response.get("tool_trace",[]) if t.get("type")=="tool_call" and not t.get("authorized")]
                assertions.append({"name":"Allowed tool usage","passed":not unauthorized,"expected":[],"actual":[t.get("tool") for t in unauthorized],"weight":1})
        row={"id":task["id"],"prompt":task["prompt"],"category":task.get("category","correctness"),"output":response["output"],"assertions":assertions,"passed":all(a["passed"] for a in assertions),"latency_ms":round((time.monotonic()-begin)*1000,3),"attempts":attempts,"error":error,"usage":response.get("usage"),"provider_metadata":response.get("provider_metadata",{}),"tool_trace":response.get("tool_trace",[]),"artifact":{"type":"json" if isinstance(response["output"],(dict,list)) else "text","mime":"application/json" if isinstance(response["output"],(dict,list)) else "text/plain","hash":digest(response["output"])}}
        result["tasks"].append(row)
        emit("task_completed",task_id=task["id"],passed=row["passed"],latency_ms=row["latency_ms"])
    if result["status"]=="running":
        result["status"]="cancelled" if cancelled and cancelled() else "budget_exceeded" if time.monotonic()-started >= wall else "completed"
    rows=result["tasks"]
    for row in rows:
        for key,value in (row.get("usage") or {}).items() if isinstance(row.get("usage"),dict) else []:
            if type(value) in (int,float) and math.isfinite(value) and value >= 0:
                result["usage"][key]=result["usage"].get(key,0)+value
    result["not_run_tasks"]=[{"id":t["id"],"category":t.get("category","correctness"),"reason":result["status"] if result["status"]!="completed" else "scenario_limit"} for t in suite["tasks"][len(rows):]]
    total=len(suite["tasks"])
    passed=sum(t["passed"] for t in rows)
    latencies=sorted(t["latency_ms"] for t in rows)
    assertions=[a for t in rows for a in t["assertions"]]
    weight=sum(a["weight"] for a in assertions)
    dimensions={}
    for category in sorted(set(t.get("category","correctness") for t in suite["tasks"])):
        group=[t for t in rows if t["category"]==category]
        dimension_total=sum(t.get("category","correctness")==category for t in suite["tasks"])
        dimensions[category]={"passed":sum(t["passed"] for t in group),"total":dimension_total,"executed":len(group),"not_run":dimension_total-len(group)}
    result["summary"]={"passed":passed,"total":total,"executed":len(rows),"not_run":total-len(rows),"failed":len(rows)-passed,"pass_rate":passed/total,"assertions_passed":sum(a["passed"] for a in assertions),"assertions_total":len(assertions),"weighted_assertion_rate":sum(a["weight"] for a in assertions if a["passed"])/weight if weight else 0,"confidence_interval":_wilson(passed,total),"latency_p50_ms":latencies[len(latencies)//2] if latencies else None,"latency_p95_ms":latencies[min(len(latencies)-1,math.ceil(len(latencies)*.95)-1)] if latencies else None,"dimensions":dimensions}
    result["duration_ms"]=round((time.monotonic()-started)*1000,3)
    emit("run_completed",status=result["status"],passed=passed,total=total)
    # Providers may reflect the authorization credential in output/usage/metadata.
    # Preserve the redaction in the hashed record, never persist the credential.
    if credential:
        for row in result["tasks"]:
            for assertion in row["assertions"]:
                for field in ("expected","actual"): assertion[field]=redact_payload(assertion.get(field),credential)
        result=redact_values(result,credential)
        for row in result["tasks"]:
            row["artifact"]["hash"]=digest(row["output"])
    result["evidence_hash"]=digest({k:v for k,v in result.items() if k!="evidence_hash"})
    return result
