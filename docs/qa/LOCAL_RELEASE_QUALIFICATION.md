# Local-first release qualification

Baseline: `2d90b924ca343817d582b30f6322ea9b6601939c`, existing `codex/praxis-final-release` branch. Main remains the PR #2 merge. No new PR, force push, main modification, deployment or paid model call is part of this qualification.


## Final local-first decision

**READY FOR CONTROLLED BETA**, scoped to the qualified POSIX local-first product. Deferred cloud identity, organizations and object storage do not block this decision. This is not a general multi-platform production certification.

| Area | Result | Evidence and limits |
|---|---|---|
| Linux cloud fresh installation + genuine inference lifecycle | PASS | `evidence/local-release/lifecycle-linux.json`: source `1a82ee1`, clean tracked runtime, 38 checks; CPU SmolLM2-135M 0/8 task quality, actual HTTP and fixture agent execution, reports, ownership, backup, restore, two read-only restarts |
| Ubuntu 24.04 / Python 3.12 / Node 22 | PASS | Native GitHub lifecycle job at `daa847c`; clean pip lock/npm ci, CLI, builds, Chromium, explicitly labeled fixtures, HTTP, private paths, SQLite, backup/restore/restart. Real inference acceptance is separately Linux-cloud evidence |
| macOS 15 / Python 3.12 / Node 22 | PASS | Native GitHub lifecycle job at `daa847c`, same enumerated fixture lifecycle. Real model execution and every macOS version/architecture/filesystem are NOT VERIFIED; macOS 14 runner was BLOCKED before setup, not passed |
| Windows Server 2022 / Python 3.12 / Node 22 | FAIL | Installation/CLI/build/browser-dependency steps passed, native lifecycle failed with HTTPError after 20 checks. Upload publication uses POSIX directory fsync (`os.O_DIRECTORY`), and private mode bits/installer paths are not Windows-qualified. Native Windows remains unsupported; no tests suppressed |
| Failure/recovery regression suite | PASS | 13 tests across backup/recovery modules, including real killed-process recovery, actual SQLite SQLITE_FULL and permission denial; ENOSPC file/backup failures are explicitly syscall fault injections |
| Full engineering gate | PASS | `daa847c`: 339 scored checks, 286 Python tests + 44 subtests; 39 Vitest tests; 14 Node Worker tests; builds, owned HTTP, real browser, local PostgreSQL, dependency/secret audits. Final documentation commit repeats the normal gate |
| Static analysis | PARTIAL | 130 retained Bandit findings: 115 LOW, 15 MEDIUM, zero HIGH. Every location assessed in LOCAL_SAST_REVIEW.md/JSON; no demonstrated untrusted-input exploit in the flagged sinks; PATH/OS/tooling residual risks retained |
| Accessibility/usability | PARTIAL | Actual Chromium + axe: 12 sampled pages, 27 targeted checks, zero detected automated A/AA violations; keyboard-only account form, skip links, visible focus, labels, error alerts, dark/light pages and 390/768/1280 layouts. 24 contrast-review candidates are decorative symbols; two unsupported generic-group labels were repaired. No exhaustive WCAG/screen-reader certification |

Native platform run: https://github.com/akilanpl/praxis/actions/runs/42795199240 . Its overall FAILURE is retained because Windows failed; Linux/macOS passed independently. The earlier macOS 14 cancellation and Windows failure are also retained: https://github.com/akilanpl/praxis/actions/runs/42794367066 . Full remote gate: https://github.com/akilanpl/praxis/actions/runs/42795199046 . Source-bound private databases/backups stay in ignored cloud `work/`; only safe summaries and screenshots are committed. Artifact browser inspection is explicitly checked by the final lifecycle harness in addition to hash/record checks. The published native workflow reruns that harness on the final commit; final exact-commit Actions results are authoritative.

## Remaining local limitations

- Native Windows is unsupported; use a qualified POSIX environment rather than treating WSL as tested Windows acceptance. WSL, network/removable filesystems, GUI installers, unattended service managers and every OS/hardware version are NOT VERIFIED.
- macOS lifecycle evidence uses explicit fixtures; Linux evidence covers genuine CPU inference. Provider/model quality and availability are separate from local product acceptance. Demo results do not establish model performance.
- No physical power-cut, failing hardware, exhaustive screen-reader/WCAG, external penetration-test or independent trusted-runner certification. Fault injections and actual OS/SQLite failures are distinguished.
- The trusted OS user/installation boundary remains essential. No arbitrary executable artifacts, automatic task resume, backup encryption/off-host retention, public control-plane hosting, or promised durability on unsupported filesystems.
- Backups are verified self-reported snapshots, not signatures from an independent party. Protect sessions/password hashes and retain a pre-upgrade copy. Follow [installation and recovery](../operations/LOCAL_INSTALLATION_RECOVERY.md).

## Reproduction

```sh
# Fresh disposable Python dependency environment; never point this at existing data.
python3.12 -m venv work/qualification-env
work/qualification-env/bin/python -m pip install -r requirements-lock.txt
PLAYWRIGHT_BROWSERS_PATH=./work/browsers work/qualification-env/bin/python -m playwright install chromium
PYTHONPATH=runner PLAYWRIGHT_BROWSERS_PATH=./work/browsers \
  work/qualification-env/bin/python scripts/qualify_local.py --output work/qualification-new
# --fixture-only is explicit infrastructure acceptance, not real inference.
PYTHONPATH=runner PLAYWRIGHT_BROWSERS_PATH=./work/browsers \
  work/qualification-env/bin/python scripts/accessibility_check.py --output work/a11y-new
.venv/bin/python -m pytest tests/test_backup_recovery.py tests/test_local_failure_recovery.py -q
.venv/bin/python -m bandit -r runner scripts -f json -o work/bandit-new.json
```

The genuine inference harness starts only the pinned local CPU model service; it does not call paid providers. Built UI/static website assets and npm lock installation are required first. Output directories must be new. The original live workspace is never selected by these harnesses. Detailed private lifecycle databases are deliberately not public artifacts.
