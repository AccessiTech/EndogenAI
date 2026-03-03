# Phase 7 — Decision 3 Research: Metacognition Monitoring Scope

_Generated: 2026-03-02 by Docs Executive Researcher_

_Decision: Phase 6 outputs only (Option A — confirmed)_

_Cross-references:_
- _D3: docs/research/phase-7-synthesis-workplan.md §7 item 5_
- _Phase 6 source: modules/group-iii-executive-output/_
- _shared/types/reward-signal.schema.json_
- _shared/schemas/motor-feedback.schema.json_

_Sources fetched:_
- _docs/research/sources/phase-7/tech-otel-fastapi-instrumentation.md (55,949 chars)_
- _docs/research/sources/phase-7/tech-otel-genai-agent-spans.md (225,239 chars)_
- _docs/research/sources/phase-7/tech-otel-genai-metrics.md (238,076 chars)_
- _docs/research/sources/phase-7/bio-anterior-cingulate-cortex.md (existing)_
- _docs/research/sources/phase-7/bio-metacognition.md (existing)_
- _docs/research/sources/phase-7/bio-prefrontal-cortex.md (existing)_

---

## 1. Decision Summary

**Decision 3**: `metacognition` monitors **Phase 6 outputs only** (`executive-agent` and
`motor-output`). Full cross-phase monitoring (Phases 1–5) is deferred.

This document provides the endogenous evidence base for that decision, answering:
1. What exactly is observable in Phase 6 (from code)?
2. Where does the biological model say monitoring should attach?
3. How does metacognition observe Phase 6 without invasive coupling?
4. Which specific metrics to compute, and how to name them?
5. What is explicitly deferred and why?

---

## 2. Phase 6 Observable Surface (Endogenous Code Analysis)

Phase 6 consists of three modules. The following is derived from direct source inspection.

### 2.1 `motor-output` — Emitted Signals

**File**: `modules/group-iii-executive-output/motor-output/src/motor_output/feedback.py`

Every dispatch cycle, `FeedbackEmitter.build_feedback()` computes and emits a `MotorFeedback`:

| Field | Type | Computed from | Metacognition relevance |
|---|---|---|---|
| `deviation_score` | float [0,1] | Jaccard distance between `predicted_outcome` and `actual_outcome` | Primary error signal; 0 = perfect prediction, 1 = total divergence |
| `success` | bool | Dispatch channel result | Binary task outcome |
| `escalate` | bool | `deviation_score > 0.8` OR channel exhausted | High-severity failure flag |
| `reward_signal.value` | float | 1.0 if success else 0.0 (motor-output source) | Raw reward before executive-agent scaling |
| `latency_ms` | int | Wall-clock time from dispatch to completion | Performance tracking |
| `retry_count` | int | Tier-1 retry attempts before feedback | Error severity indicator |
| `channel` | enum | http / a2a / file / render / control-signal | Per-channel success profiling |

**Key structlog events emitted by motor-output** (observable via log interception):
```
feedback.emitted       → action_id, deviation_score
feedback.emit_error    → action_id, error
```

### 2.2 `executive-agent` — Derived and Emitted Signals

**File**: `modules/group-iii-executive-output/executive-agent/src/executive_agent/feedback.py`

`FeedbackHandler.receive_feedback()` processes inbound `MotorFeedback` and produces a `reward_delta`:

```python
# From executive-agent/feedback.py — the actual reward scaling:
def _compute_reward_delta(reward_value: float, deviation_score: float) -> float:
    effective = reward_value * (1.0 - deviation_score * 0.5)
    return max(-0.15, min(0.15, effective * 0.15))
```

| Derived signal | Formula | Range | Metacognition relevance |
|---|---|---|---|
| `reward_delta` | `reward_value × (1 − deviation_score × 0.5) × 0.15` | ±0.15 | Priority weight change per episode — accumulating this over N episodes = confidence score proxy |
| Goal lifecycle transition | EXECUTING → COMPLETED or FAILED | enum state | BDI cycle outcome counter |
| Escalation event | `feedback.escalate == True` | bool | Emergency signal; ACC ERN analogue |

**Key structlog events emitted by executive-agent**:
```
feedback.goal_transitioned   → goal_id, new_state, success
feedback.escalation          → goal_id, action_id, error
feedback.transition_error    → goal_id, error
feedback.reward_signal_forwarded → goal_id
```

