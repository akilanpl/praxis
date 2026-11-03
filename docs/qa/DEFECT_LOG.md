# Confirmed defects and repairs

- Python 3.9 direct socket timeout was mislabeled connection_error. Existing HTTP deadline test failed; classified socket.timeout correctly; full HTTP suite passed.
- Application connection diagnostics incorrectly invoked model inference. New regression failed first; diagnostics now issue bounded GET /health; application tests passed.
- Target and world wrong-type/non-finite/out-of-range values could persist or produce HTTP 500. Forty of 44 new validation cases initially failed. Strict type/budget/domain/seed validation, safe slugs, clone-ID stripping and idempotency mismatch protection made all 44 pass.
- Website harness incorrectly used input_value on an HTML output element. Switched to reading rendered text; seven real browser assertions passed.
- Arena automatically loaded the next pair while displaying prior identities. Hold the voted pair with disabled vote buttons; explicit next comparison clears identities. Full real-model browser journey passed.
- Forms could be submitted repeatedly without a stable request key. Added in-flight guard, disabled submit state and a per-launch idempotency key. Server rejects key reuse with different payloads.
- Expired sessions did not restore sign-in, and slow requests could populate a newer route. Clear invalid sessions and check route/session identity before rendering response data.
- Disposable PostgreSQL socket path exceeded macOS limits. Use a short private temporary directory; host run then passed and stopped its own server.
- Python 3.9 dependency versions were below current security fixes. Preserve old virtualenv under ignored work/, require Python 3.12, install patched tooling and freeze versions; new pip-audit reports zero known vulnerabilities.
- Public acceptance exports included random idempotency nonces flagged by Gitleaks. Omit replay nonces from shared exports, retain complete private DB records and unchanged model evidence hashes. No provider keys were present in those artifacts.
