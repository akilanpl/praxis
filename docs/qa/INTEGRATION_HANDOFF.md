# Integration handoff

Primary local runtime: React production frontend served with Python HTTP API and SQLite evidence. Real CPU model servers expose loopback OpenAI-compatible endpoints at 8788/8789; users explicitly register them. The Worker is a separate limited metadata runtime, not a hosted replacement for all local API routes.

Run `.pushgate/run.sh` from an environment with PostgreSQL shared memory and Chromium permission. On this Mac, keep the isolated host Chromium running and use the host command in ENVIRONMENT_UNBLOCK_PLAN.md. Source changes require the gate again. Generated evidence changes alone do not alter model responses or evaluator hashes.

After approved GitHub publication, make `pushgate / gate` a required check and disallow force pushes. Onboarding must run `git config core.hooksPath .githooks`; Git does not install hooks automatically on clone.
