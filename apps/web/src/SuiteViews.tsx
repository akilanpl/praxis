import { useEffect, useState } from "react";
import { Badge, CodeBlock, Icon } from "./ui";
import { Link } from "react-router-dom";

export function suiteIssues(value: any): string[] {
  if (!value || typeof value !== "object" || Array.isArray(value))
    return ["Definition must be a JSON object."];
  const issues: string[] = [];
  if (typeof value.slug !== "string" || !/^[a-z0-9-]{1,100}$/.test(value.slug))
    issues.push("Use a lowercase suite slug with letters, digits and hyphens.");
  if (!value.title || typeof value.title !== "string")
    issues.push("Give this suite a title.");
  if (!value.version || typeof value.version !== "string")
    issues.push("An explicit version is required.");
  if (!Array.isArray(value.tasks) || !value.tasks.length)
    issues.push("Add at least one scenario.");
  if (
    Array.isArray(value.tasks) &&
    value.tasks.some(
      (task: any) =>
        !task ||
        typeof task !== "object" ||
        Array.isArray(task) ||
        typeof task.id !== "string",
    )
  )
    issues.push(
      "Every scenario must be a JSON object with a string identifier.",
    );
  if (
    Array.isArray(value.tasks) &&
    value.tasks.some(
      (task: any) =>
        task?.prompt !== undefined && typeof task.prompt !== "string",
    )
  )
    issues.push("All scenario prompts must be text.");
  if (
    Array.isArray(value.tasks) &&
    new Set(value.tasks.map((t: any) => t?.id)).size !== value.tasks.length
  )
    issues.push("Scenario identifiers must be unique.");
  return issues;
}
function JsonField({
  label,
  value,
  onApply,
  array = false,
}: {
  label: string;
  value: any;
  onApply: (v: any) => void;
  array?: boolean;
}) {
  const serialized = JSON.stringify(value ?? (array ? [] : {}), null, 2);
  const [text, T] = useState(serialized),
    [error, E] = useState("");
  useEffect(() => {
    T(serialized);
    E("");
  }, [serialized]);
  return (
    <div className="json-field">
      <label>
        {label}
        <textarea
          aria-label={label}
          spellCheck={false}
          rows={8}
          value={text}
          onChange={(e) => T(e.target.value)}
        />
      </label>
      {error && (
        <p role="alert" className="inline-error">
          {error}
        </p>
      )}
      <button
        type="button"
        className="secondary"
        onClick={() => {
          try {
            const parsed = JSON.parse(text);
            if (
              array
                ? !Array.isArray(parsed)
                : !parsed || typeof parsed !== "object" || Array.isArray(parsed)
            )
              throw Error();
            onApply(parsed);
            E("");
          } catch {
            E(
              array
                ? "Enter a JSON array of assertions."
                : "Enter a JSON schema object.",
            );
          }
        }}
      >
        Apply {array ? "assertions" : "schema"}
      </button>
    </div>
  );
}
export default function SuiteEditor({
  initial,
  onSave,
  busy,
  onError,
}: {
  initial?: any;
  onSave: (value: any) => Promise<void>;
  busy: boolean;
  onError: (message: string) => void;
}) {
  const blank = {
    schema_version: "praxis.suite.v1",
    slug: "my-suite",
    title: "",
    version: "1.0.0",
    tasks: [],
  };
  const [text, T] = useState(JSON.stringify(initial || blank, null, 2)),
    [selected, S] = useState(0),
    [mode, M] = useState("structured");
  const initialText = initial ? JSON.stringify(initial, null, 2) : "";
  useEffect(() => {
    if (initialText) {
      T(initialText);
      S(0);
    }
  }, [initialText]);
  let definition: any,
    syntax = "";
  try {
    definition = JSON.parse(text);
  } catch {
    syntax = "Enter valid JSON";
  }
  const structurable =
    typeof definition?.slug === "string" &&
    typeof definition?.title === "string" &&
    typeof definition?.version === "string" &&
    Array.isArray(definition?.tasks) &&
    definition.tasks.every(
      (task: any) =>
        task &&
        typeof task === "object" &&
        !Array.isArray(task) &&
        typeof task.id === "string" &&
        (task.prompt === undefined || typeof task.prompt === "string"),
    );
  const issues = syntax
      ? ["Definition is incomplete or malformed JSON."]
      : suiteIssues(definition),
    tasks = Array.isArray(definition?.tasks) ? definition.tasks : [],
    task = structurable ? tasks[selected] : undefined;
  function edit(key: string, value: any) {
    T(JSON.stringify({ ...definition, [key]: value }, null, 2));
  }
  function editTask(key: string, value: any) {
    edit(
      "tasks",
      tasks.map((t: any, i: number) =>
        i === selected ? { ...t, [key]: value } : t,
      ),
    );
  }
  return (
    <form
      className="suite-editor"
      aria-busy={busy}
      onSubmit={async (e) => {
        e.preventDefault();
        try {
          await onSave(JSON.parse(text));
        } catch {
          onError("Enter valid JSON");
        }
      }}
    >
      <div className="section-heading">
        <div>
          <h2>
            {initial
              ? "Create an immutable revision"
              : "Build an evaluation contract"}
          </h2>
          <p>Versioned scenarios, explicit assertions, inspectable fixtures.</p>
        </div>
        <Badge>New version</Badge>
      </div>
      <div
        className="editor-switch"
        role="group"
        aria-label="Suite editing mode"
      >
        <button
          type="button"
          className={mode === "structured" ? "selected secondary" : "ghost"}
          onClick={() => M("structured")}
        >
          Structured editor
        </button>
        <button
          type="button"
          className={mode === "json" ? "selected secondary" : "ghost"}
          onClick={() => M("json")}
        >
          Full JSON
        </button>
      </div>
      {mode === "structured" && structurable && (
        <>
          <div className="form-grid">
            <label>
              Suite title
              <input
                value={definition.title || ""}
                onChange={(e) => edit("title", e.target.value)}
                maxLength={200}
              />
            </label>
            <label>
              Suite slug
              <input
                value={definition.slug || ""}
                onChange={(e) => edit("slug", e.target.value)}
                maxLength={100}
              />
            </label>
            <label>
              Version
              <input
                value={definition.version || ""}
                onChange={(e) => edit("version", e.target.value)}
                maxLength={40}
              />
            </label>
          </div>
          <div className="editor-workspace">
            <div className="scenario-list">
              <div className="section-label">
                SCENARIOS <span>{tasks.length}</span>
              </div>
              {tasks.map((t: any, i: number) => (
                <button
                  type="button"
                  className={i === selected ? "selected" : ""}
                  key={i}
                  onClick={() => S(i)}
                >
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  {t.id || "Untitled scenario"}
                </button>
              ))}
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  edit("tasks", [
                    ...tasks,
                    {
                      id: "scenario-" + (tasks.length + 1),
                      prompt: "",
                      category: "correctness",
                      output_schema: { type: "object" },
                      assertions: [],
                      passing_fixture: {},
                      failing_fixture: {},
                    },
                  ]);
                  S(tasks.length);
                }}
              >
                + Add scenario
              </button>
            </div>
            <div className="scenario-editor">
              {task ? (
                <>
                  <label>
                    Scenario identifier
                    <input
                      value={task.id || ""}
                      onChange={(e) => editTask("id", e.target.value)}
                    />
                  </label>
                  <label>
                    Scenario prompt
                    <textarea
                      rows={4}
                      value={task.prompt || ""}
                      onChange={(e) => editTask("prompt", e.target.value)}
                    />
                  </label>
                  <JsonField
                    label="Output schema"
                    value={task.output_schema}
                    onApply={(value) => editTask("output_schema", value)}
                  />
                  <JsonField
                    label="Assertions JSON"
                    value={task.assertions}
                    array
                    onApply={(value) => editTask("assertions", value)}
                  />
                  <details>
                    <summary>Fixture inspection</summary>
                    <CodeBlock
                      label="Passing fixture · deterministic reference"
                      value={task.passing_fixture}
                    />
                    <CodeBlock
                      label="Failing fixture · negative reference"
                      value={task.failing_fixture}
                    />
                    <p>
                      Edit fixture values in the complete definition below.
                      Fixtures are not hidden benchmarks or model inference.
                    </p>
                  </details>
                </>
              ) : (
                <div className="empty-state compact">
                  <Icon name="suite" size={28} />
                  <h3>Start with one explicit task</h3>
                  <p>
                    Add a scenario, define its output schema, and write
                    assertions that can fail.
                  </p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
      <details
        className="definition-editor"
        open={mode === "json" || !!syntax || !structurable}
      >
        <summary>Complete versioned definition</summary>
        <label>
          Versioned suite JSON
          <textarea
            rows={20}
            spellCheck={false}
            value={text}
            onChange={(e) => T(e.target.value)}
          />
        </label>
      </details>
      <div
        className={"validation-note " + (issues.length ? "warning" : "success")}
        role="status"
      >
        <strong>
          {issues.length
            ? "Definition needs attention"
            : "Ready for runtime validation"}
        </strong>
        {issues.length ? (
          <ul>
            {issues.map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        ) : (
          <p>
            The local API performs authoritative schema and assertion-language
            validation on save.
          </p>
        )}
      </div>
      <div className="form-footer">
        <p>
          Existing versions stay immutable. Saving registers a new suite/version
          pair.
        </p>
        <button disabled={busy} type="submit">
          {busy ? "Saving…" : "Save configuration"}
          <Icon name="arrow" size={16} />
        </button>
      </div>
    </form>
  );
}
export function SuiteExplorer({ suite }: { suite: any }) {
  const [selected, S] = useState(0);
  const tasks = suite.tasks || [],
    task = tasks[selected];
  return (
    <div className="suite-explorer">
      <div className="editor-workspace">
        <nav className="scenario-list" aria-label="Suite scenarios">
          <div className="section-label">
            SCENARIOS <span>{tasks.length}</span>
          </div>
          {tasks.map((t: any, i: number) => (
            <button
              className={i === selected ? "selected" : ""}
              key={t.id || i}
              onClick={() => S(i)}
            >
              <span>{String(i + 1).padStart(2, "0")}</span>
              {t.id}
            </button>
          ))}
        </nav>
        <div className="scenario-editor">
          {task ? (
            <>
              <div className="section-heading">
                <h3>{task.id}</h3>
                <Badge>{task.category || "Contract"}</Badge>
              </div>
              <p>{task.prompt}</p>
              <CodeBlock label="Output schema" value={task.output_schema} />
              <CodeBlock
                label="Executable assertions"
                value={task.assertions}
              />
              {task.api_request && (
                <CodeBlock
                  label="HTTP request contract"
                  value={task.api_request}
                />
              )}
              <details>
                <summary>Reference fixtures</summary>
                <CodeBlock
                  label="Passing fixture"
                  value={task.passing_fixture}
                />
                <CodeBlock
                  label="Failing fixture"
                  value={task.failing_fixture}
                />
              </details>
              {task.environment && (
                <CodeBlock
                  label="Bounded agent environment"
                  value={task.environment}
                />
              )}
            </>
          ) : (
            <p>No scenario definitions recorded.</p>
          )}
        </div>
      </div>
      <details>
        <summary>Complete immutable definition</summary>
        <CodeBlock value={suite} />
      </details>
      <Link
        className="button secondary"
        to={
          "/suites/new?source=" +
          encodeURIComponent(suite.slug + "@" + suite.version)
        }
      >
        Create revision <Icon name="arrow" size={15} />
      </Link>
    </div>
  );
}
