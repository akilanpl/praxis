# Local-first release qualification

Baseline: `2d90b924ca343817d582b30f6322ea9b6601939c`, existing `codex/praxis-final-release` branch. Main remains the PR #2 merge. No new PR, force push, main modification, deployment or paid model call is part of this qualification.

## Scope and provisional results

Linux cloud: a fresh Python 3.12 dependency installation and a separate disposable workspace completed real local SmolLM2-135M inference (0/8 task quality), explicit fixture agent execution (4/4), actual owned HTTP contracts (4/4), matched comparison, browser JSON export, printable HTML reports, artifact ingestion, complete backup, new-directory restore and two read-only restarts with ownership, records and hashes preserved. Exact source-bound rerun and remote platform results will be recorded after the implementation commit.

A backup integrity defect was reproduced: a manifest could omit database-referenced uploaded objects. Verification now requires exact reference equality, valid object digests and foreign keys. SQLite read-only URLs escape special path characters. Snapshot/restore publication fsyncs files and directories on supported POSIX filesystems. No physical power-loss durability certification is claimed. Injected ENOSPC tests are distinguished from actual SQLite SQLITE_FULL and real POSIX permission denial.

The unsuppressed Bandit inventory and every finding's contextual exploitability/impact assessment are in [LOCAL_SAST_REVIEW.md](LOCAL_SAST_REVIEW.md) and `evidence/local-release/`. No blanket suppression was added. An older assertion-based proof now refuses optimized Python before touching workspace data.

Actual Chromium/axe checks sampled 12 application/website pages and 25 keyboard, semantics, error-alert and layout checks. Two generic website groups received semantic roles for their labels. Automated A/AA violations were zero after repair; decorative-symbol contrast candidates require human interpretation and do not establish WCAG certification. Screen-reader and exhaustive accessibility certification remain NOT VERIFIED.

## Platform matrix pending remote execution

| Platform | Current qualification | Limits |
|---|---|---|
| Linux | PASS for disposable lifecycle in this cloud environment | Host Node 24; independent Node 22/Python 3.12 CI is required; distro/filesystem scope is specific |
| macOS | NOT VERIFIED | Remote macOS runner qualification pending; no user's Mac is accessed |
| Windows | NOT VERIFIED / not supported for this release | POSIX installer, Unix venv paths and directory-fsync/private-permission contract are not Windows-qualified; remote native probe pending |

The native platform workflow preserves failures and uses explicit fixtures. It does not run paid inference or silently skip a platform. Platform job success is evidence only for its enumerated checks, not every device/filesystem/architecture or GUI installer. Hosted Supabase/Auth, organizations and R2 are deferred and do not gate the local product.
