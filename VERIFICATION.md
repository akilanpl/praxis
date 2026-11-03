# Verification — 2026-11-03

**Overall: partial acceptance; full quality gate is NOT green.** The implemented local control plane, evaluation logic and frontend build are integrated. HTTP listener/browser, real inference, production cloud workflows and Postgres authorization are not verified. No public deployment occurred.

| Command or demonstration | Actual result | Scope / limitation |
|---|---|---|
| `npm run build` | PASS | React production build and TypeScript Worker typecheck. Web JS gzip ~78 KiB. React Router emits harmless ignored `use client` bundle warnings. |
| `npm run typecheck --workspace packages/contracts` | PASS | Shared Zod contracts compile. |
| `npm run test --workspace apps/api` | PASS, 14 tests | Mocked Supabase transport; auth rejection, ownership, secret rejection, size/origin boundaries, no endpoint proxying, no trust escalation. Not a live Supabase test. |
| `.venv/bin/python -m pytest tests -q` | 54 passed, 7 environment errors | Seven loopback HTTP adapter tests cannot bind: `PermissionError: [Errno 1] Operation not permitted`. These tests remain enabled; nothing was skipped to turn the full gate green. |
| `.venv/bin/python -m pytest tests -q -k 'not AdapterContractTests'` | PASS, 54 tests | Explicit diagnostic subset excludes seven socket-dependent tests. Engine/schema/negative fixtures, agent mutation/permissions, worlds, persistence/isolation, concurrent matching/voting/idempotency, inert uploads/WAV, mocked provider/application contracts and real HTTP parser via byte buffers. Not real HTTP transport or inference. |
| `.venv/bin/python scripts/integration_proof.py` | PASS | Actual in-process control-plane calls and SQLite persistence: 2 model fixture runs and 1 executable agent fixture run; assertions/timings/events; seed replay 1→5→12 entities; other-owned blind pairing/vote; duplicate vote HTTP-equivalent 409; scoped persisted preference calculation; 1-second WAV metadata. Explicit demo providers, no model inference. |
| `.venv/bin/praxis suites list` | PASS | Six versioned suites, 40 scenarios. Every task's passing and failing output fixture is graded in tests. Developer reasoning is not counted as code execution. |
| `.venv/bin/python scripts/browser_check.py` | BLOCKED | Real HTTP/browser acceptance script exists. Local server listener is denied before browser workflow can begin. |
| `PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/praxis check-website --output-dir evidence/website` | BLOCKED | Chromium installed, but startup fails at macOS `MachPortRendezvousServer` bootstrap check-in with permission denied (1100). No screenshot, browser assertion pass or visual QA is claimed. |
| Ollama `/api/tags` discovery | BLOCKED | Loopback connection denied by execution sandbox. No usable endpoint established. `PRAXIS_MODEL_API_KEY` absent; no keys printed. No genuine model request or inference quality is verified. |
| Worker `deploy:review` dry-run with local XDG/log paths | PASS | Wrangler bundle 777.35 KiB / gzip 122.06 KiB. Metadata-only Worker; no remote deployment or resource mutation. |
| `npm install --cache ./work/npm-cache` after security updates | PASS, 0 vulnerabilities reported | Initial install reported 10 high advisories; upgraded router/Vite/Wrangler/Zod using advisory fixes. Later standalone audit retry was blocked by DNS resolution; it did not provide a new audit result. |
| Postgres/Supabase RLS regression SQL | NOT RUN | CLI, psql and a provisioned database unavailable. Reviewed schema source and ownership tests are not equivalent to verified RLS. |
| Fresh setup dependency installation | PARTIAL | Virtualenv, editable Python package/dependencies, npm install and build ran successfully. `setup.sh` is provided but end-to-end fresh server/browser startup is blocked here. |
| Public deployment / paid inference | NOT PERFORMED | No credentials, production architecture acceptance or deployment approval. No paid resources, model downloads, GitHub push or remote mutation. |

Commands and raw output: `evidence/verification/commands.json` and adjacent logs. Persisted fixture evidence: `evidence/integration-proof.json`, `evidence/{demo-run,demo-failing-run,agent-run}.json`, matching printable HTML, and `evidence/world-replay.json`. Generated records are explicitly infrastructure fixtures and excluded from official rankings.

## Remaining acceptance gaps

No robust untrusted code/app executor; arbitrary executable HTML/code is refused. No real-model-driven world policy, generated media inference/quality scoring, automatic pricing, streaming, individual-task resume, YAML authoring, held-out official suites, collaborative organization runtime, official trusted runner enrollment, public moderation/anti-bot pipeline, retention/deletion workflow, R2 signing or full hosted feature parity. Video codec/duration inspection is unknown. The Worker handles authenticated metadata/evidence only and cannot serve as a replacement for the complete local API.

Cost: no paid inference, provisioned cloud compute or deployment. Reasonable local open-source dependencies and Chromium were downloaded. Source is in local Git commits only. See README.md for exact startup and re-verification commands on a normal local machine.
