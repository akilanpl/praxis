import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, CodeBlock, Icon, Modal } from "./ui";

export function downloadFile(text: string, name: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function printableReport(run: any) {
  const escape = (value: any) =>
    String(
      typeof value === "string"
        ? value
        : (JSON.stringify(value, null, 2) ?? "Not recorded"),
    ).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c]!,
    );
  const result = run.result || {};
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Praxis evaluation report</title><style>body{max-width:1100px;margin:48px auto;padding:0 24px;font:15px/1.6 system-ui;color:#19221b}h1{font-size:36px}h2{margin-top:36px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f5f0;padding:16px}table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{border:1px solid #d2d9d2;padding:10px;text-align:left;overflow-wrap:anywhere}small{color:#465746}@media print{body{margin:0}section{break-inside:avoid}}</style><body><small>PRAXIS / EVALUATION EVIDENCE</small><h1>${escape(run.target_name || result.target_name || run.id)}</h1><p>Execution: ${escape(run.status)} · Provenance: ${escape(run.trust || result.trust)} · Suite: ${escape(run.suite_slug || result.suite_slug)} @ ${escape(run.suite_version || result.suite_version)} · Seed ${escape(run.seed)}</p><h2>Task outcome summary</h2><pre>${escape(result.summary || "No graded result recorded")}</pre><p>Execution completion does not imply assertion success. Unexecuted scenarios remain in the denominator.</p>${(result.tasks || []).map((t: any) => `<section><h2>${escape(t.id)} · ${t.passed ? "Pass" : "Fail"}</h2><table><thead><tr><th>Assertion</th><th>Result</th><th>Expected</th><th>Observed</th></tr></thead><tbody>${(t.assertions || []).map((a: any) => `<tr><td>${escape(a.name || a.type)}</td><td>${a.passed ? "Pass" : "Fail"}</td><td>${escape(a.expected)}</td><td>${escape(a.actual)}</td></tr>`).join("")}</tbody></table><h3>Output and execution evidence</h3><pre>${escape(t)}</pre></section>`).join("")}<h2>Unexecuted scenarios</h2><pre>${escape(result.not_run_tasks || [])}</pre><h2>Reproducibility manifest</h2><pre>${escape(run)}</pre></body></html>`;
}
export default function RunInspector({
  run,
  busy,
  onCancel,
  onExport,
}: {
  run: any;
  busy: boolean;
  onCancel: () => Promise<any>;
  onExport: () => Promise<void>;
}) {
  const [failedOnly, Failed] = useState(false),
    [confirm, Confirm] = useState(false);
  const result = run.result || {},
    tasks = result.tasks || [],
    summary = result.summary || {};
  const passed = summary.passed ?? 0,
    total = summary.total ?? tasks.length;
  const active = ["queued", "running"].includes(run.status);
  return (
    <>
      <div className="run-banner">
        <div>
          <Badge tone={active ? "warning" : "neutral"}>{run.status}</Badge>
          <Badge tone={run.trust === "demo" ? "warning" : "neutral"}>
            {run.trust || result.trust || "self-reported"}
          </Badge>
          <p className="subtle">
            {run.target_name || result.target_name || run.target_id}{" "}
            <span> / </span> {run.suite_slug || result.suite_slug}{" "}
            <code>
              v{run.suite_version || result.suite_version || "pending"}
            </code>
          </p>
        </div>
        <div className="actions">
          <button
            className="secondary"
            disabled={!active || busy}
            title={
              active ? "Request bounded cancellation" : "Run already finished"
            }
            onClick={() => Confirm(true)}
          >
            Cancel run
          </button>
          <button className="secondary" onClick={onExport}>
            <Icon name="file" />
            Export evidence
          </button>
          <button
            className="secondary"
            onClick={() =>
              downloadFile(
                printableReport(run),
                "praxis-report.html",
                "text/html",
              )
            }
          >
            Export HTML
          </button>
          <button className="secondary" onClick={() => window.print()}>
            Print report
          </button>
        </div>
      </div>
      <section className="run-summary panel">
        <div className="run-summary-primary">
          <span className="eyebrow">TASK CONTRACTS</span>
          <div className="score">
            <strong>{passed}</strong>
            <span>/ {total}</span>
            <Badge tone={passed === total && total > 0 ? "success" : "danger"}>
              {total
                ? Math.round((100 * passed) / total) + "% passed"
                : "Not graded"}
            </Badge>
          </div>
          <h2 className="execution-heading">
            {run.status} · {run.trust || result.trust || "self-reported"}
          </h2>
          <p>Execution status and assertion results are separate signals.</p>
        </div>
        <dl className="summary-facts">
          <div>
            <dt>Executed</dt>
            <dd>{summary.executed ?? tasks.length}</dd>
          </div>
          <div>
            <dt>Assertions passed</dt>
            <dd>
              {summary.assertions_passed ?? "—"}{" "}
              <span>/ {summary.assertions_total ?? "—"}</span>
            </dd>
          </div>
          <div>
            <dt>Not run</dt>
            <dd>{summary.not_run ?? result.not_run_tasks?.length ?? 0}</dd>
          </div>
          <div>
            <dt>Seed</dt>
            <dd>{run.seed ?? "—"}</dd>
          </div>
          <div>
            <dt>Median latency</dt>
            <dd>
              {summary.latency_p50_ms !== undefined
                ? Math.round(summary.latency_p50_ms) + " ms"
                : "Not recorded"}
            </dd>
          </div>
          <div>
            <dt>Evidence</dt>
            <dd className="mono">
              {result.evidence_hash
                ? result.evidence_hash.slice(0, 12) + "…"
                : "Pending"}
            </dd>
          </div>
        </dl>
      </section>
      {run.error && (
        <div className="error" role="status">
          {run.error}
        </div>
      )}
      {result.not_run_tasks?.length > 0 && (
        <article className="warning-panel">
          <h2>Unexecuted scenarios</h2>
          <p>These remain in the task denominator.</p>
          <CodeBlock value={result.not_run_tasks} />
        </article>
      )}
      <div className="inspection-layout">
        <nav className="task-nav" aria-label="Task navigation">
          <div className="section-label">
            SCENARIOS <span>{tasks.length}</span>
          </div>
          <button
            className={"filter-toggle " + (failedOnly ? "selected" : "")}
            aria-pressed={failedOnly}
            onClick={() => Failed(!failedOnly)}
          >
            Failed tasks only
          </button>
          {tasks
            .filter((t: any) => !failedOnly || !t.passed)
            .map((t: any) => (
              <a key={t.id} href={"#task-" + tasks.indexOf(t)}>
                <span
                  className={
                    "task-indicator " + (t.passed ? "success" : "danger")
                  }
                >
                  {t.passed ? "✓" : "×"}
                </span>
                <span>{t.id}</span>
                <small>{t.assertions?.length ?? 0}</small>
              </a>
            ))}
          {!tasks.length && (
            <p>Task evidence appears as execution is persisted.</p>
          )}
        </nav>
        <div className="task-content">
          {tasks
            .filter((t: any) => !failedOnly || !t.passed)
            .map((t: any) => (
              <article
                className={
                  "task-card " + (t.passed ? "task-passed" : "task-failed")
                }
                key={t.id}
                id={"task-" + tasks.indexOf(t)}
              >
                <div className="task-heading">
                  <div>
                    <span className="eyebrow">
                      SCENARIO {String(tasks.indexOf(t) + 1).padStart(2, "0")}
                    </span>
                    <h2>{t.id}</h2>
                  </div>
                  <Badge tone={t.passed ? "success" : "danger"}>
                    {t.passed ? "Passed" : "Failed"}
                  </Badge>
                </div>
                <div className="task-meta">
                  <span>
                    <Icon name="clock" size={14} />
                    {t.latency_ms ?? "—"} ms
                  </span>
                  <span>{t.attempts ?? "—"} attempt(s)</span>
                  <span>
                    {t.usage?.completion_tokens !== undefined
                      ? t.usage.completion_tokens + " completion tokens"
                      : "Usage not recorded"}
                  </span>
                </div>
                {t.error && (
                  <div className="task-error">
                    <strong>{t.error.category || "Execution error"}</strong>
                    <p>{t.error.message || JSON.stringify(t.error)}</p>
                  </div>
                )}
                <div
                  className="tablewrap assertion-table"
                  role="region"
                  aria-label={"Assertion results for " + t.id}
                  tabIndex={0}
                >
                  <table>
                    <thead>
                      <tr>
                        <th>Assertion</th>
                        <th>Result</th>
                        <th>Expected</th>
                        <th>Observed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {t.assertions?.map((a: any, i: number) => (
                        <tr
                          key={i}
                          className={!a.passed ? "assertion-failed" : ""}
                        >
                          <td>{a.name || a.type}</td>
                          <td>
                            <Badge tone={a.passed ? "success" : "danger"}>
                              {a.passed ? "Pass" : "Fail"}
                            </Badge>
                          </td>
                          <td>
                            <code>{JSON.stringify(a.expected)}</code>
                          </td>
                          <td>
                            {JSON.stringify(a.actual)?.length > 240 ? (
                              <details>
                                <summary>Inspect observed output</summary>
                                <CodeBlock value={a.actual} />
                              </details>
                            ) : (
                              <code>{JSON.stringify(a.actual)}</code>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {!t.assertions?.length && (
                  <p>
                    No assertions recorded. This does not establish task
                    success.
                  </p>
                )}
                <details className="evidence-disclosure">
                  <summary>Prompt and output</summary>
                  <CodeBlock label="Task prompt" value={t.prompt} />
                  <CodeBlock
                    label="Raw output / HTTP response"
                    value={t.output}
                  />
                </details>
                {!!t.tool_trace?.length && (
                  <details className="evidence-disclosure">
                    <summary>
                      Tool trace · {t.tool_trace.length} recorded events
                    </summary>
                    <CodeBlock
                      label="Executed actions and state evidence"
                      value={t.tool_trace}
                    />
                  </details>
                )}
                <details className="evidence-disclosure">
                  <summary>Timing, usage & artifact provenance</summary>
                  <CodeBlock
                    value={{
                      latency_ms: t.latency_ms,
                      attempts: t.attempts,
                      usage: t.usage,
                      provider_metadata: t.provider_metadata,
                      artifact: t.artifact,
                    }}
                  />
                </details>
              </article>
            ))}
          {failedOnly && !tasks.some((t: any) => !t.passed) && (
            <article className="empty-state">
              <Icon name="check" size={28} />
              <h2>No failed executed tasks</h2>
              <p>Review the denominator above for unexecuted scenarios.</p>
            </article>
          )}
        </div>
      </div>
      <article className="timeline">
        <div className="section-heading">
          <h2>Execution timeline</h2>
          <Link to={"/artifacts?record=" + encodeURIComponent(run.id)}>
            Inspect run artifacts <Icon name="arrow" size={15} />
          </Link>
        </div>
        {(result.events || run.events || []).map((e: any, i: number) => (
          <details key={i}>
            <summary>
              <span className="timeline-index">
                {String(i + 1).padStart(2, "0")}
              </span>
              <code>{e.type || e.event || "event"}</code>
              <span>{e.task_id || "Run"}</span>
            </summary>
            <CodeBlock value={e} />
          </details>
        ))}
        <details className="evidence-disclosure">
          <summary>Reproducibility manifest</summary>
          <CodeBlock value={run} />
        </details>
      </article>
      {confirm && (
        <Modal title="Cancel this evaluation?" onDismiss={() => Confirm(false)}>
          <p>
            Cancellation is requested at the runtime's next safe boundary.
            Recorded evidence remains available; completed HTTP mutations cannot
            be undone.
          </p>
          <div className="actions">
            <button className="secondary" onClick={() => Confirm(false)}>
              Keep running
            </button>
            <button
              className="danger-button"
              disabled={busy}
              onClick={async () => {
                await onCancel();
                Confirm(false);
              }}
            >
              Confirm cancellation
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
