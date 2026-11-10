# Frontend review checkpoint — 2026-11-10

**READY FOR FRONTEND REVIEW.** Dedicated branch `codex/praxis-frontend-revamp` preserves the local-first backend and independent website. The redesigned shell, registries, immutable suite editor, evidence inspectors, reports and local settings are documented in [frontend handoff](docs/frontend/FINAL_HANDOFF.md), with source-bound [evidence](evidence/frontend/). Current gate: 339 checks; 286 Python tests + 44 subtests, 57 Vitest tests and 14 Worker tests. Latest remote standard/full-gate/frontend-browser checks passed at `daa8bd8`; native Linux/macOS passed and Windows remains unsupported with a visible failure. This frontend verdict does not upgrade the existing controlled POSIX beta to production. No deployment, PR or merge occurred. Earlier checkpoints below remain historical.

# Current independent review verification — 2026-11-10

**Verdict: READY FOR REVIEW.** This checkpoint supersedes the historical verification below. No public deployment or hosted identity certification follows from these results.

Review starts from original HEAD `8a2fe33468d14363152d7deca5179c6ab1c91267`; all six original commits are preserved. PR #2 was already merged before review. Fetched main is `914d2267acdd541348fa247ad773b333504ce311`. User requests branch-only publication on `codex/praxis-final-release`, no new PR or merge. Source tested by the full gate: `375688f0c872d7636a33b750441033b3aef4031e`. Following documentation/evidence updates do not change executable source; the normal pre-push gate also runs at the final branch HEAD.

All source, dependencies, private test databases, model weights, browser artifacts and Git operations remain in the original managed Codex Cloud workspace. Runtime: Python 3.12.14, Node 24.22.1, npm 11.9.0, locked Playwright 1.64.1/Chromium 156.0.8078.4. App Vite 6.4.5/React 19.1.0 remain unchanged; patched Vitest/coverage-v8 5.1.0 are separate test tooling. Full test tooling requires Node 22.12+ and Chromium. Optional Bandit is pinned at 1.8.6; locks include all additions.

