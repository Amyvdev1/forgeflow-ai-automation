# ForgeFlow AI Automation

**A personal full-stack portfolio demonstration of reliable, human-reviewable AI workflow execution.**

ForgeFlow turns an unstructured input into a reviewable action brief. It intentionally keeps the system boundary visible: every run records its execution mode, stores a durable result, and requires a human checkpoint before any future external delivery.

> This repository is an independent code sample. It is **not** a production service, customer deployment, certified security control, or a claim of enterprise scale.

## Why this project exists

This project demonstrates the engineering decisions behind practical AI automation:

- A responsive **React + TypeScript** control plane for selecting workflows, submitting inputs, inspecting outputs, and viewing run history.
- A documented **FastAPI + SQLite** REST service with structured request validation, seeded workflows, durable run records, explicit states, and an operational health endpoint.
- An optional **Gemini API adapter** that is used only when configured. If an AI call is unavailable, the API returns a transparent deterministic fallback rather than pretending the model ran.
- A documented human-review checkpoint so a generated output does not become an automatic external action.
- **pytest** API coverage, a GitHub Actions CI workflow, Dockerfiles, and Docker Compose for reproducible local setup.

## Architecture

```text
React / TypeScript dashboard
        |
        | REST: workflows, workflow runs, health
        v
FastAPI service ---- SQLite durable store
        |
        +---- Optional Gemini adapter (only with GEMINI_API_KEY)
        |
        +---- Deterministic fallback + run status / error record
```

## Local setup

### Option A — run the services in development mode

```bash
# terminal 1
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# terminal 2
cd frontend
corepack enable
pnpm install
pnpm dev
```

Open `http://localhost:5174`. The Vite proxy forwards `/api` calls to the FastAPI service.

### Option B — run with Docker Compose

```bash
cp .env.example .env
# Add GEMINI_API_KEY only if you want to test the optional adapter.
docker compose up --build
```

Open the static dashboard at `http://localhost:8080` and the API health check at `http://localhost:8000/health`.

## Optional Gemini integration

1. Copy `.env.example` to `.env`.
2. Set `GEMINI_API_KEY` locally. Never commit a key.
3. In the dashboard, enable **Use Gemini adapter if configured**.

The backend calls `gemini-2.5-flash` by default and requests JSON-shaped output. If the key is absent or the provider fails, the response is marked `degraded` with `execution_mode: deterministic_fallback`, preserving the reason in the run record.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Minimal service health signal |
| `GET` | `/api/workflows` | Read workflow definitions |
| `POST` | `/api/workflows` | Create a validated workflow definition |
| `POST` | `/api/workflows/{workflow_id}/runs` | Execute a workflow and persist an auditable result |
| `GET` | `/api/runs` | Review recent recorded runs |

## Quality checks

```bash
cd backend && pytest -q
cd frontend && pnpm check && pnpm build
```

The repository’s GitHub Actions workflow runs the API tests plus the frontend type-check and production build on pushes and pull requests.

The current API tests cover the health signal, deterministic workflow execution, durable run history, and the transparent fallback state when an AI key is unavailable. Manual local verification should still be performed before using any changed workflow with real content.

## What this code sample does not claim

- It does **not** claim production AI reliability, autonomous external delivery, real customer data, enterprise monitoring, cloud-scale infrastructure, Kubernetes, or formal security/compliance certification.
- It does **not** include a hard-coded API key or send data to an AI provider unless an operator intentionally configures the optional adapter.
- It does **not** replace human approval for consequential work.

## Stack

React · TypeScript · Vite · FastAPI · Pydantic · SQLite · REST · pytest · Docker · Docker Compose · GitHub Actions · optional Gemini API

---

Created as a public portfolio code sample by [Amy Villa](https://github.com/Amyvdev1).
