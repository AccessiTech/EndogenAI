# Temporal vs. Prefect Spike

_Spec defined in [phase-6-detailed-workplan.md §8](phase-6-detailed-workplan.md)_  
_Status: **PENDING** — must complete before `agent-runtime` (§6.2) implementation begins_  
_Date conducted: —_  
_Conducted by: —_

---

## 1. Purpose

Determine which durable workflow orchestrator to use as `primary` in `orchestrator.config.json`
before the `agent-runtime` module is built. The result of this spike does not gate
`executive-agent` (§6.1) work.

The orchestrator is **user-configurable** regardless of the spike result — see §5 below and
`orchestrator.config.json` for all valid `primary` / `fallback` combinations. This spike
establishes the correct default shipped configuration.

---

## 2. Spike Scope

Both orchestrators must be exercised against the same minimal test harness:

1. Execute a **3-step pipeline** with one simulated LLM call (mocked via `unittest.mock`
   patching `litellm.completion`).
2. **Simulate a Worker crash** mid-execution (kill the Worker process after step 1 completes
   and before step 2 starts; allow the server/scheduler to retain state).
3. **Restart the Worker** and verify execution resumes from the crash point rather than
   restarting from the beginning.

The test harness lives in `modules/group-iii-executive-output/agent-runtime/spike/` and is
deleted (or moved to `tests/`) after the spike is resolved. It must not be shipped as
production code.

---

## 3. Pass/Fail Criteria

| # | Criterion | Temporal pass condition | Prefect pass condition |
|---|---|---|---|
| C1 | Deterministic replay after crash | Must replay from the **exact crash point** with no data loss (Event History guarantees) | Acceptable if the last completed `@task` is not re-executed (result is checkpointed) |
| C2 | Startup time (cold `docker compose up`) | Pass if < 30 seconds to first Worker poll | N/A — no server required |
| C3 | LLM Activity idempotency | Pass if the replayed LLM call uses the cached result from Event History (no duplicate real LLM call) | Pass if `@task` result is checkpointed and not retried |
| C4 | Local dev experience | Pass if `docker compose up temporal` is a single command that produces a healthy server | N/A — no server required |

**Decision rule**:
- Temporal is `primary` if it passes **all four** criteria (C1–C4).
- Prefect is `primary` only if Temporal **fails C2** (cold-start > 30 s) **AND** Prefect passes
  C1 (replay).
- If both orchestrators pass, prefer Temporal (Event History provides a stronger durability
  guarantee than Prefect's checkpoint store).

---

## 4. Results

> **Fill in this table after running the spike.**

| Criterion | Temporal result | Temporal pass? | Prefect result | Prefect pass? |
|---|---|---|---|---|
| C1 — Replay from crash | — | ❓ | — | ❓ |
| C2 — Cold-start time | — s | ❓ | N/A | ✅ |
| C3 — LLM idempotency | — | ❓ | — | ❓ |
| C4 — Local dev UX | — | ❓ | N/A | ✅ |

### 4.1 Crash-recovery evidence

```
# Paste test output here — e.g. pytest -s spike/test_crash_recovery.py
```

### 4.2 Cold-start timing evidence (Temporal)

```
# docker compose up temporal --no-deps 2>&1 | grep -E "started|listening|poll"
# Record elapsed time from `docker compose up` to first Worker poll log line
```

### 4.3 LLM idempotency evidence

```
# Show that litellm.completion mock was called exactly once per Activity invocation
# even after replay — e.g. mock.call_count = 1 after crash + resume
```

---

## 5. Decision

> **Fill in this section after evaluating the results table above.**

**Primary orchestrator**: `temporal` | `prefect` _(delete one)_

**Fallback orchestrator**: `prefect` | `none` _(delete one)_

**Rationale**: _(one or two sentences explaining why)_

**Limitations discovered**: _(any caveats or known issues found during the spike)_

---

## 6. Config to Apply

After completing §5, copy the resolved values into
`modules/group-iii-executive-output/agent-runtime/orchestrator.config.json`:

```json
{
  "primary": "<temporal|prefect>",
  "fallback": "<prefect|none>",
  "temporalServerUrl": "localhost:7233",
  "temporalNamespace": "endogenai",
  "temporalTaskQueue": "brain-runtime",
  "prefectApiUrl": "http://localhost:4200",
  "workflowIdStrategy": "goal_id_with_attempt",
  "fallbackTrigger": {
    "strategy": "circuit-breaker",
    "maxTemporalConnectRetries": 3,
    "fallbackCooldownSeconds": 60
  }
}
```

Valid modes reference (from `phase-6-detailed-workplan.md §8.4`):

| `primary` | `fallback` | Runtime behaviour |
|---|---|---|
| `temporal` | `prefect` | **Default shipped config.** Temporal with Prefect circuit-breaker |
| `temporal` | `none` | Temporal only; hard-fail if server down |
| `prefect` | `none` | Prefect only; no Temporal server required (e.g. local dev without Docker) |
| `none` | `none` | Dry-run / test mode; records intent but does not execute |

---

## 7. Sign-off Gate

Before opening the `agent-runtime` implementation PR, confirm all boxes are checked:

- [ ] Results table (§4) fully populated with evidence
- [ ] Decision (§5) recorded — primary and fallback chosen
- [ ] `orchestrator.config.json` updated with chosen values (§6)
- [ ] Spike harness code moved to `tests/spike/` or deleted
- [ ] This file committed to `docs/research/`
