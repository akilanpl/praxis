# QA checkpoint

Base main: 841d8a9. Previous a4435f1 is its ancestor. Branch: feature/qa-hardening-release.

Baseline after loopback access: 60 Python tests passed, one genuine timeout-classification failure. Baseline coverage and several integration layers were unmeasured; the deterministic historical baseline therefore scores missing groups as zero, not as passes.

Candidate: full Python suite, Worker security tests, full real-model Chromium journey, owned website browser checks, native host PostgreSQL/RLS, build and installed runner wheel have executable evidence in evidence/release/. Read machine-readable reports for the latest exact counts and SHAs. Public deployment remains BLOCKED, not a local test failure silently converted to a pass.

No GitHub remote initially existed; publication must use an explicitly approved repository and a passing pre-push gate. No existing Supabase project or production database was mutated.
