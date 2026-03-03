# metacognition

**Metacognition & Monitoring Layer — §7.2**

Port: **8171**

Brain analogue: **Anterior Cingulate Cortex (ACC) + Prefrontal Cortex BA10 + Nelson & Narens meta-level**

---

## Purpose

The metacognition module is the self-monitoring layer of the EndogenAI brain. It observes Phase 6
outputs (`executive-agent` + `motor-output`) in real time, computes rolling confidence scores and
deviation z-scores, emits structured Prometheus metrics, and triggers corrective A2A tasks to
`executive-agent` when sustained low confidence is detected.

Neuroscience analogues:
- **ACC (anterior cingulate cortex)** — error detection via deviation z-score anomaly flagging
- **PFC BA10** — prospective confidence calibration via rolling reward delta + success rate
- **Nelson & Narens meta-level** — monitoring (object-level → meta-level) and control (meta-level → object-level)

---

## Interface

This module exposes both an **A2A** (task delegation) interface and an **MCP** (context resource) interface.

### A2A Interface

| Direction | Task | Payload |
|-----------|------|---------|
| Inbound | `evaluate_output` | `EvaluateOutputPayload` (see below) |
| Outbound | `request_correction` | `{task_type, task_confidence, deviation_zscore, goal_id}` |

**Inbound `evaluate_output` payload:**
```json
{
  "goal_id": "uuid",
  "action_id": "uuid",
  "success": true,
  "escalate": false,
  "deviation_score": 0.2,
  "reward_value": 0.8,
  "task_type": "navigation",
  "retry_count": 0,
  "policy_denied": false,
  "trace_id": null
}
```

**Endpoint:** `POST http://localhost:8171/tasks`

JSON-RPC 2.0 envelope:
```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "tasks/send",
  "params": {
    "task_type": "evaluate_output",
    "goal_id": "...",
    ...
  }
}
```

---

### MCP Resources

| URI | Type | Description |
|-----|------|-------------|
| `resource://brain.metacognition/confidence/current` | `dict[str, float]` | Current task_confidence per task_type |
| `resource://brain.metacognition/anomalies/recent` | `list[MetacognitiveEvaluation]` | Recent error_detected=True events |
| `resource://brain.metacognition/report/session` | `MetacognitiveSessionReport` | Session-level aggregate report |

**MCP endpoint:** `http://localhost:8171/mcp`

**Tools:**

| Tool | Input | Output |
|------|-------|--------|
| `evaluate` | `{goal_id, action_id, success, escalate, deviation_score, reward_value, task_type?}` | `MetacognitiveEvaluation` |
| `configure-threshold` | `{confidence_threshold: float [0,1]}` | Updated threshold confirmation |
| `report` | `{}` | `MetacognitiveSessionReport` |

---

## Prometheus Metrics

All metrics use the `brain_metacognition_` prefix (required by the Prometheus relabel filter).

| Metric | Type | Description |
|--------|------|-------------|
| `brain_metacognition_task_confidence` | Gauge | Rolling confidence per task_type [0,1] |
| `brain_metacognition_deviation_score` | Gauge | Rolling mean deviation score |
| `brain_metacognition_reward_delta` | Histogram | Distribution of reward delta values |
| `brain_metacognition_task_success_rate` | Gauge | Rolling success rate per task_type |
| `brain_metacognition_escalation_total` | Counter | Cumulative escalation events |
| `brain_metacognition_retry_count` | Histogram | Distribution of retry counts |
| `brain_metacognition_policy_denial_rate` | Gauge | Rolling policy denial rate |
| `brain_metacognition_deviation_zscore` | Gauge | Z-score of deviation score |

Prometheus scrape endpoint: `http://localhost:9464/metrics`

---

## Alert Rules

Defined in `observability/prometheus-rules/metacognition.yml` (copied to top-level `observability/prometheus-rules/`):

| Alert | Condition | Severity |
|-------|-----------|----------|
| `TaskConfidenceLow` | `task_confidence < 0.7` for 5m | warning |
| `DeviationAnomalyHigh` | `deviation_zscore > 2.5` for 2m | warning |
| `EscalationRateElevated` | `rate(escalation_total[5m]) > 0.1` for 5m | critical |
| `PolicyDenialRateHigh` | `policy_denial_rate > 0.3` for 5m | warning |

---

## Configuration

`monitoring.config.json`:

| Key | Default | Description |
|-----|---------|-------------|
| `confidence_threshold` | `0.7` | Below this triggers alert window tracking |
| `deviation_error_threshold` | `0.75` | Z-score above this sets `error_detected=True` |
| `rolling_window_size` | `20` | Number of events in rolling window per task_type |
| `alert_window_minutes` | `5` | Minutes of sustained low confidence before `request_correction` |
| `otlp_endpoint` | `http://localhost:4317` | OTLP gRPC collector |
| `prometheus_port` | `9464` | Prometheus scrape port |
| `escalation_enabled` | `true` | Whether to send `request_correction` A2A tasks |
| `executive_agent_url` | `http://localhost:8161` | Target for `request_correction` |
| `chromadb_url` | `http://localhost:8000` | ChromaDB endpoint for evaluation event storage |
| `service_name` | `"metacognition"` | OTel resource attribute `service.name` |
| `service_namespace` | `"brain"` | OTel resource attribute `service.namespace` |
| `metrics_export.otlp_enabled` | `true` | Enable OTLP gRPC metric export |
| `metrics_export.prometheus_enabled` | `true` | Enable Prometheus scrape endpoint |

Environment variable overrides: `EXECUTIVE_AGENT_URL`, `CHROMADB_URL`, `OTLP_ENDPOINT`, `PROMETHEUS_PORT`, `METACOGNITION_PORT`.

---

## Deployment

```bash
cd modules/group-iv-adaptive-systems/metacognition
uv sync
uv run uvicorn metacognition.server:app --host 0.0.0.0 --port 8171
```

Dependencies: ChromaDB (`:8000`), OTLP collector (`:4317`), executive-agent (`:8161`).

---

## Development

```bash
uv run ruff check .
uv run mypy src/
uv run pytest
```
