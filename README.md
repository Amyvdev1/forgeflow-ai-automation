# ForgeFlow AI Automation

> **AI automation systems with explicit execution state, deterministic fallback, persistence, and human review.**

[Source](https://github.com/Amyvdev1/forgeflow-ai-automation) · [Amy Villa on GitHub](https://github.com/Amyvdev1) · [Contact](mailto:amyv.dev@gmail.com)

## What it solves

ForgeFlow turns unstructured input into a **reviewable next action** while keeping the execution path visible: deterministic logic, optional AI-provider use, degraded fallback, persisted history, and a human decision point.

## Why it exists

Automation demos often present a generated answer without showing how it was produced or what happened when a provider failed. ForgeFlow is designed around the opposite principle: the interface and API expose execution mode, persisted state, fallback behavior, and the checkpoint where human judgment remains necessary.

## Live demo

**Production deployment: pending.** The repository includes a complete local browser/API path and Docker Compose topology. The demo does not require an AI key: the deterministic path works without external services, and the optional Gemini adapter is used only when explicitly enabled.

## Architecture

```text
React + TypeScript dashboard
        │  REST: workflows, runs, health
        ▼
FastAPI service ───────── SQLite workflow + run records
        │
        ├── deterministic result path
        └── optional Gemini adapter
                  │
                  └── handled failure → persisted degraded fallback
```

### Stack

**React · TypeScript · FastAPI · Pydantic · SQLite · Docker/Compose · Nginx · Vitest · pytest · GitHub Actions**

## Key engineering decisions

| Decision | Why it is here |
|---|---|
| **Deterministic execution is always available** | The product still behaves predictably when no external provider is configured. |
| **AI provider is opt-in** | The system never implies that a model ran unless the operator requested it and credentials are present. |
| **Execution mode is persisted** | A reviewer can distinguish deterministic, provider-backed, and degraded-fallback results after the run completes. |
| **Fallback is visible, not silent** | Provider/parsing failures become a `degraded` result with recorded fallback state and error context. |
| **SQLite persistence** | Run history survives request boundaries and makes state inspectable without adding an ORM layer. |
| **Human review remains explicit** | Automation produces a next-action brief; it does not pretend to replace judgment. |
| **Same-origin local delivery** | Nginx serves the built client and proxies API requests in Compose, exercising a realistic browser-to-service path locally. |

## Failure behavior

ForgeFlow treats failure as product state:

- missing `GEMINI_API_KEY` → persisted deterministic fallback,
- handled provider/parsing error → `degraded` result with fallback context,
- invalid workflow/input → typed FastAPI/Pydantic error boundary,
- client request failure → visible interface error instead of silent success,
- health or proxy failure → reproducible local checks fail rather than masking the delivery problem.

A workflow can be useful without pretending it is autonomous. The result always exposes how it was produced.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Small service health response. |
| `GET` | `/api/workflows` | Reads available workflow definitions. |
| `POST` | `/api/workflows` | Creates a validated local workflow definition. |
| `POST` | `/api/workflows/{workflow_id}/runs` | Executes a workflow and stores an auditable result. |
| `GET` | `/api/runs` | Reads recent persisted execution records. |

## Testing & CI

```bash
cd backend && pytest -q
cd frontend && pnpm test:run && pnpm check && pnpm build
```

The backend suite covers health, deterministic execution with persistence, and missing-key AI fallback. The frontend suite covers workflow loading, explicit execution-mode language, and a submitted deterministic run. GitHub Actions runs backend tests plus frontend tests, TypeScript checking, and the production build on pushes and pull requests.

For the local two-service delivery path:

```bash
cp .env.example .env
docker compose up --build
./scripts/smoke-compose.sh
```

The smoke check loads the Nginx-served dashboard, reaches the proxied health endpoint, and posts a deterministic workflow run through the same-origin `/api` path.

## Security / evidence boundaries

ForgeFlow is an **independent portfolio engineering sample**, not a production service. It does not claim customer data, autonomous external delivery, enterprise-scale infrastructure, formal security/compliance certification, provider uptime guarantees, rate limiting, queues, external observability, production deployment, or client outcomes.

The Gemini key is never committed, and the service does not call an AI provider unless an operator explicitly enables the adapter.

## 5-minute code review path

1. [`backend/app/main.py`](backend/app/main.py) — typed API models, SQLite schema, deterministic execution, optional Gemini adapter, fallback behavior, and routes.
2. [`backend/tests/test_main.py`](backend/tests/test_main.py) — health, persistence, and missing-key fallback behavior.
3. [`frontend/src/App.tsx`](frontend/src/App.tsx) — workflow selection, API request path, explicit execution-mode state, history, and errors.
4. [`frontend/src/App.test.tsx`](frontend/src/App.test.tsx) — focused interface behavior.
5. [`docker-compose.yml`](docker-compose.yml) — local API + Nginx delivery topology.
6. [`scripts/smoke-compose.sh`](scripts/smoke-compose.sh) — browser-to-API delivery smoke path.
7. [`docs/INTEGRATION_WALKTHROUGH.md`](docs/INTEGRATION_WALKTHROUGH.md) — consumer-oriented request/response and fallback walkthrough.

For a deeper source tour, read [`docs/CODE_TOUR.md`](docs/CODE_TOUR.md).

## Run locally

### Development

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

Open `http://localhost:5174`.

### Docker Compose

```bash
cp .env.example .env
# Add GEMINI_API_KEY only when intentionally testing the optional AI adapter.
docker compose up --build
```

Open `http://localhost:8080`.

---

Built by **Amy Villa** as an inspectable AI Automation Systems engineering sample.
