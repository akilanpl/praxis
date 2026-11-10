# Verification — Codex Cloud, 2026-11-10

**Verdict: READY FOR REVIEW. Local feature gate PASS; no production or hosted-product certification.**

Base: `8f1e8847b31fc0b81fd17c1bdacfa626dc737f1e` (`main`). Tested runtime source: `378d5d38782ee13921989bc71feef25f996f568d`; following documentation/evidence commits do not change executable application source. The checkout and all acceptance work are inside managed Codex Cloud `/workspace/praxis`. Original historical evidence is preserved.

Runtime: Python 3.12.14, Node 24.22.1, npm 11.9.0, locked Playwright 1.64.1 / Chromium 156.0.8078.4, Vite 6.4.5, Wrangler 4.157.0. Python and npm lockfiles were installed; no major dependency upgrades were introduced.

| Area | Result | Current evidence / scope |
|---|---|---|
| Complete Python suite | PASS | `evidence/final/python.log`, `python.xml`: **140 tests + 44 subtests**, no skips. Includes actual loopback protocol/deadline/agent HTTP tests, ownership, concurrency, idempotency, restart and transaction rollback regressions. |
| Frontend tests | PASS | `evidence/final/gate/browser/result.json`: real browser → HTTP → SQLite journey with two CPU models; separate explicit fixture journey in `evidence/final/browser/result.json`. No mocked backend in either browser journey. |
| Frontend lint | PASS | `evidence/final/lint.log`: compiler unused-local/parameter checks on both frontends. This is limited compiler lint, not a separate ESLint/style audit. |
| TypeScript checks | PASS | `evidence/final/typecheck.log`: web, website, shared contracts and Worker. |
| API / Worker tests | PASS | `evidence/final/worker.log`: 14 tests with controlled Supabase transport. `worker-runtime.json`: actual local workerd health 200 and unconfigured metadata API 503. Not hosted Auth. |
| Production builds | PASS | `evidence/final/build.log`, `build-manifest.json`: both frontends, contracts, Worker bundle, Python compilation and wheel. No deployment. |
| Installation / package | PASS | `evidence/final/setup.log`: documented `./scripts/setup.sh` succeeds with the locks; `gate/wheel.json` loads 6 suites/40 scenarios and executes 12 explicit model/agent fixture tasks away from source. |
| HTTP integration | PASS | Python real loopback tests and `suite-matrix.json`: actual authorized HTTP positive/negative execution of all four public application scenarios. Controlled fixture server, not hosted application acceptance. |
| PostgreSQL / RLS | PARTIAL | `evidence/final/gate/postgres.json`: actual PostgreSQL 17.11 Alpine container, network disabled, identical schema/migration, ownership/trust/persistence SQL and RLS enabled on all 28 tables. Also Debian PostgreSQL 17 acceptance in `evidence/final/postgres.json`. Synthetic auth.uid/JWT claims; hosted Supabase Auth NOT VERIFIED. SQL exercises selected ownership paths, not exhaustive per-table business acceptance. |
| Browser acceptance | PASS | Full real-model journey: registration/connection/run/inspection/export interaction/comparison/world/upload/vote/isolation/navigation and 390/1280 layouts. Owned website fixture assertions also pass. See `gate/browser/result.json`, screenshot files and `gate-summary.md`. |
| Security checks | PASS | Gitleaks history scan, staged-change scan, npm/pip advisory audits report no known findings. HTTP framing/origin/owner/redaction/redirect/tool/isolation regressions pass. Bounded scope; no claim of a comprehensive external penetration test. |
| Model execution infrastructure | PASS | Two new real cloud CPU ONNX runs, raw reports and `evidence-integrity.json`. Benchmark quality is FAIL: **0/8 each**, not fixture substitution. |
| All public suites / scenarios | PASS | `suite-matrix.json` and `suite-runs/`: six suites, forty scenarios each executed positively and negatively (80 task executions). Models and tools use explicitly labeled fixtures; HTTP uses actual owned fixture-server requests. |
| Evidence / reports | PASS | `evidence-integrity.json`: result digests, per-output hashes, ordered events and regenerated escaped standalone HTML for both real-model reports. CLI positive/negative exports and HTML escaping are in Python tests. |
| Website responsiveness | PASS | `gate/website/result.json`, `website-{390,768,1280}.png`: no overflow, browser errors or broken local assets; semantic heading, keyboard skip and internal anchors checked. Desktop/mobile screenshots inspected. |
| Website production build | PASS | `npm run website:build`, included in root build; semantic React/Vite site without third-party scripts/tracking or fabricated live demo. |
| Changed executable-line coverage | NOT VERIFIED | Python statements 85.48%, branches 76.10%; TypeScript changed-line coverage is unavailable. `diff-coverage.json` records the full-base measurement. No tests/coverage exclusions were added to inflate this result. |
| Complete hosted workflow / public deployment | NOT VERIFIED | Not deployed; no production URL, approved project/credentials, hosted auth/dispatch parity or real-URL acceptance. |
| GitHub publication | BLOCKED | Configured GitHub API identity returns 401 Bad credentials; the actual push failed because Git could not obtain a username/credential with terminal prompts disabled. No PR was created. `evidence/final/git-push.log` and final handoff retain exact retry commands. |