| Area | Result | Exact command / evidence and scope |
|---|---|---|
| Independent baseline audit | PASS | `evidence/review/original-commits.txt`, `original-changed-files.txt`, `current-main-diff.txt`: six original commits, 165 historical changed files, empty content diff against merged main before remediation. Findings and evidence audit in `docs/qa/INDEPENDENT_PR_REVIEW.md`. |
| Python suite | PASS | `pytest tests -q --cov=praxis --cov-branch ...`: **276 tests + 44 subtests**, no skips. `evidence/review/python.log/xml`. |
| Python statement / branch coverage | PASS | **97.19% statements / 91.43% branches**, targets 90/85. `python-coverage.json`, no exclusions. Scope is the distributed runner package, including module entrypoint and actual owned-browser code via greenlet/thread tracing. Operational/QA scripts are exercised and SAST-reviewed separately; that percentage is not claimed for every repository Python script. |
| Controlled TypeScript tests | PASS | `npm run test:typescript`: **39 tests** for frontend transport/session/forms/loading/errors, website, Worker routes/negative boundaries and contracts. DOM and Supabase transport are controlled, not hosted acceptance. `typescript.log`, `typescript/coverage-final.json`, `coverage-summary.json`, HTML report. |
| Changed TypeScript executable lines | PASS | **99.02%**, target 85; changed security-sensitive TS branch outcomes **89.57%**, target 80. `coverage-targets.json`: actual git hunks against main + Istanbul statement/branch maps; both frontends, Worker, contracts included, missing files fail. Whole TS report is separate from Python. |
| Original Worker tests | PASS | `node --import tsx --test apps/api/test/security.test.ts`: **14 tests retained**, controlled transport. `worker.log`; this is not hosted Supabase Auth. |
| Compiler lint / type checks | PASS | `npm run lint`, `npm run typecheck`: all four workspaces; lint is compiler unused-local/parameter checking, not an ESLint/style certification. `lint.log`, `typecheck.log`. |
| Builds / wheel | PASS | `npm run build`: evaluation UI, separate website, shared contracts, Worker dry-run bundle, Python compilation, wheel. `build.log`, `build-manifest.json`, `acceptance/wheel.json`: installed wheel away from source, six suites/40 definitions and 12 explicit fixture tasks. |
| Reproducible installation | PASS | Documented `./scripts/setup.sh` completes after lock changes (`setup.log`). A fresh `work/review-fresh-install` virtualenv installs `requirements-lock.txt` and runs six-suite registry/eight-task explicit fixture (`fresh-install.log`, `fresh-install-smoke.json`). No neural inference is claimed for installation smoke. |
| All public scenarios | PASS | `scripts/suite_acceptance.py`: all six suites, 40 positive + 40 negative task executions; model/tool fixtures explicitly labeled; application checks use an actual owned HTTP server. `acceptance/suite-matrix.json`, `suite-runs/`. |
| Actual HTTP security / integration | PASS | `security-http.py/json`: 12 live loopback checks through Handler/SQLite for Host/Origin, owner isolation, trust rejection, inert uploads and revocation. Python also uses an actual owned HTTP service that commits then disconnects, proving POST is not replayed. Provider protocol/timeout HTTP tests remain enabled. |
| Actual PostgreSQL / RLS | PASS | `scripts/postgres_container_check.py`: actual PostgreSQL 17.11 Alpine, network disabled, source-bound receipt/image digest. Schema/migration equality, selected ownership/trust SQL, all 28 RLS-enabled tables, concurrent idempotency, transaction rollback, cross-user read denial and restart persistence. `acceptance/postgres.json/log`. Local auth.uid/JWT-claim fixture; not exhaustive hosted business acceptance. |
| Hosted Supabase identity | NOT VERIFIED | No approved dedicated hosted environment or identity credentials. Mocked Worker tests and local claims are not substituted for hosted Auth. |
| Real model task results | FAIL | Source-bound actual CPU ONNX browser runs each scored **0/8 structured-agent v1.0.0 tasks**. Invocation/persistence/grading completed, task assertions failed. `acceptance/browser/run-1.json`, `run-2.json`; self-reported, not fixture inference or official leaderboard certification. |
| Production-built browser workflows | PASS | `scripts/browser_check.py`: actual browser → HTTP → SQLite, two real models, reports, comparisons, replay, inert uploads/WAV, other-owned voting and duplicate denial, navigation; report/dashboard checks at **390/768/1280** and zero browser errors. `acceptance/browser/result.json` and screenshots. |
| Website production browser | PASS | `scripts/website_check.py`: actual built static site, three widths, anchors/semantic heading/skip navigation/no local asset or browser errors. `acceptance/website/result.json` and screenshots. Not exhaustive WCAG or actual hosting acceptance. |
| Backup / recovery | PASS | `tests/test_backup_recovery.py`: actual SQLite backup + referenced object hashes, new-directory restore, owner/session/artifact recovery, corruption and future-schema denial, private file modes. Snapshot tooling never overwrites an active workspace. |
| Secret/dependency scans | PASS | Gitleaks history/staged changes and complete npm/pip audits report no known findings. `gitleaks.*`, `npm-audit.json`, `python-audit.json`. Initial advised Vitest version was replaced, not suppressed; before-report retained. |
| SAST | PARTIAL | Unsuppressed Bandit runner/scripts scan has no HIGH finding. Assertion, subprocess, controlled loopback URL and synthetic test SQL flags remain in `bandit.json/log` with per-location contextual `security-triage.json`. No external penetration or ASVS certification. |
| Deployment/operations | NOT VERIFIED | Application/website/Worker are not deployed. Actual public TLS/domain/headers/monitoring, hosted retention/backup/account lifecycle and edge abuse controls require separate approved resources and acceptance. |

The full local feature gate passes **329 scored checks, internal score 100/100**, at the exact executable source above. `evidence/review/gate-receipt.json` preserves commands, exit codes, durations, code hashes and clean-source identity; `gate-summary.md` records scope. This is internal test accounting, not a production or security certification. Combined changed Python/TS executable-line evidence is measured, not the old unknown coverage cap. Explicit Python/TS threshold checks fail closed.

The earlier stricter browser attempt failed on 390px report overflow and is retained as `mobile-failed-gate.json`, `mobile-failed-browser.log` and `report-layout-red.*`. The repair wraps compact event JSON and provides readable keyboard-focusable table scrolling; it does not hide overflow to pass. Red regression output is retained. Original 186-check/89-score and 0/8 model receipts are preserved under `evidence/final`; audited limitations are recorded in `acceptance-claim-audit.json` and `historical-evidence-audit.json`.

## Exact reproduction in the cloud checkout

```sh
./scripts/setup.sh
PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=./work/browsers npm test
npm run test:typescript
npm run typecheck
npm run lint
npm run build
PLAYWRIGHT_BROWSERS_PATH=./work/browsers NODE_USE_ENV_PROXY=1 \
  PRAXIS_COVERAGE_BASE=914d2267acdd541348fa247ad773b333504ce311 \
  PRAXIS_EVIDENCE_DIR=./work/review-verification .pushgate/run.sh --mode=review
.venv/bin/python evidence/review/security-http.py
```