**File**: `modules/group-iii-executive-output/executive-agent/src/executive_agent/deliberation.py`

BDI deliberation loop emits lifecycle transitions at each cycle:
```
deliberation.cycle_start    → cycle_id
deliberation.goal_committed → goal_id, goal_class, priority
deliberation.goal_suppressed → goal_id, reason
deliberation.policy_denied  → goal_id, violations
```

**File**: `modules/group-iii-executive-output/executive-agent/src/executive_agent/policy.py`

`PolicyDecision` objects expose `allow`, `violations: list[str]`, `explanation`, `cached`.

| Signal | Metacognition relevance |
|---|---|
| `policy_denied` event | Constraint violation rate — an ACC conflict-monitoring analogue |
| `violations` list | Specific constraint failure type — trend analysis possible |

### 2.3 `agent-runtime` — Observable Signals

`agent-runtime` queues and dispatches actions between `executive-agent` and `motor-output`.
Less directly relevant than the other two, but its queue depth is a congestion proxy:
- Action queue depth → downstream latency proxy
- Decomposer failure events → structured task failure signals

### 2.4 Existing Instrumentation Baseline

**Critical finding**: Phase 6 uses **`structlog` only — zero OTel instrumentation**.

No `TracerProvider`, `MeterProvider`, spans, or metrics exist in Phase 6 code. The Prometheus
`prometheus.yml` scrapes `brain_.*` metrics from the OTel Collector, but Phase 6 contributes
nothing to that stream today.

This has a direct consequence for observation strategy (see §5).

---

## 3. Schema Corrections

### 3.1 `reward-signal.schema.json` Location

**D3 synthesis workplan incorrectly stated** this file was absent from `shared/schemas/`.

**Actual location**: `shared/types/reward-signal.schema.json` ✅ — fully defined, 123 lines.

Key fields beyond the inline version in `motor-feedback.schema.json`:

| Field | Type | Relevance |
|---|---|---|
| `type` | enum: reward / penalty / confidence-boost / confidence-drop / frustration / satisfaction / … | Semantic category — directly maps to metacognition event type labelling |
| `trigger` | enum: task-success / task-failure / goal-achieved / prediction-error / self-evaluation / … | Maps to specific ACC monitoring events |
| `decay.halfLifeMs` | int | TD temporal discount — aligns with how metacognition should weight older episodes |
| `traceContext.traceparent` | W3C trace ID string | **OTel trace correlation already baked in** — `RewardSignal` can be linked to an OTel trace span |

The `traceContext.traceparent` field is the most important finding: `RewardSignal` was designed
to be correlated with OTel traces. This means the Phase 5 affective module (which emits
`RewardSignal` to executive-agent) already anticipates OTel instrumentation — metacognition
just needs to respect that contract.

### 3.2 `motor-feedback.schema.json` Field Naming

Confirmed field: `reward_signal.value` (not `.delta`). The inline `reward_signal` in
`MotorFeedback` is a simpler, float-only version of the full `shared/types/reward-signal.schema.json`.
The D1 and D2 documents used `delta` terminology; the correct field name is `value`.

**Action** (from Decision 1B): extract the inline version as `shared/schemas/reward-signal.schema.json`
and `$ref` it from `motor-feedback.schema.json`. This does not affect `shared/types/reward-signal.schema.json`,
which is the richer schema used by Phase 5.

---

## 4. Biological Mapping: PFC and ACC → Phase 6 Signals

### 4.1 ACC as Phase 6 Error Detector

The ACC's primary metacognitive functions (D1 §3.1, bio-anterior-cingulate-cortex.md):

- **Rostral ACC (rACC)**: affective error monitoring — fires when outcome violates expectation
- **Dorsal ACC (dACC)**: cognitive conflict monitoring — fires when two response options compete
- **ERN (Error-Related Negativity)**: ERP component at ~100ms post-error; amplitude scales with error severity

Phase 6 mappings:

| ACC function | Phase 6 observable | Metacognition computation |
|---|---|---|
| rACC: outcome violation | `deviation_score` | Error detected when `deviation_score > θ` (configurable threshold) |
| ERN amplitude | `deviation_score` magnitude | `reward_deviation_zscore = (deviation_score - μ) / σ` over rolling window |
| dACC: conflict monitoring | `policy_denied` + `violations` list | Constraint conflict rate = `policy_denials / total_cycles` |
| Post-error slowing | `retry_count` | High retry count = motor system already doing post-error slowing |
| Escalation | `escalate == True` | Highest-severity error; maps to PFC escalation pathway |

