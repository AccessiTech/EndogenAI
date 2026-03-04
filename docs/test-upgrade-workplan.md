# Test Upgrade Workplan

This document catalogues every known test gap, regression, quality issue, and tooling deficiency
across the EndogenAI monorepo as of 2026-03-03. Updated 2026-03-03 to incorporate owner decisions
on all 6 open questions (see Section 9). It is intended to be handed directly to Implement agents
or Phase Executives without further clarification.

---

## Executive Summary

| Category | Count | Severity |
|----------|-------|----------|
| Active regressions (blocking CI) | 3 | CRITICAL |
| Source files with zero tests | 30+ | CRITICAL–HIGH |
| Test quality issues (FAIL) | 4 | HIGH |
| Test quality issues (WARN) | 9 | MEDIUM |
| Tooling gaps | 5 | HIGH |
| Permanently-skipped integration tests | 4 | MEDIUM |

Three tests are failing right now and must be fixed before any other upgrade work proceeds. Coverage
tooling (`pytest-cov`, `@vitest/coverage-v8`) is absent from every package, so all coverage
percentages below are estimates. The `scan_coverage_gaps.py` registry covers only 4 of 20+
packages. The client application layer has the worst estimated coverage (~25%) and the most
complete absence of tests for individual components.

---

## 1. Active Regressions — Fix Immediately

These failures are blocking CI. They must be resolved before any other work in this workplan is
started.

### Regression 1 — `motor-output` `test_emit_tolerates_failure`

| Field | Value |
|-------|-------|
| **File** | [`modules/group-iii-executive-output/motor-output/tests/test_feedback.py`](../modules/group-iii-executive-output/motor-output/tests/test_feedback.py) |
| **Line** | 91 |
| **Symptom** | `ValueError: ActionSpec.goal_id is required` raised inside `FeedbackEmitter.build_feedback()` before `emit()` is ever reached; the test never exercises the intended tolerates-failure path |
| **Root cause** | `ActionSpec` fixture constructed without `goal_id` argument |
| **Fix** | Add `goal_id="goal-004"` to the `ActionSpec` instantiation at line 91 |
| **Effort** | S |
| **Owner** | Implement agent |

### Regression 2 — `executive-agent` OPA Testcontainer 30 s timeout

| Field | Value |
|-------|-------|
| **File** | [`modules/group-iii-executive-output/executive-agent/tests/test_integration_bdi_loop.py`](../modules/group-iii-executive-output/executive-agent/tests/test_integration_bdi_loop.py) |
| **Line** | 35 |
| **Symptom** | OPA Testcontainer fixture waits for log string `"Loaded policy bundle"` which OPA never emits when started without `--bundle`; both tests ERROR after 30 s |
| **Root cause** | Wrong wait string for the OPA startup mode in use |
| **Fix** | Change wait string to `"Initializing server"` **or** replace log-wait with an HTTP health-check against `/health` |
| **Effort** | S |
| **Owner** | Implement agent |

### Regression 3 — `apps/default/server` `mcp-client.test.ts` Headers bracket notation

| Field | Value |
|-------|-------|
| **File** | [`apps/default/server/tests/mcp-client.test.ts`](../apps/default/server/tests/mcp-client.test.ts) |
| **Line** | 67 |
| **Symptom** | `fetchOptions.headers['Last-Event-ID']` uses bracket notation on a `Headers` instance; always returns `undefined`; assertion always passes vacuously |
| **Root cause** | `Headers` is a class; property access must use `.get()` |
| **Fix** | Replace `fetchOptions.headers['Last-Event-ID']` with `fetchOptions.headers.get('Last-Event-ID')` — **or** change the implementation to use a plain object |
| **Effort** | S |
| **Owner** | Implement agent |

---

## 2. Critical Coverage Gaps

Files with zero tests where bugs would directly affect end-user-visible behaviour.

