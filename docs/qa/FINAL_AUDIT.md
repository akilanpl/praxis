# Cloud release audit — 2026-11-10

Base: `8f1e884` on `main`, origin `https://github.com/akilanpl/praxis.git`.
Managed Codex Cloud provider and attached executor verified before modifying source.
All checkout, package, browser, model and Git work stays in `/workspace/praxis`.
No user computer, production resource, paid model API or remote database was used.

## Dependency and execution map

- `apps/web`: React 19 / React Router / Vite 6 / TypeScript. One local UI entry point, routed by pathname. Vite proxies `/api` to loopback Python; built assets are served by Python.
- `runner/praxis/server.py`: loopback HTTP, PBKDF2 accounts, hashed bearer sessions, owner-scoped SQLite WAL records, two-worker evaluation executor, event snapshots, artifacts and local Arena. Uploaded objects live beside the database.
- `engine.py`: suite validation → adapter invocation → schema/DSL and actual-state checks → per-task records → suite-wide statistics → hashed evidence. `adapters.py`, `agent.py`, `application.py` implement distinct model, simulated-tool and HTTP execution semantics. `worlds.py` is a separate deterministic reference policy. `media.py` and `artifact_checks.py` inspect inert artifacts and an owned browser fixture.
- `cli.py`: installed console entry point, versioned suite validation/execution, world replay and JSON/standalone printable HTML exports. Wheel includes six public suites / 40 tasks.
- `apps/api`: separate metadata-only Cloudflare Worker; shared Zod contracts in `packages/contracts`; authenticated user JWT forwarded to Supabase/PostgREST. No workload dispatch or endpoint proxy.
- `supabase/schema.sql` and the tracked migration are identical. Twenty-eight owner-scoped RLS tables; operator-owned trust/vote/ranking mutations denied to clients. Organizations are stored, not a collaborative runtime.
- `apps/website`: separate static React/Vite public engineering website. Imports actual suite definitions; links to source/docs/evidence; no authentication, tracking or API dependency. Root build includes this site without changing the evaluation application's origin.
- Root npm lock and Python lock pin development dependencies. Setup disables ONNX's optional CUDA download, retaining packaged CPU execution. Browser and PostgreSQL are independent acceptance prerequisites.

## Inspected surfaces

README/status/verification/changelog/AGENTS; Python and npm manifests/locks; every runner module; local UI routes/styles/config; Worker routes and contracts; SQL/migration/ownership/persistence checks; all automated tests; CI/pushgate/build/setup/package/browser/model tooling; historical acceptance receipts and QA/cloud/security/architecture handoffs. Historical archives were not extracted or altered.

## Findings and resolution

| Finding | Resolution / evidence |
|---|---|
| Old status documents contradict later evidence | Current results supersede dated checkpoints; historical receipts retained. |
| Non-object JSON and invalid provider content/usage can escape classification | Strict protocol validation; regressions in `tests/test_final_release.py`. No fixture fallback. |
| Per-read timeout permits trickled responses to exceed total duration | Shared byte/elapsed-deadline reader; trickle regression. |
| Reflected provider credential can enter persisted evidence | Redact known credential throughout results before final hash; recompute output hashes. Metadata-only configuration capture. |
| Application requests lacked explicit ownership acknowledgement | `authorized:true` required before requests; separate POST mutation consent; UI acknowledgement and CLI flags. Existing targets must be registered again with consent. This is acknowledgement, not independent ownership verification. |
| Suite revisions resolved ambiguously | Explicit `slug@version` UI routes; ambiguous API execution/inspection returns 409; concurrent suite creation serialized; route-safe versions. |
| Restart/idempotency scans depend on 500-record list cap | Query complete active/idempotent records directly; >500-record restart regression. List UI remains capped. |
| Final artifacts and run status could persist separately | Commit generated artifact rows and final run record together; injected second-artifact failure regression proves rollback. |
| Failed agent decision can lose prior trace | Attach already-executed state/trace to adapter failure evidence. |
| Suite token budget was recorded but not applied | Effective adapter token cap is minimum of target and suite cap. |
| Unexecuted task/category evidence incomplete | Named not-run records and full category denominators; UI and standalone reports expose them. |
| Ambiguous HTTP request framing | Reject Transfer-Encoding and duplicate Content-Length; parser regressions. |
| UI auxiliary loading errors swallowed | Surface errors; loading/error state for data routes; bounded form fields; export failures handled and object URL revoked. |
| Standalone HTML lacked assertion expectations/observations | Add escaped expected/observed values and configuration/unexecuted records. |
| Setup allowed drifting Python dependencies and unnecessary CUDA download | Install existing Python lock, CPU-only ONNX installer mode; CI uses same inputs. |
| No dedicated project website | Added separate `apps/website`, semantic sections, source-derived counts, explicit historical model failures, trust boundaries, metadata, favicon, responsive layouts. |
| Existing browser script could overwrite historical receipts | Optional `PRAXIS_EVIDENCE_DIR`; this mission records under `evidence/final`. |
| Native PostgreSQL binaries absent | Actual disposable network-isolated PostgreSQL container acceptance added; no mocks or remote migrations. |

## Acceptance checklist

- [x] Cloud preflight; correct remote; dedicated branch; original evidence preserved.
- [x] Current full Python suite and HTTP tests; Worker tests; all TS checks; production builds.
- [x] Browser application fixture journey; website desktop/tablet/mobile screenshots and inspection.
- [x] Actual disposable PostgreSQL schema/ownership/persistence acceptance.
- [x] Dependency advisories and tracked-history secret scan.
- [x] Real cloud CPU model invocation; results reported independently of transport success.
- [ ] Hosted Supabase Auth / complete hosted application parity (external project/credentials/implementation).
- [ ] Public deployment (not authorized or performed).
- [ ] Remote branch/PR publication (depends on working GitHub write access).

## Known scope limits

Local runtime remains single-process, loopback-only and intended for trusted local operators, not public multi-tenant hosting. Cancellation is cooperative between requests; a current HTTP call observes its deadline. Agent steps are bounded but not resumable, and individual intermediate agent steps are persisted with the final task record rather than durably streamed at each action. Crash recovery retains event snapshots, not a resumable partial task. Final result and generated artifact rows commit in one SQLite transaction; upload bytes and metadata still require backing up together. Upload inspection is bounded signature/metadata inspection, not malware detection. Response schemas and custom suites are operator inputs, not a hardened hostile-code sandbox. General untrusted code execution, streaming, full hosted workflows, trusted official ranking, held-out suites, automatic pricing and external-model-driven adaptive worlds remain unsupported.

No broad production or general-model-capability claim follows from this acceptance.

The initial aggregate gate attempt was INCOMPLETE after the Debian PostgreSQL Docker image exhausted the 7.9 GiB cloud writable layer. Its receipt is preserved as `evidence/final/preliminary-gate.json`. The container harness now defaults to the smaller official PostgreSQL 17 Alpine image; SQL acceptance is unchanged. Compiler lint checks unused locals/parameters in both frontend workspaces; no separate stylistic ESLint claim is made.
