import { FormEvent, useEffect, useMemo, useState } from "react";

type Workflow = {
  id: string;
  name: string;
  description: string;
  prompt: string;
  tags: string[];
  enabled: boolean;
};

type Run = {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: "completed" | "degraded";
  execution_mode: "deterministic" | "gemini" | "deterministic_fallback";
  input: string;
  result: {
    summary: string;
    priority: string;
    detected_signals: string[];
    recommended_next_action: string;
    review_checkpoint: string;
  };
  error_message: string | null;
  created_at: string;
};

const initialInput = "A customer says the export stopped working after their last update and they need a report before a client review tomorrow.";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init
  });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export default function App() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [input, setInput] = useState(initialInput);
  const [useAi, setUseAi] = useState(false);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = useMemo(
    () => workflows.find((workflow) => workflow.id === selectedId) ?? workflows[0],
    [selectedId, workflows]
  );

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [workflowData, runData] = await Promise.all([
        request<Workflow[]>("/api/workflows"),
        request<Run[]>("/api/runs")
      ]);
      setWorkflows(workflowData);
      setRuns(runData);
      if (!selectedId && workflowData[0]) setSelectedId(workflowData[0].id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to reach the local API.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function execute(event: FormEvent) {
    event.preventDefault();
    if (!selected || !input.trim()) return;
    setRunning(true);
    setError(null);
    try {
      const run = await request<Run>(`/api/workflows/${selected.id}/runs`, {
        method: "POST",
        body: JSON.stringify({ input, use_ai: useAi })
      });
      setRuns((existing) => [run, ...existing]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Workflow execution failed.");
    } finally {
      setRunning(false);
    }
  }

  const successfulRuns = runs.filter((run) => run.status === "completed").length;

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="ForgeFlow home">
          <span className="brand-mark">FF</span>
          <span>ForgeFlow<span className="brand-ai"> AI</span></span>
        </a>
        <div className="status-line"><span className="pulse" /> Workflow control plane <span className="slash">/</span> personal demo</div>
        <a className="source-link" href="https://github.com/Amyvdev1" target="_blank" rel="noreferrer">GitHub ↗</a>
      </header>

      <section className="hero" id="top">
        <div>
          <p className="eyebrow">Reliable automation, designed for review</p>
          <h1>Turn an unclear request into a <em>visible next step.</em></h1>
          <p className="lede">A personal full-stack demonstration of workflow execution, transparent AI fallbacks, persistent run history, and human approval points.</p>
        </div>
        <div className="signal-orb" aria-hidden="true"><span /><span /><span /></div>
      </section>

      <section className="metrics" aria-label="Workspace metrics">
        <article><span>Configured workflows</span><strong>{workflows.length || "—"}</strong><small>SQLite-backed definitions</small></article>
        <article><span>Recorded runs</span><strong>{runs.length}</strong><small>durable execution history</small></article>
        <article><span>Completed</span><strong>{successfulRuns}</strong><small>reviewable outputs</small></article>
        <article><span>Mode</span><strong>{useAi ? "AI ready" : "Safe"}</strong><small>explicit, not hidden</small></article>
      </section>

      <section className="workspace" aria-label="ForgeFlow workspace">
        <aside className="workflow-panel">
          <div className="panel-heading"><span>WORKFLOWS</span><button onClick={() => void refresh()} disabled={loading}>Refresh</button></div>
          {loading && <p className="empty">Loading the local control plane…</p>}
          {!loading && workflows.map((workflow) => (
            <button
              className={`workflow-card ${workflow.id === selected?.id ? "selected" : ""}`}
              key={workflow.id}
              onClick={() => setSelectedId(workflow.id)}
            >
              <span className="workflow-name">{workflow.name}</span>
              <span className="workflow-description">{workflow.description}</span>
              <span className="tag-row">{workflow.tags.map((tag) => <i key={tag}>{tag}</i>)}</span>
            </button>
          ))}
        </aside>

        <section className="run-panel">
          <div className="panel-heading"><span>EXECUTION BRIEF</span><span className="mode-label">{useAi ? "AI adapter requested" : "deterministic preview"}</span></div>
          {selected && <>
            <h2>{selected.name}</h2>
            <p className="prompt-note">{selected.prompt}</p>
            <form onSubmit={execute}>
              <label htmlFor="workflow-input">Input to structure</label>
              <textarea id="workflow-input" value={input} onChange={(event) => setInput(event.target.value)} rows={7} />
              <div className="form-footer">
                <label className="switch-row"><input type="checkbox" checked={useAi} onChange={(event) => setUseAi(event.target.checked)} /> Use Gemini adapter if configured</label>
                <button className="run-button" type="submit" disabled={running || !input.trim()}>{running ? "Running…" : "Run workflow →"}</button>
              </div>
            </form>
            <p className="boundary">The app records whether an AI request ran, fell back safely, or was not requested. It does not send anything externally without a future connector and human approval.</p>
          </>}
          {error && <p className="error" role="alert">{error}</p>}
        </section>

        <section className="history-panel">
          <div className="panel-heading"><span>RUN HISTORY</span><span>{runs.length} entries</span></div>
          {!runs.length && <p className="empty">Run a workflow to create an auditable result.</p>}
          {runs.slice(0, 4).map((run) => (
            <article className="run-card" key={run.id}>
              <div><span className={`run-status ${run.status}`}>{run.status}</span><span className="run-mode">{run.execution_mode.replaceAll("_", " ")}</span></div>
              <h3>{run.workflow_name}</h3>
              <p>{run.result.summary}</p>
              <dl>
                <div><dt>Priority</dt><dd>{run.result.priority}</dd></div>
                <div><dt>Next</dt><dd>{run.result.recommended_next_action}</dd></div>
              </dl>
              {run.error_message && <small className="fallback">Fallback detail: {run.error_message}</small>}
            </article>
          ))}
        </section>
      </section>

      <footer>
        <span>ForgeFlow AI Automation</span>
        <span>React · TypeScript · FastAPI · SQLite · optional Gemini adapter · Docker · CI</span>
        <span>Personal portfolio demo — not a production service.</span>
      </footer>
    </main>
  );
}