### Client Internals tab — 7 components, 0 tests

All files in `apps/default/client/tabs/Internals/`:

| File | Risk |
|------|------|
| `AgentCardBrowser.tsx` | Agent discovery UI — untested rendering and interaction |
| `AgentCardBrowserPanel.tsx` | Panel wrapper — untested |
| `CollectionsViewer.tsx` | Vector store inspection — untested |
| `ConfidencePanel.tsx` | Confidence score display — untested |
| `MemoryInspector.tsx` | Memory state viewer — untested |
| `SignalTraceFeed.tsx` | Live signal trace — untested |
| `Placeholder.tsx` | Fallback component — untested |

Minimum required tests per component: renders without crashing, key props reflected in output,
accessible role/label.

### Client — API and Auth layer, 0 tests

| File | Risk |
|------|------|
| `apps/default/client/api/gateway.ts` | All client→server API calls go through this; any regression is silent |
| `apps/default/client/auth/AuthProvider.tsx` | Token provisioning — session loss on regression |
| `apps/default/client/auth/LoginPage.tsx` | Auth entry point — untested UI flow |
| `apps/default/client/auth/useAuth.ts` | Auth hook — untested state transitions |
| `apps/default/client/auth/AuthContext.ts` | Auth context — untested |

---

## 3. High-Priority Coverage Gaps

### 3.1 Systemic Gaps (10+ modules affected)

These are patterns repeated across every phase-3 and phase-4 module. Fix the pattern once per
module rather than module-by-module.

#### A2A handler dispatch — 10 untested files

Every module below has an `a2a_handler.py` with zero test coverage. The A2A layer is the
primary inter-agent communication path.

| Module path (prefix `modules/`) | File |
|----------------------------------|------|
| `group-ii-cognitive-processing/affective/src/` | `a2a_handler.py` |
| `group-ii-cognitive-processing/short-term-memory/src/` | `a2a_handler.py` |
| `group-ii-cognitive-processing/long-term-memory/src/` | `a2a_handler.py` |
| `group-ii-cognitive-processing/episodic-memory/src/` | `a2a_handler.py` |
| `group-ii-cognitive-processing/reasoning/src/` | `a2a_handler.py` |
| `group-iii-executive-output/executive-agent/src/` | `a2a_handler.py` |
| `group-iii-executive-output/agent-runtime/src/` | `a2a_handler.py` |
| `group-iii-executive-output/motor-output/src/` | `a2a_handler.py` |
| `group-iv-adaptive-systems/learning-adaptation/src/` | `a2a_handler.py` |
| `group-iv-adaptive-systems/metacognition/src/` | `a2a_handler.py` |

Minimum test contract per handler: valid dispatch routes to correct handler function; unknown
method returns JSON-RPC error; malformed envelope returns parse error; internal error is wrapped
correctly.

#### MCP tool dispatch — 9 untested files

Same set of modules (working-memory excepted), each with an `mcp_tools.py`:

| Module | File |
|--------|------|
| `group-ii-cognitive-processing/affective/src/` | `mcp_tools.py` |
| `group-ii-cognitive-processing/short-term-memory/src/` | `mcp_tools.py` |
| `group-ii-cognitive-processing/long-term-memory/src/` | `mcp_tools.py` |
| `group-ii-cognitive-processing/episodic-memory/src/` | `mcp_tools.py` |
| `group-ii-cognitive-processing/reasoning/src/` | `mcp_tools.py` |
| `group-iii-executive-output/executive-agent/src/` | `mcp_tools.py` |
| `group-iii-executive-output/agent-runtime/src/` | `mcp_tools.py` |
| `group-iii-executive-output/motor-output/src/` | `mcp_tools.py` |
| `group-iv-adaptive-systems/learning-adaptation/src/` | `mcp_tools.py` |

Minimum test contract: tool registration is correct; each registered tool callable returns the
expected schema shape; error path returns MCP error envelope.

