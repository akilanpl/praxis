"""Run from the user's normal Terminal: isolated, loopback-only Chromium CDP."""
from pathlib import Path
import subprocess
import urllib.request
import time
ROOT=Path(__file__).resolve().parents[1]
executables=list((ROOT/'work/browsers').glob('chromium-*/chrome-mac-*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'))
if not executables:raise SystemExit('Install Chromium first: PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/python -m playwright install chromium')
profile=ROOT/'work/host-browser-profile';profile.mkdir(parents=True,exist_ok=True)
log=open(ROOT/'work/host-browser.log','a')
process=subprocess.Popen([str(executables[-1]),'--remote-debugging-address=127.0.0.1','--remote-debugging-port=9333','--user-data-dir='+str(profile),'--no-first-run','--no-default-browser-check','about:blank'],stdout=log,stderr=log)
for _ in range(100):
 try:
  with urllib.request.urlopen('http://127.0.0.1:9333/json/version',timeout=.5) as response:
   if response.status==200:print('Isolated host Chromium ready at http://127.0.0.1:9333. Close this test browser when acceptance is finished.');break
 except OSError:
  if process.poll() is not None:raise SystemExit('Chromium exited. See work/host-browser.log')
  time.sleep(.1)
else:raise SystemExit('Chromium did not become ready. See work/host-browser.log')
