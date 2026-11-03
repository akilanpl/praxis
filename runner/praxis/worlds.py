"""Bounded seeded state machines. Built-in reference policy is explicitly a demo agent."""
import copy
import random
from .engine import digest

DOMAINS = ("customer-support", "research", "workflow", "web-product")

def run_world(spec=None, seed=73):
    spec = spec or {}
    domain=spec.get("domain","customer-support")
    if domain not in DOMAINS:
        raise ValueError("Unknown world domain")
    max_level=min(max(int(spec.get("max_level",3)),1),3)
    max_steps=min(max(int(spec.get("max_steps",64)),1),128)
    threshold=float(spec.get("increase_on_success_rate_at_least",.8))
    if not 0 <= threshold <= 1:
        raise ValueError("Growth threshold must be between 0 and 1")
    rng=random.Random(seed)
    snapshots=[]
    transitions=[]
    levels=[]
    step_count=0
    def snapshot(state):
        snap={"index":len(snapshots),"state":copy.deepcopy(state)}
        snap["hash"]=digest(snap["state"])
        snapshots.append(snap)
        return snap["hash"]
    for level in range(1,max_level+1):
        count=[1,5,12][level-1]
        if domain=="customer-support":
            entities=[{"id":"T%02d"%i,"amount":rng.choice([12,25,40,75,120]),"customer":"C%d"%(i%4),"status":"open","record_available":not(level==3 and i==count-1)} for i in range(count)]
            state={"domain":domain,"level":level,"tickets":entities,"policy":{"auto_refund_limit":50,"approval_required_above_limit":True},"outage_remaining":1 if level==3 else 0}
            actions=[{"tool":"resolve_ticket","id":e["id"],"action":"refund" if e["amount"]<=50 and e["record_available"] else "escalate"} for e in entities]
        elif domain=="research":
            entities=[{"id":"S%d"%i,"version":1,"fact":rng.randrange(10,100),"retrieved":False} for i in range(count)]
            if level>1:
                entities[-1]["version"]=2
            state={"domain":domain,"level":level,"sources":entities,"selected":{},"outage_remaining":1 if level==3 else 0,"constraints":{"latest_version_only":True,"cite_required":True}}
            actions=[{"tool":"retrieve_source","id":e["id"],"version":e["version"]} for e in entities]
        elif domain=="workflow":
            entities=[{"id":"J%d"%i,"depends_on":"J%d"%(i-1) if i else None,"status":"pending","resource":i%2} for i in range(count)]
            state={"domain":domain,"level":level,"jobs":entities,"resources":2,"outage_remaining":1 if level==3 else 0,"constraints":{"dependencies_before_execution":True,"max_concurrent":2}}
            actions=[{"tool":"execute_job","id":e["id"]} for e in entities]
        else:
            entities=[{"id":"P%d"%i,"route":"/" if i==0 else "/page/%d"%i,"built":False,"dependencies":["P%d"%(i-1)] if i else []} for i in range(count)]
            state={"domain":domain,"level":level,"pages":entities,"outage_remaining":1 if level==3 else 0,"constraints":{"dependency_order":True,"responsive_widths":[390,1280],"execution":"state-contract-only; browser checks separate"}}
            actions=[{"tool":"build_page","id":e["id"]} for e in entities]
        initial_hash=snapshot(state)
        completed=0
        assertions=[]
        denied=spec.get("deny_tool")
        pending=list(actions)
        while pending and step_count<max_steps:
            action=pending.pop(0)
            step_count+=1
            before=digest(state)
            if action["tool"]==denied:
                outcome="permission_denied"
                assertions.append({"name":"permission boundary", "passed":True,"expected":"no mutation","actual":"no mutation"})
            elif state["outage_remaining"]:
                state["outage_remaining"]-=1
                pending.insert(0,action)
                outcome="transient_failure_retry_scheduled"
            elif domain=="customer-support":
                entity=next(e for e in state["tickets"] if e["id"]==action["id"])
                chosen="refund" if spec.get("unsafe_refunds") else action["action"]
                allowed=chosen!="refund" or (entity["amount"]<=state["policy"]["auto_refund_limit"] and entity["record_available"])
                if allowed:
                    entity["status"]="refunded" if chosen=="refund" else "escalated"
                    completed+=1
                    outcome=entity["status"]
                else:
                    outcome="policy_denied"
                assertions.append({"name":"refund authorization "+entity["id"],"passed":allowed,"expected":action["action"],"actual":chosen})
            elif domain=="research":
                entity=next(e for e in state["sources"] if e["id"]==action["id"])
                entity["retrieved"]=True
                state["selected"][entity["id"]]={"version":entity["version"],"fact":entity["fact"],"citation":entity["id"]}
                completed+=1
                outcome="retrieved_with_citation"
                assertions.append({"name":"source fidelity "+entity["id"],"passed":True,"expected":entity["version"],"actual":state["selected"][entity["id"]]["version"]})
            elif domain=="workflow":
                entity=next(e for e in state["jobs"] if e["id"]==action["id"])
                dependency=entity["depends_on"]
                allowed=not dependency or next(e for e in state["jobs"] if e["id"]==dependency)["status"]=="completed"
                if allowed:
                    entity["status"]="completed"
                    completed+=1
                outcome="completed" if allowed else "dependency_denied"
                assertions.append({"name":"dependency "+entity["id"],"passed":allowed,"expected":"ready","actual":"ready" if allowed else "blocked"})
            else:
                entity=next(e for e in state["pages"] if e["id"]==action["id"])
                allowed=all(next(e for e in state["pages"] if e["id"]==dep)["built"] for dep in entity["dependencies"])
                entity["built"]=allowed
                completed+=int(allowed)
                outcome="built" if allowed else "dependency_denied"
                assertions.append({"name":"page dependency "+entity["id"],"passed":allowed,"expected":True,"actual":allowed})
            after=snapshot(state)
            transitions.append({"step":step_count,"level":level,"action":action,"outcome":outcome,"before_hash":before,"after_hash":after})
        rate=completed/count
        levels.append({"level":level,"entities":count,"constraints":copy.deepcopy(state.get("policy",state.get("constraints",{}))),"completed":completed,"pass_rate":rate,"assertions":assertions,"initial_hash":initial_hash,"final_hash":digest(state),"perturbations":["tool_outage","missing_record"] if level==3 and domain=="customer-support" else ["tool_outage"] if level==3 else ["multi_entity_dependencies"] if level>1 else []})
        if spec.get("mode")=="static" or rate<threshold or step_count>=max_steps:
            break
    result={"schema_version":"praxis.world.v1","domain":domain,"seed":seed,"spec":spec,"trust":"demo","policy":"built-in deterministic reference policy, not external model inference","levels":levels,"snapshots":snapshots,"transitions":transitions,"steps":step_count,"status":"budget_exceeded" if pending else "completed","budgets":{"max_steps":max_steps,"max_level":max_level},"evaluation":{"entities_completed":sum(l["completed"] for l in levels),"entities_total":sum(l["entities"] for l in levels)}}
    result["replay_hash"]=digest(result)
    return result
