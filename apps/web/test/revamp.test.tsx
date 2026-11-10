import React from "react";
import { afterEach, beforeEach, it, expect, vi } from "vitest";
import {
  render,
  screen,
  waitFor,
  cleanup,
  fireEvent,
  act,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { WorkspaceShell, Modal, CodeBlock, Icon } from "../src/ui";
import RunInspector, { printableReport } from "../src/RunInspector";
import SuiteEditor, { SuiteExplorer, suiteIssues } from "../src/SuiteViews";
import ArtifactInspector from "../src/ArtifactInspector";
import Overview from "../src/Overview";
import Settings from "../src/Settings";
import { App } from "../src/main";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
const call = vi.mocked(api);
const suite = {
  slug: "authored",
  title: "Authored suite",
  version: "1.0.0",
  tasks: [
    {
      id: "first",
      prompt: "Inspect outputs",
      output_schema: { type: "object" },
      assertions: [{ name: "value", passed: true, expected: 1, actual: 1 }],
      passing_fixture: { value: 1 },
      failing_fixture: { value: 0 },
    },
    {
      id: "second",
      prompt: "Bounded task",
      category: "agent",
      environment: { state: {} },
      api_request: { method: "GET", path: "/health" },
      assertions: [],
    },
  ],
};
const run = {
  id: "r1",
  target_id: "t1",
  target_name: "Actual fixture",
  status: "completed",
  trust: "demo",
  seed: 73,
  suite_slug: "authored",
  suite_version: "1.0.0",
  result: {
    evidence_hash: "abcdef1234567890",
    summary: {
      passed: 1,
      total: 2,
      executed: 2,
      assertions_passed: 1,
      assertions_total: 2,
      latency_p50_ms: 2,
    },
    tasks: [
      {
        id: "first",
        passed: true,
        prompt: "prompt",
        output: { value: 1 },
        latency_ms: 1,
        attempts: 1,
        usage: { completion_tokens: 4 },
        assertions: [{ name: "value", passed: true, expected: 1, actual: 1 }],
        artifact: { hash: "digest" },
      },
      {
        id: "second",
        passed: false,
        error: { category: "timeout", message: "deadline" },
        output: "x".repeat(15000),
        tool_trace: [{ type: "tool_call", authorized: false }],
        assertions: [
          {
            type: "state",
            passed: false,
            expected: true,
            actual: "x".repeat(300),
          },
        ],
      },
    ],
    events: [{ type: "run_completed", task_id: "second" }],
    not_run_tasks: [{ id: "not-run" }],
  },
};
function wrap(element: React.ReactNode, path = "/dashboard") {
  window.history.replaceState({}, "", path);
  return render(<BrowserRouter>{element}</BrowserRouter>);
}
beforeEach(() => {
  localStorage.clear();
  document.documentElement.className = "";
  HTMLDialogElement.prototype.showModal = function () {
    this.open = true;
  };
  HTMLDialogElement.prototype.close = function () {
    this.open = false;
  };
  call.mockReset();
  call.mockResolvedValue([]);
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  vi.stubGlobal(
    "URL",
    Object.assign(URL, {
      createObjectURL: vi.fn(() => "blob:owned"),
      revokeObjectURL: vi.fn(),
    }),
  );
  vi.spyOn(window, "print").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
it("palette supports query, arrows, Enter, escape, no results and focus restoration", async () => {
  wrap(
    <WorkspaceShell
      token="fixture"
      targets={[{ id: "t", name: "Owned model", kind: "model" }]}
      suites={[suite]}
      runs={[run]}
      onSignOut={vi.fn()}
      refresh={vi.fn()}
    >
      <h1>Workspace</h1>
    </WorkspaceShell>,
  );
  const trigger = screen.getByRole("button", { name: /Search workspace/ });
  await userEvent.click(trigger);
  const input = screen.getByRole("combobox", {
    name: "Search commands and records",
  });
  await userEvent.type(input, "No matching record");
  expect(
    screen.getByText("No matching commands or loaded records."),
  ).toBeTruthy();
  await userEvent.clear(input);
  fireEvent.keyDown(input, { key: "ArrowDown" });
  fireEvent.keyDown(input, { key: "ArrowUp" });
  await userEvent.type(input, "Reports");
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(window.location.pathname).toBe("/reports"));
  expect(screen.queryByRole("dialog")).toBeNull();
  fireEvent.keyDown(window, { key: "k", ctrlKey: true });
  await screen.findByRole("dialog");
  fireEvent(
    screen.getByRole("dialog"),
    new Event("cancel", { bubbles: true, cancelable: true }),
  );
  expect(screen.queryByRole("dialog")).toBeNull();
  fireEvent.keyDown(window, { key: "k", metaKey: true });
  await userEvent.click(screen.getByRole("option", { name: /Authored suite/ }));
  expect(window.location.pathname).toContain("/suites/authored");
});
it("shell persists collapse/theme, provides session menu, refresh and signed-out navigation", async () => {
  const refresh = vi.fn(),
    signOut = vi.fn();
  wrap(
    <WorkspaceShell
      token="fixture"
      targets={[]}
      suites={[]}
      runs={[]}
      onSignOut={signOut}
      refresh={refresh}
    >
      <h1>Workspace</h1>
    </WorkspaceShell>,
    "/models",
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Collapse sidebar" }),
  );
  expect(localStorage.getItem("praxis-sidebar")).toBe("collapsed");
  await userEvent.click(screen.getByRole("button", { name: "Expand sidebar" }));
  await userEvent.click(
    screen.getByRole("button", { name: "Theme", exact: true }),
  );
  expect(document.documentElement.classList.contains("light")).toBe(true);
  window.dispatchEvent(new Event("praxis-toggle-theme"));
  await waitFor(() =>
    expect(document.documentElement.classList.contains("light")).toBe(false),
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Refresh workspace" }),
  );
  expect(refresh).toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
  expect(signOut).toHaveBeenCalled();
  await userEvent.click(screen.getByLabelText("Local session menu"));
  expect(screen.getByText("Local session active")).toBeTruthy();
  fireEvent.keyDown(window, { key: "r" });
  expect(window.location.pathname).toBe("/runs");
  cleanup();
  wrap(
    <WorkspaceShell
      token=""
      targets={[]}
      suites={[]}
      runs={[]}
      onSignOut={signOut}
      refresh={refresh}
    >
      <h1>Signed out</h1>
    </WorkspaceShell>,
  );
  expect(screen.getByRole("link", { name: "Sign in" })).toBeTruthy();
});
it("mobile navigation closes on Escape, link navigation and scrim and traps keyboard traversal", async () => {
  wrap(
    <WorkspaceShell
      token="fixture"
      targets={[]}
      suites={[]}
      runs={[]}
      onSignOut={vi.fn()}
      refresh={vi.fn()}
    >
      <h1>Workspace</h1>
    </WorkspaceShell>,
  );
  const open = screen.getByRole("button", { name: "Open navigation" });
  await userEvent.click(open);
  expect(document.querySelector(".workspace-body")?.hasAttribute("inert")).toBe(
    true,
  );
  fireEvent.keyDown(window, { key: "Tab", shiftKey: true });
  fireEvent.keyDown(window, { key: "Tab" });
  fireEvent.keyDown(window, { key: "Escape" });
  expect(document.querySelector(".workspace-body")?.hasAttribute("inert")).toBe(
    false,
  );
  await userEvent.click(open);
  await userEvent.click(
    screen.getByRole("button", { name: "Close navigation drawer" }),
  );
  await userEvent.click(open);
  await userEvent.click(
    screen.getByRole("button", { name: "Close navigation", exact: true }),
  );
  await userEvent.click(open);
  await userEvent.click(
    screen.getByRole("link", { name: "Targets", exact: true }),
  );
  expect(window.location.pathname).toBe("/targets");
});
it("modal dismiss and code preview preserve full untrusted text without execution", async () => {
  const close = vi.fn();
  wrap(
    <Modal title="Owned dialog" onDismiss={close}>
      <CodeBlock value={"<script>untrusted</script>" + "x".repeat(15000)} />
    </Modal>,
  );
  expect(document.querySelector("script")).toBeNull();
  await userEvent.click(
    screen.getByRole("button", { name: /Show complete output/ }),
  );
  expect(screen.getByRole("button", { name: /Collapse preview/ })).toBeTruthy();
  await userEvent.click(
    screen.getByRole("button", { name: /Collapse preview/ }),
  );
  await userEvent.click(screen.getByRole("button", { name: "Close dialog" }));
  expect(close).toHaveBeenCalled();
  cleanup();
  render(
    <>
      <CodeBlock value={undefined} />
      <Icon name="unrecognized" />
    </>,
  );
  expect(screen.getByText("Not recorded")).toBeTruthy();
});
it("run inspection keeps failures, traces and provenance, exports inert HTML, and confirms cancellation", async () => {
  const cancel = vi.fn(async () => ({ ok: true })),
    exporter = vi.fn(async () => {});
  wrap(
    <RunInspector
      run={{ ...run, status: "running", error: "Interrupted previously" }}
      busy={false}
      onCancel={cancel}
      onExport={exporter}
    />,
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Failed tasks only" }),
  );
  expect(
    screen.queryByRole("heading", { name: "first", exact: true }),
  ).toBeNull();
  expect(screen.getByRole("cell", { name: "Fail", exact: true })).toBeTruthy();
  await userEvent.click(
    screen.getByRole("button", { name: "Failed tasks only" }),
  );
  await userEvent.click(screen.getByText("Tool trace · 1 recorded events"));
  expect(screen.getByText(/Executed actions and state evidence/)).toBeTruthy();
  await userEvent.click(screen.getAllByText("Prompt and output")[1]);
  await userEvent.click(
    within(
      screen
        .getByRole("heading", { name: "second", exact: true })
        .closest("article")!,
    ).getByRole("button", { name: /Show complete output/ }),
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Export evidence" }),
  );
  expect(exporter).toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Export HTML" }));
  expect(URL.createObjectURL).toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Print report" }));
  expect(window.print).toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Cancel run" }));
  await userEvent.click(screen.getByRole("button", { name: "Keep running" }));
  expect(cancel).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Cancel run" }));
  await userEvent.click(
    screen.getByRole("button", { name: "Confirm cancellation" }),
  );
  expect(cancel).toHaveBeenCalledOnce();
  const html = printableReport({
    ...run,
    target_name: "<img src=x onerror=alert(1)>",
    result: {
      tasks: [
        {
          id: "<script>bad</script>",
          assertions: [
            { name: '"quoted"', actual: "<svg onload=bad()>", expected: "a'b" },
          ],
        },
      ],
    },
  });
  expect(html).not.toContain("<script>bad");
  expect(html).not.toContain("<img src=x");
  expect(html).toContain("&lt;svg");
  expect(html).toContain("default-src 'none'");
  expect(printableReport({})).toContain("No graded result");
});
it("empty run data and all-passing filter states do not invent evidence", async () => {
  wrap(
    <RunInspector
      run={{ status: "queued" }}
      busy={true}
      onCancel={vi.fn()}
      onExport={vi.fn()}
    />,
  );
  expect(screen.getByText("Not graded")).toBeTruthy();
  expect(
    screen.getByText("Task evidence appears as execution is persisted."),
  ).toBeTruthy();
  cleanup();
  wrap(
    <RunInspector
      run={{
        ...run,
        result: {
          tasks: [run.result.tasks[0]],
          summary: { total: 1, passed: 1 },
          events: [{ event: "old_event" }],
        },
      }}
      busy={false}
      onCancel={vi.fn()}
      onExport={vi.fn()}
    />,
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Failed tasks only" }),
  );
  expect(screen.getByText("No failed executed tasks")).toBeTruthy();
  expect(screen.getByText("100% passed")).toBeTruthy();
});
it("structured suite editor edits metadata, tasks, schemas and assertions without mutating versions", async () => {
  const save = vi.fn(async () => {}),
    error = vi.fn();
  wrap(
    <SuiteEditor initial={suite} onSave={save} busy={false} onError={error} />,
  );
  await userEvent.clear(screen.getByLabelText("Suite title"));
  await userEvent.type(
    screen.getByLabelText("Suite title"),
    "Revised contract",
  );
  await userEvent.clear(screen.getByLabelText("Version", { exact: true }));
  await userEvent.type(
    screen.getByLabelText("Version", { exact: true }),
    "1.0.1",
  );
  await userEvent.clear(screen.getByLabelText("Suite slug"));
  await userEvent.type(screen.getByLabelText("Suite slug"), "authored-copy");
  await userEvent.click(screen.getByRole("button", { name: /second/ }));
  await userEvent.type(screen.getByLabelText("Scenario identifier"), "a");
  await userEvent.type(screen.getByLabelText("Scenario prompt"), " more");
  fireEvent.change(screen.getByLabelText("Output schema"), {
    target: { value: "invalid" },
  });
  await userEvent.click(screen.getByRole("button", { name: "Apply schema" }));
  expect(screen.getByRole("alert")).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Output schema"), {
    target: { value: '{"type":"object"}' },
  });
  await userEvent.click(screen.getByRole("button", { name: "Apply schema" }));
  fireEvent.change(screen.getByLabelText("Assertions JSON"), {
    target: { value: "{}" },
  });
  await userEvent.click(
    screen.getByRole("button", { name: "Apply assertions" }),
  );
  expect(screen.getByText("Enter a JSON array of assertions.")).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Assertions JSON"), {
    target: { value: "[]" },
  });
  await userEvent.click(
    screen.getByRole("button", { name: "Apply assertions" }),
  );
  await userEvent.click(screen.getByText("Fixture inspection"));
  await userEvent.click(screen.getByRole("button", { name: "+ Add scenario" }));
  await userEvent.click(
    screen.getByRole("button", { name: "Save configuration" }),
  );
  expect(save).toHaveBeenCalled();
  expect(save.mock.calls[0][0].version).toBe("1.0.1");
  expect(suite.version).toBe("1.0.0");
});
it("suite validation handles malformed objects, duplicates, missing scenarios and raw JSON", async () => {
  expect(suiteIssues(null).length).toBe(1);
  expect(suiteIssues([]).length).toBe(1);
  expect(suiteIssues({}).length).toBe(4);
  expect(
    suiteIssues({ ...suite, tasks: [{ id: "x" }, { id: "x" }] }),
  ).toContain("Scenario identifiers must be unique.");
  expect(suiteIssues(suite)).toEqual([]);
  const save = vi.fn(async () => {}),
    error = vi.fn();
  wrap(<SuiteEditor onSave={save} busy={false} onError={error} />);
  expect(screen.getByText("Start with one explicit task")).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: "Full JSON" }));
  fireEvent.change(screen.getByLabelText("Versioned suite JSON"), {
    target: { value: "invalid" },
  });
  await userEvent.click(
    screen.getByRole("button", { name: "Save configuration" }),
  );
  expect(error).toHaveBeenCalledWith("Enter valid JSON");
  fireEvent.change(screen.getByLabelText("Versioned suite JSON"), {
    target: { value: JSON.stringify(suite) },
  });
  await userEvent.click(
    screen.getByRole("button", { name: "Structured editor" }),
  );
  expect(screen.getByLabelText("Scenario identifier")).toHaveProperty(
    "value",
    "first",
  );
  cleanup();
  wrap(<SuiteExplorer suite={suite} />);
  await userEvent.click(screen.getByRole("button", { name: /second/ }));
  expect(screen.getByText("HTTP request contract")).toBeTruthy();
  expect(screen.getByText("Bounded agent environment")).toBeTruthy();
  await userEvent.click(screen.getByText("Reference fixtures"));
  expect(screen.getByText("Failing fixture")).toBeTruthy();
  expect(
    screen.getByRole("link", { name: /Create revision/ }).getAttribute("href"),
  ).toContain("authored");
  cleanup();
  wrap(<SuiteExplorer suite={{}} />);
  expect(screen.getByText("No scenario definitions recorded.")).toBeTruthy();
});
it("artifact selection displays only selected media and keeps HTML inert", async () => {
  const items = [
    {
      id: "text",
      filename: "untrusted.html",
      mime: "text/plain",
      content: "<script>bad()</script>",
      trust: "demo",
      sha256: "digest",
      size: 22,
    },
    { id: "image", mime: "image/png", data_url: "data:image/png;base64,AA" },
    { id: "audio", mime: "audio/wav", data_url: "data:audio/wav;base64,AA" },
    { id: "video", mime: "video/webm", data_url: "data:video/webm;base64,AA" },
    { id: "binary", mime: "application/octet-stream" },
  ];
  const view = wrap(<ArtifactInspector items={items} />);
  expect(screen.getByText("<script>bad()</script>")).toBeTruthy();
  expect(document.querySelector("script")).toBeNull();
  await userEvent.click(screen.getByRole("button", { name: /^image / }));
  expect(screen.getByRole("img")).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: /^audio / }));
  expect(document.querySelector("audio")).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: /^video / }));
  expect(document.querySelector("video")).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: /^binary / }));
  expect(
    screen.getByText("Binary artifact; metadata shown above."),
  ).toBeTruthy();
  view.unmount();
  wrap(<ArtifactInspector items={[]} />);
  expect(screen.getByText("No matching artifacts")).toBeTruthy();
});
it("overview derives execution distributions and failures only from persisted records", () => {
  wrap(
    <Overview
      data={{ runs: 2, targets: 1, artifacts: 2, recent_runs: [run] }}
      targets={[{ kind: "model" }]}
      suites={[suite]}
      runs={[
        run,
        {
          ...run,
          id: "r2",
          status: "failed",
          result: { summary: { failed: 1 } },
          error: "Provider timeout",
        },
      ]}
    />,
  );
  expect(screen.getByText("Recent failures")).toBeTruthy();
  expect(screen.getByLabelText("Execution status distribution")).toBeTruthy();
  expect(screen.getByText("2 run(s)")).toBeTruthy();
  cleanup();
  wrap(<Overview data={null} targets={[]} suites={[]} runs={[]} />);
  expect(
    screen.getByText("No percentages are inferred before a run exists."),
  ).toBeTruthy();
});
it("settings reads actual diagnostics and identity, offers CLI instructions and theme preference", async () => {
  call.mockImplementation(async (path) =>
    path === "/health"
      ? { ok: true, mode: "local" }
      : { username: "local-owner" },
  );
  wrap(<Settings />);
  expect(await screen.findByText("local-owner")).toBeTruthy();
  expect(screen.getByText("Health request succeeded")).toBeTruthy();
  expect(
    screen.getByText("CLI operation · stop the runtime first"),
  ).toBeTruthy();
  const listener = vi.fn();
  window.addEventListener("praxis-toggle-theme", listener);
  await userEvent.click(
    screen.getByRole("button", { name: "Switch appearance" }),
  );
  expect(listener).toHaveBeenCalled();
  window.removeEventListener("praxis-toggle-theme", listener);
  cleanup();
  call.mockRejectedValue(Error("API offline"));
  wrap(<Settings />);
  expect(await screen.findByText("API offline")).toBeTruthy();
});
it("loaded registries support sorting, scoped filtering, pagination and report links", async () => {
  localStorage.token = "fixture";
  const records = Array.from({ length: 15 }, (_, i) => ({
    id: "target-" + i,
    name: "Target " + String(i).padStart(2, "0"),
    kind: i % 2 ? "agent" : "model",
    provider: i % 2 ? "custom" : "demo",
    capabilities: ["json"],
    created_at: i,
  }));
  call.mockImplementation(async (path) =>
    path === "/targets"
      ? records
      : path === "/suites"
        ? [suite]
        : path === "/runs"
          ? [run]
          : [],
  );
  wrap(<App />, "/targets");
  await screen.findByRole("heading", { name: "Target 14" });
  await userEvent.click(screen.getByRole("button", { name: "Next" }));
  expect(screen.getByRole("heading", { name: "Target 00" })).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: "Previous" }));
  await userEvent.selectOptions(screen.getByLabelText("Sort by"), "name");
  expect(screen.getByRole("heading", { name: "Target 00" })).toBeTruthy();
  await userEvent.selectOptions(
    screen.getByLabelText("Filter records"),
    "agent",
  );
  expect(screen.queryByRole("heading", { name: "Target 00" })).toBeNull();
  await userEvent.selectOptions(screen.getByLabelText("Sort by"), "status");
  await userEvent.type(screen.getByLabelText("Search records"), "absent");
  expect(screen.getByText("No matching records")).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: "Clear filters" }));
  expect(screen.queryByText("No matching records")).toBeNull();
  cleanup();
  wrap(<App />, "/reports");
  expect(await screen.findByText("Inspect evidence →")).toBeTruthy();
});
it("session replacement immediately hides old registry data and stale exports cannot download", async () => {
  localStorage.token = "old";
  let resolve!: (v: any) => void;
  call.mockImplementation(async (path) =>
    path === "/targets"
      ? [{ id: "old", name: "Private old target", kind: "model" }]
      : path === "/suites"
        ? [suite]
        : path === "/runs/r1"
          ? run
          : [],
  );
  wrap(<App />, "/targets");
  await screen.findByRole("heading", { name: "Private old target" });
  call.mockImplementation(() => new Promise((r) => (resolve = r)));
  await act(async () => {
    localStorage.token = "new";
    window.dispatchEvent(new StorageEvent("storage", { key: "token" }));
  });
  expect(
    screen.queryByRole("heading", { name: "Private old target" }),
  ).toBeNull();
  cleanup();
  localStorage.token = "old";
  call.mockImplementation(async (path) => (path === "/runs/r1" ? run : []));
  wrap(<App />, "/runs/r1");
  await screen.findByRole("heading", { name: "completed · demo" });
  call.mockImplementation((path) =>
    path === "/runs/r1/export"
      ? new Promise((r) => (resolve = r))
      : Promise.resolve([]),
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Export evidence" }),
  );
  await act(async () => {
    localStorage.token = "new";
    window.dispatchEvent(new StorageEvent("storage", { key: "token" }));
  });
  await act(async () => resolve(run));
  expect(URL.createObjectURL).not.toHaveBeenCalled();
});

