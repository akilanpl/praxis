# Current post-publication status — 2026-11-10

**READY FOR REVIEW**, within documented component contracts. Original PR #2 was already merged before this review. All six original commits remain ancestors; new review/remediation commits stay on `codex/praxis-final-release`. User directs branch-only publication, no new PR or merge.

Independent review reproduced and repaired mutation replay, false-positive exhausted agents, redaction corruption, capped internal integrity lookups, stale-session UI behavior, upload durability, malformed input and mobile report defects. Password hashes now have a versioned 600,000-round format with compatible on-login upgrades. Backup/new-directory restore and future-schema refusal are tested.

Current runner verification: 276 Python tests + 44 subtests; 39 controlled TypeScript tests plus the original 14 Worker tests. Python and changed TypeScript coverage targets are met without exclusions. Production-built browser acceptance, actual PostgreSQL concurrency/rollback/restart, source-bound receipts, package installation and all-six-suite positive/negative executions are documented in VERIFICATION.md. Real ONNX task results remain 0/8 each. SAST findings are retained with contextual PARTIAL triage, not hidden.

No application, website or Worker production deployment has occurred. Hosted Supabase identity, public edge controls, domain/HTTPS/headers, operational monitoring and hosted recovery require dedicated approved environments and acceptance. Arbitrary untrusted code, cloud product parity, official trusted ranking and the other unsupported capabilities below remain outside scope.

See [independent review](docs/qa/INDEPENDENT_PR_REVIEW.md), [production/recovery contracts](docs/qa/PRODUCTION_READINESS_REVIEW.md), and current evidence under `evidence/review`.

---

## Historical implementation checkpoint

# Implementation status — 2026-11-10

**Local release candidate; hosted product acceptance remains partial. No public deployment.**

Implemented: authenticated loopback workspace; owner-scoped SQLite WAL; model/agent/application registry; versioned suite authoring/cloning/export; OpenAI-compatible/Ollama/custom protocols; bounded tool agents with actual state assertions; authorized HTTP contracts; deterministic reference worlds; persisted events/results; inert artifact/media inspection; JSON and printable HTML reports; condition-matched local comparisons and blind voting; separate metadata Worker and PostgreSQL RLS schema.

Added/hardened in this release: elapsed HTTP read deadlines, malformed-provider classification, credential reflection redaction, usage aggregation, safe configuration capture, named unexecuted tasks/full category denominators, suite token bounds, version-qualified suite inspection, complete restart/idempotency queries beyond the list cap, atomic final run/artifact metadata, agent error traces, explicit HTTP target authorization acknowledgement, HTTP framing rejection and escaped assertion expectations/observations in reports.

The separate professional website is implemented at `apps/website`, using the existing React/Vite toolchain. It imports actual suite counts, explains the architecture and unsupported boundaries, links historical 0/8 model results, and does not advertise a live application. Root build includes it.

Current cloud checks include the full Python suite (140 tests plus 44 subtests), 14 controlled-transport Worker tests, all TypeScript checks, component builds, installed wheel execution, real loopback HTTP, actual disposable PostgreSQL 17 ownership/persistence/RLS checks, fixture and real-model browser journeys, and website screenshots at 390/768/1280 pixels. Both new real CPU ONNX model runs passed infrastructure acceptance but scored 0/8 on structured-agent. See VERIFICATION.md and evidence/final for exact commands/source scope; this paragraph does not certify hosted Auth.

Unsupported: full hosted workflows, collaborative cloud organizations, R2/queues, operator-trusted runs/official rankings, arbitrary untrusted code/HTML execution without a hardened external executor, external-model-driven adaptive worlds, streaming, individual-task resume, held-out datasets, learned judges, multimodal generation/quality inference, automatic pricing, production moderation/retention.

External requirements: functioning GitHub write credentials for publication; separately approved deployment environments and production credentials; hosted Supabase Auth/Worker and frontend integration acceptance; actual-URL smoke testing. No paid resources, remote database migrations or public deployment were performed.

## Branch publication follow-up

Commit `b760fbbe59b3a2e8629651058bfc5f570e2d1326` passed the 329-check cloud-workspace gate and both remote GitHub workflows: [Praxis verification](https://github.com/akilanpl/praxis/actions/runs/42787331622) and [pushgate](https://github.com/akilanpl/praxis/actions/runs/42787331880). See `evidence/review/publication-verification.json`. The standard test command now runs 276 Python tests plus 44 subtests, 39 Vitest tests and 14 Node Worker tests. Coverage remains 97.19% runner Python statements, 91.43% branches, 99.02% changed TypeScript executable lines and 89.57% security-sensitive TypeScript branch outcomes against the review baseline.

CI follow-ups separate Vitest files from Node test discovery, explicitly bind acceptance subprocesses to checkout sources, isolate wheel installation from checkout metadata, compare changed-source coverage with the PR/default branch rather than the preceding push, and bound native PostgreSQL commands while retaining restart logs. Both native PostgreSQL CI acceptance and network-isolated PostgreSQL container acceptance passed; neither establishes hosted Supabase Auth acceptance. Failure identifiers are available through check annotations without exposing raw test logs. Previous failing runs remain visible.

The user authorized pushing the existing branch only. No new PR was created, no PR was merged, no main push or force-push occurred, and nothing was deployed. The original six commits remain ancestors. The engineering verdict remains **READY FOR REVIEW**. Approved hosting/domain/HTTPS configuration, hosted identity acceptance, operational controls and the documented security/retention requirements remain external production prerequisites. Actual model performance remains 0/8 for each of the two local SmolLM2 models. This documentation follow-up is verified again by the normal pre-push gate and GitHub workflows; their exact-commit results are available in Actions rather than self-referential committed receipts.

## Local-first release qualification (supersedes the earlier review-only verdict)

**READY FOR CONTROLLED BETA** for qualified POSIX local use. [Qualification matrix](docs/qa/LOCAL_RELEASE_QUALIFICATION.md) records the precise scope: fresh Linux genuine-inference lifecycle, native Ubuntu 24.04 and macOS 15 fixture lifecycles, and an actual Windows failure (unsupported). The normal gate passed 339 checks at `daa847c`, with 286 Python tests + 44 subtests, 39 Vitest tests and 14 Worker tests. The final commit repeats the gate and native matrix; failures remain visible. Deferred cloud services do not gate the local product.

Backup verification now requires exact DB/manifest uploaded-object references and foreign keys, escaped read-only SQLite URIs and durable POSIX publication. Tests cover actual process kill/restart, SQLite full/permission denial, corruption, malformed providers, duplicate requests, future schema and explicitly injected ENOSPC failures. An older assertion proof refuses optimized Python. Every retained Bandit location is assessed in [SAST review](docs/qa/LOCAL_SAST_REVIEW.md); 130 findings remain unsuppressed, with no HIGH and no demonstrated flagged runtime exploit. Accessibility sampling used actual Chromium/axe and keyboard input; it is not WCAG certification. See [installation/recovery](docs/operations/LOCAL_INSTALLATION_RECOVERY.md), [safe evidence](evidence/local-release/) and the matrix for limits. No deployment, main modification, merge, new PR, paid infrastructure or production credential configuration occurred.
