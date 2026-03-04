#!/usr/bin/env bash
# =============================================================================
# scripts/healthcheck.sh
#
# Purpose:
#   Verify that all EndogenAI backing services are reachable and ready for
#   integration tests. Exits 0 only when ALL services pass their checks.
#
# Services checked:
#   - ChromaDB          (HTTP GET /api/v1/heartbeat)
#   - Ollama            (HTTP GET /api/tags + nomic-embed-text model present)
#   - OTel collector    (TCP port 4317 — gRPC OTLP endpoint)
#   - Prometheus        (HTTP GET /-/ready)
#
# Inputs:
#   Environment variables (all optional — defaults match docker-compose.yml):
#     CHROMADB_URL     default: http://localhost:8000
#     OLLAMA_URL       default: http://localhost:11434
#     OTEL_HOST        default: localhost
#     OTEL_GRPC_PORT   default: 4317
#     PROMETHEUS_URL   default: http://localhost:9090
#     OLLAMA_MODEL     default: nomic-embed-text
#
# Outputs:
#   Prints PASS/FAIL status per service.
#   Exits 0 if all services pass; exits 1 if any fail.
#
# Usage:
#   bash scripts/healthcheck.sh
#   # or with overrides:
#   OLLAMA_URL=http://ollama:11434 bash scripts/healthcheck.sh
#
# =============================================================================

set -euo pipefail

CHROMADB_URL="${CHROMADB_URL:-http://localhost:8000}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
OTEL_HOST="${OTEL_HOST:-localhost}"
OTEL_GRPC_PORT="${OTEL_GRPC_PORT:-4317}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
OLLAMA_MODEL="${OLLAMA_MODEL:-nomic-embed-text}"

PASS=0
FAIL=1
overall=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

check_http() {
  local label="$1"
  local url="$2"
  local expected_status="${3:-200}"

  local status
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")

  if [[ "$status" == "$expected_status" ]]; then
    echo "  [PASS] $label  ($url → HTTP $status)"
    return $PASS
  else
    echo "  [FAIL] $label  ($url → HTTP $status, expected $expected_status)"
    return $FAIL
  fi
}

check_tcp() {
  local label="$1"
  local host="$2"
  local port="$3"

  if nc -z -w 5 "$host" "$port" 2>/dev/null; then
    echo "  [PASS] $label  ($host:$port reachable)"
    return $PASS
  else
    echo "  [FAIL] $label  ($host:$port not reachable)"
    return $FAIL
  fi
}

# ---------------------------------------------------------------------------
# 1. ChromaDB
# ---------------------------------------------------------------------------
echo ""
echo "=== ChromaDB ==="
if ! check_http "ChromaDB heartbeat" "${CHROMADB_URL}/api/v1/heartbeat"; then
  overall=1
fi

# ---------------------------------------------------------------------------
# 2. Ollama — service reachability + model availability
# ---------------------------------------------------------------------------
echo ""
echo "=== Ollama ==="
if check_http "Ollama API" "${OLLAMA_URL}/api/tags"; then
  # Check that the required model is listed
  tags_json=$(curl -s --max-time 5 "${OLLAMA_URL}/api/tags" 2>/dev/null || echo '{}')
  if echo "$tags_json" | grep -q "\"${OLLAMA_MODEL}\""; then
    echo "  [PASS] Ollama model '${OLLAMA_MODEL}' is pulled"
  else
    echo "  [FAIL] Ollama model '${OLLAMA_MODEL}' is NOT pulled — run: ollama pull ${OLLAMA_MODEL}"
    overall=1
  fi
else
  overall=1
fi

# ---------------------------------------------------------------------------
# 3. OTel collector — gRPC endpoint (TCP port check)
# ---------------------------------------------------------------------------
echo ""
echo "=== OpenTelemetry Collector ==="
if ! check_tcp "OTel gRPC (OTLP)" "${OTEL_HOST}" "${OTEL_GRPC_PORT}"; then
  overall=1
fi

# ---------------------------------------------------------------------------
# 4. Prometheus
# ---------------------------------------------------------------------------
echo ""
echo "=== Prometheus ==="
if ! check_http "Prometheus ready" "${PROMETHEUS_URL}/-/ready"; then
  overall=1
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
if [[ "$overall" -eq 0 ]]; then
  echo "All backing services are reachable and ready."
else
  echo "One or more backing services are NOT ready. Start them with: docker compose up -d"
fi

exit "$overall"
