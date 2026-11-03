import os
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
os.chdir(root)
env=dict(os.environ,PYTHONPATH=str(root/'runner'))
api=subprocess.Popen([sys.executable,'-m','praxis.server'],env=env)
web=subprocess.Popen(['npm','run','dev','--workspace','apps/web'])
try:
    web.wait()
except KeyboardInterrupt: pass
finally:
    web.terminate(); api.terminate(); web.wait(); api.wait()
