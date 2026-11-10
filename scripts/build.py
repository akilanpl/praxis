"""Build all shipped components; never publish or provision remote resources."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
OUT.mkdir(exist_ok=True)
env = dict(os.environ, PYTHONPYCACHEPREFIX=str(ROOT / 'work' / 'pycache'),
           XDG_CONFIG_HOME=str(ROOT / 'work' / 'wrangler-config'),
           WRANGLER_LOG_PATH=str(ROOT / 'work' / 'wrangler-build.log'),
           WRANGLER_SEND_METRICS='false')
steps = [
    ['npm', 'run', 'build', '--workspace', 'apps/website'],
    ['npm', 'run', 'build', '--workspace', 'apps/web'],
    ['npm', 'run', 'typecheck', '--workspace', 'packages/contracts'],
    ['npm', 'run', 'typecheck', '--workspace', 'apps/api'],
    [str(ROOT / 'node_modules' / '.bin' / 'wrangler'), 'deploy', '--dry-run',
     '--config', 'apps/api/wrangler.toml', '--outdir', str(OUT / 'worker')],
    [sys.executable, '-m', 'compileall', '-q', 'runner/praxis', 'scripts'],
    [sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation',
     '--wheel-dir', str(OUT / 'runner'), '.'],
]
manifest = {'status': 'building', 'remote_deployment': False, 'steps': []}
try:
    for command in steps:
        print('\nBuilding: ' + ' '.join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT, env=env)
        manifest['steps'].append({'command': command, 'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError('Build step failed with exit code %s' % result.returncode)
    wheel = OUT / 'runner' / 'praxis-0.1.0-py3-none-any.whl'
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        scenarios = [name for name in names if '/share/praxis/scenarios/' in name and name.endswith('.json')]
        expected = {p.name for p in (ROOT / 'packages' / 'scenarios').glob('*.json')}
        if {Path(name).name for name in scenarios} != expected:
            raise RuntimeError('Runner wheel is missing versioned scenarios')
        tasks = sum(len(json.loads(archive.read(name))['tasks']) for name in scenarios)
        if tasks < 30 or 'praxis/cli.py' not in names or 'praxis/server.py' not in names:
            raise RuntimeError('Runner wheel failed package completeness check')
    artifacts = [ROOT / 'apps/website/dist/index.html', ROOT / 'apps/web/dist/index.html', OUT / 'worker/index.js', wheel]
    for path in artifacts:
        if not path.is_file():
            raise RuntimeError('Expected build artifact missing: ' + str(path))
    manifest.update(status='passed', suites=len(scenarios), scenarios=tasks,
                    artifacts=[{'path':str(path.relative_to(ROOT)), 'bytes':path.stat().st_size,
                                'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in artifacts])
except Exception as exc:
    manifest.update(status='failed', error=str(exc))
finally:
    (OUT / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
if manifest['status'] != 'passed':
    print(manifest['error'], file=sys.stderr)
    sys.exit(1)
print('\nAll components built. Manifest: dist/build-manifest.json')
