import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "./api";
import { Badge, CodeBlock, Icon } from "./ui";
export const recoveryCommands =
  ".venv/bin/python scripts/backup_workspace.py backup \\\n  --database .praxis/praxis.sqlite --directory work/private-snapshot\n\n.venv/bin/python scripts/backup_workspace.py verify \\\n  --directory work/private-snapshot\n\n.venv/bin/python scripts/backup_workspace.py restore \\\n  --source work/private-snapshot --directory work/restored-workspace";
export default function Settings() {
  const [health, H] = useState<any>(null),
    [account, A] = useState<any>(null),
    [error, E] = useState("");
  useEffect(() => {
    let current = true;
    Promise.all([api("/health"), api("/me")])
      .then(([h, a]) => {
        if (current) {
          H(h);
          A(a);
        }
      })
      .catch((e) => {
        if (current) E(e.message);
      });
    return () => {
      current = false;
    };
  }, []);
  return (
    <div className="settings-layout">
      <nav className="settings-nav" aria-label="Workspace settings sections">
        <a href="#account">Account & sessions</a>
        <a href="#providers">Model providers</a>
        <a href="#storage">Workspace storage</a>
        <a href="#recovery">Backup & restore</a>
        <a href="#runtime">Runtime diagnostics</a>
        <a href="#preferences">Preferences</a>
      </nav>
      <div>
        <article id="account">
          <div className="section-heading">
            <div>
              <span className="eyebrow">ACCOUNT</span>
              <h2>Secure local workspace</h2>
            </div>
            <Badge>Local session</Badge>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Account</dt>
              <dd>{account?.username || "Current local account"}</dd>
            </div>
            <div>
              <dt>Authority</dt>
              <dd>Owner-scoped bearer session</dd>
            </div>
            <div>
              <dt>Session storage</dt>
              <dd>This browser; hashed sessions on the local runtime</dd>
            </div>
          </dl>
          <p>
            Sign out from the top bar to revoke all local sessions for this
            account. Provider keys are not browser session credentials. No
            hosted account is required.
          </p>
        </article>
        <article id="providers">
          <span className="eyebrow">CONNECTIONS</span>
          <h2>Model provider configuration</h2>
          <p>
            Register OpenAI-compatible, Ollama or custom HTTP endpoints.
            Credentials belong in the runner environment as{" "}
            <code>PRAXIS_MODEL_API_KEY</code>, never in registry metadata,
            prompts or this interface.
          </p>
          <Link className="button secondary" to="/targets">
            Manage registered targets <Icon name="arrow" size={15} />
          </Link>
          <p>
            Deterministic providers are explicitly labeled fixtures. Test each
            endpoint's connection before evaluating.
          </p>
        </article>
        <article id="storage">
          <span className="eyebrow">PERSISTENCE</span>
          <h2>Workspace storage</h2>
          <dl className="metadata-list">
            <div>
              <dt>Default database</dt>
              <dd>
                <code>.praxis/praxis.sqlite</code>
              </dd>
            </div>
            <div>
              <dt>Uploaded objects</dt>
              <dd>
                Private <code>objects/</code> directory beside the selected
                database
              </dd>
            </div>
            <div>
              <dt>Override</dt>
              <dd>
                <code>PRAXIS_DB</code> on the local process
              </dd>
            </div>
          </dl>
          <p>
            These are documented defaults, not a filesystem probe. The browser
            cannot inspect your configured path or available disk space. Keep
            the database and objects together, on a qualified private POSIX
            filesystem.
          </p>
        </article>
        <article id="recovery">
          <span className="eyebrow">RECOVERY</span>
          <h2>Backup & restore</h2>
          <Badge tone="warning">CLI operation · stop the runtime first</Badge>
          <p>
            There is no backup API or browser file transfer. Run the reviewed
            commands in the environment hosting Praxis, using the actual
            database path and a new private destination. Never overwrite the
            active workspace.
          </p>
          <CodeBlock
            label="Local snapshot, verification and new-directory restore"
            value={recoveryCommands}
          />
          <p>
            Backups include private account/session data. Keep them out of Git.
            Verify object hashes, ownership and run records, restart the
            restored workspace, and retain the original copy. Windows is not
            qualified for this filesystem contract.
          </p>
          <Link className="text-link" to="/docs#recovery">
            Read the recovery checklist <Icon name="arrow" size={15} />
          </Link>
        </article>
        <article id="runtime">
          <div className="section-heading">
            <div>
              <span className="eyebrow">DIAGNOSTICS</span>
              <h2>Local runtime</h2>
            </div>
            <Badge tone={health?.ok ? "success" : "neutral"}>
              {health?.ok ? "Health request succeeded" : "Not verified"}
            </Badge>
          </div>
          {error ? (
            <p role="status">{error}</p>
          ) : health ? (
            <CodeBlock label="Actual /api/health response" value={health} />
          ) : (
            <p role="status">Checking the local runtime…</p>
          )}
          <p>
            Health confirms API reachability, not model capability, provider
            availability or task success.
          </p>
        </article>
        <article id="preferences">
          <span className="eyebrow">APPEARANCE</span>
          <h2>Application preferences</h2>
          <p>
            Dark/light theme and sidebar preference stay in this browser. Use
            Ctrl/Cmd-K to navigate commands and loaded records.
          </p>
          <button
            className="secondary"
            onClick={() =>
              window.dispatchEvent(new Event("praxis-toggle-theme"))
            }
          >
            <Icon name="sun" size={16} />
            Switch appearance
          </button>
        </article>
      </div>
    </div>
  );
}