#### OTel setup — 4 untested files

| Module | File |
|--------|------|
| `group-ii-cognitive-processing/working-memory/src/instrumentation/` | `otel_setup.py` |
| `group-iii-executive-output/executive-agent/src/instrumentation/` | `otel_setup.py` |
| `group-iii-executive-output/motor-output/src/instrumentation/` | `otel_setup.py` |
| `group-iv-adaptive-systems/metacognition/src/instrumentation/` | `otel_setup.py` |

Minimum test contract: `setup_telemetry()` configures a tracer provider without raising; span
attributes are set correctly; OTLP exporter endpoint is read from env.

### 3.2 Infrastructure Gaps

| File | Gap | Minimum tests |
|------|-----|---------------|
| `infrastructure/a2a/src/orchestrator.ts` | Main A2A routing — zero unit tests | Route dispatch; unknown agent returns error; concurrent task queuing |
| `infrastructure/a2a/src/validate.ts` | JSON-RPC envelope validation — zero tests | Valid envelope passes; missing `id` rejected; wrong `jsonrpc` version rejected |
| `infrastructure/mcp/src/sync.ts` | Context-sync logic — zero tests | Sync merges contexts correctly; conflict resolution path |
| `infrastructure/mcp/src/validate.ts` | Validation helpers — zero tests | Each validator function: passing and failing inputs |
| `apps/default/server/src/auth/sessions.ts` | Session store — zero tests | Create/get/delete lifecycle; expiry |
| `apps/default/server/src/middleware/tracing.ts` | Tracing middleware — zero tests | Span created per request; error status set on exception |
| `apps/default/server/src/routes/wellknown.ts` | `/.well-known/agent-card.json` route — zero tests | Returns 200 with valid agent-card shape |

### 3.3 Application Layer Gaps

| Package | Est. coverage | Primary gap |
|---------|--------------|-------------|
| `apps/default/client` | ~25% | Internals tab (7 components), auth layer (5 files), gateway.ts |
| `apps/default/server` | ~40% | auth/sessions.ts, middleware/tracing.ts, routes/wellknown.ts |

### 3.4 Module-Specific Gaps

| File | Gap |
|------|-----|
| `modules/group-ii-cognitive-processing/long-term-memory/src/reconsolidation.py` | Memory reconsolidation logic — 0% coverage |
| `modules/group-iii-executive-output/agent-runtime/src/workflow.py` | Core Temporal/Prefect task execution — 0% |
| `modules/group-iii-executive-output/agent-runtime/src/worker.py` | Worker lifecycle — 0% |
| `modules/group-iii-executive-output/agent-runtime/src/prefect_fallback.py` | Fallback engine — 0% |
| `modules/group-iv-adaptive-systems/learning-adaptation/src/training/skill_feedback_callback.py` | RL feedback hook — 0% |
| `shared/vector-store/python/src/embedding.py` | Ollama embedding wrapper — no tests |

---

## 4. Medium-Priority Gaps

