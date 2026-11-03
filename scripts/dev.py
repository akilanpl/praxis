import os
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
os.chdir(root)
env=dict(os.environ,PYTHONPATH=str(root/'runner'))
python=str(root/'.venv/bin/python') if (root/'.venv/bin/python').exists() else sys.executable
api=subprocess.Popen([python,'-m','praxis.server'],env=env)
web=subprocess.Popen(['npm','run','dev','--workspace','apps/web'])
try:
    web.wait()
except KeyboardInterrupt: pass
finally:
    web.terminate(); api.terminate(); web.wait(); api.wait()
