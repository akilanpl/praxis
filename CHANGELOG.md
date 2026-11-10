# Changelog

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