| Package | Est. coverage | Gap severity | Notes |
|---------|--------------|--------------|-------|
| `infrastructure/mcp` | ~60% | MEDIUM | sync.ts, validate.ts missing |
| `infrastructure/a2a` | ~45% | HIGH | orchestrator.ts, validate.ts missing |
| `infrastructure/adapters` | ~50% | HIGH | 6 passing tests but surface area larger |
| `shared/vector-store/python` | ~65% | MEDIUM | embedding.py entirely missing |
| `shared/a2a/python` | ~75% | MEDIUM | — |
| `group-ii/affective` | ~60% | MEDIUM | mcp_tools.py, a2a_handler.py |
| `group-ii/working-memory` | ~75% | MEDIUM | otel_setup.py |
| `group-ii/short-term-memory` | ~65% | MEDIUM | mcp_tools.py, a2a_handler.py |
| `group-ii/long-term-memory` | ~60% | MEDIUM | reconsolidation.py + handler files |
| `group-ii/episodic-memory` | ~65% | MEDIUM | mcp_tools.py, a2a_handler.py |
| `group-ii/reasoning` | ~65% | MEDIUM | 4 integration tests permanently skipped |
| `group-iii/executive-agent` | ~50% | HIGH | mcp_tools.py, a2a_handler.py, otel_setup.py; 2 ERRORs |
| `group-iii/agent-runtime` | ~45% | HIGH | workflow.py, worker.py, prefect_fallback.py all 0% |
| `group-iii/motor-output` | ~55% | HIGH | 1 blocking FAIL; a2a_handler.py, otel_setup.py |
| `group-iii integration` | thin (4 tests) | MEDIUM | Pipeline layer needs expansion |
| `group-iv/learning-adaptation` | ~50% | HIGH | skill_feedback_callback.py 0% |
| `group-iv/metacognition` | ~45% | HIGH | a2a_handler.py, otel_setup.py |
| `group-iv integration` | thin (2 tests) | MEDIUM | Pipeline layer needs expansion |
| `scripts/validate_frontmatter.py` | ~30% | MEDIUM | Pre-commit hook — no tests |
| `scripts/fetch_source.py` | ~30% | MEDIUM | — |
| `scripts/fix_agent_tools.py` | ~30% | MEDIUM | — |
| `infrastructure/mcp/src/run.ts` | 0% | MEDIUM | Process entry point — startup/shutdown paths |

---

## 5. Test Quality Issues

### 5.1 FAIL — Blocking

These represent broken or vacuous test logic beyond the three active regressions above.

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| Q1 | `modules/group-iii-executive-output/motor-output/tests/test_feedback.py` | 91 | ValueError crash before `emit()` reached — see Regression 1 | Add `goal_id="goal-004"` |
| Q2 | `modules/group-iii-executive-output/executive-agent/tests/test_integration_bdi_loop.py` | 35 | OPA 30 s timeout ERROR — see Regression 2 | Change wait string to `"Initializing server"` |
| Q3 | `apps/default/server/tests/mcp-client.test.ts` | 67 | `Headers` bracket notation always undefined — see Regression 3 | Use `.get('Last-Event-ID')` |
| Q4 | `modules/group-iii-executive-output/agent-runtime/tests/test_orchestrator.py` | 95 | `test_loads_config_file` makes **zero assertions**; Orchestrator config loading is completely unverified | Add assertions that the loaded config values match the file contents |

### 5.2 WARN — Non-Blocking Quality Issues

| # | File | Line(s) | Issue | Recommended Fix |
|---|------|---------|-------|-----------------|
| W1 | `modules/group-iii-executive-output/executive-agent/tests/test_integration_bdi_loop.py` | 45 | Accepts `"FAILED"` as a valid BDI loop outcome; masks OPA policy denial | Assert only `"COMPLETED"` or `"PARTIAL"` as success; fail on `"FAILED"` |
| W2 | `modules/group-ii-cognitive-processing/reasoning/tests/test_server.py` | 59 | `assert status_code in (200, 404)` on a registered route; masks a real 404 bug | Change to `assert status_code == 200` |
| W3 | `modules/group-iii-executive-output/motor-output/tests/test_feedback.py` | 108 | `test_preaction_signal_posted` never asserts that `respx` captured the POST | Add `respx.calls.assert_called_once()` or inspect `respx.calls.last.request` |
| W4 | `shared/vector-store/python/tests/test_chroma.py` + `test_qdrant.py` | all functions | ~45 test functions missing `-> None` return-type annotations | Add `-> None` to all test function signatures |
| W5 | `modules/group-iii-executive-output/agent-runtime/tests/test_orchestrator.py` | 93 | `tmp_path` typed as `pytest.TempPathFactory`; correct type is `pathlib.Path` | Fix annotation to `tmp_path: pathlib.Path` |
| W6 | `apps/default/client/tests/hooks/usePkceAuth.test.ts` | 69, 79 | Two tests named `"login() stores/constructs ..."` never call `login()` | Either call `login()` in the test body or rename the tests to match what they actually assert |
| W7 | `apps/default/client/tests/hooks/useSSEStream.test.ts` | 107 | Last-Event-ID reconnect flushes via 3× `await Promise.resolve()`; fragile tick counting | Use `vi.runAllTimersAsync()` or `flushPromises()` from `@vue/test-utils` |
| W8 | `infrastructure/mcp/tests/resources.test.ts` | multiple | Cleanup inside test body (not `afterEach`) affects all 11 transport tests; same pattern in OPA integration cleanup | Move teardown into `afterEach` hooks |
| W9 | `shared/vector-store/python/tests/test_chroma.py` | — | No `SKIP_CHROMA_TESTS` environment guard (unlike `test_qdrant.py` which has `SKIP_QDRANT_TESTS`) | Add `pytest.importorskip` or `@pytest.mark.skipif(os.getenv("SKIP_CHROMA_TESTS"), ...)` guard |

