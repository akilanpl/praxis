# Current post-publication engineering handoff — 2026-11-10

## A. Implementation summary

Independent review of all original six commits reproduced and repaired P1 mutation replay and false-positive agent step exhaustion, plus material P2 redaction, internal lookup, stale-session, object durability, malformed input and mobile report defects. Passwords now use versioned 600,000-round PBKDF2 with compatible on-login upgrades. Backup/new-directory restore, future-schema refusal, private permissions, elapsed inbound body limits and finite/nesting-bounded JSON are tested. Original commits and historical failures/evidence are preserved.

Review findings with commit/line/severity/reproduction and resolution: `INDEPENDENT_PR_REVIEW.md`. Component release/rollback contracts: `PRODUCTION_READINESS_REVIEW.md`. No new application architecture or hosted feature parity is invented.

## B. Architecture

Local React/Vite UI → session-aware transport → loopback Python control plane → SQLite WAL/hash-addressed objects/two-worker runner → model, permissioned simulated agent or authorized HTTP adapter. Separate deterministic reference worlds remain fixtures. The independent static website retains source-derived suite counts. The optional Worker remains metadata-only with user JWT forwarded to PostgREST/RLS; it never executes workloads or proxies user endpoints.

## C. Verification matrix

| Area | Result | Evidence |
|---|---|---|
| Python suite | PASS | 276 tests + 44 subtests, no skips; `evidence/review/python.log/xml` |
| Python coverage | PASS | 97.19% statements / 91.43% branches, runner-wide, no exclusions |
| TypeScript tests | PASS | 39 controlled DOM/transport tests, original 14 Worker tests retained separately |
| Changed TypeScript coverage | PASS | 99.02% executable lines / 89.57% security-sensitive branch outcomes, actual git/V8 maps |
| Compiler lint / types / builds / wheel | PASS | All workspaces, production static bundles, Worker dry-run, runner package |
| Installation | PASS | Documented setup plus fresh locked virtualenv smoke and installed wheel |
| HTTP / local web security | PASS | Real owned mutation-disconnect test and 12 actual Handler/SQLite ownership/origin/host/trust/revocation checks |
| PostgreSQL / RLS | PASS | Actual disposable PG17: schema, selected policies, 28 enabled tables, concurrent idempotency, rollback, cross-owner denial, restart |
| Hosted Supabase Auth | NOT VERIFIED | Synthetic local claims/controlled Worker transport do not certify hosted identity |
| Production-built browser | PASS | Actual model/HTTP/SQLite journey, report layouts at 390/768/1280, artifact/comparison/vote/replay flows |
| Model task quality | FAIL | Both actual SmolLM2 CPU ONNX models: 0/8 structured-agent tasks; invocation/persistence/grading completed |
| Website build/responsiveness | PASS | Fresh built-site Chromium evidence at three widths; not actual-host/WCAG certification |
| Backup/recovery | PASS | Real SQLite snapshot, object hash verification and new-directory restore, session/owner recovery and corrupt/future-schema denial |
| Secret/dependency scans | PASS | Gitleaks, npm/pip scans; no known findings |
| SAST | PARTIAL | Unsuppressed Bandit output and contextual triage retained; no HIGH finding, no external certification |
| Deployment / operational hosting | NOT VERIFIED | No public app/site/Worker deployment, dedicated hosted identity or live operational acceptance |

Exact executable source: `375688f0c872d7636a33b750441033b3aef4031e`. Full local feature gate: **PASS, 329 scored checks, internal 100/100**, with measured coverage rather than an unknown-coverage cap. This is internal check accounting, not production certification. See `evidence/review/gate-receipt.json`, `coverage-targets.json`, TypeScript/Python reports and source-bound `acceptance/` receipts. The normal pre-push gate also verifies final branch HEAD; CI results must be assessed at that exact SHA.

Earlier failing regression/mobile checks remain retained. Actual 390px overflow was repaired, not hidden. Full commands, environment and limits are in root VERIFICATION.md. All engineering and artifacts remain in the original Codex Cloud workspace; nothing was downloaded/copied to the user's Mac.

## D. Actual models

| Model | Suite | Tasks | Passed | Pass rate |
|---|---|---:|---:|---:|
| SmolLM2-135M-Instruct-ONNX, CPU q4 | structured-agent v1.0.0 | 8 | 0 | 0% |
| SmolLM2-360M-Instruct-ONNX, CPU q4 | structured-agent v1.0.0 | 8 | 0 | 0% |

Current raw outputs, assertions, usage, timings and model revisions: `evidence/review/acceptance/browser/run-{1,2}.json`. These are real local HTTP inference, not fixtures. All-six-suite positive/negative matrix uses explicit model/tool fixtures plus an actual owned HTTP fixture; it is not 80 neural-model tasks. Hashes are integrity checks, not independent attestations.

## E. Remaining blockers / scope exclusions

No identified P0/P1 finding remains open in the supported local/static contract. Hosted identity/dispatch/feature parity, approved deployment resources/domain/HTTPS/headers, actual-URL acceptance, edge rate/abuse controls, hosted account lifecycle/retention, monitoring and hosted recovery remain unverified prerequisites. SAST findings are contextually triaged rather than suppressed; comprehensive external penetration and accessibility audits remain unverified.

