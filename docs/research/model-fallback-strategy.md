# Model Fallback Strategy — Issue #35 Priority C (Domain C)

_Researched: 2026-03-06 by Docs Executive Researcher_
_Sources: GitHub Copilot docs (docs.github.com, fetched 2026-03-06)_

---

## 1. VS Code Copilot Model Tiers (as of 2026-03)

### Plan overview

| Plan | Price | Chat | Completions | Premium requests/mo |
|------|-------|------|-------------|---------------------|
| **Free** | $0 | 50 messages/month | 2,000/month | 50 |
| **Pro** | $10/month | Unlimited (included models) | Unlimited | 300 |
| **Pro+** | $39/month | Unlimited (all models) | Unlimited | 1,500 |
| **Business** | $19/seat/month | Unlimited (included models) | Unlimited | 300/user |
| **Enterprise** | $39/seat/month | Unlimited (included models) | Unlimited | 1,000/user |

**Included models** (zero premium requests on paid plans): GPT-5 mini, GPT-4.1, GPT-4o.

### Free-tier model access

Free-tier users may select from the following models; each costs **one premium request** per
interaction (50/month total):

| Model | Premium multiplier (Free) |
|-------|--------------------------|
| Claude Haiku 4.5 | 1 (normally 0.33 on paid) |
| GPT-4.1 | 1 (free on paid) |
| GPT-5 mini | 1 (free on paid) |
| Grok Code Fast 1 | 1 (normally 0.25 on paid) |
| Raptor mini | 1 (free on paid) |
| Goldeneye | 1 (exclusive to Free tier) |

> Claude Sonnet 4.6, Claude Opus, Gemini, and GPT-5.x series are **not available** on Free.

### Model multipliers on paid plans

| Model | Multiplier (paid) | Notes |
|-------|-------------------|-------|
| GPT-5 mini / GPT-4.1 / GPT-4o | **0** | Included; no premium request spend |
| Raptor mini | **0** | Included |
| Claude Haiku 4.5 | **0.33** | Good for lightweight tasks |
| Grok Code Fast 1 | **0.25** | Fast; low cost |
| Gemini 3 Flash | **0.33** | Fast / lightweight |
| Claude Sonnet 4.5 / 4.6 | **1.0** | Current EndogenAI default |
| Gemini 2.5 Pro / 3 Pro / 3.1 Pro | **1.0** | |
| GPT-5.1 / 5.2 series | **1.0** | |
| Claude Opus 4.5 / 4.6 | **3.0** | Expensive; avoid unless required |
| Claude Opus 4.6 (fast mode) | **30.0** | Extreme cost; reserve for benchmarking only |

---

## 2. Copilot "Auto" Model Routing (as of 2026-03)

> **Source**: `docs.github.com/en/copilot/concepts/auto-model-selection` (fetched 2026-03-06)

Auto model selection is **generally available in VS Code**; public preview in VS, JetBrains,
Eclipse, Xcode.

### What Auto selects from

When a user picks "Auto" in Copilot Chat, the router chooses from this pool
(subject to plan and policy):

- GPT-4.1
- GPT-5.2-Codex
- GPT-5.3-Codex
- Claude Haiku 4.5
- Claude Sonnet 4.5
- Grok Code Fast 1
- Raptor mini

**Hard exclusions** — Auto will never select:
- Any model with premium multiplier > 1 (rules out Opus, GPT-5.4, etc.)
- Models blocked by org/enterprise policy
- Models not available in the user's plan

### Routing logic (current)

> "Copilot auto model selection is currently optimised for **model availability**,
> choosing from a list of models that may change over time."
> — GitHub Docs

Task-aware routing is **announced but not yet live**. A note from the docs reads:
> "Soon Copilot auto model selection will choose the best model for you by taking into
> account both model availability and your task."

**Practical implication**: Do not rely on Auto to select the most capable model for a given
task — it currently picks based on load/availability. Agents running critical-path tasks
(implementation, schema authoring) should explicitly name the model.

### 10% premium discount with Auto

Paid-plan users get a 10% multiplier discount when using Auto (e.g., Sonnet 4.5 at 1.0×
becomes 0.9×). This does **not** apply to Copilot Free.

---

## 3. Task-to-Tier Mapping Table

The columns below use the following shorthands:

- **Sonnet 4.6** — Claude Sonnet 4.6 (explicit; 1.0× premium)
- **Auto** — Copilot Auto (availability-routed; ≤1.0× pool; 10% discount on paid)
- **Included** — GPT-5 mini / GPT-4.1 / Raptor mini (0× premium on paid)
- **Haiku 4.5** — Claude Haiku 4.5 (0.33× premium; good quality for lightweight text)
- **Local** — Ollama on-device (from Domain A findings; no cloud cost)

