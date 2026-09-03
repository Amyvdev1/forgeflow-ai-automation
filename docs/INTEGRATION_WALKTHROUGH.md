# ForgeFlow — API Integration Walkthrough

ForgeFlow is a **personal full-stack code sample** that demonstrates a narrow integration pattern: a browser UI submits a structured workflow request to a typed FastAPI API, the API records an explicit execution mode and result, and a later caller can retrieve the local run history. This guide is intended for technical conversations about API contracts, integration boundaries, fallback behavior, and the work that would still be required for production delivery.

## Start with the contract

The browser-facing endpoints live under `/api`. The local dashboard uses the same-origin path in the Docker Compose setup, while Vite proxies the path during development.

| Endpoint | Purpose | Important behavior |
|---|---|---|
| `GET /health` | Checks that the FastAPI service responds. | Returns a small service/status/timestamp payload. |
| `GET /api/workflows` | Lists the local workflow definitions. | Used by the dashboard to populate the workflow selector. |
| `POST /api/workflows` | Creates a validated local workflow. | Enforces typed field lengths and returns `201 Created`. |
| `POST /api/workflows/{workflow_id}/runs` | Executes one workflow request. | Returns an explicit execution mode and stores the local run record. |
| `GET /api/runs` | Reads the latest local history. | Returns up to 30 persisted records, newest first. |

## Walk through one request

Start the API locally, or start the Compose topology described in the [README](../README.md). Then choose a known workflow ID from `GET /api/workflows`.

```bash
curl -s http://127.0.0.1:8000/api/workflows
```

A deterministic run is deliberately available without an AI provider key:

```bash
curl -s \
  -X POST http://127.0.0.1:8000/api/workflows/wf_feedback_triage/runs \
  -H 'Content-Type: application/json' \
  -d '{"input":"A customer cannot save an urgent request.","use_ai":false}'
```

The response identifies both the result and the execution path. A representative response shape is:

```json
{
  "status": "completed",
  "execution_mode": "deterministic",
  "result": {
    "priority": "high",
    "recommended_next_action": "Review the input against the feedback triage criteria before sending or automating a downstream action.",
    "review_checkpoint": "A human should approve the output before external delivery."
  }
}
```

The key design choice is that `execution_mode` is never inferred from marketing language. It is one of `deterministic`, `gemini`, or `deterministic_fallback`, so an API consumer can distinguish a configured model call from a local fallback.

## Error and integration behavior

| Situation | API behavior | What an integrating client should do |
|---|---|---|
| Unknown workflow ID | `404 Workflow not found` | Refresh workflow definitions or present a clear configuration error. |
| Disabled workflow | `409 Workflow is disabled` | Do not retry blindly; surface that an operator needs to re-enable it. |
| Invalid request body | FastAPI validation response | Keep client inputs within the documented constraints and show the field-level error. |
| `use_ai: true` without a provider key | `201` with `status: degraded` and `execution_mode: deterministic_fallback` | Treat the result as a successful local fallback, expose the reason, and retain the required human review. |
| Handled provider/response failure | `201` with the same explicit fallback mode | Avoid representing the fallback as a successful model result. |

These patterns are verified by focused API tests. See [`backend/tests/test_main.py`](../backend/tests/test_main.py) and the repository CI workflow.

## Delivery boundary

The Docker Compose configuration exposes the browser app on port `8080` and routes same-origin `/api/*` and `/health` paths through Nginx to the FastAPI service. The repository includes a local smoke script for that path:

```bash
./scripts/smoke-compose.sh
```

This documents a **local development/demonstration topology**. It is not a claim of hosted production deployment, production observability, rate limiting, retries, enterprise authentication, customer integrations, or a service-level agreement.

## Questions this sample supports

A reviewer can use this project to discuss:

- how a browser UI consumes a typed REST API;
- why an execution mode and degradation state should be explicit in the response contract;
- how SQLite run history makes an execution path inspectable locally;
- how an operator-facing workflow can retain a human review point; and
- what needs to change before connecting an API to a real identity provider, external system, or production environment.

For the code-level path, continue to the [engineering code tour](CODE_TOUR.md). For the explicit scope boundary, see the [README](../README.md#intentional-boundaries).
