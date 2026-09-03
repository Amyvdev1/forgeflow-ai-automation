#!/usr/bin/env sh
set -eu

base_url="${FORGEFLOW_WEB_URL:-http://localhost:8080}"
workflow_id="${FORGEFLOW_WORKFLOW_ID:-wf_feedback_triage}"

wait_for() {
  url="$1"
  label="$2"
  attempt=1
  while [ "$attempt" -le 20 ]; do
    if wget -q -O /dev/null "$url"; then
      printf '%s is reachable at %s\n' "$label" "$url"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  printf '%s did not become reachable at %s\n' "$label" "$url" >&2
  return 1
}

wait_for "$base_url/" "ForgeFlow web"
wait_for "$base_url/health" "ForgeFlow proxied health endpoint"

response="$(wget -q -O - \
  --header='Content-Type: application/json' \
  --post-data='{"input":"A customer cannot save an urgent request.","use_ai":false}' \
  "$base_url/api/workflows/$workflow_id/runs")"

printf '%s' "$response" | grep -q '"execution_mode":"deterministic"'
printf '%s' "$response" | grep -q '"status":"completed"'
printf 'ForgeFlow same-origin workflow smoke test passed.\n'
