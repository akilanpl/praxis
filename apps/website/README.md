# Praxis project website

A separate static React/Vite engineering website. It does not replace `apps/web`, call the evaluation API, claim a live demo, or include third-party tracking.

From the repository root, install the existing lockfiles with `./scripts/setup.sh` (Python 3.12+, Node 22+, npm and POSIX shell), then:

```sh
npm run website:dev
# http://127.0.0.1:5174
npm run website:build
# apps/website/dist
```

`npm run build` builds the website together with the evaluation UI, contracts, Worker bundle and runner wheel. Suite names/counts come from the six checked-in JSON definitions, not duplicated benchmark data. Model result links refer to the explicitly historical ONNX acceptance records.

Browser acceptance (cloud workspace or CI only for this mission):

```sh
PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/python scripts/website_check.py
```

The script serves only the production build on an ephemeral loopback port, checks anchors, semantic headings, keyboard skip navigation, metadata, browser errors and 390/768/1280-pixel overflow, and saves full-page screenshots to `evidence/final/website`. Use `PRAXIS_EVIDENCE_DIR` for a separate receipt directory. Screenshot inspection is part of the recorded acceptance; it is not automated visual similarity certification.

No public URL or canonical deployment origin is configured because no deployment has occurred. Relative assets work at a hosting origin's root. Before an explicitly approved deployment, configure the actual origin, canonical/`og:url` and any desired social image, serve `dist` as static content, apply response security headers, and smoke-test the real URL. No runtime secrets or cloud API account is required for this website.