| Task type | Recommended tier | Rationale | Local model substitute |
|-----------|-----------------|-----------|------------------------|
| Cold-start orientation / workplan reading | **Auto** | High-context read; no code changes required; load-routing acceptable | `qwen2.5:7b` (adequate for summarisation; no tool-calling) |
| Implementation (code changes, multi-file) | **Sonnet 4.6** | Agentic tool-calling; quality-critical; Auto pool does not guarantee capable model | None — local models lack reliable multi-file agentic editing |
| Documentation authoring | **Included** (GPT-5 mini) or **Haiku 4.5** | Prose generation; no tool-calling; fast turnaround | `qwen2.5:7b` or `qwen2.5-coder:7b` via BYOK chat |
| Research / web-search synthesis | **Sonnet 4.6** | Correct source attribution; synthesis quality critical; web tool access | None — local models have no web access |
| Schema authoring and validation | **Sonnet 4.6** | Precision required; downstream consumers depend on schema correctness | None |
| Test scaffolding (stubs only) | **Haiku 4.5** or **Included** | Template-like output; no deep reasoning needed | `qwen2.5-coder:7b` — strong HumanEval performance |
| Review (read-only audit) | **Auto** | Comprehensive read; no writes; load-routing acceptable during review passes | `qwen2.5:7b` for lightweight checks; not a substitute for full audit |
| Git / PR operations (CLI) | **Included** | Terminal-adjacent text operations; low complexity | N/A — git operations are deterministic CLI, not model-dependent |
| Embeddings | **Local** (`nomic-embed-text`) | Already mandated by AGENTS.md; 768-dim; no cloud cost | `nomic-embed-text` (Ollama, mandatory default) |
| Simple read-only file inspection | **Included** (Raptor mini) | Zero premium; fast; adequate for file reads and quick questions | Any local model — `qwen2.5:7b` for chat, `qwen2.5-coder:7b` for code |
| Long-running agent mode sessions | **Auto** (with Sonnet 4.6 fallback) | Auto discount helps with per-turn cost; fall back to Sonnet 4.6 if quality degrades | `qwen2.5:7b` for tool-calling scaffolding only |
| Scratchpad / session summarisation | **Included** or **Haiku 4.5** | Short prose; no tool-calling; low stakes | `qwen2.5:7b` |

### Priority classification

**Must stay on Sonnet 4.6 (or equivalent ≥1× model):**
- Multi-file implementation with agentic tool-calling
- Schema authoring and migration
- Research synthesis with citation requirements

**Can move to Auto or Included (with no quality regression on typical tasks):**
- Workplan reading and orientation
- Documentation authoring
- Test scaffolding (stubs)
- Git/PR CLI operations
- Session/scratchpad summarisation
- Review passes (read-only)

**Should move fully local (already done or straightforward):**
- Embeddings (`nomic-embed-text` via Ollama — already AGENTS.md spec)
- Simple file inspection and grep-style queries
- Documentation-authoring via Continue.dev chat where cloud unavailable

---

## 4. Draft `## Model Selection` Section for Root `AGENTS.md`

> **Status: DRAFT ONLY — not to be committed to `AGENTS.md` directly.** This section is for
> human review. Copy-paste when approved.

