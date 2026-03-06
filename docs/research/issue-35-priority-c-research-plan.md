# Issue #35 Priority C — Research Plan: Local Compute & Model Fallback

> **Status**: ⬜ DRAFT — Awaiting review and approval before execution  
> **Scope**: Issue #35 Priority C + cross-issue research tasks (#32, #33, #34, #36)  
> **Branch**: `feat/issue-35-programmatic-stance` (or a new branch post-merge)  
> **Produced by**: Executive Planner (delegated from Executive Orchestrator, 2026-03-05)  
> **For**: Human review before any agent proceeds

---

## Contents

1. [Background & Issue Cross-Map](#1-background--issue-cross-map)
2. [Research Domain A — Local Compute for VS Code Copilot](#2-research-domain-a--local-compute-for-vs-code-copilot)
3. [Research Domain B — Local / Distributed MCP Frameworks](#3-research-domain-b--local--distributed-mcp-frameworks)
4. [Research Domain C — Free-Tier & Model Fallback Strategy](#4-research-domain-c--free-tier--model-fallback-strategy)
5. [Research Domain D — Async Terminal Process Handling (#33)](#5-research-domain-d--async-terminal-process-handling-33)
6. [Research Domain E — Architectural Research Source Manifest (#32)](#6-research-domain-e--architectural-research-source-manifest-32)
7. [Research Domain F — Background Reading (#34, #36)](#7-research-domain-f--background-reading-34-36)
8. [Sequencing & Agent Delegation Map](#8-sequencing--agent-delegation-map)
9. [Deliverables Checklist](#9-deliverables-checklist)
10. [Open Questions](#10-open-questions)

---

## 1. Background & Issue Cross-Map

### Issue #35 Priority C (this plan)

> Establish local / locally networked compute for VS Code Copilot to utilize.
> Research / document how to run as much of VS Code Copilot locally as possible.
> Research / document / synthesize methodologies on locally distributing MCP frameworks.

Priority C depends on Priorities A and B being stable (done ✅). It is unblocked.

### Cross-issue dependencies

| Issue | Title | Relevance to #35-C |
|-------|-------|-------------------|
| **#32** | Architectural Research | Contains 20+ links to MCP frameworks, local LLM tools, agent architectures — directly feeds Domain B and D |
| **#33** | Handling Async processes in the terminal | Informs Executive Automator scope; research deliverable is agent-guidance documentation for long-running processes |
| **#34** | Product Design, Research, and Definition | Background context; lower priority — note in Domain F |
| **#36** | Extensive lit review of AI in ScFi | Background context; lowest priority — note in Domain F |

---

## 2. Research Domain A — Local Compute for VS Code Copilot

**Goal**: Document exactly what can be run locally on macOS (your M3/M4 machines) for
VS Code Copilot, including Sheela's M4 as a networked inference server.

### Sub-questions

1. **Local LLM inference for Copilot completions**: Can VS Code Copilot be pointed at a
   local Ollama or LM Studio endpoint for completions and chat? What is the setup?
2. **Sheela's M4 as a shared inference node**: What is the minimum viable setup to expose
   an Ollama instance on Sheela's Mac as a LAN endpoint accessible from your Mac in
   VS Code Copilot?
3. **Which model sizes run well on M4?**: What quantisation levels (Q4_K_M, Q8, etc.)
   for Claude-equivalent models (Qwen 2.5, Llama 3.3, Mistral) are practical on 16–32 GB
   M4 unified memory for coding tasks?
4. **Network topology**: Tailscale vs. LAN vs. mDNS — what is the lowest-friction setup
   for two Macs sharing an Ollama endpoint?

### Approach

1. Check if `scripts/` already has a relevant healthcheck or setup guide — extend if so.
2. Use `fetch_source.py` to pull the following key sources (from issue #32's checklist):
   - `https://www.xda-developers.com/youre-using-local-llm-wrong-if-youre-prompting-it-like-cloud-llm/`
   - LM Studio offline-first article (Google share link in #32 — search for canonical URL first)
3. Web-search: "VS Code Copilot local LLM endpoint 2025", "Ollama LAN shared inference macOS"
4. Write findings to `docs/research/local-compute-findings.md`

### Deliverable

`docs/research/local-compute-findings.md` — covering:
- Step-by-step local inference setup (Ollama on M4)
- Network sharing setup (Sheela's Mac → your Mac)
- Recommended model sizes / quantisations for coding tasks
- VS Code Copilot configuration to point at local endpoint

---

## 3. Research Domain B — Local / Distributed MCP Frameworks

**Goal**: Survey existing MCP framework implementations suitable for local or LAN-distributed
deployment; identify best practices for this project's architecture.

### Sub-questions

1. What open-source MCP server implementations exist beyond the reference implementation?
2. Which support local-first deployment (no cloud dependency)?
3. How do they handle multi-agent routing, tool discovery, and auth locally?
4. What are the performance characteristics on Apple Silicon?
5. What is the state of locally-distributed MCP (multiple MCP servers on a LAN)?

### Approach

1. Use `fetch_source.py` to pull key sources from issue #32:
   - `https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills`
   - `https://opensourceprojects.dev/post/e7415816-a348-4936-b8bd-0c651c4ab2d8`
   - `https://www.docker.com` Docker AI for agent builders link (find canonical from #32)
   - `https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/`
   - `https://github.com/originalankur/GenerateAgents.md`
   - `https://arxiv.org/html/2512.05470v1`
2. Web-search: "MCP server local deployment LAN 2025", "distributed MCP framework multi-node"
3. Scan pulled sources for secondary links → add to `docs/research/sources/mcp-followup-manifest.md`
4. Write synthesis to `docs/research/mcp-local-distribution-findings.md`

### Deliverable

`docs/research/mcp-local-distribution-findings.md` — covering:
- Candidate MCP frameworks with local-first support
- Architecture patterns for LAN-distributed MCP
- Recommended approach for EndogenAI's Phase 9+ architecture
- Points of integration with existing `infrastructure/mcp/`

---

## 4. Research Domain C — Free-Tier & Model Fallback Strategy

**Goal**: Document a practical model-tiering strategy for this project — reducing Claude
Sonnet 4.6 token spend by routing lower-stakes tasks to free-tier or cheaper models.

### Sub-questions

1. What models are available on the VS Code Copilot Auto tier (free or lower-cost)?
2. What does the Auto model actually route to — is the routing transparent and
   configurable?
3. Which agent tasks are suitable for free-tier models vs. require Claude Sonnet 4.6?
4. How do we encode model-tier preferences in agent files without hardcoding a model
   that may change?

### Approach

1. Web-search: "VS Code Copilot Auto model 2026 routing", "GitHub Copilot model tiers free"
2. Cross-reference existing `AGENTS.md` to identify which agents are critical-path
   (should stay on Sonnet 4.6) vs. supportive (can downgrade)
3. Propose a tiering table in the research doc

### Deliverable

`docs/research/model-fallback-strategy.md` — covering:
- VS Code Copilot Auto model capabilities and routing (as of 2026-03)
- Recommended task-to-tier mapping (table)
- Draft guidance text for `AGENTS.md` "Model Selection" section (for human review
  before merging)
- Decision log: what to hardcode vs. leave to auto-routing

---

## 5. Research Domain D — Async Terminal Process Handling (#33)

**Goal**: Produce agent-guidance documentation for handling async/long-running terminal
processes — addressing issue #33 directly.

### Sub-questions from #33

1. When should an agent make a process synchronous vs. use interval check-ins?
2. What timeout limits are appropriate for: model downloads, Docker builds, test runs?
3. How should agents handle observable-status processes (Docker, pip install) vs.
   silent processes (background scripts)?
4. How should executive agents request/delegate status checks for long-running sub-agents?
5. What observability APIs exist for the tools agents use (Docker, uv, pytest, pnpm)?

### Approach

1. Review `scripts/watch_scratchpad.py` as a reference for the interval/cooldown pattern
   already in use in this codebase.
2. Review `scripts/healthcheck.sh` for timeout patterns.
3. Web-search: "VS Code Copilot agent terminal timeout patterns", "MCP async tool handling"
4. Document findings as a new section in `docs/guides/agents.md` (existing agent guide)
   rather than a standalone file — keeps guidance co-located with agent usage docs.

### Deliverable

Addition to `docs/guides/agents.md`: **Async Terminal Process Handling** section, covering:
- Decision table: sync vs. interval vs. timeout
- Recommended timeout values by task type
- Code-pattern examples (polling with sleep, background PID tracking)
- Observability API reference for Docker, uv, pnpm, pytest

---

## 6. Research Domain E — Architectural Research Source Manifest (#32)

**Goal**: Execute the `fetch_source.py` workflow for issue #32's research checklist.
This is a prerequisite for Domains A and B above.

### Approach

The issue #32 specifies this workflow exactly:
```
1. Create a research manifest for the links listed in #32
2. Use fetch_source.py to pull sources (exclude YouTube, x.com)
3. For YouTube: web-search for description/transcript; add canonical source to manifest
4. Scan pulled sources for secondary links → followup manifest
5. Write Gate 1 deliverable: synthesised findings
```

### Agent assignment

→ **Docs Executive Researcher** (designated for pre-planning research passes)  
→ Restrict scope: `docs/research/sources/`, `scripts/fetch_source.py`, web searches only  
→ Do NOT modify `docs/Workplan.md` or any source code in this pass

### Deliverable

- `docs/research/sources/issue-32-manifest.md` — all fetched source URLs with one-line descriptions
- `docs/research/sources/issue-32-followup-manifest.md` — secondary links found in pulled sources
- `docs/research/architectural-research-synthesis.md` — Gate 1 synthesis document

---

## 7. Research Domain F — Background Reading (#34, #36)

These are lower-priority; capture them for awareness.

**#34 — Product Design, Research, and Definition**  
Strategic product direction. Not immediately actionable for engineering. Recommend:
- Assign a reading session to the Executive Orchestrator or human review
- No agent delegation needed now; flag for a "product design" session post-PR #41 merge

**#36 — Extensive lit review of AI in ScFi**  
Long-term cultural/ethical background reading. Explicitly low-priority.
- Assigned to human (@AccessiT3ch, @Copilot per issue)
- No immediate engineering deliverable
- Recommend: create a research brief outline as a scratchpad note during a low-token session

---

## 8. Sequencing & Agent Delegation Map

```
Executive Orchestrator
  │
  ├─ [Can run in parallel once #32 manifest is pulled]
  │
  ├─ @Docs Executive Researcher
  │    Scope: issue-32-manifest (all non-YT/X links)
  │    Output: docs/research/sources/issue-32-manifest.md
  │    → reports back to Orchestrator
  │
  ├─ @Implement (or Docs Scaffold)
  │    Scope: Domain D — async terminal guidance addition to docs/guides/agents.md
  │    Input: patterns from healthcheck.sh + watch_scratchpad.py
  │    Output: docs/guides/agents.md addition
  │    → Review → commit
  │
  └─ After manifest complete:
       @Docs Executive Researcher (pass 2)
         Scope: Domains A + B — pull sources from manifest, web-search, synthesise
         Output: local-compute-findings.md + mcp-local-distribution-findings.md
         → Review → commit
       @Implement (or Docs Scaffold)
         Scope: Domain C — model fallback strategy
         Output: model-fallback-strategy.md
         → Review → commit
```

**Estimated session budget**: Domains A+B+D = ~1 full session. Domain C = ~0.5 session.
Domain E (manifest fetch) = ~0.5 session. Recommend sequencing E first.

---

## 9. Deliverables Checklist

- [ ] `docs/research/sources/issue-32-manifest.md` — source manifest for #32 links
- [ ] `docs/research/sources/issue-32-followup-manifest.md` — secondary link followup
- [ ] `docs/research/architectural-research-synthesis.md` — Gate 1 synthesis (#32)
- [ ] `docs/research/local-compute-findings.md` — Domain A
- [ ] `docs/research/mcp-local-distribution-findings.md` — Domain B
- [ ] `docs/research/model-fallback-strategy.md` — Domain C
- [ ] Addition to `docs/guides/agents.md` — Domain D (async terminal handling)

---

## 10. Open Questions

| Question | Owner | Blocking? |
|----------|-------|-----------|
| Does VS Code Copilot support a custom local LLM endpoint directly, or only via an MCP tool? | Research | Yes — affects Domain A scope |
| Is Sheela's Mac on the same LAN or would Tailscale be needed? | Human | Affects Domain A networking sub-question |
| Should model-tier recommendations be encoded in agent `.agent.md` files as a new field, or only in `AGENTS.md` prose? | Human | Affects Domain C deliverable format |
| Issue #32 has Google Share links (non-canonical). Should we web-search for canonical URLs first, or have the agent attempt to follow them? | Human | Affects Domain E workflow |
