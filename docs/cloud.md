# Cloud deployment and boundaries

The complete integrated application currently runs locally. The Cloudflare Worker is a separate, deliberately limited metadata control plane: validated Supabase authentication, immutable target registration, versioned run requests, evidence submission and private run reads. It does not execute inference, custom URL requests, HTML or user code. Cloud Arena, cloud cancellation/background dispatch, official publication, R2 uploads and frontend Supabase sign-in are not connected. Do not deploy the local frontend against this Worker and describe it as feature complete.

## Historical source review checkpoint

The following paragraph describes the earlier environment, not current cloud acceptance. Current disposable PostgreSQL 17 results are in `evidence/final/postgres.json`; hosted Supabase Auth remains unverified.

## Reviewed source and verification

The Worker validates access tokens by contacting Supabase Auth `/auth/v1/user`; it forwards the same user token to PostgREST, preserving database RLS. No service-role fallback exists. The Supabase URL is operator configured, never supplied by a request. User metadata never determines access. See [Supabase authentication](https://supabase.com/docs/reference/javascript/auth-getuser) and [row security](https://supabase.com/docs/guides/database/postgres/row-level-security). These official docs were reviewed during implementation. The changelog markdown could not be fetched by the available web reader (unsupported markdown response), and direct host DNS was unavailable; no claim of complete changelog review is made.

`supabase/schema.sql` is reviewed schema source, not an applied or CLI-generated migration. This environment did not provide Supabase CLI, PostgreSQL or cloud credentials. Consequently SQL execution, Auth integration and actual RLS enforcement have **not been verified**. `supabase/tests/ownership.sql` supplies transaction-rolled-back positive and negative checks to run on a throwaway database. Passing mocked Worker tests does not prove real RLS. Verified locally: API TypeScript check passed; shared contracts check passed; 14/14 Worker security tests passed. Wrangler 4.157.0 dry-run bundled 777.35 KiB (122.06 KiB gzip) with no deployment. The dry-run command was `XDG_CONFIG_HOME=./work/wrangler-config WRANGLER_SEND_METRICS=false WRANGLER_LOG_PATH=./work/wrangler.log npm run deploy:review --workspace apps/api`; redirecting its configuration avoids writing into the protected user preferences directory.

Schema controls include RLS on every table, explicit revoked anonymous grants, owner-only reads and inserts, immutable model/suite revisions, composite owner/parent foreign keys, run/evidence uniqueness, no user trust promotion, and operator-only runner approval, voting and ratings. Organization records are stored but collaborative membership authorization is not enabled. Official rankings stay empty until an operator pipeline is implemented and verified.

## Safe deployment procedure (approval required)

1. Install and inspect current Supabase CLI: `supabase --help`, `supabase migration --help`, `supabase migration new --help`, `supabase db --help`. Work in a dedicated throwaway local Supabase project.
2. Generate a migration using `supabase migration new praxis_schema`; copy `supabase/schema.sql` into the newly generated file. Do not invent a migration timestamp or use a production database to develop policies.
3. Apply locally, run `supabase/tests/ownership.sql`, and run the CLI's supported advisors. Review all deny and allow checks. Add full per-table tests before production.
4. Confirm quotas and the then-current provider pricing. Cloudflare CPU limits do not allow arbitrary inference. R2 storage and egress, Supabase usage and model inference may incur charges. Configure explicit budgets; no unlimited free compute is promised.
5. Configure `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` and exact `ALLOWED_ORIGIN`. Never put a Supabase secret/service-role key in the frontend or this Worker.
6. Run `npm run build`, `npm run test --workspace apps/api`, and `npm run deploy:review --workspace apps/api` for a Wrangler dry run. This last command still requires dependencies/platform compatibility and is not a production deployment.
7. Obtain explicit user approval before remote migrations, resource creation, secret configuration or `wrangler deploy`. No public deployment has occurred.

## HTTP interface

Authenticated endpoints require a Supabase bearer access token. `/api/health` is public. `/api/me`, GET/POST `/api/targets`, GET/POST `/api/runs`, GET `/api/runs/:id` and POST `/api/evidence` are implemented. POST schemas are in `packages/contracts`; unknown fields are rejected. Evidence is capped at 1 MiB, records are marked self-reported and duplicate manifests return HTTP 409. A cryptographic digest is not proof of benchmark truth.

All responses have request IDs, no-store, nosniff and restrictive CSP. Cross-origin access is denied except the exact configured frontend origin. Configure Cloudflare edge rate limits before public exposure: application-level distributed quota enforcement is not implemented. The API exposes at most 100 records per list; cursor pagination remains unsupported. Revocation and account deletion require an operator process; validate existing sessions before sensitive lifecycle actions.

Large artifacts remain local. R2 has no binding or public upload route until authenticated object authorization, MIME sniffing, retention and signed access are implemented. Browser previews must remain isolated from the primary origin.

## Dedicated project website

`npm run website:build` emits static `apps/website/dist`; it is separate from the local evaluation frontend and metadata Worker. No hosting resources, Site registration, production secrets or public deployment were created in this mission. Before approved hosting, configure the actual canonical origin/social URL, static security headers and real-URL acceptance. See `apps/website/README.md`.

The current cloud audit verified schema/migration equality and executed ownership/persistence SQL against real network-isolated PostgreSQL 17 with synthetic auth claims. This is local database acceptance only, not hosted Supabase authentication or a remote migration. GitHub credentials may independently block branch/PR publication; see the final handoff for actual operations.
