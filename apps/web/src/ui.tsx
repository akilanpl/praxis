import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

const shapes: Record<string, ReactNode> = {
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v3m0 16v3M1 12h3m16 0h3" />
    </>
  ),
  suite: (
    <>
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </>
  ),
  play: <path d="m8 4 12 8-12 8z" />,
  compare: (
    <>
      <path d="M4 6h16m-4-4 4 4-4 4M20 18H4m4-4-4 4 4 4" />
    </>
  ),
  file: (
    <>
      <path d="M14 2H5v20h14V7zM14 2v6h5M8 13h8m-8 4h5" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="m9 3 6 0 1 4 4 2v6l-4 2-1 4H9l-1-4-4-2V9l4-2z" />
    </>
  ),
  search: (
    <>
      <circle cx="10" cy="10" r="6" />
      <path d="m15 15 6 6" />
    </>
  ),
  menu: <path d="M4 6h16M4 12h16M4 18h16" />,
  close: <path d="m6 6 12 12M6 18 18 6" />,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  chevron: <path d="m9 5 7 7-7 7" />,
  box: (
    <>
      <path d="m12 2 10 5v10l-10 5-10-5V7zM2 7l10 5 10-5M12 12v10" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 6v6l4 2" />
    </>
  ),
  check: <path d="m4 12 5 5L20 6" />,
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 1v3m0 16v3M1 12h3m16 0h3M4 4l2 2m12 12 2 2M4 20l2-2M18 6l2-2" />
    </>
  ),
};

