"""Versioned, bounded evaluation with independent assertions and replay metadata."""
import copy
import hashlib
import json
import math
import sys
import time
import uuid
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
                if not isinstance(check,dict) or check.get("op") not in OPERATORS or not isinstance(check.get("path", ""),str) or len(check.get("path", "")) > 256:
                    errors.append("task %s assertion outside bounded DSL" % tid)
                elif isinstance(check.get("weight",1),bool) or not isinstance(check.get("weight",1),(int,float)) or not math.isfinite(check.get("weight",1)) or not 0 < check.get("weight",1) <= 100:
                    errors.append("task %s assertion weight must be finite and positive" % tid)
    execution=suite.get("execution",{})
    if not isinstance(execution,dict):
        errors.append("execution must be an object")
    else:
        for key,low,high in (("max_wall_seconds",1,600),("max_scenario_count",1,64),("max_output_tokens",1,8192),("max_retries",0,2)):
            if key in execution and (isinstance(execution[key],bool) or not isinstance(execution[key],(int,float)) or not math.isfinite(execution[key]) or not low<=execution[key]<=high):
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
    events=[]
    def emit(kind, **fields):
        event={"sequence":len(events),"type":kind,"elapsed_ms":round((time.monotonic()-started)*1000,3),**fields}
        events.append(event)
        if on_event:
            on_event(event)
    safe_target={k:v for k,v in target.items() if k not in ("key","api_key","token","secret","password")}
    result={"id":str(uuid.uuid4()),"runner_version":__version__,"adapter_version":"1","target_id":target.get("id"),"target_name":target.get("name",target.get("model","Demo fixture")),"target_kind":target.get("kind","model"),"model_config_hash":digest(safe_target),"suite_slug":suite["slug"],"suite_version":suite["version"],"suite_hash":digest(suite),"seed":seed,"trust":"demo" if target.get("provider","demo").startswith("demo") else "self-reported","tasks":[],"events":events,"cost":{"status":"unknown","estimated_usd":None},"usage":{},"status":"running"}
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
        for attempt in range(retries+1):
            attempts=attempt+1
            try:
                bounded_target={**target,"timeout":min(float(target.get("timeout",20)),max(0.1,wall-(time.monotonic()-started)))}
                response=invoke_application(bounded_target,task,seed) if target.get("kind")=="application" else invoke_agent(bounded_target,task,seed) if target.get("kind")=="agent" else invoke(bounded_target,task,seed)
                error=None
                break
            except AdapterError as exc:
                error={"category":exc.category,"message":str(exc)}
                emit("attempt_failed",task_id=task["id"],attempt=attempts,category=exc.category)
                if exc.category not in ("timeout","connection_error","http_error"):
                    break
            except (TypeError,ValueError) as exc:
                error={"category":"configuration","message":"Invalid numeric adapter configuration"}
                break
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
        row={"id":task["id"],"prompt":task["prompt"],"category":task.get("category","correctness"),"output":response["output"],"assertions":assertions,"passed":all(a["passed"] for a in assertions),"latency_ms":round((time.monotonic()-begin)*1000,3),"attempts":attempts,"error":error,"usage":response.get("usage"),"tool_trace":response.get("tool_trace",[]),"artifact":{"type":"json" if isinstance(response["output"],(dict,list)) else "text","mime":"application/json" if isinstance(response["output"],(dict,list)) else "text/plain","hash":digest(response["output"])}}
        result["tasks"].append(row)
        emit("task_completed",task_id=task["id"],passed=row["passed"],latency_ms=row["latency_ms"])
    if result["status"]=="running":
        result["status"]="completed"
    rows=result["tasks"]
    total=len(suite["tasks"])
    passed=sum(t["passed"] for t in rows)
    latencies=sorted(t["latency_ms"] for t in rows)
    assertions=[a for t in rows for a in t["assertions"]]
    weight=sum(a["weight"] for a in assertions)
    dimensions={}
    for category in sorted(set(t["category"] for t in rows)):
        group=[t for t in rows if t["category"]==category]
        dimensions[category]={"passed":sum(t["passed"] for t in group),"total":len(group)}
    result["summary"]={"passed":passed,"total":total,"executed":len(rows),"not_run":total-len(rows),"failed":len(rows)-passed,"pass_rate":passed/total,"assertions_passed":sum(a["passed"] for a in assertions),"assertions_total":len(assertions),"weighted_assertion_rate":sum(a["weight"] for a in assertions if a["passed"])/weight if weight else 0,"confidence_interval":_wilson(passed,total),"latency_p50_ms":latencies[len(latencies)//2] if latencies else None,"latency_p95_ms":latencies[min(len(latencies)-1,math.ceil(len(latencies)*.95)-1)] if latencies else None,"dimensions":dimensions}
    result["duration_ms"]=round((time.monotonic()-started)*1000,3)
    emit("run_completed",status=result["status"],passed=passed,total=total)
    result["evidence_hash"]=digest({k:v for k,v in result.items() if k!="evidence_hash"})
    return result
