# ForgeFlow AI Automation

> **A full-stack workflow control-plane demonstration that turns unstructured input into a reviewable next action—without hiding how the result was produced.**

[Source repository](https://github.com/Amyvdev1/forgeflow-ai-automation) · [Amy Villa on GitHub](https://github.com/Amyvdev1) · [Portfolio](https://amy-villa-signal-gallery.vercel.app/) · [Contact Amy](mailto:amyv.dev@gmail.com)

ForgeFlow is an independent full-stack code sample built to demonstrate practical AI automation patterns: clear input contracts, durable run history, explicit execution modes, optional model use, safe fallback behavior, and a visible human review checkpoint.

> A workflow can be useful without pretending it is autonomous. ForgeFlow records whether a run used deterministic logic, successfully used the configured Gemini adapter, or fell back because the optional AI adapter was unavailable.

## System at a glance

```text
React + TypeScript dashboard
        │  REST: workflows, runs, health
        ▼
FastAPI service ───────── SQLite workflow + run records
        │
        ├── deterministic result path
        └── optional Gemini adapter
                  │
                  └── handled failure → recorded degraded fallback
```

## What Amy built

| Layer | What the code does |
|---|---|
| **Control plane** | React dashboard loads workflows and recent history, selects a workflow, accepts text input, requests optional AI use, and renders status, priority, next action, and fallback information. |
| **API contract** | FastAPI routes and Pydantic models validate workflow and input fields, create workflows, execute runs, and return typed records. |
| **SQLite persistence** | The backend creates workflow/run tables, seeds two initial workflow definitions, writes execution records, and reads the most recent run history. |
| **Deterministic path** | Local logic normalizes input, detects a small documented high-signal vocabulary, derives priority, and returns an action brief plus a human-review checkpoint. |
| **Optional AI adapter** | A direct Gemini API integration is requested only when an operator enables it and configures `GEMINI_API_KEY`; the model is never presumed to have run. |
| **Transparent fallback** | Missing credentials or handled provider/parsing failures produce a persisted `degraded` result with `deterministic_fallback` and an error message. |
| **Reproducible delivery** | Dockerfiles, a same-origin Nginx/Compose topology, `.env.example`, a local smoke check, and GitHub Actions document the local services and verification commands. |

## Code map

| Source area | What it explains |
|---|---|
| [`backend/app/main.py`](backend/app/main.py) | FastAPI lifecycle, CORS, Pydantic models, SQLite schema, seed data, serializers, deterministic workflow logic, Gemini adapter, fallback behavior, and API routes. |
| [`backend/tests/test_main.py`](backend/tests/test_main.py) | Tests for health, deterministic execution with persisted history, and missing-key AI fallback. |
| [`frontend/src/App.tsx`](frontend/src/App.tsx) | Dashboard state, REST helper, workflow selection, form submit behavior, metrics, run-history cards, error feedback, and the AI toggle. |
| [`frontend/src/styles.css`](frontend/src/styles.css) | Focus-visible treatment, responsive panels, reduced-motion rules, and the control-plane visual language. |
| [`frontend/src/App.test.tsx`](frontend/src/App.test.tsx) | Focused interface checks that verify workflow loading, explicit execution-mode language, and a deterministic run request. |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Separate backend and frontend GitHub Actions jobs for pytest plus interface tests, TypeScript, and production-build checks. |
| [`docker-compose.yml`](docker-compose.yml) | The local two-service topology: FastAPI/SQLite API, health checks, and an Nginx-served frontend that proxies browser API requests. |
| [`scripts/smoke-compose.sh`](scripts/smoke-compose.sh) | A repeatable local browser-to-API smoke check for the Nginx proxy path. |

Read the detailed [engineering code tour](docs/CODE_TOUR.md) for the flow from an input to a persisted run record.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Small service health response. |
| `GET` | `/api/workflows` | Reads available workflow definitions. |
| `POST` | `/api/workflows` | Creates a validated local workflow definition. |
| `POST` | `/api/workflows/{workflow_id}/runs` | Executes a workflow and stores an auditable result. |
| `GET` | `/api/runs` | Reads the latest persisted execution records. |

## Local setup

### Development mode

```bash
# Terminal 1 — API
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — web dashboard
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:5174`. Vite proxies `/api` requests to the FastAPI service.

### Docker Compose

```bash
cp .env.example .env
# Add GEMINI_API_KEY only when intentionally testing the optional AI adapter.
docker compose up --build
```

The dashboard is served at `http://localhost:8080`. In this local container setup, Nginx serves the built React app and proxies same-origin `/api/*` and `/health` requests to the FastAPI service. API health also remains directly available at `http://localhost:8000/health` for local inspection.

After both services report healthy, run the reproducible browser-to-API smoke check:

```bash
./scripts/smoke-compose.sh
```

The check loads the Nginx-served dashboard, reaches the proxied health endpoint, and posts a deterministic workflow run through the same-origin `/api` path. This validates the **local Docker delivery topology**; it does not claim a hosted production deployment.

## Verification

```bash
cd backend && pytest -q
cd frontend && pnpm test:run && pnpm check && pnpm build
```

The local API suite covers health, deterministic run persistence, and the missing-key fallback path. The frontend suite covers initial workflow loading, explicit execution-mode language, and a submitted deterministic run. The public [GitHub Actions workflow](https://github.com/Amyvdev1/forgeflow-ai-automation/actions) runs backend tests plus frontend interface tests, type-checking, and production build checks on pushes and pull requests.

## Intentional boundaries

ForgeFlow is a **personal portfolio code sample**, not a production service. It does not claim customer data, autonomous external delivery, enterprise-scale infrastructure, formal security/compliance certification, provider uptime guarantees, rate limiting, retries, observability, external connectors, or production deployment. The Gemini key is never committed and the service does not call an AI provider unless an operator explicitly enables the optional adapter.

---

Created by **Amy Villa** to demonstrate full-stack engineering, transparent AI automation, and human-centered workflow design.