### 4.2 PFC as Phase 6 Confidence Estimator

The PFC Nelson & Narens meta-level (D1 §3.2, bio-metacognition.md):

- **Monitoring function**: reads from object level (Phase 6), computes confidence
- **Control function**: sends corrective signals back to object level

Phase 6 mappings:

| PFC function | Phase 6 observable | Metacognition computation |
|---|---|---|
| Anterior PFC (BA10) confidence | Cumulative `reward_delta` from executive-agent | `task_confidence = f(rolling_mean_reward_delta, success_rate)` |
| DLPFC working memory | Goal lifecycle history | Episode count per `goal_class` — habit detection upstream |
| Posterior parietal decision confidence | `deviation_score` trend | Bayesian update on each episode for per-`task_type` confidence |
| Prefrontal escalation pathway | Prometheus alert | Alert fires when `task_confidence < threshold` for sustained window |

### 4.3 The N&N Separation: Why Phase 6 Only Is Correct

Nelson & Narens (1990) define the meta-level as receiving **one-way read access** to the
object level, with control signals flowing back via a controlled intervention only.

- The object level is Phase 6 (executive-agent + motor-output): produces overt behaviour
- The meta-level is the `metacognition` module: monitors and occasionally intervenes

Extending the meta-level to monitor Phases 1–5 is biologically plausible but architecturally
premature: the PFC does not monitor individual neuron activations — it receives processed,
already-integrated signals. The Phase 6 `MotorFeedback` + `reward_delta` stream is exactly
that: the processed, integrated output of the full perception–cognition–action pipeline.
Monitoring it is both necessary and sufficient for Phase 7's goals.

---

## 5. Observation Architecture: Three Strategies

Phase 6 has no OTel. Metacognition needs to observe it. Three strategies offer different
trade-offs on invasiveness, richness, and coupling.

### Strategy A — FastAPI OTel Auto-Instrumentation

**Source**: docs/research/sources/phase-7/tech-otel-fastapi-instrumentation.md

Add one line to each Phase 6 server.py at startup:
```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)
```

This automatically creates HTTP spans for every incoming request, including:
- `http.method`, `http.route`, `http.status_code`, `http.target`
- Request/response duration
- Optional custom attribute injection via `server_request_hook`

**What this gives metacognition** (without any metacognition-specific code in Phase 6):
- Per-endpoint latency (e.g., `/a2a/receive_feedback` call duration)
- HTTP error rate (5xx = escalated or crashing)
- Throughput (feedback cycle rate)

**What this does NOT give**:
- Business-level signals: `deviation_score`, `reward_delta`, goal lifecycle state
- These are in the request/response body, not in HTTP metadata

**Pro**: One-line change per Phase 6 module; non-breaking; already in the OTel Collector pipeline.
**Con**: Coarse-grained — only HTTP-level observability, not domain-level.

### Strategy B — A2A Observer Hook (Explicit Push)

Phase 6 modules explicitly call a metacognition A2A endpoint at key monitoring points.
No OTel required — metacognition receives a structured `TaskResult` or `MotorFeedback` push.

```python
# In executive-agent/feedback.py — addition to receive_feedback():
if self._metacognition is not None:
    await self._metacognition.send_task("evaluate_output", {
        "task_result": {
            "goal_id": goal_id,
            "success": success,
            "deviation_score": feedback.deviation_score,
            "reward_delta": reward_delta,
            "escalated": feedback.escalate,
            "task_type": goal.goal_class,
        }
    })
```

**What this gives metacognition**: full domain-level signals — `deviation_score`, `reward_delta`,
`goal_class`, lifecycle state.

**Pro**: Rich business-level signals. Decoupled via A2A (metacognition can be absent/offline without
breaking Phase 6 — send_task is fire-and-forget with error handling). N&N-clean: object
level actively notifies meta-level.
**Con**: Requires changes in two Phase 6 files (`executive-agent/feedback.py` and optionally
`executive-agent/deliberation.py`). Creates an optional dependency on `metacognition` A2A URL.

### Strategy C — Hybrid (Recommended)

Combine both: auto-instrumentation for zero-cost HTTP tracing + explicit A2A push for
domain business metrics.

