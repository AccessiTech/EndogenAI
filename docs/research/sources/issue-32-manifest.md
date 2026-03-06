# Issue #32 — Source URL Manifest

_Compiled: 2026-03-05 by Docs Executive Researcher_
_Source issue: GitHub Issue #32 (architectural research backlog, branch feat/issue-35-programmatic-stance)_

All links extracted from the Issue #32 body and verified or researched as of 2026-03-05.

---

## Verified Canonical URLs

| # | Title | Canonical URL | Status | Notes |
|---|---|---|---|---|
| 1 | Creating agent skills for GitHub Copilot CLI | https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills | ✅ verified | GitHub Docs |
| 2 | You're using your local LLM wrong if you're prompting it like a cloud LLM | https://www.xda-developers.com/youre-using-local-llm-wrong-if-youre-prompting-it-like-cloud-llm/ | ✅ verified | XDA Developers |
| 3 | GenerateAgents.md — Auto-generate AGENTS.md via DSPy RLM | https://github.com/originalankur/GenerateAgents.md | ✅ verified | GitHub repo; Python tool using DSPy + LiteLLM; supports Ollama endpoints |
| 4 | Pinchtab: headless browser fleet orchestrator | https://opensourceprojects.dev/post/e7415816-a348-4936-b8bd-0c651c4ab2d8 | ✅ fetched | Node.js; headless browser fleet; not directly an MCP/agent framework |
| 5 | Claude Skills and Subagents: Escaping the Prompt Engineering Hamster Wheel | https://towardsdatascience.com/claude-skills-and-subagents-escaping-the-prompt-engineering-hamster-wheel/ | ✅ verified | Towards Data Science |
| 6 | Build and Deploy Multi-Agent AI with Python and Docker | https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/ | ✅ verified | FreeCodeCamp; covers `host.docker.internal:11434` for Ollama in Docker |
| 7 | The AI Coding Loop: How to Guide AI With Rules and Tests | https://www.freecodecamp.org/news/how-to-guide-ai-with-rules-and-tests/ | ✅ verified | FreeCodeCamp |
| 8 | Everything is Context: Agentic File System Abstraction (AIGNE Framework) | https://arxiv.org/html/2512.05470v1 | ✅ verified | arxiv; supports MCP + Ollama/OpenAI/Claude/Gemini/DeepSeek as mountable modules |
| 9 | Google AI Introduces STATIC: A Sparse Matrix Framework Delivering 948x Faster Constrained Decoding | https://www.marktechpost.com/2026/03/01/google-ai-introduces-static-a-sparse-matrix-framework-delivering-948x-faster-constrained-decoding-for-llm-based-generative-retrieval/ | ✅ verified | MarkTechPost; paper: https://arxiv.org/pdf/2602.22647 |
| 10 | A Coding Implementation: Hierarchical Planner AI Agent Using Open-Source LLMs | https://www.marktechpost.com/2026/02/27/a-coding-implementation-to-build-a-hierarchical-planner-ai-agent-using-open-source-llms-with-tool-execution-and-structured-multi-agent-reasoning/ | ✅ verified | MarkTechPost; uses Qwen2.5-1.5B-Instruct; code: GitHub Marktechpost/AI-Tutorial-Codes-Included |
| 11 | Meet NullClaw: The 678 KB Zig AI Agent Framework Running on 1 MB RAM | https://www.marktechpost.com/2026/03/02/meet-nullclaw-the-678-kb-zig-ai-agent-framework-running-on-1-mb-ram-and-booting-in-two-milliseconds/ | ✅ verified | MarkTechPost; repo: https://github.com/nullclaw/nullclaw |

---

## Unresolved Links

| # | Title (from issue) | Original Link | Resolution Status | Notes |
|---|---|---|---|---|
| A | I let an AI agent organize my entire PC, and it actually worked | https://share.google/DG67eTC9m4VI6DQlD | ❌ Google Share redirect — unresolvable via fetch | Title suggests PC automation / file-organisation agent demo |
| B | How I built a Claude Code workflow with LM Studio for offline-first development | https://share.google/eRjsjmfC7gsXy4MAD | ❌ Google Share redirect; Medium + InfoWorld 404 | Article describes LM Studio BYOK with Claude Code; likely originally on Medium or Substack |
| C | Scientists made AI agents ruder — and they performed better at complex reasoning tasks | https://share.google/c1CmKbnmrAZFaTv5T | ❌ Google Share redirect → spam redirect | Live Science article (livescience.com); direct URL: https://www.livescience.com/technology/artificial-intelligence/scientists-made-ai-agents-ruder-and-they-performed-better-at-complex-reasoning-tasks (resolves to ad-redirect) |
| D | Docker AI for agent builders: models, tools and cloud offload | https://www.kdnuggets.com/docker-ai-for-agent-builders-models-tools-and-cloud-offload | ❌ HTTP 403 | KDNuggets; content likely behind auth wall or moved |

---

## Excluded Links (not suitable for manifest)

| Type | URL | Reason |
|---|---|---|
| X/Twitter | https://x.com/i/status/2028417556986650699 | openFang post; requires login; ephemeral |
| YouTube | https://youtu.be/GDm_uH6VxPY?si=8vgAq-jqLcYMkepf | Video; no fetchable canonical text |
| YouTube | https://youtu.be/Mi5wOpAgixw?si=DtXH3HhiF_n5tfmg | Video; no fetchable canonical text |

---

## Key Themes Across Resolved Sources

1. **Local-first inference**: Multiple articles (XDA, LM Studio, Ollama) affirm that prompting
   local models requires different patterns than cloud models — shorter system prompts,
   explicit JSON schemas, lower temperature. Relevant to all EndogenAI agent configs.

2. **Hierarchical agent architecture**: The MarkTechPost tutorial (item 10) demonstrates a
   planner→executor→aggregator pattern using `Qwen2.5-1.5B-Instruct` — directly applicable
   to EndogenAI's group-iii executive-output layer.

3. **Context engineering > prompt engineering**: AIGNE paper (item 8) frames agentic work as
   file-system operations on context, not prompt iteration. Aligns with EndogenAI's
   endogenous-first principle.

4. **Lightweight agent runtimes for edge**: NullClaw (item 11) demonstrates 678 KB / 1 MB RAM
   Zig-based agent framework. Relevant if EndogenAI needs low-overhead signal-processing
   modules or embedded deployment targets.

5. **Auto-generating AGENTS.md**: GenerateAgents.md (item 3) uses DSPy RLM to derive agent
   specifications from a codebase — could automate AGENTS.md maintenance as codebase grows.

6. **Constrained decoding at scale**: STATIC (item 9) solves structured output enforcement at
   YouTube scale. Context-relevant if EndogenAI modules need guaranteed JSON schema compliance
   from local models (current workaround: schema prompting + retry logic).
