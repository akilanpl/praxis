# Implementation status — 2026-11-10

**Local release candidate; hosted product acceptance remains partial. No public deployment.**

Implemented: authenticated loopback workspace; owner-scoped SQLite WAL; model/agent/application registry; versioned suite authoring/cloning/export; OpenAI-compatible/Ollama/custom protocols; bounded tool agents with actual state assertions; authorized HTTP contracts; deterministic reference worlds; persisted events/results; inert artifact/media inspection; JSON and printable HTML reports; condition-matched local comparisons and blind voting; separate metadata Worker and PostgreSQL RLS schema.

Added/hardened in this release: elapsed HTTP read deadlines, malformed-provider classification, credential reflection redaction, usage aggregation, safe configuration capture, named unexecuted tasks/full category denominators, suite token bounds, version-qualified suite inspection, complete restart/idempotency queries beyond the list cap, atomic final run/artifact metadata, agent error traces, explicit HTTP target authorization acknowledgement, HTTP framing rejection and escaped assertion expectations/observations in reports.

The separate professional website is implemented at `apps/website`, using the existing React/Vite toolchain. It imports actual suite counts, explains the architecture and unsupported boundaries, links historical 0/8 model results, and does not advertise a live application. Root build includes it.

Current cloud checks include the full Python suite (140 tests plus 44 subtests), 14 controlled-transport Worker tests, all TypeScript checks, component builds, installed wheel execution, real loopback HTTP, actual disposable PostgreSQL 17 ownership/persistence/RLS checks, fixture and real-model browser journeys, and website screenshots at 390/768/1280 pixels. Both new real CPU ONNX model runs passed infrastructure acceptance but scored 0/8 on structured-agent. See VERIFICATION.md and evidence/final for exact commands/source scope; this paragraph does not certify hosted Auth.

Unsupported: full hosted workflows, collaborative cloud organizations, R2/queues, operator-trusted runs/official rankings, arbitrary untrusted code/HTML execution without a hardened external executor, external-model-driven adaptive worlds, streaming, individual-task resume, held-out datasets, learned judges, multimodal generation/quality inference, automatic pricing, production moderation/retention.

External requirements: functioning GitHub write credentials for publication; separately approved deployment environments and production credentials; hosted Supabase Auth/Worker and frontend integration acceptance; actual-URL smoke testing. No paid resources, remote database migrations or public deployment were performed.