**Tier 1 (HTTP level — zero Phase 6 code changes)**:
```
FastAPIInstrumentor.instrument_app(app)  # added to each Phase 6 server.py
→ OTel Collector → Prometheus
→ brain_executive_agent_http_request_duration_seconds
→ brain_motor_output_http_request_duration_seconds
```

**Tier 2 (Domain level — small Phase 6 additions)**:
```
executive-agent FeedbackHandler  →  A2A send_task("evaluate_output", TaskResult)
                                      → metacognition evaluator
                                        → brain_executive_agent_deviation_score (gauge)
                                        → brain_executive_agent_reward_delta    (histogram)
                                        → brain_executive_agent_escalation_total (counter)
                                        → brain_executive_agent_task_confidence  (gauge)
```

**Why hybrid**:
- HTTP auto-instrumentation bootstraps observability instantly and costs nothing
- The A2A hook is small, optional, and architecturally clean — it treats Phase 6 as the true object level and metacognition as the true meta-level
- Together they cover both the low-level performance view and the high-level semantic view

**Biological parallel**: the ACC receives two streams — a fast subcortical loop (like auto-instrumentation,
giving coarse/fast signals) and a slower cortical loop (like the A2A hook, giving rich semantic content).
Both are needed for full metacognitive monitoring.

---

## 6. Signal-to-Metric Mapping

Full mapping from Phase 6 observable → metacognition computation → Prometheus metric.

### Tier 1 metrics (from FastAPI auto-instrumentation, zero new code)

| Phase 6 source | OTel span attribute | Prometheus metric | Type |
|---|---|---|---|
| motor-output `/dispatch` endpoint latency | `http.server.request.duration` | `brain_motor_output_request_duration_seconds` | Histogram |
| executive-agent `/a2a/receive_feedback` latency | `http.server.request.duration` | `brain_executive_agent_request_duration_seconds` | Histogram |
| HTTP error rate (5xx) | `http.response.status_code` | `brain_http_errors_total` | Counter |

### Tier 2 metrics (from A2A `evaluate_output` push, computed in metacognition evaluator)

| Phase 6 field | Source | Metacognition metric name | Type | Prometheus rule |
|---|---|---|---|---|
| `deviation_score` | `MotorFeedback` (motor-output) | `brain_metacognition_deviation_score` | Gauge | Alert when mean > 0.6 over 5m |
| `reward_delta` | FeedbackHandler computation | `brain_metacognition_reward_delta` | Histogram | Alert when p50 < -0.05 over 5m |
| `success` per `goal_class` | `MotorFeedback` (via executive-agent) | `brain_metacognition_task_success_rate` | Gauge | Alert when < threshold per task type |
| `escalate` flag count | `MotorFeedback` | `brain_metacognition_escalation_total` | Counter | Alert when rate > N/min |
| `retry_count` | `MotorFeedback` | `brain_metacognition_retry_count` | Histogram | Alert when p95 > 2 |
| `policy_denied` events | deliberation structlog | `brain_metacognition_policy_denial_rate` | Gauge | Alert when sustained > threshold |
| Derived: `task_confidence` | Rolling mean of reward_delta | `brain_metacognition_task_confidence` | Gauge | Alert when < `confidence_threshold` |
| Derived: `reward_deviation_zscore` | z-score of deviation_score vs rolling mean | `brain_metacognition_deviation_zscore` | Gauge | Alert when > `anomaly_zscore_threshold` |

### Metric naming rationale

The Prometheus scrape in `prometheus.yml` keeps only `brain_.*` metrics:
```yaml
metric_relabel_configs:
  - source_labels: [__name__]
    regex: "brain_.*"
    action: keep
```
All metrics must be prefixed `brain_` to flow through the pipeline. The `brain_metacognition_`
sub-namespace distinguishes metacognition metrics from future module-specific metrics.

---

## 7. Alignment with OTel GenAI Semantic Conventions

**Source**: docs/research/sources/phase-7/tech-otel-genai-agent-spans.md

The OTel GenAI Agent Spans specification (development status) defines span names for AI agent
frameworks. Key conventions relevant to Phase 7:

| OTel GenAI convention | EndogenAI analogue | Phase 7 application |
|---|---|---|
| `gen_ai.agent.name` span attribute | `"executive-agent"`, `"motor-output"` | Tag all metacognition spans with the source agent name |
| `gen_ai.agent.id` span attribute | `GoalItem.id` | Correlate spans back to individual BDI goals |
| `execute_agent_tool` span name | BDI deliberation cycle | Instrument deliberation as a GenAI agent tool span |
| `agent.invoke` span name | A2A `send_task` call | Tag A2A task calls with GenAI agent invoke convention |

