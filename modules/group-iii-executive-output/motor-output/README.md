# motor-output

**Group III — Executive & Output Modules | §6.3**

Motor / Output / Effector layer for EndogenAI. Receives ActionSpec messages from
executive-agent or agent-runtime and routes them to the appropriate output channel
with error policy and corollary discharge feedback.

## Purpose

`motor-output` is the **motor effector layer** of the EndogenAI pipeline. It receives
`ActionSpec` messages from `executive-agent` and routes them to one of four output
channels: outbound HTTP, A2A agent delegation, filesystem write, or LLM-rendered
structured output.

Before each dispatch a **preaction signal** is emitted to `executive-agent` (SMA
analogue — channel pre-selection). After each dispatch a `MotorFeedback` object is
posted back with a `deviation_score` and `reward_signal`, closing the corollary-discharge
loop. Channel selection, retry logic, circuit-breaking, and escalation are all governed
by `error-policy.config.json`, keeping policy separate from dispatch mechanics.

---

## Neuroanatomical Analogues

| Component | Brain Region |
|-----------|-------------|
| `dispatcher.py` | Primary Motor Cortex (M1) — action dispatch router |
| `channel_selector.py` | Premotor Cortex (PMd) — pre-action channel selection |
| `feedback.py` | Spinocerebellar tract / SMA — corollary discharge, proprioceptive feedback |
| `error_policy.py` | Descending inhibition / cortico-thalamo-cortical escalation |
| `channels/http_channel.py` | Corticospinal tract → peripheral HTTP effector |
| `channels/a2a_channel.py` | Corticospinal tract → A2A agent effector |
| `channels/file_channel.py` | Corticospinal tract → filesystem effector |
| `channels/render_channel.py` | Corticospinal tract → LLM render effector |

## Interface

### A2A (JSON-RPC 2.0) — `POST /tasks`

| `task_type` | Payload | Description |
|-------------|---------|-------------|
| `dispatch_action` | `ActionSpec` fields | Dispatch a single action |
| `dispatch_batch` | `{action_specs: [ActionSpec]}` | Dispatch multiple actions concurrently |
| `get_status` | `{action_id: str}` | Retrieve dispatch record |
| `abort_dispatch` | `{action_id: str}` | Abort a pending dispatch |

### MCP Tools — `POST /mcp/tools/call`

| Tool | Description |
|------|-------------|
| `motor_output.dispatch_action` | Dispatch an action to an output channel |
| `motor_output.get_dispatch_status` | Get dispatch record by action_id |
| `motor_output.list_channels` | List available channels |
| `motor_output.abort_dispatch` | Abort a pending dispatch |

## Output Channels

| Channel | Trigger | Handler |
|---------|---------|---------|
| `http` | Default; explicit `params.url` | `HTTPChannel` — outbound HTTP |
| `a2a` | `params.a2a_url`; `type` contains `delegate` | `A2AChannel` — JSON-RPC 2.0 A2A |
| `file` | `params.path`; `type` contains `write_file` | `FileChannel` — filesystem write (aiofiles) |
| `render` | `type` contains `render` | `RenderChannel` — LiteLLM acompletion |

## Error Policy

Three-tier policy loaded from `error-policy.config.json`:

1. **Retry** — exponential backoff up to `maxAttempts`
2. **Circuit Breaker** — fail fast after `failureThreshold` failures per channel
3. **Escalation** — POST `dispatch_failure` task to executive-agent

## Corollary Discharge

Before dispatch, a `preaction_signal` is sent to executive-agent (SMA analogue).
After dispatch, a `MotorFeedback` object is POSTed to executive-agent with:

- `deviation_score` — Jaccard-based comparison of predicted vs. actual outcome
- `reward_signal` — binary {0, 1} signal for reinforcement
- `escalate` flag — set when deviation_score > 0.8

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `MO_PORT` | `8163` | HTTP listen port |
| `EXECUTIVE_AGENT_URL` | `http://localhost:8161` | Corollary discharge target |

## Deployment

### Local (development)

```bash
# From this directory
uv sync
uv run serve
```

### Docker

```bash
docker build -t endogenai/motor-output:latest .
docker run -p 8163:8163 -p 8263:8263 endogenai/motor-output:latest
```

### Docker Compose

```bash
# From repo root — starts all dependencies and modules
docker compose --profile modules up -d
```

`executive-agent` must be reachable at `EXECUTIVE_AGENT_URL` (default
`http://localhost:8161`) before `motor-output` starts dispatching, as corollary-discharge
feedback and preaction signals are POSTed to it after every dispatch.

---

## Development

```bash
cd modules/group-iii-executive-output/motor-output
uv sync
uv run ruff check .
uv run mypy src/
uv run pytest
```

## Testing

Framework: **pytest**. Coverage threshold: **80%** (enforce with `pytest-cov` once installed — see P05).

```bash
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# No live services required for unit tests
SKIP_INTEGRATION_TESTS=1 uv run pytest -m "not integration" -q
```

Estimated coverage: ~91%. Active regression (resolved in test sweep 2026-03-03):
- `tests/test_feedback.py:91` — `ActionSpec` missing `goal_id` causes `ValueError` before `emit()` is reached — see [workplan](../../../docs/test-upgrade-workplan.md) P01

Known gaps — no tests yet for:
- `src/a2a_handler.py` — see P09
- `src/instrumentation/otel_setup.py` — covered by `tests/test_otel_setup.py`

> **Coverage as of 2026-03-03 test sweep:** **91%**. See workplan §7.

## Ports

| Protocol | Port |
|----------|------|
| A2A + MCP HTTP | 8163 |
| MCP SSE | 8263 |
