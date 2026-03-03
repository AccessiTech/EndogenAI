---
id: shared-types
version: 0.1.0
status: active
authority: normative
last-reviewed: 2026-03-02
---

# Shared Types

Simplified JSON Schema type definitions used by Python modules across the EndogenAI system. These schemas define the core cognitive data structures that flow between layers.

## Purpose

`shared/types/` contains the three foundational type schemas that all Python cognitive modules share. Unlike the full protocol schemas in `shared/schemas/`, these are designed to be consumed directly by Python code-generation tooling (`scripts/codegen_types.py`) to produce Pydantic dataclasses. Every memory item, reward signal, and signal envelope in the system must conform to these schemas.

---

## Type Catalogue

| File | Title | Description |
|------|-------|-------------|
| `memory-item.schema.json` | `MemoryItem` | Unified memory record used across all memory timescales — working, short-term, long-term, and episodic. Contains content, embedding reference, importance score, affective valence, Tulving triple, and access metadata. |
| `reward-signal.schema.json` | `RewardSignal` | Reward and affective weighting structure used by the Affective / Motivational Layer and the Learning & Adaptation system. Carries scalar reward, valence, arousal, and actor-critic assignment fields. |
| `signal.schema.json` | `Signal` | Common signal envelope passed between layers in EndogenAI. Signals flow bottom-up (Input → Signal Processing → Cognitive Processing) and carry modality, payload, priority, and session metadata. |

---

## Usage

### Python (via code-generated Pydantic models)

The canonical Python representations are generated from these schemas. To regenerate:

```bash
uv run python scripts/codegen_types.py --schema shared/types/memory-item.schema.json --out shared/types/
```

Modules import the generated models directly:

```python
from endogenai_vector_store.models import MemoryItem  # includes MemoryItem
```

### Validation

Any module receiving a `MemoryItem` from the network should validate it against the schema before use:

```python
import json, jsonschema, pathlib

schema = json.loads(pathlib.Path("shared/types/memory-item.schema.json").read_text())
jsonschema.validate(instance=item_dict, schema=schema)
```

---

## See Also

- [shared/schemas/](../schemas/README.md) — full protocol-level schemas (MCPContext, A2ATask, ActionSpec, etc.)
- [shared/vector-store/](../vector-store/README.md) — vector store adapter (uses `MemoryItem` as its core record type)
- [modules/group-ii-cognitive-processing/memory/](../../modules/group-ii-cognitive-processing/memory/README.md) — primary consumer of `MemoryItem`
