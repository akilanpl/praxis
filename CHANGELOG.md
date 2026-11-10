# Changelog

## Frontend review — 2026-11-10

- Introduce a reusable dark/light design system, responsive workspace navigation and keyboard command palette without new runtime dependencies.
- Redesign data-derived overview, targets, immutable suites, run/assertion/trace inspection, inert artifacts, comparisons, reports and honest CLI-oriented settings.
- Preserve API/SQLite/evidence semantics and separate website; strengthen frontend session masking, stale-export guards and malformed suite editing.
- Add real local API/browser acceptance at six widths, eleven axe samples, complete PDF verification and measured route-split bundle budgets. Retain earlier failures and unsupported Windows qualification.
- Publish on the dedicated frontend branch for review; no deployment, merge or new PR.


## Post-publication review — 2026-11-10

- Preserve the original six commits and merged PR #2; publish remediation only on the existing branch, with no new PR or merge.
- Prevent POST mutation replay and passing agent step exhaustion; enforce literal mutation consent.
- Repair redaction protocol/key-collision handling and reject unsafe/non-finite/deep JSON, malformed HTTP and usage/action shapes.
- Remove presentation caps from internal integrity/history/active-run decisions; atomically persist private uploaded objects and verify backup/new-directory restore.
- Version PBKDF2 hashing at 600,000 rounds with successful-login legacy upgrades; reject unsupported future SQLite schemas.
- Bind frontend requests to sessions; repair actual 390px report overflow with wrapped event evidence and keyboard-accessible assertion-table scrolling.
- Add measured TypeScript coverage and expanded Python regressions, source-bound/fail-closed receipts, actual PostgreSQL concurrency/rollback/restart tests and explicit component release contracts.
- Retain failed regression/mobile acceptance evidence and unsuppressed security scanner output. No hosted identity, production deployment or broad model capability claim.

## Unreleased — 2026-11-10

- Add a separate responsive React/Vite engineering website with source-derived suite counts, honest model evidence and explicit local/cloud trust boundaries.
- Harden provider parsing, elapsed HTTP read deadlines, usage tracking, credential redaction and hashed evidence. Preserve prior agent traces on decision failure and honor suite token bounds.
- Require application target ownership/permission acknowledgement, retaining separate mutation consent. Add CLI flags and UI validation; existing targets require re-registration with consent.
- Make suite revisions explicit; reject ambiguous versions and concurrent duplicate creation. Recover active runs and reuse idempotency records beyond list pagination.
- Commit final results/artifact rows atomically. Preserve named unexecuted tasks/category denominators and export assertion expectations/observations.
- Reject ambiguous HTTP framing; surface frontend loading/errors and handle export failures.
- Use existing Python lock and packaged CPU ONNX binaries in setup/CI. Add real disposable PostgreSQL container and production website browser acceptance; isolate new evidence from historical records.
- Record cloud verification and real ONNX runs: both tested models scored 0/8. No public deployment or hosted Auth acceptance is claimed.

## 0.1.0 — 2026-11-03

Integrated local accounts, model/agent/application registry, versioned suite authoring, bounded execution, assertion reports, adaptive replay, artifact inspection, consented blind voting and scoped descriptive ratings. Added six suites with 40 scenario definitions, safe execution refusals, local SQLite/file storage, typed cloud metadata API and Postgres/RLS schema source. Cloud production operation and browser/inference acceptance remain unverified.

Post-publication CI follow-up: root `npm test` now runs Python, measured TypeScript tests, and the Node Worker tests. The Vitest Worker file uses `.vitest.ts` so Node's `*.test.ts` discovery cannot execute it with the wrong runner. No tests were removed. Bounded failure identifiers are emitted to GitHub checks without raw exception bodies or credentials.

The release gate explicitly sets the checkout runner import path for subprocesses instead of depending on a pre-existing editable installation. Installed-wheel acceptance remains a separate isolated check.

CI follow-up: use the PR/default-branch review baseline for changed-source coverage across documentation pushes. Native PostgreSQL commands are time-bounded, and restart explicitly retains the disposable server log path. A real PostgreSQL container check verified restart and queries with the log option; Docker exec did not reproduce the suspected native inherited-pipe hang, so the next native CI run remains authoritative.

Recorded passing standard and full-gate GitHub runs at b760fbb, including native PostgreSQL acceptance, and branch-only publication in the final handoff. Production/hosted identity limitations remain explicit.

Local-first qualification: fix manifest omission of database-referenced uploaded artifacts, check backup foreign keys, escape SQLite read-only paths, fsync snapshot publication, and refuse optimized legacy proof execution. Add actual killed-process, SQLite-full/permission-denial and explicitly injected ENOSPC regressions; fresh lifecycle and native platform CI; pinned dev-only axe tooling and semantic website groups. Native Linux/macOS fixture lifecycles pass; native Windows fails and remains unsupported. Verdict is controlled POSIX beta; cloud feature deferrals do not block it.
