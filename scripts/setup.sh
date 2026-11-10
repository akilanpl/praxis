#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
command -v python3.12 >/dev/null || { echo 'Python 3.12+ required'; exit 1; }
command -v npm >/dev/null || { echo 'Node 22+ and npm required'; exit 1; }
python3.12 -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"'
node -e 'if (Number(process.versions.node.split(".")[0]) < 22 || (Number(process.versions.node.split(".")[0]) === 22 && Number(process.versions.node.split(".")[1]) < 12)) { console.error("Node 22.12+ required"); process.exit(1); }'
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip "setuptools>=84.1,<85" wheel
.venv/bin/python -m pip install -r requirements-lock.txt
ONNXRUNTIME_NODE_INSTALL=skip npm ci --cache ./work/npm-cache
npm run build
printf 'Ready. Start with npm run dev or PYTHONPATH=runner .venv/bin/python -m praxis.server\n'
