import React from "react";
import { afterEach, beforeEach, it, expect, vi } from "vitest";
import {
  render,
  screen,
  waitFor,
  cleanup,
  fireEvent,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { App } from "../src/main";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
const call = vi.mocked(api);
const targets = [
  { id: "m1", name: "Model fixture", kind: "model", provider: "demo" },
  { id: "a1", name: "Agent fixture", kind: "agent", provider: "demo" },
  { id: "h1", name: "HTTP fixture", kind: "application", provider: "custom" },
];
const suites = [
  {
    slug: "structured-agent",
    version: "1",
    title: "Structured suite",
    tasks: [{ id: "t" }],
  },
  {
    slug: "agent-workflows",
    version: "1",
    title: "Agent suite",
    tasks: [{ environment: {} }],
  },
  {
    slug: "http-application",
    version: "1",
    title: "HTTP suite",
    tasks: [{ api_request: {} }],
  },
];
const result = {
  trust: "demo",
  suite_slug: "structured-agent",
  suite_version: "1",
  summary: { passed: 1, total: 2, pass_rate: 0.5 },
  not_run_tasks: [{ id: "missing" }],
  events: [{ type: "run_completed" }],
  tasks: [
    {
      id: "t",
      passed: true,
      prompt: "prompt",
      output: { ok: true },
      latency_ms: 1,
      assertions: [
        { name: "schema", passed: true, expected: true, actual: true },
        { name: "long", passed: false, expected: 1, actual: "x".repeat(250) },
      ],
    },
    {
      id: "f",
      passed: false,
      output: "bad",
      error: { category: "timeout" },
      assertions: [],
    },
  ],
};
let records: Record<string, unknown>;
function open(path: string) {
  window.history.replaceState({}, "", path);
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>,
  );
}
async function settled() {
  await act(async () => {
    await new Promise((r) => setTimeout(r, 0));
  });
}
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.open = true;
  };
  HTMLDialogElement.prototype.close = function () {
    this.open = false;
  };
  localStorage.clear();
  localStorage.token = "session-fixture";
  records = {};
  call.mockReset();
  call.mockImplementation(async (path, body) => {
    if (body !== undefined) {
      if (path.startsWith("/auth/")) return { token: "new-session", user: {} };
      if (path === "/targets") return { id: "saved" };
      if (path === "/runs") return { id: "r1" };
      if (path === "/suites") return { slug: "saved" };
      if (path === "/worlds") return { id: "w1" };
      return { ok: true };
    }
    if (path in records) return records[path];
    if (path === "/targets") return targets;
    if (path === "/suites") return suites;
    if (path === "/dashboard")
      return {
        runs: 0,
        targets: 3,
        recent_runs: [
          {
            id: "r1",
            target_name: "Model fixture",
            suite_slug: "structured-agent",
            status: "completed",
          },
        ],
      };
    if (path === "/runs/r1" || path === "/runs/r1/export")
      return { id: "r1", status: "completed", trust: "demo", seed: 73, result };
    return [];
  });
  vi.stubGlobal(
    "URL",
    Object.assign(URL, {
      createObjectURL: vi.fn(() => "blob:fixture"),
      revokeObjectURL: vi.fn(),
    }),
  );
  vi.spyOn(window, "print").mockImplementation(() => {});
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});
it("home, theme and signed-out authentication workflow", async () => {
  delete localStorage.token;
  open("/");
  expect(screen.getByText(/Judge AI by/)).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: /Theme/ }));
  cleanup();
  open("/settings");
  await userEvent.type(screen.getByLabelText("Account name"), "tester");
  await userEvent.type(screen.getByLabelText("Password"), "test-password-123");
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  await screen.findByRole("heading", { name: "Overview" });
  expect(localStorage.token).toBe("new-session");
});
it.each([
  "/dashboard",
  "/settings",
  "/admin",
  "/docs",
  "/methodology",
  "/privacy",
  "/terms",
  "/not-found",
])("renders stable route %s", async (path) => {
  open(path);
  await settled();
  expect(screen.getByRole("main")).toBeTruthy();
  if (path === "/not-found")
    expect(screen.getByText("Page not found")).toBeTruthy();
});
it.each(["/models", "/agents", "/apps"])(
  "filters targets and executes diagnostics %s",
  async (path) => {
    open(path);
    await settled();
    const names = {
      "/models": "Model fixture",
      "/agents": "Agent fixture",
      "/apps": "HTTP fixture",
    };
    expect(screen.getByRole("heading", { name: names[path] })).toBeTruthy();
    await userEvent.click(
      screen.getByRole("button", { name: "Test connection" }),
    );
    await screen.findByRole("heading", { name: "Operation result" });
    await userEvent.type(screen.getByLabelText("Search records"), "absent");
    expect(
      screen.queryByRole("button", { name: "Test connection" }),
    ).toBeNull();
  },
);
it.each(["/models/new", "/agents/new", "/apps/new"])(
  "saves target form and explicit consent %s",
  async (path) => {
    open(path);
    await userEvent.type(screen.getByLabelText("Name"), "owned target");
    if (path === "/apps/new") {
      await userEvent.type(
        screen.getByLabelText("Endpoint"),
        "http://localhost:9000",
      );
      await userEvent.click(screen.getByLabelText(/I own this endpoint/));
      await userEvent.click(screen.getByLabelText(/Allow explicit POST/));
    }
    await userEvent.click(
      screen.getByRole("button", { name: "Save configuration" }),
    );
    await waitFor(() =>
      expect(call.mock.calls.some(([p, b]) => p === "/targets" && !!b)).toBe(
        true,
      ),
    );
    const body = call.mock.calls.find(
      ([p, b]) => p === "/targets" && !!b,
    )![1] as any;
    expect(body.authorized).toBe(path === "/apps/new");
    expect(body.allow_mutation).toBe(path === "/apps/new");
  },
);
it("loading, empty, error and request rejection are distinguishable", async () => {
  let finish!: (v: unknown) => void;
  call.mockImplementation((path) =>
    path === "/runs" ? new Promise((r) => (finish = r)) : Promise.resolve([]),
  );
  open("/runs");
  expect(screen.getByRole("status").textContent).toContain("Loading");
  await act(async () => finish([]));
  expect(await screen.findByText("No records yet")).toBeTruthy();
  cleanup();
  call.mockRejectedValue(Error("offline"));
  open("/runs");
  expect((await screen.findByRole("alert")).textContent).toContain("offline");
});
it("suite JSON form rejects malformed input and saves valid definition", async () => {
  open("/suites/new");
  await userEvent.click(
    await screen.findByRole("button", { name: "Full JSON" }),
  );
  const input = screen.getByLabelText("Versioned suite JSON");
  await userEvent.clear(input);
  await userEvent.type(input, "invalid");
  await userEvent.click(
    screen.getByRole("button", { name: "Save configuration" }),
  );
  expect(await screen.findByText("Enter valid JSON")).toBeTruthy();
  fireEvent.change(input, { target: { value: JSON.stringify(suites[0]) } });
  await userEvent.click(
    screen.getByRole("button", { name: "Save configuration" }),
  );
  await screen.findByRole("heading", { name: "Evaluation suites" });
});
it("run form filters suites by selected target and preserves launch key", async () => {
  open("/runs/new");
  await settled();
  await userEvent.selectOptions(screen.getByLabelText("Target ID"), "a1");
  expect(screen.getByRole("option", { name: "Agent suite · 1" })).toBeTruthy();
  await userEvent.selectOptions(screen.getByLabelText("Target ID"), "h1");
  expect(screen.getByRole("option", { name: "HTTP suite · 1" })).toBeTruthy();
  await userEvent.selectOptions(screen.getByLabelText("Target ID"), "m1");
  await userEvent.click(screen.getByLabelText(/Publish outputs/));
  await userEvent.click(
    screen.getByRole("button", { name: "Start evaluation" }),
  );
  await screen.findByRole("heading", { name: "completed · demo" });
  const body = call.mock.calls.find(
    ([p, b]) => p === "/runs" && !!b,
  )![1] as any;
  expect(body.public).toBe(true);
  expect(body.seed).toBe(73);
  expect(body.suite_version).toBe("1");
  expect(body.idempotency_key).toBeTruthy();
});
it("run inspection, standalone export interaction and print handle failures", async () => {
  records["/runs/r1"] = { id: "r1", status: "running", seed: 73, result };
  open("/runs/r1");
  await screen.findByText("Unexecuted scenarios");
  await userEvent.click(screen.getByRole("button", { name: "Cancel run" }));
  await userEvent.click(
    await screen.findByRole("button", { name: "Confirm cancellation" }),
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Export evidence" }),
  );
  expect(URL.createObjectURL).toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Print report" }));
  expect(window.print).toHaveBeenCalled();
  call.mockRejectedValueOnce(Error("export failed"));
  await userEvent.click(
    screen.getByRole("button", { name: "Export evidence" }),
  );
  expect(await screen.findByText("export failed")).toBeTruthy();
});
it("world creation and replay expose deterministic levels", async () => {
  open("/worlds/new");
  await userEvent.type(screen.getByLabelText("Name"), "owned world");
  await userEvent.click(
    screen.getByRole("button", { name: "Save configuration" }),
  );
  await waitFor(() =>
    expect(call.mock.calls.some(([p, b]) => p === "/worlds" && !!b)).toBe(true),
  );
  cleanup();
  records["/worlds/w1"] = {
    id: "w1",
    name: "World",
    replay: { levels: [{ level: 1 }] },
  };
  open("/worlds/w1");
  await screen.findByText("Level 1");
  await userEvent.click(
    screen.getByRole("button", { name: "Execute deterministic replay" }),
  );
  expect(call.mock.calls.some(([p]) => p === "/worlds/w1/replay")).toBe(true);
});
it("suite details clone/export and list links retain version identity", async () => {
  records["/suites/structured-agent@1"] = suites[0];
  open("/suites/structured-agent@1");
  await screen.findByText("Clone suite");
  await userEvent.click(screen.getByRole("button", { name: "Export JSON" }));
  expect(URL.createObjectURL).toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Clone suite" }));
  expect(call.mock.calls.some(([p, b]) => p === "/suites" && !!b)).toBe(true);
  cleanup();
  open("/suites");
  await settled();
  expect(
    screen
      .getAllByRole("link", { name: /Inspect suite/ })[0]
      .getAttribute("href"),
  ).toContain("@1");
});
it("blind vote reveal remains bound to pair until next comparison", async () => {
  records["/arena"] = {
    id: "match",
    demo: true,
    a: { content: "first" },
    b: { content: "second" },
  };
  call.mockImplementation(async (path, body) =>
    path === "/arena/match/vote"
      ? { choice: "a", a: "Model A", b: "Model B" }
      : path in records
        ? records[path]
        : [],
  );
  open("/arena");
  await screen.findByText("Output A");
  await userEvent.click(screen.getByRole("button", { name: "A wins" }));
  expect(await screen.findByText("Vote recorded")).toBeTruthy();
  expect(
    (screen.getByRole("button", { name: "A wins" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
  await userEvent.click(
    screen.getByRole("button", { name: "Next comparison" }),
  );
  await waitFor(() => expect(screen.queryByText("Vote recorded")).toBeNull());
});
it("empty arena, rankings, comparison and runs list show actual state", async () => {
  records["/arena"] = { empty: true, reason: "No owned pair" };
  open("/arena");
  expect(await screen.findByText("No eligible comparison yet")).toBeTruthy();
  cleanup();
  records["/leaderboards"] = { objective: [], preference: [] };
  open("/leaderboards");
  expect(await screen.findByText("Objective evidence")).toBeTruthy();
  cleanup();
  records["/runs"] = [
    {
      id: "r1",
      target_id: "m1",
      suite_slug: "structured-agent",
      seed: 73,
      conditions_hash: "condition",
      result,
    },
  ];
  open("/compare");
  await screen.findByText("Matched evaluation matrix");
  expect(screen.getByText("1 / 2")).toBeTruthy();
  cleanup();
  open("/runs");
  expect(await screen.findByText("Inspect evidence →")).toBeTruthy();
});
it("uploads enforce size and render inert text, image, audio and video previews", async () => {
  records["/artifacts"] = [
    { id: "html", mime: "text/plain", content: "<script>inert</script>" },
    {
      id: "img",
      mime: "image/png",
      data_url: "data:image/png;base64,AA",
      filename: "Image",
    },
    { id: "audio", mime: "audio/wav", data_url: "data:audio/wav;base64,AA" },
    { id: "video", mime: "video/mp4", data_url: "data:video/mp4;base64,AA" },
    { id: "unknown", mime: "application/octet-stream" },
  ];
  open("/artifacts");
  await screen.findByText("<script>inert</script>");
  await userEvent.click(screen.getByRole("button", { name: /^audio / }));
  expect(document.querySelector("audio")).toBeTruthy();
  await userEvent.click(screen.getByRole("button", { name: /^video / }));
  expect(document.querySelector("video")).toBeTruthy();
  const input = screen.getByLabelText("Choose a file");
  await userEvent.upload(input, new File(["x".repeat(1048577)], "large.txt"));
  expect(
    await screen.findByText("File exceeds 1 MiB upload limit"),
  ).toBeTruthy();
  await userEvent.upload(input, new File(["safe"], "test.txt"));
  await waitFor(() =>
    expect(call.mock.calls.some(([p, b]) => p === "/artifacts" && !!b)).toBe(
      true,
    ),
  );
  await userEvent.click(
    screen.getByRole("button", { name: "Check owned website fixture" }),
  );
  expect(call.mock.calls.some(([p]) => p === "/artifacts/check-website")).toBe(
    true,
  );
});
it("stale auxiliary response cannot populate a new session", async () => {
  let old!: (value: unknown) => void;
  let first = true;
  call.mockImplementation((path) => {
    if (path === "/targets" && first) {
      first = false;
      return new Promise((r) => (old = r));
    }
    return Promise.resolve(
      path === "/targets" ? [] : path === "/suites" ? suites : [],
    );
  });
  open("/runs/new");
  await settled();
  await act(async () => {
    localStorage.token = "new-session";
    window.dispatchEvent(new StorageEvent("storage", { key: "token" }));
  });
  await act(async () =>
    old([{ id: "private-old", name: "Other session target", kind: "model" }]),
  );
  expect(
    screen.queryByRole("option", { name: /Other session target/ }),
  ).toBeNull();
  await act(async () => {
    delete localStorage.token;
    window.dispatchEvent(new StorageEvent("storage", { key: null }));
  });
  expect(await screen.findByLabelText("Account name")).toBeTruthy();
});
it("logout, expired session and action failures surface safely", async () => {
  open("/settings");
  await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
  expect(await screen.findByLabelText("Account name")).toBeTruthy();
  cleanup();
  localStorage.token = "session";
  open("/settings");
  await act(async () =>
    window.dispatchEvent(new Event("praxis-session-expired")),
  );
  expect(await screen.findByLabelText("Account name")).toBeTruthy();
  call.mockRejectedValue(Error("denied"));
  await userEvent.type(screen.getByLabelText("Account name"), "tester");
  await userEvent.type(screen.getByLabelText("Password"), "test-password-123");
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(await screen.findByText("denied")).toBeTruthy();
});