The local service is private, single-process and loopback-only. Arbitrary untrusted code/HTML lacks an external hardened executor and remains unsupported. Per-agent-step durable streaming, individual-task resume, cloud orgs/R2/queues, official trusted rankings, held-out suites, learned judges, multimodal quality inference, automatic pricing and model-driven adaptive worlds remain outside scope. A privileged local OS process can access the owner's data; local accounts are not OS isolation. Host support beyond tested Linux/Python/Node combinations is not certified.

## F. Deployment and recovery

**Application, website and Worker: not publicly deployed.** No production secrets, paid infrastructure, remote migrations, main writes or deployment were performed. Follow `PRODUCTION_READINESS_REVIEW.md` for explicit approval dependencies and the deployment/recovery checklist. Backup/restore publishes a new verified directory only. Keep a pre-upgrade snapshot and matching runner; old code does not understand strengthened password hashes or newer schemas. Retain the previous static artifact for eventual website rollback.

## G. Git and publication

Original PR #2 was already MERGED before review; main baseline is `914d226`. All original six commits through `8a2fe33` are retained. New commits remain on `codex/praxis-final-release`; user explicitly requests **push branch only, no new PR and no merge**. The historical GitHub credential blocker below has been resolved using private cloud CLI configuration outside the repository; never print or commit tokens. Final branch/remote SHA and CI URLs are reported after push.

New code/review commits: `871785e` review baseline; `1409dbd` evaluation/recovery fixes; `44edde2` TypeScript/session/security coverage; `a4be4cc` source-bound coverage/DB acceptance; `d4008c4` password compatibility/mobile reports; `375688f` finite/bounded JSON. Documentation/evidence commits follow. No rewrite, squash or force push.

## H. Verdict

**READY FOR REVIEW.** Evidence supports reviewing the remediated local workspace and static website. It does not justify production-hosting acceptance for any component with unmet identity, operational or deployment prerequisites.

---

## Historical pre-publication handoff (preserved)

# Praxis engineering handoff — 2026-11-10

## A. Implementation summary

Preserved the existing architecture and completed a bounded local release pass. Hardened malformed-provider classification, elapsed HTTP read deadlines, known-credential redaction, token limits, usage/configuration capture, unexecuted-task/category accounting, explicit HTTP authorization, version-qualified suites, restart/idempotency queries, atomic final artifact/result persistence, agent failure traces, request framing and printable reports. Improved frontend validation/loading/errors and added a separate professional project website with source-derived suite counts. See `FINAL_AUDIT.md` for findings, dependency map and regression evidence.

All operations used managed Codex Cloud `/workspace/praxis`. No source, archive, dependency, build or browser artifact was copied to the user's Mac. No production resources, paid API usage, public deployment or remote migration occurred.

## B. Architecture

Evaluation UI: `apps/web` → authenticated loopback Python API → SQLite WAL + hash-addressed objects + two-worker executor → distinct model, simulated tool-agent and owned HTTP adapters. Versioned scenarios and independent assertions produce retained outputs/traces/errors, task verdicts, JSON and printable HTML. Deterministic worlds remain a separate reference-policy subsystem.

Metadata cloud API: separate Worker → Supabase token validation → user JWT forwarded to PostgREST/RLS. It neither proxies user endpoints nor executes workloads and is not hosted product parity.

Project website: independent static React/Vite/TypeScript workspace `apps/website`, sharing the existing toolchain and actual suite definitions. It has no evaluation API dependency, login, third-party tracking or fake hosted demo. Root builds both frontends.

## C. Verification matrix

| Area | Result | Evidence |
|---|---|---|
| Python tests | PASS | `evidence/final/python.log`: 140 tests, 44 subtests, no skips |
| Frontend tests | PASS | `gate/browser/result.json`, explicit fixture `browser/result.json` |
| Frontend compiler lint / TypeScript | PASS | `lint.log`, `typecheck.log`; no separate style-lint claim |
| API/Worker tests | PASS | `worker.log`: 14 controlled-transport tests; `worker-runtime.json`: real local workerd smoke |
| Production builds | PASS | `build.log`, `build-manifest.json`; both frontends, contracts, Worker, wheel |
| HTTP integration | PASS | Python loopback regressions; `suite-matrix.json` with all four HTTP scenarios through an owned test server |
| PostgreSQL/RLS | PARTIAL | Actual PostgreSQL 17 schema/ownership/persistence tests passed, 28 tables have RLS. Hosted Supabase Auth NOT VERIFIED. `gate/postgres.json` |
| Browser acceptance | PASS | Full real-model browser → API → SQLite journey, uploads, replay, Arena, isolation, routes and layouts |
| Security checks | PASS | Gitleaks, npm/pip audits and security regressions; scoped acceptance, not external penetration certification |
| Model execution | PASS | Two genuine cloud CPU ONNX runs persisted and graded; quality results are 0/8 each |
| Website responsiveness | PASS | `gate/website/result.json` and inspected 390/768/1280 screenshots |
| Website build | PASS | Root build and website production browser test |
| Suite/evidence exports | PASS | 40 positive + 40 negative executions; result/output hashes, event sequence and escaped report verification |
| Whole-change executable-line coverage | NOT VERIFIED | Python statements 85.48%, branches 76.10%; frontend executable-line coverage absent |
| Hosted Auth / deployment | NOT VERIFIED | No dedicated hosted acceptance or deployment performed |

