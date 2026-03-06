# Local Compute Findings — Issue #35 Priority C

_Researched: 2026-03-05 by Docs Executive Researcher_
_Sources: VS Code docs (code.visualstudio.com/docs/copilot/language-models, fetched 2026-03-05)_

---

## Domain A — VS Code Copilot + Local LLM Endpoint

### Blocking Question (from research plan)
> Can VS Code Copilot use a custom local LLM endpoint (e.g. Ollama at `localhost:11434`)
> directly via configuration, or does it require an MCP wrapper?

### Answer: Direct config — no MCP wrapper needed for chat

As of VS Code 1.104 (released ~February 2026), VS Code ships a **Language Models editor**
(`Chat: Manage Language Models`) that supports "Bring Your Own Key" (BYOK) model providers.
**Ollama is a built-in provider** — no extension, no MCP wrapper, no proxy required for chat.

**Steps to configure:**
1. Open VS Code command palette → `Chat: Manage Language Models`
2. Click **Add Models** → select **Ollama**
3. Select model from list (e.g. `qwen2.5-coder:7b`, `phi-4`)
4. The model appears in the model picker in the Chat panel

**Custom OpenAI-compatible endpoint (Insiders only as of 1.104):**
```json
// settings.json
"github.copilot.chat.customOAIModels": [
  {
    "id": "local-qwen",
    "baseURL": "http://localhost:11434/v1",
    "apiKey": "ollama"
  }
]
```

### Critical limitations

| Capability | Local model | Cloud model |
|---|---|---|
| Chat (Copilot Chat panel) | ✅ Supported | ✅ Supported |
| Inline completions (ghost text) | ❌ NOT supported | ✅ Supported |
| Repo indexing / embeddings | ❌ Requires Copilot service | ✅ Supported |
| Agent mode tool calls | ⚠️ Model-dependent | ✅ Supported |

**Inline completions are not available for local models.** The inline completion provider
(`InlineCompletionItemProvider`) is a separate VS Code API that requires a dedicated extension
(e.g. Continue.dev) and cannot be satisfied by the BYOK chat model alone.

**Network requirement:** Even with a local model configured for chat, VS Code still connects
to GitHub's Copilot service for embeddings, semantic repo-index queries, and task-routing
metadata. A Copilot plan (Free tier is sufficient) is required.

**BYOK not available for:** Copilot Business or Enterprise plans (as of 1.104).

### Implication for EndogenAI

The MCP wrapper previously considered for routing VS Code Copilot requests to Ollama is
**not needed for chat**. Direct configuration achieves the same result. MCP remains relevant
for tool dispatch and A2A integration, but not as a local LLM proxy for chat.

---

## Domain A — Supplementary: LM Studio Offline-First Workflow

The Issue #32 link to an LM Studio + Claude Code offline-first article (Google share link
`share.google/eRjsjmfC7gsXy4MAD`) could not be resolved — neither the Medium nor InfoWorld
URL matched. The article title is: _"How I built a Claude Code workflow with LM Studio for
offline-first development."_

**Implication:** LM Studio exposes an OpenAI-compatible `/v1` endpoint locally (default
`http://localhost:1234/v1`) and can be used identically to Ollama for the BYOK Insiders
custom endpoint setting. The same limitation applies: chat only, no inline completions.

---

## Domain B — M1 Mac Model Recommendations

_Based on: Ollama model catalog (ollama.com/search, fetched 2026-03-05), community sources,
and quantization guidelines. M1 Mac = Apple Silicon arm64, unified memory._

### Assumptions
- M1 base: 8–16 GB unified RAM; M1 Pro/Max: 16–96 GB
- Ollama handles Metal GPU acceleration automatically on Apple Silicon
- Models should fit within ~60–70% of total RAM to leave headroom for OS + Chrome

### Recommended models by use-case

#### Chat / general reasoning
| Model | Size | RAM (Q4) | Notes |
|---|---|---|---|
| `qwen2.5:7b` | 7B | ~5 GB | Strong multilingual, good tool-calling |
| `qwen3.5:1.5b` | 1.5B | ~1.5 GB | New (Mar 2026), on-device optimised |
| `mistral:7b` | 7B | ~5 GB | Reliable baseline, good instruction following |
| `phi-4:14b` | 14B | ~10 GB | Strong reasoning, Microsoft, fits M1 Pro |
| `llama3.2:3b` | 3B | ~2.5 GB | Fast, fits M1 base |

#### Code completion / coding chat
| Model | Size | RAM (Q4) | Notes |
|---|---|---|---|
| `qwen2.5-coder:7b` | 7B | ~5 GB | **Top recommendation** for code; HumanEval SOTA for 7B |
| `qwen2.5-coder:14b` | 14B | ~10 GB | Better for M1 Pro/Max; strong FIM support |
| `deepseek-coder-v2:16b` | 16B | ~12 GB | Excellent code; M1 Pro/Max only |
| `starcoder2:7b` | 7B | ~5 GB | Good FIM (fill-in-middle) for completions |

#### Embeddings
| Model | Size | RAM | Notes |
|---|---|---|---|
| `nomic-embed-text` | 137M | <1 GB | **Default for EndogenAI** (AGENTS.md spec); 768-dim |
| `qwen3-embedding:0.6b` | 0.6B | ~0.5 GB | New (Mar 2026), multilingual, strong retrieval |
| `qwen3-embedding:4b` | 4B | ~3 GB | Higher quality; 4096-dim; M1 Pro recommended |
| `mxbai-embed-large` | 335M | <1 GB | Strong MTEB performance, 1024-dim |

> `nomic-embed-text` remains the correct default per AGENTS.md. `qwen3-embedding:0.6b` is
> a viable future upgrade with better multilingual coverage.

#### Tool-calling / agentic use
| Model | Size | RAM (Q4) | Notes |
|---|---|---|---|
| `qwen2.5:7b` | 7B | ~5 GB | Reliable JSON tool-call output |
| `mistral-nemo:12b` | 12B | ~8 GB | Mistral's tool-call tuned model |
| `llama3.1:8b` | 8B | ~6 GB | Strong function-calling; Ollama-native |
| `ministral-3b` | 3B | ~2.5 GB | New (Mar 2026), fast, 128K ctx |

### M1 base (8 GB RAM) quick-start
```bash
ollama pull nomic-embed-text          # embeddings (required by EndogenAI)
ollama pull qwen2.5-coder:7b          # coding
ollama pull qwen2.5:7b                # chat + tool-calling
```

### M1 Pro (16 GB RAM) recommended stack
```bash
ollama pull nomic-embed-text
ollama pull qwen2.5-coder:14b         # better code quality
ollama pull qwen2.5:14b               # chat + agentic
```

---

## Summary

| Finding | Conclusion |
|---|---|
| VS Code local LLM config | **Direct BYOK, no MCP wrapper needed for chat** |
| Inline completions | NOT supported with local models — use Continue.dev extension |
| Best embedding model | `nomic-embed-text` (spec) → `qwen3-embedding:0.6b` (upgrade candidate) |
| Best coding model (8 GB) | `qwen2.5-coder:7b` |
| Best coding model (16 GB) | `qwen2.5-coder:14b` |
| Best chat/agentic (8 GB) | `qwen2.5:7b` |
| Ollama in Docker | Reach host via `http://host.docker.internal:11434` (macOS/Windows) |