Full gate prerequisites: Chromium, locked browser/test packages, Gitleaks on PATH or `work/gitleaks/gitleaks`, and native PostgreSQL or the managed local Docker daemon. Pinned free CPU ONNX models are cached/downloaded in cloud only. The Docker fallback uses the official PostgreSQL 17 Alpine image and records the actual digest. No paid model API is required. New acceptance output defaults to ignored `work/acceptance/<SHA>`; source-bound receipts fail on stale/missing/dirty-source evidence. CI uploads current evidence; historical receipts are never proof of later code by themselves.

Current deployment/recovery checklist and component contracts: [PRODUCTION_READINESS_REVIEW.md](docs/qa/PRODUCTION_READINESS_REVIEW.md). Findings/status: [INDEPENDENT_PR_REVIEW.md](docs/qa/INDEPENDENT_PR_REVIEW.md). All original commits remain preserved. No new PR, merge, main push, force push, paid provisioning or production deployment is performed.

---

## Historical pre-review verification (preserved)

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

## Branch publication follow-up

Commit `b760fbbe59b3a2e8629651058bfc5f570e2d1326` passed the 329-check cloud-workspace gate and both remote GitHub workflows: [Praxis verification](https://github.com/akilanpl/praxis/actions/runs/42787331622) and [pushgate](https://github.com/akilanpl/praxis/actions/runs/42787331880). See `evidence/review/publication-verification.json`. The standard test command now runs 276 Python tests plus 44 subtests, 39 Vitest tests and 14 Node Worker tests. Coverage remains 97.19% runner Python statements, 91.43% branches, 99.02% changed TypeScript executable lines and 89.57% security-sensitive TypeScript branch outcomes against the review baseline.

CI follow-ups separate Vitest files from Node test discovery, explicitly bind acceptance subprocesses to checkout sources, isolate wheel installation from checkout metadata, compare changed-source coverage with the PR/default branch rather than the preceding push, and bound native PostgreSQL commands while retaining restart logs. Both native PostgreSQL CI acceptance and network-isolated PostgreSQL container acceptance passed; neither establishes hosted Supabase Auth acceptance. Failure identifiers are available through check annotations without exposing raw test logs. Previous failing runs remain visible.

The user authorized pushing the existing branch only. No new PR was created, no PR was merged, no main push or force-push occurred, and nothing was deployed. The original six commits remain ancestors. The engineering verdict remains **READY FOR REVIEW**. Approved hosting/domain/HTTPS configuration, hosted identity acceptance, operational controls and the documented security/retention requirements remain external production prerequisites. Actual model performance remains 0/8 for each of the two local SmolLM2 models. This documentation follow-up is verified again by the normal pre-push gate and GitHub workflows; their exact-commit results are available in Actions rather than self-referential committed receipts.

## Local-first release qualification (supersedes the earlier review-only verdict)

**READY FOR CONTROLLED BETA** for qualified POSIX local use. [Qualification matrix](docs/qa/LOCAL_RELEASE_QUALIFICATION.md) records the precise scope: fresh Linux genuine-inference lifecycle, native Ubuntu 24.04 and macOS 15 fixture lifecycles, and an actual Windows failure (unsupported). The normal gate passed 339 checks at `daa847c`, with 286 Python tests + 44 subtests, 39 Vitest tests and 14 Worker tests. The final commit repeats the gate and native matrix; failures remain visible. Deferred cloud services do not gate the local product.

Backup verification now requires exact DB/manifest uploaded-object references and foreign keys, escaped read-only SQLite URIs and durable POSIX publication. Tests cover actual process kill/restart, SQLite full/permission denial, corruption, malformed providers, duplicate requests, future schema and explicitly injected ENOSPC failures. An older assertion proof refuses optimized Python. Every retained Bandit location is assessed in [SAST review](docs/qa/LOCAL_SAST_REVIEW.md); 130 findings remain unsuppressed, with no HIGH and no demonstrated flagged runtime exploit. Accessibility sampling used actual Chromium/axe and keyboard input; it is not WCAG certification. See [installation/recovery](docs/operations/LOCAL_INSTALLATION_RECOVERY.md), [safe evidence](evidence/local-release/) and the matrix for limits. No deployment, main modification, merge, new PR, paid infrastructure or production credential configuration occurred.
