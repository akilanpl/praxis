# Frontend redesign handoff

**Verdict: READY FOR FRONTEND REVIEW.** This is a frontend review qualification, not production, hosted identity, Windows support or WCAG certification. All work remained in the original Codex Cloud workspace and GitHub. Nothing was deployed or merged; no PR was created.

## Scope and architecture

Baseline: `75243f70731fb5b8001ff39c64d83af9a02120b5`. Dedicated branch: `codex/praxis-frontend-revamp`. The backend runner, adapters, SQLite schemas, shared contracts, metadata Worker, dependency manifests/locks and independent `apps/website` have no content changes against that baseline. Existing endpoints and evidence semantics remain authoritative.

The workspace now has a cohesive charcoal/green design system, collapsible grouped navigation, mobile drawer, breadcrumbs, session menu, persisted themes and keyboard command palette. Data-derived overview, target registries, immutable suite editor/explorer, bounded launch, assertion/trace inspector, artifact viewer, comparisons, reports and honest local settings share reusable primitives. Large inspectors are lazy chunks. Record filtering/sorting and twelve-row pagination are client-side over returned owned records. There are no fabricated metrics, screenshots, model outcomes or backup API controls.

See [design system](DESIGN_SYSTEM.md), [architecture](ARCHITECTURE.md), [route/API audit](AUDIT.md), [screen guide](SCREEN_GUIDE.md), and [performance](PERFORMANCE.md).

## Verification

Source-bound acceptance and bundle measurements, gate summary, frontend test output and selected screenshots are retained under [evidence/frontend](../../evidence/frontend/). The receipt identifies the tested commit and runtime file hashes; subsequent documentation-only commits are qualified again by the normal gate and Actions.

| Area | Result | Evidence and scope |
|---|---|---|
| Complete Python regression suite | PASS | 286 tests + 44 subtests; full normal gate, no required cases skipped. |
| Controlled TypeScript suite | PASS | 57 Vitest tests; aggregate 96.21% statements, 90.15% branches, 96.47% lines. Includes malformed suite drafts, owner masking, stale exports, logout failures, native modal behavior and lazy inspectors. DOM/transport tests are distinguished from browser acceptance. |
| Worker tests | PASS | Original 14 Node tests; controlled Supabase transport, not hosted identity acceptance. |
| Type checks, lint and production builds | PASS | Both TypeScript checks; web/website builds, Worker and runner wheel in the root gate. No runtime dependency changes. |
| Full release gate | PASS | 339 checks at `daa8bd8`; Python 97.19% statement / 91.43% branch coverage, changed runtime executable lines 428/451 (94.90%). |
| Real frontend/API lifecycle | PASS | Disposable owner-scoped SQLite and actual HTTP; registration, immutable suite revision, model/agent fixtures, owned HTTP evaluation, failure inspection, cancellation, inert upload, comparison, blind vote/reveal and session expiration. Fixtures are explicitly not inference. |
| Reports | PASS | Complete JSON and escaped standalone HTML; Chromium PDF text independently checked with `pdftotext` for all eight task assertion tables and reproducibility manifest, with readable light print colors and run context. |
| Responsiveness | PASS | Document-overflow checks at 390/768/1024/1280/1440/1920; intentional evidence-table scrolling. Screenshots inspected at desktop, tablet and mobile sizes. |
| Accessibility sampling | PASS | Eleven actual Chromium/axe A/AA samples plus keyboard palette/drawer/dialog checks; latest remote frontend acceptance passed. See limitations below. |
| Real PostgreSQL and model regressions | PASS | Existing full gate runs actual disposable PostgreSQL and genuine CPU ONNX evaluations. Infrastructure acceptance does not imply task success: both documented SmolLM2 models remain 0/8. |
| Platform qualification | PARTIAL | Current native Ubuntu 24.04 and macOS 15 lifecycles pass; Windows fails the existing POSIX storage contract and remains unsupported. |
| Independent website regression | PASS | Unchanged source; build and existing browser checks remain in the full gate. No redesign replaced the website. |

Remote checks for source `daa8bd8`:

- [Standard verification](https://github.com/akilanpl/praxis/actions/runs/42830952219)
- [Full push gate](https://github.com/akilanpl/praxis/actions/runs/42830952256)
- [Frontend browser acceptance](https://github.com/akilanpl/praxis/actions/runs/42830952231)
- [Native platform matrix](https://github.com/akilanpl/praxis/actions/runs/42830952649) — Linux/macOS pass, Windows fails; overall workflow is correctly red.

Exact publication-head checks remain visible in Actions; do not infer their success from an earlier commit receipt.

## Accessibility findings and limits

Corrected visible-label/name mismatches, mobile overflow, modal/drawer focus handling, malformed suite JSON rendering and dark-theme print contrast. Named scrollable assertion tables preserve all evidence; status uses text as well as color. HTML artifacts remain inert source, and exported reports escape content with restrictive CSP.

One earlier expanded remote accessibility run failed the aggregate axe check; its report remains in Actions (42828499962). The next two expanded runs passed (42829823772 and 42830952231) after the chart gained an explicit group role; bounded failure annotations were subsequently added. The exact cause of the earlier aggregate failure was not recovered, so repeatability deserves monitoring; it was not suppressed or relabeled. Axe incomplete/manual items include native avatar-summary naming and contrast under modal overlap. Manual keyboard/visual sampling is not a screen-reader or comprehensive WCAG audit. Firefox, WebKit, high-contrast OS modes, zoom combinations and assistive-technology acceptance remain NOT VERIFIED.

## Performance and operational limits

Actual final initial JS is 277,375 bytes (Python gzip estimate 88,129 bytes), versus baseline 247,546 bytes; CSS is 35,837 bytes (gzip estimate 7,820 bytes). Four inspectors are separate route chunks. All explicit bundle budgets pass. This is a measured increase for the new shell/workflows, not a claim of smaller initial assets. No invented Lighthouse score or production latency/capacity claim is made.

The API still returns full records and caps lists at 500; twelve-row UI pagination is not server pagination. Expanding complete evidence can create large DOM content. Command search covers loaded authorized data, not a remote global index. Backup/restore remains the existing qualified CLI workflow; settings provides exact commands and limitations rather than pretending the browser can inspect disk paths or perform a backup. No arbitrary-code sandbox, hosted product parity, deployment or paid inference was added. Existing local controlled-beta/platform/security limitations remain in force.

## Reproduction

Use the repository's locked installation instructions and qualified POSIX environment. Run `npm test`, `npm run lint`, `npm run typecheck`, and `npm run build` as documented in the root manifests. For the additional acceptance, build `apps/web` and `apps/website`, install the locked Playwright Chromium browser plus OS dependencies and `poppler-utils`, then run:

```sh
.venv/bin/python scripts/frontend_bundle.py --output work/frontend-bundle.json
.venv/bin/python scripts/frontend_acceptance.py --output work/frontend-acceptance
```

The acceptance output directory must not already exist. Its `private/` database contains test sessions and must never be committed or uploaded; only the explicitly allowlisted report, receipt and screenshots are publication evidence. The workflow `.github/workflows/frontend-review.yml` follows that allowlist. No credentials belong in frontend configuration.