export function Icon({
  name = "grid",
  size = 18,
}: {
  name?: string;
  size?: number;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {shapes[name] || shapes.grid}
    </svg>
  );
}
export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return (
    <span className={"badge " + tone}>
      <span className="status-dot" />
      {children}
    </span>
  );
}
export function CodeBlock({
  value,
  label = "Evidence",
}: {
  value: any;
  label?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const text =
    typeof value === "string"
      ? value
      : (JSON.stringify(value, null, 2) ?? "Not recorded");
  return (
    <div className="code-block">
      <div className="code-label">
        {label}
        <span>Read only</span>
      </div>
      <pre role="region" tabIndex={0} aria-label={label}>
        {expanded ? text : text.slice(0, 14000)}
      </pre>
      {text.length > 14000 && (
        <button className="ghost" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Collapse preview" : "Show complete output"} (
          {text.length.toLocaleString()} characters)
        </button>
      )}
    </div>
  );
}
export function Modal({
  title,
  onDismiss,
  children,
}: {
  title: string;
  onDismiss: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const dismiss = useRef(onDismiss);
  dismiss.current = onDismiss;
  useEffect(() => {
    const node = ref.current!;
    const previous = document.activeElement as HTMLElement;
    node.showModal();
    return () => {
      node.close();
      previous?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-label={title}
      onCancel={(e) => {
        e.preventDefault();
        dismiss.current();
      }}
      onClick={(e) => {
        if (e.target === ref.current) {
          const r = ref.current.getBoundingClientRect();
          if (
            e.clientX < r.left ||
            e.clientX > r.right ||
            e.clientY < r.top ||
            e.clientY > r.bottom
          )
            dismiss.current();
        }
      }}
    >
      <div className="dialog-heading">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={onDismiss}
        >
          <Icon name="close" />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export const navigation = [
  { to: "/dashboard", label: "Overview", icon: "grid" },
  { to: "/targets", label: "Targets", icon: "target" },
  { to: "/suites", label: "Evaluation suites", icon: "suite" },
  { to: "/runs", label: "Runs", icon: "play" },
  { to: "/compare", label: "Comparisons", icon: "compare" },
  { to: "/reports", label: "Reports", icon: "file" },
  { to: "/artifacts", label: "Artifacts", icon: "box" },
  { to: "/worlds", label: "Reference worlds", icon: "grid" },
  { to: "/arena", label: "Blind review", icon: "compare" },
  { to: "/leaderboards", label: "Community signals", icon: "target" },
  { to: "/settings", label: "Settings", icon: "settings" },
  { to: "/docs", label: "Documentation", icon: "file" },
  { to: "/methodology", label: "Methodology", icon: "suite" },
  { to: "/admin", label: "Trust controls", icon: "settings" },
];
export function WorkspaceShell({
  children,
  token,
  onSignOut,
  targets,
  suites,
  runs,
  refresh,
}: {
  children: ReactNode;
  token: string;
  onSignOut: () => void;
  targets: any[];
  suites: any[];
  runs: any[];
  refresh: () => void;
}) {
  const location = useLocation(),
    navigate = useNavigate();
  const [collapsed, collapse] = useState(
    localStorage.getItem("praxis-sidebar") === "collapsed",
  );
  const [mobile, showMobile] = useState(false);
  const [palette, showPalette] = useState(false);
  const [query, Q] = useState("");
  const [active, A] = useState(0);
  const [light, Light] = useState(
    localStorage.getItem("praxis-theme") === "light" ||
      document.documentElement.classList.contains("light"),
  );
  useEffect(() => {
    const toggle = () => Light((l) => !l);
    window.addEventListener("praxis-toggle-theme", toggle);
    return () => window.removeEventListener("praxis-toggle-theme", toggle);
  }, []);
  useEffect(() => {
    document.documentElement.classList.toggle("light", light);
    localStorage.setItem("praxis-theme", light ? "light" : "dark");
  }, [light]);
  useEffect(() => {
    if (!mobile) return;
    const previous = document.activeElement as HTMLElement;
    const aside = document.querySelector<HTMLElement>(".sidebar")!;
    aside.querySelector<HTMLElement>("a")?.focus();
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const nodes = Array.from(
        aside.querySelectorAll<HTMLElement>("a,button"),
      ).filter((e) => getComputedStyle(e).display !== "none");
      const first = nodes[0],
        last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    window.addEventListener("keydown", trap);
    return () => {
      window.removeEventListener("keydown", trap);
      previous?.focus();
    };
  }, [mobile]);
  const previousPath = useRef(location.pathname);
  useEffect(() => {
    showMobile(false);
    showPalette(false);
    document.querySelector(".session-menu")?.removeAttribute("open");
    if (previousPath.current !== location.pathname) {
      previousPath.current = location.pathname;
      const timer = window.setTimeout(
        () => document.getElementById("main")?.focus(),
        0,
      );
      return () => clearTimeout(timer);
    }
  }, [location.pathname]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        showMobile(false);
        showPalette((p) => !p);
        Q("");
        A(0);
      }
      if (e.key === "Escape") showMobile(false);
      if (
        e.key === "r" &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey &&
        !(e.target as HTMLElement).closest?.("dialog") &&
        !["INPUT", "TEXTAREA", "SELECT"].includes(
          (e.target as HTMLElement).tagName,
        )
      )
        navigate("/runs");
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);
  const options = [
    ...navigation,
    ...targets.map((t) => ({
      to:
        "/" +
        ({ model: "models", agent: "agents", application: "apps" }[t.kind] ||
          "targets") +
        "?record=" +
        encodeURIComponent(t.id),
      label: t.name,
      icon: "target",
    })),
    ...suites.map((s) => ({
      to: "/suites/" + s.slug + "@" + s.version,
      label: s.title + " · " + s.version,
      icon: "suite",
    })),
    ...runs.map((r) => ({
      to: "/runs/" + r.id,
      label: (r.target_name || r.target_id) + " · " + r.status,
      icon: "play",
    })),
  ]
    .filter((x) => x.label.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 24);
  const area = location.pathname.split("/")[1];
  const current = navigation.find((x) => x.to === "/" + area) || {
    label:
      (
        {
          models: "Models",
          agents: "Agents",
          apps: "HTTP applications",
          privacy: "Privacy",
          terms: "Terms",
        } as any
      )[area] || "Workspace",
  };
  return (
    <div
      className={
        "workspace " +
        (collapsed ? "sidebar-collapsed " : "") +
        (mobile ? "mobile-open" : "")
      }
    >
      <a className="skip" href="#main">
        Skip to content
      </a>
      <button
        className="sidebar-scrim"
        aria-label="Close navigation"
        tabIndex={mobile ? 0 : -1}
        onClick={() => showMobile(false)}
      />
      <aside className="sidebar" aria-label="Workspace navigation">
        <button
          className="icon-button mobile-close"
          aria-label="Close navigation drawer"
          onClick={() => showMobile(false)}
        >
          <Icon name="close" />
        </button>
        <Link className="brand" to="/">
          <span className="brand-mark" aria-hidden="true">
            P<span />
          </span>
          <span className="brand-copy">
            PRAXIS<small>EVALUATION WORKSPACE</small>
          </span>
        </Link>
        <div className="workspace-switch">
          <span className="workspace-avatar">L</span>
          <span className="nav-label">
            Local workspace<small>Private · on this machine</small>
          </span>
          <span className="online-dot" title="Local-first mode" />
        </div>
        <div className="nav-section-label">WORKSPACE</div>
        <nav aria-label="Primary navigation">
          {navigation.slice(0, 7).map((x) => (
            <Link
              key={x.to}
              aria-label={x.label}
              className={
                current.label === x.label ||
                (x.to === "/targets" &&
                  ["models", "agents", "apps"].includes(area))
                  ? "active"
                  : ""
              }
              aria-current={current.label === x.label ? "page" : undefined}
              to={x.to}
              title={collapsed ? x.label : undefined}
            >
              <Icon name={x.icon} />
              <span className="nav-label">{x.label}</span>
            </Link>
          ))}
        </nav>
        <div className="nav-section-label">EXPLORE</div>
        <nav aria-label="Reference navigation">
          {navigation.slice(7, 10).map((x) => (
            <Link
              key={x.to}
              aria-label={x.label}
              className={
                current.label === x.label ||
                (x.to === "/targets" &&
                  ["models", "agents", "apps"].includes(area))
                  ? "active"
                  : ""
              }
              to={x.to}
            >
              <Icon name={x.icon} />
              <span className="nav-label">{x.label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-foot">
          <Link
            aria-label="Settings & recovery"
            title="Settings & recovery"
            to="/settings"
          >
            <Icon name="settings" />
            <span className="nav-label">Settings & recovery</span>
          </Link>
          <Link aria-label="Documentation" title="Documentation" to="/docs">
            <Icon name="file" />
            <span className="nav-label">Documentation</span>
          </Link>
          <button
            className="ghost collapse-toggle"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            onClick={() => {
              collapse(!collapsed);
              localStorage.setItem(
                "praxis-sidebar",
                collapsed ? "expanded" : "collapsed",
              );
            }}
          >
            <Icon name="menu" />
            <span className="nav-label">
              {collapsed ? "Expand sidebar" : "Collapse sidebar"}
            </span>
          </button>
          <div className="local-note nav-label">
            <span className="online-dot" /> Your runtime. Your evidence.
          </div>
        </div>
      </aside>
      <div className="workspace-body" inert={mobile || undefined}>
        <header className="topbar">
          <div className="breadcrumbs">
            <button
              className="icon-button mobile-toggle"
              aria-label="Open navigation"
              aria-expanded={mobile}
              onClick={() => showMobile(!mobile)}
            >
              <Icon name="menu" />
            </button>
            <Link to="/dashboard">Workspace</Link>
            <span>/</span>
            <span>{current.label}</span>
            {location.pathname.split("/")[2] && (
              <>
                <span>/</span>
                <span className="breadcrumb-detail">
                  {location.pathname.endsWith("/new")
                    ? "New"
                    : location.pathname.split("/")[2]}
                </span>
              </>
            )}
          </div>
          <div className="topbar-actions">
            <button
              className="command-trigger"
              onClick={() => {
                showPalette(true);
                Q("");
                A(0);
              }}
            >
              <Icon name="search" />
              <span>Search workspace</span>
              <kbd>⌘ K</kbd>
            </button>
            <button
              className="icon-button"
              aria-label="Theme"
              title={light ? "Switch to dark theme" : "Switch to light theme"}
              onClick={() => Light(!light)}
            >
              <Icon name="sun" />
            </button>
            <button
              className="icon-button"
              aria-label="Refresh workspace"
              title="Refresh persisted records"
              onClick={refresh}
            >
              <Icon name="clock" />
            </button>
            <details className="session-menu">
              <summary aria-label="Local session menu">
                <span className="user-avatar">L</span>
              </summary>
              <div className="session-popover">
                <strong>{token ? "Local session active" : "Signed out"}</strong>
                <p>
                  Session authority stays on this runtime. Provider keys are
                  never shown here.
                </p>
                <Link to="/settings">Account & workspace settings</Link>
              </div>
            </details>
            {token ? (
              <button className="ghost sign-out" onClick={onSignOut}>
                Sign out
              </button>
            ) : (
              <Link className="button secondary" to="/settings">
                Sign in
              </Link>
            )}
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          {children}
          <footer className="bottom">
            <span>
              <span className="online-dot" /> Local-first evaluation · Evidence
              over claims
            </span>
            <Link to="/methodology">Methodology</Link>
            <Link to="/privacy">Privacy</Link>
            <Link to="/terms">Terms</Link>
          </footer>
        </main>
      </div>
      {palette && (
        <Modal title="Search workspace" onDismiss={() => showPalette(false)}>
          <div className="palette-input">
            <Icon name="search" />
            <input
              autoFocus
              role="combobox"
              aria-expanded="true"
              aria-controls="command-results"
              aria-activedescendant={
                options[active] ? "command-option-" + active : undefined
              }
              aria-label="Search commands and records"
              value={query}
              onChange={(e) => {
                Q(e.target.value);
                A(0);
              }}
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") {
                  e.preventDefault();
                  A(Math.min(active + 1, options.length - 1));
                }
                if (e.key === "ArrowUp") {
                  e.preventDefault();
                  A(Math.max(0, active - 1));
                }
                if (e.key === "Enter" && options[active]) {
                  navigate(options[active].to);
                  showPalette(false);
                }
              }}
            />
          </div>
          <div
            className="command-list"
            role="listbox"
            id="command-results"
            aria-label="Commands and records"
          >
            {options.map((x, i) => (
              <button
                role="option"
                aria-selected={i === active}
                id={"command-option-" + i}
                tabIndex={-1}
                className={i === active ? "selected" : ""}
                key={x.to}
                onClick={() => {
                  navigate(x.to);
                  showPalette(false);
                }}
              >
                <Icon name={x.icon} />
                <span>{x.label}</span>
                <small>
                  Open <Icon name="arrow" size={14} />
                </small>
              </button>
            ))}
            {!options.length && <p>No matching commands or loaded records.</p>}
          </div>
          <div className="dialog-footer">
            ↑ ↓ Navigate <span>↵ Open</span>
            <span>esc Close</span>
          </div>
        </Modal>
      )}
    </div>
  );
}
