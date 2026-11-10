# Local installation and recovery

This is a private loopback, local-first release contract. It requires a trusted OS account, checkout, interpreter, PATH and dependency installation. Logical Praxis accounts do not isolate a malicious process running as the same OS user. Do not publish or tunnel the control plane. No arbitrary untrusted-code execution is supported.

## Installation

Use Python **3.12** and Node.js **22.12+** with npm and a POSIX shell. The tested Python series is 3.12; do not infer acceptance for every later Python release. Native Windows is not supported by the POSIX installer/private filesystem durability contract. See [platform qualification](../qa/LOCAL_RELEASE_QUALIFICATION.md) for actual, scoped OS evidence.

From a trusted checkout in a private directory:

```sh
./scripts/setup.sh
PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/python -m playwright install chromium
npm run dev
```

The development UI is `http://127.0.0.1:5173`; the API binds to loopback port 8787. Lockfile installation includes the editable `praxis` CLI. Chromium is needed for browser checks, not ordinary model/agent/HTTP evaluation. Headless Linux may need the official Playwright browser dependencies installed by its administrator. The cloud qualification uses the approved environment's browser installation; it never installs software on the user's Mac.

For a built integrated local UI:

```sh
npm run build
PYTHONPATH=runner .venv/bin/python -m praxis.server
```

Open `http://127.0.0.1:8787`. Set `PRAXIS_DB` before starting if selecting a different private workspace; its parent also holds `objects/`. Keep the DB and objects together. The server defaults to `.praxis/praxis.sqlite` in the checkout. A wheel includes the runner/CLI/scenarios; it is not a standalone packaged desktop UI installer. A model endpoint is separate: use an explicitly owned OpenAI-compatible, Ollama or custom endpoint and its documented model identifier. Provider credentials belong in the process environment, not targets, reports or Git. Deterministic `demo`/`demo-failing` providers are infrastructure fixtures, not inference.

## Stop and snapshot

Stop the development launcher/local server before an operator recovery drill, and confirm it has exited. Ctrl-C runs shutdown; in-flight bounded work may need time to finish. If an OS process must be killed, the next startup marks queued/running runs **interrupted**, retains recorded events, and requires a new attempt. There is no individual-task resume promise. The regression suite exercises an actual killed process after a real owned provider request begins.

```sh
.venv/bin/python scripts/backup_workspace.py backup \
  --database .praxis/praxis.sqlite --directory work/private-snapshot
.venv/bin/python scripts/backup_workspace.py verify \
  --directory work/private-snapshot
.venv/bin/python scripts/backup_workspace.py restore \
  --source work/private-snapshot --directory work/restored-workspace
PRAXIS_DB="$PWD/work/restored-workspace/praxis.sqlite" \
  PYTHONPATH=runner .venv/bin/python -m praxis.server
```

Backup/restore destinations must not exist. Never overwrite the only database/object copy or point a recovery test at the active workspace. SQLite online backup gives a consistent database snapshot; verification requires supported schema, database digest/quick_check/foreign keys, exact manifest-to-DB uploaded-object references, and each copied object's hash. Restore re-verifies the copied snapshot and publishes a new directory. Files/directories are private and fsynced before publication on supported POSIX filesystems. SQLite read-only URIs correctly escape spaces, `#` and `?` in paths.

Verify account ownership, target/suite/run IDs, assertion/event evidence, artifact hashes, and exports. Stop the restored process and restart it again for read-only inspection. Keep the source and its pre-recovery snapshot unchanged. Sessions and password hashes are private recovery data; restoring preserves session state/expiry, not a new authentication boundary. Stop and protect a compromised workspace rather than treating backup hashes as signatures from an independent trusted party.

## Failure response

- **Full disk / permission denial:** the operation reports failure; resolve capacity/permissions and retry with a new destination. Never delete the only source to make space. Unpublished temporary files are cleaned. If publication succeeded but parent-directory fsync failed, a verified destination may exist even though durability was not confirmed: inspect and verify it; never overwrite blindly. No claim of physical drive or power-cut certification is made.
- **Corrupt/missing object or inconsistent manifest:** verification refuses restore. Preserve the damaged copy and recover from a verified snapshot. Upload retry can repair a corrupt hash-addressed object when the original bytes are available; it cannot reconstruct lost bytes magically.
- **Corrupt DB / future schema:** startup or verification refuses it. Preserve bytes and use the matching runner or a verified backup. Do not reset the version or fabricate a new manifest to bypass verification.
- **Interrupted run:** retained events remain inspectable; start a new run. Unknown-outcome POST mutations are not automatically replayed. Duplicate idempotency keys return the existing run or reject a changed request.
- **Malformed provider output:** classified adapter/grading failure remains a failure; no fixture fallback replaces it.

Retain the exact runner commit and locks with a pre-upgrade verified backup. Legacy password hashes upgrade only after a valid login; rollback to an older runner requires the pre-upgrade snapshot. Backups are not encrypted/off-host automatically. Protect them with the OS, private storage and an explicit retention policy; do not commit or publicly upload private snapshots. The qualification publishes summaries/screenshots only, never its account/session database.
