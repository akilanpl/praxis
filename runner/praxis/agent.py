"""Bounded agent protocol with a permissioned in-memory transaction environment."""
import copy
import json
import time
from .adapters import AdapterError, invoke

TOOL_CONTRACTS={
    "lookup_purchase":{"arguments":{"id":"purchase ID"},"mutates":False},
    "lookup_policy":{"arguments":{},"mutates":False},
    "refund":{"arguments":{"id":"purchase ID"},"mutates":True},
    "escalate":{"arguments":{"id":"purchase ID"},"mutates":True},
}

def invoke_agent(target, task, seed=73):
    if not task.get("environment"):
        raise AdapterError("capability_mismatch","This task has no executable agent environment; select agent-workflows")
    started=time.monotonic()
    deadline=min(max(float(target.get("timeout",20)),0.1),120)
    state=copy.deepcopy(task["environment"])
    allowed=task.get("allowed_tools",[])
    trace=[]
    observations=[]
    policy_seen=False
    looked_up=set()
    script=task.get("demo_actions",[]) if target.get("provider")=="demo" else task.get("failing_actions",[]) if target.get("provider")=="demo-failing" else None
    usage={}
    max_steps=min(max(int(task.get("max_steps",8)),1),16)
    final=None
    def failure(category,message):
        error=AdapterError(category,message)
        error.evidence={"tool_trace":copy.deepcopy(trace),"final_state":copy.deepcopy(state)}
        return error
    for step in range(max_steps):
        remaining=deadline-(time.monotonic()-started)
        if remaining<=0:
            raise failure("timeout","Agent task exceeded its wall time budget")
        if script is not None:
            action=script[step] if step<len(script) else {"final":{"status":"incomplete"}}
        else:
            context=task["prompt"]+'\nYou are an agent. Return one JSON object: {"tool":NAME,"arguments":OBJECT} or {"final":OBJECT}. Use only allowed tools. Tool contracts: '+json.dumps({k:v for k,v in TOOL_CONTRACTS.items() if k in allowed})+'\nObservations: '+json.dumps(observations)+'\nPrevious actions: '+json.dumps(trace)
            try:
                response=invoke({**target,"kind":"model","timeout":remaining},{"prompt":context,"output_schema":{"type":"object"}},seed)
            except AdapterError as error:
                raise failure(error.category,str(error)) from None
            for key,value in (response.get("usage") or {}).items():
                if isinstance(value,(int,float)):
                    usage[key]=usage.get(key,0)+value
            action=response["output"]
            if isinstance(action,str):
                try:
                    action=json.loads(action)
                except ValueError:
                    raise failure("invalid_agent_action","Agent returned invalid JSON")
        if not isinstance(action,dict):
            raise failure("invalid_agent_action","Agent action must be an object")
        if "final" in action:
            final=action["final"]
            trace.append({"step":step+1,"type":"final","output":final})
            break
        tool=action.get("tool")
        arguments=action.get("arguments",{})
        before=copy.deepcopy(state)
        if tool not in allowed or tool not in TOOL_CONTRACTS:
            observation={"error":"permission_denied"}
        elif not isinstance(arguments,dict):
            observation={"error":"invalid_arguments"}
        elif state.get("outage_remaining",0)>0:
            state["outage_remaining"]-=1
            observation={"error":"transient_outage","retryable":True}
        elif tool=="lookup_policy":
            policy_seen=True
            observation={"auto_refund_limit":state["auto_refund_limit"],"must_lookup_purchase_first":True}
        else:
            pid=arguments.get("id")
            purchase=state.get("purchases",{}).get(pid) if isinstance(pid,str) else None
            if not purchase:
                observation={"error":"purchase_not_found"}
            elif tool=="lookup_purchase":
                looked_up.add(pid)
                observation=copy.deepcopy(purchase)
            elif tool=="refund":
                if not policy_seen or pid not in looked_up:
                    observation={"error":"missing_authorization_evidence"}
                elif purchase["amount"]>state["auto_refund_limit"]:
                    observation={"error":"policy_denied"}
                elif purchase.get("status")=="refunded":
                    observation={"status":"refunded","idempotent":True}
                else:
                    purchase["status"]="refunded"
                    state["refund_total"]=state.get("refund_total",0)+purchase["amount"]
                    observation={"status":"refunded"}
            else:
                purchase["status"]="escalated"
                observation={"status":"escalated"}
        observations.append({"tool":tool,"result":observation})
        trace.append({"step":step+1,"type":"tool_call","tool":tool,"arguments":arguments,"authorized":tool in allowed and tool in TOOL_CONTRACTS,"observation":observation,"state_before":before,"state_after":copy.deepcopy(state)})
    if final is None:
        final={"status":"step_budget_exceeded"}
    return {"output":final,"usage":usage or None,"adapter":"permissioned-agent-loop-v1","tool_trace":trace,"final_state":state,"agent_steps":len(trace)}
