import { useState } from "react";
import { Badge, CodeBlock, Icon } from "./ui";
export default function ArtifactInspector({ items }: { items: any[] }) {
  const [selected, S] = useState("");
  const current = items.find((x) => x.id === selected) || items[0];
  return (
    <div className="artifact-workspace">
      <nav className="artifact-list" aria-label="Artifact files">
        <div className="section-label">
          LOADED ARTIFACTS <span>{items.length}</span>
        </div>
        {items.map((x) => (
          <button
            className={x.id === current?.id ? "selected" : ""}
            onClick={() => S(x.id)}
            key={x.id}
          >
            <Icon name="file" />
            <span>
              {x.filename || x.task_id || x.id}
              <small>
                {x.mime || "Unknown type"} · {x.size ?? "Unknown"} bytes
              </small>
            </span>
          </button>
        ))}
      </nav>
      {current ? (
        <article className="artifact-preview">
          <div className="section-heading">
            <div>
              <span className="eyebrow">ARTIFACT INSPECTOR</span>
              <h2>
                {current.filename || current.task_id || "Artifact evidence"}
              </h2>
            </div>
            <Badge tone={current.trust === "demo" ? "warning" : "neutral"}>
              {current.trust || "self-reported"}
            </Badge>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Identifier</dt>
              <dd>
                <code>{current.id}</code>
              </dd>
            </div>
            <div>
              <dt>MIME</dt>
              <dd>{current.mime}</dd>
            </div>
            <div>
              <dt>SHA256</dt>
              <dd>
                <code>{current.sha256 || current.sha || "Not recorded"}</code>
              </dd>
            </div>
            <div>
              <dt>Size</dt>
              <dd>{current.size ?? "Not recorded"} bytes</dd>
            </div>
          </dl>
          <div className="preview-canvas">
            {current.data_url && current.mime?.startsWith("image/") ? (
              <img
                src={current.data_url}
                alt={current.filename || "Evaluation screenshot"}
              />
            ) : current.data_url && current.mime === "audio/wav" ? (
              <audio controls src={current.data_url} />
            ) : current.data_url &&
              ["video/mp4", "video/webm"].includes(current.mime) ? (
              <video controls src={current.data_url} />
            ) : (
              <CodeBlock
                label="Inert content preview"
                value={
                  current.content || "Binary artifact; metadata shown above."
                }
              />
            )}
          </div>
          <p className="subtle">
            HTML is displayed as inert source. No uploaded executable content
            runs on the workspace origin.
          </p>
        </article>
      ) : (
        <article className="empty-state">
          <Icon name="box" size={30} />
          <h2>No matching artifacts</h2>
          <p>
            Upload evidence below or run an evaluation to preserve its outputs.
          </p>
        </article>
      )}
    </div>
  );
}