---

## 6. Tooling & Infrastructure Tasks

| # | Task | Impact | Effort |
|---|------|--------|--------|
| T1 | Install `pytest-cov` in **every** Python package (`uv add --dev pytest-cov`) and add `[tool.pytest.ini_options] addopts = "--cov=src --cov-report=term-missing"` to each `pyproject.toml` | Enables real coverage gating in CI | M |
| T2 | Install `@vitest/coverage-v8` in **every** TypeScript package and add `coverage: { provider: "v8" }` to each `vitest.config.ts` | Enables real coverage gating in CI | M |
| T3 | Expand `scripts/testing/scan_coverage_gaps.py` `PYTHON_PACKAGES` and `TS_PACKAGES` registries to include all 20+ packages (currently only 4 registered): add all `modules/group-i` through `group-iv` packages, `apps/default/server`, `apps/default/client`, `infrastructure/a2a`, `infrastructure/mcp`, `infrastructure/adapters` | Makes gap scanner authoritative | S |
| T4 | Add a separate `integration` CI job for the 4 permanently-skipped `group-ii/reasoning` integration tests that requires live LiteLLM + Ollama + ChromaDB; use `pytest -m integration` marker and appropriate `env:` block | Makes integration tests runnable without polluting unit test runs | M |
| T5 | Expand `group-iii` integration test suite from 4 test cases to cover the full pipeline: intent → planning → execution → feedback round-trip | 4 cases for an entire executive layer is insufficient | L |
| T5b | Expand `group-iv` integration test suite from 2 test cases | Same rationale | L |
| T6 | Set up integration test environment: use `docker compose up -d --wait` for standard services (ChromaDB, Ollama, Redis, OTel); create `scripts/healthcheck.sh` to verify Ollama has `nomic-embed-text` pulled; use Testcontainers only for OPA and Temporal. **Decided** — see Q2. | Enables repeatable integration test runs from CI and local | M |
| T7 | Add `SKIP_INTEGRATION_TESTS` monorepo-level coarse env var to all Python `conftest.py` files; each file skips its integration tests if `SKIP_INTEGRATION_TESTS` **or** the applicable per-service var (`SKIP_CHROMA_TESTS`, `SKIP_QDRANT_TESTS`, `SKIP_OPA_TESTS`, `SKIP_TEMPORAL_TESTS`) is set. **Decided** — see Q6. | Consistent skip behaviour across all packages | M |

---

## 7. Prioritised Upgrade Task List

Tasks are ordered by: (1) CI-blocking first, (2) systemic fixes before one-offs, (3) tooling
before new coverage work (tooling unlocks measurement).

