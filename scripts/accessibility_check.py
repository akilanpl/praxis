"""Actual Chromium + axe checks, not an exhaustive WCAG or assistive-tech audit."""
import argparse
import functools
import http.server
import json
import os
from pathlib import Path
import secrets
import threading
import time
from playwright.sync_api import sync_playwright,expect
from praxis.server import ControlPlane,Handler

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False,mode=0o700)
    app=ControlPlane(out/'private'/'praxis.sqlite')
    workspace=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    workspace.app=app;workspace.web_root=ROOT/'apps/web/dist';workspace.origins={f'http://127.0.0.1:{workspace.server_port}'}
    class Static(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    website=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Static,directory=str(ROOT/'apps/website/dist')))
    servers=[workspace,website];threads=[threading.Thread(target=s.serve_forever) for s in servers]
    for thread in threads:thread.start()
    results={'status':'FAIL','scope':'actual Chromium, axe WCAG A/AA automated rules and targeted keyboard/DOM/manual visual checks; no WCAG certification or screen-reader certification','axe_version':json.loads((ROOT/'node_modules/axe-core/package.json').read_text())['version'],'pages':[],'checks':[]}
    def check(name,condition):
        results['checks'].append({'name':name,'status':'PASS' if condition else 'FAIL'})
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch();context=browser.new_context(viewport={'width':1280,'height':900},bypass_csp=True)
            # CSP bypass is only for injected audit instrumentation, not a security test.
            page=context.new_page();base=f'http://127.0.0.1:{workspace.server_port}'
            def audit(name,url):
                page.goto(url,wait_until='networkidle');page.evaluate((ROOT/'node_modules/axe-core/axe.min.js').read_text())
                data=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
                results['pages'].append({'name':name,'url_path':url.removeprefix(base) if url.startswith(base) else 'static website','violations':[{'id':v['id'],'impact':v['impact'],'help':v['help'],'nodes':[{'target':n['target'],'failureSummary':n.get('failureSummary')} for n in v['nodes']]} for v in data['violations']],'incomplete':[{'id':v['id'],'nodes':[{'target':n['target'],'reason':n.get('failureSummary')} for n in v['nodes']]} for v in data['incomplete']],'passes':len(data['passes'])})
                check('Single page heading '+name,page.locator('h1').count()==1)
            audit('signed-out settings',base+'/settings')
            page.keyboard.press('Tab');check('Workspace skip link is first keyboard stop',page.locator('.skip').evaluate('(e)=>e===document.activeElement'))
            page.keyboard.press('Enter');check('Workspace skip link reaches main',page.evaluate('location.hash')=='#main')
            for _ in range(15):
                page.keyboard.press('Tab')
                if page.locator('input[name=username]').evaluate('(e)=>e===document.activeElement'):break
            check('Keyboard traversal reaches labeled account input',page.locator('input[name=username]').evaluate('(e)=>e===document.activeElement'))
            page.keyboard.type('a11y-'+secrets.token_hex(4));page.keyboard.press('Tab');page.keyboard.type(secrets.token_urlsafe(24));page.keyboard.press('Tab');page.keyboard.press('Tab');page.keyboard.press('Enter');page.wait_for_url('**/dashboard')
            check('Keyboard-only account form submission',True)
            token=page.evaluate('localStorage.token')
            account=app.auth('Bearer '+token)
            target=app.request('POST','/api/targets',{'name':'Accessibility fixture','kind':'model','provider':'demo'},'Bearer '+token)
            run=app.request('POST','/api/runs',{'target_id':target['id'],'suite_slug':'structured-agent','seed':73},'Bearer '+token)
            for _ in range(100):
                run=app.store.get('run',run['id'],account)
                if run['status'] not in ('queued','running'):break
                time.sleep(.05)
            for route in ['/dashboard','/models/new','/runs/new','/runs/'+run['id'],'/artifacts','/compare','/settings']:
                audit('dark '+route,base+route)
            page.goto(base+'/models/new');page.get_by_label('Name',exact=True).fill('Invalid endpoint');page.get_by_label('Endpoint',exact=True).fill('file:///untrusted');page.get_by_role('button',name='Save configuration').click()
            expect(page.get_by_role('alert')).to_be_visible();check('Validation error announced with alert role',True)
            page.goto(base+'/dashboard');page.get_by_role('button',name='Theme',exact=False).click();audit('light dashboard',base+'/dashboard');audit('light model form',base+'/models/new');audit('light report',base+'/runs/'+run['id'])
            for width in (390,768,1280):
                page.set_viewport_size({'width':width,'height':900});page.goto(base+'/runs/'+run['id']);check('Workspace report responsive '+str(width),not page.evaluate('document.documentElement.scrollWidth>innerWidth'));page.screenshot(path=str(out/('workspace-'+str(width)+'.png')))
            page.set_viewport_size({'width':1280,'height':900});audit('static website',f'http://127.0.0.1:{website.server_port}')
            page.keyboard.press('Tab');check('Website first keyboard stop is skip link',page.locator('.skip').evaluate('(e)=>e===document.activeElement'));page.keyboard.press('Enter');check('Website skip link reaches main',page.evaluate('location.hash')=='#main')
            # Visible keyboard focus is checked from computed styles at the focused link.
            page.keyboard.press('Tab');check('Website visible focus outline',page.evaluate('getComputedStyle(document.activeElement).outlineStyle')!='none')
            for width in (390,768,1280):
                page.set_viewport_size({'width':width,'height':900});check('Website responsive '+str(width),not page.evaluate('document.documentElement.scrollWidth>innerWidth'));page.screenshot(path=str(out/('website-'+str(width)+'.png')),full_page=True)
            check('No automated A/AA violations on audited pages',not any(row['violations'] for row in results['pages']))
            context.close();browser.close()
        results['status']='PASS' if all(c['status']=='PASS' for c in results['checks']) else 'FAIL'
    finally:
        for server in servers:server.shutdown();server.server_close()
        for thread in threads:thread.join()
        app.pool.shutdown(wait=True)
        (out/'result.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'status':results['status'],'pages':len(results['pages']),'violations':sum(len(x['violations']) for x in results['pages'])}))
    raise SystemExit(0 if results['status']=='PASS' else 1)

if __name__=='__main__':main()