**OTel GenAI Metrics** (docs/research/sources/phase-7/tech-otel-genai-metrics.md):

| OTel GenAI metric | EndogenAI analogue |
|---|---|
| `gen_ai.client.operation.duration` (histogram) | `brain_motor_output_request_duration_seconds` |
| `gen_ai.client.token.usage` (histogram) | Not directly applicable — no token counting; nearest analogue is `retry_count` |

**Recommendation**: use `brain_metacognition_` prefix (not `gen_ai.`) for all custom metrics.
The OTel GenAI conventions are designed for LLM clients, not BDI agent systems. Follow their
structural patterns (histograms for duration, counters for events) but use the `brain_` namespace
that already runs through the Prometheus pipeline.

---

## 8. What Is Deferred and Why

| Deferred scope | Why deferred | When to revisit |
|---|---|---|
| Phase 5 memory retrieval quality (§5.1–5.4) | Memory modules have no stable `TaskResult` output yet; ChromaDB query latency is available but semantically thin | Phase 8: after memory modules are proven stable |
| Phase 5 affective/motivational signals (§5.5) | `RewardSignal` already flows from affective to executive-agent; metacognition would see this via the Phase 6 feedback loop anyway | Covered indirectly via `reward_delta` today |
| Phase 5 reasoning (§5.6 DSPy) | Reasoning is inside executive-agent's BDI deliberation; the deliberation output IS the Phase 6 gateway | Covered indirectly via `policy_denied` and goal commitment signals |
| Phase 1–4 signal processing quality | No structured output format yet; no schema contracts for signal quality | Phase 9+: requires Phase 1–4 to emit structured `TaskResult` objects |
| Cross-phase trace propagation | `RewardSignal.traceContext.traceparent` provides the hook but requires all modules to propagate W3C trace context | Can be activated once OTel is added to all modules — the schema contract is already in place |

**Key insight on indirect coverage**: because Phase 6 sits at the end of the full pipeline,
its `deviation_score` and `reward_delta` are **emergent products of all upstream processing**.
A Phase 2 reasoning failure that produces a bad plan will still manifest as a high
`deviation_score` in Phase 6 `MotorFeedback`. Metacognition monitoring Phase 6 will detect
it — just without pinning which upstream phase caused it. That attribution is the future scope.

---

## 9. Implementation Notes

### 9.1 Phase 6 Changes Required (Minimal)

Three small additions to Phase 6 to enable Tier 2 monitoring:

**`executive-agent/feedback.py`** — add optional metacognition A2A send after reward_delta computation:
```python
def __init__(self, goal_stack, affective_client=None, metacognition_client=None):
    self._metacognition = metacognition_client
    ...

async def receive_feedback(self, feedback):
    ...
    if self._metacognition is not None:
        with contextlib.suppress(Exception):
            await self._metacognition.send_task("evaluate_output", {
                "goal_id": goal_id,
                "success": success,
                "deviation_score": feedback.deviation_score,
                "reward_delta": reward_delta,
                "escalated": feedback.escalate,
                "task_type": _get_goal_class(goal_id, self._goal_stack),
                "reward_signal_type": feedback.reward_signal.get("type"),
            })
```

**`executive-agent/server.py`** and **`motor-output/server.py`** — add one line each:
```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)  # after app = FastAPI(...)
```

**`executive-agent/pyproject.toml`** and **`motor-output/pyproject.toml`** — add dependency:
```toml
"opentelemetry-instrumentation-fastapi>=0.50b0",
```

### 9.2 New `metacognitive-evaluation.schema.json`

Based on §6 metrics and Phase 6 observable surface, the schema should include:

```json
{
  "event_id": "uuid",
  "goal_id": "uuid",
  "task_type": "string",
  "deviation_score": "number [0,1]",
  "reward_delta": "number [-0.15, 0.15]",
  "escalated": "boolean",
  "success": "boolean",
  "retry_count": "integer",
  "task_confidence": "number [0,1]",
  "reward_deviation_zscore": "number",
  "error_detected": "boolean",
  "source_module": "string (executive-agent | motor-output)",
  "timestamp": "date-time",
  "trace_context": { "traceparent": "string" }
}
```