| ID | Description | Effort | Owner | Prerequisites |
|----|-------------|--------|-------|---------------|
| P01 | Fix Regression 1 — add `goal_id="goal-004"` to `ActionSpec` in `test_feedback.py:91` | S | Implement | — |
| P02 | Fix Regression 2 — change OPA wait string to `"Initializing server"` in `test_integration_bdi_loop.py:35` | S | Implement | — |
| P03 | Fix Regression 3 — replace bracket notation with `.get()` on `Headers` in `mcp-client.test.ts:67` | S | Implement | — |
| P04 | Fix Q4 — add assertions to `test_loads_config_file` in `test_orchestrator.py:95` | S | Implement | — |
| P05 | Install `pytest-cov` in all Python packages (T1) | M | Implement | — |
| P06 | Install `@vitest/coverage-v8` in all TypeScript packages (T2) | M | Implement | — |
| P07 | Expand `scan_coverage_gaps.py` registry to all 20+ packages (T3). `DEFAULT_THRESHOLD = 80` is confirmed correct and is the hard floor — do not lower it; 80% is enforced immediately once tooling is installed. Long-term aspiration is as close to 100% as possible. | S | Implement | P05, P06 |
| P08 | Fix all 9 WARN issues (W1–W9) | M | Implement | P01–P03 |
| P09 | Add `a2a_handler.py` tests for all 10 untested modules (§3.1) | XL | Implement / Phase 3+4 Executive | — |
| P10 | Add `mcp_tools.py` tests for all 9 untested modules (§3.1) | XL | Implement / Phase 3+4 Executive | — |
| P11 | Add `otel_setup.py` tests for 4 untested modules (§3.1) | M | Implement | — |
| P12 | Add tests for `infrastructure/a2a/src/orchestrator.ts` and `validate.ts` | M | Implement | — |
| P13 | Add tests for `infrastructure/mcp/src/sync.ts` and `validate.ts` | M | Implement | — |
| P14 | Add tests for `apps/default/server/src/auth/sessions.ts` | M | Implement | — |
| P15 | Add tests for `apps/default/server/src/middleware/tracing.ts` and `routes/wellknown.ts` | S | Implement | — |
| P16 | Add tests for `apps/default/client/api/gateway.ts` | M | Implement | — |
| P17 | Add tests for `apps/default/client/auth/` (AuthProvider, LoginPage, useAuth, AuthContext) | M | Implement | — |
| P18 | **Phase A** — Add jsdom unit tests for all 7 `apps/default/client/tabs/Internals/` components using Vitest + React Testing Library; add `global.EventSource = vi.fn()` to `tests/setup.ts` for `SignalTraceFeed`. Aligns with existing Vitest setup. Phase B (Playwright integration tests) is tracked separately in P27 and depends on this task. | L | Implement | — |
| P19 | Add tests for `group-ii/long-term-memory/src/reconsolidation.py` | M | Phase 5 Memory Executive | — |
| P20 | Add tests for `agent-runtime` — two-track approach (decided, Q3): **(unit)** test `prefect_fallback._run_sequential()` with mocked httpx and no external deps; **(integration)** test `workflow.py` and `worker.py` using `temporalio.testing.WorkflowEnvironment.start_time_skipping()` (in-process, no Docker required) | L | Phase 6 Executive | — |
| P21 | Add test for `learning-adaptation/src/training/skill_feedback_callback.py` | M | Phase 4 Executive | — |
| P22 | Add tests for `shared/vector-store/python/src/embedding.py` | M | Implement | — |
| P23 | Add tests for `scripts/validate_frontmatter.py`, `fetch_source.py`, `fix_agent_tools.py` | M | Implement | — |
| P24 | Add integration CI job for reasoning module (T4): use `docker compose up -d --wait` for standard services; run `scripts/healthcheck.sh` to confirm Ollama has `nomic-embed-text`; Testcontainers for OPA and Temporal only. **Decided approach** — see Q2, T6. | M | Implement | T6 |
| P25 | Expand group-iii + group-iv integration test suites (T5, T5b) | L | Phase 6 Executive | P09, P10 |
| P26 | Review and update `scan_coverage_gaps.py` scanner logic (make config-missing warnings hard-fail with `exit 1`); create targeted specialist scanner scripts as needed — one script per domain if warranted. Every new or modified scanner script must open with a docstring/comment block describing its purpose, inputs, outputs, and usage example (per AGENTS.md script conventions). Extend, do not duplicate existing scripts. **Decided** — see Q4. | M | Implement | P05, P06, P07 |
| P27 | **Phase B** — Set up Playwright component testing (`@playwright/experimental-ct-react`) for `apps/default/client`; author integration tests covering all client-layer routes and key user flows. This is a separate track from the P18 jsdom unit tests, not a replacement. **Depends on P18 (Phase A) being complete.** Decided — see Q5 Phase B. | L | Implement | P18 |

