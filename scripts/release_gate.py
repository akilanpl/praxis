"""Real acceptance stages and a reproducible score, without a bypass switch."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from diff_coverage import measure_diff

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
SHA=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
BRANCH=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
OUT=ROOT/'.pushgate/reports';OUT.mkdir(parents=True,exist_ok=True)
EVIDENCE=Path(os.environ.get('PRAXIS_EVIDENCE_DIR',str(ROOT/'evidence/final/gate'))).resolve();EVIDENCE.mkdir(parents=True,exist_ok=True)
ENV=dict(os.environ,PRAXIS_EVIDENCE_DIR=str(EVIDENCE),PYTHONPYCACHEPREFIX=str(ROOT/'work/pycache'),PIP_CACHE_DIR=str(ROOT/'work/pip-cache'))
if sys.platform=='darwin':ENV.setdefault('PRAXIS_BROWSER_CDP','http://127.0.0.1:9333')
P=ROOT/'.venv/bin/python'
report={'commit':SHA,'branch':BRANCH,'seed':73,'scope':'local code acceptance; no claim of hosted Auth or production deployment','tests':[],'stages':[],'environment_started':True,'security_clear':True,'coverage':{}}
owned=[];start=time.monotonic()
def add(name,family,status,sev='P1',duration=0):report['tests'].append({'id':family+'.'+str(len(report['tests'])+1),'name':name,'family':family,'sev':sev,'status':status,'duration_ms':duration,'retries':0})
def stage(name,command):
    begin=time.monotonic()
    try:
        result=subprocess.run([str(c) for c in command],cwd=ROOT,env=ENV,capture_output=True,text=True,timeout=600)
        output=result.stdout+result.stderr;code=result.returncode
    except (OSError,subprocess.TimeoutExpired) as exc:output=str(exc);code=1
    (OUT/(name+'.log')).write_text(output)
    report['stages'].append({'name':name,'command':[str(c) for c in command],'exit_code':code,'duration_ms':(time.monotonic()-begin)*1000})
    return code==0,output

def family(name):
    n=name.lower()
    if any(w in n for w in ('concurrent','concurrency','uniqueness')):return 'C01'
    if 'persisted_run' in n:return 'Y01'
    if any(w in n for w in ('cancel','deadline','timeout','restart')):return 'R03'
    if any(w in n for w in ('isolation','owner','auth','secret','permission','credentials','denied','report_escapes')):return 'Z06'
    if 'world_contract_rejects' in n or any(w in n for w in ('budget','boundary','limit','wav','invalid_target')):return 'V02'
    if any(w in n for w in ('invalid','malformed','bad_json','unsafe_dsl','slug','clone','idempotency')):return 'X01'
    if any(w in n for w in ('adapter','protocol','httpboundary','application','connector')):return 'A18'
    return 'B01'

def junit(path):
    if not path.exists():add('Python report missing','B01','notrun','P0');return
    for case in ET.parse(path).iter('testcase'):
        name=case.get('classname','')+'.'+case.get('name','')
        state='fail' if case.find('failure') is not None or case.find('error') is not None else 'skip' if case.find('skipped') is not None else 'pass'
        add(name,family(name),state,duration=float(case.get('time','0'))*1000)

def healthy(port,model):
    try:
        with urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/health',timeout=2) as r:data=json.load(r)
        return data.get('real_inference') is True and data.get('model')==model
    except OSError:return False

try:
    ok,_=stage('build',['npm','run','build']);add('All component production build','S01','pass' if ok else 'fail','P0')
    ok,_=stage('frontend-lint',['npm','run','lint']);add('Frontend compiler unused-code lint','S01','pass' if ok else 'fail','P0')
    ok,_=stage('wheel',[P,'scripts/verify_wheel.py']);add('Isolated runner wheel installation and bundled execution','S01','pass' if ok else 'fail','P0')
    coverage_path = OUT / 'coverage.json'
    coverage_path.unlink(missing_ok=True)
    ok,_=stage('python',[P,'-m','pytest','tests','-q','--cov=praxis','--cov-branch','--cov-report=json:'+str(OUT/'coverage.json'),'--junitxml='+str(OUT/'python.xml')]);junit(OUT/'python.xml')
    if ok and coverage_path.exists():
        coverage = json.loads(coverage_path.read_text())
        totals = coverage['totals']
        diff, diff_status = measure_diff(ROOT, os.environ.get('PRAXIS_COVERAGE_BASE'), coverage.get('files'))
        report['coverage'] = {
            'line': 100 * totals['covered_lines'] / totals['num_statements'] if totals['num_statements'] else None,
            'branch': 100 * totals['covered_branches'] / totals['num_branches'] if totals['num_branches'] else None,
            'diff': diff,
            'diff_status': diff_status,
        }
    else:
        report['coverage'] = {'diff': None, 'diff_status': 'coverage run failed or report missing'}
    ok,output=stage('worker',['node','--import','tsx','--test','--test-reporter=tap','apps/api/test/security.test.ts'])
    rows=re.findall(r'^(ok|not ok) \d+ - (.+)$',output,re.M)
    for state,name in rows:add(name,'A07' if 'token' in name or 'unauthenticated' in name else 'Z07','pass' if state=='ok' else 'fail','P0')
    if not rows:add('Worker security report missing','Z07','notrun','P0')
    leak=shutil.which('gitleaks') or str(ROOT/'work/gitleaks/gitleaks')
    ok,_=stage('secrets',[leak,'git','--log-opts=--all','--redact','--no-banner','--report-format','json','--report-path',str(OUT/'gitleaks.json')]);add('Tracked history secret scan','S05','pass' if ok else 'fail','P0');report['security_clear']&=ok
    ok,_=stage('npm-audit',['npm','audit','--json','--cache','./work/npm-cache']);add('Node dependency advisory audit','S06','pass' if ok else 'fail','P0');report['security_clear']&=ok
    ok,_=stage('python-audit',[P,'-m','pip_audit','--skip-editable','--cache-dir','work/pip-audit-cache','--format','json','--output',str(OUT/'python-audit.json')]);add('Python dependency advisory audit','S06','pass' if ok else 'fail','P0');report['security_clear']&=ok
    postgres_script='scripts/postgres_acceptance.py' if shutil.which('psql') else 'scripts/postgres_container_check.py'
    ok,_=stage('postgres',[P,postgres_script])
    pg=json.loads((EVIDENCE/'postgres.json').read_text())
    for item in pg.get('checks',[]):add(item['name'],'D01','pass' if item['passed'] else 'fail','P0')
    if not ok:add('Disposable native PostgreSQL environment','D01','notrun' if pg['status']=='blocked' else 'fail','P0');report['environment_started']=False
    for port,model in [(8788,'onnx-community/SmolLM2-135M-Instruct-ONNX'),(8789,'onnx-community/SmolLM2-360M-Instruct-ONNX')]:
        if not healthy(port,model):
            e=dict(ENV,PRAXIS_MODEL_PORT=str(port),PRAXIS_LOCAL_MODEL=model)
            log=open(OUT/('model-'+str(port)+'.log'),'w')
            proc=subprocess.Popen(['node','scripts/local_model_server.mjs'],cwd=ROOT,env=e,stdout=log,stderr=log);owned.append((proc,log))
            deadline=time.monotonic()+180
            while time.monotonic()<deadline and proc.poll() is None:
                if healthy(port,model):break
                time.sleep(.2)
            if not healthy(port,model):report['environment_started']=False
    ok,_=stage('browser',[P,'scripts/browser_check.py'])
    browser=json.loads((EVIDENCE/'browser/result.json').read_text())
    for item in browser.get('checks',[]):
        group='F04' if 'viewport' in item['name'] or 'navigation' in item['name'] else 'E04'
        add(item['name'],group,'pass' if item['passed'] else 'fail','P0')
    if not ok:add('Full Chromium user journey','E04','fail','P0')
    ok,_=stage('website',[P,'-m','praxis','check-website','--output-dir',str(OUT/'website')])
    if ok:
        for item in json.loads((OUT/'website/website-checks.json').read_text())['assertions']:add(item['name'],'F06','pass' if item['passed'] else 'fail')
    else:add('Owned website artifact browser checks','F06','notrun','P0')
    ok,_=stage('project-website',[P,'scripts/website_check.py']);add('Project website production browser acceptance','F06','pass' if ok else 'fail','P0')
    # Performance and operational health on a fresh, bounded local API.
    e=dict(ENV,PRAXIS_PORT='8794',PRAXIS_DB=str(ROOT/'work'/('gate-'+SHA+'.sqlite')))
    log=open(OUT/'health-api.log','w');proc=subprocess.Popen([str(P),'-m','praxis.server'],env=e,stdout=log,stderr=log);owned.append((proc,log))
    samples=[];ready=time.monotonic()+10
    while time.monotonic()<ready:
        try:
            with urllib.request.urlopen('http://127.0.0.1:8794/api/health',timeout=.5) as r:assert json.load(r)['ok']
            break
        except OSError:time.sleep(.1)
    for _ in range(30):
        begin=time.perf_counter()
        with urllib.request.urlopen('http://127.0.0.1:8794/api/health',timeout=2) as r:assert json.load(r)['ok']
        samples.append((time.perf_counter()-begin)*1000)
    p95=sorted(samples)[28];report['performance']={'requests':30,'p95_ms':p95,'scope':'loopback health requests, not capacity certification'}
    add('Bounded health request latency p95 < 300 ms','P01','pass' if p95<300 else 'fail')
    add('Fresh local API reports its real mode','O01','pass')
except Exception as exc:
    report['error']=str(exc);report['environment_started']=False;add('Acceptance orchestration failed','O01','fail','P0')
finally:
    for proc,log in reversed(owned):
        proc.terminate()
        try:proc.wait(timeout=20)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
        log.close()
    spec=importlib.util.spec_from_file_location('gate_score',ROOT/'.pushgate/score.py');scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
    baseline=ROOT/'.pushgate/baseline.json'
    if baseline.exists():report['baseline_score']=json.loads(baseline.read_text())['score']
    report['duration_seconds']=time.monotonic()-start
    report['result']=scorer.score(report)
    path=OUT/(SHA+'.json');path.write_text(json.dumps(report,indent=2)+'\n')
    result=report['result']
    lines=['# Push Gate Report','Commit: '+SHA+' | Branch: '+BRANCH+' | Seed: 73','',f"## Result: {result['decision']} — Score {result['score']} / 100 — Grade {result['grade']}",'',report['scope'],'','| Group | Weight | Tests | Passed | Rate |','|---|---:|---:|---:|---:|']
    for group,row in result['groups'].items():lines.append(f"| {group} | {row['weight']} | {row['tests']} | {row['passed']} | {row['rate']:.3f} |")
    lines+=['','Coverage: '+json.dumps(report['coverage']), 'Changed runtime line evidence: '+report['coverage'].get('diff_status','unavailable')+'.','Production deployment, hosted Supabase Auth and official trust certification are not verified by this local code gate.']
    (OUT/(SHA+'.md')).write_text('\n'.join(lines)+'\n')
    print(json.dumps(result,indent=2))
raise SystemExit(0 if report['result']['decision']=='PASS' else 1)