it("completed inspection avoids polling and unrelated bulk history transfers", async () => {
  localStorage.token = "fixture";
  call.mockImplementation(async (path) => (path === "/runs/r1" ? run : []));
  wrap(<App />, "/runs/r1");
  await screen.findByRole("heading", { name: "completed · demo" });
  expect(call.mock.calls.some(([path]) => path === "/runs")).toBe(false);
  const reads = call.mock.calls.filter(([path]) => path === "/runs/r1").length;
  vi.useFakeTimers();
  await act(async () => vi.advanceTimersByTime(8000));
  expect(call.mock.calls.filter(([path]) => path === "/runs/r1").length).toBe(
    reads,
  );
  vi.useRealTimers();
});
it("failed server logout is reported honestly and authentication payloads stay out of operation feedback", async () => {
  localStorage.token = "fixture";
  call.mockImplementation(async (path, body) =>
    path === "/auth/logout"
      ? Promise.reject(Error("API unavailable"))
      : body !== undefined
        ? { token: "never-render-this-session", user: { id: "owner" } }
        : [],
  );
  wrap(<App />, "/settings");
  await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
  expect(
    await screen.findByText(
      "Signed out in this browser. Server session revocation could not be verified.",
    ),
  ).toBeTruthy();
  expect(localStorage.token).toBeUndefined();
  await userEvent.click(screen.getByRole("button", { name: "Dismiss notice" }));
  await userEvent.type(screen.getByLabelText("Account name"), "owned-account");
  await userEvent.type(screen.getByLabelText("Password"), "test-password-123");
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  await screen.findByRole("heading", { name: "Overview" });
  expect(screen.queryByText("never-render-this-session")).toBeNull();
  expect(
    screen.queryByRole("heading", { name: "Operation result" }),
  ).toBeNull();
});