---

## 8. Areas of Strength — Do Not Regress

The following test suites are high-quality and should be treated as canonical examples
when writing new tests elsewhere in the codebase.

| Package / File | Why it is a good example |
|---------------|--------------------------|
| `infrastructure/a2a/tests/` | Conformance and server tests — spec-pinned, full lifecycle (send → ack → result → error) |
| `shared/a2a/python/tests/test_client.py` | Error hierarchy fully tested; mock transport cleanly isolated |
| `modules/group-iv-adaptive-systems/learning-adaptation/tests/` | All 4 test files use real `async` patterns correctly, no `asyncio.run()` anti-patterns |
| `modules/group-iv-adaptive-systems/metacognition/tests/` | Uses real `MeterProvider`; no mock-everything shortcut |
| `apps/default/server/tests/auth.test.ts` | Full PKCE round-trip tested; auth state transitions covered |
| `apps/default/server/tests/gateway.test.ts` | CORS gating, error paths, response shapes all verified |
| `apps/default/server/tests/telemetry.test.ts` | Span creation and attribute correctness tested |
| `apps/default/client/tests/ChatTab.test.tsx` | ARIA role assertions + keyboard interaction coverage |
| `apps/default/client/tests/TabBar.test.tsx` | Accessible navigation, selected-state, keyboard flow |
| `modules/group-i-signal-processing/` (all 3 modules) | Best-covered module group (~75–80%); sensory-input, attention-filtering, perception are the reference bar for cognitive modules |
| `infrastructure/mcp/tests/` (broker, registry, well-known) | No issues; clean isolation |

---

## 9. Open Questions

### Decisions Log

All 6 questions are now DECIDED. Summary:

| Q | Decision |
|---|----------|
| Q1 | **80% line coverage for all packages**, enforced immediately once tooling is installed; long-term aspiration is as close to 100% as possible. No tiered thresholds; no ratchet. |
| Q2 | `docker compose up -d --wait` for standard services (ChromaDB, Ollama, Redis, OTel); `scripts/healthcheck.sh` verifies Ollama has `nomic-embed-text`; Testcontainers for OPA and Temporal only. |
| Q3 | Unit tests for `prefect_fallback._run_sequential()` (mock httpx, no deps); integration tests for `workflow.py` and `worker.py` via `temporalio.testing.WorkflowEnvironment.start_time_skipping()` (in-process, no Docker). |
| Q4 | Install tools + expand registry + hard-fail config warnings with `exit 1`; plus new task P26 for specialist scanner scripts with required AGENTS.md-compliant documentation. |
| Q5 | Phase A (P18): jsdom + targeted mocks for all Internals components; Phase B (P27, depends on P18): Playwright `@playwright/experimental-ct-react` integration tests for `apps/default/client`. |
| Q6 | `SKIP_INTEGRATION_TESTS` as monorepo-level coarse override; `SKIP_CHROMA_TESTS`, `SKIP_QDRANT_TESTS`, `SKIP_OPA_TESTS`, `SKIP_TEMPORAL_TESTS` as fine-grained per-service controls; each `conftest.py` checks coarse OR per-service var. |

