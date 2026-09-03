"""ForgeFlow AI Automation API.

Personal portfolio demonstration: a small, documented workflow service with
explicit state, durable execution history, deterministic fallback behavior,
and an optional Gemini adapter that is activated only when configured.
"""

from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DATABASE_PATH = Path(os.getenv("FORGEFLOW_DB", "forgeflow.db"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield

app = FastAPI(
    title="ForgeFlow AI Automation API",
    version="0.1.0",
    description="Personal portfolio demonstration of reliable, human-reviewable AI workflow execution.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=8, max_length=280)
    prompt: str = Field(min_length=10, max_length=1200)
    tags: list[str] = Field(default_factory=list, max_length=6)
    enabled: bool = True


class WorkflowRunRequest(BaseModel):
    input: str = Field(min_length=3, max_length=6000)
    use_ai: bool = False


class WorkflowRecord(BaseModel):
    id: str
    name: str
    description: str
    prompt: str
    tags: list[str]
    enabled: bool
    created_at: str


class RunRecord(BaseModel):
    id: str
    workflow_id: str
    workflow_name: str
    status: Literal["completed", "degraded"]
    execution_mode: Literal["deterministic", "gemini", "deterministic_fallback"]
    input: str
    result: dict
    error_message: str | None
    created_at: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection() -> Generator[sqlite3.Connection, None, None]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_database() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workflows (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              description TEXT NOT NULL,
              prompt TEXT NOT NULL,
              tags_json TEXT NOT NULL,
              enabled INTEGER NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS workflow_runs (
              id TEXT PRIMARY KEY,
              workflow_id TEXT NOT NULL,
              workflow_name TEXT NOT NULL,
              status TEXT NOT NULL,
              execution_mode TEXT NOT NULL,
              input TEXT NOT NULL,
              result_json TEXT NOT NULL,
              error_message TEXT,
              created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_runs_created_at ON workflow_runs(created_at DESC);
            """
        )
        count = conn.execute("SELECT COUNT(*) AS count FROM workflows").fetchone()["count"]
        if count == 0:
            for workflow in default_workflows():
                conn.execute(
                    """INSERT INTO workflows (id, name, description, prompt, tags_json, enabled, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        workflow["id"],
                        workflow["name"],
                        workflow["description"],
                        workflow["prompt"],
                        json.dumps(workflow["tags"]),
                        int(workflow["enabled"]),
                        workflow["created_at"],
                    ),
                )


def default_workflows() -> list[dict]:
    created_at = "2026-09-03T00:00:00+00:00"
    return [
        {
            "id": "wf_feedback_triage",
            "name": "Feedback triage",
            "description": "Structures raw customer feedback into a reviewable action brief.",
            "prompt": "Identify theme, urgency, owner suggestion, and a concise next action. Preserve uncertainty.",
            "tags": ["support", "operations", "review"],
            "enabled": True,
            "created_at": created_at,
        },
        {
            "id": "wf_content_brief",
            "name": "Content brief organizer",
            "description": "Converts an unstructured request into a bilingual delivery brief.",
            "prompt": "Extract audience, objective, deliverables, review questions, and missing information.",
            "tags": ["content", "bilingual", "handoff"],
            "enabled": True,
            "created_at": created_at,
        },
    ]


def serialize_workflow(row: sqlite3.Row) -> WorkflowRecord:
    return WorkflowRecord(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        prompt=row["prompt"],
        tags=json.loads(row["tags_json"]),
        enabled=bool(row["enabled"]),
        created_at=row["created_at"],
    )


def serialize_run(row: sqlite3.Row) -> RunRecord:
    return RunRecord(
        id=row["id"],
        workflow_id=row["workflow_id"],
        workflow_name=row["workflow_name"],
        status=row["status"],
        execution_mode=row["execution_mode"],
        input=row["input"],
        result=json.loads(row["result_json"]),
        error_message=row["error_message"],
        created_at=row["created_at"],
    )


def deterministic_result(workflow: WorkflowRecord, text: str) -> dict:
    words = [word.strip(".,!?;:\n").lower() for word in text.split() if word.strip(".,!?;:\n")]
    high_signal = [word for word in words if word in {"broken", "urgent", "error", "cannot", "failed", "bug", "help"}]
    priority = "high" if high_signal else "standard"
    return {
        "summary": " ".join(text.split())[:280],
        "priority": priority,
        "detected_signals": sorted(set(high_signal)) or ["manual review recommended"],
        "recommended_next_action": f"Review the input against the {workflow.name.lower()} criteria before sending or automating a downstream action.",
        "review_checkpoint": "A human should approve the output before external delivery.",
        "input_word_count": len(words),
    }


def gemini_result(workflow: WorkflowRecord, text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    prompt = (
        "You are an automation assistant. Return only valid JSON with keys summary, priority, "
        "detected_signals, recommended_next_action, review_checkpoint. Do not claim certainty "
        "that is not supported by the input.\n\n"
        f"Workflow: {workflow.name}\nInstructions: {workflow.prompt}\nInput: {text}"
    )
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}",
        data=json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode())
        text_output = payload["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text_output)
        return {
            "summary": str(parsed.get("summary", ""))[:600],
            "priority": str(parsed.get("priority", "standard"))[:40],
            "detected_signals": parsed.get("detected_signals", []),
            "recommended_next_action": str(parsed.get("recommended_next_action", "Human review required."))[:600],
            "review_checkpoint": str(parsed.get("review_checkpoint", "Human review required."))[:600],
        }
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc


@app.get("/health")
def health() -> dict:
    return {"service": "forgeflow-api", "status": "ok", "timestamp": utc_now()}


@app.get("/api/workflows", response_model=list[WorkflowRecord])
def list_workflows() -> list[WorkflowRecord]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM workflows ORDER BY created_at ASC").fetchall()
    return [serialize_workflow(row) for row in rows]


@app.post("/api/workflows", response_model=WorkflowRecord, status_code=status.HTTP_201_CREATED)
def create_workflow(payload: WorkflowCreate) -> WorkflowRecord:
    record = WorkflowRecord(id=f"wf_{uuid4().hex[:12]}", created_at=utc_now(), **payload.model_dump())
    with connection() as conn:
        conn.execute(
            """INSERT INTO workflows (id, name, description, prompt, tags_json, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (record.id, record.name, record.description, record.prompt, json.dumps(record.tags), int(record.enabled), record.created_at),
        )
    return record


@app.post("/api/workflows/{workflow_id}/runs", response_model=RunRecord, status_code=status.HTTP_201_CREATED)
def run_workflow(workflow_id: str, payload: WorkflowRunRequest) -> RunRecord:
    with connection() as conn:
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow = serialize_workflow(row)
    if not workflow.enabled:
        raise HTTPException(status_code=409, detail="Workflow is disabled")

    execution_mode: Literal["deterministic", "gemini", "deterministic_fallback"] = "deterministic"
    run_status: Literal["completed", "degraded"] = "completed"
    error_message: str | None = None
    if payload.use_ai:
        try:
            result = gemini_result(workflow, payload.input)
            execution_mode = "gemini"
        except RuntimeError as exc:
            result = deterministic_result(workflow, payload.input)
            execution_mode = "deterministic_fallback"
            run_status = "degraded"
            error_message = str(exc)
    else:
        result = deterministic_result(workflow, payload.input)

    run = RunRecord(
        id=f"run_{uuid4().hex[:12]}",
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        status=run_status,
        execution_mode=execution_mode,
        input=payload.input,
        result=result,
        error_message=error_message,
        created_at=utc_now(),
    )
    with connection() as conn:
        conn.execute(
            """INSERT INTO workflow_runs (id, workflow_id, workflow_name, status, execution_mode, input, result_json, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run.id, run.workflow_id, run.workflow_name, run.status, run.execution_mode, run.input, json.dumps(run.result), run.error_message, run.created_at),
        )
    return run


@app.get("/api/runs", response_model=list[RunRecord])
def list_runs() -> list[RunRecord]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 30").fetchall()
    return [serialize_run(row) for row in rows]
