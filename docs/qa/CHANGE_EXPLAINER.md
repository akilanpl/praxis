# Change explanation

The first checks verified mostly isolated logic because sockets and Chromium startup were denied. Authorized loopback access exposed the real timeout-classification defect. A host-launched isolated Chromium then allowed full browser → HTTP → SQLite testing, without mocks replacing the backend. Two pinned small ONNX models ran on CPU and generated their own responses. Both failed the strict JSON benchmark; infrastructure acceptance verifies recording and grading, not a minimum model quality score.

Validation regressions demonstrated concrete persistence and UI failures before patches. The fixes reject invalid input before writing, preserve immutable suite IDs on clones, bind idempotency keys to their original request, and keep voted identity reveals associated with the correct pair. Runtime security required moving to an already installed Python 3.12; no architecture rewrite occurred.

In 30 seconds: Praxis now performs real local inference and a real browser journey, with independent grading, persisted evidence, reproducible worlds and eligible blind voting. Native PostgreSQL RLS was exercised on a disposable host cluster. Public hosting remains incomplete and is not represented as deployed.
