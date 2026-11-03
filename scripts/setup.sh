#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo 'Python 3.9+ required'; exit 1; }
command -v npm >/dev/null || { echo 'Node 20.19+ and npm required'; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[test]'
npm ci
npm run build
printf 'Ready. Start with npm run dev or PYTHONPATH=runner .venv/bin/python -m praxis.server\n'
