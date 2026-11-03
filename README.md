# Praxis

Artifact-first AI evaluation with an integrated local workspace, a Python runner, and a limited Cloudflare metadata API. Judge AI by what it makes and what it accomplishes.

**Build status:** working, tested local control-plane logic and execution kernel; not a completed production platform. No model quality results are fabricated. Read [VERIFICATION.md](VERIFICATION.md) for exact passing commands, environment blocks and unsupported capabilities.

## Start locally

Requirements: Node 22+, Python 3.9+, npm. No cloud account or model download required.

```sh
./scripts/setup.sh
npm run dev
```

Open `http://127.0.0.1:5173`. Create a local account with a password of at least 10 characters. Sessions expire after one day. The API binds **only** to loopback at port 8787; it must not be exposed publicly.

For a single production-build local process:

```sh
npm run build
.venv/bin/python -m praxis.server
```

Open `http://127.0.0.1:8787`. SQLite records and immutable deduplicated uploaded objects live in `.praxis/`. The current execution environment denies socket binding and Chromium IPC; run these startup/browser commands in a normal local terminal. The source, build, in-process API and database logic have been exercised here.

## Evaluate a model

1. Open Models → Create target. Choose OpenAI-compatible (`openai`), Ollama or custom HTTP. Keep API keys out of the registry. The OpenAI endpoint is its base URL including `/v1`; Ollama uses `http://127.0.0.1:11434`.
2. Set `PRAXIS_MODEL_API_KEY` in the runner process environment if required, then start the server. Never paste keys into targets, prompts or artifacts.
3. Click Test connection. It performs one actual readiness request; provider usage may incur cost. The local runner, not the Worker, performs inference.
4. Launch evaluation, choose the target and a compatible suite, then inspect the persisted report. Use `structured-agent` for JSON model tasks, `agent-workflows` for actual tool agents, and `http-application` for conventional REST applications.
5. Compare runs with identical suite digest/version and seed. Inspect assertions, output, latency, configuration hashes, unknown costs and provenance. Exports are JSON; browser print produces PDF-friendly reports.

`demo` and `demo-failing` are explicit deterministic infrastructure fixtures, **not model inference**. They intentionally produce passing/failing fixture outputs. They never enter official objective rankings. External endpoints remain self-reported, never automatically verified.

```sh
.venv/bin/praxis suites list
.venv/bin/praxis validate packages/scenarios/structured-agent-v1.json
.venv/bin/praxis run --provider ollama --endpoint http://127.0.0.1:11434 --model YOUR_MODEL --suite structured-agent --output work/real-run.json
.venv/bin/praxis report work/real-run.json --output work/report.html
.venv/bin/praxis run --kind agent --provider demo --suite agent-workflows --output work/agent-fixture.json
.venv/bin/praxis world --domain customer-support --seed 73 --output work/world.json
```

## Suites, worlds and applications

Six versioned suites contain 40 public deterministic scenarios. Thirty-two test JSON/grounded reasoning/security/developer contracts, four execute actual agent tools with independently checked state, and four perform HTTP application contracts. Developer reasoning tasks **do not** count as executed code or rendered websites. Every scenario has passing and failing regression fixtures. Custom authoring uses JSON Schema and a bounded assertion DSL; arbitrary Python/eval assertions and schema references are rejected. JSON import, clone and export are available; YAML import and held-out official datasets are unsupported.

Worlds mutate actual entities and record transitions and snapshot hashes. A bounded deterministic reference policy is explicitly demo, not external inference. Support, research, workflow and web-product contracts grow from 1 to 5 to 12 entities when the measured policy succeeds. Tool outages and denied actions affect state and progression. Replay with the same spec/seed yields an identical hash. External-model-driven adaptive worlds and a graphical tool contract editor are not implemented.

Applications use real local HTTP contracts, not model prompts. Clone `http-application` to change paths/assertions for an owned app. POST tests require explicit `allow_mutation:true` in a local target; the default denies mutations. Untrusted generated apps/code are refused without a configured OS isolation boundary. Arbitrary code execution/container executor support is absent.

## Artifacts and Arena

Uploads accept at most 1 MiB of UTF-8 text/JSON/HTML, PNG/JPEG/GIF, WAV, MP4 or WebM. MIME is inspected from bytes, never trusted from extensions. Text and HTML are inert; no primary-origin iframe execution. WAV duration and PNG/GIF dimensions are measured. Video duration/codec remain unknown without a media probe. This is metadata inspection and human preview, not generated image/video quality inference. Objects are SHA256 deduplicated. Uploaded artifacts remain private; only explicitly published run outputs can enter Arena.

For a fixture Arena test: publish two runs on distinct targets with the same suite/seed; create another local account to vote. Owners cannot vote on their own artifacts. The server persists randomized A/B order, hides identity metadata until voting, excludes non-comparable/private artifacts, and enforces exactly one vote per account/match transactionally. Repeated/concurrent pairing requests reuse the same match. Elo-like preference ratings are scoped by evaluation conditions and trust; fewer than 20 votes is labeled insufficient evidence. Both-bad votes are stored but do not affect relative Elo. No global official preference certification is claimed.

Objective leaderboards remain empty until an operator-controlled trusted runner system exists. Neither local signatures nor uploaded scores confer trust. Public multi-user anti-abuse, moderation operations, robust bot detection and official trusted runner enrollment are unsupported.

## Verification

```sh
npm test                                 # full suite, including real loopback adapter tests
npm run build                            # web production build + Worker typecheck
npm run typecheck --workspace packages/contracts
.venv/bin/python scripts/integration_proof.py
```

The proof script executes real control-plane/SQLite logic in process, using explicitly labeled fixture providers. It saves task evidence, HTML reports, replay and voting records in `evidence/`; it does not verify HTTP transport or inference.

Browser checks require a normal local environment:

```sh
.venv/bin/python -m pip install -e '.[browser]'
PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/python scripts/browser_check.py
PLAYWRIGHT_BROWSERS_PATH=./work/browsers .venv/bin/praxis check-website --output-dir evidence/website
```

The website checker executes only the source-controlled owned fixture, with no inherited browser credentials and outbound network blocked. Cart, search, validation, labels, mobile/desktop overflow and runtime checks save screenshots. Arbitrary HTML is rejected because a browser context alone is not robust isolation. Browser startup is blocked here; no successful browser result or screenshot is claimed.

## Cloud and operational limits

See [docs/cloud.md](docs/cloud.md) for Worker, Supabase and R2 configuration boundaries. The Worker is a **limited metadata control plane**, not a cloud version of all local workflows. It verifies Supabase bearer tokens, forwards user JWTs for RLS, stores targets/run requests/self-reported evidence and never fetches custom endpoints. Cloud Arena, queues, R2 upload signing and hosted inference are unsupported. Postgres schema/RLS source exists but has not been applied or tested against a real Postgres instance. No public deployment occurred.

The local implementation has owner isolation, host/origin restrictions, hashed sessions/passwords, auth/request limits, request IDs, cancellation, evidence hashes and run idempotency. It is a single-computer workspace, not hardened public hosting. Organizations are schema groundwork, not functional collaborative workspaces. Records are capped at 500 per list, without cursor pagination. Deletion/retention automation, resumable individual tasks, model streaming, automatic pricing, learned judges, provider-specific multimodal inference and robust sandbox infrastructure remain unsupported.

No cloud resources, paid inference, GitHub repository or deployment are created by setup. Deployment, paid operations and remote changes require explicit approval.
