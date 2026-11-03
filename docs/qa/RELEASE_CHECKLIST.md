# Release checklist

- [x] Existing main lineage and clean starting state recovered; changes isolated to QA branch.
- [x] Real local HTTP, model inference and Chromium journeys recorded.
- [x] Disposable native PostgreSQL/RLS tests passed on host; no production testing.
- [x] Actual model failures remain failures; worlds/reference policies and owned fixtures labeled.
- [x] Patched Python runtime and dependency advisory scans.
- [ ] Complete gate at final source SHA, including native host database stage.
- [ ] Approval for an exact GitHub destination and publication scope.
- [ ] Full hosted Supabase Auth/control-plane integration and dedicated project.
- [ ] Cloudflare authentication and deployment approval/configuration.
- [ ] Exact public deployment URL smoke-tested.

The local code gate uses a conservative 89-point cap while whole-product diff coverage is unmeasured. It can approve a QA feature branch under the documented 80-point threshold; it cannot approve main/release branches at the 90-point threshold or certify a hosted production deployment. An incomplete gate blocks pushes; no bypass switch is provided.