### 9.3 Prometheus Alert Rule Templates

```yaml
# observability/prometheus-rules/metacognition.yml
groups:
  - name: metacognition
    rules:
      - alert: TaskConfidenceLow
        expr: brain_metacognition_task_confidence < 0.7
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Task confidence below threshold for {{ $labels.task_type }}"

      - alert: AnomalyRateHigh
        expr: brain_metacognition_deviation_zscore > 2.0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Deviation z-score anomaly in {{ $labels.source_module }}"

      - alert: EscalationRateElevated
        expr: rate(brain_metacognition_escalation_total[5m]) > 0.1
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Elevated escalation rate from motor-output"
```

---

## 10. Decisions Recorded

### Strategy C — Hybrid observation architecture ✅ DECIDED

The recommended hybrid strategy is confirmed. Implementation proceeds in two tiers:

**Tier 1 (FastAPI auto-instrumentation)**: Add `FastAPIInstrumentor.instrument_app(app)` to
`executive-agent/server.py` and `motor-output/server.py`. Zero Phase 6 domain-logic changes.
Gives free HTTP-level spans flowing through the existing OTel Collector → Prometheus pipeline.

**Tier 2 (A2A observer hook)**: Add optional `metacognition_client` to `FeedbackHandler`.
Configured via `METACOGNITION_URL` environment variable (default `None` = disabled), ensuring
Phase 6 remains fully runnable without Phase 7 deployed. Call is wrapped in
`contextlib.suppress(Exception)` — non-fatal to the Phase 6 feedback loop.

### Open question 1 — Metacognition URL configuration ✅ DECIDED

`METACOGNITION_URL` environment variable, defaulting to `None` (disabled). This is consistent
with how other optional inter-module A2A URLs are handled in Phase 6 (`channels.config.json`
pattern applies to required channels; optional monitoring hooks use env vars). No changes to
`channels.config.json` schema required.

### Open question 2 — structlog → OTel log bridge ✅ DECIDED (stretch goal)

Treat as a Phase 7 stretch goal, not a core delivery item. The `opentelemetry-instrumentation-logging`
package can bridge Python `logging.Logger` to OTel log records. If structlog is configured to
emit via Python's standard `logging` module (which it supports via `structlog.stdlib`), this
gives a free third tier of observability. Implement only after Tier 1 and Tier 2 are stable.
Document in `metacognition/README.md` as a known future enhancement.

### Open question 3 — W3C trace context propagation ✅ DECIDED (Phase 7 scope)

Activating `RewardSignal.traceContext.traceparent` propagation is **in scope for Phase 7** as
a Tier 1 enhancement (added once FastAPI auto-instrumentation is running). The active span's
`traceparent` should be injected into each `RewardSignal` emitted by `executive-agent` before
forwarding downstream. This enables distributed tracing across the Phase 5 → Phase 6 →
metacognition chain without requiring cross-phase monitoring scope expansion.

---

## 11. Source References

| Source | URL | Fetched |
|---|---|---|
| OTel FastAPI instrumentation | https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html | 2026-03-02 |
| OTel GenAI agent spans semconv | https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/ | 2026-03-02 |
| OTel GenAI metrics semconv | https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/ | 2026-03-02 |
| anterior-cingulate-cortex Wikipedia | https://en.wikipedia.org/wiki/Anterior_cingulate_cortex | 2026-03-03 (prior session) |
| Metacognition Wikipedia | https://en.wikipedia.org/wiki/Metacognition | 2026-03-03 (prior session) |
| Prefrontal cortex Wikipedia | https://en.wikipedia.org/wiki/Prefrontal_cortex | 2026-03-03 (prior session) |
| motor-output feedback.py (endogenous) | modules/group-iii-executive-output/motor-output/src/motor_output/feedback.py | — |
| executive-agent feedback.py (endogenous) | modules/group-iii-executive-output/executive-agent/src/executive_agent/feedback.py | — |
| shared/types/reward-signal.schema.json (endogenous) | shared/types/reward-signal.schema.json | — |
| shared/schemas/motor-feedback.schema.json (endogenous) | shared/schemas/motor-feedback.schema.json | — |
| observability/otel-collector.yaml (endogenous) | observability/otel-collector.yaml | — |
| observability/prometheus.yml (endogenous) | observability/prometheus.yml | — |
