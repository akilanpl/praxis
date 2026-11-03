# Host and deployment boundaries

Network permission now allows loopback servers. The managed shell still denies macOS Chromium IPC and native PostgreSQL shared memory. Computer Use explicitly refused Terminal access; this restriction was not bypassed.

The user launched `scripts/start_host_browser.py` from normal Terminal. It creates a separate Chromium profile, keeps debugging loopback-only at port 9333, and does not disable browser security. Python Playwright connects using `PRAXIS_BROWSER_CDP=http://127.0.0.1:9333` and creates disposable browser contexts. The user also ran `scripts/postgres_acceptance.py`; its native PostgreSQL 15.19 cluster, RLS and integrity checks passed. Only synthetic data were inserted and the owned cluster was stopped.

Run the complete gate from normal Terminal for native database coverage:

```sh
cd /Users/akilan/Documents/Codex/2026-11-03/read-praxis-ultimate-master-prompt-md/outputs/praxis
PRAXIS_BROWSER_CDP=http://127.0.0.1:9333 .pushgate/run.sh --mode=local
```

It builds, tests, scans, starts disposable services, runs real local CPU inference/browser acceptance and records a deterministic score. It does not publish or provision cloud resources. On Linux CI the browser and database start normally without the macOS host bridge.

Cloudflare CLI reports unauthenticated. Connected Supabase projects are unrelated to Praxis; none were changed. Deploying the current metadata Worker alone does not produce the full hosted product. A dedicated approved project plus frontend Supabase session wiring and runner dispatch/persistence parity are still required before claiming public product acceptance. No temporary account, paid project or tunnel is used as a substitute.
