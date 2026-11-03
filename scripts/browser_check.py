"""Full browser -> HTTP -> SQLite journey, with explicit real/fixture mode."""
import argparse
import base64
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.error
import urllib.request
import wave
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--fixture-only',action='store_true',help='Infrastructure test only; never real inference evidence')
args=parser.parse_args()
folder=ROOT/'evidence/release/browser';folder.mkdir(parents=True,exist_ok=True)
name=secrets.token_hex(4)
base='http://127.0.0.1:8790'
env=dict(os.environ,PRAXIS_DB=str(ROOT/'work'/('browser-'+name+'.sqlite')),PRAXIS_PORT='8790')
log=open(ROOT/'work'/('browser-api-'+name+'.log'),'w')
process=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-m','praxis.server'],cwd=ROOT,env=env,stdout=log,stderr=log)
result={'status':'running','mode':'explicit fixture automation; no real inference' if args.fixture_only else 'two real local CPU models; no mocked backend','checks':[],'screenshots':[]}
token=''
def http(method,path,body=None):
    req=urllib.request.Request(base+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
    with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)
def record(name,**evidence):result['checks'].append({'name':name,'passed':True,**evidence})
def screenshot(page,name):
    page.screenshot(path=str(folder/(name+'.png')),full_page=False)
    result['screenshots'].append(name+'.png')
