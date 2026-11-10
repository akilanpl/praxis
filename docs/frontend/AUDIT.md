# Frontend redesign baseline

Baseline `75243f70731fb5b8001ff39c64d83af9a02120b5`, original cloud workspace. Dedicated branch `codex/praxis-frontend-revamp`. The Python runtime, SQLite schema, adapters, agent execution and object store remain authoritative and unchanged.

## Existing application and contracts

`apps/web/src/main.tsx` contains the router/controller, every page and form. `api.ts` captures each request's bearer session, emits expiration only for the current session, and refuses malformed JSON. Controller refs prevent stale route/session responses from replacing current content. Existing typed build uses React 19, Router 7, Vite 6, TypeScript; there is no component library or editor framework. The existing CSS supports dark/light styles but lacks a coherent shell and inspection hierarchy. The independent `apps/website` is a separate React/Vite build and retains its own entry point and stylesheet.

| Existing routes | API/data | Working operations retained |
|---|---|---|
| `/`, `/dashboard` | `/dashboard`, `/targets`, `/suites` | Local introduction, persisted counts/recent runs |
| `/models`, `/agents`, `/apps`, each `/new` | `/targets`, `/{id}/diagnostics` | Typed registration, explicit HTTP ownership/mutation consent, connection tests |
| `/suites`, `/suites/{slug}@{version}`, `/suites/new` | `/suites` | Immutable version registration, inspection, clone and JSON export; no PUT/delete |
| `/runs`, `/runs/new`, `/runs/{id}` | `/runs`, `/{id}/cancel`, `/{id}/export` | Idempotent launch, compatible suite selection, polling, assertion/output inspection, JSON export and browser print |
| `/artifacts` | `/artifacts`, `/artifacts/check-website` | Bounded file ingestion, inert HTML/text, image/audio/video signatures, owned browser fixture |
| `/compare`, `/arena`, `/leaderboards` | `/runs`, `/arena`, `/{id}/vote`, `/leaderboards` | Condition matching; backend-controlled blind assignments; vote then reveal; no official trusted ranking |
| `/worlds`, `/worlds/new`, `/worlds/{id}` | `/worlds`, `/{id}/replay` | Deterministic reference worlds, state/replay evidence |
| `/settings`, `/admin`, `/docs`, `/methodology`, `/privacy`, `/terms` | `/auth/register`, `/auth/login`, `/auth/logout`; local information | Local accounts/session revocation and honest documentation; operator grants are unavailable |

SQLite `Store` owns `users`, hashed `sessions`, owner-bound JSON `records`, unique `votes`, and `audit`. Records carry runs/events/results/artifacts; secrets are rejected in targets. Schemas/scenario validation are server-owned. Lists return at most 500 records; no server pagination/search endpoint exists. UI pagination/search must state its loaded-record scope. Uploaded bytes live in a private sibling `objects/` directory; inline evidence lives in SQLite. HTML is inert text. Fixture provider and self-reported trust labels must remain visible.

Backup/restore is a reviewed CLI workflow, not an API. Settings must provide accurate commands/instructions, not a fake backup button. Suite editing must create a new version; modifying a version in place is unsupported. Target diagnostics are explicit requests, not inferred live availability. Browser `window.print()` is the existing printable report operation; standalone HTML export may use a client-rendered inert report without executing content.

## Baseline acceptance

Existing tests: 286 Python tests + 44 subtests, 39 controlled Vitest tests including web/session/Worker/website, and 14 independent Node Worker tests. Existing real Chromium acceptance covers registration, two real local CPU endpoints, eight-task reports, comparisons, world replay, inert upload/audio, blind voting, ownership and navigation. Local qualification adds 39 disposable lifecycle checks and 27 accessibility checks across 12 sampled pages. These are historical baseline counts; current-source checks are rerun and final results recorded separately. All private disposable databases and tokens remain in ignored cloud `work/`.

## Redesign plan

Keep the controller/API semantics and route compatibility; extract presentation into a shared shell, primitives and lazy-loaded evidence/suite/artifact views. Establish tokens before screens. Add `/targets` and `/reports` as read-only frontend projections over existing APIs. Overview derives status/suite/failure activity from persisted loaded records. Build command navigation, responsive sidebar, persisted themes, explicit target diagnostics, client filtering/sorting/pagination, immutable suite revision editing, launch context, task anchors/traces, accessible confirmations, and recovery instructions. No backend or migration changes are authorized by this redesign.
