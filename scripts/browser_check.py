"""Real browser/HTTP acceptance; requires localhost sockets and Chromium permission."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'evidence'/'browser'; folder.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,PRAXIS_DB=str(ROOT/'work'/'browser.sqlite'))
process=subprocess.Popen([str(ROOT/'.venv/bin/python'),'-m','praxis.server'],cwd=ROOT,env=env)
try:
    for i in range(100):
        try: urllib.request.urlopen('http://127.0.0.1:8787/api/health',timeout=.5); break
        except OSError:
            if process.poll() is not None: raise RuntimeError('Local server failed to bind; browser acceptance is blocked')
            time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[]; page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:8787/settings')
        page.get_by_label('Account name').fill('browser-'+secrets.token_hex(4))
        page.get_by_label('Password').fill(secrets.token_urlsafe(24))
        page.get_by_role('button',name='Continue',exact=True).click()
        page.wait_for_url('**/dashboard')
        page.goto('http://127.0.0.1:8787/models/new')
        page.get_by_label('Name',exact=True).fill('Browser demo transport fixture')
        page.get_by_label('Provider').select_option('demo')
        page.get_by_role('button',name='Save configuration').click()
        page.wait_for_url('**/models')
        page.goto('http://127.0.0.1:8787/runs/new')
        page.get_by_label('Suite slug').select_option('structured-agent@1.0.0')
        page.get_by_role('button',name='Start evaluation').click()
        page.wait_for_url('**/runs/*')
        page.get_by_role('heading',name='completed · demo').wait_for(timeout=20000)
        assert page.get_by_role('columnheader',name='Assertion',exact=True).count()>0
        page.screenshot(path=str(folder/'run-report.png'),full_page=True)
        for width in (390,1280):
            page.set_viewport_size({'width':width,'height':900})
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not errors,errors
        (folder/'result.json').write_text(json.dumps({'status':'passed','provider':'explicit demo fixture; no model inference','assertions':['signup','connect target','launch suite','persisted report assertions','390/1280 viewport','no runtime errors']},indent=2))
        browser.close()
finally:
    process.terminate(); process.wait(timeout=10)
