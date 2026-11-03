#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo 'Python 3.9+ required'; exit 1; }
command -v npm >/dev/null || { echo 'Node 22+ and npm required'; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3,9), "Python 3.9+ required"'
node -e 'if (Number(process.versions.node.split(".")[0]) < 22) { console.error("Node 22+ required"); process.exit(1); }'
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip "setuptools>=61" wheel
.venv/bin/python -m pip install -e '.[test]'
npm ci --cache ./work/npm-cache
npm run build
printf 'Ready. Start with npm run dev or PYTHONPATH=runner .venv/bin/python -m praxis.server\n'