Aggregate feature gate: **PASS, 186 executed checks, score 89/100**, all executed checks passed. The conservative score cap remains because whole-change executable-line coverage is not measured; this is a feature-branch threshold, not protected-main or production acceptance. Raw receipt: `evidence/final/gate-receipt.json`. Its short-form coverage base was rejected as unmeasured; `diff-coverage.json` retries the full SHA and confirms frontend executable-line evidence is absent. Neither result is relabeled as measured coverage.

The earlier aggregate attempt is retained as `preliminary-gate.json`: INCOMPLETE after the large Debian Docker image exhausted the 7.9 GiB writable layer. The smaller official PostgreSQL Alpine image resolved that cloud resource blocker without changing the schema or SQL assertions. No failed test was removed or weakened. Historical reports below are not current acceptance.

## Reproduce in cloud

```sh
./scripts/setup.sh
npm test
npm run typecheck
npm run lint
npm run build
PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=./work/browsers NODE_USE_ENV_PROXY=1 \
  PRAXIS_COVERAGE_BASE=8f1e8847b31fc0b81fd17c1bdacfa626dc737f1e \
  .pushgate/run.sh --mode=cloud
.venv/bin/python evidence/final/suite-execution.py
```

The full gate additionally needs Docker or native PostgreSQL, Gitleaks on PATH or `work/gitleaks/gitleaks`, and cached/downloadable pinned free CPU ONNX models. The Docker fallback defaults to `postgres:17-alpine`; the receipt records its actual digest. Network-restricted cloud Node requires inherited proxy/CA settings, with `NODE_USE_ENV_PROXY=1`. Never disable TLS verification. Browser/model downloads stay in cloud. No paid API is needed.

New acceptance scripts support `PRAXIS_EVIDENCE_DIR` to preserve historical receipts. The gate writes under `evidence/final/gate` by default and diagnostic logs under ignored `.pushgate/reports`. Keep source identity alongside copied receipts. Credentials, private SQLite files, model weights, node_modules and browser binaries are not committed.

Remaining release limits: loopback/single-process design; cooperative cancellation; no task resume or per-agent-step durable streaming; operator-supplied schemas have no OS resource isolation; bounded signature inspection is not malware scanning; no public moderation/retention/organizations runtime; no official trusted ranking, hardened arbitrary-code executor or hosted feature parity. A separate hosted project, approval, secrets, integration and actual-URL acceptance are required before deployment.

---

## Historical checkpoint (superseded by the dated cloud results above)

# Verification — 2026-11-03

**Overall: partial acceptance; full quality gate is NOT green.** The implemented local control plane, evaluation logic and frontend build are integrated. HTTP listener/browser, real inference, production cloud workflows and Postgres authorization are not verified. No public deployment occurred.

| Command or demonstration | Actual result | Scope / limitation |
|---|---|---|
| `npm run build` | PASS | React production build, shared contracts, TypeScript Worker typecheck, bundled Worker, Python compilation and distributable runner wheel (6 suites / 40 scenarios). Web JS gzip ~78 KiB. React Router emits harmless ignored `use client` bundle warnings. |
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

## Build completeness follow-up

The root `npm run build` now builds all existing components, rather than only the frontend and Worker typecheck. It emits a fail-fast manifest with hashes and validates that the wheel contains all six suite files and 40 scenarios. `scripts/setup.sh` and CI now install the Python packaging tools required by the unified build. This does not resolve the unsupported features or environment-blocked acceptance checks listed above.

The distributable wheel was installed into `work/wheel-smoke`, then imported and executed outside the source checkout with no inherited PYTHONPATH. Six suites / 40 scenarios loaded; 8 model-fixture tasks and 4 executable agent-fixture tasks passed; world levels were 1/5/12 entities. This verifies packaging and demo execution, not real inference. See `evidence/verification/wheel-smoke.json`.