Note: the draft below includes the `COPILOT_PLAN` config variable (Q4 decision)
   and a quarterly-review anchor for the CI lint rule (Q1 decision).

   ```markdown
## Model Selection

All LLM inference in EndogenAI source code routes through LiteLLM — direct SDK calls to
Anthropic, OpenAI, or Ollama are prohibited.

For **agent sessions** (VS Code Copilot Chat), the following tiering applies:

### Choosing the right model

| Task category | Model recommendation |
|---------------|---------------------|
| Multi-file implementation, schema authoring, research synthesis | **Claude Sonnet 4.6** (explicit) |
| Workplan reading, orientation, review (read-only) | **Copilot Auto** |
| Documentation, test stubs, git/PR CLI | **Included** (GPT-5 mini / GPT-4.1) or **Claude Haiku 4.5** |
| Embeddings | **Local** — `nomic-embed-text` via Ollama (mandatory) |

**Copilot Auto** routes among GPT-4.1, GPT-5.2-Codex, GPT-5.3-Codex, Claude Haiku 4.5,
Claude Sonnet 4.5, Grok Code Fast 1, and Raptor mini. It is optimised for load/availability,
not task quality. Use it for read-heavy and lower-stakes tasks; override to Sonnet 4.6 for
any task where output quality has downstream consequences.

**Local LLM inference** (Ollama, BYOK via VS Code `Chat: Manage Language Models`):
- Chat / general reasoning: `qwen2.5:7b`
- Code completion / coding chat: `qwen2.5-coder:7b`
- Embeddings: `nomic-embed-text` (required default)
- Local models do **not** support inline completions — use Continue.dev extension for that.

### Free-tier considerations

Copilot Free is limited to 50 chat messages and 2,000 completions per month. All chat
interactions consume a premium request on Free. For extended agent sessions, a Pro plan
(300 premium requests/month, unlimited included-model chat) is strongly recommended.

### Stability caveat

Auto model pool and premium multipliers are subject to change without notice by GitHub.
Verify current values at:
- Plans: `docs.github.com/en/copilot/get-started/plans`
- Auto pool: `docs.github.com/en/copilot/concepts/auto-model-selection`
- Multipliers: `docs.github.com/en/copilot/concepts/billing/copilot-requests#model-multipliers`
```

---

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| Prose-only section in `AGENTS.md` (no new frontmatter field) | Simpler first; a structured `model-tier:` frontmatter field in `.agent.md` files can be added if the fleet grows and per-agent overrides become common. Prose is human-readable and sufficient for the current fleet size (~30 agents). |
| Sonnet 4.6 hardcoded for implementation, schema, research | These are quality-critical paths where a load-balanced Auto could silently downgrade to Raptor mini or Haiku 4.5. Explicit selection removes routing uncertainty. |
| Auto acceptable for read-only, orientation, review | Routing uncertainty is acceptable when output is advisory or human-reviewed before any commit. 10% discount also helps with session length. |
| Local models endorsed for docs/test-stubs but NOT implementation | `qwen2.5-coder:7b` performs well on HumanEval for isolated functions but lacks the tool-calling reliability needed for EndogenAI's multi-file agentic workflows. |
| Inline completions excluded from local recommendation for agent sessions | VS Code BYOK (Ollama chat) cannot satisfy the inline completion API — that requires Continue.dev. Agents in Copilot Chat mode are unaffected; this only matters for human developer experience. |
| No recommendation to use Claude Opus | 3× multiplier drains a Pro plan's 300 premium requests in ~100 turns. Sonnet 4.6 at 1× is the practical ceiling for sustained agent work. |

---

## 6. Sources

| Source | URL | Fetched |
|--------|-----|---------|
| Plans for GitHub Copilot | `https://docs.github.com/en/copilot/get-started/plans` | 2026-03-06 |
| Requests in GitHub Copilot (premium + multipliers) | `https://docs.github.com/en/copilot/concepts/billing/copilot-requests` | 2026-03-06 |
| About Copilot auto model selection | `https://docs.github.com/en/copilot/concepts/auto-model-selection` | 2026-03-06 |
| AI model comparison | `https://docs.github.com/en/copilot/reference/ai-models/model-comparison` | 2026-03-06 |
| Domain A — Local compute findings | `docs/research/local-compute-findings.md` | 2026-03-05 |

---

## 7. Decisions — Resolved 2026-03-06

1. **Auto pool stability** ✅
   Add a **quarterly review CI lint rule** that fails with a warning comment when the
   `AGENTS.md ## Model Selection` section's "last reviewed" date is more than 90 days old.
   This keeps the tier table from going stale as Copilot's Auto pool evolves.
   → Task: `scripts/lint/check_model_review_date.py` (to be implemented by Executive Scripter).

2. **Continue.dev integration** ✅
   Incorporate Continue.dev as the recommended inline-completion path for local models.
   Human will be hands-on for setup when ready. The new-machine setup wizard (see
   `docs/research/local-compute-findings.md §New Machine Setup`) will include a
   Continue.dev configuration step.

3. **LiteLLM model aliases — development savings first** ✅
   Scope of this document is **agent-session (developer) token savings only**.
   Once local-compute setup is validated in development, the cost-reduction findings
   will be brought to module-level LiteLLM config (Phases 5–7 source code) in a
   separate pass. Do not conflate agent-session choices with production inference routing.

4. **Subscription tier — Copilot Pro; make configurable** ✅
   Current plan: **Copilot Pro** (individual). BYOK/local Ollama is supported on Pro.
   BYOK is disabled on Business and Enterprise plans.
   Introduce a config variable `COPILOT_PLAN` (values: `free` | `pro` | `business` |
   `enterprise`) so guidance that depends on plan tier is gated at a single point.
   Document in `AGENTS.md ## Model Selection` draft (§4 of this file) and in the
   new-machine setup wizard. If the plan changes, update this variable and re-run the
   setup wizard to regenerate applicable guidance.
