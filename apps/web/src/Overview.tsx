import { Link } from "react-router-dom";
import { Badge, Icon } from "./ui";
export default function Overview({
  data,
  targets,
  suites,
  runs,
}: {
  data: any;
  targets: any[];
  suites: any[];
  runs: any[];
}) {
  const states = runs.reduce((a: Record<string, number>, r) => {
    a[r.status || "unknown"] = (a[r.status || "unknown"] || 0) + 1;
    return a;
  }, {});
  const failures = runs
    .filter(
      (r) =>
        r.status === "failed" ||
        r.status === "interrupted" ||
        (r.result?.summary?.failed ?? 0) > 0,
    )
    .slice(0, 4);
  const activity = Object.entries(
    runs.reduce((a: Record<string, number>, r) => {
      const key = r.suite_slug + " @ " + r.suite_version;
      a[key] = (a[key] || 0) + 1;
      return a;
    }, {}),
  ).slice(0, 5);
  return (
    <>
      <div className="overview-intro">
        <div>
          <p className="page-description">
            A clear view of your evaluation workspace.
            <br />
            Every result links back to the evidence behind it.
          </p>
        </div>
        <div className="actions">
          <Link className="button secondary" to="/targets">
            Manage targets
          </Link>
          <Link className="button" to="/runs/new">
            <Icon name="play" size={15} />
            New evaluation
          </Link>
        </div>
      </div>
      <section className="metric-grid" aria-label="Persisted workspace summary">
        {[
          ["Evaluations", data?.runs ?? 0, "Recorded by the local API", "play"],
          [
            "Registered targets",
            data?.targets ?? targets.length,
            "Models, agents & HTTP apps",
            "target",
          ],
          [
            "Available suites",
            suites.length,
            "Public and private versions",
            "suite",
          ],
          [
            "Stored artifacts",
            data?.artifacts ?? 0,
            "Outputs and uploaded evidence",
            "box",
          ],
        ].map(([name, value, note, icon]) => (
          <article className="metric-card" key={String(name)}>
            <div>
              <span>{name}</span>
              <Icon name={String(icon)} size={17} />
            </div>
            <strong>{value}</strong>
            <small>{note}</small>
          </article>
        ))}
      </section>
      <div className="overview-grid">
        <article className="recent-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">EXECUTION HISTORY</span>
              <h2>Recent runs</h2>
            </div>
            <Link to="/runs">
              View all <Icon name="arrow" size={14} />
            </Link>
          </div>
          {data?.recent_runs?.length ? (
            <div className="recent-runs">
              {data.recent_runs.map((r: any) => (
                <Link key={r.id} to={"/runs/" + r.id}>
                  <span className="run-glyph">
                    <Icon name="play" size={16} />
                  </span>
                  <span className="recent-run-name">
                    <strong>{r.target_name || r.target_id}</strong>
                    <small>
                      {r.suite_slug} <span>·</span>{" "}
                      {r.result?.summary
                        ? r.result.summary.passed +
                          " / " +
                          r.result.summary.total +
                          " tasks passed"
                        : "Inspect execution evidence"}
                    </small>
                  </span>
                  <Badge
                    tone={
                      r.status === "failed"
                        ? "danger"
                        : r.status === "running"
                          ? "warning"
                          : "neutral"
                    }
                  >
                    {r.status}
                  </Badge>
                  <Icon name="chevron" size={15} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-state compact">
              <Icon name="play" size={28} />
              <h3>Your first evaluation starts here</h3>
              <p>
                Connect an endpoint or explicitly choose a deterministic
                fixture, then run a versioned suite.
              </p>
              <Link className="text-link" to="/runs/new">
                Launch evaluation <Icon name="arrow" size={14} />
              </Link>
            </div>
          )}
        </article>
        <article className="outcomes-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">LOADED RUN RECORDS</span>
              <h2>Execution outcomes</h2>
            </div>
            <Icon name="grid" />
          </div>
          {runs.length ? (
            <>
              <div
                className="outcome-bar"
                role="group"
                aria-label="Execution status distribution"
              >
                {Object.entries(states).map(([key, count]) => (
                  <span
                    key={key}
                    className={"outcome-segment " + key}
                    style={{ flex: Number(count) }}
                    title={key + ": " + count}
                  />
                ))}
              </div>
              <dl className="outcome-legend">
                {Object.entries(states).map(([key, count]) => (
                  <div key={key}>
                    <dt>
                      <span className={"legend-dot " + key} />
                      {key}
                    </dt>
                    <dd>{String(count)}</dd>
                  </div>
                ))}
              </dl>
              <p className="subtle">
                Execution completion is separate from task success. Distribution
                covers {runs.length} loaded records.
              </p>
            </>
          ) : (
            <div className="empty-state compact">
              <Icon name="clock" size={26} />
              <h3>No execution history yet</h3>
              <p>No percentages are inferred before a run exists.</p>
            </div>
          )}
        </article>
        <article>
          <div className="section-heading">
            <div>
              <span className="eyebrow">REGISTRY</span>
              <h2>Evaluation targets</h2>
            </div>
            <Link to="/targets">
              Manage <Icon name="arrow" size={14} />
            </Link>
          </div>
          <div className="target-summary">
            {[
              ["model", "Models", "models"],
              ["agent", "Tool agents", "agents"],
              ["application", "HTTP applications", "apps"],
            ].map(([kind, label, path]) => (
              <Link to={"/" + path} key={kind}>
                <span className="target-kind-icon">
                  <Icon
                    name={
                      kind === "model"
                        ? "target"
                        : kind === "agent"
                          ? "box"
                          : "compare"
                    }
                  />
                </span>
                <span>{label}</span>
                <strong>{targets.filter((t) => t.kind === kind).length}</strong>
                <Icon name="chevron" size={14} />
              </Link>
            ))}
          </div>
          <p className="subtle">
            A registered endpoint is not a verified connection. Run diagnostics
            from the registry.
          </p>
        </article>
        <article>
          <div className="section-heading">
            <div>
              <span className="eyebrow">CONTRACT ACTIVITY</span>
              <h2>Suite activity</h2>
            </div>
            <Link to="/suites">
              Explore <Icon name="arrow" size={14} />
            </Link>
          </div>
          {activity.length ? (
            <dl className="activity-list">
              {activity.map(([suite, count]) => (
                <div key={suite}>
                  <dt>{suite}</dt>
                  <dd>{String(count)} run(s)</dd>
                </div>
              ))}
            </dl>
          ) : (
            <div className="empty-state compact">
              <h3>No suite activity recorded</h3>
              <p>
                {suites.length} available suite versions. Inspect their
                scenarios before you launch.
              </p>
              <Link className="text-link" to="/suites">
                Explore evaluation suites <Icon name="arrow" size={14} />
              </Link>
            </div>
          )}
        </article>
      </div>
      {failures.length > 0 && (
        <article className="failure-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">NEEDS INSPECTION</span>
              <h2>Recent failures</h2>
            </div>
            <Badge tone="danger">{failures.length} shown</Badge>
          </div>
          {failures.map((r) => (
            <Link key={r.id} to={"/runs/" + r.id} className="failure-row">
              <span>
                <strong>{r.target_name || r.target_id}</strong>
                <small>
                  {r.result?.summary?.failed ?? "—"} failed tasks ·{" "}
                  {r.error || r.suite_slug}
                </small>
              </span>
              <span>
                Inspect failure <Icon name="arrow" size={14} />
              </span>
            </Link>
          ))}
        </article>
      )}
      <article className="getting-started">
        <div>
          <span className="eyebrow">START WITH EVIDENCE</span>
          <h2>Start with evidence</h2>
          <p>
            Register a demo target to verify the pipeline, or connect your own
            endpoint for real inference. Public fixtures establish
            infrastructure behavior, not model capability.
          </p>
        </div>
        <Link className="button secondary" to="/models/new">
          Connect a target <Icon name="arrow" size={16} />
        </Link>
      </article>
    </>
  );
}
