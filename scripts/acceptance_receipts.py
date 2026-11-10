"""A process exit code cannot substitute for current-source acceptance evidence."""
import json
from pathlib import Path

def accepted_receipt(path,commit,minimum=1):
    try:value=json.loads(Path(path).read_text())
    except (OSError,ValueError):return False,{'status':'failed','checks':[],'error':'Missing or invalid receipt'}
    if not isinstance(value,dict):return False,{'status':'failed','checks':[],'error':'Receipt must be an object'}
    checks=value.get('checks',[])
    accepted=(value.get('status')=='passed' and value.get('source_commit')==commit and value.get('source_dirty') is False and isinstance(checks,list) and len(checks)>=minimum and all(isinstance(c,dict) and c.get('passed') is True for c in checks))
    return accepted,value
