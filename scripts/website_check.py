from evidence_identity import source_identity
"""Production website acceptance in disposable Chromium; no deployed site implied."""
import functools
import http.server
import json
import os
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('PRAXIS_EVIDENCE_DIR',str(ROOT/'evidence/final')))/'website'
OUT.mkdir(parents=True,exist_ok=True)
class Static(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Static,directory=str(ROOT/'apps/website/dist')))
thread=threading.Thread(target=server.serve_forever);thread.start()
result={'status':'running','scope':'built repository website over loopback HTTP; no public deployment','checks':[]}
result.update(source_identity())
def check(name,passed,**evidence):
    result['checks'].append({'name':name,'passed':bool(passed),**evidence})
    assert passed,name
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(service_workers='block')
        page=context.new_page();errors=[];bad=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
        page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle')
        expect(page.get_by_role('heading',level=1)).to_have_text('Evaluate what AI systems actually do.')
        check('six public suite links from source',page.locator('.suite-row').count()==6)
        check('forty source scenarios',page.locator('.facts').inner_text().find('40')>=0)
        check('unique semantic page heading',page.locator('h1').count()==1)
        check('page metadata',bool(page.title()) and page.locator('meta[name="description"]').count()==1 and page.locator('link[rel="icon"]').count()==1)
        links=page.locator('a').evaluate_all('(nodes)=>nodes.map(n=>({href:n.getAttribute("href"),text:n.textContent.trim()}))')
        for link in links:
            href=link['href'];check('meaningful link: '+link['text'],bool(href and link['text']))
            if href.startswith('#') and len(href)>1:check('anchor exists: '+href,page.locator(href).count()==1)
        page.keyboard.press('Tab');check('keyboard skip link',page.locator('.skip').evaluate('(e)=>e===document.activeElement'))
        page.keyboard.press('Enter');check('skip reaches main',page.evaluate('location.hash')=='#main')
        for width in (390,768,1280):
            page.set_viewport_size({'width':width,'height':900})
            page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle')
            check(f'no overflow at {width}',not page.evaluate('document.documentElement.scrollWidth>innerWidth'))
            page.screenshot(path=str(OUT/f'website-{width}.png'),full_page=True)
        page.get_by_role('link',name='Explore the architecture',exact=False).click()
        expect(page.locator('#architecture')).to_be_in_viewport()
        check('architecture CTA',page.evaluate('location.hash')=='#architecture')
        check('no browser errors',not errors,errors=errors)
        check('no broken local assets',not bad,failures=bad)
        check('no third-party scripts',page.locator('script[src]').evaluate_all('(s)=>s.every(x=>new URL(x.src).origin===location.origin)'))
        context.close();browser.close()
    result['status']='passed'
except Exception as e:
    result.update(status='failed',error=f'{type(e).__name__}: {e}')
    raise
finally:
    server.shutdown();server.server_close();thread.join()
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
