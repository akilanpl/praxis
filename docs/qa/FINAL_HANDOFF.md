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
- Following commits synchronize docs and preserve acceptance evidence; see Git log and final chat handoff for their exact IDs/publication outcome.

No main overwrite, force push, branch deletion or historical evidence deletion. No PR is claimed without successful GitHub creation. Changed-file manifest: `evidence/final/changed-files.txt`.

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
