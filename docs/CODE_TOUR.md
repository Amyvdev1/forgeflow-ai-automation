# ForgeFlow AI Automation — Engineering Code Tour

This guide follows one workflow execution from the dashboard input to the stored result. ForgeFlow is intentionally small enough to inspect end to end while still showing a real full-stack boundary.

## 1. API lifecycle and storage initialization

`backend/app/main.py` creates the FastAPI application with a lifespan hook. On startup, `initialize_database` creates the `workflows` and `workflow_runs` SQLite tables, creates a reverse-time index for recent runs, and seeds two workflow definitions if the store is empty. The database path is environment-configurable through `FORGEFLOW_DB`.

## 2. Typed request and response contracts

`WorkflowCreate` and `WorkflowRunRequest` constrain the acceptable workflow fields and text input lengths. `WorkflowRecord` and `RunRecord` make the returned data explicit. In particular, `RunRecord` limits status to `completed` or `degraded`, and limits execution mode to `deterministic`, `gemini`, or `deterministic_fallback`. Those fields make the automation path visible to the caller.

## 3. Persistence and serialization

The `connection` context manager opens and closes SQLite connections while committing successful work. Workflow tags and run results are stored as JSON fields, then converted back to typed records through serializer helpers. The API records the input, result, mode, error message when relevant, and UTC creation time for each run.

## 4. Deterministic workflow path

`deterministic_result` is the default execution path. It cleans words, checks a small fixed list of high-signal terms, assigns `high` or `standard` priority, returns a bounded summary, includes a next action, and always adds a human-review checkpoint. This path keeps the demo runnable without a model key and makes its logic inspectable.

## 5. Optional Gemini adapter and fallback

`gemini_result` runs only if a caller requests AI and `GEMINI_API_KEY` is present. It sends a JSON-output prompt to the configured Gemini model and normalizes the response into the same result shape. If configuration, provider, response-shape, or JSON parsing fails in the handled error path, `run_workflow` records a `degraded` run with `execution_mode: deterministic_fallback` and preserves the reason. A user can therefore distinguish a successful model run from a fallback result.

## 6. REST routes

`GET /health` returns a lightweight health response. The workflow list and create routes expose local definitions. `POST /api/workflows/{workflow_id}/runs` checks that the workflow exists and is enabled before executing the correct path and persisting the run. `GET /api/runs` returns up to 30 records ordered from most recent to oldest.

## 7. Dashboard behavior

`frontend/src/App.tsx` uses a small typed `request` helper. On load, it fetches workflows and runs in parallel. The operator can choose a workflow, enter text, select the optional AI mode, and run the workflow. Returned records are prepended to the in-memory history view. The UI renders the execution mode, status, resulting priority, next action, and fallback detail, so an AI setting does not become an invisible implementation detail.

## 8. Validation, containers, and CI

`backend/tests/test_main.py` verifies health, deterministic workflow execution plus stored history, and missing-key AI fallback. The GitHub Actions workflow runs backend pytest and a separate Node 22/pnpm type-check/build job. `docker-compose.yml` defines the API service with a named volume for local SQLite data and a static frontend image served through Nginx. `.env.example` documents optional settings without storing secrets.

## Scope statement

This project evidences a local full-stack workflow demo with SQLite persistence, API validation, typed UI state, optional model use, explicit fallback records, focused tests, containers, and CI configuration. It does not represent an enterprise AI platform or claim production deployment, security certification, external delivery, customer outcomes, or formal reliability guarantees.
