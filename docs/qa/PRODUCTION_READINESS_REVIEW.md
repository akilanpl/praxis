# Production readiness review and release contracts

Review date: 2026-11-10. All engineering/verification takes place in the existing Codex Cloud workspace. No deployment, production secret, paid resource or remote migration is authorized. PR #2 is already merged; the user requests new commits on the existing branch only, no new PR.

Overall verdict: **READY FOR REVIEW**, with final exact-source gate evidence recorded in VERIFICATION.md. Passing tests do not establish production hosting. Component contracts differ.

## Local evaluation application

**Supported contract:** private loopback-only, single-process workspace on an operator-controlled Linux host, Python 3.12+, Node 22.12+ for checkout tooling, POSIX shell, npm and reproducible lockfiles. Cloud verification uses Python 3.12.14 / Node 24.22.1; GitHub CI supplies a separate Node 22/Linux check. Windows/macOS and arbitrary packaged GUI installers are NOT VERIFIED in this review. Wheel supports CLI/scenarios; the integrated UI must be built from the checkout.

**Security defaults:** literal application ownership/permission acknowledgement and distinct POST consent; POST never automatically replays after unknown outcome. Agent requires an actual final action, step permissions and real simulated state evidence. Known credentials are redacted before output grading, protocol field names remain stable, payload key collisions fail closed. Accounts use versioned PBKDF2-HMAC-SHA-256 at 600,000 rounds, legacy successful-login upgrades, and expiring hashed bearer sessions, ownership checks, exact browser origins/loopback hosts, no cookie authority. Database/new workspace/object/backup permissions are private (600 files, 700 directories). HTML stays inert; untrusted executable workloads remain unsupported. The user-controlled local runner intentionally permits owned loopback endpoints and is not a public URL proxy.

**Persistence/recovery:** SQLite WAL with transactions for final run/artifact rows; full internal history queries independent of display limits; atomic fsynced object publication. Interrupted runs are marked interrupted on restart, never resumed. Per-agent-step durable streaming and multi-process service coordination remain outside contract. Schema v0 is the current supported SQLite format; newer user_version is explicitly refused. No destructive automatic migration is implemented.

**Verified backup workflow** (all commands for this mission remain in cloud):

```sh
.venv/bin/python scripts/backup_workspace.py backup \
  --database .praxis/praxis.sqlite --directory work/private-snapshot
.venv/bin/python scripts/backup_workspace.py verify --directory work/private-snapshot
.venv/bin/python scripts/backup_workspace.py restore \
  --source work/private-snapshot --directory work/restored-workspace
```

Snapshot uses SQLite's backup API, then copies only object hashes referenced by the snapshot. Each file hash and database quick_check/schema are verified. Restore publishes a new directory and refuses to overwrite any existing workspace. Prompts, outputs, password hashes and sessions are private data; encrypt/offline-protect backups and control retention. No off-host upload or encryption-key provisioning is included. Backup isn't a deletion/retention service. A real test restores owner session, artifact bytes and hashes; corruption/unsupported schema tests fail closed.

**Upgrade/rollback checklist:** stop the old runner for upgrades; retain its exact Git SHA, locks and a verified snapshot; build/test the candidate in cloud; restore snapshot to a new directory for smoke testing; point PRAXIS_DB only at that disposable copy; verify login, targets/suites/history/artifacts and ownership. Do not open a newer schema with an older runner. Older runners cannot verify the strengthened password format; use the pre-upgrade snapshot when rolling back. Roll back by stopping the candidate and using the old runner with the pre-upgrade verified snapshot, preserving post-upgrade data for recovery. Never overwrite the only database/object copy. No guarantee of backward data migration is made.

**Operations:** keep loopback private; do not tunnel/port-forward the control plane. Provider credentials belong in process environment and can incur charges only when explicitly invoked. No credentials/bodies are logged; API failures have request IDs and sanitized messages. Full diagnostic logging, distributed quotas, automatic key rotation, public moderation/retention and account lifecycle operations are not production services here. A local privileged OS process can read the owner's files; logical accounts are not an OS sandbox.

## Static project website

**Implemented/build acceptance:** independent React/Vite static bundle, source-derived suite counts, explicit trust/status text, no trackers/login/runtime credentials. Production build and real Chromium checks cover desktop/tablet/mobile layout, semantic heading, keyboard skip, labels/anchors and browser errors. Controlled DOM tests add measurable source coverage. This is not exhaustive WCAG certification or external-link uptime monitoring.

