import { api } from "./api";
import { recordMatches } from "./records";
import { useState, useEffect, useRef, useMemo, lazy, Suspense } from "react";
import Overview from "./Overview";
import { WorkspaceShell, Badge, CodeBlock, Icon } from "./ui";
const RunInspector = lazy(() => import("./RunInspector"));
const SuiteEditor = lazy(() => import("./SuiteViews"));
const SuiteExplorer = lazy(() =>
  import("./SuiteViews").then((module) => ({ default: module.SuiteExplorer })),
);
const Settings = lazy(() => import("./Settings"));
const ArtifactInspector = lazy(() => import("./ArtifactInspector"));
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";
import "./style.css";
export function App() {
  const location = useLocation();
  let p = location.pathname,
    n = useNavigate();
  let [data, D] = useState<any>(null),
    [error, E] = useState(""),
    [notice, Notice] = useState(""),
    [token, T] = useState(localStorage.token),
    [out, O] = useState<any>(null),
    [targets, ST] = useState<any[]>([]),
    [suites, SS] = useState<any[]>([]),
    [search, Search] = useState(""),
    [chosenTarget, ChooseTarget] = useState(""),
    [busy, Busy] = useState(false),
    [history, History] = useState<any[]>([]),
    [sort, Sort] = useState("recent"),
    [page, Page] = useState(1),
    [filter, Filter] = useState("all"),
    [diagnostics, Diagnostics] = useState<Record<string, any>>({}),
    [provider, Provider] = useState("demo"),
    [chosenSuite, ChooseSuite] = useState("");
  useEffect(() => {
    Search(new URLSearchParams(location.search).get("record") || "");
    Page(1);
    Filter("all");
    ChooseTarget(new URLSearchParams(location.search).get("target") || "");
    ChooseSuite("");
    Provider(p.startsWith("/apps") ? "custom" : "demo");
  }, [p, location.search]);
  useEffect(() => {
    Page(1);
  }, [search, sort, filter]);
  useEffect(() => {
    Diagnostics({});
  }, [token]);
  const dataSession = useRef(token),
    auxSession = useRef(token);
  if (dataSession.current !== token) data = null;
  if (auxSession.current !== token) {
    targets = [];
    suites = [];
    history = [];
  }
  useEffect(() => {
    dataSession.current = token;
    auxSession.current = token;
    D(null);
    ST([]);
    SS([]);
    History([]);
    ChooseTarget("");
    ChooseSuite("");
  }, [token]);
  const pending = useRef(false),
    runTicket = useRef(crypto.randomUUID()),
    activePath = useRef(p),
    activeToken = useRef(token);
  activePath.current = p;
  activeToken.current = token;
  useEffect(() => {
    const expired = () => {
      delete localStorage.token;
      T("");
      Notice(
        "Your local session expired. Sign in to continue inspecting private evidence.",
      );
    };
    const storage = (e: StorageEvent) => {
      if (e.key === "token" || e.key === null) T(localStorage.token || "");
    };
    window.addEventListener("praxis-session-expired", expired);
    window.addEventListener("storage", storage);
    return () => {
      window.removeEventListener("praxis-session-expired", expired);
      window.removeEventListener("storage", storage);
    };
  }, []);
  useEffect(() => {
    let current = true;
    if (token) {
      if (!["/targets", "/models", "/agents", "/apps"].includes(p))
        api("/targets")
          .then((x) => {
            if (current) ST(x);
          })
          .catch((e) => {
            if (current) E(e.message);
          });
      if (["/dashboard", "/targets", "/models", "/agents", "/apps"].includes(p))
        api("/runs")
          .then((x) => {
            if (current) History(Array.isArray(x) ? x : []);
          })
          .catch((e) => {
            if (current) E(e.message);
          });
      if (p !== "/suites")
        api("/suites")
          .then((x) => {
            if (current) SS(x);
          })
          .catch((e) => {
            if (current) E(e.message);
          });
    } else {
      ST([]);
      SS([]);
      History([]);
    }
    return () => {
      current = false;
    };
  }, [token, p]);
  let area = p.split("/")[1] || "home";
  let endpoint = (
    {
      targets: "targets",
      reports: "runs",
      models: "targets",
      agents: "targets",
      apps: "targets",
      dashboard: "dashboard",
      runs: "runs",
      suites: "suites",
      worlds: "worlds",
      arena: "arena",
      leaderboards: "leaderboards",
      compare: "runs",
      artifacts: "artifacts",
    } as any
  )[area];
  let load = () => {
    if (endpoint && token && !p.endsWith("/new"))
      api(
        "/" +
          endpoint +
          (["runs", "worlds", "suites"].includes(area) &&
          p.split("/")[2] &&
          p.split("/")[2] !== "new"
            ? "/" + p.split("/")[2]
            : ""),
      )
        .then((x) => {
          if (activePath.current === p && activeToken.current === token) {
            D(x);
            if (Array.isArray(x)) {
              if (endpoint === "targets") ST(x);
              if (endpoint === "suites") SS(x);
              if (endpoint === "runs") History(x);
            }
            E("");
          }
        })
        .catch((e) => {
          if (activePath.current === p && activeToken.current === token)
            E(e.message);
        });
  };
  useEffect(() => {
    D(null);
    O(null);
    E("");
    if (p === "/runs/new") runTicket.current = crypto.randomUUID();
    load();
  }, [p, token]);
  useEffect(() => {
    if (area === "runs" && ["queued", "running"].includes(data?.status)) {
      let i = setInterval(load, 2000);
      return () => clearInterval(i);
    }
  }, [p, token, data?.status]);
  async function action(path: string, body: any) {
    if (pending.current) return;
    pending.current = true;
    Busy(true);
    try {
      E("");
      let x = await api(path, body);
      if (activePath.current !== p || activeToken.current !== token) return;
      O(path.startsWith("/auth/") ? null : x);
      if (!path.includes("/vote") && !path.includes("/auth/logout")) load();
      return x;
    } catch (e: any) {
      if (activePath.current === p && activeToken.current === token)
        E(e.message);
    } finally {
      pending.current = false;
      Busy(false);
    }
  }
  let rows = Array.isArray(data) ? data : [];
  const matchingSuites = suites
    .filter((s) => {
      const kind =
        targets.find((t) => t.id === (chosenTarget || targets[0]?.id))?.kind ||
        "model";
      return s.tasks?.every((task: any) =>
        kind === "agent"
          ? !!task.environment
          : kind === "application"
            ? !!task.api_request
            : !task.environment && !task.api_request,
      );
    })
    .sort(
      (a, b) =>
        Number(b.slug === "structured-agent") -
        Number(a.slug === "structured-agent"),
    );
  const selectedTarget = targets.find(
    (t) => t.id === (chosenTarget || targets[0]?.id),
  );
  const selectedSuite =
    matchingSuites.find((s) => s.slug + "@" + s.version === chosenSuite) ||
    matchingSuites[0];
  const revision = useMemo(() => {
    const source = new URLSearchParams(location.search).get("source");
    const suite = suites.find((s) => s.slug + "@" + s.version === source);
    if (!suite) return undefined;
    const parts = String(suite.version).split(".");
    parts[parts.length - 1] = String(
      (Number(parts[parts.length - 1]) || 0) + 1,
    );
    return { ...suite, version: parts.join(".") };
  }, [location.search, suites]);
  const filteredRows = rows
    .filter(
      (x) =>
        !["models", "agents", "apps"].includes(area) ||
        x.kind ===
          ({ models: "model", agents: "agent", apps: "application" } as any)[
            area
          ],
    )
    .filter((x) => area !== "reports" || !!x.result)
    .filter((x) => recordMatches(x, search))
    .filter(
      (x) =>
        filter === "all" ||
        [x.kind, x.status, x.provider, x.trust].includes(filter),
    )
    .sort((a, b) =>
      sort === "name"
        ? String(a.target_name || a.name || a.title || a.id).localeCompare(
            String(b.target_name || b.name || b.title || b.id),
          )
        : sort === "status"
          ? String(a.status || a.provider || "").localeCompare(
              String(b.status || b.provider || ""),
            )
          : (b.created_at || 0) - (a.created_at || 0),
    );
  const pages = Math.max(1, Math.ceil(filteredRows.length / 12));
  const visibleRows = filteredRows.slice(
    (Math.min(page, pages) - 1) * 12,
    Math.min(page, pages) * 12,
  );
  const loading = (
    <div className="loading-state" role="status">
      <span>Loading workspace…</span>
      <div className="skeleton" />
      <div className="skeleton" />
      <div className="skeleton" />
    </div>
  );
  function refreshWorkspace() {
    load();
    if (["/dashboard", "/targets", "/models", "/agents", "/apps"].includes(p))
      api("/runs")
        .then((x) => {
          if (activePath.current === p && activeToken.current === token)
            History(Array.isArray(x) ? x : []);
        })
        .catch((e) => {
          if (activePath.current === p && activeToken.current === token)
            E(e.message);
        });
  }
  async function diagnose(id: string) {
    const result = await action("/targets/" + id + "/diagnostics", {});
    if (result) Diagnostics((d) => ({ ...d, [id]: result }));
  }

  function form(kind: string) {
    return (
      <form
        key={token + kind + area}
        aria-busy={busy}
        onSubmit={async (e) => {
          e.preventDefault();
          let f = Object.fromEntries(new FormData(e.currentTarget));
          if (kind === "auth") {
            let x = await action("/auth/" + f.mode, {
              username: f.username,
              password: f.password,
            });
            if (x) {
              Notice("");
              localStorage.token = x.token;
              T(x.token);
              n("/dashboard");
            }
          } else if (kind === "target") {
            let saved = await action("/targets", {
              ...f,
              max_tokens: Number(f.max_tokens || 1024),
              temperature: Number(f.temperature || 0),
              timeout: Number(f.timeout),
              allow_mutation: f.allow_mutation === "on",
              authorized: f.authorized === "on",
              kind:
                area === "agents"
                  ? "agent"
                  : area === "apps"
                    ? "application"
                    : "model",
              capabilities:
                area === "agents"
                  ? ["text", "json", "tools"]
                  : area === "apps"
                    ? ["web", "json"]
                    : ["text", "json"],
            });
            if (saved) n("/" + area);
          } else if (kind === "run") {
            let x = await action("/runs", {
              ...f,
              suite_slug: String(f.suite_slug).split("@")[0],
              suite_version: String(f.suite_slug).split("@")[1],
              idempotency_key: runTicket.current,
              seed: Number(f.seed),
              public: f.public === "on",
            });
            if (x) n("/runs/" + x.id);
          } else if (kind === "world") {
            let saved = await action("/worlds", {
              ...f,
              seed: Number(f.seed),
              max_level: Number(f.max_level),
            });
            if (saved) n("/worlds");
          }
        }}
      >
        {kind === "auth" ? (
          <>
            <label>
              Account name
              <input name="username" required minLength={3} />
            </label>
            <label>
              Password
              <input name="password" type="password" required minLength={10} />
            </label>
            <label>
              Action
              <select name="mode">
                <option value="register">Create local account</option>
                <option value="login">Sign in</option>
              </select>
            </label>
          </>
        ) : kind === "target" ? (
          <>
            <label>
              Name
              <input name="name" maxLength={120} required />
            </label>
            <label>
              Provider
              <select
                name="provider"
                value={provider}
                onChange={(e) => Provider(e.target.value)}
              >
                {(area === "apps"
                  ? ["custom"]
                  : ["demo", "demo-failing", "openai", "ollama", "custom"]
                ).map((x) => (
                  <option key={x}>{x}</option>
                ))}
              </select>
            </label>
            <label>
              Endpoint
              <input
                name="endpoint"
                type="url"
                required={area === "apps" || !provider.startsWith("demo")}
                placeholder="http://localhost:11434"
              />
            </label>
            {area !== "apps" && (
              <label>
                Model identifier
                <input name="model" defaultValue="demo" required />
              </label>
            )}
            <div className="form-grid budget-fields">
              {area !== "apps" && (
                <>
                  <label>
                    Response token limit
                    <input
                      type="number"
                      name="max_tokens"
                      min={1}
                      max={8192}
                      defaultValue={1024}
                      required
                    />
                  </label>
                  <label>
                    Temperature
                    <input
                      type="number"
                      name="temperature"
                      min={0}
                      max={2}
                      step={0.1}
                      defaultValue={0}
                      required
                    />
                  </label>
                </>
              )}
              <label>
                Request timeout (seconds)
                <input
                  type="number"
                  name="timeout"
                  min={0.1}
                  max={120}
                  step={0.1}
                  defaultValue={20}
                  required
                />
              </label>
            </div>
            <div className="validation-note">
              <Badge tone={provider.startsWith("demo") ? "warning" : "neutral"}>
                {area === "apps"
                  ? "Owned HTTP execution"
                  : provider.startsWith("demo")
                    ? "Deterministic fixture"
                    : "Configured provider"}
              </Badge>
              <p>
                {area === "apps"
                  ? "HTTP contracts execute actual requests. Ownership and mutation permissions are explicit."
                  : provider.startsWith("demo")
                    ? "No model inference occurs. Use this provider to test the evaluation pipeline."
                    : "Connection status is unknown until you test the endpoint. Credentials are read from PRAXIS_MODEL_API_KEY on the local runtime."}
              </p>
            </div>
            {area === "apps" && (
              <label className="check">
                <input type="checkbox" name="authorized" required /> I own this
                endpoint or have permission to run these HTTP checks
              </label>
            )}
            {area === "apps" && (
              <label className="check">
                <input type="checkbox" name="allow_mutation" /> Allow explicit
                POST contract tests on this owned application
              </label>
            )}
            <p>
              Credentials stay on the local runner. Demo output is excluded from
              official rankings.
            </p>
          </>
        ) : kind === "run" ? (
          <>
            <label>
              Target ID
              <select
                name="target_id"
                required
                value={chosenTarget || targets[0]?.id || ""}
                onChange={(e) => {
                  ChooseTarget(e.target.value);
                  ChooseSuite("");
                }}
              >
                {targets.map((t) => (
                  <option value={t.id} key={t.id}>
                    {t.name} · {t.provider}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Suite slug
              <select
                name="suite_slug"
                key={chosenTarget}
                required
                value={
                  selectedSuite
                    ? selectedSuite.slug + "@" + selectedSuite.version
                    : ""
                }
                onChange={(e) => ChooseSuite(e.target.value)}
              >
                {matchingSuites.map((t) => (
                  <option
                    value={t.slug + "@" + t.version}
                    key={t.slug + "@" + t.version}
                  >
                    {t.title} · {t.version}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Seed
              <input
                name="seed"
                type="number"
                defaultValue={73}
                min={-2147483648}
                max={2147483647}
                required
              />
            </label>
            <div className="launch-summary">
              <div className="section-label">EXECUTION PLAN</div>
              <h3>{selectedSuite?.title || "Select a compatible suite"}</h3>
              <dl className="metadata-list">
                <div>
                  <dt>Scenarios</dt>
                  <dd>{selectedSuite?.tasks?.length ?? "—"}</dd>
                </div>
                <div>
                  <dt>Execution kind</dt>
                  <dd>{selectedTarget?.kind || "No target selected"}</dd>
                </div>
                <div>
                  <dt>Provider</dt>
                  <dd>
                    <Badge
                      tone={
                        selectedTarget?.provider?.startsWith("demo")
                          ? "warning"
                          : "neutral"
                      }
                    >
                      {selectedTarget?.kind === "application"
                        ? "Actual owned HTTP requests"
                        : selectedTarget?.provider?.startsWith("demo")
                          ? "Deterministic fixture · no inference"
                          : selectedTarget?.provider || "Not selected"}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt>Request bound</dt>
                  <dd>{selectedTarget?.timeout ?? 20} seconds</dd>
                </div>
                <div>
                  <dt>Scenario token limit</dt>
                  <dd>
                    {selectedTarget?.kind === "application"
                      ? "Not applicable to HTTP"
                      : Math.min(
                          selectedTarget?.max_tokens ?? 1024,
                          selectedSuite?.execution?.max_output_tokens ?? 8192,
                        )}
                  </dd>
                </div>
                <div>
                  <dt>Suite wall limit</dt>
                  <dd>
                    {selectedSuite?.execution?.max_wall_seconds ?? 120} seconds
                  </dd>
                </div>
                <div>
                  <dt>Scenario execution cap</dt>
                  <dd>
                    {Math.min(
                      selectedSuite?.tasks?.length ?? 0,
                      selectedSuite?.execution?.max_scenario_count ?? 64,
                    )}{" "}
                    · unexecuted tasks remain in the denominator
                  </dd>
                </div>
                <div>
                  <dt>Retry policy</dt>
                  <dd>
                    {selectedSuite?.execution?.max_retries ?? 0} retries · POST
                    mutations are never automatically replayed
                  </dd>
                </div>
              </dl>
              <p>
                Completion is not a task pass. Required assertions determine
                success; unexecuted tasks stay in the denominator.
              </p>
              {!targets.length && (
                <Link to="/models/new">Register a target first →</Link>
              )}
            </div>
            <label className="check">
              <input type="checkbox" name="public" /> Publish outputs for blind
              community comparisons
            </label>
            <p>
              Publishing permits other accounts to view and vote on your
              outputs. Keep private prompts and sensitive data out of public
              runs.
            </p>
          </>
        ) : (
          <>
            <label>
              Name
              <input name="name" maxLength={120} required />
            </label>
            <label>
              Domain
              <select name="domain">
                {["support", "research", "workflow", "web-product"].map((x) => (
                  <option key={x}>{x}</option>
                ))}
              </select>
            </label>
            <label>
              Maximum level
              <input
                name="max_level"
                type="number"
                min="1"
                max="3"
                defaultValue="3"
              />
            </label>
            <label>
              Seed
              <input name="seed" type="number" defaultValue="73" />
            </label>
          </>
        )}
        <button
          type="submit"
          disabled={
            busy || (kind === "run" && (!selectedTarget || !selectedSuite))
          }
        >
          {kind === "auth"
            ? "Continue"
            : kind === "run"
              ? "Start evaluation"
              : "Save configuration"}
        </button>
      </form>
    );
  }
  return (
    <WorkspaceShell
      token={token}
      targets={targets}
      suites={suites}
      runs={history}
      refresh={refreshWorkspace}
      onSignOut={async () => {
        const result = await action("/auth/logout", {});
        delete localStorage.token;
        T("");
        Notice(
          result
            ? ""
            : "Signed out in this browser. Server session revocation could not be verified.",
        );
      }}
    >
      {notice && (
        <div className="notice" role="status">
          {notice}
          <button className="ghost" onClick={() => Notice("")}>
            Dismiss notice
          </button>
        </div>
      )}
      {error && (
        <div role="alert" className="error">
          {error}
        </div>
      )}
      {area === "home" ? (
        <>
          <section className="hero">
            <span className="eyebrow">ARTIFACT FIRST AI EVALUATION</span>
            <h1>
              Judge AI by
              <br />
              what it accomplishes.
            </h1>
            <p>
              Connect a model. Run reproducible tasks. Inspect the evidence
              behind every result.
            </p>
            <Link className="button" to={token ? "/dashboard" : "/settings"}>
              Open your laboratory ↗
            </Link>
            <small>
              Local execution · No cloud account required · Demo results clearly
              labeled
            </small>
          </section>
          <section className="grid">
            {[
              [
                "01",
                "Connect",
                "Register models, tool agents and applications as distinct targets.",
              ],
              [
                "02",
                "Execute",
                "Run versioned tasks with independent assertions and bounded worlds.",
              ],
              [
                "03",
                "Inspect",
                "Trace failures, replay conditions and compare matched artifacts.",
              ],
            ].map(([a, b, c]) => (
              <article>
                <span className="eyebrow">{a} / LAB PROTOCOL</span>
                <h2>{b}</h2>
                <p>{c}</p>
              </article>
            ))}
          </section>
          <section className="hero">
            <h2>
              Every claim needs evidence.
              <br />
              Every failure teaches something.
            </h2>
            <p>
              Objective execution and human preference remain separate. Local
              reports are self reported; demo providers never enter official
              rankings.
            </p>
          </section>
        </>
      ) : (
        <>
          <div className="title">
            <div>
              <span className="eyebrow">
                LOCAL WORKSPACE /{" "}
                {area === "runs" ? "EXECUTION & EVIDENCE" : "PRAXIS"}
              </span>
              <h1>
                {area === "runs"
                  ? p === "/runs/new"
                    ? "Launch evaluation"
                    : "Run evidence"
                  : (
                      {
                        dashboard: "Overview",
                        targets: "Targets",
                        models: "Models",
                        agents: "Agents",
                        apps: "HTTP applications",
                        suites: "Evaluation suites",
                        compare: "Comparisons",
                        reports: "Reports",
                        settings: "Workspace settings",
                      } as any
                    )[area] || area[0].toUpperCase() + area.slice(1)}
              </h1>
            </div>
            {[
              "targets",
              "models",
              "agents",
              "apps",
              "suites",
              "worlds",
            ].includes(area) &&
              !p.endsWith("/new") && (
                <Link
                  className="button"
                  to={area === "targets" ? "/models/new" : "/" + area + "/new"}
                >
                  Create{" "}
                  {area === "suites"
                    ? "suite"
                    : area === "worlds"
                      ? "world"
                      : "target"}{" "}
                  +
                </Link>
              )}
          </div>
          {["targets", "models", "agents", "apps"].includes(area) &&
            !p.endsWith("/new") && (
              <div className="route-tabs">
                <Link
                  className={area === "targets" ? "selected" : ""}
                  to="/targets"
                >
                  All targets
                </Link>
                <Link
                  className={area === "models" ? "selected" : ""}
                  to="/models"
                >
                  Models
                </Link>
                <Link
                  className={area === "agents" ? "selected" : ""}
                  to="/agents"
                >
                  Agents
                </Link>
                <Link className={area === "apps" ? "selected" : ""} to="/apps">
                  HTTP applications
                </Link>
              </div>
            )}
          {!token ? (
            form("auth")
          ) : endpoint && !data && !p.endsWith("/new") ? (
            error ? (
              <article className="empty-state">
                <Icon name="clock" size={28} />
                <h2>Workspace unavailable</h2>
                <p>
                  Your saved evidence has not been replaced. Retry the local API
                  request.
                </p>
                <button onClick={load}>Retry request</button>
              </article>
            ) : (
              loading
            )
          ) : p.endsWith("/new") ? (
            area === "suites" ? (
              <Suspense fallback={loading}>
                <SuiteEditor
                  key={token + location.search}
                  initial={revision}
                  busy={busy}
                  onError={E}
                  onSave={async (value) => {
                    let saved = await action("/suites", value);
                    if (saved) n("/suites");
                  }}
                />
              </Suspense>
            ) : (
              <div className="configuration-layout">
                <div>
                  <div className="form-intro">
                    <h2>
                      {area === "runs"
                        ? "Configure a reproducible evaluation"
                        : area === "worlds"
                          ? "Create a reference environment"
                          : "Register an evaluation target"}
                    </h2>
                    <p>
                      {area === "runs"
                        ? "Match a target with a versioned contract. Inspect the execution plan before launch."
                        : "Configuration is stored locally. Explicit permissions and evidence determine what a target can do."}
                    </p>
                  </div>
                  {form(
                    area === "runs"
                      ? "run"
                      : area === "worlds"
                        ? "world"
                        : "target",
                  )}
                </div>
                <aside className="configuration-note">
                  <span className="eyebrow">BEFORE YOU BEGIN</span>
                  <h3>Make the contract explicit.</h3>
                  <p>
                    Models generate responses. Agents execute permitted tools.
                    HTTP targets receive actual requests. Their execution
                    semantics remain distinct.
                  </p>
                  <p>
                    Store credentials in the runtime environment. Public outputs
                    are opt-in; private data stays private by default.
                  </p>
                  <Link to="/methodology">
                    How evaluation works <Icon name="arrow" size={14} />
                  </Link>
                </aside>
              </div>
            )
          ) : area === "settings" ? (
            <Suspense fallback={loading}>
              <Settings key={token} />
            </Suspense>
          ) : area === "dashboard" ? (
            <Overview
              data={data}
              targets={targets}
              suites={suites}
              runs={history}
            />
          ) : area === "arena" ? (
            data?.id ? (
              <>
                <p>
                  Blind comparison ·{" "}
                  {data.demo ? "Demonstration artifacts" : "Matched conditions"}
                </p>
                <div className="grid">
                  {["a", "b"].map((x) => (
                    <article>
                      <h2>Output {x.toUpperCase()}</h2>
                      <pre>{data[x]?.content}</pre>
                    </article>
                  ))}
                </div>
                <div className="actions">
                  {["a", "b", "tie", "both_bad"].map((choice) => (
                    <button
                      key={choice}
                      disabled={busy || !!out?.choice}
                      onClick={() =>
                        action("/arena/" + data.id + "/vote", { choice })
                      }
                    >
                      {choice === "a"
                        ? "A wins"
                        : choice === "b"
                          ? "B wins"
                          : choice === "tie"
                            ? "Tie"
                            : "Both bad"}
                    </button>
                  ))}
                </div>
                {out?.choice && (
                  <article>
                    <h2>Vote recorded</h2>
                    <p>
                      A: {out.a} · B: {out.b}
                    </p>
                    <button
                      onClick={() => {
                        O(null);
                        load();
                      }}
                    >
                      Next comparison
                    </button>
                  </article>
                )}
              </>
            ) : (
              <article>
                <h2>No eligible comparison yet</h2>
                <p>
                  {data?.reason ||
                    "Run two distinct targets on the same versioned task. Self voting is excluded."}
                </p>
              </article>
            )
          ) : area === "leaderboards" ? (
            <>
              <article>
                <h2>Objective evidence</h2>
                <p>
                  Only approved trusted execution qualifies. Demo and self
                  reported runs are excluded.
                </p>
                <pre>{JSON.stringify(data?.objective || [], null, 2)}</pre>
              </article>
              <article>
                <h2>Community preference</h2>
                <p>
                  Sparse ratings are insufficient evidence for a global rank.
                </p>
                <pre>{JSON.stringify(data?.preference || [], null, 2)}</pre>
              </article>
            </>
          ) : area === "runs" && data && !Array.isArray(data) ? (
            <Suspense fallback={loading}>
              <RunInspector
                run={data}
                busy={busy}
                onCancel={() => action("/runs/" + data.id + "/cancel", {})}
                onExport={async () => {
                  try {
                    let r = await api("/runs/" + data.id + "/export");
                    const { downloadFile } = await import("./RunInspector");
                    if (
                      activePath.current !== p ||
                      activeToken.current !== token
                    )
                      return;
                    downloadFile(
                      JSON.stringify(r, null, 2),
                      "praxis-run.json",
                      "application/json",
                    );
                  } catch (e: any) {
                    E(e.message);
                  }
                }}
              />
            </Suspense>
          ) : ["worlds", "suites"].includes(area) &&
            data &&
            !Array.isArray(data) ? (
            <article>
              <h2>{data.name || data.title || data.id || data.slug}</h2>
              {area === "worlds" ? (
                <>
                  <button
                    onClick={() => action("/worlds/" + data.id + "/replay", {})}
                  >
                    Execute deterministic replay
                  </button>
                  <p>
                    Demonstration reference policy; no external model inference.
                    Each complexity level records changed state, transitions and
                    independent assertions.
                  </p>
                  {(out?.levels || data.replay?.levels || []).map(
                    (x: any, i: number) => (
                      <section>
                        <h3>Level {x.level || i + 1}</h3>
                        <pre>{JSON.stringify(x, null, 2)}</pre>
                      </section>
                    ),
                  )}
                </>
              ) : (
                <>
                  <div className="actions">
                    <button
                      onClick={async () => {
                        let slug = String(data.slug) + "-copy-" + Date.now();
                        let x = await action("/suites", {
                          ...data,
                          slug,
                          title: data.title + " copy",
                        });
                        if (x) n("/suites/" + slug + "@" + x.version);
                      }}
                    >
                      Clone suite
                    </button>
                    <button
                      onClick={() => {
                        let a = document.createElement("a");
                        a.href = URL.createObjectURL(
                          new Blob([JSON.stringify(data, null, 2)], {
                            type: "application/json",
                          }),
                        );
                        a.download = data.slug + ".json";
                        a.click();
                      }}
                    >
                      Export JSON
                    </button>
                  </div>
                  <p>
                    {data.tasks?.length} immutable task definitions · Version{" "}
                    {data.version}
                  </p>
                </>
              )}
              {area === "suites" ? (
                <Suspense fallback={loading}>
                  <SuiteExplorer suite={data} />
                </Suspense>
              ) : (
                <CodeBlock value={data} />
              )}
            </article>
          ) : area === "compare" ? (
            <article>
              <h2>Matched evaluation matrix</h2>
              <p>
                Only rows with an identical conditions hash are comparable. This
                includes suite digest, seed, target kind and runner budgets.
                Configuration hashes identify each target separately.
              </p>
              <div className="actions comparison-actions">
                <Link className="button secondary" to="/arena">
                  Open blind review <Icon name="compare" size={15} />
                </Link>
                <Link className="text-link" to="/runs/new">
                  Create compatible runs <Icon name="arrow" size={15} />
                </Link>
              </div>
              <div
                className="tablewrap"
                role="region"
                aria-label="Matched comparison matrix"
                tabIndex={0}
              >
                <table>
                  <thead>
                    <tr>
                      <th>Target</th>
                      <th>Suite / version</th>
                      <th>Seed</th>
                      <th>Passed / total</th>
                      <th>Provenance</th>
                      <th>Conditions hash</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <tr key={r.id}>
                        <td>
                          <Link to={"/runs/" + r.id}>
                            {r.result?.target_name || r.target_id}
                          </Link>
                        </td>
                        <td>
                          {r.result?.suite_slug || r.suite_slug} /{" "}
                          {r.result?.suite_version || "pending"}
                        </td>
                        <td>{r.seed}</td>
                        <td>
                          {r.result?.summary
                            ? r.result.summary.passed +
                              " / " +
                              r.result.summary.total
                            : "Not run"}
                        </td>
                        <td>{r.result?.trust || r.trust}</td>
                        <td>
                          <code>{r.conditions_hash || "pending"}</code>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {!rows.length && <p>No recorded runs yet.</p>}
            </article>
          ) : endpoint ? (
            <>
              <div className="registry-toolbar">
                <label className="search-field">
                  <Icon name="search" />
                  Search records
                  <input
                    value={search}
                    onChange={(e) => Search(e.target.value)}
                    placeholder="Search names, identifiers and content"
                  />
                </label>
                <label>
                  Sort by
                  <select value={sort} onChange={(e) => Sort(e.target.value)}>
                    <option value="recent">Most recent</option>
                    <option value="name">Name A–Z</option>
                    <option value="status">Status / provider</option>
                  </select>
                </label>
                <label>
                  Filter records
                  <select
                    value={filter}
                    onChange={(e) => Filter(e.target.value)}
                  >
                    <option value="all">All loaded records</option>
                    {Array.from(
                      new Set(
                        rows
                          .flatMap((x) => [
                            x.kind,
                            x.status,
                            x.provider,
                            x.trust,
                          ])
                          .filter(Boolean),
                      ),
                    ).map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="registry-caption">
                <span>{filteredRows.length} matching loaded records</span>
                <span>
                  Showing {Math.min(page, pages)} of {pages} · up to 500
                  returned by the local API
                </span>
              </div>
              {area === "artifacts" ? (
                <Suspense fallback={loading}>
                  <ArtifactInspector items={visibleRows} />
                </Suspense>
              ) : (
                <div
                  className={
                    "records " +
                    (["targets", "models", "agents", "apps"].includes(area)
                      ? "target-registry"
                      : "")
                  }
                >
                  {visibleRows.map((x) => (
                    <article key={x.id || x.slug}>
                      <span className="eyebrow">
                        {x.provider ||
                          x.version ||
                          x.trust ||
                          x.status ||
                          "PERSISTED RECORD"}
                      </span>
                      <h2>{x.target_name || x.name || x.title || x.id}</h2>
                      <code>{x.id || x.slug}</code>
                      <p>
                        {["runs", "reports"].includes(area)
                          ? `${x.suite_slug || x.result?.suite_slug || "Suite not recorded"} · v${x.suite_version || x.result?.suite_version || "—"} · Seed ${x.seed ?? "—"}`
                          : x.description || x.kind || x.mime || x.status}
                      </p>
                      {["targets", "models", "agents", "apps"].includes(
                        area,
                      ) && (
                        <>
                          <div className="target-configuration">
                            <Badge
                              tone={
                                x.provider?.startsWith("demo")
                                  ? "warning"
                                  : "neutral"
                              }
                            >
                              {x.kind === "application"
                                ? "HTTP contract target"
                                : x.provider?.startsWith("demo")
                                  ? "Fixture provider"
                                  : "Model endpoint"}
                            </Badge>
                            <Badge
                              tone={
                                diagnostics[x.id]
                                  ? diagnostics[x.id].ok
                                    ? "success"
                                    : "danger"
                                  : "neutral"
                              }
                            >
                              {diagnostics[x.id]
                                ? diagnostics[x.id].ok
                                  ? "Connection verified"
                                  : "Connection failed"
                                : "Not checked"}
                            </Badge>
                          </div>
                          <p className="endpoint-value">
                            {x.endpoint ||
                              (x.kind !== "application" &&
                              x.provider?.startsWith("demo")
                                ? "Deterministic fixture · no endpoint"
                                : "Endpoint not configured")}
                          </p>
                          <div className="capabilities">
                            <span>Declared</span>
                            {(x.capabilities || []).map((c: string) => (
                              <code key={c}>{c}</code>
                            ))}
                          </div>
                          <p className="subtle">
                            {history.find((r) => r.target_id === x.id)
                              ? "Last recorded activity: " +
                                history.find((r) => r.target_id === x.id)
                                  ?.status
                              : "No recorded evaluations"}
                          </p>
                          <Link
                            className="text-link"
                            to={"/runs/new?target=" + encodeURIComponent(x.id)}
                          >
                            Evaluate target <Icon name="arrow" size={14} />
                          </Link>
                        </>
                      )}
                      {["runs", "reports"].includes(area) && (
                        <div className="run-row-facts">
                          <Badge
                            tone={x.status === "failed" ? "danger" : "neutral"}
                          >
                            {x.status || "Not recorded"}
                          </Badge>
                          <span>
                            {x.result?.summary
                              ? x.result.summary.passed +
                                " / " +
                                x.result.summary.total +
                                " tasks passed"
                              : "No graded result"}
                          </span>
                          <Badge>
                            {x.trust || x.result?.trust || "self-reported"}
                          </Badge>
                        </div>
                      )}
                      {["runs", "reports"].includes(area) && (
                        <Link to={"/runs/" + x.id}>Inspect evidence →</Link>
                      )}
                      {["targets", "models", "agents", "apps"].includes(
                        area,
                      ) && (
                        <button disabled={busy} onClick={() => diagnose(x.id)}>
                          Test connection
                        </button>
                      )}
                      {area === "worlds" && (
                        <button
                          onClick={() =>
                            action("/worlds/" + x.id + "/replay", {})
                          }
                        >
                          Execute and replay
                        </button>
                      )}
                      {area === "suites" && (
                        <Link to={"/suites/" + x.slug + "@" + x.version}>
                          Inspect suite →
                        </Link>
                      )}
                      {area === "worlds" && (
                        <Link to={"/worlds/" + x.id}>Inspect world →</Link>
                      )}
                      {area === "suites" && (
                        <details>
                          <summary>Definition</summary>
                          <pre>{JSON.stringify(x, null, 2)}</pre>
                        </details>
                      )}
                    </article>
                  ))}
                </div>
              )}
              {filteredRows.length > 12 && (
                <nav className="pagination" aria-label="Record pages">
                  <button
                    className="secondary"
                    disabled={page <= 1}
                    onClick={() => Page(Math.max(1, page - 1))}
                  >
                    Previous
                  </button>
                  <span>
                    Page {Math.min(page, pages)} of {pages}
                  </span>
                  <button
                    className="secondary"
                    disabled={page >= pages}
                    onClick={() => Page(Math.min(pages, page + 1))}
                  >
                    Next
                  </button>
                </nav>
              )}
              {rows.length > 0 &&
                !filteredRows.length &&
                area !== "artifacts" && (
                  <article className="empty-state">
                    <Icon name="search" size={28} />
                    <h2>No matching records</h2>
                    <p>Try another query or clear your filters.</p>
                    <button
                      className="secondary"
                      onClick={() => {
                        Search("");
                        Filter("all");
                      }}
                    >
                      Clear filters
                    </button>
                  </article>
                )}
              {area === "artifacts" && (
                <article>
                  <h2>Ingest evidence</h2>
                  <label>
                    Choose a file
                    <input
                      type="file"
                      onChange={async (e) => {
                        let f = e.target.files?.[0];
                        if (!f) return;
                        if (f.size > 1048576) {
                          E("File exceeds 1 MiB upload limit");
                          return;
                        }
                        let r = new FileReader();
                        r.onload = () =>
                          action("/artifacts", {
                            filename: f.name,
                            content_base64: String(r.result).split(",")[1],
                            public: false,
                          });
                        r.readAsDataURL(f);
                      }}
                    />
                  </label>
                  <button
                    onClick={() => action("/artifacts/check-website", {})}
                  >
                    Check owned website fixture
                  </button>
                  <p>
                    Demonstration fixture only. Executes real browser checks and
                    records screenshot evidence; arbitrary HTML is never
                    embedded here.
                  </p>
                </article>
              )}
              {!rows.length && (
                <article>
                  <Icon name={area === "suites" ? "suite" : "box"} size={28} />
                  <h2>{data ? "No records yet" : "Loading workspace…"}</h2>
                  <p>
                    Persisted evidence appears here after you create a
                    configuration or execute a run.
                  </p>
                  <Link
                    className="button secondary"
                    to={
                      area === "runs" || area === "reports"
                        ? "/runs/new"
                        : area === "suites"
                          ? "/suites/new"
                          : "/models/new"
                    }
                  >
                    {area === "runs" || area === "reports"
                      ? "Launch an evaluation"
                      : area === "suites"
                        ? "Create a suite"
                        : "Register a target"}{" "}
                    <Icon name="arrow" size={15} />
                  </Link>
                </article>
              )}
            </>
          ) : (
            <article>
              <h2>
                {!["admin", "docs", "methodology", "privacy", "terms"].includes(
                  area,
                )
                  ? "Page not found"
                  : area === "admin"
                    ? "Operator trust controls"
                    : "Evidence you can reproduce"}
              </h2>
              {!["admin", "docs", "methodology", "privacy", "terms"].includes(
                area,
              ) && (
                <Link className="button" to="/dashboard">
                  Return to laboratory
                </Link>
              )}
              <p>
                Praxis evaluates versioned tasks using independent assertions.
                Local execution is self reported, and deterministic providers
                are labeled demo. Neither qualifies for official objective
                rankings.
              </p>
              <h3>Run locally</h3>
              <pre>
                praxis suites list{"\n"}praxis run --help{"\n"}praxis validate
                --help
              </pre>
              <p>
                Inference uses your endpoint and compute. Untrusted code
                requires isolation; it must never execute on the application
                origin. HTML artifacts are displayed as inert source.
              </p>
              {area === "docs" && (
                <section id="recovery">
                  <h3>Recovery checklist</h3>
                  <p>
                    Stop the runtime. Use the actual database path with
                    scripts/backup_workspace.py to create and verify a private
                    snapshot. Restore into a new directory, then inspect account
                    ownership, recorded runs and artifact hashes. Restart the
                    restored installation for a second read-only check. Keep the
                    source untouched. The settings recovery section provides the
                    exact CLI commands; no browser backup operation is
                    implemented.
                  </p>
                  <Link className="button secondary" to="/settings#recovery">
                    Backup & restore instructions
                  </Link>
                </section>
              )}
              <h3>Privacy and terms</h3>
              <p>
                Local workspace records remain on this computer. Only submit
                artifacts you have permission to share. No hosted availability
                or model accuracy is guaranteed. Deployment and paid inference
                require explicit operator configuration.
              </p>
            </article>
          )}
          {out && (
            <article aria-live="polite">
              <h2>Operation result</h2>
              <Badge tone={out.ok === false ? "danger" : "neutral"}>
                {out.ok === false
                  ? "Diagnostic reported a failure"
                  : "Response recorded"}
              </Badge>
              <details>
                <summary>Response evidence</summary>
                <CodeBlock value={out} />
              </details>
            </article>
          )}
        </>
      )}
    </WorkspaceShell>
  );
}
const root = document.getElementById("root");
if (root)
  createRoot(root).render(
    <BrowserRouter>
      <App />
    </BrowserRouter>,
  );
