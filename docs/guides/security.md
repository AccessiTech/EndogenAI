---
id: guide-security
version: 0.1.0
status: stub
last-reviewed: 2026-02-24
---

# Security

> **Status: stub** — This document will be expanded during Phase 8 (Security).

Security model, sandboxing policies, and least-privilege patterns for the EndogenAI framework.

## Principles

- **Security & Privacy by Design** — security is a first-class concern at every layer boundary
- **Least Privilege** — each module operates with the minimum permissions required
- **Module Sandboxing** — modules are isolated via container-level policies

## Module Sandboxing

_OPA policies and gVisor sandbox templates to be added in Phase 8 (`security/`)._

## Inter-Module Interface Review

_Security review of all inter-module interfaces to be conducted in Phase 8._

## References

- [Architecture Overview](../architecture.md)
- [Workplan — Phase 8](../Workplan.md#phase-8--cross-cutting-security-deployment--documentation)
