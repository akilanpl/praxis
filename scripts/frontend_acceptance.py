"""Redesign acceptance against an owned real local API, never mocked frontend data."""
import argparse
import base64
import http.server
import json
import os
from pathlib import Path
import secrets
import threading
import time
import urllib.request
from playwright.sync_api import sync_playwright,expect
from praxis.server import ControlPlane,Handler
from evidence_identity import source_identity

ROOT=Path(__file__).resolve().parents[1]
class Owned(http.server.BaseHTTPRequestHandler):
    calls=[]
    slow=False
    def log_message(self,*args):pass
    def send(self,status,body):
        raw=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.slow and self.path=='/health':time.sleep(5)
        self.calls.append(('GET',self.path));self.send(200 if self.path=='/health' else 404,{'status':'ok'})
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path!='/orders' or body!={'quantity':0}:raise RuntimeError('Unexpected mutation')
        self.calls.append(('POST',self.path));self.send(422,{'field':'quantity'})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False,mode=0o700)
    app=ControlPlane(out/'private'/'praxis.sqlite');server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);server.app=app;server.web_root=ROOT/'apps/web/dist';server.origins={f'http://127.0.0.1:{server.server_port}'}
    owned=http.server.ThreadingHTTPServer(('127.0.0.1',0),Owned);servers=[server,owned];threads=[threading.Thread(target=s.serve_forever) for s in servers]
    for thread in threads:thread.start()
    result={'status':'FAIL','mode':'real browser -> actual local HTTP API -> disposable SQLite; explicitly labeled evaluation fixtures and owned HTTP requests, not model capability','checks':[],'screenshots':[],'accessibility':[]}
    identity=source_identity();result.update({k:v for k,v in identity.items() if k!='source_files'});result['source_files']=[{'path':k,'sha256':v} for k,v in identity['source_files'].items()]
    base=f'http://127.0.0.1:{server.server_port}';token='';errors=[];runs=[]
    def check(name,condition=True):
        if not condition:raise RuntimeError(name)
        result['checks'].append({'name':name,'status':'PASS'})
    def request(method,path,body=None):
        req=urllib.request.Request(base+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
        with urllib.request.urlopen(req,timeout=60) as response:return json.load(response)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch();context=browser.new_context(viewport={'width':1440,'height':1000},bypass_csp=True);page=context.new_page()
            # CSP bypass permits axe instrumentation only; security header tests run separately.
            page.on('pageerror',lambda error:errors.append(type(error).__name__+': '+str(error)))
            last_navigation=0.0
            def go(url,**kwargs):
                nonlocal last_navigation
                # Pace navigation, not HTTP responses, to respect the real API quota.
                pause=2.1-(time.monotonic()-last_navigation)
                if pause>0:time.sleep(pause)
                last_navigation=time.monotonic();kwargs.setdefault('wait_until','networkidle');return page.goto(url,**kwargs)
            def screenshot(name,full=False):
                page.screenshot(path=str(out/(name+'.png')),full_page=full);result['screenshots'].append(name+'.png')
            def audit(name):
                page.evaluate((ROOT/'node_modules/axe-core/axe.min.js').read_text())
                data=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})")
                result['accessibility'].append({'name':name,'violations':[{'id':v['id'],'impact':v['impact'],'targets':[{'target':n['target'],'reason':n.get('failureSummary')} for n in v['nodes']]} for v in data['violations']],'incomplete':[{'id':v['id'],'targets':[{'target':n['target'],'reason':n.get('failureSummary')} for n in v['nodes']]} for v in data['incomplete']],'passes':len(data['passes'])})
            def register(name):
                nonlocal token
                go(base+'/settings');page.get_by_label('Account name').fill(name);page.get_by_label('Password').fill(secrets.token_urlsafe(24));page.get_by_role('button',name='Continue',exact=True).click();page.wait_for_url('**/dashboard');token=page.evaluate('localStorage.token')
            register('frontend-owner-'+secrets.token_hex(4));expect(page.get_by_role('heading',name='Your first evaluation starts here')).to_be_visible();screenshot('overview-empty-1440');check('First-time account and actionable empty overview')
            audit('empty overview')
            configs=[('Passing contract fixture','/models/new','demo'),('Failing contract fixture','/models/new','demo-failing'),('Bounded agent fixture','/agents/new','demo'),('Owned HTTP application','/apps/new','custom')]
            targets=[]
            for name,route,provider in configs:
                go(base+route);page.get_by_label('Name',exact=True).fill(name);page.get_by_label('Provider').select_option(provider)
                if route=='/apps/new':
                    page.get_by_label('Endpoint',exact=True).fill(f'http://127.0.0.1:{owned.server_port}');page.get_by_label('I own this endpoint',exact=False).check();page.get_by_label('Allow explicit POST',exact=False).check()
                page.get_by_role('button',name='Save configuration',exact=True).click();page.wait_for_url('**'+route.removesuffix('/new'));target=next(t for t in request('GET','/api/targets') if t['name']==name);targets.append(target)
            go(base+'/models');card=page.locator('article').filter(has=page.get_by_role('heading',name=configs[0][0],exact=True));card.get_by_role('button',name='Test connection').click();expect(card.get_by_text('Connection verified',exact=True)).to_be_visible();check('Target registration, consent and explicit diagnostics')
            go(base+'/targets');screenshot('targets-1440');audit('target registry')
            for index,target in enumerate(targets):
                go(base+'/runs/new?target='+target['id']);page.get_by_label('Target ID').select_option(target['id']);suite='http-application' if target['kind']=='application' else 'agent-workflows' if target['kind']=='agent' else 'structured-agent';page.get_by_label('Suite slug').select_option(suite+'@1.0.0');page.get_by_label('Publish outputs for blind community comparisons').check()
                if index==0:screenshot('launch-1440');audit('launch flow')
                with page.expect_response(lambda r:r.url.endswith('/api/runs') and r.request.method=='POST') as response:page.get_by_role('button',name='Start evaluation',exact=True).click()
                run_id=response.value.json()['id'];page.wait_for_url('**/runs/'+run_id);expect(page.get_by_role('heading',name='completed · '+('self-reported' if target['kind']=='application' else 'demo'),exact=True)).to_be_visible(timeout=30000);run=request('GET','/api/runs/'+run_id);runs.append(run)
                expected=0 if target['provider']=='demo-failing' else len(run['result']['tasks']);check('Persisted assertion results '+target['name'],run['result']['summary']['passed']==expected)
            check('Actual owned HTTP execution',('POST','/orders') in Owned.calls)
            failed=runs[1];go(base+'/runs/'+failed['id']);expect(page.get_by_role('cell',name='Fail',exact=True).first).to_be_visible();page.get_by_role('button',name='Failed tasks only').click();check('Failed task filtering retains visible failed assertions',page.get_by_role('columnheader',name='Assertion',exact=True).count()==8);page.get_by_role('button',name='Failed tasks only').click();page.get_by_text('Prompt and output',exact=True).first.click();screenshot('run-failure-1440');audit('failed run inspector')
            for button,filename in [('Export evidence','evidence.json'),('Export HTML','report.html')]:
                with page.expect_download() as download:page.get_by_role('button',name=button,exact=True).click()
                download.value.save_as(str(out/filename))
            check('JSON export matches persisted result',json.loads((out/'evidence.json').read_text())['id']==failed['id']);check('Standalone HTML export is script-free', '<script' not in (out/'report.html').read_text().lower())
            Owned.slow=True
            slow_target=request('POST','/api/targets',{'name':'Owned cancellation contract','kind':'application','provider':'custom','endpoint':f'http://127.0.0.1:{owned.server_port}','authorized':True,'allow_mutation':False})
            cancelled=request('POST','/api/runs',{'target_id':slow_target['id'],'suite_slug':'http-application','seed':73})
            go(base+'/runs/'+cancelled['id']);page.get_by_role('button',name='Cancel run',exact=True).click();expect(page.get_by_role('dialog',name='Cancel this evaluation?')).to_be_visible();screenshot('cancel-confirmation-1440');audit('cancellation dialog');page.keyboard.press('Escape');expect(page.get_by_role('dialog')).not_to_be_visible();page.get_by_role('button',name='Cancel run',exact=True).click();page.get_by_role('button',name='Confirm cancellation',exact=True).click();expect(page.get_by_role('heading',name='cancelled · self-reported',exact=True)).to_be_visible(timeout=30000);Owned.slow=False
            cancelled=request('GET','/api/runs/'+cancelled['id']);check('Actual cancellation dialog and retained denominator',cancelled['result']['summary']['total']==4 and cancelled['result']['summary']['not_run']>0)
            # Immutable suite creation and revision use the existing POST-only contract.
            source=request('GET','/api/suites/structured-agent@1.0.0');source.update(slug='frontend-authored-contract',title='Frontend acceptance contract');source['tasks']=source['tasks'][:2]
            go(base+'/suites/new');page.get_by_role('button',name='Full JSON',exact=True).click();page.get_by_label('Versioned suite JSON').fill(json.dumps(source));page.get_by_role('button',name='Save configuration',exact=True).click();page.wait_for_url('**/suites');go(base+'/suites/frontend-authored-contract@1.0.0');page.get_by_role('button',name=source['tasks'][1]['id'],exact=False).click();screenshot('suite-explorer-1440');page.get_by_role('link',name='Create revision',exact=False).click();expect(page.get_by_label('Version',exact=True)).to_have_value('1.0.1');page.get_by_label('Suite title').fill('Frontend acceptance revised');page.get_by_role('button',name='Save configuration',exact=True).click();page.wait_for_url('**/suites');check('Suite creation and immutable revision',request('GET','/api/suites/frontend-authored-contract@1.0.0')['title']!=request('GET','/api/suites/frontend-authored-contract@1.0.1')['title'])
            go(base+'/suites/new');page.get_by_role('button',name='Add scenario',exact=False).click();page.get_by_label('Output schema',exact=True).fill('{broken');page.get_by_role('button',name='Apply schema').click();expect(page.get_by_role('alert')).to_be_visible();check('Inline schema validation');screenshot('suite-editor-1440');audit('suite editor')
            go(base+'/artifacts');html=out/'inert.html';html.write_text('<script>window.__untrusted_executed=true</script>');page.get_by_label('Choose a file').set_input_files(str(html));expect(page.get_by_text(html.read_text(),exact=True)).to_be_visible();check('HTML upload remains inert',not page.evaluate('window.__untrusted_executed'));screenshot('artifact-inspector-1440');audit('artifact inspector')
            go(base+'/compare');expect(page.get_by_role('link',name=targets[0]['name'],exact=True)).to_be_visible();check('Condition-matched comparison',runs[0]['conditions_hash']==runs[1]['conditions_hash']);screenshot('comparison-1440')
            go(base+'/dashboard');page.keyboard.press('Control+k');expect(page.get_by_role('dialog',name='Search workspace')).to_be_visible();page.get_by_role('combobox',name='Search commands and records').fill('Reports');screenshot('command-palette-1440');audit('command palette');page.keyboard.press('Enter');page.wait_for_url('**/reports');check('Keyboard command palette navigates to reports')
            go(base+'/settings');expect(page.get_by_role('heading',name='Backup & restore',exact=True)).to_be_visible();expect(page.get_by_text('CLI operation · stop the runtime first',exact=True)).to_be_visible();check('Settings exposes honest CLI recovery contract');screenshot('settings-1440');audit('workspace settings')
            for route in ['/','/dashboard','/targets','/models','/agents','/apps','/suites','/runs','/reports','/runs/new','/artifacts','/compare','/arena','/leaderboards','/worlds','/worlds/new','/settings','/admin','/docs','/methodology','/privacy','/terms','/missing-route']:
                go(base+route,wait_until='networkidle');expect(page.locator('main h1')).to_be_visible();check('Real API route '+route)
            for width in [390,768,1024,1280,1440,1920]:
                page.set_viewport_size({'width':width,'height':1000})
                for route,name in [('/dashboard','overview'),('/targets','targets'),('/runs/'+failed['id'],'failed-run'),('/suites/frontend-authored-contract@1.0.1','suite'),('/settings','settings')]:
                    go(base+route,wait_until='networkidle');check('No document overflow '+name+' '+str(width),not page.evaluate('document.documentElement.scrollWidth>innerWidth'));screenshot(name+'-'+str(width))
                if width in [390,768]:
                    page.get_by_role('button',name='Open navigation').click();expect(page.get_by_role('complementary',name='Workspace navigation')).to_be_visible();screenshot('navigation-'+str(width));page.keyboard.press('Escape');check('Mobile drawer Escape restores usable workspace',not page.locator('.workspace-body').evaluate('(e)=>e.inert'))
            page.set_viewport_size({'width':1440,'height':1000});go(base+'/dashboard');page.get_by_role('button',name='Collapse sidebar').click();screenshot('overview-collapsed-1440');audit('collapsed navigation');page.get_by_role('button',name='Expand sidebar').click();page.get_by_role('button',name='Theme',exact=True).click();screenshot('overview-light-1440');audit('light overview')
            go(base+'/settings');context_id=request('GET','/api/me')['id']
            with app.store.connect() as db:db.execute('UPDATE sessions SET expires=0 WHERE user_id=?',(context_id,))
            go(base+'/runs');expect(page.get_by_label('Account name')).to_be_visible();check('Expired sessions return to local authentication')
            register('frontend-reviewer-'+secrets.token_hex(4));go(base+'/arena');expect(page.get_by_role('heading',name='Output A',exact=True)).to_be_visible();match=request('GET','/api/arena');check('Blind assignment does not reveal identities','target_id' not in json.dumps(match));screenshot('blind-review-1440');page.get_by_role('button',name='A wins',exact=True).click();expect(page.get_by_role('heading',name='Vote recorded',exact=True)).to_be_visible();check('Vote reveal and replay prevention',not page.get_by_role('button',name='A wins',exact=True).is_enabled());screenshot('blind-reveal-1440')
            check('No browser runtime errors',not errors);check('No automated A/AA violations in sampled pages',not any(x['violations'] for x in result['accessibility']))
            result['performance']=page.evaluate('({navigation:performance.getEntriesByType("navigation").map(n=>({duration:n.duration,domContentLoaded:n.domContentLoadedEventEnd,transferSize:n.transferSize})),resources:performance.getEntriesByType("resource").filter(r=>r.initiatorType==="script"||r.initiatorType==="link").map(r=>({name:new URL(r.name).pathname,transferSize:r.transferSize,duration:r.duration}))})')
            context.close();browser.close();result['status']='PASS'
    except Exception as error:
        result['error_type']=type(error).__name__;result['error']=str(error)[:500];raise
    finally:
        for s in servers:s.shutdown();s.server_close()
        for t in threads:t.join()
        app.pool.shutdown(wait=True)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(result['checks']),'accessibility_pages':len(result['accessibility'])}))

if __name__=='__main__':main()
