# Praxis local runner

From the repository root, create a virtual environment, install `pip install -e '.[test,browser]'` and run `python -m playwright install chromium` if browser checks are wanted. Without installation, `PYTHONPATH=runner python3 -m praxis` works when Pydantic/JSON Schema dependencies are installed.

```
praxis suites list
praxis validate packages/scenarios/structured-agent-v1.json
praxis run --provider demo --suite structured-agent --output data/demo-run.json
praxis run --provider ollama --endpoint http://127.0.0.1:11434 --model YOUR_MODEL --output data/ollama-run.json
praxis run --provider openai --endpoint https://YOUR_PROVIDER/v1 --model YOUR_MODEL --output data/model-run.json
praxis report data/demo-run.json --output data/report.html
praxis world --domain customer-support --seed 73 --output data/world.json
praxis check-website --output-dir data/website-proof
```

`PRAXIS_MODEL_API_KEY` is read only by the local process and not persisted. Other environment variable names can be selected by `--key-env`. Endpoint credentials in URLs, query strings and redirects are rejected. The local runner deliberately can reach loopback for Ollama; this adapter must never be exposed as a hosted arbitrary-URL proxy.

The custom HTTP protocol sends POST `{protocol:"praxis.model.v1",model,input,seed,max_tokens}` and requires response `{output: JSON|string, usage?:object}`. OpenAI-compatible uses `/chat/completions`; Ollama uses `/api/chat` and does not assume compatible sampling fields. Non-demo inference is self-reported, never automatically verified. No external inference is made by the demo provider. Demo fixtures read explicit passing/failing outputs to exercise the grading infrastructure.

There are 36 public deterministic tasks across five immutable fixture suite versions. JSON Schema and bounded assertion operators (`equals`, `contains`, `not_contains`, `subset`, `gte`, `lte`) grade each independently. Each failed provider call produces a failing assertion. The primary denominator is **all suite tasks**, including not-run tasks. Assertion-weighted score is separate from full task completion. Wilson intervals describe the observed fixture task sample, not a general model confidence claim. Cost remains unknown, never zero inferred from missing usage. No LLM judge is used.

Worlds are real bounded state machines with seeded entities, dependencies, denied actions, snapshot hashes and replay; the reference policy is a clearly labeled **demo**, not a model-driven agent. Support, research, workflow and web-product state contracts are included. External-model-driven world action policies are not implemented. A separate `agent-workflows` suite uses an actual bounded agent loop with permissioned lookup, refund and escalation tools. It independently grades mutated state, tool permissions and final responses. External providers return one JSON tool action per step; demo providers use labeled action scripts. Invoke it with `praxis run --kind agent --provider demo --suite agent-workflows`. The web-product world tests state dependency contracts, not website rendering.

Developer-contract tasks assess code/UI/API reasoning and are explicitly **not** executable application evaluations. Browser verification is a separate real Playwright harness for a source-controlled owned website fixture. It checks cart mutation, search, invalid email rejection, labels, two viewport sizes and runtime errors; screenshots are persisted. The browser context has no inherited credentials and denies network, but this is not an OS security sandbox. Arbitrary untrusted HTML/code workloads are therefore **rejected**, rather than silently run without robust isolation. Container/cloud executor support is not implemented.

Streaming, resumed individual tasks, judge adapters, real image/video inference and automatic token pricing are unsupported. Cancellation is checked between calls; in-flight network reads obey provider deadlines. Maximum retries 2, 64 tasks, 600-second suite budget, 8192 output tokens and 2 MiB HTTP responses are enforced. Output schema references are rejected. A configured API key and endpoint may incur provider costs; the CLI is user-controlled and does not start paid calls unless explicitly invoked.