try:
    for _ in range(100):
        if process.poll() is not None:raise RuntimeError('Acceptance API failed to start; inspect '+str(log.name))
        try:
            with urllib.request.urlopen(base+'/api/health',timeout=.5) as response:
                if response.status==200:break
        except OSError:time.sleep(.1)
    else:raise RuntimeError('Acceptance API health deadline exceeded')
    with sync_playwright() as p:
        external=os.environ.get('PRAXIS_BROWSER_CDP')
        browser=p.chromium.connect_over_cdp(external) if external else p.chromium.launch(headless=True)
        context=browser.new_context(viewport={'width':1280,'height':900},service_workers='block')
        page=context.new_page();errors=[];dialogs=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('dialog',lambda dialog:(dialogs.append(dialog.message),dialog.dismiss()))
        def register(prefix):
            global token
            page.goto(base+'/settings')
            page.get_by_label('Account name').fill(prefix+'-'+name)
            page.get_by_label('Password').fill(secrets.token_urlsafe(24))
            page.get_by_role('button',name='Continue',exact=True).click()
            page.wait_for_url('**/dashboard')
            token=page.evaluate('localStorage.token')
            assert http('GET','/api/me')['username']==prefix+'-'+name
        register('browser-owner')
        record('Register in Chromium and retrieve authenticated account through real HTTP')
        configs=[('Explicit passing fixture','demo','','demo'),('Explicit failing fixture','demo-failing','','demo-failing')] if args.fixture_only else [
            ('SmolLM2 135M CPU q4','openai','http://127.0.0.1:8788/v1','onnx-community/SmolLM2-135M-Instruct-ONNX'),
            ('SmolLM2 360M CPU q4','openai','http://127.0.0.1:8789/v1','onnx-community/SmolLM2-360M-Instruct-ONNX')]
        runs=[]
        for target_name,provider,endpoint,model in configs:
            page.goto(base+'/models/new')
            page.get_by_label('Name',exact=True).fill(target_name)
            page.get_by_label('Provider').select_option(provider)
            page.get_by_label('Endpoint',exact=True).fill(endpoint)
            page.get_by_label('Model identifier').fill(model)
            page.get_by_role('button',name='Save configuration').click()
            page.wait_for_url('**/models')
            target=next(x for x in http('GET','/api/targets') if x['name']==target_name)
            card=page.get_by_role('article').filter(has=page.get_by_role('heading',name=target_name,exact=True))
            with page.expect_response(lambda r:r.url.endswith('/diagnostics') and r.request.method=='POST') as diagnostic:
                card.get_by_role('button',name='Test connection').click()
            data=diagnostic.value.json();assert data['ok'],data
            if not args.fixture_only:assert not data['demo']
            page.goto(base+'/runs/new')
            page.get_by_label('Target ID').select_option(target['id'])
            page.get_by_label('Suite slug').select_option('structured-agent@1.0.0')
            page.get_by_label('Publish outputs for blind community comparisons').check()
            with page.expect_response(lambda r:r.url.endswith('/api/runs') and r.request.method=='POST') as submitted:
                page.get_by_role('button',name='Start evaluation').click()
            run_id=submitted.value.json()['id']
            page.wait_for_url('**/runs/'+run_id)
            expect(page.get_by_role('heading',name='completed · '+('demo' if args.fixture_only else 'self-reported'),exact=True)).to_be_visible(timeout=180000)
            run=http('GET','/api/runs/'+run_id)
            assert run['status']=='completed' and len(run['result']['tasks'])==8
            assert all(t['output'] is not None and not t['error'] for t in run['result']['tasks'])
            assert page.get_by_role('columnheader',name='Assertion',exact=True).count()==8
            page.get_by_role('button',name='Export evidence').click()
            runs.append(run)
            screenshot(page,'report-'+str(len(runs)))
            record('Connect, diagnose, execute, persist and inspect '+target_name,run_id=run_id,benchmark_passed=run['result']['summary']['passed'],benchmark_total=8,trust=run['trust'])
        assert runs[0]['conditions_hash']==runs[1]['conditions_hash']
        page.goto(base+'/compare')
        for target_name,*_ in configs:expect(page.get_by_role('link',name=target_name,exact=True)).to_be_visible()
        screenshot(page,'compare')
        record('Compare two matched targets with identical suite, seed and budgets')
        page.goto(base+'/arena')
        expect(page.get_by_role('heading',name='No eligible comparison yet')).to_be_visible()
        record('Owner cannot vote on own published outputs')
        page.goto(base+'/worlds/new')
        page.get_by_label('Name',exact=True).fill('Support acceptance '+name)
        page.get_by_label('Domain').select_option('support')
        page.get_by_role('button',name='Save configuration').click()
        page.wait_for_url('**/worlds')
        world=next(w for w in http('GET','/api/worlds') if w['name']=='Support acceptance '+name)
        page.goto(base+'/worlds/'+world['id'])
        with page.expect_response(lambda r:r.url.endswith('/replay')) as replay:
            page.get_by_role('button',name='Execute deterministic replay').click()
        data=replay.value.json()
        assert [l['entities'] for l in data['levels']]==[1,5,12]
        assert http('POST','/api/worlds/'+world['id']+'/replay',{})==data
        expect(page.get_by_role('heading',name='Level 3',exact=True)).to_be_visible()
        screenshot(page,'world')
        record('Bounded adaptive reference world persists state and replays identically',trust=data['trust'],replay_hash=data['replay_hash'])
        page.goto(base+'/artifacts')
        source=folder/'inert.html';source.write_text('<script>alert("never execute")</script>')
        with page.expect_response(lambda r:r.url.endswith('/api/artifacts') and r.request.method=='POST') as upload:
            page.get_by_label('Choose a file').set_input_files(str(source))
        artifact=upload.value.json()
        assert artifact['mime']=='text/plain' and artifact['public'] is False
        page.get_by_label('Search records').fill(artifact['id'])
        expect(page.get_by_text('<script>alert("never execute")</script>',exact=True)).to_be_visible()
        assert not dialogs
        screenshot(page,'artifact-inert')
        record('Browser file upload is private and HTML renders inertly')
        source_wav=folder/'one-second.wav'
        with wave.open(str(source_wav),'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(8000);wav.writeframes(b'\0\0'*8000)
        page.get_by_label('Search records').fill('')
        with page.expect_response(lambda r:r.url.endswith('/api/artifacts') and r.request.method=='POST') as upload:
            page.get_by_label('Choose a file').set_input_files(str(source_wav))
        artifact=upload.value.json();assert artifact['mime']=='audio/wav' and artifact['duration_seconds']==1
        page.get_by_label('Search records').fill(artifact['id'])
        expect(page.locator('audio')).to_be_visible()
        record('Real WAV ingestion measures duration and provides an audio preview')
        with page.expect_response(lambda r:r.url.endswith('/auth/logout')):
            page.get_by_role('button',name='Sign out',exact=True).click()
        expect(page.get_by_label('Account name')).to_be_visible()
        register('browser-reviewer')
        page.goto(base+'/arena')
        expect(page.get_by_role('heading',name='Output A',exact=True)).to_be_visible()
        match=http('GET','/api/arena');assert match.get('id')
        assert 'target_id' not in json.dumps(match)
        if not args.fixture_only:assert not match['demo']
        screenshot(page,'arena-blind')
        with page.expect_response(lambda r:r.url.endswith('/vote') and r.request.method=='POST') as vote:
            page.get_by_role('button',name='A wins',exact=True).click()
        revealed=vote.value.json()
        expect(page.get_by_role('heading',name='Vote recorded',exact=True)).to_be_visible()
        assert not page.get_by_role('button',name='A wins',exact=True).is_enabled()
        assert {revealed['a'],revealed['b']}=={c[0] for c in configs}
        try:http('POST','/api/arena/'+match['id']+'/vote',{'choice':'b'});raise AssertionError('Duplicate vote accepted')
        except urllib.error.HTTPError as error:assert error.code==409
        try:http('GET','/api/runs/'+runs[0]['id']);raise AssertionError('Foreign report exposed')
        except urllib.error.HTTPError as error:assert error.code==404
        screenshot(page,'arena-revealed')
        record('Anonymous other-owned vote reveals identities once and rejects replay',demo=match['demo'])
        board=http('GET','/api/leaderboards')
        assert not board['objective'] and len(board['preference'])==2
        assert all(r['votes']==1 and r['status']=='insufficient evidence' for r in board['preference'])
        record('Preference updates persist independently of empty official objective rankings')
        for route in ('/dashboard','/models','/agents','/apps','/suites','/worlds','/runs/new','/artifacts','/compare','/leaderboards','/methodology','/docs','/settings','/admin','/privacy','/terms','/not-a-page'):
            page.goto(base+route)
            expect(page.locator('main h1')).to_be_visible()
        record('Visible navigation and branded missing-page route render without runtime errors')
        page.goto(base+'/dashboard')
        for width in (390,1280):
            page.set_viewport_size({'width':width,'height':900})
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'),width
            screenshot(page,'dashboard-'+str(width))
        assert not errors,errors
        assert not dialogs,dialogs
        record('390/1280 viewport checks and zero uncaught page errors')
        for i,run in enumerate(runs):
            (folder/('run-'+str(i+1)+'.json')).write_text(json.dumps({k:v for k,v in run.items() if k!='idempotency_key'},indent=2)+'\n')
        context.close()
        if not external:browser.close()
    result['status']='passed'
except Exception as exc:
    result.update(status='failed',error=type(exc).__name__+': '+str(exc))
    raise
finally:
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    process.terminate();process.wait(timeout=15);log.close()
    print(json.dumps(result,indent=2))