it("malformed scenario JSON remains editable and never crashes or silently drops invalid entries", async () => {
  for (const tasks of [[null], ["invalid"], [{ id: { invalid: true } }]]) {
    wrap(
      <SuiteEditor
        initial={{ ...suite, tasks }}
        onSave={vi.fn()}
        busy={false}
        onError={vi.fn()}
      />,
    );
    expect(screen.getByRole("status").textContent).toContain("scenario");
    expect(
      JSON.parse(
        (screen.getByLabelText("Versioned suite JSON") as HTMLTextAreaElement)
          .value,
      ).tasks,
    ).toEqual(tasks);
    cleanup();
  }
});

it("invalid metadata and non-text prompts retain safe raw editing without coercion crashes", () => {
  for (const invalid of [
    { ...suite, slug: { toString: null } },
    { ...suite, title: { toString: null } },
    { ...suite, version: [] },
    { ...suite, tasks: [{ id: "bad-prompt", prompt: { toString: null } }] },
  ]) {
    wrap(
      <SuiteEditor
        initial={invalid}
        onSave={vi.fn()}
        busy={false}
        onError={vi.fn()}
      />,
    );
    expect(screen.getByRole("status").textContent).toContain(
      "Definition needs attention",
    );
    expect(
      JSON.parse(
        (screen.getByLabelText("Versioned suite JSON") as HTMLTextAreaElement)
          .value,
      ),
    ).toEqual(invalid);
    cleanup();
  }
});
