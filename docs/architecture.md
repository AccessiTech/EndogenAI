---
id: architecture
version: 0.1.0
status: stub
last-reviewed: 2026-02-24
---

# Architecture

> **Status: stub** — This document will be expanded as implementation progresses through the Workplan phases.

Full architectural overview of the EndogenAI framework, including layer descriptions and signal-flow diagrams.

## Overview

EndogenAI is organized into layered groups that mirror the brain's bottom-up signal processing, bidirectional cognitive feedback, and adaptive learning. MCP and A2A are **cross-cutting infrastructure** — they are not sequential layers but rather a communication backbone that spans all groups.

## Layers

- **Group I — Signal Processing**: Sensory input, attention & filtering, perception
- **Group II — Cognitive Processing**: Working memory, short-term memory, long-term memory, episodic memory, affective/motivational layer, decision-making & reasoning
- **Group III — Executive & Output**: Executive agent, agent runtime, motor/output/effector
- **Group IV — Adaptive Systems**: Learning & adaptation, meta-cognition & monitoring

## Cross-Cutting Infrastructure

- **MCP** — Module Context Protocol: context broker and capability registry spanning all layers
- **A2A** — Agent-to-Agent: task coordination protocol between autonomous module agents

## Signal Flow

_Signal-flow diagrams to be added in Phase 7._

## References

- [Workplan](Workplan.md) — phased implementation roadmap
- [MCP Protocol Guide](protocols/mcp.md)
- [A2A Protocol Guide](protocols/a2a.md)
