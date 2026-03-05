# Resources

Static knowledge resources for the frankenbrAIn framework. These files are the **morphogenetic seed** — the initial encoding
from which all module analogies, interfaces, and conventions are derived.

## Directory Structure

```
resources/
├── static/
│   └── knowledge/
│       └── brain-structure.md     # Authoritative neuroanatomical reference (morphogenetic seed)
└── neuroanatomy/
    ├── sensory-cortex.md          # → sensory-input module
    ├── thalamus.md                # → attention-filtering module
    ├── association-cortices.md    # → perception module
    ├── hippocampus.md             # → memory modules (all timescales)
    ├── limbic-system.md           # → affective module
    ├── prefrontal-cortex.md       # → reasoning module
    ├── frontal-lobe.md            # → executive-agent module
    └── cerebellum.md              # → agent-runtime + motor-output modules
```

## `static/knowledge/`

Long-term static knowledge documents. These are loaded at boot time by the Long-Term Memory module
(`modules/group-ii-cognitive-processing/memory/long-term-memory/`) and chunked/embedded into the
`brain.long-term-memory` vector collection using LlamaIndex.

Each document must include YAML frontmatter with at minimum:

```yaml
---
id: <kebab-case-unique-id>
version: <semver>
status: <draft | in-progress | stable>
authority: <descriptive | normative>
last-reviewed: <YYYY-MM-DD>
seed-collection: <vector-collection-name>
chunking: <section-boundary | paragraph | fixed-token>
maps-to-modules:
  - <module-path>
---
```

## `neuroanatomy/`

Neuroanatomical region stubs — one file per primary module-mapped brain region. Each file establishes:

- The brain region's biological function
- Its signal inputs and outputs
- Key design notes for the corresponding frankenbrAIn module

These files are enriched from `raw_data_dumps/Human_Brain__wiki.md` as part of Phase 0 seed knowledge population.

## URI Registry _(Phase 8.5)_

All MCP-accessible resources are registered in `resources/uri-registry.json` (created in Phase 8.5, validated
against `shared/schemas/uri-registry.schema.json`). The registry uses two URI namespaces:

**Static resources** (this directory):
```
brain://resources/static/knowledge/<id>
brain://resources/neuroanatomy/<id>
```

**Module resources** (per cognitive module, `brain://group-*` scheme):
```
brain://group-i/perception/signal/current
brain://group-i/attention/filter/current
brain://group-ii/working-memory/context/current
brain://group-ii/episodic-memory/episode/{id}
brain://group-ii/reasoning/plan/current
brain://group-iii/executive-agent/status
brain://group-iii/motor-output/queue
brain://group-iv/reward/signal/recent
brain://group-iv/adaptive/weights/current
brain://group-iv/metacognition/confidence/current
```

Per-layer resource definitions are split across `group-i-resources.json` through `group-iv-resources.json` and
merged into `uri-registry.json`. Access-control taxonomy (read:public, read:authenticated, subscribe:authenticated,
write:admin) is documented in `access-control.md` (both created in Phase 8.5).

See `resources/README.md` Phase 8.5 deliverables and
[`docs/Workplan.md §8.5`](../docs/Workplan.md#85-mcp-resource-registry-resources) for implementation detail.
