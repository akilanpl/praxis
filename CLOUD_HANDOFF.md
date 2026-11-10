# Current independent review handoff — 2026-11-10

Remain in the same managed Cloud checkout `/workspace/praxis`, branch `codex/praxis-final-release`. Original six commits through `8a2fe33` are preserved. PR #2 was already merged to main `914d226` before review. The user explicitly requests branch-only publication: no new PR, no merge, no main push or force push. GitHub access was restored using private CLI config outside this repository; never print credential files or tokens, and do not reuse historical Mac procedures or credential-blocker claims below as current state.

Read `docs/qa/INDEPENDENT_PR_REVIEW.md`, `PRODUCTION_READINESS_REVIEW.md`, current `VERIFICATION.md` and `evidence/review`. Core findings are repaired with new commits. Exact tested source and final gate receipts are recorded there. TypeScript coverage now includes both frontends, Worker and contracts; Python coverage traces actual Playwright greenlets. Failed mobile/regression receipts remain evidence. SAST warnings remain unsuppressed and triaged. No deployment/paid resources/remote migrations are authorized or performed.

---

# Current cloud handoff — 2026-11-10

The historical handoff below is retained for provenance. Current work uses managed Codex Cloud `/workspace/praxis`, origin `https://github.com/akilanpl/praxis.git`, branch `codex/praxis-final-release`, based on main `8f1e884`. Do not follow historical Mac/Terminal paths or backup exceptions: all source, dependencies, browser artifacts and Git operations for this mission stay in cloud. No deployment or paid resources are authorized.

Read `docs/qa/FINAL_AUDIT.md`, `VERIFICATION.md` and `evidence/final/` for this release. Four implementation commits harden execution/evidence, add the separate website and adapt acceptance to constrained cloud storage. The full Python suite has 140 tests plus 44 subtests. Real ONNX 135M/360M runs each scored 0/8; fixture results remain separate. Native PostgreSQL is tested through an actual network-isolated disposable container, not mocks. Hosted Supabase Auth and production deployment remain outside acceptance.

GitHub API calls return 401 Bad credentials for the configured GH_TOKEN. Never print tokens or compensate with local downloads. A branch push/PR must use restored authorized GitHub access and the existing gate; no bypass or force push. See final report for the actual publication outcome.

---

# Continue Praxis in Codex Cloud

Existing repository only; preserve the architecture and all evidence. Start on feature/qa-hardening-release.

## Verified work
- Main lineage: 57a3575 -> a9e85fa -> a4435f1 -> 841d8a9. c65d89c contains real acceptance work.
- Python 3.12.13 runtime replaces insecure/EOL 3.9 environment; frozen dependencies in requirements-lock.txt. Older environment remains ignored under work/.
- Latest full Python run: 116 top-level tests passed (44 additional nested subtests), including real loopback HTTP adapters. Worker suite: 14 passed.
- Two real pinned CPU ONNX models, SmolLM2 135M and 360M, ran through an OpenAI-compatible endpoint and persisted raw inputs/outputs, usage, timings and assertions. Both scored 0/8 on strict structured-agent. This is not a fabricated success score.
- Complete Chromium journey previously PASSED: registration, two real connections, suite runs, reports, matched comparison, 1/5/12-entity world replay, inert HTML/WAV upload, other-owned blinded voting, identity reveal and duplicate rejection. Evidence under evidence/release/browser/.
- Native PostgreSQL 15.19 host run passed schema application, ownership/forgery checks, all 28 RLS tables, run/evidence persistence and vote uniqueness. Uses local auth.uid claim fixture; hosted Supabase Auth is NOT verified. Successful host evidence preserved in postgres-host-passed.json.
- Builds and installed runner wheel succeeded. Wheel loads 6 suites/40 definitions and executed 12 demo fixture tasks; do not claim 40 real-model executions.
- Latest Python and Node dependency audits found no known vulnerabilities. Gitleaks scanned history/staged source with no leaks after omitting public idempotency nonces. Provider keys are not tracked.

## Immediate blockers and next actions
1. Read .pushgate/reports/c65d89c*.json and associated logs if available locally; the committed release evidence includes the earlier passing browser run. Latest gate is INCOMPLETE: macOS sandbox denies native PostgreSQL shared memory; a later browser attempt timed out waiting for Continue to become stable. Do not label that attempt passed. Diagnose isolated browser contexts, background tab animation scheduling and Playwright/Chrome version compatibility; never force-click or disable security to green tests.
2. Linux cloud should remove macOS IPC/shared-memory limitations. Run npm ci; create Python 3.12 venv; pip install --upgrade pip 'setuptools>=84.1,<85' wheel; pip install -e '.[test,browser]'; install Chromium with Playwright and native PostgreSQL.
3. Run .pushgate/run.sh. It starts bounded real CPU model servers if missing, runs build/wheel/116 Python/14 Worker/native DB/browser/audits, and records a deterministic score. No paid model API needed. Keep root hooks enabled. The QA branch threshold is 80; unknown whole-product diff coverage conservatively caps the score at 89; main/release threshold is 90. No production readiness is implied.
4. Fix remaining regression/acceptance defects; preserve before/after evidence. Update README/VERIFICATION/IMPLEMENTATION_STATUS, which retain older historical limitations and Python version text.
5. Public deployment is NOT performed. Cloudflare CLI is unauthenticated, no approved dedicated Praxis Supabase project exists, and the Worker remains metadata-only. Frontend Supabase auth/runner dispatch and hosted feature parity are unfinished. Do not mutate unrelated connected Supabase projects or publish a static UI as a fully working cloud product. Obtain specific deployment authority/credentials; no paid resources without approval.
6. Continue meaningful commits, full security testing and exact deployed smoke if deployment becomes authorized. Do not merge to main without an accepted protected-branch gate.

## Local-only resources not in Git
Ignored work/ includes downloaded Chromium, small model weights, native PostgreSQL clusters, Gitleaks binary and virtualenvs. They are reproducible, not source. Private SQLite evidence is under .praxis/; shareable actual model reports/screenshots are tracked. No secrets, dependencies, caches or model binaries should be pushed.

The latest push request is an urgent preservation handoff because the user's battery is low, not a declaration of release acceptance.

## Battery-critical remote checkpoint

Private GitHub repository: https://github.com/akilanpl/praxis
Branch: feature/qa-hardening-release. Initial emergency backup commit: 9213301.
User explicitly approved the backup-only push despite the incomplete gate. Ordinary hooks remain enabled; the exception is audited in .pushgate/bypass.log.

Codex CLI authenticated successfully and listed zero existing tasks. Repository-specific cloud environment lookup returned HTTP 403, detail type repo_not_accessible, message Repository is not accessible. No cloud task was submitted. The user must enable access to this private repository in the Codex GitHub connection and create/select its cloud environment. Then submit a cloud task on feature/qa-hardening-release with: "Read CLOUD_HANDOFF.md completely and continue the final Praxis integration/acceptance mission. Preserve evidence, fix the incomplete gate, and do not claim public deployment or tests passed without execution."

Do not substitute an unrelated cloud environment or change repository visibility to work around the missing authorization.

Current local-first decision: controlled POSIX beta, with qualified Ubuntu/macOS fixture lifecycles and unsupported native Windows. Cloud hosting deferrals are separate. See [local qualification](docs/qa/LOCAL_RELEASE_QUALIFICATION.md) and [recovery operations](docs/operations/LOCAL_INSTALLATION_RECOVERY.md).
