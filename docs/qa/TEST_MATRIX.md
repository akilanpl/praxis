# Acceptance map

Baseline: main `841d8a9`, clean checkout. `a4435f1` is its earlier verification checkpoint, not a conflicting head. Work continues on `feature/qa-hardening-release`.

| Requirement | Positive / negative oracle | Evidence | Current scope |
|---|---|---|---|
| Local authentication | Chromium signup, authenticated HTTP account; revoked/foreign access denied | browser/result.json, Python tests | Real local password/session auth |
| Genuine model run | Actual ONNX CPU responses, usage, timings, persisted assertions | real-*.json, browser/run-*.json | Two distinct real models; strict benchmark scores 0/8 each |
| Report and compare | Rendered assertions, exports and identical conditions hashes | browser/report-*.png, compare.png | Self-reported; excluded from official objective ranks |
| Adaptive worlds | 1/5/12 mutable entities, hashes equal on replay, resource/permission boundaries | world screenshot, Python world tests | Real state machine; reference policy explicitly demo |
| Artifacts | Inert HTML, 1-second WAV metadata and audio preview, owned website interactions/screenshots | browser/artifact-inert.png, website/ | No claim of generated media inference or arbitrary code isolation |
| Anonymous Arena | Other account receives blind pair; owner excluded; identities after vote; replay 409 | browser/arena-*.png | Real model outputs; sparse preference only |
| Database | Disposable native PostgreSQL schema, 28 RLS tables, isolation/forgery/uniqueness | postgres.json / postgres.log | auth.uid claim fixture, not hosted Supabase Auth |
| API validation | Wrong types, numeric limits, slug paths, clone IDs, idempotency mismatch | validation-red/green reports, Python suite | Actual temporary SQLite persistence, no external side effects |
| Worker | Native local workerd health and safe 503 when unconfigured; JWT-forwarding negative unit tests | worker-runtime.json, Worker test log | Cloud metadata only; hosted end-to-end Auth not tested |
| Build/package | Web/TS/Worker build, isolated runner wheel loading all suites | build manifest, wheel.json | Six suites / 40 definitions; 12 wheel fixture tasks executed |
| Public release | Exact deployed smoke and cloud identity/config required | Release report | BLOCKED: no Cloudflare authentication or dedicated approved cloud project |
