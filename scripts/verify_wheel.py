"""Install the built runner away from the checkout and execute bundled suites."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
folder=Path(tempfile.mkdtemp(prefix='wheel-release-',dir=str(ROOT/'work')))
subprocess.run([sys.executable,'-m','venv','--without-pip',str(folder)],check=True)
python=folder/'bin/python'
wheel=ROOT/'dist/runner/praxis-0.1.0-py3-none-any.whl'
subprocess.run([sys.executable,'-m','pip','--python',str(python),'install','--no-deps','--no-index',str(wheel)],check=True)
env=dict(os.environ,PYTHONPATH=str(ROOT/'.venv/lib'/('python%d.%d'%sys.version_info[:2])/'site-packages'),PYTHONPYCACHEPREFIX=str(ROOT/'work/pycache'))
code='''import json,praxis
from praxis.engine import list_suites,execute_run
from praxis.worlds import run_world
assert "wheel-release-" in praxis.__file__,praxis.__file__
suites=list_suites()
assert len(suites)==6 and sum(len(s["tasks"]) for s in suites)==40
for slug,kind,count in [("structured-agent","model",8),("agent-workflows","agent",4)]:
 result=execute_run({"provider":"demo","kind":kind},next(s for s in suites if s["slug"]==slug))
 assert result["summary"]["passed"]==count
assert [l["entities"] for l in run_world({})["levels"]]==[1,5,12]
print(json.dumps({"status":"passed","suites":6,"scenarios_loaded":40,"fixture_tasks_executed":12,"world_entity_levels":[1,5,12],"scope":"isolated installed package; locked dependencies reused locally; no model inference"}))
'''
r=subprocess.run([str(python),'-c',code],cwd=folder,env=env,text=True,capture_output=True,check=True)
print(r.stdout)
out=Path(os.environ.get('PRAXIS_EVIDENCE_DIR',str(ROOT/'evidence/release')));out.mkdir(parents=True,exist_ok=True)
(out/'wheel.json').write_text(r.stdout)