**Deployment status: NOT VERIFIED / not deployed.** Missing dependencies: approved domain/origin, DNS/HTTPS/hosting access, deployment authorization and operational ownership. Do not claim a public URL. Canonical and og:url/social-image origin must use the real approved host; current metadata deliberately does not invent one.

**Before deployment:** choose approved static host; configure HTTPS redirects and HSTS only after HTTPS is confirmed; serve a restrictive CSP (default-src self; script-src self; style-src self; img-src self data; object-src none; base-uri self; frame-ancestors none), nosniff, Referrer-Policy, appropriate immutable caching for hashed assets and revalidation for index.html. Add the actual canonical/social URL. Validate headers, accessibility, external links and mobile layout at the real URL. Record artifact hashes and approved commit. Establish uptime/error monitoring without tracking users. Keep the prior static build/version for rollback and smoke-test rollback. None of these hosting steps has been performed.

## Optional metadata Worker

**Contract:** metadata-only experimental control plane; bearer token validation via Supabase Auth and user JWT forwarding to PostgREST. Never proxies endpoints, executes user workloads or claims hosted app parity. Strict payload schemas, byte/elapsed body bounds, fixed input buffer, exact CORS, no-store/nosniff/CSP, no client trust promotion. Owner RLS is authoritative.

**Acceptance:** controlled transport tests cover documented routing/auth/error decisions; actual local workerd smoke exercises unconfigured health/failure behavior. Actual disposable PostgreSQL checks schema, selected ownership/trust constraints, all 28 RLS-enabled tables, concurrent idempotency, transaction rollback, cross-user denial and persistence after restart. Local auth.uid/JWT-claim fixture is NOT hosted Supabase identity acceptance. Operator-owned cloud voting/approval paths remain unavailable.

**NOT READY for public hosting:** no approved dedicated Supabase/Cloudflare environment, production credentials, hosted Auth/account/session acceptance, edge rate/abuse controls, retention/account deletion, production observability or backup/recovery drill for a hosted database. R2/orgs/queues/official rankings/runner dispatch are not implemented. Do not mutate unrelated connected projects or use service-role bypasses.

**Before optional cloud acceptance:** obtain explicit approval and budgets for a dedicated test environment; configure publishable key, correct HTTPS Supabase origin and exact frontend origin; validate real isolated accounts and revoked/expired tokens with RLS; run migrations only against the approved disposable environment; implement edge quotas and lifecycle/retention policy; test hosted backups/restore and monitoring; verify actual URL and security headers; record rollback/migration compatibility. All production/paid/remote migration steps require separate approval.

## Security tooling and interpretation

Dependency audits and secret scans remain enabled, no findings are hidden to green a pipeline. Bandit scans runner and verification scripts without exclusions/suppressions; raw output is retained. Its assertion/subprocess/loopback URL/test SQL findings require contextual triage: test SQL values are source-controlled synthetic constants; subprocesses use argument arrays without shell; fixture URL calls use explicit loopback services; reference world PRNG is reproducibility, not cryptography; token examples are fixtures. No new verified SQL injection or arbitrary-code path follows from those flags. SAST is PARTIAL pending documented triage, not a zero-warning certification. OWASP ASVS/session/SSRF guidance informs the threat model but provides no certification.

## Final gate requirements

Complete Python/TypeScript tests, compiler lint/typechecks, production builds and wheel, security/audit scans, source-bound receipts, measured Python >=90/85 statement/branch coverage, changed TS >=85 executable-line coverage and >=80 security-branch coverage, actual PostgreSQL restart/concurrency, real-model browser journey, fixture regression matrix and responsive website checks. Preserve original historical 0/8 model results; a successful invocation is not a passing model task. Final numbers and exact source commit belong in VERIFICATION.md and the independent review resolution section.

Publication evidence: the staged default Gitleaks scan initially reported 45 generic-key candidates. Each was verified as a public source-file SHA256 digest. Published provenance maps use reversible explicit path/sha256 entries; no values were removed and no scan rules were excluded. See `evidence/review/provenance-publication.json`. Generated coverage HTML retains tool-emitted whitespace. The user authorized a branch push only; no new PR or merge is authorized.
