"""Source provenance only; this does not confer independent trusted-runner status."""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
PATHS=('runner','tests','apps','packages','scripts','supabase','package.json','package-lock.json','pyproject.toml','requirements-lock.txt','.github','.pushgate','vitest.config.ts')
def source_identity():
    if not __debug__:raise RuntimeError("Acceptance requires Python assertions enabled")
    names=subprocess.check_output(['git','ls-files','-z','--',*PATHS],cwd=ROOT).decode().split('\0')
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(names) if name and (ROOT/name).is_file()}
    dirty=subprocess.run(['git','diff','--quiet','HEAD','--',*PATHS],cwd=ROOT).returncode!=0
    return {'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_dirty':dirty,'source_tree_sha256':hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),'source_files':hashes}
