---
id: module-attention-filtering
version: 0.1.0
status: active
authority: normative
last-reviewed: 2026-02-28
maps-to-modules:
  - modules/group-i-signal-processing/attention-filtering
---

# Attention & Filtering Layer

> **Neuroanatomy analogy**: [Thalamus](../../../resources/neuroanatomy/thalamus.md)

Salience scoring, relevance filtering, signal gating, and signal routing for the
brAIn framework.  Analogous to the thalamus — the relay hub that regulates which
signals reach higher cortical layers.

---

## Purpose

The Attention & Filtering Layer receives **Signal** envelopes from the Sensory /
Input Layer, evaluates each for salience, suppresses irrelevant signals, and
routes the remainder to the appropriate downstream module (typically the
Perception Layer).

It also exposes a **top-down attention modulation interface**: the Executive /
Agent Layer can inject `AttentionDirective` messages to bias salience scoring
toward specific modalities or signal types — implementing goal-directed attention.

---

## Salience Scoring

Salience is computed as:

```
base_weight(modality) × (0.5 + priority/10 × 0.5)
```

Directive boosts are applied multiplicatively post-score.  The default threshold
is `0.3`; signals below this are discarded.

| Modality | Base weight |
|----------|------------|
| `control` | 0.90 |
| `api-event` | 0.70 |
| `text` | 0.60 |
| `image` | 0.50 |
| `audio` | 0.50 |
| `sensor` | 0.40 |
| `internal` | 0.30 |

---

## Interface

### Python

```python
from endogenai_attention_filtering import AttentionFilter, AttentionDirective

af = AttentionFilter(threshold=0.3)

# Optionally inject a top-down directive
directive = AttentionDirective(
    directive_id="focus-text",
    modality_boost={"text": 2.0},
    session_id="sess-abc",
    ttl_ms=5000,
)
af.apply_directive(directive)

filtered = af.evaluate(signal)
if filtered:
    print(filtered.routed_to, filtered.salience.score)
```

### Signal routing

| Modality | Default `routed_to` |
|----------|---------------------|
| `text`, `image`, `audio`, `sensor`, `api-event`, `internal` | `"perception"` |
| `control` | `"executive"` |

---

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `threshold` | `0.3` | Minimum salience score to pass gating |
| `module_id` | `"attention-filtering"` | Canonical module identifier |

---

## MCP + A2A

- **A2A endpoint**: `http://localhost:8102` (`agent-card.json`)
- **MCP endpoint**: `http://localhost:8103`
- Registers capabilities: `mcp-context`, `a2a-task`
- All cross-module communication routes through `infrastructure/adapters/bridge.ts`

---

## Development

```bash
cd modules/group-i-signal-processing/attention-filtering
uv sync
uv run pytest
uv run ruff check .
uv run mypy src/
```