---

1. **Coverage thresholds** — **DECIDED**: **80% line coverage for all packages**, enforced immediately once `pytest-cov` / `@vitest/coverage-v8` are installed (P05–P06). Long-term aspiration is as close to 100% as possible. The previously suggested two-tier approach (70% new / 60% existing) and any ratchet language are withdrawn. The `scan_coverage_gaps.py` `DEFAULT_THRESHOLD = 80` setting is confirmed correct and is a hard floor, not an overly strict suggestion. No special per-package exemptions below 80% are granted; `scripts/` entry-point packages follow the same floor.

2. **Integration test environment** — **DECIDED**: Use `docker compose up -d --wait` for standard services (ChromaDB, Ollama, Redis, OTel). Create `scripts/healthcheck.sh` to verify that Ollama has the `nomic-embed-text` model pulled (consistent with root `AGENTS.md` guidance). Use Testcontainers only for OPA and Temporal, which cannot be incorporated into the standard compose stack. Tasks P24 and T6 reflect this approach.

3. **`agent-runtime` workflow tests** — **DECIDED**: Two-track approach. **(1) Unit:** `prefect_fallback._run_sequential()` tested with mocked httpx and no external dependencies. **(2) Integration:** `workflow.py` and `worker.py` tested using `temporalio.testing.WorkflowEnvironment.start_time_skipping()` — in-process, no Docker or Temporal dev server required. Task P20 reflects this.

4. **`scan_coverage_gaps.py` authority** — **DECIDED**: Install tools (P05–P06) + expand registry (P07) + make config-missing warnings hard-fail with `exit 1`. Additionally, a new task (P26) covers reviewing and updating the scanner logic and creating targeted specialist scanner scripts (one per domain if warranted). Per AGENTS.md script conventions, every new or modified scanner script must open with a docstring/comment block describing its purpose, inputs, outputs, and usage example. Documentation is required for every new or modified scanner script.

5. **Client component tests** — **DECIDED (two-phase)**:
   - **Phase A** (confirmed, unblocks P18): jsdom + targeted mocks for all Internals tab components using the existing Vitest + React Testing Library setup. Add `global.EventSource = vi.fn()` to `tests/setup.ts` for `SignalTraceFeed`'s EventSource dependency. P18 proceeds immediately.
   - **Phase B** (new, P27): Full Playwright integration testing for `apps/default/client` using `@playwright/experimental-ct-react` component testing mode. This is a separate track from Phase A jsdom unit tests, not a replacement. Phase B depends on Phase A (P18) being complete.

6. **SKIP guards** — **DECIDED**: Introduce `SKIP_INTEGRATION_TESTS` as a monorepo-level coarse override env var. Retain `SKIP_CHROMA_TESTS`, `SKIP_QDRANT_TESTS`, `SKIP_OPA_TESTS`, and `SKIP_TEMPORAL_TESTS` as fine-grained per-service controls. Each `conftest.py` must skip its integration tests if **either** the coarse var **or** the per-service var is set. New Testcontainer-dependent tests (including OPA and Temporal via T6) must follow this pattern. Task T7 implements this.

---

## Related References

- [docs/Workplan.md](Workplan.md) — phase-by-phase implementation roadmap
- [docs/architecture.md](architecture.md) — component map and signal-flow diagrams
- [scripts/testing/](../scripts/testing/) — gap scanner and coverage tooling
- [shared/a2a/python/README.md](../shared/a2a/python/README.md) — A2A client reference (example of well-tested shared package)
- [CONTRIBUTING.md](../CONTRIBUTING.md) — branch naming, PR guidelines, coding standards
- [AGENTS.md](../AGENTS.md) — `uv run` requirement, commit discipline, guardrails