Local feature gate: **PASS — 186 checks, 89/100**. All executed checks passed. The conservative coverage cap is retained, not bypassed; the feature threshold is 80. This does not satisfy protected-main or production acceptance. `evidence/final/gate-receipt.json` identifies executable source `378d5d38782ee13921989bc71feef25f996f568d`. Subsequent changes are documentation/evidence only. Earlier disk-exhausted aggregate attempt remains `INCOMPLETE` in `preliminary-gate.json`.

Full commands, versions and evidence scopes are in `VERIFICATION.md`. The documented setup and isolated installed-wheel execution passed.

## D. Actual model evaluation results

| Model | Suite | Tasks | Passed | Real pass rate |
|---|---|---:|---:|---:|
| onnx-community/SmolLM2-135M-Instruct-ONNX, CPU q4 | structured-agent 1.0.0 | 8 | 0 | 0% |
| onnx-community/SmolLM2-360M-Instruct-ONNX, CPU q4 | structured-agent 1.0.0 | 8 | 0 | 0% |

Raw new reports, printable HTML and receipts are under `evidence/final/real-*`. These are actual model outputs, not fixtures. Infrastructure acceptance passes because real invocation/output persistence/grading completed; the task assertions failed. Results remain self-reported and public-task-specific. Earlier historical receipts are retained separately.

## E. Remaining blockers and unsupported scope

- GitHub API credentials return 401 Bad credentials; publication depends on a working authorized connection.
- No hosted Supabase Auth/complete cloud dispatch/frontend parity acceptance; no dedicated production credentials/project.
- No deployment approval, configured public origin, actual-URL smoke or live application/website. Website canonical/social origin and static response headers must use the eventual approved host.
- Frontend changed executable-line coverage is not measured. Browser journeys are passing but are not exhaustive visual/accessibility or business-state proofs.
- Single-process, loopback-only local service; public hosting requires a different reviewed operational boundary and distributed abuse controls.
- Cooperative cancellation; individual tasks cannot resume; per-agent-step state is retained on task completion/failure rather than durably streamed after every action.
- Custom suites/schemas are operator inputs without hostile-workload OS isolation. Arbitrary untrusted executable code/HTML is refused; a browser context is not a robust sandbox.
- No cloud organizations runtime, R2/queues, official operator-trusted ranking, held-out suites, learned judges, multimodal generation/quality scoring, automatic pricing, production retention/moderation pipeline or external-model-driven adaptive worlds.
- Artifact inspection is bounded byte/metadata inspection, not malware or perceptual certification. Uploaded bytes and metadata must be backed up together.
- PostgreSQL tests use synthetic auth claims and selected authorization paths; hosted identity and exhaustive business acceptance remain unverified.

## F. Deployment status

**Application: not publicly deployed. Website: not publicly deployed. Worker: not deployed.** Cloud loopback acceptance services are temporary verification infrastructure, not public hosting. No live URL is advertised. Production provisioning, secrets, remote migrations and paid operations require explicit approval.

## G. Git status

Branch: `codex/praxis-final-release`, based on main `8f1e884`.

- `a149af6` — execution/evidence/local boundary hardening and regressions.
- `b94f9a4` — separate engineering website, root build and browser acceptance.
- `4587c79` — constrained-cloud PostgreSQL image and frontend compiler lint.
- `378d5d3` — continue independent checks when an acceptance receipt is unavailable.
- `2a04e2d` — synchronized documentation and preserved cloud acceptance evidence.
- Final documentation-only commit records the publication blocker; its ID is in the final chat handoff.

No main overwrite, force push, branch deletion or historical evidence deletion. The actual push attempt failed before publication: Git could not read a GitHub username with terminal prompts disabled. The API also returned 401 Bad credentials. No remote branch or PR was created. The full log is `evidence/final/git-push.log`. Changed-file manifest: `evidence/final/changed-files.txt`.

Retry only from this cloud checkout after restoring GitHub access:

```sh
git push -u origin codex/praxis-final-release
gh pr create --repo akilanpl/praxis --base main --head codex/praxis-final-release \
  --title 'Harden Praxis evaluation evidence and add the engineering website' \
  --body-file docs/qa/PR_DESCRIPTION.md
```

The normal pre-push gate stays enabled. Do not use a bypass, force push or local download to compensate for missing access.

## H. Final engineering verdict

**READY FOR REVIEW.** Evidence supports reviewing the hardened local workspace and separate website. Passing local acceptance and real inference transport do not certify model quality, hosted identity, cloud feature parity, protected-main coverage or production deployment. Those limits remain explicit release requirements.
